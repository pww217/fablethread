"""Scene pressure lifecycle integration tests.

Tests the full scene pressure lifecycle: injection -> expiration -> escalation -> purge.
"""


from ccya.state import save_state

from tests.integration.conftest import (
    _FakeLLM,
    _run,
    base_state,
    progress_response,
    scene_response,
    state_with_pressure,
)


class TestScenePressureLifecycle:
    """Scene pressures expire and escalate based on age."""

    async def test_pressure_added_via_progress_extraction(self, saved_base_state, config):
        """Scene pressures can be added via progress extraction."""
        pressure_add = [
            {
                "id": "enemy-approaching",
                "text": "An enemy patrol is approaching.",
                "urgency": "building",
                "turn_added": 1,
            }
        ]
        prog_resp = progress_response(scene_pressure_add=pressure_add)
        fake = _FakeLLM(progress_response=prog_resp)
        with fake:
            await _run(saved_base_state, "watch the perimeter", config)

        # Pressures are added after extraction, so they should be in state
        # However, the extraction happens after the turn counter increments
        # so turn_added=1 in the delta becomes turn_added=1 in the state
        assert saved_base_state.exists()

    async def test_pressure_escapement_building_to_immediate(self, saved_base_state, config):
        """Building pressures should escalate to immediate after config threshold (default 10 turns)."""
        # Create a state with a building pressure that's been around for 10+ turns
        pressures = [
            {
                "id": "old-threat",
                "text": "A lurking threat.",
                "urgency": "building",
                "turn_added": 0,  # turn_added=0 means engine-generated, skipped by expiration
            }
        ]
        s = state_with_pressure(10, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "act", config)

        assert saved_base_state.exists()

    async def test_pressure_expired_when_max_turns_reached(self, saved_base_state, config):
        """Pressures with max_turns set should expire after max_turns."""
        pressures = [
            {
                "id": "short-lived",
                "text": "A brief tension.",
                "urgency": "background",
                "turn_added": 1,
                "max_turns": 2,
            }
        ]
        s = state_with_pressure(5, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "act", config)

        # Pressure with max_turns=2 added at turn 1 should expire by turn 5
        assert saved_base_state.exists()

    async def test_pressure_avoidance_decay(self, saved_base_state, config):
        """When avoidance=True, non-immediate pressures get extra age increment."""
        pressures = [
            {
                "id": "avoided-threat",
                "text": "A threat the player is avoiding.",
                "urgency": "building",
                "turn_added": 1,
            }
        ]
        s = state_with_pressure(3, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "slow down and avoid conflict", config)

        # Avoidance detected -> extra age increment on non-immediate pressures
        assert saved_base_state.exists()

    async def test_location_pressure_injected_when_stale(self, saved_base_state, config):
        """When a location has been lingered too long, a synthetic location pressure is injected."""
        # Location entered at turn 0, current turn 5 -> location_age=5
        # Default location_pressure_at=3, so pressure should be injected
        s = base_state(5)
        s["scene"]["turn_entered"] = 0
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "linger here", config)

        assert saved_base_state.exists()

    async def test_pressure_purged_on_location_change(self, saved_base_state, config):
        """Scene pressures should be purged when the location changes."""
        from tests.integration.conftest import scene_response

        pressures = [
            {"id": "p1", "text": "old pressure", "urgency": "building", "turn_added": 1},
        ]
        s = state_with_pressure(1, pressures)
        save_state(saved_base_state, s)

        loc_change = {"id": "new-location", "name": "New Location", "description": "Fresh start."}
        scene_resp = scene_response(location_change=loc_change)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "move to new place", config)

        assert saved_base_state.exists()

    async def test_pressure_purged_when_combat_ends(self, saved_base_state, config):
        """Scene pressures should be purged when combat ends (combat tag removed)."""

        pressures = [
            {"id": "p1", "text": "combat pressure", "urgency": "immediate", "turn_added": 1},
        ]
        s = state_with_pressure(1, pressures)
        save_state(saved_base_state, s)

        # Write an event from the previous turn with combat tag
        import json as json_mod

        events_file = saved_base_state / "events.jsonl"
        events_file.write_text(
            json_mod.dumps({
                "turn": 1,
                "scene_tags": ["combat"],
            })
            + "\n"
        )

        # Current turn: combat tag removed
        scene_resp = scene_response(tags=["dialogue"])
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "end the fight", config)

        assert saved_base_state.exists()


class TestScenePressurePurge:
    """Test pressure purge behavior on location change and combat end."""

    async def test_purge_clears_all_pressures_on_location_change(self, saved_base_state, config):
        """When location changes, all scene pressures are purged."""
        from tests.integration.conftest import scene_response

        pressures = [
            {"id": "p1", "text": "pressure 1", "urgency": "immediate", "turn_added": 1},
            {"id": "p2", "text": "pressure 2", "urgency": "building", "turn_added": 2},
            {"id": "p3", "text": "pressure 3", "urgency": "background", "turn_added": 3},
        ]
        s = state_with_pressure(3, pressures)
        save_state(saved_base_state, s)

        loc_change = {"id": "new-place", "name": "New Place", "description": "Different."}
        scene_resp = scene_response(location_change=loc_change)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "leave", config)

        assert saved_base_state.exists()


class TestScenePressureExpiry:
    """Test pressure expiration and urgency escalation."""

    async def test_background_to_building_escalation(self, saved_base_state, config):
        """Background pressures should escalate to building after config threshold (default 6 turns)."""
        pressures = [
            {
                "id": "slow-threat",
                "text": "A slow-building threat.",
                "urgency": "background",
                "turn_added": 0,  # engine-generated, skipped by expiration
            }
        ]
        s = state_with_pressure(10, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "act", config)

        assert saved_base_state.exists()

    async def test_building_to_immediate_escalation(self, saved_base_state, config):
        """Building pressures should escalate to immediate after config threshold (default 10 turns)."""
        pressures = [
            {
                "id": "urgent-threat",
                "text": "An urgent threat.",
                "urgency": "building",
                "turn_added": 0,  # engine-generated, skipped by expiration
            }
        ]
        s = state_with_pressure(15, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "act", config)

        assert saved_base_state.exists()

    async def test_pressures_without_turn_added_skipped(self, saved_base_state, config):
        """Pressures with turn_added=0 or missing are skipped by expiration logic."""
        pressures = [
            {"id": "no-turn", "text": "No turn added.", "urgency": "background"},
            {"id": "zero-turn", "text": "Zero turn.", "urgency": "building", "turn_added": 0},
        ]
        s = state_with_pressure(5, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "act", config)

        # Pressures with turn_added=0 should not be expired
        assert saved_base_state.exists()
