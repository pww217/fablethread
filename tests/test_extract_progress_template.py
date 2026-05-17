"""Verify extract_progress_user.j2 rendering (no active_domains gating)."""
from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


@pytest.fixture
def env() -> Environment:
    prompts_dir = Path(__file__).parent.parent / "ccya" / "prompts"
    return Environment(loader=FileSystemLoader(str(prompts_dir)))


def _render(env: Environment, **ctx) -> str:
    tmpl = env.get_template("extract_progress_user.j2")
    base = {
        "narration": "test prose",
        "pc": {"name": "PC", "tagline": "x"},
        "active_threads": [],
        "recent_events": [],
        "world_state": [],
        "scene_pressure": [],
        "known_characters": [],
        "scene_result": {},
        "deescalate": False,
        "narrative_velocity": 0.0,
        "intent": None,
        "recent_turns": [],
        "turn_no": 1,
        "stakes": "",
        "band": "",
        "pending_beat": None,
    }
    base.update(ctx)
    return tmpl.render(**base)


def test_known_characters_not_in_progress(env: Environment) -> None:
    """known_characters moved to scene stream; should NOT appear in progress user prompt."""
    out = _render(env, known_characters=[{"id": "n1", "name": "N"}])
    assert "## known_characters" not in out
