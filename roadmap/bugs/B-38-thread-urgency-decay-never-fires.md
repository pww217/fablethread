---
title: "Thread urgency decay and auto-dormant never fire when record produces no thread updates"
status: done
completed: 2026-07-09
urgency: 1
size: medium
created: 2026-07-07
ticket_id: B-38
labels:
  - engine
  - pacing
---

# B-38: thread_urgency_decay and auto_dormant never fire

## Symptom

Threads remain at `urgency=normal` for 8+ turns without being demoted to `background`. Threads untouched for 4+ turns are not being marked dormant.

## Evidence

All 3 Phase 2 runs (noir-1930s, space-western, golden-piracy) show `thread_updates=0` in every event. The engine produced no explicit thread updates from the record step.

**Affected threads:**
- noir-1930s: `judicial_rigging` (normal for 10+ turns, last_updated=9), `heist_trail` (normal for 20+ turns)
- space-western: `corporate_encroachment` (normal for 11+ turns, last_updated=9), `coalition_pursuit` (normal for 7 turns, last_updated=23)
- golden-piracy: `governor_secret` (normal for 10+ turns, last_updated=9), `cargo_discrepancy` (urgent→normal→urgent oscillation)

## Root Cause

`_apply_thread_updates()` in `turn_state.py:17` only runs when `record_result.thread_update` is not None. The auto-dormant logic (line 113) and urgency decay logic (line 136) are inside this function.

When the record step produces no thread updates (which is the common case — most turns don't require thread changes), the entire auto-dormant and urgency decay block is skipped.

```python
def _apply_thread_updates(state, record_result, config, ...):
    if not record_result.thread_update:
        return None  # <-- Returns early, skipping auto-dormant + decay below
    
    # ... thread update processing ...
    
    # Auto-dormant — fire every turn.
    if config and remaining_threads:
        # ... never reached when no thread updates ...
    
    # Urgency decay
    if config and remaining_threads:
        # ... never reached when no thread updates ...
```

## Fix

### Phase 1: Extract auto-dormant + urgency decay

A new `_apply_thread_automatics()` function was created in `turn_state.py` that runs auto-dormant and urgency decay every turn, independent of explicit thread updates. It is called unconditionally from `_apply_state_updates()` alongside the existing `_apply_thread_updates()` call.

### Phase 2: Fix urgency_set_turn tracking

`_apply_thread_automatics()` auto-changed urgency (auto-dormant sets `urgency=background`, urgency decay demotes stepwise) but did not update `urgency_set_turn`. The checker uses `current_turn - urgency_set_turn` to measure how long a thread has been at its current urgency level. When the engine auto-changed urgency, the counter was stale, causing false positives.

Fixed in 3 places:
- `turn_state.py:163` — auto-dormant now sets `urgency_set_turn: turn_no`
- `turn_state.py:100` — dormant invariant enforcement now sets `urgency_set_turn: turn_no`
- `thread_sanitizer.py:415` — dormant invariant enforcement now sets `urgency_set_turn: turn_no`

## Evidence (ev-review 2026-07-09, noir-1930s 15t)

- union_corruption: urgency_set_turn=7 at T7, urgency=urgent at T9, decayed to normal at T10 (exactly 8 turns at urgency, matches thread_urgency_max_age=8)
- strike_funding: urgency_set_turn updated at T5, T6, T7, T8 — tracking accurate; goes dormant=True at T15 (untouched since T4, 11 turns >= threshold=8)
- _apply_thread_automatics() called unconditionally at turn_state.py:543 (not gated on record_result.thread_update)
- urgency_set_turn set in 3 places: _apply_thread_updates() line 99, _apply_thread_automatics() line 165, _apply_sanitization() line 414
- thread_urgency_decay checker passes 5/5, 15/15, 15/15, 15/15 across all four runs

## Impact

- Threads stuck at `urgency=normal` indefinitely (no demotion)
- Threads not being auto-dormant after 4 turns of inactivity
- `thread_urgency_decay` checker fails across all runs
- Thread urgency is no longer a dynamic pacing signal
