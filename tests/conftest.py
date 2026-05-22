"""Test fixtures for CCYA engine testing — FakeLLM, render env, smoke/integration helpers."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Render test fixture (shared with Phase 1)
# ---------------------------------------------------------------------------

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def jinja_env():
    from ccya.engine.config import _build_jinja_env

    return _build_jinja_env(str(_REPO_ROOT / "ccya" / "prompts"))


# ---------------------------------------------------------------------------
# FakeLLM — replaces LLM calls for smoke and integration tests (Phase 2)
# ---------------------------------------------------------------------------

_log = logging.getLogger(__name__)


class FakeLLM:
    """Deterministic LLM replacement that returns pre-configured responses per phase/turn.

    Usage in test files:
        fake_llm.responses["rules"] = ['{"intent": "attack", ...}', '...']  # one per turn
        fake_llm.responses["narrate"] = ["Prose response.", "..."]
        fake_llm.responses["extract_scene"] = ['{...SceneExtractResult JSON...}', "..."]
        fake_llm.responses["extract_state"] = ['{...StateExtractResult JSON...}', "..."]
        fake_llm.responses["extract_progress"] = ['{...ProgressExtractResult JSON...}', "..."]

    The turn counter advances after extract_progress response is returned.
    """

    def __init__(self) -> None:
        self.responses: dict[str, list[str]] = {}
        self._phase_counters: dict[str, int] = {}

    async def chat(
        self,
        host: str,
        model: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float | None = None,
        timeout: float = 180.0,
    ) -> dict[str, Any]:
        """Non-streaming replacement matching llm_client.chat() signature."""
        phase = self._detect_phase(messages)
        if phase not in self._phase_counters:
            self._phase_counters[phase] = 0
        responses_list = self.responses.get(phase, [])
        idx = min(self._phase_counters[phase], len(responses_list) - 1)
        response_text = responses_list[idx] if responses_list else ""
        self._phase_counters[phase] += 1
        return {
            "response": response_text,
            "done": True,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    async def stream(
        self,
        host: str,
        model: str,
        messages: list[dict[str, Any]],
        *,
        temperature: float | None = None,
        timeout: float = 180.0,
        stream_stats: dict[str, Any] | None = None,
    ) -> AsyncIterator[str]:
        """Streaming replacement matching llm_client.chat_stream() signature."""
        phase = self._detect_phase(messages)
        if phase not in self._phase_counters:
            self._phase_counters[phase] = 0
        responses_list = self.responses.get(phase, [])
        idx = min(self._phase_counters[phase], len(responses_list) - 1)
        response_text = responses_list[idx] if responses_list else ""
        self._phase_counters[phase] += 1
        for token in response_text.split():
            yield token

    def _detect_phase(self, messages: list[dict[str, Any]]) -> str:
        """Determine pipeline phase from message content."""
        if not messages:
            return "unknown"

        # Check all messages for distinctive markers (system prompt first)
        all_content = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "") or ""
            if isinstance(content, str):
                all_content += f"[{role}] {content}\n"

        # Rules system prompt is distinctive — check first
        if "You decide whether the player action requires a skill check" in all_content:
            return "rules"

        # Extract scene uses minimal NPC roster with known_characters between TRACE markers
        if "<<TRACE_IMMUTABLE_START>>" in all_content and ("known_characters" in all_content or "`caron` | Caron" in all_content):
            return "extract_scene"

        # State extract has distinctive sections: active_conditions + inventory (current stacks) + player_intent
        if "## active_conditions" in all_content and "player_intent" in all_content:
            return "extract_state"

        # Progress extract uses [SCENE]/[ARC] scope tags for threads
        if "[SCENE]" in all_content or "[ARC]" in all_content:
            return "extract_progress"

        # Narrate has distinctive markers: Band, GM Beat, Narration Directive sections
        if "**Band:**" in all_content and ("GM Beat:" in all_content or "Narration Directive:" in all_content):
            return "narrate"

        # Fallback heuristics based on system prompt patterns
        if "skill check" in all_content:
            return "rules"

        # Default to rules as safest fallback (most common first call)
        return "rules"


@pytest.fixture()
def fake_llm():
    """Create a fresh FakeLLM instance for each test."""
    llm = FakeLLM()
    yield llm
    # Reset state between tests
    llm._phase_counters.clear()


@pytest.fixture(autouse=False)
def fake_llm_patch(monkeypatch, fake_llm: FakeLLM):
    """Patch LLM calls at their import sites in engine modules.

    Patch rules.py (llm_chat), turn.py (llm_chat_stream for narration), and
    extraction.py (llm_chat for scene/state/progress streams). Not autouse —
    only used by smoke/integration tests that need the full pipeline.
    """
    import ccya.engine.rules as rules_mod

    # Patch chat at module level where it's imported
    monkeypatch.setattr(rules_mod, "llm_chat", fake_llm.chat)

    # Narration streaming is called from turn.py (not narrate.py directly)
    import ccya.engine.turn as turn_mod

    monkeypatch.setattr(turn_mod, "llm_chat_stream", fake_llm.stream)

    # Extraction uses llm_chat for all 3 streams
    import ccya.engine.extraction as extraction_mod

    monkeypatch.setattr(extraction_mod, "llm_chat", fake_llm.chat)

    yield fake_llm

    # Reset turn counter between tests
    fake_llm._turn_counter = 0


# ---------------------------------------------------------------------------
# Smoke test helpers (Phase 3)
# ---------------------------------------------------------------------------

_MINIMAL_STATE: dict[str, Any] = {
    "meta": {
        "game_name": "Test Game",
        "turn": 1,
        "setting_pack": "default",
        "model": "",
        "pending_gm_beat": None,
        "prior_history": [],
    },
    "pc": {
        "name": "Test PC",
        "tagline": "The Brave",
        "bio": "A brave adventurer.",
        "stats": {"strength": 3, "dexterity": 2, "wits": 1, "lore": 1, "charisma": 1, "resolve": 1},
        "conditions": [],
    },
    "location": {
        "id": "tavern",
        "name": "The Rusty Tankard",
        "description": "A cozy inn with a warm fire.",
    },
    "inventory": [
        {"id": "dagger", "name": "Steel Dagger", "amount": 1, "notes": ""},
    ],
    "arc": {
        "visible_goal": "",
        "thematic_question": "",
        "hidden_truths": [],
        "discovered_truths": [],
        "threads": [],
        "completed_threads": [],
        "pc_drive": "",
    },
    "scene": {
        "tags": [],
        "tagline": None,
        "present_npcs": [],
        "world_state": [],
        "recent_events": [],
        "recently_left": [],
        "recently_left_turns": 2,
        "turn_entered": 1,
        "location_entered_turn": 1,
    },
}


@pytest.fixture()
def minimal_state_dict():
    """Return a copy of the minimal state dict for smoke tests."""
    return json.loads(json.dumps(_MINIMAL_STATE))


@pytest.fixture()
def setup_save_dir(tmp_path: Path, minimal_state_dict: dict[str, Any]):
    """Write state.yaml and empty events.jsonl to tmp_path.

    Returns the path to the save directory.
    """
    import yaml

    save_dir = tmp_path / "test-save"
    save_dir.mkdir()

    with open(save_dir / "state.yaml", "w") as f:
        yaml.safe_dump(minimal_state_dict, f)

    # Create empty events.jsonl if it doesn't exist
    (save_dir / "events.jsonl").touch()

    return save_dir


# ---------------------------------------------------------------------------
# Integration test helpers (Phase 4) — load scenarios from evals/scenarios/
# ---------------------------------------------------------------------------


def _discover_scenario_files():
    """Discover all scenario .py files under evals/scenarios/."""
    scenarios_dir = Path(__file__).resolve().parents[1] / "evals" / "scenarios"
    return sorted(
        p for p in scenarios_dir.glob("*.py") if p.name != "__init__.py" and p.is_file()
    )


def _load_scenario_module(path: Path) -> Any:
    """Import a scenario module and return the `scenario` attribute."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"_test_scenario_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load scenario module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sc = getattr(mod, "scenario", None)
    if sc is None:
        raise AttributeError(f"{path} must define module-level `scenario`")
    return sc
