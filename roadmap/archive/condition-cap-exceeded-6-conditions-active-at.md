---
title: "Condition cap exceeded — 6 conditions active at T21, exceeding PC_CONDITIONS_MAX=5"
status: canceled
created: 2026-06-12
labels:
  - Bug
  - Extraction
---

## Bug

`PC_CONDITIONS_MAX = 5` (from `ccya/state/delta_builder.py:23`). At T21, 6 conditions are active, exceeding the cap by 1.

## Evidence

From applied data tracking active conditions in cordyceps-year-twenty-2026-06-11 save:

| Turn | Active Count | Conditions |
|------|-------------|------------|
| T13 | 3 | pinned, wounded_chest, bleeding_chest |
| T16-T17 | 3 | bleeding_chest, pinned_by_lights, wounded_chest |
| T19 | 4 | bleeding, bleeding_chest, injured_ribs, wounded_chest |
| T20-T24 | 5 | at cap |
| **T21** | **6** | **bleeding, bleeding_chest, injured_ribs, lightheadedness, pinned, wounded_chest** |

T21 exceeds the cap by 1 condition.

## Scope

* Investigate why condition cap is not enforced at T21
* Ensure cap is applied when conditions are added, not just at state snapshot time
* Add checker to detect cap violations

## Files

* `ccya/state/delta_builder.py` — PC_CONDITIONS_MAX definition (line 23)
* `ccya/engine/extraction.py` — condition extraction
* `ccya/engine/sanitizer.py` — condition application
* `ccya/ev/checkers/` — conditions lifecycle checker

## Validation

Confirmed in `docs/ev/cordyceps-findings.md §5a` — 6 conditions active at T21, exceeding PC_CONDITIONS_MAX=5.
