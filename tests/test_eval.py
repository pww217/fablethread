"""Tests for ccya.eval module."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

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
            "scene": {"tags": [], "present_npcs": [], "world_state": [], "recent_events": [], "tagline": ""},
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
                "scene": {"tags": [], "present_npcs": [], "world_state": [], "recent_events": [], "tagline": ""},
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
# _find_json_object
# ---------------------------------------------------------------------------


def test_find_json_object_simple():
    from ccya.eval.judge import _find_json_object
    obj = _find_json_object('{"a": 1}')
    assert obj == '{"a": 1}'


def test_find_json_object_nested():
    from ccya.eval.judge import _find_json_object
    obj = _find_json_object('{"a": {"b": 2}}')
    assert obj == '{"a": {"b": 2}}'


def test_find_json_object_with_trailing_text():
    from ccya.eval.judge import _find_json_object
    obj = _find_json_object('{"a": 1} trailing {text}')
    assert obj == '{"a": 1}'


def test_find_json_object_no_braces():
    from ccya.eval.judge import _find_json_object
    assert _find_json_object("no braces here") is None


def test_find_json_object_unmatched():
    from ccya.eval.judge import _find_json_object
    assert _find_json_object('{"a": 1') is None


def test_find_json_object_multiline():
    from ccya.eval.judge import _find_json_object
    text = '{\n  "a": 1,\n  "b": 2\n}'
    obj = _find_json_object(text)
    assert obj == text


# ---------------------------------------------------------------------------
# parse_judge_response with trailing braces
# ---------------------------------------------------------------------------


def test_parse_judge_response_trailing_braces():
    from ccya.eval.judge import parse_judge_response
    s = '{"overall_score": 4, "findings": [], "comments": ""} trailing {text}'
    out = parse_judge_response(s)
    assert out["overall_score"] == 4
