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

from ccya.engine import (
    EngineConfig,
    run_turn,
    _build_jinja_env,
    _narrate_messages,
    _extract_scene_messages,
    _extract_state_messages,
    _extract_progress_messages,
)
from ccya.llm_client import strip_thinking
from ccya.models import (
    CompendiumNpcUpdate,
    ConditionAdd,
    ConditionRemove,
    LocationRef,
    RecentEventUpdate,
    InventoryItem,
    InventoryRemove,
    InventoryUpdate,
    NpcRef,
    QuestObjectiveUpdate,
    QuestUpdate,
    SceneExtractResult,
    StateExtractResult,
    StateDelta,
)

# Rules Call 0 returns this when no check is required (default for most tests).
_RULES_NO_ROLL = json.dumps(
    {
        "intent": "player action",
        "intent_verb": "act",
        "target": "",
        "stakes": "",
        "check": {"required": False},
        "scope": {
            "active_domains": ["scene", "present_npcs"],
            "skip_domains": [],
            "implicit_preconditions": [],
            "ambiguities": [],
        },
    }
)
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
            "stats": {
                "strength": 2,
                "dexterity": 2,
                "wits": 3,
                "lore": 2,
                "charisma": 2,
                "resolve": 2,
            },
            "conditions": [],
        },
        "location": {
            "id": "docking-ring-7",
            "name": "Docking Ring 7",
            "description": "Low-grav berth.",
        },
        "inventory": [
            {
                "id": "hand-terminal",
                "name": "Hand terminal",
                "notes": "Cracked screen.",
            },
            {"id": "vac-jacket", "name": "Vac jacket", "notes": "Thermal-lined."},
        ],
        "quests": [
            {
                "id": "quiet-signal",
                "title": "The Quiet Signal",
                "status": "active",
                "objectives": [{"description": "Find the payer", "done": False}],
            }
        ],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


# ---------------------------------------------------------------------------
# Fake LLM helpers — mock ccya.engine.llm_chat / ccya.engine.llm_chat_stream
# ---------------------------------------------------------------------------


_SCENE_RESPONSE = json.dumps({
    "scene_tags": ["exploration"],
    "scene_tagline": "Quiet corridor stretches ahead",
    "location_change": None,
    "location_description": None,
    "present_npcs": [],
    "actions": ["Look around carefully", "Check the panels", "Listen at the door", "Go back"],
    "outcome_summary": "You step through the airlock into silence.",
})

_STATE_RESPONSE = json.dumps({
    "inventory_add": [],
    "inventory_remove": [],
    "inventory_update": [],
    "pc_condition_add": [],
    "pc_condition_remove": [],
    "failed": [],
})

_PROGRESS_RESPONSE = json.dumps({
    "quest_updates": [],
    "recent_events_add": [],
    "recent_events_update": [],
    "recent_events_remove": [],
    "compendium_npc_update": [],
})


class _FakeLLM:
    """Context manager that replaces engine's llm_chat / llm_chat_stream.

    Call ordering per turn:
      chat 1  = rules (always returns _RULES_NO_ROLL)
      stream  = narrate (yields narrative text)
      chat 2  = extract_scene
      chat 3  = extract_state
      chat 4  = extract_progress

    Constructor args:
      narrative       = text streamed for narration (default "narrative text")
      scene_response  = JSON for extract_scene (default _SCENE_RESPONSE)
      state_response  = JSON for extract_state (default _STATE_RESPONSE)
      progress_response = JSON for extract_progress (default _PROGRESS_RESPONSE)

    Legacy: if a single text_responses list is passed, text_responses[0]=narrative,
    text_responses[1]=scene, text_responses[2]=state, text_responses[3]=progress.
    """

    def __init__(
        self,
        text_responses: list[str] | None = None,
        *,
        narrative: str = "narrative text",
        scene_response: str = _SCENE_RESPONSE,
        state_response: str = _STATE_RESPONSE,
        progress_response: str = _PROGRESS_RESPONSE,
    ):
        if text_responses is not None:
            narrative = text_responses[0] if len(text_responses) > 0 else narrative
            scene_response = text_responses[1] if len(text_responses) > 1 else scene_response
            state_response = text_responses[2] if len(text_responses) > 2 else state_response
            progress_response = text_responses[3] if len(text_responses) > 3 else progress_response

        self.call_log: list[dict] = []
        self.narrative = narrative
        self._scene_response = scene_response
        self._state_response = state_response
        self._progress_response = progress_response
        self._orig_stream = None
        self._orig_chat = None
        _self = self

        async def _fake_stream(*args, **kwargs):
            _self.call_log.append({"kind": "stream", "args": args, "kwargs": kwargs})
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield _self.narrative

        async def _fake_chat(*args, **kwargs):
            _self.call_log.append({"kind": "chat", "args": args, "kwargs": kwargs})
            chat_calls = [c for c in _self.call_log if c["kind"] == "chat"]
            n = len(chat_calls)
            if n == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {"prompt_tokens": 30, "total_tokens": 40}}
            if n == 2:
                return {"response": _self._scene_response, "done": True, "usage": {"prompt_tokens": 100, "total_tokens": 200}}
            if n == 3:
                return {"response": _self._state_response, "done": True, "usage": {"prompt_tokens": 80, "total_tokens": 160}}
            # n == 4+: progress (and any retries)
            return {"response": _self._progress_response, "done": True, "usage": {"prompt_tokens": 90, "total_tokens": 180}}

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
    async for kind, payload in run_turn(
        save_dir,
        user_input,
        config=config,
        template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
    ):
        if kind == "complete":
            result = payload
    return result


async def _run_with_tokens(save_dir, user_input, config=None):
    """Collect all token events and the final TurnResult."""
    tokens = []
    result = None
    async for kind, payload in run_turn(
        save_dir,
        user_input,
        config=config,
        template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
    ):
        if kind == "token":
            tokens.append(payload)
        elif kind == "complete":
            result = payload
    return tokens, result


# ---------------------------------------------------------------------------
# TestParseActionsFromNarrate
# ---------------------------------------------------------------------------



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
    """Prompt message shape tests for narrate and per-stream extract builders."""

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

    # --- extract_scene ---

    def test_extract_scene_has_system_user_roles(self):
        env = self._env()
        msgs = _extract_scene_messages(env, "The airlock opened.", _make_state())
        assert [m["role"] for m in msgs] == ["system", "user"]

    def test_extract_scene_user_contains_narration(self):
        env = self._env()
        narrative = "You step through the airlock. The corridor hums."
        msgs = _extract_scene_messages(env, narrative, _make_state())
        user = next(m for m in msgs if m["role"] == "user")
        assert narrative in user["content"]

    def test_extract_scene_system_has_output_schema(self):
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", _make_state())
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "## Output schema" in system
        assert "scene_tags" in system
        assert "present_npcs" in system
        assert "actions" in system
        assert "outcome_summary" in system

    def test_extract_scene_no_inventory_or_quests(self):
        """Scene stream must not include inventory or quest sections."""
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", _make_state())
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "inventory" not in user.lower()
        assert "quest" not in user.lower()

    def test_extract_scene_thinking_toggle(self):
        env = self._env()
        off = _extract_scene_messages(env, "N.", _make_state(), enable_thinking=False)
        on = _extract_scene_messages(env, "N.", _make_state(), enable_thinking=True)
        assert not off[-1]["content"].endswith("/think")
        assert on[-1]["content"].endswith("/think")

    # --- extract_state ---

    def test_extract_state_has_system_user_roles(self):
        env = self._env()
        scene = SceneExtractResult()
        msgs = _extract_state_messages(env, "N.", _make_state(), scene_result=scene)
        assert [m["role"] for m in msgs] == ["system", "user"]

    def test_extract_state_user_contains_inventory(self):
        env = self._env()
        state = _make_state()
        scene = SceneExtractResult()
        msgs = _extract_state_messages(env, "N.", state, scene_result=scene)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "hand-terminal" in user

    def test_extract_state_user_contains_conditions(self):
        env = self._env()
        state = _make_state()
        state["pc"]["conditions"] = [{"id": "injured", "label": "injured", "description": "", "added_turn": 0}]
        scene = SceneExtractResult()
        msgs = _extract_state_messages(env, "N.", state, scene_result=scene)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "injured" in user

    def test_extract_state_system_byte_stable_across_turns(self):
        """System prompt for extract_state must not vary turn-to-turn (cache stability)."""
        env = self._env()
        scene = SceneExtractResult()
        # Two states with different scene/inventory/conditions/rules outcome
        s1 = _make_state(turn=0)
        s2 = _make_state(turn=5)
        s2["pc"]["conditions"] = [{"id": "wounded", "label": "wounded", "description": "hit", "added_turn": 4}]
        from ccya.models import RulesOutcome
        roll = RulesOutcome(rolled=True, skill="strength", difficulty="hard", final_total=8, band="mixed", directive="The strike succeeds with cost.")
        m1 = _extract_state_messages(env, "N1", s1, scene_result=scene)
        m2 = _extract_state_messages(env, "N2", s2, scene_result=scene, rules_outcome=roll)
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2

    def test_extract_state_user_has_quantity_discipline(self):
        env = self._env()
        scene = SceneExtractResult()
        msgs = _extract_state_messages(env, "N.", _make_state(), scene_result=scene)
        system = next(m for m in msgs if m["role"] == "system")["content"]
        # Quantity exactness lives in the system prompt as a static rule.
        assert "Quantities are exact" in system

    def test_extract_state_expired_conditions_shown(self):
        env = self._env()
        scene = SceneExtractResult()
        expired = [{"id": "bruised_ribs", "label": "bruised ribs"}]
        msgs = _extract_state_messages(
            env, "N.", _make_state(), scene_result=scene, engine_expired_conditions=expired
        )
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "engine_expired_conditions" in user
        assert "bruised ribs" in user

    # --- extract_progress ---

    def test_extract_progress_has_system_user_roles(self):
        env = self._env()
        scene = SceneExtractResult()
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(env, "N.", _make_state(), scene_result=scene, state_result=state_res)
        assert [m["role"] for m in msgs] == ["system", "user"]

    def test_extract_progress_user_contains_quests(self):
        env = self._env()
        scene = SceneExtractResult()
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(env, "N.", _make_state(), scene_result=scene, state_result=state_res)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "quiet-signal" in user
        assert "The Quiet Signal" in user

    def test_extract_progress_user_contains_recent_events(self):
        env = self._env()
        state = _make_state()
        state["scene"]["recent_events"] = ["Alpha fact.", "Beta fact."]
        scene = SceneExtractResult()
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(env, "N.", state, scene_result=scene, state_result=state_res)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "Alpha fact." in user
        assert "Beta fact." in user

    def test_extract_progress_world_state_only_when_no_quests(self):
        """World state block appears in progress user only when there are no active quests."""
        env = self._env()
        state = _make_state()
        state["scene"]["world_state"] = ["WORLD_FACT_MARKER"]
        scene = SceneExtractResult()
        state_res = StateExtractResult()

        # With active quest: world state should NOT appear
        msgs_with_quest = _extract_progress_messages(env, "N.", state, scene_result=scene, state_result=state_res)
        user_with_quest = next(m for m in msgs_with_quest if m["role"] == "user")["content"]
        assert "WORLD_FACT_MARKER" not in user_with_quest

        # Without quests: world state SHOULD appear
        state_no_quests = {**state, "quests": []}
        msgs_no_quest = _extract_progress_messages(env, "N.", state_no_quests, scene_result=scene, state_result=state_res)
        user_no_quest = next(m for m in msgs_no_quest if m["role"] == "user")["content"]
        assert "WORLD_FACT_MARKER" in user_no_quest

    def test_extract_progress_user_has_quest_threshold_directive(self):
        """quest_threshold_directive is computed in engine and lives in user prompt."""
        env = self._env()
        scene = SceneExtractResult()
        state_res = StateExtractResult()

        state_no_q = {**_make_state(), "quests": []}
        msgs = _extract_progress_messages(env, "N.", state_no_q, scene_result=scene, state_result=state_res)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "quest_threshold" in user
        assert "LOW" in user

        state_many_q = {**_make_state(), "quests": [
            {"id": f"q{i}", "title": f"Q{i}", "status": "active", "objectives": []} for i in range(3)
        ]}
        msgs2 = _extract_progress_messages(env, "N.", state_many_q, scene_result=scene, state_result=state_res)
        user2 = next(m for m in msgs2 if m["role"] == "user")["content"]
        assert "HIGH" in user2

    def test_extract_progress_system_byte_stable_across_quest_count(self):
        """The progress system prompt must not vary with active_quests count."""
        env = self._env()
        scene = SceneExtractResult()
        state_res = StateExtractResult()
        s_no = {**_make_state(), "quests": []}
        s_many = {**_make_state(), "quests": [
            {"id": f"q{i}", "title": f"Q{i}", "status": "active", "objectives": []} for i in range(3)
        ]}
        m_no = _extract_progress_messages(env, "N.", s_no, scene_result=scene, state_result=state_res)
        m_many = _extract_progress_messages(env, "N.", s_many, scene_result=scene, state_result=state_res)
        sys_no = next(m for m in m_no if m["role"] == "system")["content"]
        sys_many = next(m for m in m_many if m["role"] == "system")["content"]
        assert sys_no == sys_many

    # --- Narrate-specific ---

    def test_narrate_last_turn_failed(self):
        env = self._env()
        state = _make_state()
        failed = ["tried to pick up keys but guard is still conscious"]
        msgs = _narrate_messages(env, state, "look", last_turn_failed=failed)
        user_text = next(m for m in msgs if m["role"] == "user")["content"]
        system_text = next(m for m in msgs if m["role"] == "system")["content"]
        assert "last_turn_failed" in user_text
        assert "tried to pick up keys but guard is still conscious" in user_text
        assert "tried to pick up keys" not in system_text

    def test_narrate_no_last_turn_failed_when_empty(self):
        env = self._env()
        state = _make_state()
        msgs = _narrate_messages(env, state, "look", last_turn_failed=[])
        user_text = next(m for m in msgs if m["role"] == "user")["content"]
        assert "last_turn_failed" not in user_text

    def test_narrate_thinking_toggle(self):
        env = self._env()
        off = _narrate_messages(env, _make_state(), "look", enable_narrate_thinking=False)
        on = _narrate_messages(env, _make_state(), "look", enable_narrate_thinking=True)
        assert not off[-1]["content"].endswith("/think")
        assert on[-1]["content"].endswith("/think")

    def test_strip_thinking_removes_thinking_block(self):
        raw = "<think>\n- bullet\n</think>\n\nYou step through."
        assert strip_thinking(raw).strip() == "You step through."

    def test_chronicle_injected_when_present(self):
        env = self._env()
        state = _make_state()
        chronicle_tail = "Earlier, Vex found a dead comms relay."
        msgs = _narrate_messages(env, state, "look", chronicle_tail=chronicle_tail)
        user_text = next(m for m in msgs if m["role"] == "user")["content"]
        system_text = next(m for m in msgs if m["role"] == "system")["content"]
        assert "Earlier, Vex found a dead comms relay." in user_text
        assert "Earlier, Vex found a dead comms relay." not in system_text

    def test_recent_turns_injected_when_present(self):
        env = self._env()
        state = _make_state()
        recent = [{"turn": 1, "input": "look around", "narrative": "You see a docking bay."}]
        msgs = _narrate_messages(env, state, "go forward", recent_turns=recent)
        user_text = next(m for m in msgs if m["role"] == "user")["content"]
        assert "look around" in user_text

    def test_chronicle_absent_when_empty(self):
        env = self._env()
        state = _make_state()
        msgs = _narrate_messages(env, state, "look", chronicle_tail="")
        user_text = next(m for m in msgs if m["role"] == "user")["content"]
        assert "Earlier" not in user_text

    def test_narrate_system_byte_stable_across_turns(self):
        """The narrate system prompt must not vary turn-to-turn within the same pack."""
        env = self._env()
        state1 = _make_state(turn=0)
        state2 = _make_state(turn=5)
        state2["scene"]["recent_events"] = ["some new fact"]
        from ccya.models import RulesOutcome
        roll = RulesOutcome(rolled=True, skill="strength", difficulty="hard", final_total=8, band="mixed", directive="The strike succeeds with cost.")
        m1 = _narrate_messages(env, state1, "look", pack_style="dark sci-fi")
        m2 = _narrate_messages(
            env, state2, "examine", pack_style="dark sci-fi",
            chronicle_tail="prior arc", rules_outcome=roll,
            last_turn_failed=["did not succeed"], npc_name_pool=["Anna", "Bo"],
        )
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2


# ---------------------------------------------------------------------------
# TestHappyPath
# ---------------------------------------------------------------------------


class TestHappyPath:
    async def test_narrate_and_extract(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You step through the airlock. The corridor stretches ahead, dim and humming."
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": ["You found an airlock at Docking Ring 7."],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })

        fake = _FakeLLM(narrative=narrative, progress_response=progress_response)
        with fake:
            result = await _run(
                SAVE_DIR, "I step through the airlock.", config=EngineConfig()
            )

        assert result.narrative == narrative
        assert result.recent_events == ["You found an airlock at Docking Ring 7."]
        assert result.metrics["narrate"]["total_ms"] >= 0
        assert result.metrics["extract"]["total_ms"] >= 0
        assert len(result.errors) == 0
        assert result.turn == 1

    async def test_actions_captured_from_scene_stream(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        scene_response = json.dumps({
            "scene_tags": ["exploration"],
            "scene_tagline": "Dim corridors ahead",
            "location_change": None,
            "location_description": None,
            "present_npcs": [],
            "actions": ["Open door", "Take stairs", "Check map", "Go back"],
            "outcome_summary": "You looked around carefully.",
        })
        fake = _FakeLLM(scene_response=scene_response)
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())

        assert result.actions == ["Open door", "Take stairs", "Check map", "Go back"]

    async def test_actions_empty_when_not_in_scene_response(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        scene_response = json.dumps({
            "scene_tags": ["exploration"],
            "scene_tagline": "Quiet",
            "location_change": None,
            "location_description": None,
            "present_npcs": [],
            "actions": [],
            "outcome_summary": "",
        })
        fake = _FakeLLM(narrative="narrative text without actions", scene_response=scene_response)
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())

        assert result.actions == []


# ---------------------------------------------------------------------------
# TestStreamingEvents — Critical fix #1
# ---------------------------------------------------------------------------


class TestStreamingEvents:
    """run_turn must yield ("token", str) events before ("complete", TurnResult)."""

    async def test_yields_token_events(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        fake = _FakeLLM(narrative="hello world")
        with fake:
            tokens, result = await _run_with_tokens(
                SAVE_DIR, "look", config=EngineConfig()
            )

        assert len(tokens) >= 1
        assert "".join(tokens) == "hello world"
        assert result is not None
        assert result.narrative == "hello world"

    async def test_complete_comes_after_tokens(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        events = []
        fake = _FakeLLM(narrative="the narrative")
        with fake:
            async for kind, _ in run_turn(
                SAVE_DIR,
                "look",
                config=EngineConfig(),
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

        state_response = json.dumps({
            "inventory_add": [],
            "inventory_remove": [{"id": "ghost-item-999"}],
            "inventory_update": [],
            "pc_condition_add": [],
            "pc_condition_remove": [],
            "failed": [],
        })
        fake = _FakeLLM(state_response=state_response)
        with fake:
            result = await _run(
                SAVE_DIR, "I grab the ghost item.", config=EngineConfig()
            )

        assert len(result.rejected) == 1
        assert result.rejected[0]["value"] == "ghost-item-999"
        assert "does not exist" in result.rejected[0]["reason"]
        assert len(result.errors) > 0

    async def test_trace_id_in_narrative_on_rejection(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        state_response = json.dumps({
            "inventory_add": [],
            "inventory_remove": [{"id": "ghost-item"}],
            "inventory_update": [],
            "pc_condition_add": [],
            "pc_condition_remove": [],
            "failed": [],
        })
        fake = _FakeLLM(state_response=state_response)
        with fake:
            result = await _run(SAVE_DIR, "grab ghost", config=EngineConfig())

        assert result.trace_id in result.narrative

    async def test_update_nonexistent_quest_creates_it(self) -> None:
        """quest_updates is create-or-update: unknown quest IDs should be created, not rejected."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        progress_response = json.dumps({
            "quest_updates": [{"id": "new-quest", "title": "New Quest", "status": "active", "objectives": []}],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(progress_response=progress_response)
        with fake:
            result = await _run(SAVE_DIR, "Start a new quest.", config=EngineConfig())

        assert not any(r.get("field") == "quest_updates" for r in result.rejected)
        saved = load_state(SAVE_DIR)
        quest_ids = {q.get("id") for q in saved.get("quests", [])}
        assert "new-quest" in quest_ids


# ---------------------------------------------------------------------------
# TestSchemaFailureRetry
# ---------------------------------------------------------------------------


class TestSchemaFailureRetry:
    async def test_scene_stream_retry(self) -> None:
        """Scene stream retries on bad JSON; second attempt succeeds."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        narrative = "You examine the hand terminal closely."
        good_scene = _SCENE_RESPONSE
        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            yield narrative

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            if chat_call_count == 2:
                # First scene attempt — bad JSON
                return {"response": "bad json {{{", "done": True, "usage": {}}
            if chat_call_count == 3:
                # Retry: good scene
                return {"response": good_scene, "done": True, "usage": {"prompt_tokens": 10, "total_tokens": 200}}
            # state + progress — return defaults
            if chat_call_count == 4:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _orig_stream = ccya.engine.llm_chat_stream
        _orig_chat = ccya.engine.llm_chat
        try:
            ccya.engine.llm_chat_stream = fake_stream
            ccya.engine.llm_chat = fake_chat
            result = await _run(
                SAVE_DIR, "examine", config=EngineConfig(max_extract_retries=1)
            )
        finally:
            ccya.engine.llm_chat_stream = _orig_stream
            ccya.engine.llm_chat = _orig_chat

        assert len(result.errors) == 0
        assert result.scene_tags == ["exploration"]


# ---------------------------------------------------------------------------
# TestFactCanonization
# ---------------------------------------------------------------------------


class TestFactCanonization:
    async def test_facts_in_state(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": ["The airlock hums with residual charge."],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(progress_response=progress_response)
        with fake:
            await _run(SAVE_DIR, "Touch the airlock.", config=EngineConfig())

        loaded = load_state(SAVE_DIR)
        facts = loaded.get("scene", {}).get("recent_events", [])
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
            if _chat_calls_chron == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            if _chat_calls_chron == 3:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        import ccya.engine as eng

        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = fake_stream
            eng.llm_chat = fake_chat
            await _run(
                SAVE_DIR,
                "look",
                config=EngineConfig(chronicle_prefix_budget_tokens=1500),
            )
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        all_texts = " ".join(m.get("content", "") for m in captured_messages)
        assert "MARKER_TEXT_FOR_ASSERTION" in all_texts


# ---------------------------------------------------------------------------
# TestStateApplyDelta
# ---------------------------------------------------------------------------


class TestStateApplyDelta:
    def test_inventory_add(self) -> None:
        state = _make_state()
        delta = StateDelta(
            inventory_add=[
                {"id": "plasma-cutter", "name": "Plasma cutter", "notes": "Hot."}
            ]
        )
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
            "inventory": [
                {"id": "credits", "name": "Credits", "amount": 100, "notes": "Cash."}
            ],
        }
        delta = StateDelta(
            inventory_add=[
                InventoryItem(id="credits", name="Credits", amount=50, notes="Cash.")
            ],
        )
        updated = apply_delta(state, delta)
        cred = next(i for i in updated["inventory"] if i["id"] == "credits")
        assert cred["amount"] == 150

    def test_inventory_remove_partial_amount(self) -> None:
        state = {
            **_make_state(),
            "inventory": [
                {"id": "credits", "name": "Credits", "amount": 1800, "notes": ""}
            ],
        }
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=500)])
        updated = apply_delta(state, delta)
        cred = next(i for i in updated["inventory"] if i["id"] == "credits")
        assert cred["amount"] == 1300

    def test_inventory_remove_full_stack_when_amount_exhausts(self) -> None:
        state = {
            **_make_state(),
            "inventory": [
                {"id": "credits", "name": "Credits", "amount": 100, "notes": ""}
            ],
        }
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=100)])
        updated = apply_delta(state, delta)
        assert "credits" not in [i["id"] for i in updated["inventory"]]

    def test_credits_sort_to_top(self) -> None:
        state = {
            **_make_state(),
            "inventory": [
                {
                    "id": "hand-terminal",
                    "name": "Hand terminal",
                    "amount": 1,
                    "notes": "",
                },
                {"id": "credits", "name": "Credits", "amount": 50, "notes": ""},
            ],
        }
        updated = apply_delta(state, StateDelta())
        assert updated["inventory"][0]["id"] == "credits"

    def test_location_change(self) -> None:
        state = _make_state()
        delta = StateDelta(
            location_change={
                "id": "concourse-b",
                "name": "Concourse B",
                "description": "Wide and bright.",
            }
        )
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
        assert (
            len(updated["inventory"]) == 3
        )  # hand-terminal, vac-jacket, merged water stack
        wf = next(
            i
            for i in updated["inventory"]
            if "water" in i["id"].lower() or "filter" in i["id"].lower()
        )
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

        fake = _FakeLLM()
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig())

        assert result.turn == 1

    async def test_sequential_turns_increment_cleanly(self) -> None:
        state = _make_state(turn=0)
        _write_state(SAVE_DIR, state)

        fake = _FakeLLM()
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

        fake = _FakeLLM()
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

        fake = _FakeLLM(narrative="the narrative text")
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
        fake = _FakeLLM()
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
        state["scene"]["recent_events"] = ["fact one", "fact two"]
        delta = StateDelta(recent_events_add=["fact three"])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert facts == ["fact one", "fact two", "fact three"]

    def test_empty_delta_noop(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = ["keep me"]
        delta = StateDelta()
        updated = apply_delta(state, delta)
        assert updated["scene"]["recent_events"] == ["keep me"]

    def test_update_preserves_position(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = ["alpha", "beta", "gamma"]
        delta = StateDelta(
            recent_events_update=[RecentEventUpdate(old="beta", new="beta revised")],
        )
        updated = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert facts[1] == "beta revised"
        assert facts[0] == "alpha"

    def test_remove_normalized_match(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = ["  The Ship is damaged.  ", "Other fact."]
        delta = StateDelta(recent_events_remove=["The Ship is damaged."])
        updated = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert "Other fact." in facts
        assert not any("damaged" in f for f in facts)

    def test_update_fallback_appends_when_old_missing(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = ["only"]
        delta = StateDelta(
            recent_events_update=[
                RecentEventUpdate(old="no such fact", new="appended instead")
            ],
        )
        updated = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert facts == ["only", "appended instead"]


class TestEstablishedFactsEviction:
    def test_eviction(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = ["f1", "f2", "f3", "f4", "f5"]
        delta = StateDelta(recent_events_add=["f6", "f7", "f8", "f9", "f10", "f11"])
        updated = apply_delta(state, delta, recent_events_max=10)
        facts = updated["scene"]["recent_events"]
        assert len(facts) <= 10
        assert "f11" in facts
        assert "f1" not in facts


class TestPcConditionsDelta:
    def test_add_and_remove_structured(self) -> None:
        state = _make_state()
        delta = StateDelta(pc_condition_add=[
            ConditionAdd(id="wanted", label="wanted"),
            ConditionAdd(id="injured", label="injured", description="Hit by debris."),
        ])
        updated = apply_delta(state, delta)
        cond_ids = [c["id"] for c in updated["pc"]["conditions"]]
        assert "wanted" in cond_ids and "injured" in cond_ids

        delta2 = StateDelta(pc_condition_remove=[ConditionRemove(id="wanted")])
        updated2 = apply_delta(updated, delta2)
        cond_ids2 = [c["id"] for c in updated2["pc"]["conditions"]]
        assert "wanted" not in cond_ids2
        assert "injured" in cond_ids2

    def test_string_coercion_to_structured(self) -> None:
        """Plain strings in pc_condition_add are coerced to ConditionAdd dicts."""
        state = _make_state()
        delta = StateDelta(pc_condition_add=["wanted", "injured"])
        updated = apply_delta(state, delta)
        conds = updated["pc"]["conditions"]
        assert all(isinstance(c, dict) for c in conds)
        ids = [c["id"] for c in conds]
        assert "wanted" in ids and "injured" in ids

    def test_id_dedup(self) -> None:
        """Duplicate id is rejected on add regardless of label wording."""
        state = _make_state()
        state["pc"]["conditions"] = [{"id": "bruised_ribs", "label": "bruised ribs", "description": "", "added_turn": 0}]
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="bruised_ribs", label="Bruised Ribs")])
        updated = apply_delta(state, delta)
        assert len(updated["pc"]["conditions"]) == 1

    def test_cap_at_5_evicts_oldest(self) -> None:
        """When more than 5 conditions accumulate, oldest is dropped FIFO."""
        state = _make_state()
        state["pc"]["conditions"] = [
            {"id": f"c{i}", "label": f"c{i}", "description": "", "added_turn": i}
            for i in range(1, 6)
        ]
        delta = StateDelta(pc_condition_add=[
            ConditionAdd(id="c6", label="c6"),
            ConditionAdd(id="c7", label="c7"),
        ])
        updated = apply_delta(state, delta)
        conds = updated["pc"]["conditions"]
        assert len(conds) == 5
        ids = [c["id"] for c in conds]
        assert "c7" in ids and "c6" in ids
        assert "c1" not in ids and "c2" not in ids

    def test_added_turn_stamped_by_apply_delta(self) -> None:
        """apply_delta stamps added_turn = state.meta.turn on each new condition."""
        state = _make_state(turn=5)
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="shaken", label="shaken")])
        updated = apply_delta(state, delta)
        cond = next(c for c in updated["pc"]["conditions"] if c["id"] == "shaken")
        assert cond["added_turn"] == 5


class TestConditionTTL:
    async def test_ttl_expires_old_condition(self) -> None:
        """Conditions older than condition_ttl_turns are removed before extraction."""
        state = _make_state(turn=4)
        state["pc"]["conditions"] = [
            {"id": "old_wound", "label": "old wound", "description": "", "added_turn": 0}
        ]
        _write_state(SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            result = await _run(SAVE_DIR, "look", config=EngineConfig(condition_ttl_turns=4))

        saved = load_state(SAVE_DIR)
        cond_ids = [c["id"] if isinstance(c, dict) else c for c in saved["pc"]["conditions"]]
        assert "old_wound" not in cond_ids

    async def test_recent_condition_survives_ttl(self) -> None:
        """A condition added last turn (age 1) should not expire with TTL=4."""
        state = _make_state(turn=2)
        state["pc"]["conditions"] = [
            {"id": "bruised", "label": "bruised", "description": "", "added_turn": 1}
        ]
        _write_state(SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            await _run(SAVE_DIR, "look", config=EngineConfig(condition_ttl_turns=4))

        saved = load_state(SAVE_DIR)
        cond_ids = [c["id"] if isinstance(c, dict) else c for c in saved["pc"]["conditions"]]
        assert "bruised" in cond_ids


class TestExtractionStreamSkip:
    async def test_state_stream_skipped_when_all_state_domains_skipped(self) -> None:
        """When inventory and pc_condition are both in skip_domains, only 3 chat calls occur
        (rules + scene + progress — state is omitted)."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        rules_with_skip = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
            "scope": {
                "active_domains": ["scene", "quest_updates", "recent_events"],
                "skip_domains": ["inventory", "pc_condition"],
                "implicit_preconditions": [],
                "ambiguities": [],
            },
        })

        chat_call_count = 0
        chat_responses: list[str] = []

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_with_skip, "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            # 3rd call should be progress (state is skipped)
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _orig_stream, _orig_chat = ccya.engine.llm_chat_stream, ccya.engine.llm_chat
        try:
            ccya.engine.llm_chat_stream = fake_stream
            ccya.engine.llm_chat = fake_chat
            result = await _run(SAVE_DIR, "look", config=EngineConfig())
        finally:
            ccya.engine.llm_chat_stream = _orig_stream
            ccya.engine.llm_chat = _orig_chat

        # rules(1) + scene(2) + progress(3) — no state call
        assert chat_call_count == 3
        assert len(result.errors) == 0


class TestEstablishedFactsCap25:
    def test_cap_at_25(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [f"f{i}" for i in range(24)]
        delta = StateDelta(recent_events_add=["f24", "f25", "f26"])
        updated = apply_delta(state, delta, recent_events_max=25)
        facts = updated["scene"]["recent_events"]
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
            quest_updates=[
                QuestUpdate(id="quiet-signal", status="completed", objectives=[])
            ],
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
        delta = StateDelta(
            quest_updates=[
                QuestUpdate(id="quiet-signal", status="failed", objectives=[])
            ]
        )
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["status"] == "failed"
        objs = {o["description"]: o for o in q["objectives"]}
        assert objs["A"]["done"] is True
        assert objs["B"].get("failed") is True

    def test_abandoned_does_not_auto_fail_objectives(self) -> None:
        state = _make_state()
        state["quests"][0]["objectives"] = [
            {"description": "Find the payer", "done": False}
        ]
        delta = StateDelta(
            quest_updates=[
                QuestUpdate(id="quiet-signal", status="abandoned", objectives=[])
            ]
        )
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
            quest_updates=[
                QuestUpdate(
                    id="quiet-signal",
                    objectives=[QuestObjectiveUpdate(index=1, done=True)],
                )
            ],
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
                    objectives=[
                        QuestObjectiveUpdate(
                            index=99, description="Find the payer", done=True
                        )
                    ],
                ),
            ],
        )
        updated = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["objectives"][0]["done"] is True


class TestApplyDeltaEstablishedFactsMax:
    def test_custom_max_wired(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = ["f1"]
        delta = StateDelta(recent_events_add=["f2", "f3", "f4"])
        updated = apply_delta(state, delta, recent_events_max=2)
        facts = updated["scene"]["recent_events"]
        assert len(facts) <= 2
        assert facts == ["f3", "f4"]


class TestInventoryCompendiumTagline:
    def test_inventory_update_changes_notes(self) -> None:
        state = _make_state()
        delta = StateDelta(
            inventory_update=[InventoryUpdate(id="vac-jacket", notes="Patched.")]
        )
        out = apply_delta(state, delta)
        item = next(x for x in out["inventory"] if x["id"] == "vac-jacket")
        assert item["notes"] == "Patched."

    def test_inventory_update_unknown_id_skipped(self) -> None:
        state = _make_state()
        before = len(state["inventory"])
        delta = StateDelta(
            inventory_update=[InventoryUpdate(id="nope-item", notes="x")]
        )
        out = apply_delta(state, delta)
        assert len(out["inventory"]) == before

    def test_npc_bio_mirrored_to_compendium(self) -> None:
        state = _make_state()
        delta = StateDelta(
            present_npcs=[
                NpcRef(
                    id="fixer",
                    name="Anna",
                    title="Fence",
                    notes="Watching.",
                    bio="Owes you from Tycho.",
                ),
            ],
        )
        out = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["fixer"]["bio"] == "Owes you from Tycho."

    def test_npc_bio_preserved_when_bio_empty_in_delta(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
            "bio": "Old bio.",
        }
        delta = StateDelta(
            present_npcs=[
                NpcRef(
                    id="fixer", name="Anna", title="Fence", notes="New mood.", bio=""
                ),
            ],
        )
        out = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["fixer"]["bio"] == "Old bio."

    def test_present_npcs_id_and_notes_only_hydrates_from_compendium(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
            "bio": "Stored dossier.",
        }
        delta = StateDelta(
            present_npcs=[NpcRef(id="fixer", notes="Suspicious tonight.")]
        )
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
            compendium_npc_update=[
                CompendiumNpcUpdate(id="missing-wife", bio="Seen on Ganymede.")
            ],
        )
        out = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["missing_wife"]["bio"] == "Seen on Ganymede."

    def test_recently_left_computed_when_npcs_leave(self) -> None:
        """NPCs removed from present_npcs should appear in recently_left."""
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
            "bio": "Owes you.",
        }
        state["compendium"]["npcs"]["bouncer"] = {
            "name": "Kweku",
            "title": "Doorman",
        }
        state["scene"]["present_npcs"] = [
            {"id": "fixer", "name": "Anna", "title": "Fence", "notes": "Watching."},
            {"id": "bouncer", "name": "Kweku", "title": "Doorman", "notes": "Arms crossed."},
        ]
        delta = StateDelta(
            present_npcs=[
                NpcRef(id="fixer", notes="Nodding at you."),
            ],
        )
        out = apply_delta(state, delta)
        recently_left = out["scene"]["recently_left"]
        assert len(recently_left) == 1
        assert recently_left[0]["id"] == "bouncer"
        assert recently_left[0]["name"] == "Kweku"
        assert recently_left[0]["title"] == "Doorman"
        assert out["scene"]["recently_left_turns"] == 2

    def test_recently_left_excludes_returnees(self) -> None:
        """NPCs that left and came back should NOT appear in recently_left."""
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
        }
        state["scene"]["present_npcs"] = [
            {"id": "fixer", "name": "Anna", "title": "Fence", "notes": "Watching."},
            {"id": "bouncer", "name": "Kweku", "title": "Doorman", "notes": "Arms crossed."},
        ]
        delta = StateDelta(
            present_npcs=[
                NpcRef(id="fixer", notes="Nodding."),
                NpcRef(id="bouncer", notes="Stepping aside."),
            ],
        )
        out = apply_delta(state, delta)
        assert out["scene"].get("recently_left") in ([], None)

    def test_recently_left_cleared_on_location_change(self) -> None:
        """Moving to a new location should clear recently_left."""
        state = _make_state()
        state["scene"]["present_npcs"] = [
            {"id": "fixer", "name": "Anna", "title": "Fence", "notes": "Watching."},
        ]
        state["scene"]["recently_left"] = [
            {"id": "bouncer", "name": "Kweku", "title": "Doorman"},
        ]
        state["scene"]["recently_left_turns"] = 1
        delta = StateDelta(
            present_npcs=[NpcRef(id="fixer", notes="At the new place.")],
            location_change=LocationRef(id="new-station", name="New Station", description="Bright lights."),
        )
        out = apply_delta(state, delta)
        assert out["scene"]["recently_left"] == []
        assert out["scene"]["recently_left_turns"] == 0

    def test_recently_left_uses_compendium_for_npc_info(self) -> None:
        """recently_left entries should pull name/title from compendium."""
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
        }
        state["scene"]["present_npcs"] = [
            {"id": "fixer", "name": "Anna", "title": "Fence", "notes": "Watching."},
        ]
        delta = StateDelta(
            present_npcs=[],
        )
        out = apply_delta(state, delta)
        recently_left = out["scene"]["recently_left"]
        assert len(recently_left) == 1
        assert recently_left[0]["id"] == "fixer"
        assert recently_left[0]["name"] == "Anna"
        assert recently_left[0]["title"] == "Fence"

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
            "meta": {
                "turn": 0,
                "game_name": "t",
                "setting_pack": "",
                "model": "",
                "compendium_touch_order": [],
            },
            "pc": {
                "name": "A",
                "tagline": "",
                "stats": {"body": 2, "mind": 3, "tech": 2, "social": 3},
                "conditions": [],
            },
            "location": {"id": "", "name": "", "description": ""},
            "inventory": [],
            "quests": [],
            "scene": {
                "tags": [],
                "present_npcs": [],
                "recent_events": [],
                "tagline": "",
            },
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
            "scene": {"tags": [], "present_npcs": [], "recent_events": []},
        }
        ls_save(tmp_path, raw)
        st = ls_load(tmp_path)
        assert st["pc"]["tagline"] == "old pitch"
        assert "concept" not in st["pc"]

    async def test_turn_result_includes_diff_lines(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": ["A fact."],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(narrative="short narrative.", progress_response=progress_response)
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

        fake = _FakeLLM()
        with fake:
            result = await _run(SAVE_DIR, "test", config=EngineConfig())

        assert "narrate" in result.metrics
        assert "extract" in result.metrics
        assert "first_token_ms" in result.metrics["narrate"]
        assert "total_ms" in result.metrics["narrate"]
        assert "tokens_in" in result.metrics["extract"]
        assert "tokens_out" in result.metrics["extract"]

    async def test_narrate_token_counts_from_streaming_stats(self) -> None:
        """Narrate token counts come from streaming stats (42/24 from fake)."""
        state = _make_state()
        _write_state(SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            result = await _run(SAVE_DIR, "test", config=EngineConfig())

        narr = result.metrics["narrate"]
        assert narr.get("tokens_in") == 42
        assert narr.get("tokens_out") == 24


# ---------------------------------------------------------------------------
# TestEstablishedFactsInEvent
# ---------------------------------------------------------------------------


class TestEstablishedFactsInEvent:
    async def test_event_has_facts_add_in_applied_no_narrative_key(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": ["This fact matters."],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(progress_response=progress_response)
        with fake:
            await _run(SAVE_DIR, "test", config=EngineConfig())

        events = (SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[-1])
        applied_add = event.get("applied", {}).get("recent_events_add", [])
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

        captured_messages: list[str] = []

        async def fake_stream(*args, **kwargs):
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            for m in msgs:
                captured_messages.append(m.get("content", ""))
            yield "narrative"

        _chat_calls_recent = 0

        async def fake_chat(*args, **kwargs):
            nonlocal _chat_calls_recent
            _chat_calls_recent += 1
            if _chat_calls_recent == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            if _chat_calls_recent == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            if _chat_calls_recent == 3:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        import ccya.engine as eng

        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = fake_stream
            eng.llm_chat = fake_chat
            await _run(SAVE_DIR, "go north", config=EngineConfig(window_turns=6))
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        combined = " ".join(captured_messages)
        assert (
            "I examine the signal" in combined or "The signal pulses orange" in combined
        )


# ---------------------------------------------------------------------------
# TestPackKwargs — pack_style and pack_examples wired through run_turn
# ---------------------------------------------------------------------------


class TestPackKwargs:
    """pack_style appears in narrate system; pack_examples appear in extract system."""

    async def test_pack_style_in_narrate_system(self) -> None:
        state = _make_state()
        _write_state(SAVE_DIR, state)

        captured_narrate_system = []

        async def _fake_stream(*args, **kwargs):
            msgs = args[2] if len(args) > 2 else kwargs.get("messages", [])
            for m in msgs:
                if m.get("role") == "system":
                    captured_narrate_system.append(m["content"])
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative"

        _narrate_chat_calls = 0

        async def _fake_chat(*args, **kwargs):
            nonlocal _narrate_chat_calls
            _narrate_chat_calls += 1
            if _narrate_chat_calls == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            if _narrate_chat_calls == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            if _narrate_chat_calls == 3:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        import ccya.engine as eng

        _orig_stream, _orig_chat = eng.llm_chat_stream, eng.llm_chat
        try:
            eng.llm_chat_stream = _fake_stream
            eng.llm_chat = _fake_chat
            async for _ in run_turn(
                SAVE_DIR,
                "look",
                config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
                pack_style="UNIQUE_STYLE_MARKER_7483",
            ):
                pass
        finally:
            eng.llm_chat_stream = _orig_stream
            eng.llm_chat = _orig_chat

        assert any("UNIQUE_STYLE_MARKER_7483" in s for s in captured_narrate_system)
