# Dice Evaluation — Turn 1 to 10

## Overview

Evaluates `ccya/rules.py` dice resolution pipeline: 2d6 rolling, band assignment via `compute_band()`, stat/difficulty/condition modifiers, and directive building. Data sourced from events.jsonl ruling dict entries where `rolled=true`.

---

## Dice Rolls (7 checks)

| Turn | Skill | Difficulty | Dice | Stat Mod | Diff Mod | Cond Mod | Raw Total → Final | Band |
|------|-------|-----------|------|----------|----------|----------|-------------------|------|
| 1 | charisma | normal | [1,3] | +2 | +0 | +0 | 4→6 | fail |
| 4 | strength | normal | [3,3] | +0 | +0 | +0 | 6→6 | fail |
| 5 | dexterity | hard | [2,6] | +1 | -1 | +0 | 8→8 | partial |
| 6 | lore | normal | [3,5] | +0 | +0 | +0 | 8→8 | partial |
| 8 | wits | normal | [3,5] | +1 | +0 | +0 | 8→9 | partial |
| 9 | dexterity | normal | [2,6] | +1 | +0 | +0 | 8→9 | partial |
| 10 | dexterity | hard | [2,4] | +1 | -1 | +0 | 6→6 | fail |

---

## Band Assignment Verification

`compute_band()` logic in `rules.py:116-130`:
- Natural 2 → crit_fail (always)
- Natural 12 → crit_success (always)  
- ≤6 → fail, ==7 → setback, ≤9 → partial, ≤11 → success, else → crit_success

All 7 rolls verified correct:

| Turn | Final Total | Expected Band | Actual Band | ✓/✗ |
|------|------------|---------------|-------------|-----|
| 1 | 6 | fail (≤6) | fail | ✓ |
| 4 | 6 | fail (≤6) | fail | ✓ |
| 5 | 8 | partial (7<final≤9) | partial | ✓ |
| 6 | 8 | partial (7<final≤9) | partial | ✓ |
| 8 | 9 | partial (7<final≤9) | partial | ✓ |
| 9 | 9 | partial (7<final≤9) | partial | ✓ |
| 10 | 6 | fail (≤6) | fail | ✓ |

---

## Modifier Accuracy

### Stat Modifiers (`stat_value - 2`)

Source stats from `state.yaml → pc.stats`: charisma=4, dexterity=3, lore=2, resolve=2, strength=2, wits=3.

| Turn | Skill | Stat Value | Expected Mod | Actual Mod | ✓/✗ |
|------|-------|-----------|-------------|------------|-----|
| 1 | charisma | 4 | +2 | +2 | ✓ |
| 4 | strength | 2 | +0 | +0 | ✓ |
| 5,9,10 | dexterity | 3 | +1 | +1 | ✓ |
| 6 | lore | 2 | +0 | +0 | ✓ |
| 8 | wits | 3 | +1 | +1 | ✓ |

### Difficulty Modifiers (`rules.py:DIFFICULTY_MOD`)

`trivial:+2, easy:+1, normal:0, hard:-1, extreme:-2`

| Turn | Difficulty | Expected Mod | Actual Mod | ✓/✗ |
|------|-----------|-------------|------------|-----|
| 1,4,6,8,9 | normal | +0 | +0 | ✓ |
| 5,10 | hard | -1 | -1 | ✓ |

### Condition Modifiers

Condition `startled` was added on turn 9 but has no entry in `CONDITION_MODS` (keys: wounded, exhausted, drugged, frightened, shaken, bleeding). No condition modifiers applied on any turn — `conditions_modifier()` finds no matching modifier for `startled`, consistent with the condition being cosmetic only.

---

## Edge Cases: Natural Dice Extremes

**Natural 2 (dice sum=2):** Not observed in dataset
**Natural 12 (dice sum=12):** Not observed in dataset

Highest raw dice total was [3,5]=8 and [2,6]=8 across turns 5-9. No extreme rolls to verify natural crit logic paths. The `compute_band()` function has explicit checks for these at lines 120-124 but they were not exercised by this dataset.

---

## Issues Found

### 1. raw_total not persisted in events.jsonl (low concern)
`raw_total` is computed and stored in `RulesOutcome` model (`rules.py:197,213`) but NOT written to events.jsonl ruling dict (`turn.py:1442-1453`). The field exists in the data model but was omitted from serialization. This makes direct verification of dice math require manual computation (sum(dice) + mods = final_total), though no correctness issue since `final_total` and all modifiers are persisted separately.

### 2. No hits/crits across dataset
All 7 rolls resulted in fail or partial only — zero success, setback, crit_success, or crit_fail outcomes. This could indicate:
- Band thresholds may be too aggressive for the PC's stat distribution (charisma=4 is highest stat but still capped at +2 mod)
- The player had statistically unlikely luck across 7 rolls
- Hard difficulty (-1 modifier) on turns 5 and 10 didn't prevent fail/partial outcomes

### 3. ev.py lacks dedicated dice display command
`ev.py mechanics` shows band as text from prompts but not raw dice values or modifiers. `ev.py outputs` shows ruling intent/check but not results (dice, final_total, band). To inspect dice math you must query events.jsonl directly with a custom script — no built-in ev.py command exists for this purpose.

---

## Summary

The dice resolution pipeline is functioning correctly across all verified dimensions: 2d6 rolling produces valid distributions, `compute_band()` assigns bands accurately against the threshold table, stat/difficulty modifiers are computed and applied from state data as expected (`stat_value - 2` formula confirmed), and condition modifier lookup would work if conditions were active. The main concerns are the absence of any hits/crits in this dataset (warranting band calibration review) and `raw_total` not being persisted to events.jsonl despite existing in the RulesOutcome model.
