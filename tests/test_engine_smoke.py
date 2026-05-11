"""Smoke tests for ccya engine — no real LLM needed.

Notable design decisions captured here:
- Turn counter increments in engine.py ONLY (not in apply_delta).
- run_turn() is an async generator: yields ("token", str)* then ("complete", TurnResult).
- LLM client is OpenAI-compatible (mlx_lm.server). Tests mock at the
  ccya.engine.llm_chat / ccya.llm_client.chat_stream level — both return the
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
    _expire_scene_pressures,
)
from ccya.llm_client import strip_thinking
from ccya.models import (
    CompendiumNpcUpdate,
    ConditionAdd,
    ConditionRemove,
    LocationRef,
    NpcAdd,
    NpcRemove,
    NpcUpdate,
    RecentEvent,
    RecentEventUpdate,
    InventoryItem,
    InventoryRemove,
    InventoryUpdate,
    QuestObjectiveUpdate,
    QuestUpdate,
    StateExtractResult,
    StateDelta,
)
from ccya.state import (
    apply_delta,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_state,
    save_state,
)

# ---------------------------------------------------------------------------
# Test fixtures / constants
# ---------------------------------------------------------------------------

# Rules Call 0 returns this when no check is required (default for most tests).
_RULES_NO_ROLL = json.dumps(
    {
        "intent": "player action",
        "intent_verb": "act",
        "target": "",
        "stakes": "",
        "check": {"required": False},
    }
)

_SAVE_DIR = Path(tempfile.mkdtemp())


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
            "last_compacted_turn": 0,
            "prior_history": "",
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
        "scene": {"tags": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


def _make_state_with_events(events: list[dict]) -> dict:
    state = _make_state()
    state["scene"]["recent_events"] = events
    return state


# ---------------------------------------------------------------------------
# Fake LLM helpers — mock ccya.engine.llm_chat / ccya.llm_client.chat_stream
# ---------------------------------------------------------------------------


_SCENE_RESPONSE = json.dumps({
    "scene_tags": ["exploration"],
    "scene_tagline": "Quiet corridor stretches ahead",
    "location_change": None,
    "location_description": None,
    "npc_add": [],
    "npc_remove": [],
    "npc_update": [],
    "compendium_npc_update": [],
})

_STATE_RESPONSE = json.dumps({
    "inventory_add": [],
    "inventory_remove": [],
    "inventory_update": [],
    "pc_condition_add": [],
    "pc_condition_remove": [],
})

_PROGRESS_RESPONSE = json.dumps({
    "quest_updates": [],
    "recent_events_add": [],
    "recent_events_update": [],
    "recent_events_remove": [],
    "actions": [],
    "outcome_summary": "",
})


def _make_recent_event(event_id: str, text: str, turn: int = 0) -> dict:
    return {"id": event_id, "text": text, "turn": turn}


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
        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        self._mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        self._origs = {}
        for mod in self._mods:
            if hasattr(mod, "llm_chat"):
                self._origs[mod] = ("llm_chat", mod.llm_chat)
                mod.llm_chat = self._fake_chat
            if hasattr(mod, "llm_chat_stream"):
                self._origs[mod] = ("llm_chat_stream", mod.llm_chat_stream)
                mod.llm_chat_stream = self._fake_stream
        return self

    def __exit__(self, *exc_info):
        for mod, (name, orig) in self._origs.items():
            setattr(mod, name, orig)

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
    if _SAVE_DIR.exists():
        for f in _SAVE_DIR.iterdir():
            f.unlink()
    _SAVE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    for f in _SAVE_DIR.iterdir():
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
        assert "Scene Extractor" in system
        assert "scene_tags" in system
        assert "NPC" in system
        assert "location_change" in system
        assert "compendium_npc_update" in system

    def test_extract_scene_no_inventory(self):
        """Scene stream must not include inventory sections."""
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", _make_state())
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "inventory" not in user.lower()

    def test_extract_scene_system_has_location_checklist(self):
        """System prompt mentions location description as one of four responsibilities."""
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", _make_state())
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "Location description" in system

    def test_extract_scene_system_has_npc_compendium_check(self):
        """System prompt mentions NPC presence as a responsibility."""
        env = self._env()
        msgs = _extract_scene_messages(env, "N.", _make_state())
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "NPC" in system or "npc" in system

    # --- inventory capitalization ---

    def test_capitalize_inventory_names_lowercase(self):
        from ccya.engine.extraction import _capitalize_inventory_names
        items = [InventoryItem(id="brass_key", name="brass key", amount=1), InventoryItem(id="worn_dagger", name="worn dagger", amount=1)]
        _capitalize_inventory_names(items)
        assert items[0].name == "Brass key"
        assert items[1].name == "Worn dagger"

    def test_capitalize_inventory_names_already_capitalized(self):
        from ccya.engine.extraction import _capitalize_inventory_names
        items = [InventoryItem(id="brass_key", name="Brass key", amount=1)]
        _capitalize_inventory_names(items)
        assert items[0].name == "Brass key"

    def test_capitalize_inventory_names_empty_name(self):
        from ccya.engine.extraction import _capitalize_inventory_names
        items = [InventoryItem(id="empty", name="", amount=1)]
        _capitalize_inventory_names(items)
        assert items[0].name == ""

    # --- extract_state ---

    def test_extract_state_has_system_user_roles(self):
        env = self._env()
        msgs = _extract_state_messages(env, "N.", _make_state())
        assert [m["role"] for m in msgs] == ["system", "user"]

    def test_extract_state_user_contains_inventory(self):
        env = self._env()
        state = _make_state()
        msgs = _extract_state_messages(env, "N.", state)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "hand-terminal" in user

    def test_extract_state_user_contains_conditions(self):
        env = self._env()
        state = _make_state()
        state["pc"]["conditions"] = [{"id": "injured", "label": "injured", "description": "", "added_turn": 0}]
        msgs = _extract_state_messages(env, "N.", state)
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "injured" in user

    def test_extract_state_system_byte_stable_across_turns(self):
        """System prompt for extract_state must not vary turn-to-turn (cache stability)."""
        env = self._env()
        # Two states with different scene/inventory/conditions/rules outcome
        s1 = _make_state(turn=0)
        s2 = _make_state(turn=5)
        s2["pc"]["conditions"] = [{"id": "wounded", "label": "wounded", "description": "hit", "added_turn": 4}]
        from ccya.models import RulesOutcome
        RulesOutcome(rolled=True, skill="strength", difficulty="hard", final_total=8, band="partial", directive="The strike succeeds with cost.")
        m1 = _extract_state_messages(env, "N1", s1)
        m2 = _extract_state_messages(env, "N2", s2)
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2

    def test_extract_state_user_has_quantity_discipline(self):
        env = self._env()
        msgs = _extract_state_messages(env, "N.", _make_state())
        system = next(m for m in msgs if m["role"] == "system")["content"]
        # Quantity exactness lives in the system prompt as a static rule.
        assert "Quantities are exact" in system

    def test_extract_state_system_has_generic_item_mapping(self):
        """System prompt must contain explicit generic item mapping rule."""
        env = self._env()
        msgs = _extract_state_messages(env, "N.", _make_state())
        system = next(m for m in msgs if m["role"] == "system")["content"]
        assert "generic item mapping" in system.lower() or "generic denomination" in system.lower()
        assert "NEVER invent" in system

    # --- extract_progress ---

    def test_extract_progress_has_system_user_roles(self):
        env = self._env()
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(env, "N.", _make_state(), state_result=state_res, intent=None, recent_turns=[])
        assert [m["role"] for m in msgs] == ["system", "user"]

    def test_extract_progress_user_contains_quests(self):
        env = self._env()
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(env, "N.", _make_state(), state_result=state_res, intent=None, recent_turns=[])
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "quiet-signal" in user
        assert "The Quiet Signal" in user

    def test_extract_progress_user_contains_recent_events(self):
        env = self._env()
        state = _make_state()
        state["scene"]["recent_events"] = [
            _make_recent_event("alpha", "Alpha fact."),
            _make_recent_event("beta", "Beta fact."),
        ]
        state_res = StateExtractResult()
        msgs = _extract_progress_messages(env, "N.", state, state_result=state_res, intent=None, recent_turns=[])
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "Alpha fact." in user
        assert "Beta fact." in user

    def test_extract_progress_world_state_only_when_no_quests(self):
        """World state block appears in progress user only when there are no active quests."""
        env = self._env()
        state = _make_state()
        state["scene"]["world_state"] = ["WORLD_FACT_MARKER"]
        state_res = StateExtractResult()

        # With active quest: world state should NOT appear
        msgs_with_quest = _extract_progress_messages(env, "N.", state, state_result=state_res, intent=None, recent_turns=[])
        user_with_quest = next(m for m in msgs_with_quest if m["role"] == "user")["content"]
        assert "WORLD_FACT_MARKER" not in user_with_quest

        # Without quests: world state SHOULD appear
        state_no_quests = {**state, "quests": []}
        msgs_no_quest = _extract_progress_messages(env, "N.", state_no_quests, state_result=state_res, intent=None, recent_turns=[])
        user_no_quest = next(m for m in msgs_no_quest if m["role"] == "user")["content"]
        assert "WORLD_FACT_MARKER" in user_no_quest

    def test_extract_progress_user_has_quest_threshold_directive(self):
        """quest_threshold_directive is computed in engine and lives in user prompt."""
        env = self._env()
        state_res = StateExtractResult()

        state_no_q = {**_make_state(), "quests": []}
        msgs = _extract_progress_messages(env, "N.", state_no_q, state_result=state_res, intent=None, recent_turns=[])
        user = next(m for m in msgs if m["role"] == "user")["content"]
        assert "quest_threshold" in user
        assert "LOW" in user

        state_many_q = {**_make_state(), "quests": [
            {"id": f"q{i}", "title": f"Q{i}", "status": "active", "objectives": []} for i in range(3)
        ]}
        msgs2 = _extract_progress_messages(env, "N.", state_many_q, state_result=state_res, intent=None, recent_turns=[])
        user2 = next(m for m in msgs2 if m["role"] == "user")["content"]
        assert "HIGH" in user2

    def test_extract_progress_system_byte_stable_across_quest_count(self):
        """The progress system prompt must not vary with active_quests count."""
        env = self._env()
        state_res = StateExtractResult()
        s_no = {**_make_state(), "quests": []}
        s_many = {**_make_state(), "quests": [
            {"id": f"q{i}", "title": f"Q{i}", "status": "active", "objectives": []} for i in range(3)
        ]}
        m_no = _extract_progress_messages(env, "N.", s_no, state_result=state_res, intent=None, recent_turns=[])
        m_many = _extract_progress_messages(env, "N.", s_many, state_result=state_res, intent=None, recent_turns=[])
        sys_no = next(m for m in m_no if m["role"] == "system")["content"]
        sys_many = next(m for m in m_many if m["role"] == "system")["content"]
        assert sys_no == sys_many

    # --- Narrate-specific ---

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
        assert "T1:" in user_text
        assert "You see a docking bay" in user_text

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
        state2["scene"]["recent_events"] = [_make_recent_event("some_fact", "some new fact")]
        from ccya.models import RulesOutcome
        roll = RulesOutcome(rolled=True, skill="strength", difficulty="hard", final_total=8, band="partial", directive="The strike succeeds with cost.")
        m1 = _narrate_messages(env, state1, "look", pack_style="dark sci-fi")
        m2 = _narrate_messages(
            env, state2, "examine", pack_style="dark sci-fi",
            chronicle_tail="prior arc", rules_outcome=roll,
            npc_name_pool=["Anna", "Bo"],
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
        _write_state(_SAVE_DIR, state)

        narrative = "You step through the airlock. The corridor stretches ahead, dim and humming."
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [{"id": "airlock_found", "text": "You found an airlock at Docking Ring 7.", "turn": 0}],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })

        fake = _FakeLLM(narrative=narrative, progress_response=progress_response)
        with fake:
            result = await _run(
                _SAVE_DIR, "I step through the airlock.", config=EngineConfig()
            )

        assert result.narrative == narrative
        assert len(result.recent_events) == 1
        assert result.recent_events[0].text == "You found an airlock at Docking Ring 7."
        assert result.metrics["narrate"]["total_ms"] >= 0
        assert result.metrics["extract"]["total_ms"] >= 0
        assert len(result.errors) == 0
        assert result.turn == 1

    async def test_actions_captured_from_progress_stream(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        scene_response = json.dumps({
            "scene_tags": ["exploration"],
            "scene_tagline": "Dim corridors ahead",
            "location_change": None,
            "location_description": None,
            "npc_add": [],
            "npc_remove": [],
            "npc_update": [],
            "compendium_npc_update": [],
        })
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": ["Open door", "Take stairs", "Check map", "Go back"],
            "outcome_summary": "You looked around carefully.",
        })
        fake = _FakeLLM(scene_response=scene_response, progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result.actions == ["Open door", "Take stairs", "Check map", "Go back"]

    async def test_actions_empty_when_not_in_progress_response(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        scene_response = json.dumps({
            "scene_tags": ["exploration"],
            "scene_tagline": "Quiet",
            "location_change": None,
            "location_description": None,
            "npc_add": [],
            "npc_remove": [],
            "npc_update": [],
            "compendium_npc_update": [],
        })
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "actions": [],
            "outcome_summary": "",
        })
        fake = _FakeLLM(narrative="narrative text without actions", scene_response=scene_response, progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result.actions == []


# ---------------------------------------------------------------------------
# TestStreamingEvents — Critical fix #1
# ---------------------------------------------------------------------------


class TestStreamingEvents:
    """run_turn must yield ("token", str) events before ("complete", TurnResult)."""

    async def test_yields_token_events(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        fake = _FakeLLM(narrative="hello world")
        with fake:
            tokens, result = await _run_with_tokens(
                _SAVE_DIR, "look", config=EngineConfig()
            )

        assert len(tokens) >= 1
        assert "".join(tokens) == "hello world"
        assert result is not None
        assert result.narrative == "hello world"

    async def test_complete_comes_after_tokens(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        events = []
        fake = _FakeLLM(narrative="the narrative")
        with fake:
            async for kind, _ in run_turn(
                _SAVE_DIR,
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
        _write_state(_SAVE_DIR, state)

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
                _SAVE_DIR, "I grab the ghost item.", config=EngineConfig()
            )

        assert len(result.rejected) == 1
        assert result.rejected[0]["value"] == "ghost-item-999"
        assert "does not exist" in result.rejected[0]["reason"]
        assert len(result.errors) > 0

    async def test_trace_id_in_narrative_on_rejection(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

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
            result = await _run(_SAVE_DIR, "grab ghost", config=EngineConfig())

        assert result.trace_id in result.narrative

    async def test_update_nonexistent_quest_creates_it(self) -> None:
        """quest_updates is create-or-update: unknown quest IDs should be created, not rejected."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        progress_response = json.dumps({
            "quest_updates": [{"id": "new-quest", "title": "New Quest", "status": "active", "objectives": []}],
            "recent_events_add": [],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "Start a new quest.", config=EngineConfig())

        assert not any(r.get("field") == "quest_updates" for r in result.rejected)
        saved = load_state(_SAVE_DIR)
        quest_ids = {q.get("id") for q in saved.get("quests", [])}
        assert "new-quest" in quest_ids


# ---------------------------------------------------------------------------
# TestSchemaFailureRetry
# ---------------------------------------------------------------------------


class TestSchemaFailureRetry:
    async def test_scene_stream_retry(self) -> None:
        """Scene stream retries on bad JSON; second attempt succeeds."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

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

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = await _run(
                _SAVE_DIR, "examine", config=EngineConfig(max_extract_retries=1)
            )
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        assert len(result.errors) == 0
        assert result.scene_tags == ["exploration"]


# ---------------------------------------------------------------------------
# TestFactCanonization
# ---------------------------------------------------------------------------


class TestFactCanonization:
    async def test_facts_in_state(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [{"id": "airlock_hums", "text": "The airlock hums with residual charge.", "turn": 0}],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(progress_response=progress_response)
        with fake:
            await _run(_SAVE_DIR, "Touch the airlock.", config=EngineConfig())

        loaded = load_state(_SAVE_DIR)
        facts = loaded.get("scene", {}).get("recent_events", [])
        assert len(facts) == 1
        assert facts[0]["text"] == "The airlock hums with residual charge."


# ---------------------------------------------------------------------------
# TestChroniclePrefixBudget
# ---------------------------------------------------------------------------


class TestChroniclePrefixBudget:
    def test_chronicle_tail(self) -> None:
        large_text = "This is a sentence. " * 2000
        chronicle = _SAVE_DIR / "chronicle.md"
        chronicle.write_text(large_text)
        tail = load_chronicle_tail(_SAVE_DIR, max_tokens=100)
        words = tail.split()
        assert len(words) <= 100

    async def test_chronicle_injected_in_engine_run(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)
        chronicle = _SAVE_DIR / "chronicle.md"
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

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            await _run(
                _SAVE_DIR,
                "look",
                config=EngineConfig(chronicle_prefix_budget_tokens=1500),
            )
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

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
        updated, _ = apply_delta(state, delta)
        assert "plasma-cutter" in [item["id"] for item in updated["inventory"]]
        assert len(updated["inventory"]) == 3

    def test_inventory_remove(self) -> None:
        state = _make_state()
        delta = StateDelta(inventory_remove=["hand-terminal"])
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, StateDelta())
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
        updated, _ = apply_delta(state, delta)
        assert updated["location"]["id"] == "concourse-b"

    def test_location_description_in_place(self) -> None:
        state = _make_state()
        delta = StateDelta(location_description="The berth lights flicker.")
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
        assert updated["meta"]["turn"] == 5


# ---------------------------------------------------------------------------
# TestTurnCounterSingleIncrement — Critical fix #7
# ---------------------------------------------------------------------------


class TestTurnCounterSingleIncrement:
    """Turn counter increments exactly once per run_turn() call."""

    async def test_single_increment(self) -> None:
        state = _make_state(turn=0)
        _write_state(_SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())

        assert result.turn == 1

    async def test_sequential_turns_increment_cleanly(self) -> None:
        state = _make_state(turn=0)
        _write_state(_SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            r1 = await _run(_SAVE_DIR, "first", config=EngineConfig())
            r2 = await _run(_SAVE_DIR, "second", config=EngineConfig())

        assert r1.turn == 1
        assert r2.turn == 2


# ---------------------------------------------------------------------------
# TestEventWrittenBeforeState
# ---------------------------------------------------------------------------


class TestEventWrittenBeforeState:
    async def test_write_order(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            await _run(_SAVE_DIR, "test", config=EngineConfig())

        events = (_SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        assert len(events) == 1
        event = json.loads(events[0])
        assert event["turn"] == 1
        assert event["input"] == "test"

        loaded = load_state(_SAVE_DIR)
        assert loaded["meta"]["turn"] == 1


# ---------------------------------------------------------------------------
# TestChronicleFormatted
# ---------------------------------------------------------------------------


class TestChronicleFormatted:
    """Chronicle entries are formatted with turn headers."""

    async def test_chronicle_has_turn_header(self) -> None:
        state = _make_state(turn=0)
        _write_state(_SAVE_DIR, state)
        (_SAVE_DIR / "chronicle.md").touch()

        fake = _FakeLLM(narrative="the narrative text")
        with fake:
            await _run(_SAVE_DIR, "my action", config=EngineConfig())

        chronicle = (_SAVE_DIR / "chronicle.md").read_text()
        assert "## Turn 1" in chronicle
        assert "my action" in chronicle
        assert "the narrative text" in chronicle


# ---------------------------------------------------------------------------
# TestChronicleTurnParser
# ---------------------------------------------------------------------------


class TestChronicleTurnParser:
    def test_parses_turn_blocks(self) -> None:
        _write_state(_SAVE_DIR, _make_state())
        (_SAVE_DIR / "chronicle.md").write_text(
            "\n\n## Turn 1 — look\n\nFirst narrative.\n\n## Turn 2 — go north\n\nSecond narrative longer.\n",
        )
        turns = load_recent_chronicle_turns(_SAVE_DIR, 6)
        assert len(turns) == 2
        assert turns[0]["turn"] == 1
        assert turns[0]["input"] == "look"
        assert "First narrative" in turns[0]["narrative"]
        assert turns[1]["turn"] == 2
        assert "Second narrative" in turns[1]["narrative"]

    def test_empty_chronicle(self) -> None:
        _write_state(_SAVE_DIR, _make_state())
        (_SAVE_DIR / "chronicle.md").write_text("")
        assert load_recent_chronicle_turns(_SAVE_DIR, 6) == []

    def test_tolerates_extra_blank_lines(self) -> None:
        _write_state(_SAVE_DIR, _make_state())
        (_SAVE_DIR / "chronicle.md").write_text("\n\n\n## Turn 3 — act\n\n\nBody.\n\n")
        turns = load_recent_chronicle_turns(_SAVE_DIR, 6)
        assert len(turns) == 1
        assert turns[0]["input"] == "act"
        assert turns[0]["narrative"].strip() == "Body."


# ---------------------------------------------------------------------------
# TestTurnResultTraceId
# ---------------------------------------------------------------------------


class TestTurnResultTraceId:
    async def test_unique_trace_ids(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)
        fake = _FakeLLM()
        with fake:
            r1 = await _run(_SAVE_DIR, "first", config=EngineConfig())
            r2 = await _run(_SAVE_DIR, "second", config=EngineConfig())

        assert r1.trace_id != r2.trace_id
        assert len(r1.trace_id) > 0


# ---------------------------------------------------------------------------
# TestFactDeduplication
# ---------------------------------------------------------------------------


class TestFactsDelta:
    def test_add_only(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [
            _make_recent_event("fact-one", "fact one"),
            _make_recent_event("fact-two", "fact two"),
        ]
        delta = StateDelta(recent_events_add=[RecentEvent(id="fact-three", text="fact three")])
        updated, _ = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert len(facts) == 3
        assert facts[2]["text"] == "fact three"

    def test_empty_delta_noop(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [_make_recent_event("keep-me", "keep me")]
        delta = StateDelta()
        updated, _ = apply_delta(state, delta)
        assert updated["scene"]["recent_events"] == [_make_recent_event("keep-me", "keep me")]

    def test_update_by_id(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [
            _make_recent_event("alpha", "alpha"),
            _make_recent_event("beta", "beta"),
            _make_recent_event("gamma", "gamma"),
        ]
        delta = StateDelta(
            recent_events_update=[RecentEventUpdate(id="beta", text="beta revised")],
        )
        updated, _ = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert facts[1]["text"] == "beta revised"
        assert facts[0]["text"] == "alpha"

    def test_remove_by_id(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [
            _make_recent_event("ship-damaged", "  The Ship is damaged.  "),
            _make_recent_event("other-fact", "Other fact."),
        ]
        delta = StateDelta(recent_events_remove=["ship-damaged"])
        updated, _ = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert len(facts) == 1
        assert facts[0]["id"] == "other-fact"

    def test_update_fallback_noop_when_id_missing(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [_make_recent_event("only", "only")]
        delta = StateDelta(
            recent_events_update=[
                RecentEventUpdate(id="no-such-id", text="not appended")
            ],
        )
        updated, _ = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert len(facts) == 1
        assert facts[0]["text"] == "only"

    def test_add_rejects_duplicate_id(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [_make_recent_event("dup", "existing")]
        delta = StateDelta(recent_events_add=[RecentEvent(id="dup", text="duplicate")])
        updated, _ = apply_delta(state, delta)
        facts = updated["scene"]["recent_events"]
        assert len(facts) == 1
        assert facts[0]["text"] == "existing"


class TestEstablishedFactsEviction:
    def test_eviction(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [_make_recent_event(f"f{i}", f"f{i}", turn=i) for i in range(1, 6)]
        delta = StateDelta(recent_events_add=[
            RecentEvent(id=f"f{i}", text=f"f{i}", turn=6) for i in range(6, 12)
        ])
        updated, _ = apply_delta(state, delta, recent_events_max=10)
        facts = updated["scene"]["recent_events"]
        assert len(facts) <= 10
        assert any(f["id"] == "f11" for f in facts)
        assert not any(f["id"] == "f1" for f in facts)


class TestPcConditionsDelta:
    def test_add_and_remove_structured(self) -> None:
        state = _make_state()
        delta = StateDelta(pc_condition_add=[
            ConditionAdd(id="wanted", label="wanted"),
            ConditionAdd(id="injured", label="injured", description="Hit by debris."),
        ])
        updated, _ = apply_delta(state, delta)
        cond_ids = [c["id"] for c in updated["pc"]["conditions"]]
        assert "wanted" in cond_ids and "injured" in cond_ids

        delta2 = StateDelta(pc_condition_remove=[ConditionRemove(id="wanted")])
        updated2, _ = apply_delta(updated, delta2)
        cond_ids2 = [c["id"] for c in updated2["pc"]["conditions"]]
        assert "wanted" not in cond_ids2
        assert "injured" in cond_ids2

    def test_string_coercion_to_structured(self) -> None:
        """Plain strings in pc_condition_add are coerced to ConditionAdd dicts."""
        state = _make_state()
        delta = StateDelta(pc_condition_add=["wanted", "injured"])
        updated, _ = apply_delta(state, delta)
        conds = updated["pc"]["conditions"]
        assert all(isinstance(c, dict) for c in conds)
        ids = [c["id"] for c in conds]
        assert "wanted" in ids and "injured" in ids

    def test_id_dedup(self) -> None:
        """Duplicate id is rejected on add regardless of label wording."""
        state = _make_state()
        state["pc"]["conditions"] = [{"id": "bruised_ribs", "label": "bruised ribs", "description": "", "added_turn": 0}]
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="bruised_ribs", label="Bruised Ribs")])
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
        conds = updated["pc"]["conditions"]
        assert len(conds) == 5
        ids = [c["id"] for c in conds]
        assert "c7" in ids and "c6" in ids
        assert "c1" not in ids and "c2" not in ids

    def test_added_turn_stamped_by_apply_delta(self) -> None:
        """apply_delta stamps added_turn = state.meta.turn on each new condition."""
        state = _make_state(turn=5)
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="shaken", label="shaken")])
        updated, _ = apply_delta(state, delta)
        cond = next(c for c in updated["pc"]["conditions"] if c["id"] == "shaken")
        assert cond["added_turn"] == 5


class TestExtractionStreamSkip:
    async def test_state_stream_skipped_when_all_state_domains_skipped(self) -> None:
        """When narrator emits active_domains without inventory/pc_condition,
        only 3 chat calls occur (rules + scene + progress — state is omitted)."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        rules_no_scope = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative<scope>{\"active_domains\":[\"scene\",\"quest_updates\",\"recent_events\"]}</scope>"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_no_scope, "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            # 3rd call should be progress (state is skipped)
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        # rules(1) + scene(2) + progress(3) — no state call
        assert chat_call_count == 3
        assert len(result.errors) == 0


class TestNarratorScopeStreamSkip:
    """Phase 3 — narrator-emitted <scope> tail drives stream skipping."""

    async def test_empty_scope_skips_scene_and_state_runs_progress(self) -> None:
        """active_domains=[] → only progress runs (rules + stream + progress = 3 stream/chat calls)."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        rules_no_scope = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative<scope>{\"active_domains\":[]}</scope>"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_no_scope, "done": True, "usage": {}}
            # 2nd call should be progress (scene + state are skipped)
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        # rules(1) + progress(2) — scene and state skipped
        assert chat_call_count == 2
        assert len(result.errors) == 0

    async def test_scene_only_runs_scene_and_progress(self) -> None:
        """active_domains=['scene'] → scene + progress, no state."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        rules_no_scope = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative<scope>{\"active_domains\":[\"scene\"]}</scope>"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_no_scope, "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            # 3rd call should be progress (state is skipped)
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        # rules(1) + scene(2) + progress(3) — state skipped
        assert chat_call_count == 3
        assert len(result.errors) == 0

    async def test_state_only_runs_state_and_progress(self) -> None:
        """active_domains=['inventory','pc_condition'] → state + progress, no scene."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        rules_no_scope = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative<scope>{\"active_domains\":[\"inventory\",\"pc_condition\"]}</scope>"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_no_scope, "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            # 3rd call should be progress (scene is skipped)
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        # rules(1) + state(2) + progress(3) — scene skipped
        assert chat_call_count == 3
        assert len(result.errors) == 0

    async def test_default_runs_all_three(self) -> None:
        """No scope tag → defaults applied → all 3 streams run."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        rules_no_scope = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            # No <scope> tag — defaults to all domains
            yield "narrative text"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_no_scope, "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            if chat_call_count == 3:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            # 4th call should be progress
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        # rules(1) + scene(2) + state(3) + progress(4) — all run
        assert chat_call_count == 4
        assert len(result.errors) == 0

    async def test_progress_always_runs_even_with_empty_scope(self) -> None:
        """active_domains=[] still runs progress.

        Verify progress runs (2 chat calls total: rules + progress).
        """
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        rules_no_scope = json.dumps({
            "intent": "observe",
            "intent_verb": "act",
            "target": "",
            "stakes": "",
            "check": {"required": False},
        })

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            yield "narrative<scope>{\"active_domains\":[]}</scope>"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": rules_no_scope, "done": True, "usage": {}}
            # Only progress call after rules
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            await _run(_SAVE_DIR, "look", config=EngineConfig())
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        assert chat_call_count == 2


class TestEstablishedFactsCap25:
    def test_cap_at_25(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [_make_recent_event(f"f{i}", f"f{i}") for i in range(24)]
        delta = StateDelta(recent_events_add=[
            RecentEvent(id=f"f{i}", text=f"f{i}") for i in range(24, 27)
        ])
        updated, _ = apply_delta(state, delta, recent_events_max=25)
        facts = updated["scene"]["recent_events"]
        assert len(facts) == 25
        assert any(f["id"] == "f26" for f in facts)
        assert not any(f["id"] == "f0" for f in facts)


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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
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
        updated, _ = apply_delta(state, delta)
        q = next(x for x in updated["quests"] if x["id"] == "quiet-signal")
        assert q["objectives"][0]["done"] is True


class TestApplyDeltaEstablishedFactsMax:
    def test_custom_max_wired(self) -> None:
        state = _make_state()
        state["scene"]["recent_events"] = [_make_recent_event("f1", "f1")]
        delta = StateDelta(recent_events_add=[
            RecentEvent(id=f"f{i}", text=f"f{i}") for i in range(2, 5)
        ])
        updated, _ = apply_delta(state, delta, recent_events_max=2)
        facts = updated["scene"]["recent_events"]
        assert len(facts) <= 2
        assert facts[-1]["id"] == "f4"


class TestInventoryCompendiumTagline:
    def test_inventory_update_changes_notes(self) -> None:
        state = _make_state()
        delta = StateDelta(
            inventory_update=[InventoryUpdate(id="vac-jacket", notes="Patched.")]
        )
        out, _ = apply_delta(state, delta)
        item = next(x for x in out["inventory"] if x["id"] == "vac-jacket")
        assert item["notes"] == "Patched."

    def test_inventory_update_unknown_id_skipped(self) -> None:
        state = _make_state()
        before = len(state["inventory"])
        delta = StateDelta(
            inventory_update=[InventoryUpdate(id="nope-item", notes="x")]
        )
        out, _ = apply_delta(state, delta)
        assert len(out["inventory"]) == before

    def test_npc_bio_mirrored_to_compendium(self) -> None:
        state = _make_state()
        delta = StateDelta(
            npc_add=[
                NpcAdd(
                    id="fixer",
                    name="Anna",
                    title="Fence",
                    notes="Watching.",
                    bio="Owes you from Tycho.",
                ),
            ],
        )
        out, _ = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["fixer"]["bio"] == "Owes you from Tycho."

    def test_npc_bio_preserved_when_bio_empty_in_delta(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
            "bio": "Old bio.",
        }
        delta = StateDelta(
            npc_add=[
                NpcAdd(
                    id="fixer", name="Anna", title="Fence", notes="New mood.", bio=""
                ),
            ],
        )
        out, _ = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["fixer"]["bio"] == "Old bio."

    def test_npc_add_id_and_notes_only_hydrates_from_compendium(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"]["fixer"] = {
            "name": "Anna",
            "title": "Fence",
            "bio": "Stored dossier.",
        }
        delta = StateDelta(
            npc_add=[NpcAdd(id="fixer", notes="Suspicious tonight.")]
        )
        out, _ = apply_delta(state, delta)
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
        out, _ = apply_delta(state, delta)
        assert out["compendium"]["npcs"]["missing_wife"]["bio"] == "Seen on Ganymede."

    def test_recently_left_computed_when_npcs_leave(self) -> None:
        """NPCs removed via npc_remove should appear in recently_left."""
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
            npc_remove=[NpcRemove(id="bouncer")],
            npc_update=[NpcUpdate(id="fixer", notes="Nodding at you.")],
        )
        out, _ = apply_delta(state, delta)
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
            npc_update=[
                NpcUpdate(id="fixer", notes="Nodding."),
                NpcUpdate(id="bouncer", notes="Stepping aside."),
            ],
        )
        out, _ = apply_delta(state, delta)
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
            npc_update=[NpcUpdate(id="fixer", notes="At the new place.")],
            location_change=LocationRef(id="new-station", name="New Station", description="Bright lights."),
        )
        out, _ = apply_delta(state, delta)
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
            npc_remove=[NpcRemove(id="fixer")],
        )
        out, _ = apply_delta(state, delta)
        recently_left = out["scene"]["recently_left"]
        assert len(recently_left) == 1
        assert recently_left[0]["id"] == "fixer"
        assert recently_left[0]["name"] == "Anna"
        assert recently_left[0]["title"] == "Fence"

    def test_scene_tagline_set(self) -> None:
        state = _make_state()
        delta = StateDelta(scene_tagline="Fees due at dawn")
        out, _ = apply_delta(state, delta)
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
            "scene": {"tags": [], "recent_events": []},
        }
        ls_save(tmp_path, raw)
        st = ls_load(tmp_path)
        assert st["pc"]["tagline"] == "old pitch"
        assert "concept" not in st["pc"]

    async def test_turn_result_includes_diff_lines(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)
        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [{"id": "a-fact", "text": "A fact.", "turn": 0}],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(narrative="short narrative.", progress_response=progress_response)
        with fake:
            result = await _run(_SAVE_DIR, "look", config=EngineConfig())
        assert result.diff
        assert any("A fact" in line for line in result.diff)


# ---------------------------------------------------------------------------
# TestPerTurnMetrics
# ---------------------------------------------------------------------------


class TestPerTurnMetrics:
    async def test_metrics_keys_present(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            result = await _run(_SAVE_DIR, "test", config=EngineConfig())

        assert "narrate" in result.metrics
        assert "extract" in result.metrics
        assert "first_token_ms" in result.metrics["narrate"]
        assert "total_ms" in result.metrics["narrate"]
        assert "tokens_in" in result.metrics["extract"]
        assert "tokens_out" in result.metrics["extract"]

    async def test_narrate_token_counts_from_streaming_stats(self) -> None:
        """Narrate token counts come from streaming stats (42/24 from fake)."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        fake = _FakeLLM()
        with fake:
            result = await _run(_SAVE_DIR, "test", config=EngineConfig())

        narr = result.metrics["narrate"]
        assert narr.get("tokens_in") == 42
        assert narr.get("tokens_out") == 24


# ---------------------------------------------------------------------------
# TestEstablishedFactsInEvent
# ---------------------------------------------------------------------------


class TestEstablishedFactsInEvent:
    async def test_event_has_facts_add_in_applied_no_narrative_key(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        progress_response = json.dumps({
            "quest_updates": [],
            "recent_events_add": [{"id": "fact-matters", "text": "This fact matters.", "turn": 0}],
            "recent_events_update": [],
            "recent_events_remove": [],
            "compendium_npc_update": [],
        })
        fake = _FakeLLM(progress_response=progress_response)
        with fake:
            await _run(_SAVE_DIR, "test", config=EngineConfig())

        events = (_SAVE_DIR / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(events[-1])
        applied_add = event.get("applied", {}).get("recent_events_add", [])
        assert len(applied_add) == 1
        assert applied_add[0]["text"] == "This fact matters."
        assert "narrative" not in event


# ---------------------------------------------------------------------------
# TestRecentTurnsInjected
# ---------------------------------------------------------------------------


class TestRecentTurnsInjected:
    """After a turn is played, the next turn's prompt should include it."""

    async def test_recent_turn_in_next_narrate_system(self) -> None:
        state = _make_state(turn=1)
        _write_state(_SAVE_DIR, state)
        (_SAVE_DIR / "events.jsonl").touch()
        # Prior narrative lives in chronicle.md (canonical); engine reads via load_recent_chronicle_turns
        (_SAVE_DIR / "chronicle.md").write_text(
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

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            await _run(_SAVE_DIR, "go north", config=EngineConfig(window_turns=6))
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        combined = " ".join(captured_messages)
        assert (
            "I examine the signal" in combined or "The signal pulses orange" in combined
        )


# ---------------------------------------------------------------------------
# TestPackKwargs — pack_style wired through run_turn
# ---------------------------------------------------------------------------


class TestPackKwargs:
    """pack_style appears in narrate system."""

    async def test_pack_style_in_narrate_system(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

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

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = _fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = _fake_stream
        try:
            async for _ in run_turn(
                _SAVE_DIR,
                "look",
                config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
                pack_style="UNIQUE_STYLE_MARKER_7483",
            ):
                pass
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        assert not any("UNIQUE_STYLE_MARKER_7483" in s for s in captured_narrate_system)

    async def test_pack_factions_in_narrate_system(self) -> None:
        """Factions from pack.scenario should appear in the narrate system prompt."""
        state = _make_state()
        _write_state(_SAVE_DIR, state)

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

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = _fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = _fake_stream
        try:
            async for _ in run_turn(
                _SAVE_DIR,
                "look",
                config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
                pack_factions=[{"name": "Test Faction", "disposition": "hostile", "description": "A test faction."}],
                pack_locations=[{"name": "Test Location", "type": "settlement", "description": "A test place."}],
                pack_narrator_rules=["Rule one.", "Rule two."],
            ):
                pass
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        assert any("Test Faction" in s for s in captured_narrate_system)
        assert any("hostile" in s for s in captured_narrate_system)
        assert any("Test Location" in s for s in captured_narrate_system)
        assert any("Rule one." in s for s in captured_narrate_system)
        assert any("Rule two." in s for s in captured_narrate_system)


# ---------------------------------------------------------------------------
# TestEntityDedup — alias map, fuzzy match, and dedup in apply_delta
# ---------------------------------------------------------------------------


class TestEntityDedup:
    """Tests for NPC alias map, inventory fuzzy match, and dedup in apply_delta."""

    def test_build_npc_alias_map(self) -> None:
        from ccya.state import build_npc_alias_map

        npcs = {
            "kael_marsh": {
                "name": "Kael Marsh",
                "aliases": ["scarred soldier", "the soldier"],
            },
            "torben_klask": {"name": "Torben Klask", "aliases": []},
        }
        alias_map = build_npc_alias_map(npcs)
        assert alias_map["kael_marsh"] == "kael_marsh"
        assert alias_map["scarred soldier"] == "kael_marsh"
        assert alias_map["the soldier"] == "kael_marsh"
        assert alias_map["torben_klask"] == "torben_klask"
        # Unknown alias not in map
        assert "unknown" not in alias_map

    def test_fuzzy_match_inventory_exact(self) -> None:
        from ccya.state import _fuzzy_match_inventory

        inventory = [
            {"id": "worn_dagger", "name": "Worn Dagger", "aliases": []},
        ]
        result = _fuzzy_match_inventory("worn dagger", inventory)
        assert result == "worn_dagger"

    def test_fuzzy_match_inventory_partial(self) -> None:
        from ccya.state import _fuzzy_match_inventory

        inventory = [
            {"id": "brass_key", "name": "Brass Key", "aliases": []},
        ]
        result = _fuzzy_match_inventory("brass key", inventory)
        assert result == "brass_key"

    def test_fuzzy_match_inventory_below_threshold(self) -> None:
        from ccya.state import _fuzzy_match_inventory

        inventory = [
            {"id": "short_sword", "name": "Short Sword", "aliases": []},
        ]
        result = _fuzzy_match_inventory("long sword", inventory)
        assert result is None

    def test_fuzzy_match_inventory_with_alias(self) -> None:
        from ccya.state import _fuzzy_match_inventory

        inventory = [
            {"id": "worn_dagger", "name": "Worn Dagger", "aliases": ["dagger", "the dagger"]},
        ]
        result = _fuzzy_match_inventory("dagger", inventory)
        assert result == "worn_dagger"

    def test_inventory_add_fuzzy_merge(self) -> None:
        state = _make_state()
        state["inventory"] = [
            {"id": "worn_dagger", "name": "Worn Dagger", "amount": 1, "aliases": []},
        ]
        delta = StateDelta(inventory_add=[InventoryItem(id="dagger", name="Dagger", amount=1)])
        updated, _ = apply_delta(state, delta)
        inv = updated["inventory"]
        assert len(inv) == 1
        assert inv[0]["id"] == "worn_dagger"
        assert inv[0]["amount"] == 2

    def test_inventory_add_with_aliases_merge(self) -> None:
        state = _make_state()
        state["inventory"] = [
            {"id": "worn_dagger", "name": "Worn Dagger", "amount": 1, "aliases": []},
        ]
        delta = StateDelta(inventory_add=[
            InventoryItem(id="dagger", name="Dagger", amount=1, aliases=["the dagger"])
        ])
        updated, _ = apply_delta(state, delta)
        inv = updated["inventory"]
        assert len(inv) == 1
        assert inv[0]["id"] == "worn_dagger"
        assert "the dagger" in inv[0]["aliases"]

    def test_compendium_npc_update_alias_route(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"] = {
            "kael_marsh": {
                "name": "Kael Marsh",
                "aliases": ["scarred soldier"],
            },
        }
        delta = StateDelta(compendium_npc_update=[
            CompendiumNpcUpdate(id="scarred_soldier", name="Kael Marsh", bio="A veteran")
        ])
        updated, _ = apply_delta(state, delta)
        npcs = updated["compendium"]["npcs"]
        assert "scarred_soldier" not in npcs
        assert "kael_marsh" in npcs
        assert npcs["kael_marsh"]["bio"] == "A veteran"

    def test_npc_add_alias_route(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"] = {
            "kael_marsh": {
                "name": "Kael Marsh",
                "aliases": ["scarred soldier"],
            },
        }
        delta = StateDelta(npc_add=[NpcAdd(id="scarred_soldier", name="Kael Marsh", notes="Present.")])
        updated, _ = apply_delta(state, delta)
        present = updated["scene"]["present_npcs"]
        assert len(present) == 1
        assert present[0]["id"] == "kael_marsh"

    def test_inventory_add_new_item_no_merge(self) -> None:
        state = _make_state()
        state["inventory"] = [
            {"id": "worn_dagger", "name": "Worn Dagger", "amount": 1, "aliases": []},
        ]
        delta = StateDelta(inventory_add=[InventoryItem(id="brass_key", name="Brass Key", amount=1)])
        updated, _ = apply_delta(state, delta)
        inv = updated["inventory"]
        assert len(inv) == 2
        ids = {i["id"] for i in inv}
        assert "worn_dagger" in ids
        assert "brass_key" in ids

    def test_npc_update_adds_aliases(self) -> None:
        state = _make_state()
        state["compendium"]["npcs"] = {
            "kael_marsh": {
                "name": "Kael Marsh",
                "aliases": [],
            },
        }
        delta = StateDelta(compendium_npc_update=[
            CompendiumNpcUpdate(id="kael_marsh", aliases=["scarred soldier", "the soldier"])
        ])
        updated, _ = apply_delta(state, delta)
        npcs = updated["compendium"]["npcs"]
        assert "scarred soldier" in npcs["kael_marsh"]["aliases"]
        assert "the soldier" in npcs["kael_marsh"]["aliases"]


# ---------------------------------------------------------------------------
# _expire_scene_pressures
# ---------------------------------------------------------------------------


class TestExpireScenePressures:
    def _make_state_with_pressures(self, turn: int, pressures: list[dict]) -> dict:
        state = _make_state(turn=turn)
        state["scene"]["scene_pressure"] = pressures
        return state

    def test_no_pressures_noop(self) -> None:
        state = _make_state()
        state["scene"]["scene_pressure"] = []
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert delta.scene_pressure_remove == []
        assert state["scene"]["scene_pressure"] == []

    def test_remove_expired_by_max_turns(self) -> None:
        state = self._make_state_with_pressures(
            turn=10,
            pressures=[
                {"id": "fire", "text": "Building is on fire", "urgency": "immediate", "turn_added": 7, "max_turns": 3},
                {"id": "guards", "text": "Guards approaching", "urgency": "building", "turn_added": 8, "max_turns": 5},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert "fire" in delta.scene_pressure_remove
        assert "guards" not in delta.scene_pressure_remove
        # State list is unchanged — apply_delta handles the actual removal.
        assert len(state["scene"]["scene_pressure"]) == 2

    def test_escalate_background_to_building(self) -> None:
        state = self._make_state_with_pressures(
            turn=8,
            pressures=[
                {"id": "whispers", "text": "Strange whispers", "urgency": "background", "turn_added": 1},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        # After 4 turns, background pressures escalate to immediate (TTL cap)
        assert state["scene"]["scene_pressure"][0]["urgency"] == "immediate"

    def test_escalate_building_to_immediate(self) -> None:
        state = self._make_state_with_pressures(
            turn=16,
            pressures=[
                {"id": "guards", "text": "Guards approaching", "urgency": "building", "turn_added": 5},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert state["scene"]["scene_pressure"][0]["urgency"] == "immediate"

    def test_stepwise_escalation_not_jumping(self) -> None:
        """Background at turn 11 should escalate to immediate via TTL cap (not stepwise)."""
        state = self._make_state_with_pressures(
            turn=11,
            pressures=[
                {"id": "whispers", "text": "Strange whispers", "urgency": "background", "turn_added": 1},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        # At age=10 >= 4, background pressures escalate to immediate via TTL cap
        assert state["scene"]["scene_pressure"][0]["urgency"] == "immediate"

    def test_skip_pressures_without_turn_added(self) -> None:
        """Pressures without turn_added (predate tracking) should not be expired or escalated."""
        state = self._make_state_with_pressures(
            turn=100,
            pressures=[
                {"id": "old_threat", "text": "Ancient danger", "urgency": "background"},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert delta.scene_pressure_remove == []
        assert state["scene"]["scene_pressure"][0]["urgency"] == "background"

    def test_skip_pressures_with_turn_added_zero(self) -> None:
        """Pressures with turn_added=0 should not be expired or escalated."""
        state = self._make_state_with_pressures(
            turn=100,
            pressures=[
                {"id": "zero_turn", "text": "Zero turn", "urgency": "background", "turn_added": 0},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert delta.scene_pressure_remove == []
        assert state["scene"]["scene_pressure"][0]["urgency"] == "background"

    def test_custom_thresholds_from_config(self) -> None:
        config = EngineConfig(scene_pressure_building_at=3, scene_pressure_immediate_at=5)
        state = self._make_state_with_pressures(
            turn=4,
            pressures=[
                {"id": "pressure", "text": "Test", "urgency": "background", "turn_added": 1},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta, config)
        assert state["scene"]["scene_pressure"][0]["urgency"] == "building"

    def test_no_change_no_state_write(self) -> None:
        """If nothing changes, state should not be rewritten."""
        state = self._make_state_with_pressures(
            turn=3,
            pressures=[
                {"id": "pressure", "text": "Test", "urgency": "background", "turn_added": 1},
            ],
        )
        original_list = state["scene"]["scene_pressure"]
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert state["scene"]["scene_pressure"] is original_list

    def test_mixed_expired_and_alive(self) -> None:
        state = self._make_state_with_pressures(
            turn=10,
            pressures=[
                {"id": "a", "text": "Expired", "urgency": "background", "turn_added": 5, "max_turns": 3},
                {"id": "b", "text": "Alive", "urgency": "building", "turn_added": 8},
                {"id": "c", "text": "Also expired", "urgency": "background", "turn_added": 1, "max_turns": 5},
            ],
        )
        delta = StateDelta()
        _expire_scene_pressures(state, delta)
        assert "a" in delta.scene_pressure_remove
        assert "c" in delta.scene_pressure_remove
        # State list is unchanged — apply_delta handles the actual removal.
        assert len(state["scene"]["scene_pressure"]) == 3


class TestNarrationScopeTailFilter:
    """Phase 1 — verifies <scope> tail never reaches SSE consumer.

    Pipeline behavior is unchanged in Phase 1: defaults are used regardless
    of what's in the tail. We just verify the filter strips visibly.
    """

    async def test_scope_tail_not_in_streamed_tokens(self) -> None:
        state = _make_state()
        _write_state(_SAVE_DIR, state)

        chat_call_count = 0

        async def fake_stream(*args, **kwargs):
            ss = kwargs.get("stream_stats")
            if ss is not None:
                ss["prompt_eval_count"] = 42
                ss["eval_count"] = 24
            # Yield chunks that include a <scope> tag at the end
            yield "He laughs."
            yield " The room "
            yield "stills."
            yield '\n\n<scope>'
            yield '{"active_domains":["scene"]}'
            yield "</scope>"

        async def fake_chat(*args, **kwargs):
            nonlocal chat_call_count
            chat_call_count += 1
            if chat_call_count == 1:
                return {"response": _RULES_NO_ROLL, "done": True, "usage": {}}
            if chat_call_count == 2:
                return {"response": _SCENE_RESPONSE, "done": True, "usage": {}}
            if chat_call_count == 3:
                return {"response": _STATE_RESPONSE, "done": True, "usage": {}}
            return {"response": _PROGRESS_RESPONSE, "done": True, "usage": {}}

        _mods = [ccya.engine.turn, ccya.engine.rules, ccya.engine.seed, ccya.engine.extraction]
        _origs: list[tuple] = []
        for _m in _mods:
            if hasattr(_m, "llm_chat"):
                _origs.append((_m, "llm_chat", _m.llm_chat))
                _m.llm_chat = fake_chat
            if hasattr(_m, "llm_chat_stream"):
                _origs.append((_m, "llm_chat_stream", _m.llm_chat_stream))
                _m.llm_chat_stream = fake_stream
        try:
            tokens: list[str] = []
            result = None
            async for kind, payload in run_turn(
                _SAVE_DIR,
                "look",
                config=EngineConfig(),
                template_dir=str(Path(__file__).parent.parent / "ccya" / "prompts"),
            ):
                if kind == "token":
                    tokens.append(payload)
                elif kind == "complete":
                    result = payload
        finally:
            for _m, _name, _orig in _origs:
                setattr(_m, _name, _orig)

        aggregated = "".join(tokens)
        assert "<scope>" not in aggregated
        assert "</scope>" not in aggregated
        assert "He laughs." in aggregated
        assert "The room stills." in aggregated
        assert result is not None
        # The narrative stored in TurnResult should have the scope tag stripped
        assert "<scope>" not in result.narrative
