---
title: "Pacing engine: NameError on SETUP transition + turns_in_phase resets to 0"
status: done
urgency: 1
size: small
created: 2026-07-05
ticket_id: B-31
labels:
  - engine
  - pacing
  - critical
---

## Summary

Two bugs preventing the pacing engine from advancing beyond SETUP phase. Both fixed.

### Bug 1: NameError — `convergence_score` undefined in `_compute_scene_phase`

`ccya/engine/_pacing.py:241` — the SETUP transition check used `convergence_score` which was not in scope. The function parameter is `total_convergence_score` (line 210).

**Fix:** `convergence_score` → `total_convergence_score` (line 241). Done.

### Bug 2: `turns_in_phase` resets to 0 on first SETUP→RISING transition

`ccya/engine/_pacing.py:243` — when transitioning from SETUP to RISING, the code set `turns_in_phase = 0`. This wipes the counter it needs to check for RISING→CLIMAX (requires `turns_in_phase >= RISING_min = 3`).

**Fix:** `turns_in_phase = 0` → `turns_in_phase = 1` (first turn in the new phase). Done.

### Bug 3: Misidentified

`config.py:89` sets `convergence_enter_threshold: int = 2`. Max convergence of 2 *does* meet the threshold. Was not a bug — the NameError just prevented the transition from completing.

## Verification

6 unit tests covering all phase transitions:

- SETUP→RISING (urgent threads) ✅ turns_in_phase=1
- RISING→CLIMAX (convergence ≥ threshold) ✅
- CLIMAX→RESOLUTION (thread resolved) ✅
- RESOLUTION→BREATHER ✅
- BREATHER→RISING (urgent thread) ✅
- Convergence score computation ✅

## Evidence

Validated against `saves/cordyceps-year-twenty-2026-07-05/`:
- Phase engine computed but never saved to disk (event snapshot captured before new scene applied)
- `turns_in_phase` stuck at 0 on every turn in `last_turn_state`
- Max convergence score: 2 (turns 13-15)
- No phase transitions observed — always SETUP

## Impact

- **Bug 1 (fixed):** Crashed on first turn if SETUP→RISING transition conditions were met (urgent threads present or convergence ≥ 2)
- **Bug 2 (fixed):** Even if no crash, RISING→CLIMAX never triggered because `turns_in_phase` reset to 0 on entry
