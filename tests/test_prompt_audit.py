"""New regression tests added by the prompt audit.

Covers the four guarantees the audit promised:
1. Every system prompt is byte-stable across two distinct turn states.
2. Inventory over-draw is recorded as a non-blocking warn_overdraw rejection.
3. quest_threshold_directive grows from LOW → HIGH with active-quest count.
4. Scene NPC roster deduplicates present + compendium overlap.
5. load_chronicle_tail honors skip_last_n_turns.
"""

from __future__ import annotations

from pathlib import Path

from ccya.engine import (
    _build_jinja_env,
    _extract_progress_messages,
    _extract_scene_messages,
    _extract_state_messages,
    _narrate_messages,
    _quest_threshold_directive,
    _scene_npc_roster,
    _validate,
)
from ccya.models import (
    InventoryRemove,
    RulesOutcome,
    SceneExtractResult,
    StateDelta,
    StateExtractResult,
)
from ccya.state import load_chronicle_tail


def _env():
    return _build_jinja_env(str(Path(__file__).parent.parent / "ccya" / "prompts"))


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
        "quests": [
            {"id": "q1", "title": "Q1", "status": "active", "objectives": [{"description": "x", "done": False}]},
        ],
        "scene": {"tags": [], "present_npcs": [], "recent_events": [], "tagline": ""},
        "compendium": {"npcs": {}},
    }


# ---------------------------------------------------------------------------
# 1. System-prompt byte stability across the five LLM streams
# ---------------------------------------------------------------------------


class TestSystemPromptByteStability:
    """Each LLM-call system prompt must hash identical across distinct turn states."""

    def _two_states(self) -> tuple[dict, dict]:
        s1 = _state(turn=0)
        s2 = _state(turn=7)
        s2["pc"]["conditions"] = [{"id": "wounded", "label": "wounded", "description": "hit", "added_turn": 6}]
        s2["scene"]["recent_events"] = ["The dock-master is angry."]
        s2["scene"]["present_npcs"] = [{"id": "anna", "name": "Anna", "title": "Fence", "notes": "Watching."}]
        s2["inventory"].append({"id": "credits", "name": "Credits", "amount": 250})
        return s1, s2

    def _roll(self) -> RulesOutcome:
        return RulesOutcome(
            rolled=True, skill="strength", difficulty="hard",
            final_total=8, band="partial",
            directive="The strike succeeds with cost.",
        )

    def test_narrate_system_byte_stable(self):
        env = _env()
        s1, s2 = self._two_states()
        m1 = _narrate_messages(env, s1, "x", pack_style="dark sci-fi")
        m2 = _narrate_messages(
            env, s2, "y", pack_style="dark sci-fi",
            chronicle_tail="prior arc",
            recent_turns=[{"turn": 1, "input": "look", "narrative": "..."}],
            rules_outcome=self._roll(),
            last_turn_failed=["did not succeed"],
            npc_name_pool=["Anna", "Bo"],
            recently_left=[{"id": "old", "name": "Old"}],
        )
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2

    def test_extract_scene_system_byte_stable(self):
        env = _env()
        s1, s2 = self._two_states()
        m1 = _extract_scene_messages(env, "narration A", s1)
        m2 = _extract_scene_messages(env, "narration B", s2, rules_outcome=self._roll())
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2

    def test_extract_state_system_byte_stable(self):
        env = _env()
        s1, s2 = self._two_states()
        scene = SceneExtractResult()
        m1 = _extract_state_messages(env, "N1", s1, scene_result=scene)
        m2 = _extract_state_messages(env, "N2", s2, scene_result=scene, rules_outcome=self._roll())
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2

    def test_extract_progress_system_byte_stable(self):
        env = _env()
        s1, s2 = self._two_states()
        s2["quests"] = [
            {"id": f"q{i}", "title": f"Q{i}", "status": "active", "objectives": []}
            for i in range(4)
        ]
        scene = SceneExtractResult()
        sres = StateExtractResult()
        m1 = _extract_progress_messages(env, "N1", s1, scene_result=scene, state_result=sres)
        m2 = _extract_progress_messages(
            env, "N2", s2, scene_result=scene, state_result=sres, rules_outcome=self._roll(),
        )
        sys1 = next(m for m in m1 if m["role"] == "system")["content"]
        sys2 = next(m for m in m2 if m["role"] == "system")["content"]
        assert sys1 == sys2


# ---------------------------------------------------------------------------
# 2. Inventory over-draw is non-blocking and recorded
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
# 3. quest_threshold_directive ladder
# ---------------------------------------------------------------------------


class TestQuestThresholdDirective:
    def test_zero_quests_low(self):
        s = _quest_threshold_directive([])
        assert "LOW" in s

    def test_one_quest_neutral(self):
        s = _quest_threshold_directive([{"id": "q1"}])
        assert "LOW" not in s and "HIGH" not in s

    def test_two_quests_neutral(self):
        s = _quest_threshold_directive([{"id": "q1"}, {"id": "q2"}])
        assert "LOW" not in s and "HIGH" not in s

    def test_three_quests_high(self):
        s = _quest_threshold_directive([{"id": f"q{i}"} for i in range(3)])
        assert "HIGH" in s

    def test_many_quests_high(self):
        s = _quest_threshold_directive([{"id": f"q{i}"} for i in range(7)])
        assert "HIGH" in s


# ---------------------------------------------------------------------------
# 4. Scene NPC roster dedup
# ---------------------------------------------------------------------------


class TestSceneNpcRoster:
    def test_present_only(self):
        roster = _scene_npc_roster(
            present_npcs=[{"id": "a", "name": "Anna", "notes": "watching"}],
            known_characters=[],
        )
        assert len(roster) == 1
        assert roster[0]["tags"] == ["present"]

    def test_compendium_only(self):
        roster = _scene_npc_roster(
            present_npcs=[],
            known_characters=[{"id": "b", "name": "Bo"}],
        )
        assert len(roster) == 1
        assert roster[0]["tags"] == ["compendium"]

    def test_overlap_merges(self):
        roster = _scene_npc_roster(
            present_npcs=[{"id": "a", "name": "Anna", "notes": "watching"}],
            known_characters=[{"id": "a", "name": "Anna"}],
        )
        assert len(roster) == 1
        assert set(roster[0]["tags"]) == {"present", "compendium"}
        assert roster[0]["notes"] == "watching"


# ---------------------------------------------------------------------------
# 5. load_chronicle_tail skip_last_n_turns
# ---------------------------------------------------------------------------


class TestChronicleTailSkip:
    def test_skip_last_n_drops_recent_blocks(self, tmp_path: Path):
        chron = tmp_path / "chronicle.md"
        chron.write_text(
            "## Turn 1 — first input\n\nFirst body.\n\n"
            "## Turn 2 — second input\n\nSecond body.\n\n"
            "## Turn 3 — third input\n\nThird body.\n",
        )
        # window_turns=2 — chronicle should only carry turn 1
        tail = load_chronicle_tail(tmp_path, max_tokens=1000, skip_last_n_turns=2)
        assert "First body" in tail
        assert "Second body" not in tail
        assert "Third body" not in tail

    def test_skip_zero_returns_full(self, tmp_path: Path):
        chron = tmp_path / "chronicle.md"
        chron.write_text("## Turn 1 — x\n\nbody one.\n\n## Turn 2 — y\n\nbody two.\n")
        tail = load_chronicle_tail(tmp_path, max_tokens=1000, skip_last_n_turns=0)
        assert "body one" in tail and "body two" in tail

    def test_skip_more_than_blocks_yields_empty(self, tmp_path: Path):
        chron = tmp_path / "chronicle.md"
        chron.write_text("## Turn 1 — x\n\nonly body.\n")
        tail = load_chronicle_tail(tmp_path, max_tokens=1000, skip_last_n_turns=5)
        assert "only body" not in tail
