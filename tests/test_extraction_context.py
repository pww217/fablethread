"""Tests for _build_extraction_context in extraction.py."""
import copy
from unittest import mock

from ccya.engine.extraction import _build_extraction_context
from ccya.models import (
    SceneExtractResult,
    StateExtractResult,
    NpcAdd,
    NpcRemove,
    InventoryItem,
    InventoryRemove,
    LocationRef,
    ConditionAdd,
)


def test_npc_add_appears_in_context():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult(
        npc_add=[NpcAdd(id="guard_01", notes="", name="Town Guard")],
        npc_remove=[],
    )
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert any(n["id"] == "guard_01" for n in ctx.present_npcs_this_turn)


def test_npc_remove_absent_from_context():
    state = {
        "scene": {
            "present_npcs": [{"id": "guard_01", "name": "Town Guard"}],
            "tags": [],
            "scene_pressure": [],
        },
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult(
        npc_remove=[NpcRemove(id="guard_01")],
    )
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert not any(n["id"] == "guard_01" for n in ctx.present_npcs_this_turn)


def test_inventory_add_appears_in_context():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [{"id": "sword_01", "name": "Iron Sword"}],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult()
    state_result = StateExtractResult(
        inventory_add=[InventoryItem(id="potion_01", name="Health Potion", notes="")],
        inventory_remove=[InventoryRemove(id="sword_01")],
    )
    ctx = _build_extraction_context(state, scene_result, state_result)
    ids = [i["id"] for i in ctx.inventory_this_turn]
    assert "potion_01" in ids
    assert "sword_01" not in ids


def test_location_change_applied():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult(location_change=LocationRef(id="forest", name="Forest", description="A dense wood."))
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert ctx.location_this_turn["name"] == "Forest"


def test_build_extraction_context_does_not_mutate_state():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [{"id": "sword_01", "name": "Iron Sword"}],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    state_snapshot = copy.deepcopy(state)
    scene_result = SceneExtractResult()
    state_result = StateExtractResult(
        inventory_remove=[InventoryRemove(id="sword_01")],
    )
    _build_extraction_context(state, scene_result, state_result)
    assert state == state_snapshot


def test_build_extraction_context_respects_apply_delta_rejection():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [{"id": "sword_01", "name": "Iron Sword", "amount": 1}],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult()
    state_result = StateExtractResult(
        inventory_remove=[InventoryRemove(id="sword_01")],
    )
    unchanged_state = copy.deepcopy(state)
    with mock.patch(
        "ccya.state.delta.apply_delta",
        return_value=(unchanged_state, False),
    ):
        ctx = _build_extraction_context(state, scene_result, state_result)
    ids = [i["id"] for i in ctx.inventory_this_turn]
    assert "sword_01" in ids


def test_build_extraction_context_npc_add_flows_through():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {"elara": {"name": "Elara", "title": "", "bio": ""}}},
    }
    scene_result = SceneExtractResult(
        npc_add=[NpcAdd(id="elara", notes="", name="Elara")],
    )
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert any(n["id"] == "elara" for n in ctx.present_npcs_this_turn)


def test_build_extraction_context_condition_add_flows_through():
    state = {
        "scene": {"present_npcs": [], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult()
    state_result = StateExtractResult(
        pc_condition_add=[ConditionAdd(id="wounded", label="Wounded", description="Hurts")],
    )
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert any(c["id"] == "wounded" for c in ctx.conditions_this_turn)


def test_build_extraction_context_location_change_clears_present_npcs():
    state = {
        "scene": {"present_npcs": [{"id": "guard_01"}], "tags": [], "scene_pressure": []},
        "inventory": [],
        "pc": {"conditions": []},
        "location": {"name": "Town"},
        "compendium": {"npcs": {}},
    }
    scene_result = SceneExtractResult(
        location_change=LocationRef(id="forest", name="Forest"),
    )
    state_result = StateExtractResult()
    ctx = _build_extraction_context(state, scene_result, state_result)
    assert ctx.location_this_turn["name"] == "Forest"
    assert ctx.present_npcs_this_turn == []
