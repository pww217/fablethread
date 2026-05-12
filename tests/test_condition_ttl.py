"""Tests for condition TTL: default stamping and permanent condition behavior."""

from ccya.models import ConditionAdd, StateDelta
from ccya.state import apply_delta


def _make_state(turn=0, conditions=None):
    state = {
        "meta": {"turn": turn, "compendium_touch_order": []},
        "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": conditions or []},
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [],
        "quests": [],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }
    return state


class TestConditionDefaultTTL:
    def test_none_turns_remaining_gets_default(self):
        state = _make_state(conditions=[])
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="bruised_ribs", label="Bruised", description="Got hit", turns_remaining=None)])
        state, _ = apply_delta(state, delta)
        cond = state["pc"]["conditions"][0]
        assert cond["turns_remaining"] == 10

    def test_explicit_turns_remaining_preserved(self):
        state = _make_state(conditions=[])
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="wounded", label="Wounded", description="Bad injury", turns_remaining=3)])
        state, _ = apply_delta(state, delta)
        cond = state["pc"]["conditions"][0]
        assert cond["turns_remaining"] == 3

    def test_duplicate_condition_skipped(self):
        state = _make_state(conditions=[{"id": "bruised_ribs", "label": "Bruised", "description": "Got hit", "added_turn": 5, "turns_remaining": 10}])
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="bruised_ribs", label="Bruised", description="Got hit", turns_remaining=None)])
        state, _ = apply_delta(state, delta)
        assert len(state["pc"]["conditions"]) == 1

    def test_empty_id_skipped(self):
        state = _make_state(conditions=[])
        delta = StateDelta(pc_condition_add=[ConditionAdd(id="", label="", description="", turns_remaining=None)])
        state, _ = apply_delta(state, delta)
        assert len(state["pc"]["conditions"]) == 0

    def test_permanent_condition_not_decremented_by_age_pass(self):
        """Simulate the age pass logic from run_turn: permanent conditions (None) should not be decremented."""
        state = _make_state(turn=10, conditions=[
            {"id": "permanent", "label": "Permanent", "description": "Lasting", "added_turn": 5, "turns_remaining": None},
        ])
        # Simulate the age pass logic
        updated_conds = []
        for c in state["pc"]["conditions"]:
            tr = c.get("turns_remaining")
            if tr is None:
                updated_conds.append(c)
                continue
            new_remaining = tr - 1
            if new_remaining <= 0:
                pass  # removed
            else:
                updated_conds.append({**c, "turns_remaining": new_remaining})
        state["pc"]["conditions"] = updated_conds
        assert len(state["pc"]["conditions"]) == 1
        assert state["pc"]["conditions"][0]["turns_remaining"] is None

    def test_temporary_condition_decremented_by_age_pass(self):
        """Simulate the age pass logic from run_turn: temporary conditions should be decremented."""
        state = _make_state(turn=10, conditions=[
            {"id": "fresh_wound", "label": "Fresh", "description": "Still hurts", "added_turn": 8, "turns_remaining": 5},
        ])
        updated_conds = []
        for c in state["pc"]["conditions"]:
            tr = c.get("turns_remaining")
            if tr is None:
                updated_conds.append(c)
                continue
            new_remaining = tr - 1
            if new_remaining <= 0:
                pass  # removed
            else:
                updated_conds.append({**c, "turns_remaining": new_remaining})
        state["pc"]["conditions"] = updated_conds
        assert len(state["pc"]["conditions"]) == 1
        assert state["pc"]["conditions"][0]["turns_remaining"] == 4

    def test_expired_condition_removed_by_age_pass(self):
        """Simulate the age pass logic from run_turn: expired conditions should be removed."""
        state = _make_state(turn=10, conditions=[
            {"id": "old_wound", "label": "Old", "description": "Healed", "added_turn": 5, "turns_remaining": 1},
        ])
        updated_conds = []
        for c in state["pc"]["conditions"]:
            tr = c.get("turns_remaining")
            if tr is None:
                updated_conds.append(c)
                continue
            new_remaining = tr - 1
            if new_remaining <= 0:
                pass  # removed
            else:
                updated_conds.append({**c, "turns_remaining": new_remaining})
        state["pc"]["conditions"] = updated_conds
        assert len(state["pc"]["conditions"]) == 0
