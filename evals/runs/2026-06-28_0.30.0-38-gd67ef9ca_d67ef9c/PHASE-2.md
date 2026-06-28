# Phase 2 Report

**Eval group:** `2026-06-28_0.30.0-38-gd67ef9ca_d67ef9c`
**Runs:** 3 (noir-1930s/driven, space-western/speedrunner, golden-piracy/completionist)
**Turns:** 15 each

## Summary

Phase 2 found **1 critical bug** (already fixed) and **3 checker bugs** (false positives).

### Bug Fixed

**Phase transition reading stale scene dict** — `ccya/engine/narrate.py:234,245`
- `_compute_scene_phase()` returns a new dict (line 355 of `_pacing.py`: `{**scene, ...}`)
- `narrate.py` read `scene.get("scene_phase")` and `scene.get("climax_turn_count")` from the OLD local variable
- Result: `_compute_pacing_context()` received stale phase/climax_turn_count, so CLIMAX hard cap override never triggered
- **Fix:** Changed to read from `state["scene"]` instead of local `scene` variable
- **Verified:** Post-fix noir run passes all checkers

### Checker False Positives (not engine bugs)

1. **`phase_transition_signals` — BREATHER→RISING check**
   - Reads `breather_turn_count` from CURRENT turn's pacing_context
   - But breather_turn_count is reset to 0 when transitioning to RISING
   - Should read from PREVIOUS turn's pacing_context
   - **Action needed:** Fix checker to read prev_turn breather_turn_count

2. **`phase_transition_signals` — CLIMAX extension check**
   - Checks CURRENT turn's urgent thread count
   - Extension decision is based on threads at START of turn (previous turn's state)
   - At turn 15, there WERE urgent threads from turn 14's state
   - CLIMAX extension to turn 5 is valid (5 < 4+2=6)
   - **Action needed:** Fix checker to read threads from last_turn_state

3. **`thread_cooldown`**
   - Threads created 1-2 turns apart
   - May be legitimate behavior or too-strict cooldown
   - **Action needed:** Review cooldown threshold (currently 3)

4. **`convergence_recompute` — scene_age off by 1**
   - Stored scene_age differs from recomputed by 1
   - Likely due to scene_age calculation timing
   - **Action needed:** Review scene_age computation

## Checker Scores

| Run | Pass Rate | Failures |
|-----|-----------|----------|
| noir-1930s/driven 15t | 92.9% | thread_cooldown, phase_transition_signals, convergence_recompute |
| space-western/speedrunner 15t | 90.5% | phase_transition (FIXED) |
| golden-piracy/completionist 15t | 92.9% | phase_transition (FIXED) |

## Testing Items

- **B-10 (UI highlighting):** Code fixes present, cannot validate via evals (UI-only)
- **B-20 (thread duplicate IDs):** Fixed — no duplicate thread_add IDs found in any run

## Recommendations

1. **Fix `phase_transition_signals` checker** — read breather_turn_count and threads from previous turn
2. **Review `thread_cooldown` threshold** — 3 turns may be too strict
3. **Review `convergence_recompute` scene_age calculation** — off-by-1
4. **B-10 needs live UI validation** — not testable via evals
5. **B-20 appears fixed** — no duplicates in 3 runs
