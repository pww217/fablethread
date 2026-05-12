"""Tests for apply_delta inventory merge and removal behavior."""

from ccya.models import InventoryItem, InventoryRemove, StateDelta
from ccya.state import apply_delta


def _make_state(inventory=None):
    state = {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": []},
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": inventory or [],
        "quests": [],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }
    return state


class TestInventoryDuplicateAdd:
    def test_duplicate_add_merges_amount(self):
        state = _make_state(inventory=[{"id": "brass_key", "name": "Brass Key", "amount": 1}])
        delta = StateDelta(inventory_add=[InventoryItem(id="brass_key", name="Brass Key", amount=1)])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 1
        assert state["inventory"][0]["amount"] == 2

    def test_duplicate_add_different_id_same_name(self):
        state = _make_state(inventory=[{"id": "brass_key", "name": "Brass Key", "amount": 1}])
        delta = StateDelta(inventory_add=[InventoryItem(id="brass_key", name="Brass Key", amount=2)])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 1
        assert state["inventory"][0]["amount"] == 3

    def test_new_add_creates_entry(self):
        state = _make_state(inventory=[{"id": "brass_key", "name": "Brass Key", "amount": 1}])
        delta = StateDelta(inventory_add=[InventoryItem(id="ledger", name="Ledger", amount=1)])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 2
        ids = {item["id"] for item in state["inventory"]}
        assert "brass_key" in ids
        assert "ledger" in ids


class TestInventoryZeroAmountRemoval:
    def test_full_remove_removes_item(self):
        state = _make_state(inventory=[{"id": "brass_key", "name": "Brass Key", "amount": 1}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="brass_key")])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 0

    def test_partial_remove_reduces_amount(self):
        state = _make_state(inventory=[{"id": "credits", "name": "Credits", "amount": 10}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=3)])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 1
        assert state["inventory"][0]["amount"] == 7

    def test_remove_exceeding_amount_full_removes(self):
        state = _make_state(inventory=[{"id": "credits", "name": "Credits", "amount": 2}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits", amount=10)])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 0

    def test_remove_nonexistent_id_noop(self):
        state = _make_state(inventory=[{"id": "brass_key", "name": "Brass Key", "amount": 1}])
        delta = StateDelta(inventory_remove=[InventoryRemove(id="ghost_item")])
        state, _ = apply_delta(state, delta)
        assert len(state["inventory"]) == 1
        assert state["inventory"][0]["id"] == "brass_key"
