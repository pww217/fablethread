---
title: "Phase 2 eval: thread_urgency_decay, extraction_retry_rates, convergence_recompute"
status: done
urgency: 2
size: medium
created: 2026-07-02
ticket_id: E-1
labels:
  - eval
  - engine
---

# E-1: Phase 2 eval findings

## Eval group

- **Path:** `evals/runs/2026-07-02_0.30.0-103-gf4e74db0_f4e74db/`
- **Runs:** noir-1930s:driven (5t + 15t), space-western:speedrunner (15t), golden-piracy:completionist (15t)
- **Phase reports:** PHASE-1.md, PHASE-2.md

## Findings

### 1. thread_urgency_decay not working (FAIL on all 3 runs) — FIXED

Threads stay at `urgent` for 8+ turns without being demoted to `normal`/`background`.

**Example:** `syndicate_pressure` thread at `urgent` for 8 turns (should demote to `normal`), then at `normal` for 10 turns (should demote to `background`).

**Checker:** `thread_urgency_decay`

**Root cause:** `_apply_thread_updates()` in `turn_state.py:63-64` set `updates["urgency"]` when extraction changed urgency, but never set `urgency_set_turn`. The decay code at `turn_state.py:140` checks `_set_turn = getattr(t, "urgency_set_turn", None)` and skips threads with `None`. Seed threads had `urgency_set_turn=0` from seeding, but when extraction changed urgency, it stayed stale at `0`, making `_age = turn_no - 0` always large but the thread was often dormant (skipped). When extraction woke a dormant thread and set it urgent, `urgency_set_turn` stayed at `0`, so decay never started tracking.

**Fix:** Added `updates["urgency_set_turn"] = turn_no` alongside `updates["urgency"]` in `_apply_thread_updates()`.

**Verification:** noir-1930s:driven 8-turn run — `thread_urgency_decay: PASS`. Thread `existential_void_presence` correctly got `urgency_set_turn: 3` when extraction set urgency to `normal`.

### 2. extraction_retry_rates — state extractor missing condition_change_reason (FAIL on space-western, golden-piracy) — FIXED

State extractor retry error: `EXTRACTION_COERCION_FAILED: condition_change_reason is required when condition changes are present`.

The state extractor is returning condition changes without the required `condition_change_reason` field.

**Checker:** `extraction_retry_rates`

**Root cause:** The prompt at `extract_state_system.j2:62-73` had a JSON schema example that included `inventory_change_reason` but NOT `condition_change_reason`. The LLM follows the schema and omits the field when emitting `pc_condition_add`/`pc_condition_remove`.

**Fix:** Added `"condition_change_reason": "Player received medical attention"` to the schema example in `extract_state_system.j2`.

**Verification:** noir-1930s:driven 8-turn run — `extraction_retry_rates: PASS`, 0/12 retries. Deltas show `condition_change_reason: The void exerts inward pressure on the player.` on turn 4.

### 3. convergence_recompute mismatch (FAIL on all 3 runs) — FIXED

Stored convergence scores don't match recomputed values on various turns.

**Checker:** `convergence_recompute`

**Root cause:** Off-by-one in checker — used `turn_no` (post-increment, from `ev.get("turn")`) to compute `roll_starvation`, but engine computes it at ruling time using `current_turn` (pre-increment). The engine was correct; the checker was wrong.

**Fix:** Changed `turns_since_last_roll = turn_no - last_roll_turn` to `turns_since_last_roll = current_turn - last_roll_turn` in `pacing_convergence.py:288`.

**Verification:** noir-1930s:driven 8-turn run — `convergence_recompute: PASS`.

## What was done

- Fixed StopAsyncIteration bug in extraction pipeline (I-23 Phase 3 regression)
- Phase 1: noir-1930s:driven 5 turns — all pass, no errors
- Phase 2: 3 games × 15 turns — engine stable, 3 consistent failures
- Fixed `thread_urgency_decay`: `_apply_thread_updates()` now sets `urgency_set_turn` when urgency changes
- Fixed `extraction_retry_rates`: added `condition_change_reason` to state extractor schema example
- Fixed `convergence_recompute`: used pre-increment `current_turn` instead of post-increment `turn_no` for roll_starvation
- Verified all 3 fixes: noir-1930s:driven 8-turn run — all checkers PASS

## What's next

- Resume Phase 3 of evals
