---
title: "Phase 2 eval: 15-run cycle across noir-1930s, space-western, golden-piracy"
status: done
urgency: 2
size: medium
created: 2026-07-07
ticket_id: E-12
labels:
  - pacing
  - thread-lifecycle
  - convergence
---

# E-12: Phase 2 Eval — 15-run cycle

**Eval group:** `evals/runs/2026-07-07_0.31.0-55-gcadbf0a4_cadbf0a4/`
**Date:** 2026-07-07
**Git SHA:** cadbf0a4

## Runs

1. noir-1930s:driven — 15 turns — 36/39 checkers pass (92.3%)
2. space-western:speedrunner — 15 turns — 36/39 checkers pass (92.3%)
3. golden-piracy:completionist — 15 turns — 37/39 checkers pass (94.9%)

**Aggregate: 109/117 checkers pass (93.2%)**

## Phase Reports

- [PHASE-2.md](PHASE-2.md)
- [REPORT.md](REPORT.md)

## Findings

### 0. Double `set_turn` Bug (B-28) — ROOT CAUSE

**B-28 was marked "done" but the fix was never applied.** `turn.py:218` still had a duplicate `state.set_turn()` call alongside the canonical one at `_persist_and_async_cleanup():585`.

**Impact:** Every player turn incremented by 2 instead of 1. Events showed turns 2, 4, 6, 8... instead of 1, 2, 3, 4.... This offset cascaded into all downstream checker calculations.

**Fix applied:** Removed the duplicate `set_turn()` at `turn.py:218`. Single source of truth is now `_persist_and_async_cleanup()` at line 585.

**Checkers affected by this bug:**
- `convergence_recompute` — all failures are `roll_starvation` mismatches caused by the turn offset. Fixed by B-28 fix.
- `thread_urgency_decay` — checker uses `meta.turn` from events; offset caused incorrect `turns_at_urgency` calculations.
- `gm_beat_lifecycle` — checker uses `meta.turn` for TTL calculations.
- `location_change` — checker compares `post_turn_location_id` against previous event's location.

### 1. Thread Urgency Decay — FAIL (all 3 runs) — ENGINE BUG

**Root cause:** `_apply_thread_updates()` in `turn_state.py:17` only runs when `record_result.thread_update` is not None. The auto-dormant and urgency decay logic (lines 113-160) is inside this function, so it never runs when the record step produces no thread updates.

**Evidence:** All 3 runs show `thread_updates=0` in events. Threads that haven't been updated in 4+ turns are not being marked dormant. Threads at the same urgency for 8+ turns are not being demoted.

**Fix needed:** Move auto-dormant and urgency decay logic out of `_apply_thread_updates()` so it runs every turn regardless of whether there are explicit thread updates.

### 2. Convergence Recompute — roll_starvation mismatch — FAIL (all 3 runs)

All 12 failures in noir-1930s are `roll_starvation` mismatches (stored=0, recomputed=1). This is a direct consequence of the double `set_turn` bug — the event's `turn` field was offset by 1 from what the engine used at ruling time.

**Status:** Should be resolved by B-28 fix. Re-run checkers after B-28 fix to confirm.

### 3. GM Beat Lifecycle — FAIL (noir-1930s only)

`pending_gm_beat` persisted unchanged across multiple turns (e.g., T6-T8 in noir-1930s). The checker flags `beat_consumed` when the beat persists across turns without being consumed.

**Need to verify:** Is there a TTL mechanism for `pending_gm_beat`? The checker expects beats to be consumed, but the engine may not be enforcing a TTL.

### 4. Location Change — FAIL (space-western only)

T12: `location_change` emitted with `id=unregistered_docking_ring` but previous location was also `unregistered_docking_ring`. The engine emitted a location_change even though the location didn't actually change.

**Fix needed:** Check delta_builder logic — it should not emit `location_change` when the location ID is unchanged.

### 5. `meta.turn` Set by LLM — Seed Prompt Issue

The `prepare_seed` prompt example shows `"turn": 0` in the meta section. The LLM is outputting `"turn": 1` in the seed state. This is not a known issue.

**Question:** Should `meta.turn` be set by the LLM at all? It's always 0 at seed time and managed by the engine (`turn_no = state.meta.turn + 1`). The prompt should either remove `meta.turn` from the example (engine defaults to 0) or add a hard constraint telling the LLM to set it to 0.

## Changes Since Last Eval (SHA 6735834a)

- Thread lifecycle prompt restructure (a1d05285)
- Thread creation cooldown removal (354d5d20)
- Engine model/pipeline naming audit (3335f03a)
- Convergence checker fix (deed99e4)

## Assessment

No critical bugs. All failures are intermediate severity. Thread urgency decay and convergence recompute are systematic issues that should be addressed before Phase 3.

## Resolution

All 4 bugs fixed and verified:

- **B-28** (double set_turn): Removed duplicate `state.set_turn()` at `turn.py:218`
- **B-38** (thread urgency decay): Extracted auto-dormant + urgency decay into `_apply_thread_automatics()` + fixed `urgency_set_turn` tracking in auto-dormant, dormant invariant enforcement, and thread sanitizer
- **B-39** (GM beat TTL): Added `state.set_pending_beat(None)` after narrate phase
- **B-40** (location change): Added ID comparison guard in `delta_builder.py`
- **B-41** (seed prompt meta.turn): Removed `"turn": 0` from seed prompt example

### Re-run Results (39/39 checkers pass)

1. noir-1930s:driven (2135) — 39/39 PASS
2. space-western:speedrunner (2158) — 39/39 PASS
3. golden-piracy:completionist (2203) — 39/39 PASS

### What's Next

- Resume with Phase 3 (25-run cycle)
