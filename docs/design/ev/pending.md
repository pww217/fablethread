# EV Design — Pending Items

**Last updated:** 2026-06-16

This document consolidates all EV design items that have **not yet been implemented**. Completed designs have been moved to `docs/design/complete/ev/`.

---

## 1. CLI Defaults and User Config

**Source:** `cli-defaults-and-personas-design.md` → moved to `complete/ev/cli-defaults-and-personas-design.md`

### Status: IMPLEMENTED

All items from this design have been implemented:
- `ccya/config.py` — new module with `AppConfig`, `EvConfig`, `PersonaConfig`, `load_user_config()`, `load_persona_registry()`
- `ev.py personas` command — lists built-in and user personas
- `play.py` and `check.py` — use user config defaults for model and checker-model
- Config precedence: CLI flag > Pack config > User config > Hardcoded defaults

---

## 2. Eval Methodology

**Source:** `eval-methodology-design.md` (moved to `complete/ev/` when fully implemented)

### Status: NOT IMPLEMENTED

### What's pending

| Item | Description |
|---|---|
| Scenario YAML files | `packs/eval/scenarios/` with `checker_suite`, `llm_checkers`, `llm_sample_rate` fields |
| Scenario loader updates | `ccya/ev/scenario.py` — add new fields to `Scenario` dataclass |
| Eval runner updates | `ccya/ev/eval.py` — use `checker_suite`/`llm_checkers` from scenario, add sampling logic |
| `scripts/aggregate.py` | Deterministic aggregation: pass-rate, worst-checker, cross-scenario report, improvement targets |
| Makefile eval targets | `eval-ruling`, `eval-extraction`, `eval-narration`, `eval-state`, `eval-cross`, `eval-full`, `eval-full-suggest` |

### Design decisions (final)

- Scenarios declare checker suites — no one-size-fits-all, keeps traces clean and eval fast
- No meta-judge for score synthesis — deterministic math (pass-rate, worst-checker) replaces LLM
- LLM checkers default to 100% with `llm_sample_rate` slider (0.0-1.0)
- Improvement suggestions: one batch LLM call per scenario group with failures below threshold
- Makefile orchestrates, Python does not — `make eval-full` runs 5 `ev.py eval run` + `aggregate.py`
- Scenario groups are naming conventions + Makefile targets, not code abstractions
- Aggregation is failure-rate based ("weakest link" metric)
- Unchecked event fields documented but not required coverage

### Scenario taxonomy (5 groups, 12 scenarios)

**Group 1: Ruling (3 scenarios)** — dice resolution, convergence score, phase transitions
**Group 2: Extraction (3 scenarios)** — inventory, conditions, NPCs, location
**Group 3: Narration (3 scenarios)** — GM beats, pacing directives, Curtain Call
**Group 4: State (2 scenarios)** — thread lifecycle, sanitizer lifecycle
**Group 5: Cross-cutting (1 scenario)** — long run with all checkers

### New checker opportunities

| Checker | Fields | Stage | Priority |
|---|---|---|---|
| `ruling_arithmetic` | `ruling.raw_total`, `stat_mod`, `diff_mod`, `cond_mod`, `final_total` | Ruling | High |
| `pacing_integrity` | `pacing_context.directive`, `narrate_summary.pacing_directive`, `gate`, `outcome_hint` | Narration | Medium |
| `rejected_field_integrity` | `rejected`, `applied` | Extraction | Medium |
| `change_consistency` | `changes.*`, `applied.*` | Extraction | Medium |
| `extraction_retry` | `extract.retries` | Extraction | Low |

### Files to touch

- `ccya/ev/scenario.py` — add `checker_suite`, `llm_checkers`, `llm_sample_rate` to `Scenario`
- `ccya/ev/eval.py` — use checker suites, add sampling logic
- `scripts/aggregate.py` — new module for deterministic aggregation
- `Makefile` — add eval stage targets
- `packs/eval/scenarios/` — new directory for scenario YAML files

---

## 3. UI Streaming for Evals

**Source:** `eval-ui-streaming-design.md` (moved to `complete/ev/` when fully implemented)

### Status: NOT IMPLEMENTED

### What's pending

| Item | Description |
|---|---|
| `ccya/server/streaming.py` | New module: SSE streaming infrastructure, `SSEEvent` class, streaming state management |
| `/api/eval/stream` | SSE endpoint for eval progress streaming (start, turn, stage, checker, complete, error events) |
| `/api/eval/cancel` | POST endpoint to cancel a running eval streaming session |
| `/api/turn/pipeline` | SSE endpoint for mid-turn pipeline visibility (ruling → extraction → narration → state) |
| Web UI streaming components | Progress bar, stage indicators, checker results, cancel button, pipeline visualization |

### Design decisions (final)

- SSE for streaming (not WebSockets) — simpler, unidirectional, automatic reconnection
- Single streaming endpoint `/api/eval/stream` for all eval streaming
- Streaming events: structured JSON with `type`, `data`, `timestamp`
- Mid-turn pipeline: `/api/turn/pipeline` streams sequential stage completion
- Streaming state: in-memory, not persistent (ephemeral sessions)
- Streaming timeout: 5 minutes of inactivity
- Streaming cancellation: `/api/eval/cancel` POST endpoint

### Streaming event types

- `start` — streaming session started
- `turn` — new turn started
- `stage` — pipeline stage completed (ruling/extraction/narration/state)
- `checker` — checker result emitted (pass/fail/score/findings)
- `complete` — streaming session completed
- `error` — streaming session errored
- `cancelled` — streaming session cancelled

### Alternatives rejected

- WebSockets — adds connection management, reconnection logic, message framing
- Polling — unnecessary server load and latency
- Token-level streaming — out of scope (covers eval progress and pipeline visibility only)
- Persistent streaming state — sessions are ephemeral

### Files to touch

- `ccya/server/streaming.py` — new module
- `ccya/server/routes.py` — add streaming endpoints
- `ccya/ev/eval.py` — update to yield streaming events
- `ccya/engine/turn.py` — update to yield streaming events for each stage
- `ccya/templates/` — add streaming UI components

---

## 4. EV Tool Meta-Analysis (diagnostic, not a design)

**Source:** `ev-tool-meta-analysis.md` (still in `docs/design/ev/` as reference)

### Status: PARTIALLY IMPLEMENTED

Many items from this analysis were addressed by other designs (convergence, curtain-call, phase-transitions commands). The following items remain unimplemented:

| Item | Description | Related Design |
|---|---|---|
| `search` dot-notation | `pacing_context.scene_phase:CLIMAX` fails — only supports flat `field:value` | EV Tooling (future) |
| `trace` for nested fields | `trace pacing_context.scene_phase` returns "Field not tracked" | EV Tooling (future) |
| `goals` visible_goal | `ev.py goals` doesn't read `arc_resolve.visible_goal` | EV Tooling (future) |
| Context bloat analysis | Storytell prompts grow to ~16.8k tokens, causing slowdowns | Infrastructure (future) |

### Items already implemented (from this analysis)

- `check --all` auto-detection for `--save-dir` — fixed in `__init__.py`
- `narrate.output` data shape — added `prose` field to `narrate` event
- `ev.py warnings` command — already routed and functional
- `thread_dedup_rejections` — stored in event field
- `extract.retry_errors_by_stream` — detailed retry breakdown in event
- `ev.py phase-transitions` — phase transition log with triggers
- `ev.py convergence` — per-turn convergence score + 5 components
- `ev.py curtain-call` — CLIMAX Curtain Call compliance
- `ev.py prompt-sizes` — token growth per stage

### Design decisions (final)

- Dot-notation for search/trace is a future EV tooling enhancement
- `narrate.output` should be populated from `narrate_prompt.output` or all consumers should read from `narrate_prompt.output`
- Soft-check warnings should be stored in event fields for queryability
- Context bloat is an infrastructure concern, not an EV tooling concern

---

## Summary

| Design | Status | Items Pending |
|---|---|---|
| EV Tool Meta-Findings | **COMPLETE** (moved to `complete/ev/`) | 0/10 |
| EV Session Config | **COMPLETE** (moved to `complete/ev/`) | 0/7 |
| CLI Defaults and User Config | **COMPLETE** (moved to `complete/ev/`) | 0/6 |
| Eval Methodology | Pending | 5 items + 12 scenarios |
| UI Streaming for Evals | Pending | 5 items |
| EV Tool Meta-Analysis | Partial (diagnostic reference) | 4 items |
