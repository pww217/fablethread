"""Tests for ccya.eval module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
import yaml

from ccya.eval.config import EvalConfig, InferenceConfig, load_eval_config
from ccya.eval.runner import (
    _build_engine_config,
    _patch_eval_pack_starting_state,
    _utc_ts,
    find_previous_run,
    load_run_result,
)
from ccya.eval.scenario import load_scenario


# ---------------------------------------------------------------------------
# load_eval_config
# ---------------------------------------------------------------------------


def test_load_eval_config_default():
    cfg = load_eval_config()
    assert cfg.default_pack == "eval-pack"
    assert cfg.default_save_root == "~/.cache/ccya-eval"
    assert cfg.runs_dir == "evals/runs"
    assert cfg.inference.temperature_override is None
    assert cfg.inference.cache is False
    assert cfg.judge.enabled is True
    assert cfg.report.token_warn_pct == 10.0


def test_load_eval_config_custom(tmp_path: Path):
    cfg_yaml = tmp_path / "evals" / "config.yaml"
    cfg_yaml.parent.mkdir()
    cfg_yaml.write_text(
        yaml.dump({
            "default_pack": "my-pack",
            "default_save_root": "/tmp/my-eval",
            "runs_dir": "my-runs",
            "inference": {"temperature_override": 0.5, "cache": True},
            "judge": {"enabled": False, "model": "test-model", "temperature": 0.7},
            "report": {"token_warn_pct": 15.0, "token_fail_pct": 30.0},
        })
    )
    cfg = load_eval_config(cfg_yaml)
    assert cfg.default_pack == "my-pack"
    assert cfg.default_save_root == "/tmp/my-eval"
    assert cfg.runs_dir == "my-runs"
    assert cfg.inference.temperature_override == 0.5
    assert cfg.inference.cache is True
    assert cfg.judge.enabled is False
    assert cfg.judge.model == "test-model"
    assert cfg.judge.temperature == 0.7
    assert cfg.report.token_warn_pct == 15.0
    assert cfg.report.token_fail_pct == 30.0


def test_load_eval_config_missing():
    with pytest.raises(FileNotFoundError):
        load_eval_config("/nonexistent/path.yaml")


# ---------------------------------------------------------------------------
# load_scenario
# ---------------------------------------------------------------------------


def test_load_scenario(tmp_path: Path):
    scenario_py = tmp_path / "test_scenario.py"
    scenario_py.write_text(
        "from ccya.eval.scenario import Scenario, Turn\n"
        "scenario = Scenario(\n"
        "    id='test',\n"
        "    pack='eval-pack',\n"
        "    description='A test scenario.',\n"
        "    turns=[Turn(input='Hello', phase='dialogue', expects=['scope_skips_rules'])],\n"
        ")\n"
    )
    sc = load_scenario(scenario_py)
    assert sc.id == "test"
    assert sc.pack == "eval-pack"
    assert sc.description == "A test scenario."
    assert len(sc.turns) == 1
    assert sc.turns[0].input == "Hello"
    assert sc.turns[0].phase == "dialogue"
    assert sc.turns[0].expects == ["scope_skips_rules"]


def test_load_scenario_missing_file():
    with pytest.raises(FileNotFoundError):
        load_scenario("/nonexistent/scenario.py")


def test_load_scenario_no_scenario_attr(tmp_path: Path):
    scenario_py = tmp_path / "bad_scenario.py"
    scenario_py.write_text("foo = 42\n")
    with pytest.raises(AttributeError):
        load_scenario(scenario_py)


# ---------------------------------------------------------------------------
# _build_engine_config
# ---------------------------------------------------------------------------


def test_build_engine_config_defaults():
    eval_cfg = EvalConfig()
    ec = _build_engine_config(eval_cfg)
    assert ec.model == "mlx-community/gemma-4-26b-a4b-it-mxfp8"
    assert ec.narrate_temperature == 0.9
    assert ec.extract_temperature == 0.4
    assert ec.rules_temperature == 0.2
    assert ec.generate_seed_temperature == 0.9


def test_build_engine_config_temperature_override():
    eval_cfg = EvalConfig()
    eval_cfg.inference = InferenceConfig(temperature_override=0.0)
    ec = _build_engine_config(eval_cfg)
    assert ec.narrate_temperature == 0.0
    assert ec.extract_temperature == 0.0
    assert ec.rules_temperature == 0.0
    assert ec.generate_seed_temperature == 0.0


def test_build_engine_config_custom_game_config(tmp_path: Path):
    game_cfg = tmp_path / "config.yaml"
    game_cfg.write_text(
        yaml.dump({
            "llm": {
                "host": "http://test:9999/v1",
                "model": "test-model",
                "request_timeout_s": 300,
                "narrate_temperature": 0.5,
                "extract_temperature": 0.3,
                "max_extract_retries": 3,
                "enable_extract_thinking": True,
                "enable_narrate_thinking": True,
                "prompt_token_budget": 16384,
                "generate_seed_temperature": 0.7,
                "generate_seed_max_retries": 2,
            },
            "rules": {"temperature": 0.1, "max_retries": 5},
            "game": {
                "window_turns": 5,
                "chronicle_prefix_budget_tokens": 2000,
                "recent_events_max": 20,
            },
            "logging": {
                "log_llm_io": True,
                "log_llm_io_max_chars": 8000,
                "log_prompts": True,
            },
        })
    )
    eval_cfg = EvalConfig()
    ec = _build_engine_config(eval_cfg, game_config_path=game_cfg)
    assert ec.host == "http://test:9999/v1"
    assert ec.model == "test-model"
    assert ec.prompt_token_budget == 16384
    assert ec.request_timeout_s == 300
    assert ec.narrate_temperature == 0.5
    assert ec.extract_temperature == 0.3
    assert ec.max_extract_retries == 3
    assert ec.window_turns == 5
    assert ec.chronicle_prefix_budget_tokens == 2000
    assert ec.recent_events_max == 20
    assert ec.enable_extract_thinking is True
    assert ec.enable_narrate_thinking is True
    assert ec.generate_seed_temperature == 0.7
    assert ec.generate_seed_max_retries == 2
    assert ec.log_llm_io is True
    assert ec.log_llm_io_max_chars == 8000
    assert ec.log_prompts is True
    assert ec.rules_temperature == 0.1
    assert ec.max_rules_retries == 5


def test_build_engine_config_missing_game_config():
    eval_cfg = EvalConfig()
    with pytest.raises(FileNotFoundError):
        _build_engine_config(eval_cfg, game_config_path=Path("/nonexistent/config.yaml"))


# ---------------------------------------------------------------------------
# _patch_eval_pack_starting_state
# ---------------------------------------------------------------------------


def test_patch_eval_pack_starting_state(tmp_path: Path):
    save_dir = tmp_path / "save"
    save_dir.mkdir()
    state_yaml = save_dir / "state.yaml"
    state_yaml.write_text(
        yaml.dump({
            "meta": {"game_name": "test", "turn": 0, "setting_pack": "eval-pack", "model": ""},
            "pc": {"name": "Test", "tagline": "", "bio": "", "stats": {}, "conditions": [], "momentum": 0},
            "location": {"id": "", "name": "", "description": ""},
            "inventory": [],
            "quests": [],
            "scene": {"tags": [],  "world_state": [], "recent_events": [], "tagline": ""},
            "compendium": {"npcs": {}},
        })
    )
    _patch_eval_pack_starting_state(save_dir, "eval-pack")
    state = yaml.safe_load(state_yaml.read_text())
    assert len(state["pc"]["conditions"]) == 2
    assert state["pc"]["conditions"][0]["id"] == "bruised_ribs"
    assert state["pc"]["conditions"][0]["added_turn"] == 8
    assert state["pc"]["conditions"][1]["id"] == "low_morale"
    assert state["pc"]["conditions"][1]["added_turn"] == 10


def test_patch_eval_pack_starting_state_noop():
    save_dir = Path(tempfile.mkdtemp())
    try:
        state_yaml = save_dir / "state.yaml"
        state_yaml.write_text(
            yaml.dump({
                "meta": {"game_name": "test", "turn": 0, "setting_pack": "other-pack", "model": ""},
                "pc": {"name": "Test", "tagline": "", "bio": "", "stats": {}, "conditions": [], "momentum": 0},
                "location": {"id": "", "name": "", "description": ""},
                "inventory": [],
                "quests": [],
                "scene": {"tags": [],  "world_state": [], "recent_events": [], "tagline": ""},
                "compendium": {"npcs": {}},
            })
        )
        _patch_eval_pack_starting_state(save_dir, "other-pack")
        state = yaml.safe_load(state_yaml.read_text())
        assert len(state["pc"]["conditions"]) == 0
    finally:
        import shutil
        shutil.rmtree(save_dir)


# ---------------------------------------------------------------------------
# _utc_ts
# ---------------------------------------------------------------------------


def test_utc_ts_format():
    ts = _utc_ts()
    assert len(ts) == 16  # YYYYMMDDTHHMMSSZ
    assert ts.endswith("Z")


# ---------------------------------------------------------------------------
# find_previous_run
# ---------------------------------------------------------------------------


def test_find_previous_run_no_runs_dir():
    assert find_previous_run(Path("/nonexistent"), "test") is None


def test_find_previous_run_empty_dir(tmp_path: Path):
    assert find_previous_run(tmp_path, "test") is None


def test_find_previous_run_one_run(tmp_path: Path):
    run_dir = tmp_path / "20260101T000000Z"
    run_dir.mkdir()
    (run_dir / "test.run.json").write_text("{}")
    result = find_previous_run(tmp_path, "test")
    assert result == run_dir / "test.run.json"


def test_find_previous_run_multiple_runs(tmp_path: Path):
    run_dir1 = tmp_path / "20260101T000000Z"
    run_dir1.mkdir()
    (run_dir1 / "test.run.json").write_text("{}")
    run_dir2 = tmp_path / "20260102T000000Z"
    run_dir2.mkdir()
    (run_dir2 / "test.run.json").write_text("{}")
    result = find_previous_run(tmp_path, "test")
    assert result == run_dir2 / "test.run.json"


def test_find_previous_run_excludes_target(tmp_path: Path):
    run_dir1 = tmp_path / "20260101T000000Z"
    run_dir1.mkdir()
    (run_dir1 / "test.run.json").write_text("{}")
    run_dir2 = tmp_path / "20260102T000000Z"
    run_dir2.mkdir()
    (run_dir2 / "test.run.json").write_text("{}")
    result = find_previous_run(tmp_path, "test", exclude=run_dir2)
    assert result == run_dir1 / "test.run.json"


def test_find_previous_run_skips_latest_symlink(tmp_path: Path):
    run_dir = tmp_path / "20260101T000000Z"
    run_dir.mkdir()
    (run_dir / "test.run.json").write_text("{}")
    latest = tmp_path / "latest"
    latest.symlink_to(run_dir, target_is_directory=True)
    result = find_previous_run(tmp_path, "test")
    assert result == run_dir / "test.run.json"


# ---------------------------------------------------------------------------
# load_run_result
# ---------------------------------------------------------------------------


def test_load_run_result(tmp_path: Path):
    run_json = tmp_path / "test.run.json"
    run_json.write_text(
        json.dumps({
            "scenario_id": "test",
            "pack": "eval-pack",
            "model": "test-model",
            "temperature_override": 0.5,
            "started_at": "2026-01-01T00:00:00+00:00",
            "finished_at": "2026-01-01T00:00:01+00:00",
            "save_dir": "/tmp/test-save",
            "output_dir": str(tmp_path),
            "events_jsonl_path": str(tmp_path / "test.events.jsonl"),
            "state_yaml_path": str(tmp_path / "test.state.yaml"),
            "turns": [
                {
                    "turn_number": 1,
                    "input": "Hello",
                    "phase": "dialogue",
                    "expects": ["scope_skips_rules"],
                    "duration_s": 0.5,
                    "error": None,
                    "engine_turn_number": 1,
                    "outcome_summary": "Success",
                    "narrative_chars": 100,
                }
            ],
            "total_errors": 0,
        })
    )
    result = load_run_result(run_json)
    assert result.scenario_id == "test"
    assert result.pack == "eval-pack"
    assert result.model == "test-model"
    assert result.temperature_override == 0.5
    assert len(result.turns) == 1
    assert result.turns[0].turn_number == 1
    assert result.turns[0].input == "Hello"
    assert result.turns[0].phase == "dialogue"
    assert result.turns[0].expects == ["scope_skips_rules"]
    assert result.turns[0].duration_s == 0.5
    assert result.turns[0].error is None
    assert result.turns[0].engine_turn_number == 1
    assert result.turns[0].outcome_summary == "Success"
    assert result.turns[0].narrative_chars == 100
    assert result.total_errors == 0


# ---------------------------------------------------------------------------
# parse_judge_response — YAML front matter
# ---------------------------------------------------------------------------


def test_parse_judge_response_yaml_front_matter():
    from ccya.eval.judge import parse_judge_response

    s = (
        "---\n"
        "mechanical_score: 4\n"
        "narrative_score: 3\n"
        "pipeline_scores:\n"
        "  rules: 4\n"
        "  narrate: 3\n"
        "  extract_scene: 5\n"
        "  extract_state: 4\n"
        "  extract_progress: 3\n"
        "---\n\n"
        "# Mechanical Analysis\n\n"
        "The engine worked well.\n"
    )
    scores, body = parse_judge_response(s)
    assert scores["mechanical_score"] == 4
    assert scores["narrative_score"] == 3
    assert scores["pipeline_scores"]["rules"] == 4
    assert scores["pipeline_scores"]["narrate"] == 3
    assert scores["pipeline_scores"]["extract_scene"] == 5
    assert scores["pipeline_scores"]["extract_state"] == 4
    assert scores["pipeline_scores"]["extract_progress"] == 3
    assert "Mechanical Analysis" in body


def test_parse_judge_response_missing_scores():
    from ccya.eval.judge import parse_judge_response

    s = "---\n---\n\n# No scores here\n"
    scores, body = parse_judge_response(s)
    assert scores == {}


def test_parse_judge_response_with_thinking():
    from ccya.eval.judge import parse_judge_response

    s = (
        "<think>\nSome reasoning\n</think>\n"
        "---\nmechanical_score: 5\nnarrative_score: 5\npipeline_scores:\n  rules: 5\n  narrate: 5\n  extract_scene: 5\n  extract_state: 5\n  extract_progress: 5\n---\n\nDone.\n"
    )
    scores, body = parse_judge_response(s)
    assert scores["mechanical_score"] == 5
    assert scores["narrative_score"] == 5


def test_parse_judge_response_no_front_matter():
    from ccya.eval.judge import parse_judge_response

    s = "Just plain text, no YAML front matter.\n"
    scores, body = parse_judge_response(s)
    assert scores == {}
    assert body == "Just plain text, no YAML front matter."


def test_parse_judge_response_partial_scores():
    from ccya.eval.judge import parse_judge_response

    s = (
        "---\nmechanical_score: 3\n---\n\nOnly mechanical score.\n"
    )
    scores, body = parse_judge_response(s)
    assert scores["mechanical_score"] == 3
    assert "narrative_score" not in scores
    assert scores["pipeline_scores"] == {}


# ---------------------------------------------------------------------------
# _check_asserts — rolled field
# ---------------------------------------------------------------------------


def test_check_asserts_rolled_true():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"rules": {"rolled": True, "skill": "charisma", "band": "success"}}
    asserts = [TurnAssert(stream="rules", field="rolled", expected="true")]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is True
    assert results[0]["detail"] == "rolled=True"


def test_check_asserts_rolled_false():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"rules": {"rolled": False, "intent_verb": "move"}}
    asserts = [TurnAssert(stream="rules", field="rolled", expected="false")]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is True
    assert results[0]["detail"] == "rolled=False"


def test_check_asserts_rolled_mismatch():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"rules": {"rolled": True}}
    asserts = [TurnAssert(stream="rules", field="rolled", expected="false")]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is False


def test_check_asserts_inventory_remove_found():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"applied": {"inventory_remove": [{"id": "credits", "amount": 500}]}}
    asserts = [TurnAssert(stream="extract.state", field="inventory_remove", expected="credits", min_amount=500)]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is True
    assert results[0]["detail"] == "inventory_remove[credits] amount=500"


def test_check_asserts_inventory_remove_not_found():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"applied": {"inventory_remove": []}}
    asserts = [TurnAssert(stream="extract.state", field="inventory_remove", expected="credits", min_amount=200)]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is False
    assert results[0]["detail"] == "inventory_remove[credits] not found"


def test_check_asserts_quest_updates_found():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"applied": {"quest_updates": [{"id": "deliver_the_ledger", "status": "active"}]}}
    asserts = [TurnAssert(stream="extract.progress", field="quest_updates", expected="deliver_the_ledger")]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is True


def test_check_asserts_scene_tags_found():
    from ccya.eval.runner import _check_asserts
    from ccya.eval.scenario import TurnAssert

    event = {"applied": {"scene_tags": ["combat", "stealth"]}}
    asserts = [TurnAssert(stream="extract.scene", field="scene_tags", expected="combat")]
    results = _check_asserts(asserts, event)
    assert len(results) == 1
    assert results[0]["passed"] is True


# ---------------------------------------------------------------------------
# build_trace — full-context trace
# ---------------------------------------------------------------------------


def _make_metadata(**kwargs) -> dict[str, Any]:
    return {
        "__metadata__": True,
        "pack_id": "test-pack",
        "pack_style": "A gritty sci-fi setting.",
        "seed_state": {
            "meta": {"game_name": "test", "turn": 0, "setting_pack": "test-pack", "model": ""},
            "pc": {"name": "Test", "tagline": "", "bio": "", "stats": {}, "conditions": [], "momentum": 0},
            "location": {"id": "", "name": "", "description": ""},
            "inventory": [],
            "quests": [],
            "scene": {"tags": [], "world_state": [], "recent_events": [], "tagline": ""},
            "compendium": {"npcs": {}},
        },
        **kwargs,
    }


def _make_turn_event(
    turn: int = 1,
    input_text: str = "Hello",
    rules_prompt: dict | None = None,
    narrate_prompt: dict | None = None,
    extraction: dict | None = None,
    rules: dict | None = None,
    applied: dict | None = None,
    rejected: list | None = None,
    actions: list | None = None,
    state_snapshot: dict | None = None,
) -> dict[str, Any]:
    return {
        "turn": turn,
        "input": input_text,
        "rules_prompt": rules_prompt or {},
        "narrate_prompt": narrate_prompt or {},
        "extraction": extraction or {},
        "rules": rules or {},
        "applied": applied or {},
        "rejected": rejected or [],
        "actions": actions or [],
        "state_snapshot": state_snapshot or {},
    }


def test_build_trace_full_context_structure():
    from ccya.eval.judge import build_trace

    metadata = _make_metadata()
    turn1 = _make_turn_event(
        turn=1,
        input_text="Attack the guard",
        rules_prompt={
            "rendered_system": "Rules system prompt",
            "rendered_user": "Rules user prompt",
        },
        narrate_prompt={
            "rendered_system": "Narrate system prompt",
            "rendered_user": "Narrate user prompt",
            "output": "You swing your sword.",
        },
        extraction={
            "scene": {"rendered_system": "Scene system", "rendered_user": "Scene user", "output": {"scene_tags": ["combat"]}},
            "state": {"rendered_system": "State system", "rendered_user": "State user", "output": {}},
            "progress": {"rendered_system": "Progress system", "rendered_user": "Progress user", "output": {}},
        },
        rules={"rolled": True, "band": "success", "skill": "strength"},
        applied={"inventory_add": [{"id": "gold", "amount": 10}]},
        state_snapshot={
            "meta": {"turn": 1},
            "inventory": [{"id": "gold", "amount": 10}],
        },
    )

    events = [metadata, turn1]
    trace = build_trace(events)

    assert "## World Pack Style" in trace
    assert "## Seed State" in trace
    assert "## Engine Constants" in trace
    assert "## System Prompts (identical every turn)" in trace
    assert "### Rules System Prompt" in trace
    assert "### Narrate System Prompt" in trace
    assert "### Extract Scene System Prompt" in trace
    assert "### Extract State System Prompt" in trace
    assert "### Extract Progress System Prompt" in trace
    assert "TURN 1" in trace
    assert "## User Prompts" in trace
    assert "## Engine Outputs" in trace
    assert "### Rules" in trace
    assert "### Narration" in trace
    assert "### Extract Scene" in trace
    assert "### Extract State" in trace
    assert "### Extract Progress" in trace
    assert "### Applied Deltas" in trace
    assert "### Context Telemetry" in trace
    assert "### State After Turn" in trace
    assert "A gritty sci-fi setting." in trace


def test_build_trace_no_metadata():
    from ccya.eval.judge import build_trace

    turn1 = _make_turn_event(turn=1, input_text="Hello")
    events = [turn1]
    trace = build_trace(events)

    assert "## Engine Constants" in trace
    assert "TURN 1" in trace


def test_build_trace_all_turns_included():
    """Verify all turns are included in the trace (no truncation)."""
    from ccya.eval.judge import build_trace

    metadata = _make_metadata()
    events = [metadata]

    for i in range(1, 11):
        events.append(_make_turn_event(
            turn=i,
            input_text=f"Turn {i}",
            narrate_prompt={"output": f"Narration for turn {i}"},
            state_snapshot={"meta": {"turn": i}},
        ))

    trace = build_trace(events)

    assert "TURN 1" in trace
    assert "TURN 10" in trace
    # All 10 turns should be present
    for i in range(1, 11):
        assert f"TURN {i}" in trace
    assert "[... trace truncated" not in trace


def test_build_trace_retry_turns():
    from ccya.eval.judge import build_trace

    metadata = _make_metadata()
    # Retry turn: empty rules_prompt (from run_turn_retry)
    retry_turn = _make_turn_event(
        turn=2,
        input_text="Retry",
        rules_prompt={},
        narrate_prompt={
            "rendered_system": "Narrate system",
            "rendered_user": "Narrate user",
            "output": "You try again.",
        },
        state_snapshot={"meta": {"turn": 2}},
    )
    events = [metadata, retry_turn]
    trace = build_trace(events)

    assert "TURN 2" in trace
    assert "You try again." in trace


def test_build_trace_no_truncation_small_run():
    from ccya.eval.judge import build_trace

    metadata = _make_metadata()
    events = [metadata]

    for i in range(1, 4):
        events.append(_make_turn_event(
            turn=i,
            input_text=f"Turn {i}",
            narrate_prompt={"output": f"Narration {i}"},
            state_snapshot={"meta": {"turn": i}},
        ))

    trace = build_trace(events)

    assert "TURN 1" in trace
    assert "TURN 2" in trace
    assert "TURN 3" in trace
    assert "[... trace truncated" not in trace


def test_metadata_event_format():
    from ccya.eval.judge import build_trace

    metadata = _make_metadata()
    events = [metadata]
    trace = build_trace(events)

    assert "test-pack" in trace
    assert "A gritty sci-fi setting." in trace
    assert '"game_name": "test"' in trace


# ---------------------------------------------------------------------------
# Phase 2: Dedup tests
# ---------------------------------------------------------------------------


def test_strip_immutable_sections():
    from ccya.eval.judge import _strip_immutable_sections
    text = "before\n<<<TRACE_IMMUTABLE_START>>>\n## Factions\n- one\n- two\n<<<TRACE_IMMUTABLE_END>>>\nafter"
    out = _strip_immutable_sections(text)
    assert "## Factions" not in out
    assert "before" in out
    assert "after" in out
    assert "_(immutable section omitted" in out


def test_strip_immutable_sections_no_markers():
    from ccya.eval.judge import _strip_immutable_sections
    text = "no markers here"
    assert _strip_immutable_sections(text) == text


def test_strip_remaining_markers_when_dedup_off():
    from ccya.eval.judge import _strip_remaining_markers
    text = "before\n<<<TRACE_IMMUTABLE_START>>>\nbody\n<<<TRACE_IMMUTABLE_END>>>\nafter"
    out = _strip_remaining_markers(text)
    assert "<<<TRACE" not in out
    assert "body" in out


def test_diff_state_snapshots_simple():
    from ccya.eval.judge import _diff_state_snapshots
    prev = {"meta": {"turn": 1}, "pc": {"momentum": 0}}
    cur = {"meta": {"turn": 2}, "pc": {"momentum": 1}}
    diff = _diff_state_snapshots(prev, cur)
    assert diff == {"meta": {"turn": {"from": 1, "to": 2}}, "pc": {"momentum": {"from": 0, "to": 1}}}


def test_diff_state_snapshots_inventory_add_remove():
    from ccya.eval.judge import _diff_state_snapshots
    prev = {"inventory": [{"id": "credits", "amount": 500}]}
    cur = {"inventory": [{"id": "credits", "amount": 500}, {"id": "key", "amount": 1}]}
    diff = _diff_state_snapshots(prev, cur)
    assert diff == {"inventory": {"added": [{"id": "key", "amount": 1}]}}


def test_diff_state_snapshots_inventory_change():
    from ccya.eval.judge import _diff_state_snapshots
    prev = {"inventory": [{"id": "credits", "amount": 500}]}
    cur = {"inventory": [{"id": "credits", "amount": 300}]}
    diff = _diff_state_snapshots(prev, cur)
    assert diff == {"inventory": {"changed": [{"from": {"id": "credits", "amount": 500}, "to": {"id": "credits", "amount": 300}}]}}


def test_build_trace_dedup_off_keeps_immutable():
    from ccya.eval.judge import build_trace, TraceOptions
    metadata = _make_metadata()
    turn = {
        "turn": 1,
        "input": "hi",
        "narrate_prompt": {
            "rendered_user": "before\n<<<TRACE_IMMUTABLE_START>>>\n## Factions\n- one\n<<<TRACE_IMMUTABLE_END>>>\nafter",
            "output": "narration",
        },
        "extraction": {},
        "rules_prompt": {},
        "state_snapshot": {},
    }
    trace_off = build_trace([metadata, turn], options=TraceOptions(dedup_immutable_sections=False, state_as_diff=False))
    assert "## Factions" in trace_off
    assert "<<<TRACE_IMMUTABLE_START>>>" not in trace_off


def test_build_trace_dedup_on_strips_immutable():
    from ccya.eval.judge import build_trace, TraceOptions
    metadata = _make_metadata()
    turn = {
        "turn": 1,
        "input": "hi",
        "narrate_prompt": {
            "rendered_user": "before\n<<<TRACE_IMMUTABLE_START>>>\n## Factions\n- one\n<<<TRACE_IMMUTABLE_END>>>\nafter",
            "output": "narration",
        },
        "extraction": {},
        "rules_prompt": {},
        "state_snapshot": {},
    }
    trace = build_trace([metadata, turn], options=TraceOptions(dedup_immutable_sections=True, state_as_diff=False))
    assert "## Factions" not in trace
    assert "_(immutable section omitted" in trace


def test_build_trace_state_diff_middle_turns():
    from ccya.eval.judge import build_trace, TraceOptions
    metadata = _make_metadata()
    turns = []
    for i in range(1, 4):
        turns.append({
            "turn": i,
            "input": f"t{i}",
            "rules_prompt": {},
            "narrate_prompt": {},
            "extraction": {},
            "state_snapshot": {"meta": {"turn": i}, "pc": {"momentum": i}},
        })
    trace = build_trace([metadata] + turns, options=TraceOptions(dedup_immutable_sections=False, state_as_diff=True))
    assert "TURN 1" in trace
    assert "TURN 2" in trace
    assert "TURN 3" in trace
    assert "diff vs previous turn" in trace


def test_load_eval_config_trace_defaults():
    from ccya.eval.config import load_eval_config
    cfg = load_eval_config()
    assert cfg.judge.trace.dedup_immutable_sections is True
    assert cfg.judge.trace.state_as_diff is True


def test_load_eval_config_trace_custom(tmp_path: Path):
    from ccya.eval.config import load_eval_config
    import yaml
    cfg_yaml = tmp_path / "evals" / "config.yaml"
    cfg_yaml.parent.mkdir(parents=True)
    cfg_yaml.write_text(yaml.dump({
        "judge": {"trace": {"dedup_immutable_sections": False, "state_as_diff": False}},
    }))
    cfg = load_eval_config(cfg_yaml)
    assert cfg.judge.trace.dedup_immutable_sections is False
    assert cfg.judge.trace.state_as_diff is False


# ---------------------------------------------------------------------------
# Phase 3 — Universal asserts
# ---------------------------------------------------------------------------


def test_universal_recent_events_turn_stamped_pass():
    from ccya.eval.universal_asserts import check_recent_events_turn_stamped
    ev = {"turn": 5, "applied": {"recent_events_add": [{"turn": 5, "text": "x"}]}}
    r = check_recent_events_turn_stamped(ev)
    assert r["passed"] is True


def test_universal_recent_events_turn_stamped_fail():
    from ccya.eval.universal_asserts import check_recent_events_turn_stamped
    ev = {"turn": 5, "applied": {"recent_events_add": [{"turn": 0, "text": "x"}]}}
    r = check_recent_events_turn_stamped(ev)
    assert r["passed"] is False
    assert "turn=0" in r["detail"]


def test_universal_pending_gm_beat_persists_fail():
    from ccya.eval.universal_asserts import check_pending_gm_beat_consumed
    prev = {"state_snapshot": {"scene": {"pending_gm_beat": {"type": "complication"}}}}
    cur = {"state_snapshot": {"scene": {"pending_gm_beat": {"type": "complication"}}}}
    r = check_pending_gm_beat_consumed(cur, prev)
    assert r["passed"] is False


def test_universal_pending_gm_beat_consumed_pass():
    from ccya.eval.universal_asserts import check_pending_gm_beat_consumed
    prev = {"state_snapshot": {"scene": {"pending_gm_beat": {"type": "complication"}}}}
    cur = {"state_snapshot": {"scene": {"pending_gm_beat": None}}}
    r = check_pending_gm_beat_consumed(cur, prev)
    assert r["passed"] is True


def test_universal_location_change_applied_pass():
    from ccya.eval.universal_asserts import check_location_change_applied
    prev = {"state_snapshot": {"location": {"id": "marrows_crossing"}}}
    cur = {"state_snapshot": {"location": {"id": "the_road"}}, "applied": {"location_change": {"id": "the_road"}}}
    r = check_location_change_applied(cur, prev)
    assert r["passed"] is True


def test_universal_location_change_applied_fail():
    from ccya.eval.universal_asserts import check_location_change_applied
    prev = {"state_snapshot": {"location": {"id": "marrows_crossing"}}}
    cur = {"state_snapshot": {"location": {"id": "marrows_crossing"}}, "applied": {"location_change": {"id": "the_road"}}}
    r = check_location_change_applied(cur, prev)
    assert r["passed"] is False


def test_universal_rolled_implies_binding_pass():
    from ccya.eval.universal_asserts import check_rolled_implies_binding
    ev = {"rules": {"rolled": True}, "narrate_prompt": {"rendered_user": "stuff\n## rules_outcome (BINDING — narrate this result)\nbla"}}
    r = check_rolled_implies_binding(ev)
    assert r["passed"] is True


def test_universal_rolled_implies_binding_fail():
    from ccya.eval.universal_asserts import check_rolled_implies_binding
    ev = {"rules": {"rolled": True}, "narrate_prompt": {"rendered_user": "stuff with no binding directive"}}
    r = check_rolled_implies_binding(ev)
    assert r["passed"] is False


def test_universal_npc_mention_extracted_pass():
    from ccya.eval.universal_asserts import check_npc_mention_extracted
    ev = {
        "narrate_prompt": {"output": "Caron leans forward and frowns."},
        "applied": {"npc_update": [{"id": "caron", "name": "Caron"}]},
        "state_snapshot": {},
    }
    r = check_npc_mention_extracted(ev)
    assert r["passed"] is True


def test_universal_npc_mention_extracted_fail():
    from ccya.eval.universal_asserts import check_npc_mention_extracted
    ev = {
        "narrate_prompt": {"output": "A man named Brennan stands at the door."},
        "applied": {},
        "state_snapshot": {"scene": {"present_npcs": []}, "compendium": {"npcs": {}}},
    }
    r = check_npc_mention_extracted(ev)
    assert r["passed"] is False


def test_run_all_universal_asserts_returns_five():
    from ccya.eval.universal_asserts import run_all_universal_asserts
    ev = {"turn": 1}
    rs = run_all_universal_asserts(ev, None)
    assert len(rs) == 5


# ---------------------------------------------------------------------------
# Phase 3 — Deterministic signals in trace
# ---------------------------------------------------------------------------


def test_build_trace_includes_deterministic_signals():
    from ccya.eval.judge import build_trace
    metadata = {"__metadata__": True, "scenario": "test", "pack": "test-pack"}
    turn = {"turn": 1, "input": "x", "rules_prompt": {}, "narrate_prompt": {}, "extraction": {}, "state_snapshot": {}}
    failures = [{"turn": 1, "assertion": "universal.foo", "detail": "bad"}]
    metrics = [{"turn": 1, "rules_tok_in": 100, "narrate_tok_in": 200, "scene_tok_in": 50, "state_tok_in": 0, "progress_tok_in": 80, "parse_failures": 0, "retries": 0}]
    trace = build_trace([metadata, turn], auto_checker_failures=failures, metrics_rows=metrics)
    assert "# Deterministic Signals" in trace
    assert "## Auto-Checker Failures" in trace
    assert "universal.foo" in trace
    assert "## Metrics" in trace
    assert "100" in trace


def test_build_trace_deterministic_signals_empty():
    from ccya.eval.judge import build_trace
    metadata = {"__metadata__": True}
    turn = {"turn": 1, "rules_prompt": {}, "narrate_prompt": {}, "extraction": {}, "state_snapshot": {}}
    trace = build_trace([metadata, turn])
    assert "# Deterministic Signals" not in trace


# ---------------------------------------------------------------------------
# Phase 3 — Metrics rows
# ---------------------------------------------------------------------------


def test_build_metrics_rows():
    from ccya.eval.judge import _build_metrics_rows
    events = [
        {"__metadata__": True},
        {
            "turn": 1,
            "rules_prompt": {"context_meta": {"est_tokens": 500}},
            "narrate_prompt": {"context_meta": {"est_tokens": 300}},
            "extraction": {
                "scene": {"context_meta": {"est_tokens": 200}, "attempts": 1},
                "state": {"context_meta": {"est_tokens": 150}, "attempts": 2},
                "progress": {"context_meta": {"est_tokens": 100}, "attempts": 1},
            },
        },
    ]
    rows = _build_metrics_rows(events)
    assert len(rows) == 1
    assert rows[0]["turn"] == 1
    assert rows[0]["rules_tok_in"] == 500
    assert rows[0]["narrate_tok_in"] == 300
    assert rows[0]["scene_tok_in"] == 200
    assert rows[0]["state_tok_in"] == 150
    assert rows[0]["progress_tok_in"] == 100
    assert rows[0]["parse_failures"] == 0
    assert rows[0]["retries"] == 1  # state had 2 attempts


# ---------------------------------------------------------------------------
# Phase 3 — Engine mirror constants
# ---------------------------------------------------------------------------


def test_engine_mirror_constants_block_includes_schema():
    from ccya.eval.engine_mirror import constants_block
    txt = constants_block()
    assert "Bands" in txt and "crit_success" in txt
    assert "Skills" in txt and "charisma" in txt
    assert "Difficulties" in txt
    assert "PC condition cap" in txt
    assert "Scene named NPC cap" in txt


def test_engine_mirror_schema_constants_exist():
    from ccya.eval.engine_mirror import BANDS, SKILLS, DIFFICULTIES, INTENT_VERBS_HINT, PC_CONDITION_CAP, SCENE_NAMED_NPC_CAP
    assert "crit_success" in BANDS
    assert "charisma" in SKILLS
    assert "normal" in DIFFICULTIES
    assert "attack" in INTENT_VERBS_HINT
    assert PC_CONDITION_CAP == 5
    assert SCENE_NAMED_NPC_CAP == 8
