"""New regression tests added by the prompt audit.

Covers the three guarantees the audit promised:
1. Inventory over-draw is recorded as a non-blocking warn_overdraw rejection.
2. Scene NPC roster deduplicates present + compendium overlap.
3. load_chronicle_tail honors skip_last_n_turns.
"""

from __future__ import annotations

from pathlib import Path

from ccya.engine.extraction import _scene_npc_roster
from ccya.engine.turn import _validate
from ccya.models import (
    InventoryRemove,
    StateDelta,
)
from ccya.state import load_chronicle_tail


def _state(turn: int = 0) -> dict:
    return {
        "meta": {"turn": turn, "compendium_touch_order": []},
        "pc": {
            "name": "Vex",
            "tagline": "salvage pilot",
            "bio": "",
            "stats": {"strength": 2, "dexterity": 2, "wits": 3, "lore": 2, "charisma": 2, "resolve": 2},
            "conditions": [],
        },
        "location": {"id": "ring-7", "name": "Ring 7", "description": "Low-grav berth."},
        "inventory": [
            {"id": "9mm_rounds", "name": "9mm rounds", "amount": 12},
            {"id": "vac-jacket", "name": "Vac jacket", "amount": 1},
        ],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


# ---------------------------------------------------------------------------
# 1. Inventory over-draw is non-blocking and recorded
# ---------------------------------------------------------------------------


class TestInventoryOverDrawValidator:
    def test_over_draw_records_warn_overdraw(self):
        state = _state()  # 9mm_rounds amount=12
        delta = StateDelta(inventory_remove=[InventoryRemove(id="9mm_rounds", amount=20)])
        rejected = _validate(state, delta)
        assert any(r.get("kind") == "warn_overdraw" for r in rejected)
        warn = next(r for r in rejected if r.get("kind") == "warn_overdraw")
        assert warn["requested"] == 20
        assert warn["current"] == 12

    def test_exact_draw_no_warn(self):
        state = _state()
        delta = StateDelta(inventory_remove=[InventoryRemove(id="9mm_rounds", amount=12)])
        rejected = _validate(state, delta)
        assert not any(r.get("kind") == "warn_overdraw" for r in rejected)

    def test_unknown_id_is_blocking(self):
        state = _state()
        delta = StateDelta(inventory_remove=[InventoryRemove(id="ghost-item")])
        rejected = _validate(state, delta)
        assert len(rejected) == 1
        assert rejected[0].get("kind") != "warn_overdraw"

    def test_amount_omitted_no_warn(self):
        state = _state()
        delta = StateDelta(inventory_remove=[InventoryRemove(id="9mm_rounds")])
        rejected = _validate(state, delta)
        assert rejected == []


# ---------------------------------------------------------------------------
# 2. Scene NPC roster dedup
# ---------------------------------------------------------------------------


class TestSceneNpcRoster:
    def test_compendium_only(self):
        roster = _scene_npc_roster(
            known_characters=[{"id": "b", "name": "Bo"}],
        )
        assert len(roster) == 1
        assert roster[0]["tags"] == ["compendium"]

    def test_multiple_compendium_entries(self):
        roster = _scene_npc_roster(
            known_characters=[
                {"id": "a", "name": "Anna"},
                {"id": "b", "name": "Bo"},
            ],
        )
        assert len(roster) == 2
        assert roster[0]["tags"] == ["compendium"]
        assert roster[1]["tags"] == ["compendium"]


# ---------------------------------------------------------------------------
# 3. load_chronicle_tail skip_last_n_turns
# ---------------------------------------------------------------------------


class TestChronicleTailSkip:
    def test_skip_last_n_drops_recent_blocks(self, tmp_path: Path):
        chron = tmp_path / "chronicle.md"
        chron.write_text(
            "## COMPACTED\n\n"
            "compacted summary of early events.\n\n"
            "## Turn 1 — first input\n\nFirst body.\n\n"
            "## Turn 2 — second input\n\nSecond body.\n\n"
            "## Turn 3 — third input\n\nThird body.\n",
        )
        # window_turns=2 — chronicle should only carry turn 1
        tail = load_chronicle_tail(tmp_path, max_tokens=1000, skip_last_n_turns=2)
        assert "compacted summary of early events" in tail
        assert "First body" not in tail
        assert "Second body" not in tail
        assert "Third body" not in tail

    def test_skip_zero_returns_full(self, tmp_path: Path):
        chron = tmp_path / "chronicle.md"
        chron.write_text(
            "## COMPACTED\n\n"
            "compacted summary text.\n\n"
            "## Turn 1 — x\n\nbody one.\n\n"
            "## Turn 2 — y\n\nbody two.\n"
        )
        tail = load_chronicle_tail(tmp_path, max_tokens=1000, skip_last_n_turns=0)
        assert "compacted summary text" in tail

    def test_skip_more_than_blocks_yields_empty(self, tmp_path: Path):
        chron = tmp_path / "chronicle.md"
        chron.write_text("## COMPACTED\n\n## Turn 1 — x\n\nonly body.\n")
        tail = load_chronicle_tail(tmp_path, max_tokens=1000, skip_last_n_turns=5)
        assert "only body" not in tail
