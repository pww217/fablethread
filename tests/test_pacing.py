"""Tests for _compute_narrative_velocity and _compute_narration_directive."""

from ccya.engine.turn import _compute_narrative_velocity, _compute_narration_directive


class TestComputeNarrativeVelocity:
    def test_deescalate_dominates(self):
        """deescalate=0.6 must return -0.6 regardless of momentum."""
        assert _compute_narrative_velocity(0.6, 3, False) == -0.6

    def test_avoidance_nudges_negative(self):
        """avoidance=True must return -0.4 when no deescalate."""
        assert _compute_narrative_velocity(0.0, 0, True) == -0.4

    def test_neutral(self):
        """No deescalate, no avoidance, zero momentum must return 0.0."""
        assert _compute_narrative_velocity(0.0, 0, False) == 0.0

    def test_high_momentum_positive(self):
        """Momentum=3 (ceiling) must return positive velocity ~0.5."""
        result = _compute_narrative_velocity(0.0, 3, False)
        assert result > 0
        assert result <= 0.5

    def test_low_momentum_negative(self):
        """Momentum=-3 (floor) must return negative velocity ~-0.5."""
        result = _compute_narrative_velocity(0.0, -3, False)
        assert result < 0
        assert result >= -0.5

    def test_ceiling_equals_floor_returns_zero(self):
        """momentum_ceiling == momentum_floor must return 0.0 (zero span)."""
        assert _compute_narrative_velocity(0.0, 0, False, momentum_floor=3, momentum_ceiling=3) == 0.0


class TestComputeNarrationDirective:
    def test_breathe_suppresses_overwhelm(self):
        """velocity < -0.3 must return Breathe even with 3+ immediate pressures."""
        result = _compute_narration_directive(-0.6, [{"urgency": "immediate"}] * 3, {}, [])
        assert result == "Breathe"

    def test_overwhelm_wins_when_neutral(self):
        """3+ immediate pressures must return Overwhelm at neutral velocity."""
        result = _compute_narration_directive(0.0, [{"urgency": "immediate"}] * 3, {}, [])
        assert result == "Overwhelm"

    def test_pressure_with_combat_fatigue(self):
        """1 immediate pressure + combat_age>=4 must return Pressure; Combat Fatigue."""
        result = _compute_narration_directive(0.0, [{"urgency": "immediate"}], {"combat_age": 4}, [])
        assert result == "Pressure; Combat Fatigue"

    def test_empty_when_no_signals(self):
        """No pressures, no ages must return empty string."""
        result = _compute_narration_directive(0.0, [], {}, [])
        assert result == ""

    def test_tension_from_building_pressure(self):
        """Building pressure must return Tension when nothing higher applies."""
        result = _compute_narration_directive(0.0, [{"urgency": "building", "text": "something brewing"}], {}, [])
        assert result == "Tension"

    def test_resolve_threat_building_aged_out(self):
        """Building threat past building_threat_imperative_at must return Resolve a Threat."""
        threat_ages = [{"urgency": "building", "age": 4}]
        result = _compute_narration_directive(0.0, [], {}, threat_ages, building_threat_imperative_at=4)
        assert result == "Resolve a Threat"

    def test_resolve_threat_background_aged_out(self):
        """Background threat past threat_imperative_at must return Resolve a Threat."""
        threat_ages = [{"urgency": "background", "age": 5}]
        result = _compute_narration_directive(0.0, [], {}, threat_ages, threat_imperative_at=3)
        assert result == "Resolve a Threat"

    def test_threat_pressure_aged_but_not_imperative(self):
        """Background threat between pressure_at and imperative_at must return Threat Pressure."""
        threat_ages = [{"urgency": "background", "age": 4}]
        result = _compute_narration_directive(0.0, [], {}, threat_ages, threat_pressure_at=3, threat_imperative_at=5)
        assert result == "Threat Pressure"

    def test_combat_fatigue_not_appended_when_aged_2(self):
        """combat_age=2 must not append Combat Fatigue (threshold is 3)."""
        result = _compute_narration_directive(0.0, [{"urgency": "immediate"}], {"combat_age": 2}, [])
        assert result == "Pressure"

    def test_breathe_with_combat_fatigue_only(self):
        """Breathe must not append Combat Fatigue (no secondaries when breathing)."""
        result = _compute_narration_directive(-0.6, [], {"combat_age": 5}, [])
        assert result == "Breathe"

    def test_aged_immediate_threat_resolves(self):
        """Immediate threat past age 3 must return Resolve a Threat."""
        threat_ages = [{"urgency": "immediate", "age": 4}]
        result = _compute_narration_directive(0.0, [], {}, threat_ages)
        assert result == "Resolve a Threat"
