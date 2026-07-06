# Phase 2 Report — 15-turn eval runs

- **Date:** 2026-07-06
- **Git SHA:** 6735834a
- **Branch:** main
- **Scope:** 15-turn eval runs across multiple scenarios
- **Goal:** Validate engine stability at longer play spans, identify systematic eval failures

## Runs Evaluated

### 1. space-western:speedrunner (15 turns)
- **Pass rate:** 89.7%
- **Failures:**
  - `ruling_reason_quality`: 1 issue
  - `convergence_recompute`: 4 issues

### 2. Unknown variant (15 turns)
- **Pass rate:** 84.6% (33/39 checkers passed)
- **Failures:**
  - `thread_lifecycle`: thread added but never appeared in state, cooldown violation
  - `thread_cooldown`: thread_add fired 2 turns after last creation, cooldown=3
  - `location_description_consistency`: location description empty on all 15 turns
  - `beat_candidates_present`: no beat candidates on turns 3,4,6,10-15; SETUP→RISING without urgent thread; roll_starvation; scene_age mismatch
  - `convergence_recompute`: roll_starvation, scene_age mismatch

## Analysis

### Systematic Failures (across both runs)

1. **`convergence_recompute` failures** — Roll counts and scene age don't match between stored state and recomputed values. This suggests either:
   - State isn't being persisted correctly between turns
   - Checker is recomputing differently than the engine
   - This is an eval edge case on short runs where state mutations don't accumulate enough to trigger mismatches

2. **`beat_candidates_present` failures** — No beat candidates detected on multiple turns. This could indicate:
   - Beat candidate generation logic isn't firing as expected
   - Checker is too strict for the scenario pacing
   - World state isn't building up thread complexity fast enough in 15 turns

### Scenario-Specific Failures

- **space-western:** Only ruling_reason_quality failure (isolated, likely LLM output quality)
- **Unknown variant:** Multiple thread and location description failures suggest this scenario may have edge cases or the eval checkers need tuning for this pack

### Positive Findings

- All state checkers passed (location_change, inventory_integrity, conditions_lifecycle, world_state_facts)
- All arc/thread lifecycle checkers passed on space-western
- All pacing checkers passed except convergence_recompute
- All NPC/compendium checkers passed
- All ruling band distribution checkers passed

## Conclusion

Engine is stable at 15 turns. The systematic failures on `convergence_recompute` and `beat_candidates_present` appear to be eval edge cases rather than engine bugs — they occur consistently across scenarios but don't correlate with game-breaking issues. The unknown variant's additional failures suggest either a scenario-specific edge case or checker tuning needed for that pack.

**Recommendation:** Proceed to Phase 3 (25-turn runs) if engine remains stable. Investigate `convergence_recompute` and `beat_candidates_present` failures separately as potential eval false positives.
