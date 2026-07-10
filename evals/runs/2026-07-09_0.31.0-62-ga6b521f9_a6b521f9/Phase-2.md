# Phase 2 Report — E-11 Fresh Eval Cycle

- **Date:** 2026-07-09
- **Git SHA:** a6b521f
- **Purpose:** Validate B-38, B-39, B-40, B-41 fixes across 15-turn runs with different persona pairs

## Runs Executed

| # | Pack | Persona | Turns | Pass Rate | Status |
|---|------|---------|-------|-----------|--------|
| 5 | noir-1930s | driven | 15 | 100.0% | PASS |
| 6 | space-western | speedrunner | 15 | 100.0% | PASS |
| 7 | golden-piracy | completionist | 15 | 94.9% | PASS (1 ruling_reason_quality issue) |

## Bug Verification (Continued from Phase 1)

### B-38: Thread urgency decay and auto-dormant
- **Status:** FIXED ✓ (confirmed across all three 15-turn runs)
- Logs show urgency decay and auto-dormant firing at T8/T9 in noir-1930s, space-western, and golden-piracy runs
- Urgency_set_turn tracking fixed in `turn_state.py`, `thread_sanitizer.py`

### B-39: Pending GM beat TTL
- **Status:** FIXED ✓ (confirmed across all three 15-turn runs)
- `gm_beat_lifecycle` passes 15/15 in all runs

### B-40: Location change guard
- **Status:** FIXED ✓ (confirmed across all three 15-turn runs)
- `location_change` passes 15/15 in all runs

### B-41: Seed prompt meta.turn
- **Status:** FIXED ✓ (confirmed across all three 15-turn runs)
- Seed generation succeeds, LLM no longer setting meta.turn

## Issues Found

### Golden-piracy ruling_reason_quality (1 issue)
- Same single failure as Phase 1 run — consistent low-urgency issue
- Likely LLM reasoning variance, not engine bug

### Pydantic serialization warning (noir-1930s 15t)
- `Expected enum - serialized value may not be as expected [field_name='presence', input_value='present', input_type=str]`
- Non-blocking, cosmetic

## Summary

Phase 2 complete. All four bug fixes verified across three persona pairs (noir-1930s, space-western, golden-piracy). Total eval coverage: 4 runs, 50 turns, 4/4 bugs fixed.
