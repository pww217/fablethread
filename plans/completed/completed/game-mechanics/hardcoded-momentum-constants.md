# Eliminate hardcoded momentum constants in universal_asserts.py

## Status
`completed`

## Phases

2 phases: Replace the two hardcoded references to engine constants in `ccya/eval/universal_asserts.py` with imports from `ccya.eval.engine_mirror`, which itself sources live values from production code. This eliminates drift risk if momentum behavior changes in the engine.

## Issue
Two locations in universal_asserts.py hardcode engine constants inline instead of importing them from `engine_mirror`: (1) the momentum delta mapping dict at lines 541-548 mirrors `ccya.rules.MOMENTUM_DELTA` but is duplicated, and (2) the floor threshold `-3` at line 631 mirrors `MOMENTUM_MIN` from `ccya.state.momentum`. If these values ever change in production code, the assertions silently validate against stale expectations — producing false positives (accepting wrong behavior) or false negatives (flagging correct behavior). Report.py was already fixed (commit `0f4af40`) to import `MOMENTUM_MIN`, but universal_asserts.py was missed.

## Solution
Import `MOMENTUM_DELTA` and `MOMENTUM_MIN` from `ccya.eval.engine_mirror` at the top of universal_asserts.py, then replace both inline references with the imported constants. This is a single-source-of-truth fix: if engine defaults change, only engine_mirror.py needs updating (and it imports directly from production code).

## Firm decisions
- Import from `ccya.eval.engine_mirror`, not directly from `ccya.rules` or `ccya.state.momentum`. Engine_mirror is the eval harness's designated constants module and provides a stable import path for scenarios and assertions.
- The momentum delta mapping in engine_mirror.py is defined as `MOMENTUM_DELTA: dict[str, int] = dict(_RULES_MOMENTUM_DELTA)`, which is already imported from `ccya.rules`. No changes needed to engine_mirror.py itself.

## Non-goals
- Do not touch report.py — it was already fixed in commit `0f4af40` (imports MOMENTUM_MIN correctly).
- Do not change the clamp tolerance logic at line 580 (accepted as intentional design tradeoff, tracked as L6 in FINDINGS.md).
- Do not add tests for these changes.

## Risks, Ambiguities, and Blockers
- Need to verify that `engine_mirror.py` exports both `MOMENTUM_DELTA` and `MOMENTUM_MIN`. It does (lines 30-32), but confirm no circular import issues when universal_asserts imports from engine_mirror.
- The momentum delta dict is used in a `.get(band)` call at line 548. If the band value is unknown, it returns `None` and the assertion passes with "(unknown band)" detail (line 549). This behavior should be preserved — importing the dict doesn't change this logic.

## Implementation — Phase 1: Add imports and replace momentum delta mapping

### Context files to load
- `ccya/eval/universal_asserts.py` (full file, especially lines 1-20 for existing imports)
- `ccya/eval/engine_mirror.py` (lines 30-32 for MOMENTUM_DELTA/MOMENTUM_MIN definitions)

### Detailed steps

#### Step 1.1 — Add engine_mirror import at top of universal_asserts.py

**File:** `ccya/eval/universal_asserts.py`, after line 14 (`from typing import Any`)

**What:** Insert the following import:
```python
from ccya.eval.engine_mirror import MOMENTUM_DELTA, MOMENTUM_MIN
```

**Why:** Provides access to live engine constants via the eval harness's designated constants module. Single source of truth — if momentum behavior changes in production code, only engine_mirror.py needs updating (it imports directly from `ccya.rules` and `ccya.state.momentum`).

**Validation:** Confirm the import is present at the top of the file alongside other imports. Run:
```bash
python -c "from ccya.eval.universal_asserts import MOMENTUM_DELTA, MOMENTUM_MIN; print('OK')" 2>&1 | head -5
```
Should output `OK` with no errors (verifies no circular import issues).

#### Step 1.2 — Replace hardcoded momentum delta dict with imported constant

**File:** `ccya/eval/universal_asserts.py`, lines 540-548

**What:** In the `check_momentum_band_delta()` function, replace the inline dict at lines 541-548:
```python
expected = {
    "crit_success": 2,
    "success": 1,
    "partial": 0,
    "setback": -1,
    "fail": -1,
    "crit_fail": -2,
}.get(band)
```
With:
```python
expected = MOMENTUM_DELTA.get(band)
```

**Why:** Eliminates the duplicated constant. `MOMENTUM_DELTA` is imported from `ccya.rules.MOMENTUM_DELTA` via engine_mirror.py and contains exactly the same mapping currently, but will stay in sync if production code changes. The `.get(band)` call behavior is identical — returns `None` for unknown bands, which triggers the "(unknown band)" pass-through at line 549-556.

**Validation:** Run grep to confirm no inline dict remains:
```bash
grep -n 'crit_success.*2\|crit_fail.*-2' ccya/eval/universal_asserts.py
```
Should return nothing (the only match should be in the imported constant definition, not here). Also verify the function still works by checking that `expected` is used correctly downstream at line 580.

## Tests to write or update
None — this is a constants import replacement with no behavioral change. Run lint/typecheck:
```bash
make check
```

## REPOMAP updates required
- `docs/repomap.md`: Update the "Eval harness" section if it documents universal_asserts.py's hardcoded constants (verify current state first). If there's an entry listing "universal_asserts.py — 15 assertions with inline momentum deltas", update to reflect that they now import from engine_mirror.

---

## Implementation — Phase 2: Replace hardcoded floor threshold `-3` with MOMENTUM_MIN

### Context files to load
- `ccya/eval/universal_asserts.py`, lines 620-638 (check_momentum_floor_no_relief function)
- `ccya/eval/engine_mirror.py`, line 30 (MOMENTUM_MIN definition)

### Detailed steps

#### Step 2.1 — Replace hardcoded `-3` with MOMENTUM_MIN in floor check

**File:** `ccya/eval/universal_asserts.py`, line 631

**What:** In the `check_momentum_floor_no_relief()` function, replace:
```python
if m is not None and m <= -3:
```
With:
```python
if m is not None and m <= MOMENTUM_MIN:
```

**Why:** Matches what report.py already does (commit `0f4af40` fixed this in report.py but missed universal_asserts.py). If `MOMENTUM_MIN` ever changes from `-3`, the assertion automatically adapts. Single source of truth via engine_mirror → ccya.state.momentum.MOMENTUM_MIN.

**Validation:** Run grep to confirm no hardcoded floor value remains:
```bash
grep -n '<= -3' ccya/eval/universal_asserts.py
```
Should return nothing (the `-3` literal should be gone from this file). Also verify the assertion behavior is unchanged by checking that `MOMENTUM_MIN == -3`:
```bash
python -c "from ccya.eval.engine_mirror import MOMENTUM_MIN; assert MOMENTUM_MIN == -3, f'Expected -3 got {MOMENTUM_MIN}'; print('OK')" 2>&1
```

## Tests to write or update
None — constants replacement with no behavioral change. Final verification:
```bash
make check
```

## REPOMAP updates required
- `docs/repomap.md`: Same as Phase 1 — verify if the repomap documents hardcoded constants in universal_asserts.py and update accordingly.
