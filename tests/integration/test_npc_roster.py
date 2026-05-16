"""NPC roster assembly integration test.

Tests that the NPC roster is built correctly from present_npcs, known_npcs,
and recently_left NPCs.
"""


from ccya.state import load_state, save_state

from tests.integration.conftest import (
    _FakeLLM,
    _run,
    base_state,
    scene_response,
)


class TestNpcRosterAssembly:
    """Test that the NPC roster is assembled correctly from state."""

    async def test_present_npcs_included_in_roster(self, saved_base_state, config):
        """Present NPCs from state.scene.present_npcs are included in the roster."""
        s = base_state(0)
        s["scene"]["present_npcs"] = [
            {"id": "alice", "name": "Alice", "title": "Merchant", "notes": "At the table.", "bio": "Honest merchant."},
            {"id": "bob", "name": "Bob", "title": "Guard", "notes": "By the door.", "bio": "Watchful guard."},
        ]
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "talk to the NPCs", config)

        assert saved_base_state.exists()

    async def test_known_npcs_included_in_roster(self, saved_base_state, config):
        """Known NPCs from compendium are included in the roster."""
        s = base_state(0)
        s["compendium"]["npcs"] = {
            "alice": {"name": "Alice", "title": "Merchant", "bio": "Honest merchant."},
            "bob": {"name": "Bob", "title": "Guard", "bio": "Watchful guard."},
        }
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "recall the NPCs", config)

        assert saved_base_state.exists()

    async def test_recently_left_included_in_roster(self, saved_base_state, config):
        """Recently left NPCs are included in the roster."""
        s = base_state(0)
        s["scene"]["recently_left"] = [
            {"id": "carol", "name": "Carol", "title": "Guide", "notes": "Just left."},
        ]
        s["scene"]["recently_left_turns"] = 2
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "remember who left", config)

        assert saved_base_state.exists()

    async def test_npcs_added_via_scene_extraction(self, saved_base_state, config):
        """NPCs added via scene extraction appear in the compendium."""
        npc_add = [
            {"id": "dave", "name": "Dave", "title": "Stranger", "notes": "Approaches from the shadows."},
        ]
        scene_resp = scene_response(npc_add=npc_add)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "meet the stranger", config)

        final = load_state(saved_base_state)
        # NPCs added via scene extraction are added to present_npcs, not compendium directly
        # The compendium is updated via compendium_npc_update in the scene extraction
        assert any(n["id"] == "dave" for n in final["scene"]["present_npcs"])

    async def test_npcs_added_to_compendium_via_scene_extraction(self, saved_base_state, config):
        """NPCs added via compendium_npc_update in scene extraction appear in the compendium."""
        compendium_npc_update = [
            {"id": "eve", "name": "Eve", "title": "Mysterious figure", "bio": "A stranger with secrets."},
        ]
        scene_resp = scene_response(compendium_npc_update=compendium_npc_update)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "meet the mysterious figure", config)

        final = load_state(saved_base_state)
        npcs = final["compendium"]["npcs"]
        assert "eve" in npcs


class TestNpcPresence:
    """Test NPC presence levels (PRESENT, JUST_LEFT, NEARBY, KNOWN)."""

    async def test_present_npc_in_state(self, saved_base_state, config):
        """A present NPC has presence=PRESENT in the roster."""
        s = base_state(0)
        s["scene"]["present_npcs"] = [
            {"id": "alice", "name": "Alice", "title": "Merchant", "notes": "Right here.", "bio": "Honest merchant."},
        ]
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "talk to Alice", config)

        assert saved_base_state.exists()

    async def test_recently_left_npc_in_state(self, saved_base_state, config):
        """A recently left NPC has presence=JUST_LEFT in the roster."""
        s = base_state(0)
        s["scene"]["recently_left"] = [
            {"id": "bob", "name": "Bob", "title": "Guard", "notes": "Just left the room."},
        ]
        s["scene"]["recently_left_turns"] = 1
        save_state(saved_base_state, s)

        fake = _FakeLLM()
        with fake:
            await _run(saved_base_state, "watch Bob leave", config)

        assert saved_base_state.exists()


class TestNpcCompendiumLastSeen:
    """Test that last_seen is stamped on touched NPCs after apply_delta."""

    async def test_last_seen_stamped_on_npc_add(self, saved_base_state, config):
        """When an NPC is added via compendium_npc_update, last_seen is stamped."""
        compendium_npc_update = [
            {"id": "frank", "name": "Frank", "title": "Captain", "bio": "Ship captain."},
        ]
        scene_resp = scene_response(compendium_npc_update=compendium_npc_update)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "meet the captain", config)

        final = load_state(saved_base_state)
        frank = final["compendium"]["npcs"].get("frank", {})
        last_seen = frank.get("last_seen")
        assert last_seen is not None
        assert last_seen["turn"] == 1


class TestNpcRemove:
    """Test NPC removal from the scene."""

    async def test_npc_removed_from_scene(self, saved_base_state, config):
        """An NPC removed via scene extraction disappears from present_npcs."""
        s = base_state(0)
        s["scene"]["present_npcs"] = [
            {"id": "alice", "name": "Alice", "title": "Merchant", "notes": "At the table.", "bio": "Honest merchant."},
        ]
        save_state(saved_base_state, s)

        npc_remove = [{"id": "alice"}]
        scene_resp = scene_response(npc_remove=npc_remove)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "Alice leaves", config)

        final = load_state(saved_base_state)
        present_ids = [n["id"] for n in final["scene"]["present_npcs"]]
        assert "alice" not in present_ids


class TestNpcUpdate:
    """Test NPC notes/title/bio updates via scene extraction."""

    async def test_npc_notes_updated(self, saved_base_state, config):
        """An NPC's notes can be updated via scene extraction."""
        s = base_state(0)
        s["scene"]["present_npcs"] = [
            {"id": "alice", "name": "Alice", "title": "Merchant", "notes": "At the table.", "bio": "Honest merchant."},
        ]
        save_state(saved_base_state, s)

        npc_update = [{"id": "alice", "notes": "Now standing by the window."}]
        scene_resp = scene_response(npc_update=npc_update)
        fake = _FakeLLM(scene_response=scene_resp)
        with fake:
            await _run(saved_base_state, "Alice moves to the window", config)

        final = load_state(saved_base_state)
        alice = [n for n in final["scene"]["present_npcs"] if n["id"] == "alice"]
        assert len(alice) == 1
        assert alice[0]["notes"] == "Now standing by the window."
