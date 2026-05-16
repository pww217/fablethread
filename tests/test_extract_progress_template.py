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


def test_thread_section_always_present(env: Environment) -> None:
    """Thread sections are always rendered."""
    out = _render(env, active_threads=[{"id": "t1", "summary": "T", "urgency": "normal"}])
    assert "## active_threads" in out


def test_recent_events_always_present(env: Environment) -> None:
    """Recent events section is always rendered (no active_domains gating)."""
    out = _render(env, recent_events=[{"id": "e1", "text": "fact"}])
    assert "## recent_events" in out


def test_known_characters_not_in_progress(env: Environment) -> None:
    """known_characters moved to scene stream; should NOT appear in progress user prompt."""
    out = _render(env, known_characters=[{"id": "n1", "name": "N"}])
    assert "## known_characters" not in out


def test_scene_pressure_data_rendered(env: Environment) -> None:
    """scene_pressure data context variable IS rendered in progress user prompt
    as ## Current Pressures block (migrated from scene stream)."""
    pressure = [{"id": "p1", "urgency": "immediate", "text": "fire", "turn_added": 1}]
    out = _render(env, scene_pressure=pressure)
    assert "## Current Pressures" in out
    assert "p1" in out
    assert "fire" in out
