"""Tests for scene pressure lifecycle — _purge_scene_pressures and _expire_scene_pressures."""

from typing import Any

from ccya.engine.config import EngineConfig
from ccya.engine.pressure import _expire_scene_pressures, _purge_scene_pressures
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


class TestImmediateTTL:
    """Tests for immediate pressure TTL (Phase 1)."""

    def test_immediate_ttl_set_on_escalation(self) -> None:
        """building pressure age 4 → assert max_turns set."""
        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 5},
            "scene": {"scene_pressure": [
                {"id": "p1", "urgency": "building", "text": "Threat", "turn_added": 1},
            ]},
        }
        delta = StateDelta()
        config = EngineConfig()
        _expire_scene_pressures(state, delta, config)
        assert state["scene"]["scene_pressure"][0]["urgency"] == "immediate"
        assert state["scene"]["scene_pressure"][0].get("turn_became_immediate") == 5
        assert state["scene"]["scene_pressure"][0].get("max_turns") is not None
        # turn_added=1, age=4, ttl=8 → max_turns = 1 + 4 + 8 = 13
        assert state["scene"]["scene_pressure"][0]["max_turns"] == 13

    def test_immediate_expires_after_ttl(self) -> None:
        """immediate pressure at max_turns → assert in delta.scene_pressure_remove."""
        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 13},
            "scene": {"scene_pressure": [
                {"id": "p1", "urgency": "immediate", "text": "Threat", "turn_added": 1, "max_turns": 12},
            ]},
        }
        delta = StateDelta()
        config = EngineConfig()
        _expire_scene_pressures(state, delta, config)
        assert "p1" in delta.scene_pressure_remove


class TestAvoidanceDecay:
    """Tests for avoidance-based pressure decay (Phase 2)."""

    def test_avoidance_decay_building(self) -> None:
        """building age 2, avoidance=True, decay=2 → effective_age 4, escalates."""
        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 3},
            "scene": {"scene_pressure": [
                {"id": "p1", "urgency": "building", "text": "Threat", "turn_added": 1},
            ]},
        }
        delta = StateDelta()
        config = EngineConfig(avoidance_decay_per_turn=2)
        _expire_scene_pressures(state, delta, config, avoidance=True)
        assert state["scene"]["scene_pressure"][0]["urgency"] == "immediate"

    def test_avoidance_no_effect_on_immediate(self) -> None:
        """immediate pressure, avoidance=True → effective_age unchanged."""
        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 6},
            "scene": {"scene_pressure": [
                {"id": "p1", "urgency": "immediate", "text": "Threat", "turn_added": 1, "max_turns": 20},
            ]},
        }
        delta = StateDelta()
        config = EngineConfig(avoidance_decay_per_turn=5)
        _expire_scene_pressures(state, delta, config, avoidance=True)
        # immediate pressure should NOT be expired (effective_age=5, max_turns=20)
        assert "p1" not in delta.scene_pressure_remove
        # urgency should remain immediate (no escalation needed)
        assert state["scene"]["scene_pressure"][0]["urgency"] == "immediate"


class TestFloorRelief:
    """Tests for momentum floor relief injection (Phase 3)."""

    def test_floor_relief_injection(self) -> None:
        """floor momentum with non-success band → assert pending_gm_beat injected."""
        from ccya.engine.turn import _check_floor_relief

        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 5},
            "pc": {"momentum": -3},
        }
        config = EngineConfig(momentum_floor=-3, momentum_floor_relief_turns=2)

        # First call at floor
        _check_floor_relief(state, config, "fail")
        assert state["meta"]["consecutive_floor_count"] == 1
        assert state["meta"].get("pending_gm_beat") is None

        # Second call at floor — should inject
        _check_floor_relief(state, config, "fail")
        assert state["meta"]["consecutive_floor_count"] == 2
        assert state["meta"]["pending_gm_beat"]["type"] == "breathing_room"

    def test_floor_relief_not_injected_after_success(self) -> None:
        """floor momentum with success band → assert no injection, counter resets."""
        from ccya.engine.turn import _check_floor_relief

        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 5},
            "pc": {"momentum": -3},
        }
        config = EngineConfig(momentum_floor=-3, momentum_floor_relief_turns=2)

        # First call at floor with fail
        _check_floor_relief(state, config, "fail")
        assert state["meta"]["consecutive_floor_count"] == 1

        # Second call at floor with success — resets counter, no injection
        _check_floor_relief(state, config, "success")
        assert state["meta"]["consecutive_floor_count"] == 0
        assert state["meta"].get("pending_gm_beat") is None

    def test_floor_relief_no_injection_with_existing_beat(self) -> None:
        """floor momentum with existing pending_gm_beat → assert no overwrite."""
        from ccya.engine.turn import _check_floor_relief

        state: dict[str, Any] = {
            "meta": {"game_name": "test", "turn": 5, "pending_gm_beat": {"type": "boss_encounter"}},
            "pc": {"momentum": -3},
        }
        config = EngineConfig(momentum_floor=-3, momentum_floor_relief_turns=2)

        _check_floor_relief(state, config, "fail")
        assert state["meta"]["consecutive_floor_count"] == 1
        # Existing beat should not be overwritten
        assert state["meta"]["pending_gm_beat"]["type"] == "boss_encounter"
