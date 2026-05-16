"""Tests for _narrate_messages() — scene_pressure kwarg wiring."""

from pathlib import Path

from ccya.engine.config import _build_jinja_env
from ccya.engine.narrate import _narrate_messages


def _env():
    return _build_jinja_env(str(Path(__file__).parent.parent / "ccya" / "prompts"))


def _make_state():
    return {
        "meta": {
            "game_name": "test",
            "turn": 1,
            "setting_pack": "expanse-belter",
            "model": "test-model",
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
        "inventory": [],
        "scene": {"tags": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


class TestScenePressureWiring:
    """scene_pressure kwarg must flow through _narrate_messages into the Jinja context."""

    def test_scene_pressure_immediate_rendered(self):
        """scene_pressure=[{urgency: immediate}] must produce a Pressure directive in rendered user prompt."""
        env = _env()
        state = _make_state()
        msgs = _narrate_messages(
            env,
            state,
            "look around",
            scene_pressure=[{"urgency": "immediate", "text": "test"}],
        )
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "**Narration Directive:** Pressure" in user_msg["content"]

    def test_scene_pressure_building_rendered(self):
        """scene_pressure=[{urgency: building}] must produce a Tension directive."""
        env = _env()
        state = _make_state()
        msgs = _narrate_messages(
            env,
            state,
            "look around",
            scene_pressure=[{"urgency": "building", "text": "something brewing"}],
        )
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "**Narration Directive:** Tension" in user_msg["content"]

    def test_scene_pressure_overwhelm_rendered(self):
        """Three+ immediate pressures must produce an Overwhelm directive."""
        env = _env()
        state = _make_state()
        msgs = _narrate_messages(
            env,
            state,
            "look around",
            scene_pressure=[
                {"urgency": "immediate", "text": "threat 1"},
                {"urgency": "immediate", "text": "threat 2"},
                {"urgency": "immediate", "text": "threat 3"},
            ],
        )
        user_msg = next(m for m in msgs if m["role"] == "user")
        assert "**Narration Directive:** Overwhelm" in user_msg["content"]

    def test_scene_pressure_none_is_safe(self):
        """scene_pressure=None must not raise; defaults to empty list."""
        env = _env()
        state = _make_state()
        msgs = _narrate_messages(
            env,
            state,
            "look around",
            scene_pressure=None,
        )
        user_msg = next(m for m in msgs if m["role"] == "user")
        # No Pressure/Overwhelm/Tension directive should appear
        assert "Pressure:" not in user_msg["content"]
        assert "Overwhelm:" not in user_msg["content"]
        assert "Tension:" not in user_msg["content"]


class TestThreatAgesWiring:
    """threat_ages passed to _narrate_messages must appear in rendered user prompt."""

    def test_threat_ages_wired(self):
        """threat_ages must flow through _narrate_messages into the rendered prompt."""
        env = _env()
        state = _make_state()
        threat_ages = [{"id": "p1", "text": "Guards closing in", "urgency": "immediate", "age": 4}]
        msgs = _narrate_messages(
            env,
            state,
            "I wait",
            threat_ages=threat_ages,
            turn_no=5,
            threat_imperative_at=3,
        )
        combined = " ".join(m["content"] for m in msgs)
        assert "Resolve a Threat" in combined
