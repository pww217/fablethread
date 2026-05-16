"""Tests for apply_delta location turn stamp fix."""

from ccya.models import LocationRef, StateDelta
from ccya.state.delta import apply_delta


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
