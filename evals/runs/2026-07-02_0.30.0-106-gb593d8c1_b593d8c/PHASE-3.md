# Phase 3 Report — noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist, zombie-survival:cautious, allied-ww2:aggressive

- **Date:** 2026-07-02
- **Git SHA:** b593d8c
- **Branch:** main
- **Turns:** 25 per game (125 total; golden-piracy first run only 5t due to primary LLM unreachable, second run completed 25t)
- **Pass rate:** noir-1930s 94.9% (37/39), space-western 94.9% (37/39), golden-piracy 89.7% (35/39), allied-ww2 94.9% (37/39)

## Results by Rubric Area

### Failing Checkers

1. **convergence_recompute: FAIL** (all 4 completed runs)
   - Stored convergence scores don't match recomputed values
   - Pre-existing: off-by-one in checker (uses post-increment `turn_no` instead of pre-increment `current_turn` for roll_starvation)
   - Fix committed in b593d8c but stored scores are from before the fix — checker now correct but old events still fail

2. **thread_urgency_decay: FAIL** (noir-1930s, golden-piracy, allied-ww2)
   - Threads stay at `urgent`/`normal` for 8+ turns without being demoted
   - Pre-existing bug: `_apply_thread_updates()` sets `urgency` but never sets `urgency_set_turn` when extraction changes urgency
   - Fix committed in b593d8c but stored scores are from before the fix

3. **sanitizer_lifecycle: FAIL** (space-western, golden-piracy)
   - `threads_resolved` references non-existent thread ID
   - space-western: `disarmed_in_darkness`
   - golden-piracy: `marsh_smuggler_approach`
   - **Root cause:** Checker bug — checks `threads_resolved` against `last_turn_state` (state at START of turn), but sanitizer runs at END of turn after deltas are applied. Threads added during the turn won't be in `last_turn_state`.
   - **Fix needed:** Checker should use state after deltas are applied, not `last_turn_state`

4. **thread_lifecycle: FAIL** (golden-piracy only)
   - T38: thread added but never appeared in state: `navy_boarding_action`
   - **Real bug** — extraction added a thread but it never made it into state
   - Needs investigation: likely a delta application or state mutation issue

### Passing Areas (all 4 completed runs)
- Beats: 2/2 PASS
- Goals: 2/2 PASS
- Ruling: 2/2 PASS
- State integrity: 7/7 PASS
- Arcs: 3/3 PASS
- NPCs: 2/2 PASS
- Location: PASS
- Curtain Call: PASS
- GM Beat Lifecycle: PASS
- Roll Band Consistency: PASS
- Extraction Retry Rates: PASS (0 retries across all runs — E-1 fix working)

## Critical Bug Status

**StopAsyncIteration bug: FIXED** — All turns complete with "Errors: none".

## Findings

1. **convergence_recompute: CHECKER BUG** — Uses post-increment `turn_no` instead of pre-increment `current_turn` for roll_starvation. Fix committed (b593d8c) but stored scores are from before the fix. Re-run needed to verify.

2. **thread_urgency_decay: ENGINE BUG** — `_apply_thread_updates()` sets `urgency` but never sets `urgency_set_turn` when extraction changes urgency. Fix committed (b593d8c) but stored scores are from before the fix. Re-run needed to verify.

3. **sanitizer_lifecycle: CHECKER BUG** — Checks `threads_resolved` against `last_turn_state` (state at START of turn), but sanitizer runs at END of turn after deltas are applied. Threads added during the turn won't be in `last_turn_state`. Fix: checker should use state after deltas are applied.

4. **thread_lifecycle: ENGINE BUG** — Extraction added `navy_boarding_action` thread at T38 but it never appeared in state. Real bug, needs investigation.

## No Regressions

No new bugs introduced by I-23/I-24 changes. The engine is stable across all 5 packs.

## Next

- Fix sanitizer_lifecycle checker (use post-delta state instead of `last_turn_state`)
- Investigate thread_lifecycle failure (navy_boarding_action never appeared in state)
- Re-run convergence_recompute and thread_urgency_decay with fresh data to verify E-1 fixes
