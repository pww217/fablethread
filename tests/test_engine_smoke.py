"""Smoke tests for ccya engine — no real LLM needed.

Notable design decisions captured here:
- Turn counter increments in engine.py ONLY (not in apply_delta).
- run_turn() is an async generator: yields ("token", str)* then ("complete", TurnResult).
- LLM client is OpenAI-compatible (mlx_lm.server). Tests mock at the
  ccya.engine.llm_chat / ccya.engine.llm_chat_stream level — both return the
  ccya-internal shape {"response": str, "usage": {...}}.
- Narrate call uses [system, user] message roles.
- Extract call uses [system, assistant, user] message roles.
- Chronicle tail and recent turns are injected into the narrate system prompt.
"""

import ccya.engine
import json
import tempfile
from pathlib import Path

import pytest

from ccya.engine import EngineConfig, run_turn, _build_jinja_env, _narrate_messages, _extract_messages
from ccya.llm_client import strip_thinking
from ccya.models import (
    CompendiumNpcUpdate,
    FactUpdate,
    InventoryItem,
    InventoryRemove,
    InventoryUpdate,
    IntentEnvelope,
    NpcRef,
    QuestObjectiveUpdate,
    QuestUpdate,
    Scope,
    StateDelta,
)

# Rules Call 0 returns this when no check is required (default for most tests).
_RULES_NO_ROLL = json.dumps({
    "intent": "player action",
    "intent_verb": "act",
    "target": "",
    "stakes": "",
    "check": {"required": False},
    "scope": {"active_domains": ["scene", "present_npcs"], "skip_domains": [], "implicit_preconditions": [], "ambiguities": []},
})
from ccya.state import (
    apply_delta,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_state,
    save_state,
)

SAVE_DIR = Path(tempfile.mkdtemp())


def _write_state(path: Path, data: dict) -> None:
    save_state(path, data)


def _make_state(turn: int = 0) -> dict:
    return {
        "meta": {
            "game_name": "test",
            "turn": turn,
            "setting_pack": "expanse-belter",
            "model": "mlx-community/Qwen3.6-27B-4bit",
            "compendium_touch_order": [],
        },
        "pc": {
            "name": "Vex",
            "tagline": "salvage pilot",
            "bio": "",
            "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2},
            "conditions": [],
        },
        "location": {"id": "docking-ring-7", "name": "Docking Ring 7", "description": "Low-grav berth."},
        "inventory": [
            {"id": "hand-terminal", "name": "Hand terminal", "notes": "Cracked screen."},
            {"id": "vac-jacket", "name": "Vac jacket", "notes": "Thermal-lined."},
        ],
        "quests": [{"id": "quiet-signal", "title": "The Quiet Signal", "status": "active", "objectives": [{"description": "Find the payer", "done": False}]}],
        "scene": {"tags": [], "present_npcs": [], "established_facts": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


# ---------------------------------------------------------------------------
# Fake LLM helpers — mock ccya.engine.llm_chat / ccya.engine.llm_chat_stream
# ---------------------------------------------------------------------------


class _FakeLLM:
    """Context manager that replaces engine's llm_chat / llm_chat_stream.

    llm_chat_stream is an async generator in the real code, so fake_stream
    must also be an async generator (uses `yield`).
    llm_chat is a regular async function, so fake_chat uses `return`.

    Captures all calls so tests can assert on message shapes.
    text_responses[0] = narrative text (yielded by stream)
    text_responses[1:] = extract responses (returned by chat)
    """

    def __init__(self, text_responses: list[str]):
        self.call_log: list[dict] = []
        self.narrative = text_responses[0] if text_responses else ""
        self.text_responses = text_responses
        self._orig_stream = None
        self._orig_chat = None
        _self = self

        async def _fake_stream(*args, **kwargs):
            """Async generator replacing llm_chat_stream."""
            _self.call_log.append({"kind": "stream", "args": args, "kwargs": kwargs})
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield _self.narrative

        async def _fake_chat(*args, **kwargs):
            """Regular async function replacing llm_chat.

            Call ordering: 1st = rules (returns no-roll JSON), 2nd+ = extract.
            """
            _self.call_log.append({"kind": "chat", "args": args, "kwargs": kwargs})
            chat_calls = [c for c in _self.call_log if c["kind"] == "chat"]
            if len(chat_calls) == 1:
                # First chat call is always the rules Call 0 — return no-roll intent.
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {"prompt_tokens": 30, "total_tokens": 40}}
            result_text = _self.text_responses[-1] if len(_self.text_responses) > 1 else _self.narrative
            return {"response": result_text, "done": True, "usage": {"prompt_tokens": 100, "total_tokens": 200}}

        self._fake_stream = _fake_stream
        self._fake_chat = _fake_chat

    def __enter__(self):
        self._orig_stream = ccya.engine.llm_chat_stream
        self._orig_chat = ccya.engine.llm_chat
        ccya.engine.llm_chat_stream = self._fake_stream
        ccya.engine.llm_chat = self._fake_chat
        return self

    def __exit__(self, *exc_info):
        ccya.engine.llm_chat_stream = self._orig_stream
        ccya.engine.llm_chat = self._orig_chat

    def stream_calls(self) -> list[dict]:
        return [c for c in self.call_log if c["kind"] == "stream"]

    def chat_calls(self) -> list[dict]:
        return [c for c in self.call_log if c["kind"] == "chat"]


async def _run(save_dir, user_input, config=None, fake=None):
    """Drive run_turn() async generator to completion, return TurnResult."""
    result = None
    async for kind, payload in run_turn(save_dir, user_input, config=config,
                                         template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts")):
        if kind == "complete":
            result = payload
    return result


async def _run_with_tokens(save_dir, user_input, config=None):
    """Collect all token events and the final TurnResult."""
    tokens = []
    result = None
    async for kind, payload in run_turn(save_dir, user_input, config=config,
                                         template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts")):
        if kind == "token":
            tokens.append(payload)
        elif kind == "complete":
            result = payload
    return tokens, result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_save_dir():
    if SAVE_DIR.exists():
        for f in SAVE_DIR.iterdir():
            f.unlink()
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    for f in SAVE_DIR.iterdir():
        f.unlink()


# ---------------------------------------------------------------------------
# TestPromptComposition — Critical fix #2, #3, #4
# ---------------------------------------------------------------------------


class TestPromptComposition:
    """Narrate uses [system, user]; extract uses [system, assistant, user]."""

    def _env(self):
        return _build_jinja_env(str(Path(__file__).parent.parent / "ccya" / "prompts"))

    def test_narrate_has_system_and_user_roles(self):
        env = self._env()
        state = _make_state()
        msgs = _narrate_messages(env, state, "I look around")
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "user"]

    def test_narrate_user_message_contains_player_input(self):
        env = self._env()
        state = _make_state()
        msgs = _narrate_messages(env, state, "examine the pinger")
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "examine the pinger" in user_msg["content"]

    def test_narrate_player_input_not_in_system(self):
        env = self._env()
        state = _make_state()
        msgs = _narrate_messages(env, state, "SECRET_PROBE")
        system_msg = next(m for m in msgs if m["role"] == "system")
        assert "SECRET_PROBE" not in system_msg["content"]

    def test_extract_has_system_user_roles(self):
        env = self._env()
        msgs = _extract_messages(env, "The airlock opened.", _make_state())
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "user"]

    def test_extract_user_message_contains_narrative(self):
        env = self._env()
        narrative = "You step through the airlock. The corridor hums."
        msgs = _extract_messages(env, narrative, _make_state())
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert narrative in user_msg["content"]

    def test_extract_user_message_includes_active_quests_and_inventory(self):
        env = self._env()
        state = _make_state()
        state["scene"]["present_npcs"] = [{"id": "npc-a", "name": "A", "notes": "Test."}]
        msgs = _extract_messages(env, "Narrative text.", state)
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "quiet-signal" in user_msg["content"]
        assert "hand-terminal" in user_msg["content"]
        assert "Player" in user_msg["content"]
        assert "Docking Ring 7" in user_msg["content"]
        assert "Present NPCs" in user_msg["content"]
        assert "npc-a" in user_msg["content"]
        assert "1." in user_msg["content"]  # numbered objectives

    def test_extract_user_message_includes_established_facts(self):
        env = self._env()
        state = _make_state()
        state["scene"]["established_facts"] = ["Alpha fact about the station.", "Beta fact about the crew."]
        msgs = _extract_messages(env, "Narrative text.", state)
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "Established facts" in user_msg["content"]
        assert "Alpha fact about the station." in user_msg["content"]
        assert "Beta fact about the crew." in user_msg["content"]

    def test_extract_system_omits_verbatim_pydantic_schema_dump(self):
        env = self._env()
        msgs = _extract_messages(env, "N.", _make_state())
        system_msg = next(m for m in msgs if m["role"] == "system")["content"]
        assert '"$defs"' not in system_msg
        assert "## Output schema" in system_msg

    def test_extract_thinking_toggle(self):
        """Thinking toggle is now a Qwen3 soft-switch: `/think` appended to the last user message when on."""
        env = self._env()
        off = _extract_messages(env, "N.", _make_state(), enable_extract_thinking=False)
        on = _extract_messages(env, "N.", _make_state(), enable_extract_thinking=True)
        last_off = off[-1]["content"]
        last_on = on[-1]["content"]
        assert not last_off.endswith("/think")
        assert last_on.endswith("/think")

    def test_extract_scope_in_user_message(self):
        """Scope from intent is injected into extract user message."""
        from ccya.models import Scope
        env = self._env()
        state = _make_state()
        scope = Scope(active_domains=["scene", "inventory"], skip_domains=["quest_updates", "location_change"])
        msgs = _extract_messages(env, "N.", state, intent=IntentEnvelope(scope=scope))
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "Active domains: scene, inventory" in user_msg["content"]
        assert "Skip domains: quest_updates, location_change" in user_msg["content"]

    def test_extract_scope_preconditions_in_user_message(self):
        """Scope preconditions and ambiguities appear in user message."""
        from ccya.models import Scope
        env = self._env()
        state = _make_state()
        scope = Scope(
            active_domains=["scene"],
            skip_domains=["inventory"],
            implicit_preconditions=["guard must be unconscious"],
            ambiguities=["'the chest' — which chest?"],
        )
        msgs = _extract_messages(env, "N.", state, intent=IntentEnvelope(scope=scope))
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "Preconditions assumed: guard must be unconscious" in user_msg["content"]
        assert "Ambiguities to resolve: 'the chest' — which chest?" in user_msg["content"]

    def test_extract_scope_defaults_when_no_intent(self):
        """When intent is None, scope defaults to empty (no skip_domains)."""
        env = self._env()
        msgs = _extract_messages(env, "N.", _make_state(), intent=None)
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "Active domains: " in user_msg["content"]
        assert "Skip domains: " in user_msg["content"]

    def test_narrate_thinking_toggle(self):
        """Thinking toggle is now a Qwen3 soft-switch: `/think` appended to the last user message when on."""
        env = self._env()
        off = _narrate_messages(env, _make_state(), "look", enable_narrate_thinking=False)
        on = _narrate_messages(env, _make_state(), "look", enable_narrate_thinking=True)
        last_off = off[-1]["content"]
        last_on = on[-1]["content"]
        assert not last_off.endswith("/think")
        assert last_on.endswith("/think")

    def test_strip_thinking_removes_thinking_block(self):
        """`<think>...</think>` blocks (Qwen3-style) are stripped from response text."""
        raw = "<think>\n- bullet\n</think>\n\nYou step through."
        assert strip_thinking(raw).strip() == "You step through."

    def test_chronicle_injected_when_present(self):
        env = self._env()
        state = _make_state()
        chronicle_tail = "Earlier, Vex found a dead comms relay."
        msgs = _narrate_messages(env, state, "look", chronicle_tail=chronicle_tail)
        system_text = next(m for m in msgs if m["role"] == "system")["content"]
        assert "Earlier, Vex found a dead comms relay." in system_text

    def test_recent_turns_injected_when_present(self):
        env = self._env()
        state = _make_state()
        recent = [{"turn": 1, "input": "look around", "narrative": "You see a docking bay."}]
        msgs = _narrate_messages(env, state, "go forward", recent_turns=recent)
        system_text = next(m for m in msgs if m["role"] == "system")["content"]
        assert "look around" in system_text

    def test_chronicle_absent_when_empty(self):
        env = self._env()
        state = _make_state()
        msgs = _narrate_messages(env, state, "look", chronicle_tail="")
        system_text = next(m for m in msgs if m["role"] == "system")["content"]
        assert "Earlier" not in system_text


# ---------------------------------------------------------------------------
# TestHappyPath
# ---------------------------------------------------------------------------


class TestHappyPath:

    async def test_narrate_and_extract(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You step through the airlock. The corridor stretches ahead, dim and humming."
        extract = json.dumps({
            "state_delta": {
                "established_facts_add": ["You found an airlock at Docking Ring 7."],
                "scene_tags": ["exploration"],
            },
            "actions": ["Go left", "Go right", "Check your terminal", "Wait"],
        })

        fake = _FakeLLM([narrative, extract])
        with fake:
            result = await _run(SAVE_DIR, "I step through the airlock.", config=EngineConfig())

        assert result.narrative == narrative
        assert result.established_facts == ["You found an airlock at Docking Ring 7."]
        assert result.metrics["narrate"]["total_ms"] >= 0
        assert result.metrics["extract"]["retries"] == 0
        assert len(result.errors) == 0
        # Single increment: turn starts at 0, engine increments to 1
        assert result.turn == 1

    async def test_actions_captured(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"scene_tags": ["exploration"]},
            "actions": ["Open door", "Take stairs", "Check map", "Go back"],
        })
        fake = _FakeLLM(["narrative text", extract])
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())

        assert result.actions == ["Open door", "Take stairs", "Check map", "Go back"]


# ---------------------------------------------------------------------------
# TestStreamingEvents — Critical fix #1
# ---------------------------------------------------------------------------


class TestStreamingEvents:
    """run_turn must yield ("token", str) events before ("complete", TurnResult)."""

    async def test_yields_token_events(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {},
            "actions": ["A", "B", "C", "D"],
        })
        fake = _FakeLLM(["hello world", extract])
        with fake:
            tokens, result = await _run_with_tokens(SAVE_DIR, "look", config=EngineConfig())

        assert len(tokens) >= 1
        assert "".join(tokens) == "hello world"
        assert result is not None
        assert result.narrative == "hello world"

    async def test_complete_comes_after_tokens(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        events = []
        extract = json.dumps({"state_delta": {}, "actions": ["A", "B", "C", "D"]})
        fake = _FakeLLM(["the narrative", extract])
        with fake:
            async for kind, _ in run_turn(
                SAVE_DIR, "look", config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
            ):
                events.append(kind)

        assert "token" in events
        assert events[-1] == "complete"
        assert events.index("token") < events.index("complete")


# ---------------------------------------------------------------------------
# TestRejectedDelta
# ---------------------------------------------------------------------------


class TestRejectedDelta:

    async def test_remove_nonexistent_item(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"inventory_remove": ["ghost-item-999"]},
            "actions": ["A", "B", "C", "D"],
        })
        fake = _FakeLLM([extract])
        with fake:
            result = await _run(SAVE_DIR, "I grab the ghost item.", config=EngineConfig())

        assert len(result.rejected) == 1
        assert result.rejected[0]["value"] == "ghost-item-999"
        assert "does not exist" in result.rejected[0]["reason"]
        assert len(result.errors) > 0

    async def test_trace_id_in_narrative_on_rejection(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"inventory_remove": ["ghost-item"]},
            "actions": ["A", "B", "C", "D"],
        })
        fake = _FakeLLM([extract])
        with fake:
            result = await _run(SAVE_DIR, "grab ghost", config=EngineConfig())

        assert result.trace_id in result.narrative

    async def test_update_nonexistent_quest_creates_it(self) -> None:
        """quest_updates is create-or-update: unknown quest IDs should be created, not rejected."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"quest_updates": [{"id": "new-quest", "title": "New Quest", "status": "active", "objectives": []}]},
            "actions": ["A", "B", "C", "D"],
        })
        fake = _FakeLLM([extract])
        with fake:
            result = await _run(SAVE_DIR, "Start a new quest.", config=EngineConfig())

        # Should not be rejected — quest_updates creates new quests
        assert not any(r.get("field") == "quest_updates" for r in result.rejected)
        # Quest should now exist in saved state
        saved = load_state(SAVE_DIR)
        quest_ids = {q.get("id") for q in saved.get("quests", [])}
        assert "new-quest" in quest_ids


# ---------------------------------------------------------------------------
# TestSchemaFailureRetry
# ---------------------------------------------------------------------------


class TestSchemaFailureRetry:

    async def test_single_retry(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You examine the hand terminal closely."
        good_extract = json.dumps({
            "state_delta": {"pc_condition_add": ["curious"]},
            "actions": ["A", "B", "C", "D"],
        })
        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                # Call 0 = rules intent — return no-roll.
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            if chat_call_count == 2:
                # First extract attempt — return bad JSON.
                return {"response": "bad json {{{", "done": True, "usage": {}}
            return {"response": good_extract, "done": True, "usage": {"prompt_tokens": 10, "total_tokens": 200}}

        _orig_stream = ccya.engine.llm_chat_stream
        _orig_chat = ccya.engine.llm_chat
        try:
            ccya.engine.llm_chat_stream = fake_stream
            ccya.engine.llm_chat = fake_chat
            result = await _run(SAVE_DIR, "examine", config=EngineConfig(max_extract_retries=1))
        finally:
            ccya.engine.llm_chat_stream = _orig_stream
            ccya.engine.llm_chat = _orig_chat

        assert "curious" in result.applied.get("pc_condition_add", []) or "curious" in str(result.applied)
        assert result.metrics["extract"]["retries"] == 1


# ---------------------------------------------------------------------------
# TestFactCanonization
# ---------------------------------------------------------------------------


class TestFactCanonization:

    async def test_facts_in_state(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"established_facts_add": ["The airlock hums with residual charge."]},
            "actions": ["A", "B", "C", "D"],
        })
        fake = _FakeLLM([extract])
        with fake:
            await _run(SAVE_DIR, "Touch the airlock.", config=EngineConfig())

        loaded = load_state(SAVE_DIR)
        facts = loaded.get("scene", {}).get("established_facts", [])
        assert "The airlock hums with residual charge." in facts


# ---------------------------------------------------------------------------
# TestChroniclePrefixBudget
# ---------------------------------------------------------------------------


class TestChroniclePrefixBudget:

    def test_chronicle_tail(self) -> None:
        large_text = "This is a sentence. " * 2000
        chronicle = SAVE_DIR / "chronicle.md"
        chronicle.write_text(large_text)
        tail = load_chronicle_tail(SAVE_DIR, max_tokens=100)
        words = tail.split()
        assert len(words) <= 100

    async def test_chronicle_injected_in_engine_run(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)
        chronicle = SAVE_DIR / "chronicle.md"
        chronicle.write_text("MARKER_TEXT_FOR_ASSERTION")

        captured_messages = []

        async def fake_stream(*args, **kwargs):
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            captured_messages.extend(msgs)
            yield "narrative"

        _chat_calls_chron = 0

        async def fake_chat(*args, **kwargs):
            nonlocal _chat_calls_chron
            _chat_calls_chron += 1
            if _chat_calls_chron == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            return {"response": json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]}), "done": True, "usage": {}}

        import ccya.engine as eng
        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = fake_stream
            eng.llm_chat = fake_chat
            await _run(SAVE_DIR, "look", config=EngineConfig(chronicle_prefix_budget_tokens=1500))
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        system_texts = " ".join(m.get("content", "") for m in captured_messages if m.get("role") == "system")
        assert "MARKER_TEXT_FOR_ASSERTION" in system_texts


# ---------------------------------------------------------------------------
# TestStateApplyDelta
# ---------------------------------------------------------------------------


class TestStateApplyDelta:

    def test_inventory_add(self) -> None:
        state = _make_state()
        delta = StateDelta(inventory_add=[{"id": "plasma-cutter", "name": "Plasma cutter", "notes": "Hot."}])
        updated = apply_delta(state, delta)
        assert "plasma-cutter" in [item["id"] for item in updated["inventory"]]
        assert len(updated["inventory"]) == 3

    def test_inventory_remove(self) -> None:
        state = _make_state()
        delta = StateDelta(inventory_remove=["hand-terminal"])
        updated = apply_delta(state, delta)
        assert "hand-terminal" not in [item["id"] for item in updated["inventory"]]

    def test_inventory_merges_by_id(self) -> None:
        state = {
            **_make_state(),
            "inventory": [{"id": "credits", "name": "Credits", "amount": 100, "notes": "Cash."}],
        }
        delta = StateDelta(
            inventory_add=[InventoryItem(id="credits", name="Credits", amount=50, notes="Cash.")],
        )
        updated = apply_delta(state, delta)
        cred = next(i for i in updated["inventory"] if i["id"] == "credits")
        assert cred["amount"] == 150

    def test_inventory_remove_partial_amount(self) -> None:
        state = {
            **_make_state(),
            "inventory": [{"id": "credits", "name": "Credits", "amount": 1800, "notes": ""}],
        }
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=500)])
        updated = apply_delta(state, delta)
        cred = next(i for i in updated["inventory"] if i["id"] == "credits")
        assert cred["amount"] == 1300

    def test_inventory_remove_full_stack_when_amount_exhausts(self) -> None:
        state = {
            **_make_state(),
            "inventory": [{"id": "credits", "name": "Credits", "amount": 100, "notes": ""}],
        }
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=100)])
        updated = apply_delta(state, delta)
        assert "credits" not in [i["id"] for i in updated["inventory"]]

    def test_credits_sort_to_top(self) -> None:
        state = {
            **_make_state(),
            "inventory": [
                {"id": "hand-terminal", "name": "Hand terminal", "amount": 1, "notes": ""},
                {"id": "credits", "name": "Credits", "amount": 50, "notes": ""},
            ],
        }
        updated = apply_delta(state, StateDelta())
        assert updated["inventory"][0]["id"] == "credits"

    def test_location_change(self) -> None:
        state = _make_state()
        delta = StateDelta(location_change={"id": "concourse-b", "name": "Concourse B", "description": "Wide and bright."})
        updated = apply_delta(state, delta)
        assert updated["location"]["id"] == "concourse-b"

    def test_location_description_in_place(self) -> None:
        state = _make_state()
        delta = StateDelta(location_description="The berth lights flicker.")
        updated = apply_delta(state, delta)
        assert updated["location"]["description"] == "The berth lights flicker."
        assert updated["location"]["id"] == "docking-ring-7"

    def test_inventory_id_normalization_merges_stack(self) -> None:
        state = _make_state()
        delta = StateDelta(
            inventory_add=[
                InventoryItem(id="water-filter", name="Filter", amount=1),
                InventoryItem(id="Water_Filter", name="Filter", amount=1),
            ],
        )
        updated = apply_delta(state, delta)
        assert len(updated["inventory"]) == 3  # hand-terminal, vac-jacket, merged water stack
        wf = next(i for i in updated["inventory"] if "water" in i["id"].lower() or "filter" in i["id"].lower())
        assert wf["amount"] == 2

    def test_turn_counter_not_incremented_in_apply_delta(self) -> None:
        """apply_delta must NOT change meta.turn — that is the engine's job."""
        state = _make_state(turn=5)
        delta = StateDelta()
        updated = apply_delta(state, delta)
        assert updated["meta"]["turn"] == 5


# ---------------------------------------------------------------------------
# TestTurnCounterSingleIncrement — Critical fix #7
# ---------------------------------------------------------------------------


class TestTurnCounterSingleIncrement:
    """Turn counter increments exactly once per run_turn() call."""

    async def test_single_increment(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]})
        fake = _FakeLLM([extract])
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())

        assert result.turn == 1

    async def test_sequential_turns_increment_cleanly(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]})
        fake = _FakeLLM([extract, extract])
        with fake:
            r1 = await _run(SAVE_DIR, "first", config=EngineConfig())
            r2 = await _run(SAVE_DIR, "second", config=EngineConfig())

        assert r1.turn == 1
        assert r2.turn == 2


# ---------------------------------------------------------------------------
# TestEventWrittenBeforeState
# ---------------------------------------------------------------------------


class TestEventWrittenBeforeState:

    async def test_write_order(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"established_facts_add": ["turn-1-fact"]},
            "actions": ["A","B","C","D"],
        })
        fake = _FakeLLM([extract])
        with fake:
            await _run(SAVE_DIR, "test", config=EngineConfig())

        events = (SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        assert len(events) == 1
        event = json.loads(events[0])
        assert event["turn"] == 1
        assert event["input"] == "test"

        loaded = load_state(SAVE_DIR)
        assert loaded["meta"]["turn"] == 1


# ---------------------------------------------------------------------------
# TestChronicleFormatted
# ---------------------------------------------------------------------------


class TestChronicleFormatted:
    """Chronicle entries are formatted with turn headers."""

    async def test_chronicle_has_turn_header(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)
        (SAVE_DIR / "chronicle.md").touch()

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]})
        fake = _FakeLLM(["the narrative text", extract])
        with fake:
            await _run(SAVE_DIR, "my action", config=EngineConfig())

        chronicle = (SAVE_DIR / "chronicle.md").read_text()
        assert "## Turn 1" in chronicle
        assert "my action" in chronicle
        assert "the narrative text" in chronicle


# ---------------------------------------------------------------------------
# TestChronicleTurnParser
# ---------------------------------------------------------------------------


class TestChronicleTurnParser:

    def test_parses_turn_blocks(self) -> None:
        _write_state(SAVE_DIR, _make_state())
        (SAVE_DIR / "chronicle.md").write_text(
            "\n\n## Turn 1 — look\n\nFirst narrative.\n\n## Turn 2 — go north\n\nSecond narrative longer.\n",
        )
        turns = load_recent_chronicle_turns(SAVE_DIR, 6)
        assert len(turns) == 2
        assert turns[0]["turn"] == 1
        assert turns[0]["input"] == "look"
        assert "First narrative" in turns[0]["narrative"]
        assert turns[1]["turn"] == 2
        assert "Second narrative" in turns[1]["narrative"]

    def test_empty_chronicle(self) -> None:
        _write_state(SAVE_DIR, _make_state())
        (SAVE_DIR / "chronicle.md").write_text("")
        assert load_recent_chronicle_turns(SAVE_DIR, 6) == []

    def test_tolerates_extra_blank_lines(self) -> None:
        _write_state(SAVE_DIR, _make_state())
        (SAVE_DIR / "chronicle.md").write_text("\n\n\n## Turn 3 — act\n\n\nBody.\n\n")
        turns = load_recent_chronicle_turns(SAVE_DIR, 6)
        assert len(turns) == 1
        assert turns[0]["input"] == "act"
        assert turns[0]["narrative"].strip() == "Body."


# ---------------------------------------------------------------------------
# TestTurnResultTraceId
# ---------------------------------------------------------------------------


class TestTurnResultTraceId:

    async def test_unique_trace_ids(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)
        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]})
        fake = _FakeLLM([extract, extract])
        with fake:
            r1 = await _run(SAVE_DIR, "first", config=EngineConfig())
            r2 = await _run(SAVE_DIR, "second", config=EngineConfig())

        assert r1.trace_id != r2.trace_id
        assert len(r1.trace_id) > 0


# ---------------------------------------------------------------------------
# TestFactDeduplication
# ---------------------------------------------------------------------------


class TestFactsDelta:

    def test_add_only(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["fact one", "fact two"]
        delta = StateDelta(established_facts_add=["fact three"])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert facts == ["fact one", "fact two", "fact three"]

    def test_empty_delta_noop(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["keep me"]
        delta = StateDelta()
        updated = apply_delta(state, delta)
        assert updated["scene"]["established_facts"] == ["keep me"]

    def test_update_preserves_position(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["alpha", "beta", "gamma"]
        delta = StateDelta(
            established_facts_update=[FactUpdate(old="beta", new="beta revised")],
        )
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert facts[1] == "beta revised"
        assert facts[0] == "alpha"

    def test_remove_normalized_match(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["  The Ship is damaged.  ", "Other fact."]
        delta = StateDelta(established_facts_remove=["The Ship is damaged."])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert "Other fact." in facts
        assert not any("damaged" in f for f in facts)

    def test_update_fallback_appends_when_old_missing(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["only"]
        delta = StateDelta(
            established_facts_update=[FactUpdate(old="no such fact", new="appended instead")],
        )
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert facts == ["only", "appended instead"]


class TestEstablishedFactsEviction:

    def test_eviction(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["f1", "f2", "f3", "f4", "f5"]
        delta = StateDelta(established_facts_add=["f6", "f7", "f8", "f9", "f10", "f11"])
        updated = apply_delta(state, delta, established_facts_max=10)
        facts = updated["scene"]["established_facts"]
        assert len(facts) <= 10
        assert "f11" in facts
        assert "f1" not in facts


class TestPcConditionsDelta:

    def test_add_and_remove(self) -> None:
        state = _make_state()
        delta = StateDelta(pc_condition_add=["wanted", "injured"])
        updated = apply_delta(state, delta)
        assert updated["pc"]["conditions"] == ["wanted", "injured"]
        delta2 = StateDelta(pc_condition_remove=["wanted"])
        updated2 = apply_delta(updated, delta2)
        assert updated2["pc"]["conditions"] == ["injured"]

    def test_normalized_dedup_skips_variants(self) -> None:
        """Same condition with different case / whitespace / markdown is rejected on add."""
        state = _make_state()
        state["pc"]["conditions"] = ["bruised ribs"]
        delta = StateDelta(pc_condition_add=["Bruised Ribs", "*bruised ribs*", "bruised  ribs"])
        updated = apply_delta(state, delta)
        assert updated["pc"]["conditions"] == ["bruised ribs"]

    def test_cap_at_5_evicts_oldest(self) -> None:
        """When more than 5 conditions accumulate, oldest is dropped FIFO."""
        state = _make_state()
        state["pc"]["conditions"] = ["c1", "c2", "c3", "c4", "c5"]
        delta = StateDelta(pc_condition_add=["c6", "c7"])
        updated = apply_delta(state, delta)
        conds = updated["pc"]["conditions"]
        assert len(conds) == 5
        assert "c7" in conds
        assert "c6" in conds
        assert "c1" not in conds
        assert "c2" not in conds


class TestEstablishedFactsCap25:

    def test_cap_at_25(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = [f"f{i}" for i in range(24)]
        delta = StateDelta(established_facts_add=["f24", "f25", "f26"])
        updated = apply_delta(state, delta, established_facts_max=25)
        facts = updated["scene"]["established_facts"]
        assert len(facts) == 25
        assert "f26" in facts
        assert "f0" not in facts


class TestQuestStatusSideEffects:

    def test_completed_marks_all_objectives_done(self) -> None:
        state = _make_state()
        state["quests"][0]["objectives"] = [
            {"description": "A", "done": False},
            {"description": "B", "done": False, "failed": True},
        ]
        delta = StateDelta(
            quest_updates=[QuestUpdate(id="quiet-signal", status="completed", objectives=[])],
        )
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["status"] == "completed"
        for o in q["objectives"]:
            assert o["done"] is True
            assert o.get("failed") is False

    def test_failed_marks_open_objectives_failed(self) -> None:
        state = _make_state()
        state["quests"][0]["objectives"] = [
            {"description": "A", "done": True},
            {"description": "B", "done": False},
        ]
        delta = StateDelta(quest_updates=[QuestUpdate(id="quiet-signal", status="failed", objectives=[])])
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["status"] == "failed"
        objs = {o["description"]: o for o in q["objectives"]}
        assert objs["A"]["done"] is True
        assert objs["B"].get("failed") is True

    def test_abandoned_does_not_auto_fail_objectives(self) -> None:
        state = _make_state()
        state["quests"][0]["objectives"] = [{"description": "Find the payer", "done": False}]
        delta = StateDelta(quest_updates=[QuestUpdate(id="quiet-signal", status="abandoned", objectives=[])])
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["status"] == "abandoned"
        assert q["objectives"][0]["done"] is False
        assert not q["objectives"][0].get("failed")

    def test_objective_failed_merged_on_update(self) -> None:
        state = _make_state()
        delta = StateDelta(
            quest_updates=[
                QuestUpdate(
                    id="quiet-signal",
                    objectives=[QuestObjectiveUpdate(index=1, failed=True)],
                ),
            ],
        )
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["status"] == "active"
        assert q["objectives"][0].get("failed") is True

    def test_objective_by_index_marks_done(self) -> None:
        state = _make_state()
        delta = StateDelta(
            quest_updates=[QuestUpdate(id="quiet-signal", objectives=[QuestObjectiveUpdate(index=1, done=True)])],
        )
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["objectives"][0]["done"] is True

    def test_objective_index_out_of_range_falls_back_to_description(self) -> None:
        state = _make_state()
        delta = StateDelta(
            quest_updates=[
                QuestUpdate(
                    id="quiet-signal",
                    objectives=[QuestObjectiveUpdate(index=99, description="Find the payer", done=True)],
                ),
            ],
        )
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["objectives"][0]["done"] is True


class TestApplyDeltaEstablishedFactsMax:

    def test_custom_max_wired(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["f1"]
        delta = StateDelta(established_facts_add=["f2", "f3", "f4"])
        updated = apply_delta(state, delta, established_facts_max=2)
        facts = updated["scene"]["established_facts"]
        assert len(facts) <= 2
        assert facts == ["f3", "f4"]


class TestInventoryCompendiumTagline:
    def test_inventory_update_changes_notes(self) -> None:
        state = _make_state()
        delta = StateDelta(inventory_update=[InventoryUpdate(id="vac-jacket", notes="Patched.")])
        out = apply_delta(state, delta)
        item = next(x for x in out["inventory"] if x["id"] == "vac-jacket")
        assert item["notes"] == "Patched."

    def test_inventory_update_unknown_id_skipped(self) -> None:
        state = _make_state()
        before = len(state["inventory"])
        delta = StateDelta(inventory_update=[InventoryUpdate(id="nope-item", notes="x")])
        out = apply_delta(state, delta)
        assert len(out["inventory"]) == before

    def test_npc_bio_mirrored_to_compendium(self) -> None:
        state = _make_state()
        delta = StateDelta(
            present_npcs=[
                NpcRef(id="fixer", name="Anna", title="Fence", notes="Watching.", bio="Owes you from Tycho."),
            ],
        )
        out = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["fixer"]["bio"] == "Owes you from Tycho."

    def test_npc_bio_preserved_when_bio_empty_in_delta(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {"name": "Anna", "title": "Fence", "bio": "Old bio."}
        delta = StateDelta(
            present_npcs=[
                NpcRef(id="fixer", name="Anna", title="Fence", notes="New mood.", bio=""),
            ],
        )
        out = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["fixer"]["bio"] == "Old bio."

    def test_present_npcs_id_and_notes_only_hydrates_from_compendium(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {"name": "Anna", "title": "Fence", "bio": "Stored dossier."}
        delta = StateDelta(present_npcs=[NpcRef(id="fixer", notes="Suspicious tonight.")])
        out = apply_delta(state, delta)
        npc = out["scene"]["present_npcs"][0]
        assert npc["id"] == "fixer"
        assert npc["name"] == "Anna"
        assert npc["title"] == "Fence"
        assert npc["bio"] == "Stored dossier."
        assert npc["notes"] == "Suspicious tonight."

    def test_compendium_npc_update_absent_npc(self) -> None:
        state = _make_state()
        delta = StateDelta(
            compendium_npc_update=[CompendiumNpcUpdate(id="missing-wife", bio="Seen on Ganymede.")],
        )
        out = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["missing_wife"]["bio"] == "Seen on Ganymede."

    def test_scene_tagline_set(self) -> None:
        state = _make_state()
        delta = StateDelta(scene_tagline="Fees due at dawn")
        out = apply_delta(state, delta)
        assert out["scene"]["tagline"] == "Fees due at dawn"

    def test_load_state_migrates_old_stats(self, tmp_path: Path) -> None:
        """Old 4-stat schema (body/mind/tech/social) must be migrated to the 6-stat canonical set."""
        from ccya.state import load_state as ls_load
        from ccya.state import save_state as ls_save

        raw = {
            "meta": {"turn": 0, "game_name": "t", "setting_pack": "", "model": "", "compendium_touch_order": []},
            "pc": {"name": "A", "tagline": "", "stats": {"body": 2, "mind": 3, "tech": 2, "social": 3}, "conditions": []},
            "location": {"id": "", "name": "", "description": ""},
            "inventory": [],
            "quests": [],
            "scene": {"tags": [], "present_npcs": [], "established_facts": [], "tagline": ""},
            "compendium": {"npcs": {}},
        }
        ls_save(tmp_path, raw)
        st = ls_load(tmp_path)
        stats = st["pc"]["stats"]
        assert "body" not in stats
        assert "mind" not in stats
        assert stats.get("strength") == 2
        assert stats.get("wits") == 3
        assert stats.get("lore") == 2
        assert stats.get("charisma") == 3
        assert "dexterity" in stats
        assert "resolve" in stats

    def test_load_state_migrates_concept_to_tagline(self, tmp_path: Path) -> None:
        from ccya.state import load_state as ls_load
        from ccya.state import save_state as ls_save

        raw = {
            "meta": {"turn": 0, "game_name": "t", "setting_pack": "", "model": ""},
            "pc": {"name": "A", "concept": "old pitch", "stats": {}, "conditions": []},
            "location": {"id": "", "name": "", "description": ""},
            "inventory": [],
            "quests": [],
            "scene": {"tags": [], "present_npcs": [], "established_facts": []},
        }
        ls_save(tmp_path, raw)
        st = ls_load(tmp_path)
        assert st["pc"]["tagline"] == "old pitch"
        assert "concept" not in st["pc"]

    async def test_turn_result_includes_diff_lines(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)
        extract = json.dumps({
            "state_delta": {
                "scene_tags": ["test"],
                "scene_tagline": "Dock tension rises",
                "established_facts_add": ["A fact."],
            },
            "actions": ["a", "b", "c", "d"],
        })
        fake = _FakeLLM(["short narrative.", extract])
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())
        assert result.diff
        assert any("A fact" in line for line in result.diff)


# ---------------------------------------------------------------------------
# TestPerTurnMetrics
# ---------------------------------------------------------------------------


class TestPerTurnMetrics:

    async def test_metrics_keys_present(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]})
        fake = _FakeLLM(["narrative", extract])
        with fake:
            result = await _run(SAVE_DIR, "test", config=EngineConfig())

        assert "narrate" in result.metrics
        assert "extract" in result.metrics
        assert "first_token_ms" in result.metrics["narrate"]
        assert "total_ms" in result.metrics["narrate"]
        assert "tokens_in" in result.metrics["extract"]
        assert "tokens_out" in result.metrics["extract"]

    async def test_narrate_metrics_token_counts_not_extract_copy(self) -> None:
        """Narrate token counts come from streaming stats, not extract usage."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]})
        fake = _FakeLLM(["narrative", extract])
        with fake:
            result = await _run(SAVE_DIR, "test", config=EngineConfig())

        narr = result.metrics["narrate"]
        ext = result.metrics["extract"]
        assert narr.get("tokens_in") == 42
        assert narr.get("tokens_out") == 24
        assert ext.get("tokens_in") == 100
        assert ext.get("tokens_out") == 200


# ---------------------------------------------------------------------------
# TestEstablishedFactsInEvent
# ---------------------------------------------------------------------------


class TestEstablishedFactsInEvent:

    async def test_event_has_facts_add_in_applied_no_narrative_key(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"established_facts_add": ["This fact matters."]},
            "actions": ["A","B","C","D"],
        })
        fake = _FakeLLM([extract])
        with fake:
            await _run(SAVE_DIR, "test", config=EngineConfig())

        events = (SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[-1])
        applied_add = event.get("applied", {}).get("established_facts_add", [])
        assert "This fact matters." in applied_add
        assert "narrative" not in event


# ---------------------------------------------------------------------------
# TestRecentTurnsInjected
# ---------------------------------------------------------------------------


class TestRecentTurnsInjected:
    """After a turn is played, the next turn's prompt should include it."""

    async def test_recent_turn_in_next_narrate_system(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)
        (SAVE_DIR / "events.jsonl").touch()
        # Prior narrative lives in chronicle.md (canonical); engine reads via load_recent_chronicle_turns
        (SAVE_DIR / "chronicle.md").write_text(
            "\n\n## Turn 1 — I examine the signal\n\nThe signal pulses orange.\n",
        )

        captured_system = []

        async def fake_stream(*args, **kwargs):
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            for m in msgs:
                if m.get("role") == "system":
                    captured_system.append(m["content"])
            yield "narrative"

        _chat_calls_recent = 0

        async def fake_chat(*args, **kwargs):
            nonlocal _chat_calls_recent
            _chat_calls_recent += 1
            if _chat_calls_recent == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            return {"response": json.dumps({"state_delta": {}, "actions": ["A","B","C","D"]}), "done": True, "usage": {}}

        import ccya.engine as eng
        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = fake_stream
            eng.llm_chat = fake_chat
            await _run(SAVE_DIR, "go north", config=EngineConfig(window_turns=6))
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        combined = " ".join(captured_system)
        assert "I examine the signal" in combined or "The signal pulses orange" in combined


# ---------------------------------------------------------------------------
# TestPackKwargs — pack_style and pack_examples wired through run_turn
# ---------------------------------------------------------------------------


class TestPackKwargs:
    """pack_style appears in narrate system; pack_examples appear in extract system."""

    async def test_pack_style_in_narrate_system(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        captured_narrate_system = []
        extract = json.dumps({"state_delta": {}, "actions": ["A", "B", "C", "D"]})

        async def _fake_stream(*args, **kwargs):
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            for m in msgs:
                if m.get("role") == "system":
                    captured_narrate_system.append(m["content"])
            yield "narrative"

        _narrate_chat_calls = 0

        async def _fake_chat(*args, **kwargs):
            nonlocal _narrate_chat_calls
            _narrate_chat_calls += 1
            if _narrate_chat_calls == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            return {"response": extract, "done": True, "usage": {}}

        import ccya.engine as eng
        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = _fake_stream
            eng.llm_chat = _fake_chat
            async for _ in run_turn(
                SAVE_DIR, "look",
                config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
                pack_style="UNIQUE_STYLE_MARKER_7483",
            ):
                pass
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        assert any("UNIQUE_STYLE_MARKER_7483" in s for s in captured_narrate_system)

    async def test_pack_examples_in_extract_system(self) -> None:
        from ccya.pack import ExtractExample

        state = _make_state()
        _write_state(SAVE_DIR, state)

        example_json = json.dumps({"state_delta": {}, "actions": ["A", "B", "C", "D"]})
        examples = [ExtractExample(
            title="Pack example marker UNIQUE_9928",
            thinking="- test",
            **{"json": example_json},
        )]

        captured_extract_system = []

        async def _fake_stream(*args, **kwargs):
            yield "narrative"

        _extract_chat_calls = 0

        async def _fake_chat(*args, **kwargs):
            nonlocal _extract_chat_calls
            _extract_chat_calls += 1
            if _extract_chat_calls == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            for m in msgs:
                if m.get("role") == "system":
                    captured_extract_system.append(m["content"])
            return {"response": example_json, "done": True, "usage": {}}

        import ccya.engine as eng
        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = _fake_stream
            eng.llm_chat = _fake_chat
            async for _ in run_turn(
                SAVE_DIR, "look",
                config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
                pack_examples=examples,
            ):
                pass
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        assert any("Pack example marker UNIQUE_9928" in s for s in captured_extract_system)
