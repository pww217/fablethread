"""Shared fixtures and helpers for integration tests.

Reuses the _FakeLLM pattern from test_engine_smoke.py — patches module-level
llm_chat / llm_chat_stream on ccya.engine.turn, rules, seed, extraction.

Call ordering per turn:
  chat 1  = rules (always returns _RULES_NO_ROLL by default)
  stream  = narrate (yields narrative text)
  chat 2  = extract_scene
  chat 3  = extract_state
  chat 4  = extract_progress
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ccya.engine import EngineConfig

# ---------------------------------------------------------------------------
# Default LLM responses (valid JSON matching extraction schemas)
# ---------------------------------------------------------------------------

_RULES_NO_ROLL = json.dumps({
    "intent": "player action",
    "intent_verb": "act",
    "target": "",
    "stakes": "",
    "check": {"required": False},
})

_SCENE_RESPONSE = json.dumps({
    "scene_tags": ["exploration"],
    "scene_tagline": "Quiet corridor stretches ahead",
    "location_change": None,
    "location_description": None,
    "npc_add": [],
    "npc_remove": [],
    "npc_update": [],
})

_STATE_RESPONSE = json.dumps({
    "inventory_add": [],
    "inventory_remove": [],
    "inventory_update": [],
    "pc_condition_add": [],
    "pc_condition_remove": [],
})

_PROGRESS_RESPONSE = json.dumps({
    "recent_events_add": [],
    "recent_events_update": [],
    "recent_events_remove": [],
    "actions": ["A", "B", "C", "D"],
    "outcome_summary": "",
})


# ---------------------------------------------------------------------------
# Response builders — return JSON strings for _FakeLLM
# ---------------------------------------------------------------------------


def rules_response(
    *,
    check_required: bool = False,
    skill: str | None = None,
    difficulty: str = "normal",
) -> str:
    return json.dumps({
        "intent": "player action",
        "intent_verb": "act",
        "target": "",
        "stakes": "",
        "check": {
            "required": check_required,
            "skill": skill,
            "difficulty": difficulty,
        },
    })


def scene_response(
    *,
    tags: list[str] | None = None,
    tagline: str = "",
    location_change: dict[str, str] | None = None,
    location_description: str | None = None,
    npc_add: list[dict[str, Any]] | None = None,
    npc_remove: list[dict[str, str]] | None = None,
    npc_update: list[dict[str, Any]] | None = None,
    compendium_npc_update: list[dict[str, Any]] | None = None,
) -> str:
    return json.dumps({
        "scene_tags": tags or ["exploration"],
        "scene_tagline": tagline,
        "location_change": location_change,
        "location_description": location_description,
        "npc_add": npc_add or [],
        "npc_remove": npc_remove or [],
        "npc_update": npc_update or [],
        "compendium_npc_update": compendium_npc_update or [],
    })


def state_response(
    *,
    inv_add: list[dict[str, Any]] | None = None,
    inv_remove: list[dict[str, Any]] | None = None,
    inv_update: list[dict[str, Any]] | None = None,
    cond_add: list[dict[str, Any]] | None = None,
    cond_remove: list[dict[str, str]] | None = None,
) -> str:
    return json.dumps({
        "inventory_add": inv_add or [],
        "inventory_remove": inv_remove or [],
        "inventory_update": inv_update or [],
        "pc_condition_add": cond_add or [],
        "pc_condition_remove": cond_remove or [],
    })


def progress_response(
    *,
    rec_add: list[dict[str, Any]] | None = None,
    rec_update: list[dict[str, Any]] | None = None,
    rec_remove: list[str] | None = None,
    actions: list[str] | None = None,
    outcome_summary: str = "",
    gm_beat: dict[str, Any] | None = None,
    beat_disposition: str = "consume",
    scene_pressure_add: list[dict[str, Any]] | None = None,
    scene_pressure_remove: list[str] | None = None,
    scene_pressure_update: list[dict[str, Any]] | None = None,
    advanced_threads: list[str] | None = None,
    candidate_opportunity: str | None = None,
) -> str:
    return json.dumps({
        "recent_events_add": rec_add or [],
        "recent_events_update": rec_update or [],
        "recent_events_remove": rec_remove or [],
        "actions": ["A", "B", "C", "D"] if actions is None else actions,
        "outcome_summary": outcome_summary,
        "gm_beat": gm_beat,
        "beat_disposition": beat_disposition,
        "scene_pressure_add": scene_pressure_add or [],
        "scene_pressure_remove": scene_pressure_remove or [],
        "scene_pressure_update": scene_pressure_update or [],
        "advanced_threads": advanced_threads or [],
        "candidate_opportunity": candidate_opportunity,
    })


# ---------------------------------------------------------------------------
# State builders
# ---------------------------------------------------------------------------


def base_state(turn: int = 0) -> dict[str, Any]:
    return {
        "meta": {
            "game_name": "integration-test",
            "turn": turn,
            "setting_pack": "expanse-belter",
            "model": "mlx-community/test",
            "compendium_touch_order": [],
            "last_compacted_turn": 0,
            "prior_history": [],
            "pending_gm_beat": None,
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
            "momentum": 0,
            "allegiance": None,
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
                "amount": 1,
                "notes": "Cracked screen.",
            },
            {"id": "credits", "name": "Credits", "amount": 100, "notes": "Cash."},
        ],
        "arc": {},
        "scene": {
            "tags": [],
            "world_state": [],
            "recent_events": [],
            "tagline": "",
            "scene_pressure": [],
            "turn_entered": 0,
            "present_npcs": [],
            "recently_left": [],
            "recently_left_turns": 0,
        },
        "compendium": {"npcs": {}},
        "world": {"factions": [], "locations": []},
    }


def state_with_events(turn: int = 0, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    s = base_state(turn)
    if events:
        s["scene"]["recent_events"] = events
    return s


def state_with_conditions(turn: int = 0, conditions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    s = base_state(turn)
    if conditions:
        s["pc"]["conditions"] = conditions
    return s


def state_with_inventory(turn: int = 0, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    s = base_state(turn)
    if items:
        s["inventory"] = items
    return s


def state_with_location(turn: int = 0, loc: dict[str, str] | None = None) -> dict[str, Any]:
    s = base_state(turn)
    if loc:
        s["location"] = loc
    return s


def state_with_pressure(turn: int = 0, pressures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    s = base_state(turn)
    if pressures:
        s["scene"]["scene_pressure"] = pressures
    return s


def state_with_arc(turn: int = 0, arc_data: dict[str, Any] | None = None) -> dict[str, Any]:
    s = base_state(turn)
    s["arc"] = arc_data or {
        "visible_goal": "Find the lost freighter",
        "thematic_question": "How far will you go for a paycheck?",
        "active_threads": [],
        "latent_threads": [],
        "completed_threads": [],
    }
    return s


# ---------------------------------------------------------------------------
# _FakeLLM — patches module-level llm_chat / llm_chat_stream
# ---------------------------------------------------------------------------


class _FakeLLM:
    """Context manager that replaces engine's llm_chat / llm_chat_stream.

    Call ordering per turn:
      chat 1  = rules (always returns _RULES_NO_ROLL by default)
      stream  = narrate (yields narrative text)
      chat 2  = extract_scene
      chat 3  = extract_state
      chat 4  = extract_progress

    Constructor args:
      narrative       = text streamed for narration (default "narrative text")
      scene_response  = JSON for extract_scene (default _SCENE_RESPONSE)
      state_response  = JSON for extract_state (default _STATE_RESPONSE)
      progress_response = JSON for extract_progress (default _PROGRESS_RESPONSE)
      rules_response  = JSON for rules (default _RULES_NO_ROLL)
    """

    def __init__(
        self,
        *,
        narrative: str = "narrative text",
        scene_response: str = _SCENE_RESPONSE,
        state_response: str = _STATE_RESPONSE,
        progress_response: str = _PROGRESS_RESPONSE,
        rules_response: str = _RULES_NO_ROLL,
    ):
        self.call_log: list[dict] = []
        self.narrative = narrative
        self._scene_response = scene_response
        self._state_response = state_response
        self._progress_response = progress_response
        self._rules_response = rules_response
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
                return {"response": _self._rules_response, "done": True, "usage": {"prompt_tokens": 30, "total_tokens": 40}}
            if n == 2:
                return {"response": _self._scene_response, "done": True, "usage": {"prompt_tokens": 100, "total_tokens": 200}}
            if n == 3:
                return {"response": _self._state_response, "done": True, "usage": {"prompt_tokens": 80, "total_tokens": 160}}
            return {"response": _self._progress_response, "done": True, "usage": {"prompt_tokens": 90, "total_tokens": 180}}

        self._fake_stream = _fake_stream
        self._fake_chat = _fake_chat

    def __enter__(self):
        import ccya.engine.turn as turn_mod
        import ccya.engine.rules as rules_mod
        import ccya.engine.seed as seed_mod
        import ccya.engine.extraction as extract_mod

        self._mods = [turn_mod, rules_mod, seed_mod, extract_mod]
        self._origs: list[tuple] = []
        for mod in self._mods:
            if hasattr(mod, "llm_chat"):
                self._origs.append((mod, "llm_chat", mod.llm_chat))
                mod.llm_chat = self._fake_chat
            if hasattr(mod, "llm_chat_stream"):
                self._origs.append((mod, "llm_chat_stream", mod.llm_chat_stream))
                mod.llm_chat_stream = self._fake_stream
        return self

    def __exit__(self, *exc_info):
        for mod, name, orig in self._origs:
            setattr(mod, name, orig)

    def stream_calls(self) -> list[dict]:
        return [c for c in self.call_log if c["kind"] == "stream"]

    def chat_calls(self) -> list[dict]:
        return [c for c in self.call_log if c["kind"] == "chat"]


# ---------------------------------------------------------------------------
# _run — drives run_turn() async generator to completion
# ---------------------------------------------------------------------------


async def _run(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
) -> Any:
    """Drive run_turn() async generator to completion, return TurnResult."""
    from ccya.engine import run_turn

    result = None
    async for kind, payload in run_turn(
        save_dir,
        user_input,
        config=config,
        template_dir=str(Path(__file__).parent.parent.parent / "ccya" / "prompts"),
    ):
        if kind == "complete":
            result = payload
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def save_dir(tmp_path: Path) -> Path:
    """A clean temporary directory for state files."""
    return tmp_path


@pytest.fixture
def saved_base_state(save_dir: Path) -> Path:
    """A save_dir with a minimal base_state written to it."""
    from ccya.state import save_state

    save_state(save_dir, base_state())
    return save_dir


@pytest.fixture
def config() -> EngineConfig:
    return EngineConfig()
