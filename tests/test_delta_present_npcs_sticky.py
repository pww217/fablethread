"""Tests for apply_delta NPC presence sticky behavior and recently_left tracking."""

from ccya.models import NpcAdd, NpcRemove, StateDelta
from ccya.state import apply_delta


def _make_state(present_npcs=None, compendium_npcs=None):
    state = {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": []},
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [],
        "quests": [],
        "scene": {
            "tags": [],
            "present_npcs": present_npcs or [],
            "recent_events": [],
            "tagline": "",
            "recently_left": [],
            "recently_left_turns": 0,
        },
        "compendium": {"npcs": compendium_npcs or {}},
    }
    return state


class TestPresentNpcsSticky:
    def test_no_npc_delta_preserves_present_npcs(self):
        state = _make_state(
            present_npcs=[
                {"id": "tough_a", "name": "Tough A", "title": "", "notes": "", "bio": ""},
                {"id": "tough_b", "name": "Tough B", "title": "", "notes": "", "bio": ""},
            ],
            compendium_npcs={
                "tough_a": {"name": "Tough A", "title": "", "bio": ""},
                "tough_b": {"name": "Tough B", "title": "", "bio": ""},
            },
        )
        delta = StateDelta()
        state, _ = apply_delta(state, delta)
        present = state["scene"]["present_npcs"]
        assert len(present) == 2
        present_ids = {p["id"] for p in present}
        assert "tough_a" in present_ids
        assert "tough_b" in present_ids

    def test_npc_remove_only_removes_explicit(self):
        state = _make_state(
            present_npcs=[
                {"id": "tough_a", "name": "Tough A", "title": "", "notes": "", "bio": ""},
                {"id": "tough_b", "name": "Tough B", "title": "", "notes": "", "bio": ""},
            ],
            compendium_npcs={
                "tough_a": {"name": "Tough A", "title": "", "bio": ""},
                "tough_b": {"name": "Tough B", "title": "", "bio": ""},
            },
        )
        delta = StateDelta(npc_remove=[NpcRemove(id="tough_a")])
        state, _ = apply_delta(state, delta)
        present = state["scene"]["present_npcs"]
        assert len(present) == 1
        assert present[0]["id"] == "tough_b"

    def test_npc_add_does_not_remove_others(self):
        state = _make_state(
            present_npcs=[
                {"id": "tough_a", "name": "Tough A", "title": "", "notes": "", "bio": ""},
            ],
            compendium_npcs={
                "tough_a": {"name": "Tough A", "title": "", "bio": ""},
                "new_npc": {"name": "New NPC", "title": "", "bio": ""},
            },
        )
        delta = StateDelta(npc_add=[NpcAdd(id="new_npc", name="New NPC")])
        state, _ = apply_delta(state, delta)
        present = state["scene"]["present_npcs"]
        assert len(present) == 2
        present_ids = {p["id"] for p in present}
        assert "tough_a" in present_ids
        assert "new_npc" in present_ids


class TestRecentlyLeftTracking:
    def test_removed_npc_appears_in_recently_left(self):
        state = _make_state(
            present_npcs=[
                {"id": "tough_a", "name": "Tough A", "title": "Brute", "notes": "", "bio": ""},
            ],
            compendium_npcs={
                "tough_a": {"name": "Tough A", "title": "Brute", "bio": "A scary guy"},
            },
        )
        delta = StateDelta(npc_remove=[NpcRemove(id="tough_a")])
        state, _ = apply_delta(state, delta)
        recently_left = state["scene"]["recently_left"]
        assert len(recently_left) == 1
        assert recently_left[0]["id"] == "tough_a"
        assert recently_left[0]["name"] == "Tough A"
        assert recently_left[0]["title"] == "Brute"

    def test_recently_left_turns_set_on_removal(self):
        state = _make_state(
            present_npcs=[
                {"id": "tough_a", "name": "Tough A", "title": "", "notes": "", "bio": ""},
            ],
            compendium_npcs={
                "tough_a": {"name": "Tough A", "title": "", "bio": ""},
            },
        )
        # Don't set recently_left_turns initially — let setdefault handle it
        del state["scene"]["recently_left_turns"]
        delta = StateDelta(npc_remove=[NpcRemove(id="tough_a")])
        state, _ = apply_delta(state, delta)
        assert state["scene"]["recently_left_turns"] == 2

    def test_no_recently_left_when_no_removals(self):
        state = _make_state(
            present_npcs=[
                {"id": "tough_a", "name": "Tough A", "title": "", "notes": "", "bio": ""},
            ],
            compendium_npcs={
                "tough_a": {"name": "Tough A", "title": "", "bio": ""},
            },
        )
        delta = StateDelta(npc_add=[NpcAdd(id="tough_a", name="Tough A")])
        state, _ = apply_delta(state, delta)
        # No removals, so recently_left should be empty or unchanged
        recently_left = state["scene"].get("recently_left", [])
        assert len(recently_left) == 0
