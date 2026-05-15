"""Tests for condition and pressure coexistence in apply_delta."""

from ccya.models import ConditionAdd, ConditionRemove, ScenePressure, StateDelta
from ccya.state import apply_delta


def _make_state(conditions=None, scene_pressure=None):
    state = {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {
            "name": "V", "tagline": "pilot", "bio": "",
            "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2},
            "conditions": conditions or [],
        },
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [],
        "scene": {
            "tags": [], "present_npcs": [], "recent_events": [], "tagline": "",
            "scene_pressure": scene_pressure or [],
        },
        "compendium": {"npcs": {}},
    }
    return state


class TestConditionAndPressureCoexist:
    def test_condition_and_pressure_both_applied(self):
        state = _make_state()
        delta = StateDelta(
            pc_condition_add=[ConditionAdd(id="bruised_ribs", label="Bruised Ribs", description="Aching ribs")],
            scene_pressure_add=[ScenePressure(id="patrol", text="Patrol approaching", urgency="building")],
        )
        state, _ = apply_delta(state, delta)
        conds = state["pc"]["conditions"]
        assert len(conds) == 1
        assert conds[0]["id"] == "bruised_ribs"
        assert conds[0]["turns_remaining"] == 10  # DEFAULT_CONDITION_TTL
        pressures = state["scene"]["scene_pressure"]
        assert len(pressures) == 1
        assert pressures[0]["id"] == "patrol"
        assert pressures[0]["urgency"] == "building"

    def test_condition_with_explicit_ttl_and_pressure(self):
        state = _make_state()
        delta = StateDelta(
            pc_condition_add=[ConditionAdd(id="wound", label="Wound", description="Deep cut", turns_remaining=3)],
            scene_pressure_add=[ScenePressure(id="fire", text="Fire spreading", urgency="immediate")],
        )
        state, _ = apply_delta(state, delta)
        conds = state["pc"]["conditions"]
        assert conds[0]["turns_remaining"] == 3
        pressures = state["scene"]["scene_pressure"]
        assert pressures[0]["urgency"] == "immediate"

    def test_condition_remove_and_pressure_add(self):
        state = _make_state(
            conditions=[{"id": "old_wound", "label": "Old Wound", "description": "", "added_turn": 1}],
            scene_pressure=[{"id": "old_pressure", "text": "Old", "urgency": "background", "turn_added": 1}],
        )
        delta = StateDelta(
            pc_condition_remove=[ConditionRemove(id="old_wound")],
            scene_pressure_add=[ScenePressure(id="new_pressure", text="New threat", urgency="building")],
            scene_pressure_remove=["old_pressure"],
        )
        state, _ = apply_delta(state, delta)
        assert len(state["pc"]["conditions"]) == 0
        pressures = state["scene"]["scene_pressure"]
        assert len(pressures) == 1
        assert pressures[0]["id"] == "new_pressure"

    def test_condition_dedup_with_pressure(self):
        state = _make_state(
            conditions=[{"id": "bruised_ribs", "label": "Bruised Ribs", "description": "", "added_turn": 3}],
        )
        delta = StateDelta(
            pc_condition_add=[ConditionAdd(id="bruised_ribs", label="Bruised Ribs", description="Still aching")],
            scene_pressure_add=[ScenePressure(id="patrol", text="Patrol coming", urgency="background")],
        )
        state, _ = apply_delta(state, delta)
        # Condition should not be duplicated
        assert len(state["pc"]["conditions"]) == 1
        assert state["pc"]["conditions"][0]["id"] == "bruised_ribs"
        # Pressure should be added
        assert len(state["scene"]["scene_pressure"]) == 1
