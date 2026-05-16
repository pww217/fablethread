"""Condition TTL expiry and cap integration tests.

Tests that conditions expire after their TTL (default 10 turns) and that
the cap (PC_CONDITIONS_MAX=5) evicts oldest FIFO.
"""


from ccya.state import load_state, save_state, PC_CONDITIONS_MAX

from tests.integration.conftest import (
    _FakeLLM,
    _run,
    state_response,
    state_with_conditions,
)


class TestConditionTTLExpiry:
    """Conditions with turns_remaining should expire after TTL."""

    async def test_condition_expires_after_turns_remaining(self, saved_base_state, config):
        """A condition with turns_remaining=3 should be removed after 3 turns."""
        cond = {
            "id": "wounded",
            "label": "wounded",
            "description": "Hit by debris.",
            "added_turn": 0,
            "turns_remaining": 3,
        }
        s = state_with_conditions(0, [cond])
        save_state(saved_base_state, s)

        for i in range(3):
            fake = _FakeLLM()
            with fake:
                await _run(saved_base_state, f"act turn {i+1}", config)

        final = load_state(saved_base_state)
        cond_ids = [c["id"] for c in final["pc"]["conditions"]]
        assert "wounded" not in cond_ids

    async def test_condition_permanent_when_no_turns_remaining(self, saved_base_state, config):
        """A condition without turns_remaining is permanent — does not age."""
        cond = {
            "id": "scarred",
            "label": "scarred",
            "description": "A permanent scar.",
            "added_turn": 0,
        }
        s = state_with_conditions(0, [cond])
        save_state(saved_base_state, s)

        for i in range(5):
            fake = _FakeLLM()
            with fake:
                await _run(saved_base_state, f"act turn {i+1}", config)

        final = load_state(saved_base_state)
        cond_ids = [c["id"] for c in final["pc"]["conditions"]]
        assert "scarred" in cond_ids

    async def test_condition_expired_event_written(self, saved_base_state, config):
        """When a condition expires, an event of kind 'condition_expired' is written."""
        cond = {
            "id": "injured",
            "label": "injured",
            "description": "Broken leg.",
            "added_turn": 0,
            "turns_remaining": 1,
        }
        s = state_with_conditions(0, [cond])
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "try to walk", config)

        import json as json_mod

        events_file = saved_base_state / "events.jsonl"
        events = [json_mod.loads(line) for line in events_file.read_text().strip().split("\n") if line.strip()]
        expired_events = [e for e in events if e.get("kind") == "condition_expired"]
        assert len(expired_events) >= 1


class TestConditionCap:
    """PC conditions are capped at PC_CONDITIONS_MAX (5)."""

    async def test_cap_at_5_evicts_oldest(self, saved_base_state, config):
        """When more than 5 conditions accumulate, oldest is dropped FIFO."""
        # Start with 5 conditions
        conditions = [
            {"id": f"c{i}", "label": f"c{i}", "description": "", "added_turn": i}
            for i in range(5)
        ]
        s = state_with_conditions(0, conditions)
        save_state(saved_base_state, s)

        # Add 2 more conditions across 2 turns
        for i in range(2):
            cond_add = [{"id": f"new_{i}", "label": f"new {i}", "description": ""}]
            state_resp = state_response(cond_add=cond_add)
            fake = _FakeLLM(state_response=state_resp)
            with fake:
                await _run(saved_base_state, f"acquire condition {i}", config)

        final = load_state(saved_base_state)
        conds = final["pc"]["conditions"]
        assert len(conds) == PC_CONDITIONS_MAX
        cond_ids = [c["id"] for c in conds]
        # c0 and c1 should have been evicted (oldest)
        assert "c0" not in cond_ids
        assert "c1" not in cond_ids


class TestConditionAddAndRemove:
    """Conditions can be added and removed via state extraction."""

    async def test_condition_added_via_state_extraction(self, saved_base_state, config):
        """A condition added via state extraction appears in the final state."""
        cond_add = [{"id": "shaken", "label": "shaken", "description": "Nervous."}]
        state_resp = state_response(cond_add=cond_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "see something frightening", config)

        final = load_state(saved_base_state)
        cond_ids = [c["id"] for c in final["pc"]["conditions"]]
        assert "shaken" in cond_ids

    async def test_condition_removed_via_state_extraction(self, saved_base_state, config):
        """A condition removed via state extraction disappears from the final state."""
        cond = {"id": "bruised", "label": "bruised", "description": "Bruised ribs.", "added_turn": 0}
        s = state_with_conditions(0, [cond])
        save_state(saved_base_state, s)

        cond_remove = [{"id": "bruised"}]
        state_resp = state_response(cond_remove=cond_remove)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "recover from bruising", config)

        final = load_state(saved_base_state)
        cond_ids = [c["id"] for c in final["pc"]["conditions"]]
        assert "bruised" not in cond_ids


class TestConditionAddedTurn:
    """applied_delta stamps added_turn = state.meta.turn on each new condition."""

    async def test_added_turn_stamped_by_apply_delta(self, saved_base_state, config):
        """applied_delta stamps added_turn = state.meta.turn on each new condition."""
        cond_add = [{"id": "shaken", "label": "shaken", "description": "Nervous."}]
        state_resp = state_response(cond_add=cond_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "see something scary", config)

        final = load_state(saved_base_state)
        cond = [c for c in final["pc"]["conditions"] if c["id"] == "shaken"]
        assert len(cond) == 1
        assert cond[0]["added_turn"] == 0


class TestConditionIdDedup:
    """Duplicate condition IDs are rejected on add."""

    async def test_duplicate_id_rejected(self, saved_base_state, config):
        """Duplicate id is rejected on add regardless of label wording."""
        cond = {"id": "bruised_ribs", "label": "bruised ribs", "description": "", "added_turn": 0}
        s = state_with_conditions(0, [cond])
        save_state(saved_base_state, s)

        cond_add = [{"id": "bruised_ribs", "label": "Bruised Ribs", "description": "Different wording."}]
        state_resp = state_response(cond_add=cond_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "feel the pain", config)

        final = load_state(saved_base_state)
        cond_ids = [c["id"] for c in final["pc"]["conditions"]]
        assert cond_ids.count("bruised_ribs") == 1
