"""Tests for apply_delta location turn stamp fix."""

from ccya.models import ConditionAdd, LocationRef, StateDelta
from ccya.state.delta import apply_delta, reconcile_delta


def test_apply_delta_location_stamp_uses_current_turn_no() -> None:
    """location_entered_turn must reflect current_turn_no, not the pre-increment meta.turn."""
    state: dict = {
        "meta": {"turn": 4},
        "inventory": [],
        "pc": {"conditions": []},
        "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
        "compendium": {"npcs": {}},
    }
    delta = StateDelta(
        location_change=LocationRef(id="tavern", name="The Tavern", description="A dim room.")
    )
    new_state, _ = apply_delta(state, delta, current_turn_no=5)
    assert new_state["scene"]["location_entered_turn"] == 5
    assert new_state["scene"]["turn_entered"] == 5


def test_apply_delta_location_stamp_fallback_without_current_turn_no() -> None:
    """Without current_turn_no, stamp falls back to meta.turn (existing behavior)."""
    state: dict = {
        "meta": {"turn": 4},
        "inventory": [],
        "pc": {"conditions": []},
        "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
        "compendium": {"npcs": {}},
    }
    delta = StateDelta(
        location_change=LocationRef(id="tavern", name="The Tavern", description="A dim room.")
    )
    new_state, _ = apply_delta(state, delta)
    assert new_state["scene"]["location_entered_turn"] == 4


class TestReconcileWithinDeltaConditionDedup:
    def test_dedup_duplicate_condition_adds(self):
        """reconcile_delta drops duplicate condition adds within the same delta."""
        state: dict = {
            "meta": {"turn": 5},
            "inventory": [],
            "pc": {"conditions": []},
            "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
            "compendium": {"npcs": {}},
        }
        delta = StateDelta(pc_condition_add=[
            ConditionAdd(id="shoulder_bruise", label="Shoulder Bruise"),
            ConditionAdd(id="shoulder_bruise", label="Shoulder Bruise"),
        ])
        warnings = reconcile_delta(state, delta)
        assert len(delta.pc_condition_add) == 1
        assert delta.pc_condition_add[0].id == "shoulder_bruise"
        assert any("duplicate condition add within delta" in w for w in warnings)

    def test_dedup_keeps_different_conditions(self):
        """reconcile_delta keeps different condition IDs."""
        state: dict = {
            "meta": {"turn": 5},
            "inventory": [],
            "pc": {"conditions": []},
            "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
            "compendium": {"npcs": {}},
        }
        delta = StateDelta(pc_condition_add=[
            ConditionAdd(id="shoulder_bruise", label="Shoulder Bruise"),
            ConditionAdd(id="headache", label="Headache"),
        ])
        warnings = reconcile_delta(state, delta)
        assert len(delta.pc_condition_add) == 2
        assert not any("duplicate" in w for w in warnings)


class TestConditionSurvivesInventoryConflict:
    def test_condition_applied_with_inventory_conflict(self):
        """Condition add is applied even when reconcile issues an inventory conflict warning."""
        state: dict = {
            "meta": {"turn": 5},
            "inventory": [{"id": "sword", "name": "Sword", "amount": 1}],
            "pc": {"conditions": []},
            "scene": {"recent_events": [], "scene_pressure": [], "present_npcs": [], "recently_left": []},
            "compendium": {"npcs": {}},
        }
        delta = StateDelta(
            inventory_add=[{"id": "sword", "name": "Sword", "amount": 1}],
            inventory_remove=[{"id": "sword", "amount": None}],
            pc_condition_add=[ConditionAdd(id="shoulder_bruise", label="Shoulder Bruise")],
        )
        warnings = reconcile_delta(state, delta)
        assert any("inventory conflict" in w for w in warnings)
        new_state, _ = apply_delta(state, delta)
        cond_ids = {c["id"] for c in new_state["pc"]["conditions"]}
        assert "shoulder_bruise" in cond_ids
