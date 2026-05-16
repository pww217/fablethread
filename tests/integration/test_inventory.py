"""Inventory integration tests.

Tests inventory add, remove, update, dedup, and sort behavior.
"""


from ccya.state import load_state, save_state

from tests.integration.conftest import (
    _FakeLLM,
    _run,
    state_response,
    state_with_inventory,
)


class TestInventoryAdd:
    """Inventory items can be added via state extraction."""

    async def test_inventory_item_added(self, saved_base_state, config):
        """An inventory item added via state extraction appears in the final state."""
        inv_add = [{"id": "plasma-cutter", "name": "Plasma cutter", "amount": 1, "notes": "Hot."}]
        state_resp = state_response(inv_add=inv_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "pick up plasma cutter", config)

        final = load_state(saved_base_state)
        ids = [i["id"] for i in final["inventory"]]
        assert "plasma-cutter" in ids

    async def test_inventory_item_with_amount(self, saved_base_state, config):
        """Inventory items with amount > 1 are stored correctly."""
        inv_add = [{"id": "ammo", "name": "Ammo", "amount": 50, "notes": "Bullets."}]
        state_resp = state_response(inv_add=inv_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "find ammo", config)

        final = load_state(saved_base_state)
        ammo = [i for i in final["inventory"] if i["id"] == "ammo"]
        assert len(ammo) == 1
        assert ammo[0]["amount"] == 50


class TestInventoryRemove:
    """Inventory items can be removed via state extraction."""

    async def test_inventory_item_removed(self, saved_base_state, config):
        """An inventory item removed via state extraction disappears from the final state."""
        inv_remove = [{"id": "hand-terminal"}]
        state_resp = state_response(inv_remove=inv_remove)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "discard terminal", config)

        final = load_state(saved_base_state)
        ids = [i["id"] for i in final["inventory"]]
        assert "hand-terminal" not in ids

    async def test_inventory_remove_partial_amount(self, saved_base_state, config):
        """Removing part of a stack reduces the amount."""
        items = [{"id": "credits", "name": "Credits", "amount": 1800, "notes": ""}]
        s = state_with_inventory(0, items)
        save_state(saved_base_state, s)

        inv_remove = [{"id": "credits", "amount": 500}]
        state_resp = state_response(inv_remove=inv_remove)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "spend credits", config)

        final = load_state(saved_base_state)
        credits = [i for i in final["inventory"] if i["id"] == "credits"]
        assert len(credits) == 1
        assert credits[0]["amount"] == 1300

    async def test_inventory_remove_full_stack(self, saved_base_state, config):
        """Removing the full stack removes the item entirely."""
        items = [{"id": "credits", "name": "Credits", "amount": 100, "notes": ""}]
        s = state_with_inventory(0, items)
        save_state(saved_base_state, s)

        inv_remove = [{"id": "credits", "amount": 100}]
        state_resp = state_response(inv_remove=inv_remove)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "spend all credits", config)

        final = load_state(saved_base_state)
        ids = [i["id"] for i in final["inventory"]]
        assert "credits" not in ids


class TestInventoryDedup:
    """Adding the same inventory ID merges into a stack."""

    async def test_same_id_merges_stack(self, saved_base_state, config):
        """Adding the same inventory ID multiple times merges into a single stack."""
        for i in range(3):
            inv_add = [{"id": "water-filter", "name": "Filter", "amount": 1}]
            state_resp = state_response(inv_add=inv_add)
            fake = _FakeLLM(state_response=state_resp)
            with fake:
                await _run(saved_base_state, f"find filter {i+1}", config)

        final = load_state(saved_base_state)
        wf = [i for i in final["inventory"] if "water" in i["id"].lower() or "filter" in i["id"].lower()]
        assert len(wf) == 1
        assert wf[0]["amount"] == 3

    async def test_inventory_id_normalization_merges(self, saved_base_state, config):
        """Inventory IDs are normalized (case/underscore insensitive) for merging."""
        inv_add = [
            {"id": "water-filter", "name": "Filter", "amount": 1},
            {"id": "Water_Filter", "name": "Filter", "amount": 1},
        ]
        state_resp = state_response(inv_add=inv_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "find filters", config)

        final = load_state(saved_base_state)
        wf = [i for i in final["inventory"] if "water" in i["id"].lower() or "filter" in i["id"].lower()]
        assert len(wf) == 1
        assert wf[0]["amount"] == 2


class TestInventorySort:
    """Credits sort to the top of the inventory list."""

    async def test_credits_sort_to_top(self, saved_base_state, config):
        """Credits always sort to the top of the inventory list."""
        items = [
            {"id": "hand-terminal", "name": "Hand terminal", "amount": 1, "notes": ""},
            {"id": "credits", "name": "Credits", "amount": 50, "notes": ""},
        ]
        s = state_with_inventory(0, items)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "check inventory", config)

        final = load_state(saved_base_state)
        assert final["inventory"][0]["id"] == "credits"


class TestInventoryUpdate:
    """Inventory items can be updated (name, notes) via state extraction."""

    async def test_inventory_update_changes_notes(self, saved_base_state, config):
        """An inventory update changes the item's notes."""
        inv_update = [{"id": "hand-terminal", "name": None, "notes": "Fixed screen."}]
        state_resp = state_response(inv_update=inv_update)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "fix the terminal", config)

        final = load_state(saved_base_state)
        terminal = [i for i in final["inventory"] if i["id"] == "hand-terminal"]
        assert len(terminal) == 1
        assert terminal[0]["notes"] == "Fixed screen."


class TestInventoryDedupCompendiumRedirect:
    """Inventory dedup uses the same redirect logic as compendium NPC dedup."""

    async def test_generic_currency_does_not_invent_id(self, saved_base_state, config):
        """When narration references a generic currency term and the inventory has 'credits',
        the extractor must NOT invent a new inventory ID such as 'iron_coin'."""
        items = [{"id": "credits", "name": "Credits", "amount": 850, "notes": "Common coin."}]
        s = state_with_inventory(0, items)
        save_state(saved_base_state, s)

        # Simulate the extractor returning an inventory_remove for a non-existent 'iron_coin'
        inv_remove = [{"id": "iron_coin", "amount": 1}]
        state_resp = state_response(inv_remove=inv_remove)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "pay with iron coin", config)

        final = load_state(saved_base_state)
        credits = [i for i in final["inventory"] if i["id"] == "credits"]
        assert len(credits) == 1
        assert credits[0]["amount"] == 850
        ids = [i["id"] for i in final["inventory"]]
        assert "iron_coin" not in ids
