---
title: Smoothed convergence score never persisted to state.meta
status: done
urgency: 3
size: small
created: 2026-07-13
ticket_id: B-46
labels: [pacing, convergence]
completed: 2026-07-13
design:
plan:
pr:
  url:
  branch:
---

## Description

`convergence_alpha` EMA smoothing is computed in `narrate.py:208` but never written back to `state.meta.smoothed_convergence`. The value stays at `0.0` across all turns in every eval run.

## Root Cause

`smoothed_convergence` is computed during the narrate phase via the EMA formula:

```python
prev_smoothed = state.meta.smoothed_convergence
smoothed_convergence = config.convergence_alpha * _convergence_score + (1 - config.convergence_alpha) * prev_smoothed
```

But the result is never persisted to `state.meta`. The narrate setup function returns `(pc, narr_messages, new_scene)` — only the raw `_convergence_score` gets passed downstream via `_pc.convergence_score` (which is subsequently overwritten with the raw score at line 227). There is no field carrying the smoothed value back.

## Concrete Effects

1. **CLIMAX early exit gate is effectively disabled.** `_compute_scene_phase` checks `if smoothed >= 2 and min_turns_met:` to prevent early exit when convergence legitimately drops. With `smoothed = 0.0`, this always evaluates to false, so CLIMAX→RESOLUTION exits are driven purely by turn count or hard cap.

2. **Thread culling checker blocked.** The `thread_culling` checker has a guard `"smoothed_convergence is out of order"` that skips validation whenever the smoothed value hasn't been established.

## Fix

Pass `smoothed_convergence` from `_narrate_setup` through `NarrateResult` to `run_turn`, then persist via `state.set_smoothed_convergence()` at the end of the narrate phase.

Files changed:
- `ccya/engine/narrate.py` — `_narrate_setup` return value now includes `smoothed_convergence`
- `ccya/engine/turn.py` — `NarrateResult` adds `smoothed_convergence: float = 0.0` field; `run_turn` calls `state.set_smoothed_convergence()` after new_scene application

## Verification

- Convergence score should now differ from raw score on turn 2+
- `ev.py check convergence_ema` should validate component sums once smoothed > 0.0
- CLIMAX early exit behavior may change on runs that previously exited early
