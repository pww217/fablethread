"""Tests for turn viewer dynamic mirror — tv_mirror.py and tv.py."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from ccya.server.tv import (
    _turn_viewer_data,
    _tv_extract_stream_status,
    _tv_narration_lines,
    _tv_parse_json_blob,
    _tv_dict_to_lines,
    _tv_state_diff,
    _tv_failures,
)
from ccya.server.tv_mirror import (
    _STREAMS,
    STREAM_BY_KEY,
    _get_nested,
)


# ---------------------------------------------------------------------------
# tv_mirror.py — data definitions
# ---------------------------------------------------------------------------


class TestTvMirrorCompleteness:
    def test_stream_count(self):
        assert len(_STREAMS) == 5

    def test_all_keys_present(self):
        for sd in _STREAMS:
            assert sd.key in STREAM_BY_KEY

    def test_no_duplicate_keys(self):
        keys = [sd.key for sd in _STREAMS]
        assert len(keys) == len(set(keys))

    def test_stream_descriptor_fields(self):
        for sd in _STREAMS:
            assert isinstance(sd.key, str)
            assert isinstance(sd.label, str)
            assert isinstance(sd.stage_css, str)
            assert isinstance(sd.metrics_path, str)
            assert isinstance(sd.prompt_path, str | None)
            assert isinstance(sd.output_subkey, str | None)
            assert isinstance(sd.is_text_output, bool)
            assert isinstance(sd.output_is_json_string, bool)
            assert isinstance(sd.ms_key, str)
            assert isinstance(sd.inputs, list)
            assert isinstance(sd.skip_token_display, bool)

    def test_rules_stream_config(self):
        rules = STREAM_BY_KEY["rules"]
        assert rules.output_is_json_string is True
        assert rules.ms_key == "total_ms"
        assert rules.inputs == []

    def test_narrate_stream_config(self):
        narrate = STREAM_BY_KEY["narrate"]
        assert narrate.is_text_output is True
        assert narrate.prompt_path == "narrate_prompt"
        assert narrate.metrics_path == "narrate"

    def test_extraction_streams_skip_token_display(self):
        for key in ("scene", "state", "progress"):
            sd = STREAM_BY_KEY[key]
            assert sd.skip_token_display is True

    def test_inputs_acyclic(self):
        for idx, sd in enumerate(_STREAMS):
            assert sd.key not in sd.inputs, f"{sd.key} must not appear in its own inputs"
            for inp_key in sd.inputs:
                inp_idx = next(i for i, s in enumerate(_STREAMS) if s.key == inp_key)
                assert inp_idx < idx, f"{sd.key} depends on {inp_key} which appears at index {inp_idx} >= {idx}"


class TestGetNestedCases:
    def test_normal_path(self):
        d = {"a": {"b": {"c": 42}}}
        assert _get_nested(d, "a.b.c") == 42

    def test_missing_intermediate_key(self):
        d = {"a": {"b": {}}}
        assert _get_nested(d, "a.x.c") is None

    def test_non_dict_intermediate(self):
        d = {"a": {"b": "not_a_dict"}}
        assert _get_nested(d, "a.b.c") is None

    def test_single_segment_path(self):
        d = {"top": "value"}
        assert _get_nested(d, "top") == "value"

    def test_empty_dict(self):
        assert _get_nested({}, "anything") is None

    def test_returns_non_dict_values(self):
        d = {"a": [1, 2, 3]}
        assert _get_nested(d, "a") == [1, 2, 3]

    def test_returns_string_value(self):
        d = {"a": "hello"}
        assert _get_nested(d, "a") == "hello"


# ---------------------------------------------------------------------------
# tv.py — helpers
# ---------------------------------------------------------------------------


class TestTvParseJsonBlob:
    def test_valid_json(self):
        assert _tv_parse_json_blob('{"key": "val"}') == {"key": "val"}

    def test_empty_string(self):
        assert _tv_parse_json_blob("") is None

    def test_none(self):
        assert _tv_parse_json_blob(None) is None

    def test_non_dict_json(self):
        assert _tv_parse_json_blob("[1, 2]") is None

    def test_brace_scan(self):
        result = _tv_parse_json_blob('prefix {"key": "val"} suffix')
        assert result == {"key": "val"}


class TestTvDictToLines:
    def test_empty_dict(self):
        assert _tv_dict_to_lines({}) == []

    def test_none_value(self):
        lines = _tv_dict_to_lines({"k": None})
        assert len(lines) == 1
        assert lines[0]["v"] == "null"
        assert lines[0]["dim"] is True

    def test_bool_value(self):
        lines = _tv_dict_to_lines({"k": True})
        assert lines[0]["v"] == "true"

    def test_empty_list(self):
        lines = _tv_dict_to_lines({"k": []})
        assert lines[0]["v"] == "\u2205"

    def test_list_of_primitives(self):
        lines = _tv_dict_to_lines({"k": [1, "a", 2]})
        assert lines[0]["v"] == "1, a, 2"

    def test_list_of_dicts(self):
        lines = _tv_dict_to_lines({"k": [{"id": "x"}, {"id": "y"}]})
        assert "2" in lines[0]["v"]


class TestTvNarrationLines:
    def test_empty(self):
        lines = _tv_narration_lines("")
        assert len(lines) == 1
        assert lines[0]["k"] == "chars"
        assert lines[0]["v"] == "0"

    def test_non_empty(self):
        lines = _tv_narration_lines("hello world")
        assert len(lines) == 2
        assert lines[0]["v"] == "11"
        assert lines[1]["k"] == "text"


class TestTvExtractStreamStatus:
    def test_ok(self):
        assert _tv_extract_stream_status("rules", skipped=False, error=None, attempts=1, rejected=[]) == "ok"

    def test_skipped(self):
        assert _tv_extract_stream_status("scene", skipped=True, error=None, attempts=1, rejected=[]) == "skipped"

    def test_error(self):
        assert _tv_extract_stream_status("state", skipped=False, error="boom", attempts=1, rejected=[]) == "error"

    def test_retried(self):
        assert _tv_extract_stream_status("scene", skipped=False, error=None, attempts=3, rejected=[]) == "retried"

    def test_rejected_state(self):
        rej = [{"field": "inventory_remove", "reason": "not found"}]
        assert _tv_extract_stream_status("state", skipped=False, error=None, attempts=1, rejected=rej) == "rejected"

    def test_rejected_non_state(self):
        rej = [{"field": "inventory_remove", "reason": "not found"}]
        assert _tv_extract_stream_status("scene", skipped=False, error=None, attempts=1, rejected=rej) == "ok"


# ---------------------------------------------------------------------------
# tv.py — _turn_viewer_data integration
# ---------------------------------------------------------------------------


class TestTurnViewerDataEmpty:
    def test_no_events_file(self):
        with TemporaryDirectory() as td:
            rows, has_errors = _turn_viewer_data(Path(td))
            assert rows == []
            assert has_errors is True

    def test_empty_events_file(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            path.write_text("")
            rows, has_errors = _turn_viewer_data(Path(td))
            assert rows == []
            assert has_errors is True


class TestTurnViewerDataMinimalEvent:
    def test_minimal_event(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            event = {
                "turn": 1,
                "trace_id": "abc123",
                "scope": {
                    "active_domains": [],
                },
            }
            path.write_text(json.dumps(event) + "\n")
            rows, has_errors = _turn_viewer_data(Path(td))
            assert len(rows) == 1
            row = rows[0]

            # streams has all 5 keys
            assert set(row["streams"].keys()) == {"rules", "narrate", "scene", "state", "progress"}
            for sd in _STREAMS:
                assert "status" in row["streams"][sd.key]
                assert "status_class" in row["streams"][sd.key]
                assert "stage_class" in row["streams"][sd.key]

            # row_kind and total_tt_ms_raw
            assert row["row_kind"] == "turn"
            assert row["total_tt_ms_raw"] == 0

            # inputs_snapshot has streams with inputs (narrate, scene, state, progress)
            assert "narrate" in row["inputs_snapshot"]
            assert "scene" in row["inputs_snapshot"]
            assert "state" in row["inputs_snapshot"]
            assert "progress" in row["inputs_snapshot"]

            # prompts dict has all 5 keys
            assert set(row["prompts"].keys()) == {"rules", "narrate", "scene", "state", "progress"}


class TestTurnViewerDataRealEvent:
    def test_realistic_event(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            event = {
                "turn": 1,
                "trace_id": "a1b2c3d4e5f6",
                "input": "I search the crate for useful items.",
                "scope": {
                    "active_domains": ["scene", "compendium_npc"],
                },
                "rules": {
                    "intent_verb": "search",
                    "intent": "search the crate for useful items",
                    "rolled": [3, 5],
                    "total_ms": 1200,
                    "tokens_in": 500,
                    "tokens_out": 50,
                    "skill": "perception",
                    "difficulty": 2,
                    "dice": [3, 5],
                    "stat_mod": 1,
                    "diff_mod": 2,
                    "cond_mod": 0,
                    "final_total": 11,
                    "band": "boon",
                    "outcome_summary": "You find a rusted key.",
                },
                "narrate": {
                    "first_token_ms": 200,
                    "total_ms": 3500,
                    "tokens_in": 800,
                    "tokens_out": 150,
                },
                "extract": {
                    "total_ms": 2000,
                    "tokens_in": 900,
                    "tokens_out": 100,
                },
                "extraction": {
                    "scene": {
                        "rendered_system": "Extract scene changes.",
                        "rendered_user": "User input: search the crate.",
                        "output": {"facts": ["found a rusted key"]},
                        "skipped": False,
                        "attempts": 1,
                        "retry_errors": [],
                        "tokens_in": 900,
                        "tokens_out": 100,
                        "ms": 2000,
                        "context_meta": {},
                    },
                    "state": {
                        "skipped": True,
                        "tokens_in": 0,
                        "tokens_out": 0,
                        "ms": 0,
                        "attempts": 0,
                        "retry_errors": [],
                    },
                    "progress": {
                        "rendered_system": "Extract progress.",
                        "rendered_user": "User input: search the crate.",
                        "output": {"progress": []},
                        "skipped": False,
                        "attempts": 1,
                        "retry_errors": [],
                        "tokens_in": 100,
                        "tokens_out": 20,
                        "ms": 500,
                        "context_meta": {},
                    },
                },
                "rules_prompt": {
                    "rendered_system": "Rules system prompt.",
                    "rendered_user": "Rules user prompt.",
                    "output": json.dumps({
                        "intent_verb": "search",
                        "intent": "search the crate for useful items",
                        "rolled": [3, 5],
                        "final_total": 11,
                        "band": "boon",
                    }),
                    "context_meta": {},
                },
                "narrate_prompt": {
                    "rendered_system": "Narrate system prompt.",
                    "rendered_user": "Narrate user prompt.",
                    "output": "You find an unmarked crate. Inside, you discover a rusted key.",
                    "context_meta": {},
                },
                "rejected": [],
            }
            path.write_text(json.dumps(event) + "\n")
            rows, has_errors = _turn_viewer_data(Path(td))
            assert len(rows) == 1
            row = rows[0]

            # streams
            assert row["streams"]["rules"]["tt"] != "\u2014"
            assert row["streams"]["state"]["skipped"] is True
            assert row["streams"]["state"]["tokens_in_display"] == "\u2014"

            # row_kind, total_tt_ms_raw, ms_raw
            assert row["row_kind"] == "turn"
            assert row["total_tt_ms_raw"] == 1200 + 3500 + 2000
            assert row["streams"]["rules"]["ms_raw"] == 1200
            assert row["streams"]["narrate"]["ms_raw"] == 3500
            assert row["streams"]["scene"]["ms_raw"] == 2000
            assert row["streams"]["state"]["ms_raw"] == 0
            assert row["streams"]["progress"]["ms_raw"] == 500

            # inputs_snapshot — rules has no inputs so excluded; all others present
            assert "narrate" in row["inputs_snapshot"]
            assert "scene" in row["inputs_snapshot"]
            assert "state" in row["inputs_snapshot"]
            assert "progress" in row["inputs_snapshot"]

            # prompts
            assert "unmarked crate" in row["prompts"]["narrate"]["output"]

            # connectors — 4 entries (narrate, scene, state, progress have inputs)
            assert len(row["connectors"]) == 4

            # narrate connector has one segment from rules
            narrate_conn = next(c for c in row["connectors"] if c["before_stage"] == "narrate")
            assert len(narrate_conn["segments"]) == 1
            assert narrate_conn["segments"][0]["from"] == "rules"

            # scene connector has segments for rules and narrate
            scene_conn = next(c for c in row["connectors"] if c["before_stage"] == "scene")
            scene_froms = {s["from"] for s in scene_conn["segments"]}
            assert scene_froms == {"rules", "narrate"}

            # trace_id shortening
            assert row["trace_id"] == "a1b2c3d4"


# ---------------------------------------------------------------------------
# Phase 02 — _tv_state_diff and _tv_failures
# ---------------------------------------------------------------------------


class TestTvStateDiff:
    def test_state_diff_with_inventory_add(self):
        ev = {
            "extraction": {
                "scene": {
                    "output": {"facts": ["found a rusted key"]},
                    "skipped": False,
                    "attempts": 1,
                    "retry_errors": [],
                    "tokens_in": 900,
                    "tokens_out": 100,
                    "ms": 2000,
                    "context_meta": {},
                },
                "state": {
                    "output": {"inventory_add": [{"id": "key1", "name": "rusted key"}]},
                    "skipped": False,
                    "attempts": 1,
                    "retry_errors": [],
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "ms": 500,
                    "context_meta": {},
                },
                "progress": {
                    "output": {},
                    "skipped": True,
                    "attempts": 0,
                    "retry_errors": [],
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "ms": 0,
                    "context_meta": {},
                },
            },
            "rejected": [],
        }
        changes = _tv_state_diff(ev)
        assert len(changes) == 2
        assert changes[0]["domain"] == "scene"
        assert changes[0]["field"] == "facts"
        assert changes[0]["op"] == "set"
        assert changes[0]["rejected"] is False
        assert changes[1]["domain"] == "state"
        assert changes[1]["field"] == "inventory_add"
        assert changes[1]["op"] == "add"
        assert "[1] key1" in changes[1]["value"]

    def test_state_diff_with_rejection(self):
        ev = {
            "extraction": {
                "state": {
                    "output": {"inventory_remove": "old_key"},
                    "skipped": False,
                    "attempts": 1,
                    "retry_errors": [],
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "ms": 100,
                    "context_meta": {},
                },
            },
            "rejected": [{"field": "inventory_remove", "reason": "not in inventory"}],
        }
        changes = _tv_state_diff(ev)
        assert len(changes) == 1
        assert changes[0]["field"] == "inventory_remove"
        assert changes[0]["op"] == "remove"
        assert changes[0]["rejected"] is True

    def test_state_diff_empty(self):
        ev = {"extraction": {}, "rejected": []}
        changes = _tv_state_diff(ev)
        assert changes == []


class TestTvFailures:
    def test_failures_with_retry_and_rejection(self):
        streams = {
            "rules": {"error": None, "retry_errors": [], "attempts": 1},
            "narrate": {"error": None, "retry_errors": [], "attempts": 1},
            "scene": {"error": None, "retry_errors": [], "attempts": 1},
            "state": {"error": None, "retry_errors": ["timeout on attempt 1"], "attempts": 2},
            "progress": {"error": "connection refused", "retry_errors": [], "attempts": 1},
        }
        ev = {
            "rejected": [{"field": "inventory_remove", "reason": "not in inventory"}],
        }
        failures = _tv_failures(ev, streams)
        kinds = [f["kind"] for f in failures]
        assert "retry" in kinds
        assert "llm_error" in kinds
        assert "rejection" in kinds
        assert len(failures) == 3
        retry_entry = next(f for f in failures if f["kind"] == "retry")
        assert retry_entry["stream"] == "state"
        assert retry_entry["attempt"] == 1
        error_entry = next(f for f in failures if f["kind"] == "llm_error")
        assert error_entry["stream"] == "progress"
        rejection_entry = next(f for f in failures if f["kind"] == "rejection")
        assert "inventory_remove" in rejection_entry["message"]

    def test_failures_clean(self):
        streams = {
            "rules": {"error": None, "retry_errors": [], "attempts": 1},
            "narrate": {"error": None, "retry_errors": [], "attempts": 1},
            "scene": {"error": None, "retry_errors": [], "attempts": 1},
            "state": {"error": None, "retry_errors": [], "attempts": 1},
            "progress": {"error": None, "retry_errors": [], "attempts": 1},
        }
        ev = {"rejected": []}
        failures = _tv_failures(ev, streams)
        assert failures == []

    def test_failures_top_level_error(self):
        streams = {
            "rules": {"error": None, "retry_errors": [], "attempts": 1},
            "narrate": {"error": None, "retry_errors": [], "attempts": 1},
            "scene": {"error": None, "retry_errors": [], "attempts": 1},
            "state": {"error": None, "retry_errors": [], "attempts": 1},
            "progress": {"error": None, "retry_errors": [], "attempts": 1},
        }
        ev = {"error": "something went wrong"}
        failures = _tv_failures(ev, streams)
        assert len(failures) == 1
        assert failures[0]["kind"] == "top_level_error"
        assert failures[0]["stream"] == ""


class TestRowKeysPhase2:
    def test_row_has_state_diff_and_failures(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            event = {
                "turn": 1,
                "trace_id": "abc123",
                "input": "test",
                "rules": {"total_ms": 100, "tokens_in": 10, "tokens_out": 5},
                "narrate": {"total_ms": 200, "tokens_in": 20, "tokens_out": 10},
                "extract": {"total_ms": 50, "tokens_in": 5, "tokens_out": 2},
                "extraction": {
                    "scene": {"output": {"facts": ["test fact"]}, "skipped": False, "attempts": 1, "retry_errors": [], "tokens_in": 0, "tokens_out": 0, "ms": 30, "context_meta": {}},
                    "state": {"output": {}, "skipped": True, "attempts": 0, "retry_errors": [], "tokens_in": 0, "tokens_out": 0, "ms": 0, "context_meta": {}},
                    "progress": {"output": {}, "skipped": True, "attempts": 0, "retry_errors": [], "tokens_in": 0, "tokens_out": 0, "ms": 0, "context_meta": {}},
                },
                "rejected": [],
            }
            path.write_text(json.dumps(event) + "\n")
            rows, _ = _turn_viewer_data(Path(td))
            row = rows[0]
            assert "state_diff" in row
            assert "failures" in row
            assert "scope" not in row
            assert "state_rejections" not in row


# ---------------------------------------------------------------------------
# Phase 03 — Compaction row parsing
# ---------------------------------------------------------------------------


class TestCompactionRowParsing:
    def test_compaction_row_parsed_correctly(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            compaction_event = {
                "kind": "compaction",
                "turn": 6,
                "compact_start": 1,
                "compact_end": 3,
                "bullets_count": 2,
                "sanitization": {
                    "npc_merge": [{"keep_id": "a", "remove_ids": ["b"]}],
                    "inventory_remove": [],
                    "quest_close": [],
                    "pressure_remove": [],
                    "condition_remove": [],
                    "recent_events_compact_count": 1,
                },
                "bullets_preview": ["- [T1] Bullet one", "- [T2] Bullet two"],
            }
            path.write_text(json.dumps(compaction_event) + "\n")
            rows, _ = _turn_viewer_data(Path(td))
            assert len(rows) == 1
            row = rows[0]
            assert row["row_kind"] == "compaction"
            assert row["turn"] == 6
            assert row["compact_start"] == 1
            assert row["compact_end"] == 3
            assert row["bullets_count"] == 2
            assert row["bullets_preview"] == ["- [T1] Bullet one", "- [T2] Bullet two"]
            assert row["has_sanitization"] is True
            assert row["sanitization"] is not None
            assert len(row["sanitization"]["npc_merge"]) == 1

    def test_compaction_row_no_sanitization(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            compaction_event = {
                "kind": "compaction",
                "turn": 6,
                "compact_start": 1,
                "compact_end": 3,
                "bullets_count": 2,
                "sanitization": None,
                "bullets_preview": ["- [T1] Bullet one"],
            }
            path.write_text(json.dumps(compaction_event) + "\n")
            rows, _ = _turn_viewer_data(Path(td))
            row = rows[0]
            assert row["row_kind"] == "compaction"
            assert row["has_sanitization"] is False
            assert row["sanitization"] is None

    def test_mixed_turn_and_compaction_rows(self):
        with TemporaryDirectory() as td:
            path = Path(td) / "events.jsonl"
            turn_event = {
                "turn": 5,
                "trace_id": "abc123",
                "input": "test",
                "rules": {"total_ms": 100, "tokens_in": 10, "tokens_out": 5},
                "narrate": {"total_ms": 200, "tokens_in": 20, "tokens_out": 10},
                "extract": {"total_ms": 50, "tokens_in": 5, "tokens_out": 2},
                "extraction": {
                    "scene": {"output": {}, "skipped": True, "attempts": 0, "retry_errors": [], "tokens_in": 0, "tokens_out": 0, "ms": 0, "context_meta": {}},
                    "state": {"output": {}, "skipped": True, "attempts": 0, "retry_errors": [], "tokens_in": 0, "tokens_out": 0, "ms": 0, "context_meta": {}},
                    "progress": {"output": {}, "skipped": True, "attempts": 0, "retry_errors": [], "tokens_in": 0, "tokens_out": 0, "ms": 0, "context_meta": {}},
                },
                "rejected": [],
            }
            compaction_event = {
                "kind": "compaction",
                "turn": 6,
                "compact_start": 1,
                "compact_end": 3,
                "bullets_count": 2,
                "sanitization": None,
                "bullets_preview": ["- [T1] Bullet one"],
            }
            path.write_text(json.dumps(turn_event) + "\n" + json.dumps(compaction_event) + "\n")
            rows, _ = _turn_viewer_data(Path(td))
            assert len(rows) == 2
            assert rows[0]["row_kind"] == "compaction"
            assert rows[1]["row_kind"] == "turn"
