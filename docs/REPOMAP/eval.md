# Eval harness — in-process turn driver + LLM judge

## Package structure

| File | Responsibility |
|---|---|
| `ccya/eval/__init__.py` | Re-exports: `EvalConfig`, `Scenario`, `RunResult`, `run_scenario`, `run_judge`, `generate_report` |
| `ccya/eval/config.py` | `EvalConfig`, `InferenceConfig`, `JudgeConfig`, `ReportConfig`, `load_eval_config()` |
| `ccya/eval/runner.py` | `run_scenario()`, `RunResult`, `TurnRecord`, `_build_engine_config()`, `_check_asserts()` |
| `ccya/eval/judge.py` | `run_judge()`, `JudgeResult`, `build_trace()`, `parse_judge_response()` |
| `ccya/eval/report.py` | `generate_report()` — produces REPORT.md with token-regression flags |
| `ccya/eval/scenario.py` | `Scenario`, `Turn`, `TurnAssert`, `load_scenario()`, `discover_scenarios()` |
| `ccya/eval/cli.py` | CLI entry point |

## Public APIs

- **`run_scenario(scenario, eval_config, game_config_path)`** → `RunResult` — in-process `run_turn()` driver over a static eval pack. Runs N turns, collects events, checks assertions.
- **`run_judge(scenario, run_result, eval_config)`** → `JudgeResult` — LLM judge evaluates the run, returns score + findings.
- **`generate_report(run_result, judge_result)`** → `str` — produces REPORT.md markdown with per-stream token regression flags.

## Tier 1 vs Tier 2

- **Tier 1**: `tests/test_engine_pipeline.py` — token-budget ceilings, multi-turn invariants, scope-gating tests. Uses `_FakeLLM`. Runs under `make test`.
- **Tier 2**: `make eval` — in-process `run_turn()` driver over static `eval-pack`, 6-turn `full_cycle` scenario, single LLM judge, REPORT.md with token-regression flags.

## Test files

- `tests/test_eval.py` — Tests for eval config loading, scenario loading, engine config building, run result loading, judge response parsing, assertion checking.
