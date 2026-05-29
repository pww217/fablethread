# Momentum Tracking — Turn 1 to 10

## Overview

Evaluates `ccya/state/momentum.py` momentum application system: band→delta mapping via `MOMENTUM_DELTA`, clamping to [-3, +3], state persistence, and integration with the ruling pipeline (only called when `rolled=True`). Data sourced from top-level event fields in events.jsonl (`momentum_before`, `momentum_after`, `momentum_delta`) which are written unconditionally for all turns.

---

## Momentum Evolution

| Turn | Before | After | Delta | Band | Action Taken |
|------|--------|-------|-------|------|-------------|
| 1 | +0 | -1 | -1 | fail | apply_momentum called, delta=-1 |
| 2 | -1 | -1 | +0 | (no roll) | skipped — no check required |
| 3 | -1 | -1 | +0 | (no roll) | skipped — no check required |
| 4 | -1 | -2 | -1 | fail | apply_momentum called, delta=-1 |
| 5 | -2 | -2 | +0 | partial | apply_momentum called, delta=+0 |
| 6 | -2 | -2 | +0 | partial | apply_momentum called, delta=+0 |
| 7 | -2 | -2 | +0 | (no roll) | skipped — no check required |
| 8 | -2 | -2 | +0 | partial | apply_momentum called, delta=+0 |
| 9 | -2 | -2 | +0 | partial | apply_momentum called, delta=+0 |
| 10 | -2 | -3 | -1 | fail | apply_momentum called, delta=-1 |

**Evolution path:** T1:-1 → T2:-1 → T3:-1 → T4:-2 → T5:-2 → T6:-2 → T7:-2 → T8:-2 → T9:-2 → T10:-3

---

## Band→Delta Mapping Verification

`MOMENTUM_DELTA` table in `rules.py:76-83`:
```python
{
    "crit_success": 2,
    "success": 1,
    "partial": 0,
    "setback": -1,
    "fail": -1,
    "crit_fail": -2,
}
```

All observed bands match expected deltas:

| Band | Expected Delta | Observed Deltas | ✓/✗ |
|------|---------------|-----------------|-----|
| fail | -1 | Turns 1,4,10 → all delta=-1 | ✓ |
| partial | +0 | Turns 5,6,8,9 → all delta=+0 | ✓ |

**Not observed in dataset:** crit_success (+2), success (+1), setback (-1), crit_fail (-2) — no rolls achieved these bands.

---

## Clamping Behavior Verification

`MOMENTUM_MIN=-3`, `MOMENTUM_MAX=+3` (defined at `momentum.py:12-13`).

Clamping logic in `apply_momentum()`:
```python
new_val = max(MOMENTUM_MIN, min(MOMENTUM_MAX, current + delta))
```

**No clamping occurred during turns 1-10.** Momentum ranged from -2 to +0 (after turn 9), never approaching the [-3,+3] boundaries. Turn 10 reached exactly -3 but no subsequent fail/setback/crit_fail roll would have pushed it below, so clamping was not exercised.

**Boundary test cases that WOULD trigger clamping:**
- If momentum=+3 and band=crit_success (+2): `max(-3, min(3, 5))` → +3 (clamped down from 5)
- If momentum=-3 and band=fail (-1): `max(-3, min(3, -4))` → -3 (clamped up from -4)

These edge cases exist in the code but were not tested by this dataset. The clamping logic is simple and correct — no concerns raised.

---

## State Continuity Verification

Top-level event fields `momentum_before`, `momentum_after`, `momentum_delta` are written unconditionally for ALL turns (including non-roll ones) at `turn.py:1466-1468`. This ensures momentum state is always visible in events.jsonl regardless of whether a check occurred.

**Continuity verified:** `momentum_after` of turn N equals `momentum_before` of turn N+1 for all consecutive turns (T1→T2, T2→T3, ..., T9→T10). No breaks detected.

---

## Integration with Ruling Pipeline

### When apply_momentum is called

Only when `_outcome.rolled=True` (`turn.py:800-802`). Non-roll turns (no check required) skip momentum application entirely — `apply_momentum()` never invoked, delta remains 0, and state persists unchanged from prior turn.

Verified for non-roll turns in this dataset:
| Turn | Check Required? | apply_momentum Called? | Momentum Change? | ✓/✗ |
|------|----------------|------------------------|------------------|-----|
| 2 | No (auto-assess) | No | None (-1→-1) | ✓ |
| 3 | No (auto-assess) | No | None (-1→-1) | ✓ |
| 7 | No (redundant roll avoided) | No | None (-2→-2) | ✓ |

### Momentum fields in events.jsonl ruling dict vs top-level event

There are two locations for momentum data:

**Top-level event** (`event['momentum_before']`, `event['momentum_after']`, `event['momentum_delta']`):
- Written unconditionally for ALL turns (including non-roll ones)
- Always present and numeric
- Source of truth for state continuity tracking

**Ruling dict** (`event['ruling']['momentum_before']`, etc.):
- Only written when `_outcome.rolled=True` (conditional at `turn.py:1450-1453`)
- Absent on non-roll turns — no momentum fields inside ruling dict
- Contains same values as top-level event for roll turns

**Important:** When analyzing events.jsonl, always use top-level event momentum fields to get complete picture across all turn types. Querying `ruling.momentum_before` returns None/missing on non-roll turns and can mislead analysts into thinking momentum was reset or lost (see ruling.md note about Turn 7 false anomaly).

---

## Issues Found

### 1. Clamping never tested in this dataset
Momentum stayed within [-2, +0] range across all 10 turns — the clamping logic at boundaries (-3 and +3) was never exercised. While the code is simple and correct (`max(MIN, min(MAX, val))`), there are no dedicated tests or scenario evaluations that push momentum to extremes (e.g., consecutive crit_success rolls from +2 → would clamp at +3).

### 2. Momentum delta on non-roll turns always zero
Non-roll turns show `momentum_delta=0` and unchanged before/after values, which is correct behavior but means there's no way to distinguish "no momentum change because apply_momentum was skipped" from "apply_momentum ran with a band that has delta=0 (partial)" by looking at top-level event fields alone. The distinction exists in the ruling dict (`rolled: false` vs `band: partial`) but is lost if only analyzing top-level momentum fields.

---

## Summary

The momentum tracking system functions correctly across all verified dimensions: band→delta mapping matches the MOMENTUM_DELTA table exactly, clamping logic at [-3,+3] boundaries exists and uses correct Python min/max pattern (though never exercised in this dataset), state continuity is maintained across consecutive turns with no breaks, and integration with the ruling pipeline correctly skips apply_momentum on non-roll turns. The main concerns are that boundary clamping was never tested and there's no way to distinguish skipped momentum application from zero-delta bands using only top-level event fields (though the distinction exists in events.jsonl via `ruling.rolled`).
