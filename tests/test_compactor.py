"""Unit tests for the compactor overhaul — Phases 1 & 2."""

from pathlib import Path
from unittest import mock

import pytest

from ccya.engine.compactor import (
    _apply_sanitization,
    _build_compact_messages,
    _parse_compact_response,
    _sanitization_nonempty,
    maybe_compact,
)
from ccya.engine.config import EngineConfig, _validate_compactor_config
from ccya.models import CompactorNpcMerge, CompactorSanitizationResult, load_config
from ccya.state.io import _default_state, _migrate_state
from ccya.state.chronicle import load_recent_chronicle_turns


def _fake_compact_chat(*args, **kwargs):
    """Return a valid compaction response for mocked LLM calls."""
    return {
        "response": "- [T1] The party advances through the dark corridor.\n- [T2] A goblin ambushes them.\n\n{}",
        "done": True,
    }


def _mock_compact_llm(response: str | None = None):
    """Context manager that patches ccya.engine.compactor.llm_chat."""
    if response is None:
        response = "- [T1] The party advances through the dark corridor.\n- [T2] A goblin ambushes them.\n\n{}"
    return mock.patch(
        "ccya.engine.compactor.llm_chat",
        new=lambda *a, **kw: _fake_compact_chat_response(response),
    )


async def _fake_compact_chat_response(response: str):
    """Async wrapper so the mock signature matches the real llm_chat."""
    return {
        "response": response,
        "done": True,
    }


# ---------------------------------------------------------------------------
# Config validation
# ---------------------------------------------------------------------------


class TestValidateCompactorConfig:
    def test_valid_defaults(self):
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        _validate_compactor_config(config)  # should not raise

    def test_accepts_compact_every_equal_window_turns(self):
        config = EngineConfig(window_turns=3, compact_every=3, recent_turns_min=2)
        _validate_compactor_config(config)  # should not raise — compact_every >= recent_turns_min

    def test_rejects_compact_every_less_than_recent_turns_min(self):
        config = EngineConfig(window_turns=5, compact_every=1, recent_turns_min=2)
        with pytest.raises(ValueError, match="compact_every.*must be >= recent_turns_min"):
            _validate_compactor_config(config)

    def test_rejects_recent_turns_min_gt_window_turns(self):
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=5)
        with pytest.raises(ValueError, match="recent_turns_min.*must be <= window_turns"):
            _validate_compactor_config(config)

    def test_rejects_recent_turns_min_below_1(self):
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=0)
        with pytest.raises(ValueError, match="recent_turns_min must be >= 1"):
            _validate_compactor_config(config)

    def test_rejects_negative_recent_turns_min(self):
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=-1)
        with pytest.raises(ValueError, match="recent_turns_min must be >= 1"):
            _validate_compactor_config(config)

    def test_rejects_window_turns_below_1(self):
        config = EngineConfig(window_turns=0, compact_every=6, recent_turns_min=1)
        with pytest.raises(ValueError, match="window_turns must be >= 1"):
            _validate_compactor_config(config)

    def test_rejects_negative_compact_every(self):
        config = EngineConfig(window_turns=3, compact_every=-1, recent_turns_min=1)
        with pytest.raises(ValueError, match="compact_every must be >= 0"):
            _validate_compactor_config(config)

    def test_boundary_recent_turns_min_eq_window_turns(self):
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=3)
        _validate_compactor_config(config)  # should not raise

    def test_accepts_compact_every_zero(self):
        config = EngineConfig(window_turns=3, compact_every=0, recent_turns_min=2)
        _validate_compactor_config(config)  # should not raise — 0 means disabled


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_load_config_validates(self):
        """load_config returns dict; validation should pass with repo defaults."""
        cfg = load_config()
        engine_cfg = EngineConfig(
            host=cfg["llm"]["host"],
            model=cfg["llm"]["model"],
            prompt_token_budget=cfg["llm"].get("prompt_token_budget", 28672),
            request_timeout_s=cfg["llm"]["request_timeout_s"],
            narrate_temperature=cfg["llm"]["narrate_temperature"],
            extract_temperature=cfg["llm"]["extract_temperature"],
            max_extract_retries=cfg["llm"]["max_extract_retries"],
            window_turns=cfg["game"]["window_turns"],
            chronicle_prefix_budget_tokens=cfg["game"]["chronicle_prefix_budget_tokens"],
            recent_events_max=cfg["game"]["recent_events_max"],
            enable_extract_thinking=cfg["llm"].get("enable_extract_thinking", False),
            enable_narrate_thinking=cfg["llm"].get("enable_narrate_thinking", False),
            generate_seed_temperature=cfg["llm"].get("generate_seed_temperature", 0.9),
            generate_seed_max_retries=cfg["llm"].get("generate_seed_max_retries", 1),
            log_llm_io=cfg.get("logging", {}).get("log_llm_io", False),
            log_llm_io_max_chars=cfg.get("logging", {}).get("log_llm_io_max_chars", 4000),
            log_prompts=cfg.get("logging", {}).get("log_prompts", False),
            rules_temperature=cfg.get("rules", {}).get("temperature", 0.2),
            max_rules_retries=cfg.get("rules", {}).get("max_retries", 1),
            compact_every=cfg["game"].get("compact_every", 0),
            compact_temperature=cfg["game"].get("compact_temperature", 0.1),
            recent_turns_min=cfg["game"].get("recent_turns_min", 2),
        )
        _validate_compactor_config(engine_cfg)  # should not raise


# ---------------------------------------------------------------------------
# State schema — prior_history
# ---------------------------------------------------------------------------


class TestDefaultState:
    def test_prior_history_present_in_default(self):
        state = _default_state()
        assert state["meta"]["prior_history"] == []

    def test_last_compacted_turn_present_in_default(self):
        state = _default_state()
        assert state["meta"]["last_compacted_turn"] == 0


class TestMigrateStatePriorHistory:
    def test_migrate_adds_prior_history_when_missing(self):
        state = _default_state()
        del state["meta"]["prior_history"]
        _migrate_state(state)
        assert state["meta"]["prior_history"] == []

    def test_migrate_preserves_existing_prior_history(self):
        state = _default_state()
        state["meta"]["prior_history"] = ["- [T1] test"]
        _migrate_state(state)
        assert state["meta"]["prior_history"] == ["- [T1] test"]

    def test_migrate_replaces_non_list_prior_history(self):
        state = _default_state()
        state["meta"]["prior_history"] = "not a list"
        _migrate_state(state)
        assert state["meta"]["prior_history"] == []

    def test_migrate_fixes_invalid_last_compacted_turn_missing(self):
        state = _default_state()
        del state["meta"]["last_compacted_turn"]
        _migrate_state(state)
        assert state["meta"]["last_compacted_turn"] == 0

    def test_migrate_fixes_negative_last_compacted_turn(self):
        state = _default_state()
        state["meta"]["last_compacted_turn"] = -5
        _migrate_state(state)
        assert state["meta"]["last_compacted_turn"] == 0

    def test_migrate_preserves_valid_last_compacted_turn(self):
        state = _default_state()
        state["meta"]["last_compacted_turn"] = 3
        _migrate_state(state)
        assert state["meta"]["last_compacted_turn"] == 3

    def test_migrate_fixes_non_int_last_compacted_turn(self):
        state = _default_state()
        state["meta"]["last_compacted_turn"] = "3"
        _migrate_state(state)
        assert state["meta"]["last_compacted_turn"] == 0


# ---------------------------------------------------------------------------
# Pydantic models — sanitization
# ---------------------------------------------------------------------------


class TestCompactorNpcMerge:
    def test_valid_merge(self):
        merge = CompactorNpcMerge(keep_id="a", remove_ids=["b", "c"])
        assert merge.keep_id == "a"
        assert merge.remove_ids == ["b", "c"]

    def test_empty_remove_ids(self):
        merge = CompactorNpcMerge(keep_id="a")
        assert merge.remove_ids == []

    def test_missing_keep_id_raises(self):
        with pytest.raises(Exception):  # ValidationError
            CompactorNpcMerge(remove_ids=["b"])


class TestCompactorSanitizationResult:
    def test_valid_empty(self):
        result = CompactorSanitizationResult.model_validate({})
        assert result.npc_merge == []
        assert result.inventory_remove == []
        assert result.pressure_remove == []
        assert result.condition_remove == []
        assert result.recent_events_compact == []

    def test_valid_full(self):
        result = CompactorSanitizationResult.model_validate({
            "npc_merge": [{"keep_id": "a", "remove_ids": ["b"]}],
            "inventory_remove": [{"id": "item1", "confidence": "high"}],
            "pressure_remove": [{"id": "p1", "confidence": "medium"}],
            "condition_remove": [{"id": "c1", "confidence": "high"}],
            "recent_events_compact": [{"id": "e1", "text": "Event one", "turn": 1}],
        })
        assert len(result.npc_merge) == 1
        assert result.npc_merge[0].keep_id == "a"
        assert result.npc_merge[0].remove_ids == ["b"]
        assert len(result.inventory_remove) == 1
        assert result.inventory_remove[0].id == "item1"
        assert result.inventory_remove[0].confidence == "high"
        assert len(result.pressure_remove) == 1
        assert result.pressure_remove[0].id == "p1"
        assert result.pressure_remove[0].confidence == "medium"
        assert len(result.condition_remove) == 1
        assert result.condition_remove[0].id == "c1"
        assert len(result.recent_events_compact) == 1
        assert result.recent_events_compact[0].id == "e1"
        assert result.recent_events_compact[0].text == "Event one"
        assert result.recent_events_compact[0].turn == 1

    def test_ignores_unknown_keys(self):
        result = CompactorSanitizationResult.model_validate({
            "npc_merge": [{"keep_id": "a", "remove_ids": ["b"]}],
            "unknown_key": 99,
        })
        assert len(result.npc_merge) == 1

    def test_rejects_wrong_npc_merge_shape(self):
        with pytest.raises(Exception):  # ValidationError
            CompactorSanitizationResult.model_validate({"npc_merge": "wrong_type"})

    def test_rejects_npc_merge_missing_keep_id(self):
        with pytest.raises(Exception):  # ValidationError
            CompactorSanitizationResult.model_validate({"npc_merge": [{"remove_ids": ["b"]}]})


# ---------------------------------------------------------------------------
# Phase 2: Recent-turn selection and compaction math
# ---------------------------------------------------------------------------


class TestChronicleLoaderMinTurnExclusive:
    def test_filters_turns_below_threshold(self, tmp_path: Path):
        chronicle = tmp_path / "chronicle.md"
        chronicle.write_text(
            "## Turn 1 — First\n\nNarrative 1\n\n"
            "## Turn 2 — Second\n\nNarrative 2\n\n"
            "## Turn 3 — Third\n\nNarrative 3\n\n"
            "## Turn 4 — Fourth\n\nNarrative 4\n\n"
            "## Turn 5 — Fifth\n\nNarrative 5\n\n"
        )
        result = load_recent_chronicle_turns(tmp_path, 3, min_turn_exclusive=3)
        assert len(result) == 2
        assert result[0]["turn"] == 4
        assert result[1]["turn"] == 5

    def test_no_filter_returns_last_n(self, tmp_path: Path):
        chronicle = tmp_path / "chronicle.md"
        chronicle.write_text(
            "## Turn 1 — First\n\nNarrative 1\n\n"
            "## Turn 2 — Second\n\nNarrative 2\n\n"
            "## Turn 3 — Third\n\nNarrative 3\n\n"
            "## Turn 4 — Fourth\n\nNarrative 4\n\n"
            "## Turn 5 — Fifth\n\nNarrative 5\n\n"
        )
        result = load_recent_chronicle_turns(tmp_path, 3, min_turn_exclusive=0)
        assert len(result) == 3
        assert result[0]["turn"] == 3
        assert result[1]["turn"] == 4
        assert result[2]["turn"] == 5

    def test_exclusive_filters_all_returns_empty(self, tmp_path: Path):
        chronicle = tmp_path / "chronicle.md"
        chronicle.write_text(
            "## Turn 1 — First\n\nNarrative 1\n\n"
            "## Turn 2 — Second\n\nNarrative 2\n\n"
        )
        result = load_recent_chronicle_turns(tmp_path, 5, min_turn_exclusive=2)
        assert result == []


class TestNarratorDesiredRecentComputation:
    @pytest.mark.parametrize(
        "current_turn_completed,last_compacted_turn,desired_recent,min_turn_exclusive",
        [
            (0, 0, 0, 0),
            (1, 0, 1, 0),
            (2, 0, 2, 0),
            (3, 0, 3, 0),
            (4, 0, 3, 0),
            (5, 0, 3, 0),
            (6, 0, 3, 0),
            (6, 3, 3, 3),
            (7, 3, 3, 3),
            (8, 3, 3, 3),
            (9, 3, 3, 3),
        ],
    )
    def test_desired_recent_computation(
        self,
        current_turn_completed: int,
        last_compacted_turn: int,
        desired_recent: int,
        min_turn_exclusive: int,
    ):
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        turns_since_compaction = max(0, current_turn_completed - last_compacted_turn)
        result = min(config.window_turns, turns_since_compaction)
        if current_turn_completed > 0:
            result = max(result, min(config.recent_turns_min, turns_since_compaction))
        assert result == desired_recent


class TestMaybeCompactBandMath:
    def _write_chronicle(self, save_dir: Path, turns: list[tuple[int, str, str]]) -> None:
        lines: list[str] = []
        for i, (turn_num, user_input, narrative) in enumerate(turns):
            lines.append(f"\n\n## Turn {turn_num} — {user_input}\n\n{narrative}")
        (save_dir / "chronicle.md").write_text("".join(lines))

    def _make_state(self, turn: int, last_compacted_turn: int = 0) -> dict:
        return {
            "meta": {"turn": turn, "last_compacted_turn": last_compacted_turn, "prior_history": []},
            "scene": {"tags": [], "recent_events": [], "scene_pressure": [], "present_npcs": []},
            "inventory": [],
            "compendium": {"npcs": {}},
            "pc": {"conditions": []},
        }

    @pytest.mark.asyncio
    async def test_turn6_compacts_1_to_4_sets_last_compacted_4(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (1, "Attack", "Narrative 1"),
            (2, "Talk", "Narrative 2"),
            (3, "Explore", "Narrative 3"),
            (4, "Rest", "Narrative 4"),
            (5, "Travel", "Narrative 5"),
            (6, "Fight", "Narrative 6"),
        ])
        state = self._make_state(6)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        with _mock_compact_llm():
            result, _ = await maybe_compact(tmp_path, state, config)
        assert result["meta"]["last_compacted_turn"] == 4
        assert len(result["meta"]["prior_history"]) == 2

    @pytest.mark.asyncio
    async def test_turn12_compacts_5_to_10_sets_last_compacted_10(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 13)
        ])
        state = self._make_state(12, last_compacted_turn=4)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        with _mock_compact_llm():
            result, _ = await maybe_compact(tmp_path, state, config)
        assert result["meta"]["last_compacted_turn"] == 10
        assert len(result["meta"]["prior_history"]) == 2

    @pytest.mark.asyncio
    async def test_does_not_fire_on_non_trigger_turn(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 7)
        ])
        state = self._make_state(5)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        result, compaction_ran = await maybe_compact(tmp_path, state, config)
        assert result["meta"]["last_compacted_turn"] == 0
        assert result["meta"]["prior_history"] == []
        assert compaction_ran is False

    @pytest.mark.asyncio
    async def test_recent_events_compaction(self, tmp_path: Path):
        """Compactor consolidates recent_events and writes back to state."""
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 7)
        ])
        state = self._make_state(6)
        state["scene"]["recent_events"] = [
            {"id": "arrived", "text": "You arrived in Marrow's Crossing after three days on the road.", "turn": 1},
            {"id": "rumors", "text": "You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.", "turn": 2},
            {"id": "caron_found", "text": "You found Caron in the tavern — he's been waiting for you.", "turn": 3},
        ]
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        mock_response = (
            "- [T1] You arrived in Marrow's Crossing after three days on the road.\n"
            "- [T2] Uneventful — no mechanical changes.\n"
            "- [T3] Uneventful — no mechanical changes.\n"
            "\n"
            '```json\n'
            '{"recent_events_compact": ['
            '{"id": "arrival_and_rumors", "text": "You arrived in Marrow\'s Crossing to hear that road-toughs are extorting travelers near the inn.", "turn": 1},'
            '{"id": "caron_waiting", "text": "Caron has been waiting for you in the tavern — he knows about the debt.", "turn": 3}'
            ']}\n'
            '```'
        )
        with _mock_compact_llm(mock_response):
            result, _ = await maybe_compact(tmp_path, state, config)
        assert len(result["scene"]["recent_events"]) == 2
        assert result["scene"]["recent_events"][0]["id"] == "arrival_and_rumors"
        assert result["scene"]["recent_events"][1]["id"] == "caron_waiting"

    @pytest.mark.asyncio
    async def test_recent_events_empty_input(self, tmp_path: Path):
        """Compactor with no recent_events produces no recent_events_compact."""
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 7)
        ])
        state = self._make_state(6)
        state["scene"]["recent_events"] = []
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        mock_response = (
            "- [T1] You arrived in Marrow's Crossing.\n"
            "\n"
            "{}"
        )
        with _mock_compact_llm(mock_response):
            result, _ = await maybe_compact(tmp_path, state, config)
        assert result["scene"]["recent_events"] == []

    @pytest.mark.asyncio
    async def test_recent_events_compact_replaces_all(self, tmp_path: Path):
        """Compactor replaces ALL existing recent_events, not just updates."""
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 7)
        ])
        state = self._make_state(6)
        state["scene"]["recent_events"] = [
            {"id": "old_1", "text": "Old event 1", "turn": 1},
            {"id": "old_2", "text": "Old event 2", "turn": 2},
            {"id": "old_3", "text": "Old event 3", "turn": 3},
            {"id": "old_4", "text": "Old event 4", "turn": 4},
        ]
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        mock_response = (
            "- [T1] You arrived in Marrow's Crossing.\n"
            "- [T2] Uneventful.\n"
            "- [T3] Uneventful.\n"
            "- [T4] Uneventful.\n"
            "\n"
            '```json\n'
            '{"recent_events_compact": ['
            '{"id": "consolidated", "text": "You arrived in Marrow\'s Crossing, heard about road-toughs, and found Caron waiting.", "turn": 1}'
            ']}\n'
            '```'
        )
        with _mock_compact_llm(mock_response):
            result, _ = await maybe_compact(tmp_path, state, config)
        assert len(result["scene"]["recent_events"]) == 1
        assert result["scene"]["recent_events"][0]["id"] == "consolidated"

    @pytest.mark.asyncio
    async def test_compacted_turns_removed_from_chronicle(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (1, "Attack", "Narrative 1"),
            (2, "Talk", "Narrative 2"),
            (3, "Explore", "Narrative 3"),
            (4, "Rest", "Narrative 4"),
            (5, "Travel", "Narrative 5"),
            (6, "Fight", "Narrative 6"),
        ])
        state = self._make_state(6)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        with _mock_compact_llm():
            result, _ = await maybe_compact(tmp_path, state, config)
        assert result["meta"]["last_compacted_turn"] == 4
        chronicle_text = (tmp_path / "chronicle.md").read_text()
        assert "## Turn 1 — Attack" not in chronicle_text
        assert "## Turn 2 — Talk" not in chronicle_text
        assert "## Turn 3 — Explore" not in chronicle_text
        assert "## Turn 4 — Rest" not in chronicle_text
        assert "## Turn 5 — Travel" in chronicle_text
        assert "## Turn 6 — Fight" in chronicle_text
        assert "## COMPACTED" in chronicle_text

    @pytest.mark.asyncio
    async def test_incremental_compaction_removes_new_range(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 13)
        ])
        state = self._make_state(12, last_compacted_turn=4)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        with _mock_compact_llm():
            result, _ = await maybe_compact(tmp_path, state, config)
        assert result["meta"]["last_compacted_turn"] == 10
        chronicle_text = (tmp_path / "chronicle.md").read_text()
        for t in range(1, 11):
            assert f"## Turn {t} —" not in chronicle_text
        for t in range(11, 13):
            assert f"## Turn {t} —" in chronicle_text


class TestParseCompactResponse:
    def test_returns_none_on_bad_json(self):
        response = "- [T1] Bullet one\n\n{invalid json"
        bullets, san = _parse_compact_response(response)
        assert "Bullet one" in bullets
        assert san is None

    def test_returns_none_on_validation_error(self):
        response = "- [T1] Bullet one\n\n{\"npc_merge\": \"wrong\"}"
        bullets, san = _parse_compact_response(response)
        assert "Bullet one" in bullets
        assert san is None

    def test_returns_empty_sanitization_on_valid_json(self):
        response = "- [T1] Bullet one\n\n- [T2] Bullet two\n\n{}"
        bullets, san = _parse_compact_response(response)
        assert "Bullet one" in bullets
        assert "Bullet two" in bullets
        assert san is not None
        assert san.npc_merge == []

    def test_returns_sanitization_with_data(self):
        response = "- [T1] Bullet one\n\n{\"npc_merge\": [{\"keep_id\": \"a\", \"remove_ids\": [\"b\"]}]}"
        bullets, san = _parse_compact_response(response)
        assert san is not None
        assert len(san.npc_merge) == 1
        assert san.npc_merge[0].keep_id == "a"

    def test_handles_fenced_json(self):
        response = "- [T1] Bullet one\n\n```json\n{\"npc_merge\": [{\"keep_id\": \"a\", \"remove_ids\": [\"b\"]}]}\n```"
        bullets, san = _parse_compact_response(response)
        assert "Bullet one" in bullets
        assert san is not None
        assert len(san.npc_merge) == 1
        assert san.npc_merge[0].keep_id == "a"

    def test_handles_non_json_fence(self):
        response = "- [T1] Bullet one\n\n```\nsome text\n{\"npc_merge\": []}\n```\n"
        bullets, san = _parse_compact_response(response)
        assert "Bullet one" in bullets
        assert san is not None
        assert san.npc_merge == []


class TestApplySanitization:
    def _make_state_with_data(self) -> dict:
        return {
            "meta": {"turn": 6},
            "compendium": {"npcs": {
                "npc_a": {"name": "Alice", "title": "Wizard", "bio": "", "aliases": []},
                "npc_b": {"name": "Bob", "title": "Thief", "bio": "", "aliases": []},
                "npc_c": {"name": "Carol", "title": "Healer", "bio": "", "aliases": []},
            }},
            "scene": {
                "present_npcs": [{"id": "npc_a", "name": "Alice"}, {"id": "npc_b", "name": "Bob"}],
                "scene_pressure": [
                    {"id": "press_1", "text": "Chase", "urgency": "immediate", "turn_added": 1, "max_turns": 10},
                    {"id": "press_2", "text": "Deadline", "urgency": "building", "turn_added": 2, "max_turns": 10},
                ],
            },
            "inventory": [
                {"id": "inv_1", "name": "Sword", "notes": "Sharp", "amount": 1},
                {"id": "inv_2", "name": "Shield", "notes": "Sturdy", "amount": 1},
            ],
            "pc": {
                "conditions": [
                    {"id": "cond_1", "label": "Wounded", "description": "Hurts", "added_turn": 1},
                    {"id": "cond_2", "label": "Cursed", "description": "Bad luck", "added_turn": 2},
                ],
            },
        }

    def test_skips_unknown_npc_ids(self):
        state = self._make_state_with_data()
        san = CompactorSanitizationResult.model_validate({
            "npc_merge": [{"keep_id": "npc_a", "remove_ids": ["npc_b", "npc_unknown"]}],
        })
        _apply_sanitization(state, san)
        assert "npc_b" not in state["compendium"]["npcs"]
        assert "npc_a" in state["compendium"]["npcs"]
        assert "npc_unknown" not in state["compendium"]["npcs"]

    def test_merges_known_duplicate_npc(self):
        state = self._make_state_with_data()
        san = CompactorSanitizationResult.model_validate({
            "npc_merge": [{"keep_id": "npc_a", "remove_ids": ["npc_b"]}],
        })
        _apply_sanitization(state, san)
        assert "npc_b" not in state["compendium"]["npcs"]
        assert "npc_a" in state["compendium"]["npcs"]
        present_ids = [n.get("id") if isinstance(n, dict) else n for n in state["scene"]["present_npcs"]]
        assert "npc_b" not in present_ids
        assert "npc_a" in present_ids

    def test_removes_known_inventory_item(self):
        state = self._make_state_with_data()
        san = CompactorSanitizationResult.model_validate({
            "inventory_remove": [{"id": "inv_1", "confidence": "high"}],
        })
        _apply_sanitization(state, san)
        inv_ids = {it.get("id") for it in state["inventory"]}
        assert "inv_1" not in inv_ids
        assert "inv_2" in inv_ids

    def test_skips_unknown_pressure_id(self):
        state = self._make_state_with_data()
        san = CompactorSanitizationResult.model_validate({
            "pressure_remove": [{"id": "press_1", "confidence": "high"}, {"id": "press_unknown", "confidence": "low"}],
        })
        _apply_sanitization(state, san)
        press_ids = {p.get("id") for p in state["scene"]["scene_pressure"]}
        assert "press_1" not in press_ids
        assert "press_2" in press_ids
        assert "press_unknown" not in press_ids

    def test_removes_condition(self):
        state = self._make_state_with_data()
        san = CompactorSanitizationResult.model_validate({
            "condition_remove": [{"id": "cond_1", "confidence": "high"}],
        })
        _apply_sanitization(state, san)
        cond_ids = {c.get("id") for c in state["pc"]["conditions"]}
        assert "cond_1" not in cond_ids
        assert "cond_2" in cond_ids


# ---------------------------------------------------------------------------
# Phase 3: Prompt contract
# ---------------------------------------------------------------------------


class TestSystemPromptContract:
    def test_contains_part1_part2_and_part3(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")))
        system_prompt = env.get_template("compact_system.j2").render()

        assert "PART 1" in system_prompt
        assert "PART 2" in system_prompt
        assert "PART 3" in system_prompt

    def test_json_must_be_last_thing(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")))
        system_prompt = env.get_template("compact_system.j2").render()

        assert "The JSON object must be the last thing" in system_prompt


class TestUserPromptRendersIds:
    def test_renders_inventory_ids(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")))
        user_prompt = env.get_template("compact_user.j2").render(
            turns=[{"turn": 1, "input": "Test", "narrative": "Narrative"}],
            active_quests=[{"id": "q_1", "title": "Quest", "objectives": [{"description": "Do it", "done": False}]}],
            npc_names=["Alice"],
            pressures=[{"id": "press_1", "text": "Chase", "urgency": "immediate"}],
            inventory=[{"id": "inv_1", "name": "Sword", "amount": 1, "notes": "Sharp"}],
            compendium_npcs=[("npc_a", {"name": "Alice", "title": "Wizard", "aliases": ["Alicia"]})],
            all_quests=[{"id": "q_1", "title": "Quest", "status": "active"}],
            conditions=[{"id": "cond_1", "label": "Wounded", "description": "Hurts"}],
        )

        assert "inv_1" in user_prompt
        assert "Sword" in user_prompt
        assert "Sharp" in user_prompt

    def test_renders_compendium_npc_ids(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")))
        user_prompt = env.get_template("compact_user.j2").render(
            turns=[],
            active_quests=[],
            npc_names=[],
            pressures=[],
            inventory=[],
            compendium_npcs=[("npc_a", {"name": "Alice", "title": "Wizard", "aliases": ["Alicia"]})],
            all_quests=[],
            conditions=[],
        )

        assert "npc_a" in user_prompt
        assert "Alice" in user_prompt
        assert "Wizard" in user_prompt
        assert "Alicia" in user_prompt

    def test_renders_recent_events(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")))
        user_prompt = env.get_template("compact_user.j2").render(
            turns=[],
            active_quests=[],
            npc_names=[],
            pressures=[],
            inventory=[],
            compendium_npcs=[],
            all_quests=[],
            conditions=[],
            recent_events=[
                {"id": "e1", "text": "You arrived in town.", "turn": 1},
                {"id": "e2", "text": "You met Caron.", "turn": 2},
            ],
        )

        assert "RECENT EVENTS" in user_prompt
        assert "e1" in user_prompt
        assert "You arrived in town" in user_prompt
        assert "e2" in user_prompt
        assert "You met Caron" in user_prompt

    def test_renders_all_template_vars(self):
        from jinja2 import Environment, FileSystemLoader

        env = Environment(loader=FileSystemLoader(str(Path(__file__).parent.parent / "ccya" / "prompts")))
        user_prompt = env.get_template("compact_user.j2").render(
            turns=[{"turn": 1, "input": "Attack", "narrative": "You swing your sword."}],
            arc={"visible_goal": "Find the artifact", "active_threads": [{"summary": "Locate the artifact", "urgency": "normal"}]},
            npc_names=["Alice", "Bob"],
            pressures=[{"id": "press_1", "text": "Chase", "urgency": "immediate"}],
            inventory=[{"id": "inv_1", "name": "Sword", "amount": 1, "notes": "Sharp"}],
            compendium_npcs=[("npc_a", {"name": "Alice", "title": "Wizard", "aliases": []})],
            conditions=[{"id": "cond_1", "label": "Wounded", "description": "Hurts"}],
            recent_events=[{"id": "e1", "text": "Event one", "turn": 1}],
        )

        assert "TURN 1" in user_prompt or "Turn 1" in user_prompt
        assert "Attack" in user_prompt
        assert "Find the artifact" in user_prompt
        assert "Alice" in user_prompt
        assert "press_1" in user_prompt
        assert "Chase" in user_prompt
        assert "inv_1" in user_prompt
        assert "cond_1" in user_prompt
        assert "Wounded" in user_prompt
        assert "RECENT EVENTS" in user_prompt
        assert "e1" in user_prompt

    def test_build_compact_messages_supplies_all_template_vars(self):
        state = {
            "meta": {"turn": 6},
            "scene": {
                "present_npcs": [{"id": "npc_a", "name": "Alice"}],
                "scene_pressure": [{"id": "press_1", "text": "Chase", "urgency": "immediate"}],
                "recent_events": [{"id": "e1", "text": "Event one", "turn": 1}],
            },
            "inventory": [{"id": "inv_1", "name": "Sword", "amount": 1, "notes": "Sharp"}],
            "arc": {
                "visible_goal": "Find the artifact",
                "active_threads": [{"id": "t_1", "summary": "Locate the artifact", "urgency": "normal"}],
            },
            "compendium": {"npcs": {
                "npc_a": {"name": "Alice", "title": "Wizard", "aliases": []},
                "npc_b": {"name": "Bob", "title": "Thief", "aliases": []},
            }},
            "pc": {"conditions": [{"id": "cond_1", "label": "Wounded", "description": "Hurts"}]},
        }
        turns = [{"turn": 1, "input": "Attack", "narrative": "You swing your sword."}]

        from jinja2 import Environment, FileSystemLoader
        template_dir = str(Path(__file__).parent.parent / "ccya" / "prompts")
        env = Environment(loader=FileSystemLoader(template_dir))

        messages = _build_compact_messages(env, state, turns)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

        user_content = messages[1]["content"]
        assert "inv_1" in user_content
        assert "npc_a" in user_content
        assert "npc_b" in user_content
        assert "Find the artifact" in user_content
        assert "press_1" in user_content
        assert "cond_1" in user_content
        assert "e1" in user_content
        assert "Event one" in user_content


# ---------------------------------------------------------------------------
# Phase 1: Compactor sanitization completeness
# ---------------------------------------------------------------------------


class TestSanitizationNonempty:
    def test_none_returns_false(self):
        assert _sanitization_nonempty(None) is False

    def test_empty_result_returns_false(self):
        result = CompactorSanitizationResult.model_validate({})
        assert _sanitization_nonempty(result) is False

    def test_npc_merge_returns_true(self):
        result = CompactorSanitizationResult.model_validate({
            "npc_merge": [{"keep_id": "a", "remove_ids": ["b"]}],
        })
        assert _sanitization_nonempty(result) is True

    def test_inventory_remove_returns_true(self):
        result = CompactorSanitizationResult.model_validate({
            "inventory_remove": [{"id": "item1", "confidence": "high"}],
        })
        assert _sanitization_nonempty(result) is True

    def test_pressure_remove_returns_true(self):
        result = CompactorSanitizationResult.model_validate({
            "pressure_remove": [{"id": "p1", "confidence": "medium"}],
        })
        assert _sanitization_nonempty(result) is True

    def test_condition_remove_returns_true(self):
        result = CompactorSanitizationResult.model_validate({
            "condition_remove": [{"id": "c1", "confidence": "high"}],
        })
        assert _sanitization_nonempty(result) is True

    def test_recent_events_compact_not_counted(self):
        result = CompactorSanitizationResult.model_validate({
            "recent_events_compact": [{"id": "e1", "text": "Event", "turn": 1}],
        })
        assert _sanitization_nonempty(result) is False


class TestSanitizationLogging:
    def test_structured_log_emitted(self, caplog):
        import logging
        state = {
            "meta": {"turn": 6},
            "compendium": {"npcs": {"npc_a": {"name": "Alice", "aliases": []}}},
            "scene": {"present_npcs": [], "scene_pressure": []},
            "inventory": [{"id": "inv_1", "name": "Sword", "amount": 1}],
            "pc": {"conditions": [{"id": "cond_1", "label": "Wounded", "description": ""}]},
        }
        san = CompactorSanitizationResult.model_validate({
            "npc_merge": [{"keep_id": "npc_a", "remove_ids": []}],
            "inventory_remove": [{"id": "inv_1", "confidence": "high"}],
            "pressure_remove": [],
            "condition_remove": [{"id": "cond_1", "confidence": "high"}],
        })
        with caplog.at_level(logging.INFO):
            _apply_sanitization(state, san)
        assert any("compactor sanitization applied" in r.getMessage() for r in caplog.records)
        applied_log = [r for r in caplog.records if "compactor sanitization applied" in r.getMessage()][0]
        assert applied_log.inventory_removed == 1
        assert applied_log.npcs_merged == 1
        assert applied_log.pressures_removed == 0
        assert applied_log.conditions_removed == 1


# ---------------------------------------------------------------------------
# Phase 3: Compaction event emission
# ---------------------------------------------------------------------------


class TestCompactionEventEmission:
    def _write_chronicle(self, save_dir: Path, turns: list[tuple[int, str, str]]) -> None:
        lines: list[str] = []
        for i, (turn_num, user_input, narrative) in enumerate(turns):
            lines.append(f"\n\n## Turn {turn_num} — {user_input}\n\n{narrative}")
        (save_dir / "chronicle.md").write_text("".join(lines))

    def _make_state(self, turn: int, last_compacted_turn: int = 0) -> dict:
        return {
            "meta": {"turn": turn, "last_compacted_turn": last_compacted_turn, "prior_history": []},
            "scene": {"tags": [], "recent_events": [], "scene_pressure": [], "present_npcs": []},
            "inventory": [],
            "compendium": {"npcs": {}},
            "pc": {"conditions": []},
        }

    @pytest.mark.asyncio
    async def test_compaction_event_written_when_compaction_runs(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 7)
        ])
        state = self._make_state(6)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        with _mock_compact_llm():
            _, compaction_ran = await maybe_compact(tmp_path, state, config)
        assert compaction_ran is True
        events_path = tmp_path / "events.jsonl"
        assert events_path.exists()
        lines = events_path.read_text().strip().splitlines()
        assert len(lines) == 1
        event = __import__("json").loads(lines[0])
        assert event["kind"] == "compaction"
        assert event["turn"] == 6
        assert event["compact_start"] == 1
        assert event["compact_end"] == 4
        assert event["bullets_count"] == 2
        assert len(event["bullets_preview"]) == 2
        assert event["sanitization"] is not None

    @pytest.mark.asyncio
    async def test_no_compaction_event_when_compaction_does_not_run(self, tmp_path: Path):
        self._write_chronicle(tmp_path, [
            (i, f"Action {i}", f"Narrative {i}") for i in range(1, 7)
        ])
        state = self._make_state(5)
        config = EngineConfig(window_turns=3, compact_every=6, recent_turns_min=2)
        _, compaction_ran = await maybe_compact(tmp_path, state, config)
        assert compaction_ran is False
        events_path = tmp_path / "events.jsonl"
        assert not events_path.exists()


# ---------------------------------------------------------------------------
# Phase 0: Compactor atomic write (_write_compacted_block)
# ---------------------------------------------------------------------------


class TestWriteCompactedBlockAtomic:
    def _write_chronicle(self, save_dir: Path, content: str) -> None:
        (save_dir / "chronicle.md").write_text(content)

    def test_write_compacted_block_no_tmp_left_on_success(self, tmp_path: Path):
        self._write_chronicle(tmp_path, "## Turn 1 — First\n\nNarrative 1\n\n")
        from ccya.engine.compactor import _write_compacted_block
        _write_compacted_block(tmp_path, "- [T1] Compacted bullet", 1, 1)
        assert not (tmp_path / "chronicle.md.tmp").exists()
        chronicle_text = (tmp_path / "chronicle.md").read_text()
        assert "## COMPACTED" in chronicle_text
        assert "Compacted bullet" in chronicle_text

    def test_write_compacted_block_atomic_on_crash(self, tmp_path: Path):
        self._write_chronicle(tmp_path, "## Turn 1 — First\n\nNarrative 1\n\n")
        from ccya.engine.compactor import _write_compacted_block
        original_text = (tmp_path / "chronicle.md").read_text()
        with mock.patch("os.replace", side_effect=OSError("simulated crash")):
            with pytest.raises(OSError, match="simulated crash"):
                _write_compacted_block(tmp_path, "- [T1] Compacted bullet", 1, 1)
        # Original file should be unchanged
        assert (tmp_path / "chronicle.md").read_text() == original_text
        # .tmp file should exist (write happened, rename did not)
        assert (tmp_path / "chronicle.md.tmp").exists()
        # Cleanup
        (tmp_path / "chronicle.md.tmp").unlink()

    def test_write_compacted_block_uses_utf8_encoding(self, tmp_path: Path):
        self._write_chronicle(tmp_path, "## Turn 1 — First\n\nNarrative 1\n\n")
        from ccya.engine.compactor import _write_compacted_block
        _write_compacted_block(tmp_path, "- [T1] Compacted bullet — café\n", 1, 1)
        chronicle_text = (tmp_path / "chronicle.md").read_text()
        assert "café" in chronicle_text
