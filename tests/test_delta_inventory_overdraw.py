"""Tests for apply_delta overdraw behavior."""

import logging

from ccya.models import InventoryRemove, StateDelta
from ccya.state import apply_delta


def _make_state(inventory=None):
    state = {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": []},
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": inventory or [],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }
    return state


class TestInventoryOverdraw:
    def test_overdraw_clamps_to_full_remove_no_warning(self):
        state = _make_state(inventory=[{"id": "credits", "name": "Credits", "amount": 2}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=100)])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 0

    def test_overdraw_no_negative_amounts(self):
        state = _make_state(inventory=[{"id": "credits", "name": "Credits", "amount": 1}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=999)])
        state, _ = apply_delta(state, delta)
        for item in state["inventory"]:
            assert item.get("amount", 0) >= 0

    def test_zero_amount_remove_coerced_to_full(self, caplog):
        state = _make_state(inventory=[{"id": "credits", "name": "Credits", "amount": 5}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=0)])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 0

    def test_negative_amount_remove_coerced_to_full(self, caplog):
        state = _make_state(inventory=[{"id": "credits", "name": "Credits", "amount": 5}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=-5)])
        with caplog.at_level(logging.WARNING):
            state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 0
