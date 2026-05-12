"""Tests for _check_npc_ghost_cycle — same-turn remove+add cycle detection."""

from ccya.engine.extraction import _check_npc_ghost_cycle
from ccya.models import NpcAdd, NpcRemove, SceneExtractResult


def _base_state() -> dict:
    return {
        "meta": {"turn": 5, "compendium_touch_order": []},
        "pc": {"name": "V", "tagline": "pilot", "bio": "", "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2}, "conditions": []},
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [],
        "quests": [],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {"tough_a": {"id": "tough_a", "name": "Tough A"}}},
    }


class TestNpcGhostCycle:
    def test_cycle_drops_both_ops(self, caplog):
        scene = SceneExtractResult(
            npc_remove=[NpcRemove(id="tough_a")],
            npc_add=[NpcAdd(id="tough_a", notes="")],
        )
        result = _check_npc_ghost_cycle(scene, _base_state(), trace_id="abc", turn_no=5)
        assert result.npc_remove == []
        assert result.npc_add == []
        assert any("cycle detected" in r.getMessage() for r in caplog.records)

    def test_remove_only_unchanged(self):
        scene = SceneExtractResult(npc_remove=[NpcRemove(id="tough_a")])
        result = _check_npc_ghost_cycle(scene, _base_state(), trace_id="abc", turn_no=5)
        assert len(result.npc_remove) == 1
        assert result.npc_remove[0].id == "tough_a"
        assert result.npc_add == []

    def test_add_only_unchanged(self):
        scene = SceneExtractResult(npc_add=[NpcAdd(id="new_npc", notes="")])
        result = _check_npc_ghost_cycle(scene, _base_state(), trace_id="abc", turn_no=5)
        assert result.npc_add is not None
        assert len(result.npc_add) == 1
        assert result.npc_remove == []

    def test_no_cycle_no_log(self, caplog):
        scene = SceneExtractResult(
            npc_remove=[NpcRemove(id="tough_a")],
            npc_add=[NpcAdd(id="new_npc", notes="")],
        )
        result = _check_npc_ghost_cycle(scene, _base_state(), trace_id="abc", turn_no=5)
        assert result.npc_remove[0].id == "tough_a"
        assert result.npc_add[0].id == "new_npc"
        assert not any("cycle detected" in r.getMessage() for r in caplog.records)

    def test_multiple_cycles(self):
        scene = SceneExtractResult(
            npc_remove=[NpcRemove(id="tough_a"), NpcRemove(id="tough_b")],
            npc_add=[NpcAdd(id="tough_a", notes=""), NpcAdd(id="tough_b", notes="")],
        )
        result = _check_npc_ghost_cycle(scene, _base_state(), trace_id="abc", turn_no=5)
        assert result.npc_remove == []
        assert result.npc_add == []

    def test_partial_cycle(self):
        scene = SceneExtractResult(
            npc_remove=[NpcRemove(id="tough_a"), NpcRemove(id="tough_c")],
            npc_add=[NpcAdd(id="tough_a", notes=""), NpcAdd(id="new_npc", notes="")],
        )
        result = _check_npc_ghost_cycle(scene, _base_state(), trace_id="abc", turn_no=5)
        assert len(result.npc_remove) == 1
        assert result.npc_remove[0].id == "tough_c"
        assert len(result.npc_add) == 1
        assert result.npc_add[0].id == "new_npc"
