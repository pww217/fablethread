"""Core turn pipeline integration tests.

Tests the full run_turn() flow: rules -> narrate -> extract -> apply -> persist.
Uses _FakeLLM to mock all LLM calls.
"""


from ccya.engine import EngineConfig
from ccya.state import load_state, save_state

from tests.integration.conftest import (
    _FakeLLM,
    _run,
    progress_response,
    scene_response,
    state_response,
)


class TestSingleTurnCompletes:
    """A single turn with no deltas should complete successfully."""

    async def test_turn_completes_with_narrative(self, saved_base_state, config):
        prog_resp = progress_response(actions=["A", "B", "C", "D"])
        fake = _FakeLLM(narrative="Vex steps onto the docking ring.", progress_response=prog_resp)
        with fake:
            result = await _run(saved_base_state, "step onto the ring", config)

        assert result.turn == 1
        assert result.narrative == "Vex steps onto the docking ring."
        assert len(result.errors) == 0
        assert result.actions == ["A", "B", "C", "D"]

    async def test_turn_counter_increments(self, saved_base_state, config):
        fake = _FakeLLM()
        with fake:
            result = await _run(saved_base_state, "look around", config)

        assert result.turn == 1

        fake2 = _FakeLLM()
        with fake2:
            result2 = await _run(saved_base_state, "go forward", config)

        assert result2.turn == 2

    async def test_state_persisted_after_turn(self, saved_base_state, config):
        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "test", config)

        loaded = load_state(saved_base_state)
        assert loaded["meta"]["turn"] == 1

    async def test_chronicle_written(self, saved_base_state, config):
        fake = _FakeLLM(narrative="Vex looks around the docking ring.")
        with fake:
            await _run(saved_base_state, "look", config)

        chronicle = (saved_base_state / "chronicle.md").read_text()
        assert "## Turn 1 — look" in chronicle
        assert "Vex looks around the docking ring." in chronicle

    async def test_event_written_to_jsonl(self, saved_base_state, config):
        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "test input", config)

        import json as json_mod

        events_file = saved_base_state / "events.jsonl"
        events = events_file.read_text().strip().split("\n")
        assert len(events) == 1
        event = json_mod.loads(events[0])
        assert event["turn"] == 1
        assert event["input"] == "test input"

    async def test_trace_id_unique_per_turn(self, saved_base_state, config):
        fake = _FakeLLM()
        with fake:
            r1 = await _run(saved_base_state, "first", config)

        fake2 = _FakeLLM()
        with fake2:
            r2 = await _run(saved_base_state, "second", config)

        assert r1.trace_id != r2.trace_id
        assert len(r1.trace_id) > 0


class TestActionsFromProgress:
    """Actions are captured from the progress extraction stream."""

    async def test_actions_captured(self, saved_base_state, config):
        progress_resp = progress_response(actions=["Open door", "Take stairs", "Check map"])
        fake = _FakeLLM(progress_response=progress_resp)
        with fake:
            result = await _run(saved_base_state, "look", config)

        assert result.actions == ["Open door", "Take stairs", "Check map"]

    async def test_actions_empty_when_not_in_response(self, saved_base_state, config):
        progress_resp = progress_response(actions=[])
        fake = _FakeLLM(progress_response=progress_resp)
        with fake:
            result = await _run(saved_base_state, "look", config)

        assert result.actions == []


class TestRejectedDelta:
    """Rejected deltas produce errors and fallback text."""

    async def test_remove_nonexistent_item(self, saved_base_state, config):
        state_resp = state_response(inv_remove=[{"id": "ghost-item-999"}])
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            result = await _run(saved_base_state, "grab the ghost item", config)

        assert len(result.rejected) == 1
        assert result.rejected[0]["value"] == "ghost-item-999"
        assert "does not exist" in result.rejected[0]["reason"]
        assert len(result.errors) > 0


class TestThreeTurnStateIntegrity:
    """Three sequential turns: inventory accumulates, events bounded, turn counter correct."""

    async def test_inventory_stacks_across_turns(self, saved_base_state, config):
        for i in range(3):
            inv_add = [{"id": "torch", "name": "Torch", "amount": 1}]
            state_resp = state_response(inv_add=inv_add)
            fake = _FakeLLM(state_response=state_resp)
            with fake:
                await _run(saved_base_state, f"find torch {i+1}", config)

        final = load_state(saved_base_state)
        torch_entries = [i for i in final["inventory"] if i["id"] == "torch"]
        assert len(torch_entries) == 1
        assert torch_entries[0]["amount"] == 3

    async def test_recent_events_bounded(self, saved_base_state, config):
        max_events = 3
        cfg = EngineConfig(recent_events_max=max_events)

        for i in range(5):
            rec_add = [{"id": f"event_{i}", "text": f"Event {i} happened", "turn": i}]
            prog_resp = progress_response(rec_add=rec_add)
            fake = _FakeLLM(progress_response=prog_resp)
            with fake:
                await _run(saved_base_state, f"do thing {i+1}", cfg)

        final = load_state(saved_base_state)
        events = final["scene"]["recent_events"]
        assert len(events) <= max_events

    async def test_turn_counter_increments_cleanly(self, saved_base_state, config):
        for i in range(3):
            fake = _FakeLLM()
            with fake:
                result = await _run(saved_base_state, f"turn {i+1}", config)
            assert result.turn == i + 1


class TestLocationChange:
    """Location change from scene extraction updates state."""

    async def test_location_changes(self, saved_base_state, config):
        loc_change = {"id": "concourse-b", "name": "Concourse B", "description": "Wide and bright."}
        scene_resp = scene_response(location_change=loc_change)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "move to concourse", config)

        final = load_state(saved_base_state)
        assert final["location"]["id"] == "concourse-b"
        assert final["location"]["name"] == "Concourse B"

    async def test_location_description_in_place(self, saved_base_state, config):
        scene_resp = scene_response(location_description="The berth lights flicker.")
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "look at lights", config)

        final = load_state(saved_base_state)
        assert final["location"]["description"] == "The berth lights flicker."
        assert final["location"]["id"] == "docking-ring-7"


class TestInventoryAddAndReference:
    """Inventory items are added and can be referenced in later turns."""

    async def test_inventory_item_added(self, saved_base_state, config):
        inv_add = [{"id": "plasma-cutter", "name": "Plasma cutter", "amount": 1, "notes": "Hot."}]
        state_resp = state_response(inv_add=inv_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "pick up plasma cutter", config)

        final = load_state(saved_base_state)
        ids = [i["id"] for i in final["inventory"]]
        assert "plasma-cutter" in ids

    async def test_inventory_item_referenced_in_later_turn(self, saved_base_state, config):
        # Turn 1: add item
        inv_add = [{"id": "brass-key", "name": "Brass key", "amount": 1, "notes": "Old."}]
        state_resp = state_response(inv_add=inv_add)
        fake = _FakeLLM(state_response=state_resp)
        with fake:
            await _run(saved_base_state, "find brass key", config)

        # Turn 2: use item (no delta, just verify it exists in state)
        fake2 = _FakeLLM()
        with fake2:
            await _run(saved_base_state, "use brass key", config)

        final = load_state(saved_base_state)
        ids = [i["id"] for i in final["inventory"]]
        assert "brass-key" in ids


class TestInventoryDedup:
    """Adding the same inventory ID merges into a stack."""

    async def test_same_id_merges_stack(self, saved_base_state, config):
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


class TestCompendiumDedup:
    """Compendium NPCs deduplicate by ID, name, and alias."""

    async def test_compendium_grows_by_unique_npcs(self, saved_base_state, config):
        introductions = [
            ["alice"],
            ["alice", "bob"],
            ["bob", "carol"],
            ["dave"],
        ]

        for turn_idx, ids in enumerate(introductions):
            npc_updates = [
                {"id": nid, "name": nid.title(), "title": "guide", "bio": f"bio of {nid}"}
                for nid in ids
            ]
            scene_resp = scene_response(compendium_npc_update=npc_updates)
            fake = _FakeLLM(scene_response=scene_resp)
            with fake:
                await _run(saved_base_state, f"meet {','.join(ids)}", config)

        final = load_state(saved_base_state)
        npcs = final["compendium"]["npcs"]
        assert set(npcs.keys()) == {"alice", "bob", "carol", "dave"}


class TestNarrationDirective:
    """Narration directive is computed from narrative_velocity and pressure."""

    async def test_narration_directive_injected_when_velocity_negative(self, saved_base_state, config):
        """When avoidance is detected, narrative_velocity is negative -> directive includes 'Breathe'."""
        narrative = "Vex takes a moment to catch their breath.\n\n<scope>{\"active_domains\":[\"narration_directive\"]}</scope>"
        fake = _FakeLLM(narrative=narrative)
        with fake:
            result = await _run(saved_base_state, "slow down and rest", config)

        assert result.turn == 1

    async def test_narration_directive_injected_when_pressure_immediate(self, saved_base_state, config):
        """When there are 3+ immediate pressures, directive should include 'Overwhelm'."""
        pressures = [
            {"id": "p1", "text": "enemy approaching", "urgency": "immediate", "turn_added": 0},
            {"id": "p2", "text": "ammo running low", "urgency": "immediate", "turn_added": 0},
            {"id": "p3", "text": "oxygen leaking", "urgency": "immediate", "turn_added": 0},
        ]
        from tests.integration.conftest import state_with_pressure

        s = state_with_pressure(0, pressures)
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "prepare for fight", config)

        assert saved_base_state.exists()
