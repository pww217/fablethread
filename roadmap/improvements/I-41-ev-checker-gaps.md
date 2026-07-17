---
title: "EV checker coverage gaps: EMA, thresholds, culling, arc resolve, turns_in_phase"
status: idea
urgency: 3
size: medium
created: 2026-07-13
ticket_id: I-41
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Context

EV checkers validate deterministic engine invariants from event streams. Six areas were flagged as LLM-driven/unverifiable and dropped: `beat_survives_single_turn` (already in `gm_beat_lifecycle`), `turns_in_phase` (covered by `breather_enforcement` + `climax_turn_counting`), `beat_diversity_5ban` (LLM guideline, not engine rule), `world_candidates_count` (LLM output count), `thread_urgency_transitions_valid` (LLM-driven urgency changes), and `world_beat_generation_valid` (LLM generation output). The remaining five items below validate *actual engine mechanics* — Python-enforced invariants.

## New Checkers

### 1. `convergence_ema` — EMA smoothing state continuity

- Reads: `pacing_context.convergence_score`, `pacing_context.convergence_components`, `last_turn_state.scene.smoothed_convergence`, `config.convergence_alpha`
- Verifies:
  - `smoothed = alpha * raw + (1-alpha) * prev_smoothed` on every turn
  - First turn uses raw score as initial smoothed value (no previous state)
  - After location reset (`scene.turn_entered` changes), smoothed value does **not** carry stale EMA forward — rechecked against rolling raw score history
  - `convergence_score` on `PacingContext` contains the *raw* 5-component sum, separate from the smoothed value stored in state

### 2. `convergence_threshold_context` — Config thresholds at transition gates

- Reads: `pacing_context`, `last_turn_state`, `EngineConfig`
- Verifies:
  - RISING→CLIMAX: uses `convergence_enter_threshold` (default 2) from config, *not* a hardcoded value
  - CLIMAX→RESOLUTION early exit: uses `convergence_exit_threshold` (default 1) from config
  - CLIMAX extension: `convergence >= 3` condition checks the *smoothed* convergence (not raw), and hard cap is `climax_turn_limit + extension_max` not just `climax_turn_limit`
  - All thresholds use runtime config values, not defaults baked into checker

Existing `phase_transition_signals` validates gates *fire*, but does not validate that the *threshold values* used at each gate are correct. This checker complements it by verifying threshold semantics.

### 3. `arc_resolve_lifecycle` — Successor arc creation

- Reads: `extraction.record.output` (for `arc_resolve` output), `last_turn_state.arc` / `last_turn_state.long_term_objective`, `last_turn_state.meta`
- Verifies:
  - When `arc_resolve` is emitted, successor arc is created with `next_goal` from `goal.next_goal` in Record output
  - If `next_goal` is None/empty and no successor arc exists, engine should have rejected the resolution
  - Old arc moves to `completed_threads` with `resolution_state: "resolved"` and `resolved_on_turn == turn_no`
  - Successor's `meta.goals` contains the merged goals (from `next_goal` + any carried-over goals from old arc)
  - No duplicate thread IDs in `completed_threads` after merge
  - `arc_transfer` metadata exists with `previous_id`, `next_id`, `resolved_on_turn`, `next_goal`
  - Old arc's `threads` (non-resolved ones) move to successor's `completed_threads` with `resolution_state: "abandoned"`

## Improved Checkers

### 4. `thread_culling` — Tighten existing to match engine rule

- Current: only flags when ≥5 dormant threads exist (soft warning)
- Engine rule (`_apply_thread_automatics` in `turn_state.py`): ≥3 dormant threads trigger culling, oldest moved to `completed_threads` with `resolution_state: "abandoned"`
- Improvement: validate culling fires at ≥3 dormant, check that oldest dormant threads actually appear in `completed_threads` with correct `resolution_state`

### 5. `turns_in_phase_counter` — General counter validation

- `breather_enforcement` validates `breather_turn_count` only. `climax_turn_counting` validates `climax_turn_count` only.
- New checker validates the general `turns_in_phase` field:
  - Starts at 1 on phase entry (SETUP, RISING, CLIMAX, RESOLUTION, BREATHER)
  - Increments by 1 each turn within same phase
  - Resets to 0 on phase exit
  - Survives location resets (location change resets `scene_age` but not `turns_in_phase`)

## What was dropped (and why)

| Proposal | Drop reason |
|---|---|
| `beat_survives_single_turn` | Already in `gm_beat_lifecycle` (`beat_consumed` check) |
| `turns_in_phase` (deduplicated duplicate) | Covered by `breather_enforcement` + `climax_turn_counting` + `phase_transition_signals` |
| `beat_diversity_5ban` | World AI prompt guideline, not engine-enforced rule |
| `world_candidates_count` | LLM generation count, not engine constraint |
| `thread_urgency_transitions_valid` | Urgency changes are LLM decisions via Record |
| `convergence_healthy_rhythm` | Narrative quality detector, not engine invariant |
| `world_beat_generation_valid` | LLM generation output count and content |

## Priority

1. `arc_resolve_lifecycle` — New: no existing coverage, fully deterministic engine logic
2. `turns_in_phase_counter` — New: fills gap not covered by phase-specific counters
3. `convergence_ema` — New: underlying mechanism for R→CLIMAX transitions
4. `thread_culling` — Improvement: tighten existing to match engine rule
5. `convergence_threshold_context` — New but lower priority: complements `phase_transition_signals`

## Scope

Five items, mostly small deterministic checkers (30-80 lines each). `arc_resolve_lifecycle` is the largest (~100 lines).