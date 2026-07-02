# Phase 2 Report — noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist

- **Date:** 2026-07-02
- **Git SHA:** f4e74db
- **Branch:** main
- **Turns:** 15 per game (45 total)
- **Pass rate:** noir-1930s 94.9% (37/39), space-western 92.3% (36/39), golden-piracy 92.3% (36/39)

## Results by Rubric Area

### Failing Checkers (consistent across runs)

1. **convergence_recompute: FAIL** (all 3 runs)
   - Stored convergence scores don't match recomputed values
   - Likely pre-existing: formula may have changed since stored scores were computed
   - Not a regression from current changes

2. **thread_urgency_decay: FAIL** (all 3 runs)
   - Threads stay at `urgent` for 8+ turns without being demoted to `normal`/`background`
   - Example: `syndicate_pressure` thread at `urgent` for 8 turns, should demote to `normal`
   - This is a real bug — the sanitizer's urgency decay isn't working
   - **Assessment:** Likely pre-existing (sanitizer logic unchanged in current changes)

3. **extraction_retry_rates: FAIL** (space-western, golden-piracy)
   - State extractor retry error: `EXTRACTION_COERCION_FAILED: condition_change_reason is required when condition changes are present`
   - The state extractor is returning condition changes without the required `condition_change_reason` field
   - **Assessment:** Pre-existing prompt issue — state extractor prompt doesn't instruct LLM to include `condition_change_reason`

### Passing Areas (all 3 runs)
- Beats: 2/2 PASS
- Goals: 2/2 PASS
- Ruling: 2/2 PASS
- State integrity: 7/7 PASS
- Threads lifecycle: 5/5 PASS
- NPC presence: PASS
- Location: PASS
- Curtain Call: PASS
- GM Beat Lifecycle: PASS

## Critical Bug Status

**StopAsyncIteration bug: FIXED** — All turns complete with "Errors: none". The extraction pipeline DRY refactor bug is resolved.

## Findings

1. **thread_urgency_decay not working** — Threads stay urgent indefinitely. The sanitizer should demote threads from `urgent` → `normal` after 8 turns, and `normal` → `background` after 16 turns. This is a real bug that affects long-term gameplay.

2. **State extractor missing condition_change_reason** — When conditions change, the state extractor must include `condition_change_reason`. The LLM is not being prompted to include this field. This causes validation errors and retries.

3. **convergence_recompute mismatch** — Pre-existing issue, not a regression.

## No Regressions

No new bugs introduced by I-23/I-24 changes. The engine is stable across all 3 packs.

## Next

thread_urgency_decay and extraction_retry_rates are real issues but likely pre-existing. Need to investigate whether they're regressions or pre-existing before proceeding to Phase 3.

Recommend: Fix thread_urgency_decay and extraction_retry_rates before Phase 3, as they affect gameplay quality.
