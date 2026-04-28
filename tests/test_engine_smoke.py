"""Smoke tests for ccya engine — no real Ollama needed.

Notable design decisions captured here:
- Turn counter increments in engine.py ONLY (not in apply_delta).
- run_turn() is an async generator: yields ("token", str)* then ("complete", TurnResult).
- Ollama body must have temperature/num_ctx under options{}, keep_alive top-level.
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
from ccya.models import QuestUpdate, StateDelta
from ccya.ollama import _build_body
from ccya.state import (
    apply_delta,
    load_state,
    load_chronicle_tail,
    save_state,
    append_chronicle,
    append_event,
)

SAVE_DIR = Path(tempfile.mkdtemp())


def _write_state(path: Path, data: dict) -> None:
    save_state(path, data)


def _make_state(turn: int = 0) -> dict:
    return {
        "meta": {"game_name": "test", "turn": turn, "setting_pack": "expanse-belter", "model": "gemma3:27b"},
        "pc": {"name": "Vex", "concept": "salvage pilot", "stats": {"body": 2, "mind": 3, "tech": 3, "social": 1}, "conditions": []},
        "location": {"id": "docking-ring-7", "name": "Docking Ring 7", "description": "Low-grav berth."},
        "inventory": [
            {"id": "hand-terminal", "name": "Hand terminal", "notes": "Cracked screen."},
            {"id": "vac-jacket", "name": "Vac jacket", "notes": "Thermal-lined."},
        ],
        "quests": [{"id": "quiet-signal", "title": "The Quiet Signal", "status": "active", "objectives": [{"description": "Find the payer", "done": False}]}],
        "scene": {"tags": [], "present_npcs": [], "established_facts": []},
    }


# ---------------------------------------------------------------------------
# Fake Ollama helpers
# ---------------------------------------------------------------------------


class _FakeOllama:
    """Context manager that replaces engine's ollama functions.

    ollama_chat_stream is an async generator in the real code, so fake_stream
    must also be an async generator (uses `yield`).
    ollama_chat is a regular async function, so fake_chat uses `return`.

    Captures all calls so tests can assert on message shapes.
    text_responses[0] = narrative text (yielded by stream)
    text_responses[1:] = extract responses (returned by chat)
    """

    def __init__(self, text_responses: list[str], should_fail: bool = False):
        self.call_log: list[dict] = []
        self.narrative = text_responses[0] if text_responses else ""
        self.text_responses = text_responses
        self.should_fail = should_fail
        self._orig_stream = None
        self._orig_chat = None
        # We need a reference to self inside the closures
        _self = self

        async def _fake_stream(*args, **kwargs):
            """Async generator replacing ollama_chat_stream."""
            _self.call_log.append({"kind": "stream", "args": args, "kwargs": kwargs})
            yield _self.narrative

        async def _fake_chat(*args, **kwargs):
            """Regular async function replacing ollama_chat."""
            _self.call_log.append({"kind": "chat", "args": args, "kwargs": kwargs})
            extract_call_num = sum(1 for c in _self.call_log if c["kind"] == "chat")
            if _self.should_fail and extract_call_num == 1:
                return {"response": "this is not valid json at all {{{{", "done": True, "usage": {}}
            result_text = _self.text_responses[-1] if len(_self.text_responses) > 1 else _self.narrative
            return {"response": result_text, "done": True, "usage": {"prompt_tokens": 100, "total_tokens": 200}}

        self._fake_stream = _fake_stream
        self._fake_chat = _fake_chat

    def __enter__(self):
        self._orig_stream = ccya.engine.ollama_chat_stream
        self._orig_chat = ccya.engine.ollama_chat
        ccya.engine.ollama_chat_stream = self._fake_stream
        ccya.engine.ollama_chat = self._fake_chat
        return self

    def __exit__(self, *exc_info):
        ccya.engine.ollama_chat_stream = self._orig_stream
        ccya.engine.ollama_chat = self._orig_chat

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
# TestOllamaBodyShape — Critical fix #5, #6
# ---------------------------------------------------------------------------


class TestOllamaBodyShape:
    """_build_body must place temperature/num_ctx under options{}, keep_alive top-level."""

    def test_options_wraps_temperature_and_num_ctx(self):
        body = _build_body("m", [], temperature=0.8, num_ctx=4096, keep_alive="30m")
        assert "options" in body
        assert body["options"]["temperature"] == 0.8
        assert body["options"]["num_ctx"] == 4096

    def test_keep_alive_is_top_level(self):
        body = _build_body("m", [], temperature=0.5, num_ctx=1024, keep_alive="60m")
        assert body["keep_alive"] == "60m"
        assert "keep_alive" not in body.get("options", {})

    def test_temperature_not_at_top_level(self):
        body = _build_body("m", [], temperature=0.8, num_ctx=1024)
        assert "temperature" not in body

    def test_no_options_if_no_sampling_params(self):
        body = _build_body("m", [])
        assert "options" not in body

    def test_format_is_top_level(self):
        schema = {"type": "object"}
        body = _build_body("m", [], format=schema)
        assert body["format"] == schema
        assert "format" not in body.get("options", {})


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

    def test_extract_has_system_assistant_user_roles(self):
        env = self._env()
        msgs = _extract_messages(env, "The airlock opened.")
        roles = [m["role"] for m in msgs]
        assert roles == ["system", "assistant", "user"]

    def test_extract_assistant_message_is_narrative(self):
        env = self._env()
        narrative = "You step through the airlock. The corridor hums."
        msgs = _extract_messages(env, narrative)
        assistant_msg = next(m for m in msgs if m["role"] == "assistant")
        assert narrative in assistant_msg["content"]

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
            "state_delta": {"established_facts": ["You found an airlock at Docking Ring 7."]},
            "actions": ["Go left", "Go right", "Check your terminal", "Wait"],
            "scene_tags": ["exploration"],
        })

        fake = _FakeOllama([narrative, extract])
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
            "state_delta": {},
            "actions": ["Open door", "Take stairs", "Check map", "Go back"],
            "scene_tags": ["exploration"],
        })
        fake = _FakeOllama(["narrative text", extract])
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
            "scene_tags": [],
        })
        fake = _FakeOllama(["hello world", extract])
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
        extract = json.dumps({"state_delta": {}, "actions": ["A", "B", "C", "D"], "scene_tags": []})
        fake = _FakeOllama(["the narrative", extract])
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
            "scene_tags": [],
        })
        fake = _FakeOllama([extract])
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
            "scene_tags": [],
        })
        fake = _FakeOllama([extract])
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
            "scene_tags": [],
        })
        fake = _FakeOllama([extract])
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
            "scene_tags": [],
        })
        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": "bad json {{{", "done": True, "usage": {}}
            return {"response": good_extract, "done": True, "usage": {"prompt_tokens": 10, "total_tokens": 20}}

        _orig_stream = ccya.engine.ollama_chat_stream
        _orig_chat = ccya.engine.ollama_chat
        try:
            ccya.engine.ollama_chat_stream = fake_stream
            ccya.engine.ollama_chat = fake_chat
            result = await _run(SAVE_DIR, "examine", config=EngineConfig(max_extract_retries=1))
        finally:
            ccya.engine.ollama_chat_stream = _orig_stream
            ccya.engine.ollama_chat = _orig_chat

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
            "state_delta": {"established_facts": ["The airlock hums with residual charge."]},
            "actions": ["A", "B", "C", "D"],
            "scene_tags": [],
        })
        fake = _FakeOllama([extract])
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

        async def fake_chat(*args, **kwargs):
            return {"response": json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []}), "done": True, "usage": {}}

        import ccya.engine as eng
        _orig_stream, _orig_chat = eng.ollama_chat_stream, eng.ollama_chat
        try:
            eng.ollama_chat_stream = fake_stream
            eng.ollama_chat = fake_chat
            await _run(SAVE_DIR, "look", config=EngineConfig(chronicle_prefix_budget_tokens=1500))
        finally:
            eng.ollama_chat_stream = _orig_stream
            eng.ollama_chat = _orig_chat

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

    def test_location_change(self) -> None:
        state = _make_state()
        delta = StateDelta(location_change={"id": "concourse-b", "name": "Concourse B", "description": "Wide and bright."})
        updated = apply_delta(state, delta)
        assert updated["location"]["id"] == "concourse-b"

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

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []})
        fake = _FakeOllama([extract])
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())

        assert result.turn == 1

    async def test_sequential_turns_increment_cleanly(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []})
        fake = _FakeOllama([extract, extract])
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
            "state_delta": {"established_facts": ["turn-1-fact"]},
            "actions": ["A","B","C","D"],
            "scene_tags": [],
        })
        fake = _FakeOllama([extract])
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

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []})
        fake = _FakeOllama(["the narrative text", extract])
        with fake:
            await _run(SAVE_DIR, "my action", config=EngineConfig())

        chronicle = (SAVE_DIR / "chronicle.md").read_text()
        assert "## Turn 1" in chronicle
        assert "my action" in chronicle
        assert "the narrative text" in chronicle


# ---------------------------------------------------------------------------
# TestTurnResultTraceId
# ---------------------------------------------------------------------------


class TestTurnResultTraceId:

    async def test_unique_trace_ids(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)
        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []})
        fake = _FakeOllama([extract, extract])
        with fake:
            r1 = await _run(SAVE_DIR, "first", config=EngineConfig())
            r2 = await _run(SAVE_DIR, "second", config=EngineConfig())

        assert r1.trace_id != r2.trace_id
        assert len(r1.trace_id) > 0


# ---------------------------------------------------------------------------
# TestFactDeduplication
# ---------------------------------------------------------------------------


class TestFactDeduplication:

    def test_dedup(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["fact one", "fact two"]
        delta = StateDelta(established_facts=["fact one", "fact three"])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert facts.count("fact one") == 1
        assert "fact three" in facts
        assert "fact two" in facts


class TestEstablishedFactsEviction:

    def test_eviction(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["f1", "f2", "f3", "f4", "f5"]
        delta = StateDelta(established_facts=["f6", "f7", "f8", "f9", "f10", "f11"])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["established_facts"]
        assert len(facts) <= 10
        assert "f11" in facts
        assert "f1" not in facts


class TestApplyDeltaEstablishedFactsMax:

    def test_custom_max_wired(self) -> None:
        state = _make_state()
        state["scene"]["established_facts"] = ["f1"]
        delta = StateDelta(established_facts=["f2", "f3", "f4"])
        updated = apply_delta(state, delta, established_facts_max=2)
        facts = updated["scene"]["established_facts"]
        assert len(facts) <= 2
        assert "f4" in facts


# ---------------------------------------------------------------------------
# TestPerTurnMetrics
# ---------------------------------------------------------------------------


class TestPerTurnMetrics:

    async def test_metrics_keys_present(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []})
        fake = _FakeOllama(["narrative", extract])
        with fake:
            result = await _run(SAVE_DIR, "test", config=EngineConfig())

        assert "narrate" in result.metrics
        assert "extract" in result.metrics
        assert "first_token_ms" in result.metrics["narrate"]
        assert "total_ms" in result.metrics["narrate"]
        assert "tokens_in" in result.metrics["extract"]
        assert "tokens_out" in result.metrics["extract"]

    async def test_narrate_metrics_do_not_have_token_counts(self) -> None:
        """Narrate metrics must NOT carry extract token counts (was a copy-paste bug)."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []})
        fake = _FakeOllama(["narrative", extract])
        with fake:
            result = await _run(SAVE_DIR, "test", config=EngineConfig())

        # narrate metrics should only have timing keys
        narrate_keys = set(result.metrics["narrate"].keys())
        assert narrate_keys == {"first_token_ms", "total_ms"}


# ---------------------------------------------------------------------------
# TestEstablishedFactsInEvent
# ---------------------------------------------------------------------------


class TestEstablishedFactsInEvent:

    async def test_event_has_established_facts(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        extract = json.dumps({
            "state_delta": {"established_facts": ["This fact matters."]},
            "actions": ["A","B","C","D"],
            "scene_tags": [],
        })
        fake = _FakeOllama([extract])
        with fake:
            await _run(SAVE_DIR, "test", config=EngineConfig())

        events = (SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[-1])
        assert "This fact matters." in event.get("established_facts", [])


# ---------------------------------------------------------------------------
# TestRecentTurnsInjected
# ---------------------------------------------------------------------------


class TestRecentTurnsInjected:
    """After a turn is played, the next turn's prompt should include it."""

    async def test_recent_turn_in_next_narrate_system(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)
        (SAVE_DIR / "events.jsonl").touch()
        (SAVE_DIR / "chronicle.md").touch()

        # Write a prior event manually
        append_event(SAVE_DIR, {
            "ts": "2026-01-01T00:00:00Z",
            "trace_id": "aabbccdd",
            "turn": 0,
            "input": "I examine the signal",
            "narrative": "The signal pulses orange.",
            "applied": {},
            "rejected": [],
            "actions": [],
            "scene_tags": [],
            "established_facts": [],
        })

        captured_system = []

        async def fake_stream(*args, **kwargs):
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            for m in msgs:
                if m.get("role") == "system":
                    captured_system.append(m["content"])
            yield "narrative"

        async def fake_chat(*args, **kwargs):
            return {"response": json.dumps({"state_delta": {}, "actions": ["A","B","C","D"], "scene_tags": []}), "done": True, "usage": {}}

        import ccya.engine as eng
        _orig_stream, _orig_chat = eng.ollama_chat_stream, eng.ollama_chat
        try:
            eng.ollama_chat_stream = fake_stream
            eng.ollama_chat = fake_chat
            await _run(SAVE_DIR, "go north", config=EngineConfig(window_turns=6))
        finally:
            eng.ollama_chat_stream = _orig_stream
            eng.ollama_chat = _orig_chat

        combined = " ".join(captured_system)
        assert "I examine the signal" in combined or "The signal pulses orange" in combined
