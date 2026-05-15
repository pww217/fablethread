"""Tests for _validate zero-balance inventory_remove rejection."""

from ccya.engine import _validate
from ccya.models import InventoryRemove, StateDelta


def _zero_balance_state() -> dict:
    return {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {
            "name": "Vex",
            "tagline": "salvage pilot",
            "bio": "",
            "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2},
            "conditions": [],
        },
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [
            {"id": "credits", "name": "Credits", "amount": 0},
            {"id": "9mm_rounds", "name": "9mm rounds", "amount": 12},
        ],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


class TestZeroBalanceRemove:
    def test_zero_balance_rejected(self):
        state = _zero_balance_state()
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits")])
        rejected = _validate(state, delta)
        assert len(rejected) == 1
        assert rejected[0]["kind"] == "zero_balance"
        assert rejected[0]["value"] == "credits"
        assert "zero balance" in rejected[0]["reason"]

    def test_zero_balance_blocks_turn(self):
        state = _zero_balance_state()
        delta = StateDelta(inventory_remove=[InventoryRemove(id="credits")])
        rejected = _validate(state, delta)
        blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
        assert len(blocking) == 1

    def test_non_zero_balance_not_rejected(self):
        state = _zero_balance_state()
        delta = StateDelta(inventory_remove=[InventoryRemove(id="9mm_rounds", amount=3)])
        rejected = _validate(state, delta)
        assert not any(r.get("kind") == "zero_balance" for r in rejected)

    def test_zero_balance_with_alias(self):
        state = {
            "meta": {"turn": 5, "compendium_touch_order": []},
            "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": []},
            "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
            "inventory": [
                {"id": "credits", "name": "Credits", "amount": 0, "aliases": ["cred", "cash"]},
            ],
            "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
            "compendium": {"npcs": {}},
        }
        delta = StateDelta(inventory_remove=[InventoryRemove(id="cred")])
        rejected = _validate(state, delta)
        assert len(rejected) == 1
        assert rejected[0]["kind"] == "zero_balance"
