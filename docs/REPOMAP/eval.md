# Eval harness — in-process turn driver + LLM judge

## Package structure

| File | Responsibility |
|---|---|
| `ccya/eval/__init__.py` | Re-exports: `EvalConfig`, `JudgeResult`, `RunResult`, `Scenario`, `Turn`, `TurnAssert`, `TurnRecord`, `TraceOptions`, `build_trace`, `discover_scenarios`, `engine_mirror`, `find_previous_run`, `generate_report`, `load_eval_config`, `load_run_result`, `load_scenario`, `parse_judge_response`, `run_judge`, `run_scenario` |
| `ccya/eval/config.py` | `EvalConfig`, `InferenceConfig`, `JudgeConfig` (with nested `TraceConfig`, plus `timeout_s` + `max_tokens`), `ReportConfig`, `LoggingConfig`, `load_eval_config()` |
| `ccya/eval/architecture_context.py` | `load_architecture_context()` — extracts `EVAL_CONTEXT` region from `docs/ARCHITECTURE.md` (between `<!-- EVAL_CONTEXT_START -->` and `<!-- EVAL_CONTEXT_END -->` markers), prepends to judge system message |
| `ccya/eval/redundancy.py` | `compute_redundancy_signals()` — detects cross-stream block duplication (min 60 chars/line, min 3 lines/block), returns overlap pairs; `render_redundancy_section()` — formats as markdown table for Deterministic Signals |
| `ccya/eval/compaction_signals.py` | `compute_compaction_signals()` — 14 enumerated capabilities (9 bullet-quality + 5 state-sanitization), returns capability list; `render_compaction_section()` — formats as `[OK]/[FAIL]/[NA]` table for Deterministic Signals |
| `ccya/eval/runner.py` | `run_scenario()`, `RunResult` (with `trace_md_path`, `judge_md_path`), `TurnRecord`, `_build_engine_config()`, `_check_asserts()`, `_patch_eval_pack_starting_state()`, `_apply_dotpath()`, `load_run_result()`, `find_previous_run()` (reads from `artifacts/` with back-compat), `_extract_parse_failures()`, `REPO_ROOT`, `PROMPTS_DIR` — runs scenario turns, injects `state_snapshot` into events, runs scenario-specific asserts then universal asserts |
| `ccya/eval/judge.py` | `run_judge()`, `run_judge_streaming()` (with `on_chunk` callback for streaming REPORT.md), `JudgeResult`, `TraceOptions`, `build_trace()` (with dedup options + auto_checker_failures + metrics_rows + redundancy_signals + compaction_signals), `_render_static_context()` (prepends architecture context), `_render_turn_context()` (with dedup + state diff), `_strip_immutable_sections()`, `_strip_remaining_markers()`, `_diff_state_snapshots()`, `_diff_list()`, `_hashable()`, `_maybe_dedup_user_prompt()`, `_render_deterministic_signals()` (auto-checker + metrics + redundancy + compaction), `_build_metrics_rows()`, `parse_judge_response()` (YAML front matter), `REPO_ROOT` |
| `ccya/eval/universal_asserts.py` | `run_all_universal_asserts()` + 10 assertion functions: `check_recent_events_turn_stamped`, `check_pending_gm_beat_consumed` (reads `state.meta`, not `state.scene`), `check_location_change_applied`, `check_rolled_implies_binding`, `check_npc_mention_extracted` (uses `_extract_candidate_names` helper that excludes PC name, sentence-initial capitals, short tokens ≤4 chars, common descriptors, inventory item names via partial match, and location names via partial match to reduce false positives), `check_recent_events_ring_size` (≤20 entries), `check_npc_scene_cap` (≤8 NPCs), `check_condition_no_dupes` (no duplicate IDs), `check_actions_count_and_distinct` (exactly 4 distinct), `check_momentum_band_delta` (per-band delta with engine clamp tolerance) |
| `ccya/eval/report.py` | `generate_report()` — produces REPORT.md with deterministic header, auto-checker table, judge summary, and links to trace/judge. Also: `write_report_skeleton()` — writes initial REPORT.md with header + sections; `append_judge_chunk()` — appends judge output chunk between `JUDGE_STREAM_OPEN`/`JUDGE_STREAM_CLOSE` sentinels; `finalize_report()` — hoists judge summary from body, removes streaming placeholders; `_read_events()`, `_extract_stream_metrics()`, `_summarize_events()`, `_compute_regressions()`, `_collect_flags()`, `_render_flag_block()`, `_render_judge_summary()`, `_render_combined_table()`, `_render_auto_checker_block()`, `StreamMetrics`, `TurnMetrics`, `StreamRegression`, `Flag` |
| `ccya/eval/scenario.py` | `Scenario` (with `seed_overrides`), `Turn`, `TurnAssert` (with `stream_id`), `load_scenario()`, `discover_scenarios()` |
| `ccya/eval/cli.py` | CLI entry point: `main()`, subcommands `run`, `judge-only`, `pack`, `list` — config loading, logging setup (direct `ccya.eval` logger), async dispatch; `_run_one_scenario()` — helper for multi-scenario runs with streaming REPORT.md support |
| `ccya/eval/engine_mirror.py` | Live engine constants for scenarios + `constants_block()` for judge traces (includes BANDS, SKILLS, DIFFICULTIES, INTENT_VERBS_HINT, PC_CONDITION_CAP, SCENE_NAMED_NPC_CAP) + `KNOWN_ASSERT_FIELDS` + `KNOWN_SEED_PATHS` + `EXTRACT_STREAMS` |
| `ccya/engine/markers.py` | `strip_trace_markers()`, `strip_trace_markers_in_messages()` — removes eval-trace sentinel markers from text/messages before sending to LLM |

## Public APIs

- **`run_scenario(scenario, eval_config, game_config_path)`** → `RunResult` — in-process `run_turn()` driver over a static eval pack. Runs N turns, collects events, checks assertions. Applies `scenario.seed_overrides` via `_patch_eval_pack_starting_state`. Emits `__metadata__` event as first event in the output. Run artifacts (`events.jsonl`, `run.json`) written to `artifacts/` subdirectory.
- **`run_judge(events_path, eval_config, output_dir, scenario_id, previous_judge_md_path)`** → `JudgeResult` — builds full-context trace.md (with architecture context, redundancy signals, compaction signals), runs LLM judge, writes judge.md, parses YAML front matter for scores. Back-compat wrapper around `run_judge_streaming()`.
- **`run_judge_streaming(events_path, eval_config, output_dir, scenario_id, previous_judge_md_path, on_chunk)`** → `JudgeResult` — same as `run_judge()` but streams judge output via `on_chunk` callback, writing to REPORT.md skeleton in real-time.
- **`generate_report(run_result, eval_config, judge_result)`** → `Path` — produces REPORT.md with deterministic header, auto-checker table, judge summary, and links to trace/judge files.
- **`write_report_skeleton(output_dir, scenario_id)`** → `Path` — writes initial REPORT.md with header + section placeholders.
- **`append_judge_chunk(output_path, chunk)`** → `None` — appends judge output chunk between sentinel markers.
- **`finalize_report(output_path)`** → `None` — hoists judge summary from body, removes streaming placeholders.

## Tier 1 vs Tier 2

- **Tier 1**: `tests/test_engine_pipeline.py` — token-budget ceilings, multi-turn invariants, scope-gating tests. Uses `_FakeLLM`. Runs under `make test`.
- **Tier 2**: `make eval` — in-process `run_turn()` driver over static `eval-pack`, 13-turn `full_cycle` scenario, single LLM judge, REPORT.md with deterministic header + auto-checker table.

## Scenario files

- `evals/scenarios/full_cycle.py` — Baseline 13-turn regression scenario with dual compaction (T6, T12)
- `evals/scenarios/pressure_lifecycle.py` — Scene pressure urgency escalation and expiry (imports `PRESSURE_BUILDING_AT`, `PRESSURE_IMMEDIATE_AT`)
- `evals/scenarios/gm_beat_lifecycle.py` — `pending_gm_beat` set/surface/consume lifecycle (uses `state_yaml` assert stream)
- `evals/scenarios/momentum_high.py` — High-momentum narration tone (imports `MOMENTUM_MAX`)
- `evals/scenarios/momentum_low.py` — Low-momentum narration tone (imports `MOMENTUM_MIN`)

## Test files

- `tests/test_eval.py` — Tests for eval config loading, scenario loading, engine config building, run result loading, judge response parsing (YAML front matter), assertion checking, `build_trace()` full-context trace structure and content.
- `tests/test_eval_schema.py` — Tier 1 schema validation: validates TurnAssert paths against live engine, engine_mirror self-consistency, seed_override path validation.

## Trace format

The judge receives a single markdown document (`trace.md`) with:

1. **Static Context** (appears once at top): World Pack Style, Seed State, Engine Constants, 5 System Prompts (from turn 1).
2. **Per-Turn blocks**: Input, User Prompts (5 streams, deduped if `dedup_immutable_sections` is enabled), Engine Outputs (rules parsed + raw, narration, 3 extractors), Applied Deltas, Rejected Deltas, Suggested Actions, Context Telemetry, State After Turn (full on first/last turns, diff on middle turns if `state_as_diff` is enabled).
3. **Deterministic Signals** (after all turns, when auto-checker failures or metrics exist): Auto-Checker Failures table (universal assertion failures), Metrics table (per-turn token counts, parse failures, retries), Prompt Redundancy table (cross-stream block duplication detected by harness), Compaction Features table (per-event capability observability for the compactor).

Dedup is controlled by `evals/config.yaml` under `judge.trace.*`. Default is ON for both options. If the trace exceeds the judge model's context window, the user must switch judge models.

## Judge output format

The judge response uses YAML front matter for scores, followed by an 8-section markdown body:

```yaml
---
mechanical_score: <int 1-5>
narrative_score: <int 1-5>
pipeline_scores:
  rules: <int 1-5>
  narrate: <int 1-5>
  extract_scene: <int 1-5>
  extract_state: <int 1-5>
  extract_progress: <int 1-5>
---

# Mechanical Design Critique
## Pipeline: rules
...
## Pipeline: narrate
...
## Pipeline: extract_scene
...
## Pipeline: extract_state
...
## Pipeline: extract_progress
...

# Storytelling Design Critique
## Criterion: quest_arc_quality
**Score:** <1-5>
...

# Prompt Redundancy Analysis
...

# Compaction Capabilities Report
...

# Auto-Checker Failures
...

# Additional Observations
...

# Verdict
...

# Narrative Recap
...
```

`parse_judge_response()` strips `<think>` tags, parses the YAML front matter, and returns `(scores_dict, body_md)`. Missing scores default to `?` in the report rendering.
