"""Verify extract_progress_user.j2 conditional gating by active_domains."""
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
        "active_quests": [],
        "recent_events": [],
        "world_state": [],
        "scene_pressure": [],
        "known_characters": [],
        "scene_result": {},
        "state_result": {"items_gained": [], "items_lost": []},
        "rules_outcome": None,
        "active_domains": [],
        "quest_threshold_directive": "test",
        "deescalate": False,
        "quest_ages": [],
    }
    base.update(ctx)
    return tmpl.render(**base)


def test_quest_section_omitted_without_quest_updates_domain(env: Environment) -> None:
    out = _render(env, active_domains=["scene"], active_quests=[{"id": "q1", "title": "T", "objectives": []}])
    assert "## active_quests" not in out
    assert "## quest_threshold" not in out


def test_quest_section_present_with_quest_updates_domain(env: Environment) -> None:
    out = _render(env, active_domains=["quest_updates"], active_quests=[{"id": "q1", "title": "T", "objectives": []}])
    assert "## active_quests" in out
    assert "## quest_threshold" in out


def test_recent_events_omitted_without_domain(env: Environment) -> None:
    out = _render(env, active_domains=[], recent_events=[{"id": "e1", "text": "fact"}])
    assert "## recent_events" not in out


def test_recent_events_included_with_domain(env: Environment) -> None:
    out = _render(env, active_domains=["recent_events"], recent_events=[{"id": "e1", "text": "fact"}])
    assert "## recent_events" in out


def test_known_characters_omitted_without_compendium_domain(env: Environment) -> None:
    out = _render(env, active_domains=[], known_characters=[{"id": "n1", "name": "N"}])
    assert "## known_characters" not in out


def test_known_characters_not_in_progress(env: Environment) -> None:
    """known_characters moved to scene stream; should NOT appear in progress user prompt."""
    out = _render(env, active_domains=["compendium_npc"], known_characters=[{"id": "n1", "name": "N"}])
    assert "## known_characters" not in out


def test_scene_pressure_not_in_progress(env: Environment) -> None:
    """scene_pressure moved to scene stream; should NOT appear in progress user prompt."""
    pressure = [{"id": "p1", "urgency": "immediate", "text": "fire", "turn_added": 1}]
    out = _render(env, active_domains=[], scene_pressure=pressure)
    assert "## scene_pressure" not in out
