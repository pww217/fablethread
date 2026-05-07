# Eval harness — in-process turn driver + LLM judge

## Package structure

| File | Responsibility |
|---|---|
| `ccya/eval/__init__.py` | Re-exports: `EvalConfig`, `JudgeResult`, `RunResult`, `Scenario`, `Turn`, `TurnAssert`, `TurnRecord`, `build_trace`, `discover_scenarios`, `engine_mirror`, `find_previous_run`, `generate_report`, `load_eval_config`, `load_run_result`, `load_scenario`, `parse_judge_response`, `run_judge`, `run_scenario` |
| `ccya/eval/config.py` | `EvalConfig`, `InferenceConfig`, `JudgeConfig` (`context_economy_warn_tokens`), `ReportConfig`, `LoggingConfig`, `load_eval_config()` |
| `ccya/eval/runner.py` | `run_scenario()`, `RunResult`, `TurnRecord`, `_build_engine_config()`, `_check_asserts()`, `_patch_eval_pack_starting_state()`, `_apply_dotpath()`, `load_run_result()`, `find_previous_run()`, `_extract_parse_failures()`, `REPO_ROOT`, `PROMPTS_DIR` |
| `ccya/eval/judge.py` | `run_judge()`, `JudgeResult` (`narrative_recap`, `remediation`), `build_trace()` (truncates to `max_chars`), `_render_static_context()` (world pack, seed state, constants, turn-1 system prompts), `_render_turn_context()` (per-turn user prompts, engine outputs, state snapshots), `_summarize_applied()`, `_summarize_rejected()`, `_context_line()`, `parse_judge_response()`, `_find_json_object()`, `_coerce_score()`, `_lookup_previous_overall()`, `_scope_summary()`, `_trim()`, `REPO_ROOT` |
| `ccya/eval/report.py` | `generate_report()` — produces REPORT.md with token-regression flags, context economy warnings, per-stream totals in combined table. Also: `_read_events()`, `_extract_stream_metrics()`, `_summarize_events()`, `_compute_regressions()`, `_collect_flags()`, `_render_flag_block()`, `_render_judge_summary()`, `_render_combined_table()`, `_render_auto_checker_block()`, `StreamMetrics`, `TurnMetrics`, `StreamRegression`, `Flag` |
| `ccya/eval/scenario.py` | `Scenario` (with `seed_overrides`), `Turn`, `TurnAssert` (with `stream_id`), `load_scenario()`, `discover_scenarios()` |
| `ccya/eval/cli.py` | CLI entry point |
| `ccya/eval/engine_mirror.py` | Live engine constants for scenarios + `constants_block()` for judge traces + `KNOWN_ASSERT_FIELDS` + `KNOWN_SEED_PATHS` + `EXTRACT_STREAMS` |

## Public APIs

- **`run_scenario(scenario, eval_config, game_config_path)`** → `RunResult` — in-process `run_turn()` driver over a static eval pack. Runs N turns, collects events, checks assertions. Applies `scenario.seed_overrides` via `_patch_eval_pack_starting_state`.
- **`run_judge(events_path, eval_config, previous_report_path, game_config_path)`** → `JudgeResult` — LLM judge evaluates events.jsonl, returns score + findings + `narrative_recap` + `remediation`.
- **`generate_report(run_result, judge_result, eval_config)`** → `str` — produces REPORT.md markdown with per-stream token regression flags, context economy warnings, and per-stream totals in combined table.

## Tier 1 vs Tier 2

- **Tier 1**: `tests/test_engine_pipeline.py` — token-budget ceilings, multi-turn invariants, scope-gating tests. Uses `_FakeLLM`. Runs under `make test`.
- **Tier 2**: `make eval` — in-process `run_turn()` driver over static `eval-pack`, 6-turn `full_cycle` scenario, single LLM judge, REPORT.md with token-regression flags.

## Scenario files

- `evals/scenarios/full_cycle.py` — Baseline 7-turn regression scenario
- `evals/scenarios/pressure_lifecycle.py` — Scene pressure urgency escalation and expiry (imports `PRESSURE_BUILDING_AT`, `PRESSURE_IMMEDIATE_AT`)
- `evals/scenarios/gm_beat_lifecycle.py` — `pending_gm_beat` set/surface/consume lifecycle (uses `state_yaml` assert stream)
- `evals/scenarios/momentum_high.py` — High-momentum narration tone (imports `MOMENTUM_MAX`)
- `evals/scenarios/momentum_low.py` — Low-momentum narration tone (imports `MOMENTUM_MIN`)

## Test files

- `tests/test_eval.py` — Tests for eval config loading, scenario loading, engine config building, run result loading, judge response parsing, assertion checking, `build_trace()` full-context trace structure and content.
- `tests/test_eval_schema.py` — Tier 1 schema validation: validates TurnAssert paths against live engine, engine_mirror self-consistency, seed_override path validation.
