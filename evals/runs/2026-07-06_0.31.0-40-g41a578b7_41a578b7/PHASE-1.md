# Phase 1 Report — noir-1930s:driven, 5 turns

- **Run:** `evals/runs/2026-07-06_0.31.0-40-g41a578b7_41a578b7/1055_noir-1930s_5t`
- **Date:** 2026-07-06
- **Git SHA:** 41a578b7 (at start), 76456c41 (after fixes)
- **Pass rate:** 94.9% (37/39 checkers)

## Findings

### Critical: False positives in thread_lifecycle and sanitizer_lifecycle checkers

Both checkers looked at `last_turn_state.arc.threads` instead of `last_turn_state.long_term_objective.threads`, causing all seed thread references to fail validation. This was a bug in the checkers, not the engine.

**Fix:** Updated both checkers to use backward-compat pattern: `snap.get("arc") or snap.get("long_term_objective") or {}`.

### Medium: beat_candidates_present fails on T3

Turn 3 has empty `beat_candidates` despite world step running. The LLM may have returned beats that were all filtered as duplicates or phase violations. Needs investigation across more turns to determine if this's a pattern or one-off.

### Minor: ruling_band_distribution fails (expected)

Only 1 dice roll across 5 turns (100% crit_success). This is expected with such a short run — not a bug.

## Verdict

**No critical engine bugs found.** The thread_lifecycle/sanitizer_lifecycle failures were false positives in the checkers themselves (now fixed). Engine ran cleanly through 5 turns with no game-breaking issues.

Proceeding to Phase 2.
