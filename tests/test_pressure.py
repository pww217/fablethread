"""Tests for scene pressure lifecycle — _purge_scene_pressures."""

from typing import Any

from ccya.engine.pressure import _purge_scene_pressures
from ccya.models import StateDelta


def _make_state(turn: int = 0) -> dict[str, Any]:
    return {
        "meta": {"game_name": "test", "turn": turn},
        "scene": {"scene_pressure": []},
    }


class TestPurgeScenePressures:
    def test_location_change_purges_background_only(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "guards_hunting", "urgency": "immediate", "text": "Guards on alert", "turn_added": 1},
            {"id": "fog_ahead", "urgency": "background", "text": "Dense fog", "turn_added": 1},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=True)
        assert "guards_hunting" not in delta.scene_pressure_remove
        assert "fog_ahead" in delta.scene_pressure_remove

    def test_location_change_purges_building_only(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "wall_guard", "urgency": "building", "text": "Sentry at gate", "turn_added": 1},
            {"id": "distant_thunder", "urgency": "background", "text": "Thunder rumbling", "turn_added": 1},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=True)
        assert "wall_guard" not in delta.scene_pressure_remove
        assert "distant_thunder" in delta.scene_pressure_remove

    def test_location_change_no_pressures(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": []}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=True)
        assert delta.scene_pressure_remove == []

    def test_location_change_all_immediate_survives(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "p1", "urgency": "immediate", "text": "Threat 1", "turn_added": 1},
            {"id": "p2", "urgency": "immediate", "text": "Threat 2", "turn_added": 2},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=True)
        assert delta.scene_pressure_remove == []

    def test_location_change_all_background_removed(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "p1", "urgency": "background", "text": "Texture 1", "turn_added": 1},
            {"id": "p2", "urgency": "background", "text": "Texture 2", "turn_added": 2},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=True)
        assert "p1" in delta.scene_pressure_remove
        assert "p2" in delta.scene_pressure_remove

    def test_no_location_change_uses_age_cap(self) -> None:
        state: dict[str, Any] = {"meta": {"turn": 20}, "scene": {"scene_pressure": [
            {"id": "old_pressure", "urgency": "background", "text": "Old", "turn_added": 1},
            {"id": "new_pressure", "urgency": "immediate", "text": "New", "turn_added": 10},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=False)
        assert "old_pressure" in delta.scene_pressure_remove
        assert "new_pressure" not in delta.scene_pressure_remove

    def test_combat_end_removes_immediate(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "enemy", "urgency": "immediate", "text": "Enemy present", "turn_added": 1},
            {"id": "fog", "urgency": "background", "text": "Fog", "turn_added": 1},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, combat_ended=True)
        assert "enemy" in delta.scene_pressure_remove
        assert "fog" not in delta.scene_pressure_remove

    def test_combat_end_preserves_building(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "wall_guard", "urgency": "building", "text": "Sentry", "turn_added": 1},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, combat_ended=True)
        assert "wall_guard" not in delta.scene_pressure_remove

    def test_no_flags_no_change(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "pressure", "urgency": "building", "text": "Active", "turn_added": 10},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=False, combat_ended=False)
        assert delta.scene_pressure_remove == []

    def test_mixed_urgency_location_change(self) -> None:
        state: dict[str, Any] = {"scene": {"scene_pressure": [
            {"id": "a", "urgency": "immediate", "text": "A", "turn_added": 1},
            {"id": "b", "urgency": "building", "text": "B", "turn_added": 2},
            {"id": "c", "urgency": "background", "text": "C", "turn_added": 3},
            {"id": "d", "urgency": "background", "text": "D", "turn_added": 4},
        ]}}
        delta = StateDelta()
        _purge_scene_pressures(state, delta, location_changed=True)
        assert "a" not in delta.scene_pressure_remove
        assert "b" not in delta.scene_pressure_remove
        assert "c" in delta.scene_pressure_remove
        assert "d" in delta.scene_pressure_remove
