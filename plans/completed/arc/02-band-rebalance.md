# Supporting Changes — Phase 2: Band Rebalancing + Partial Directive

## Purpose

Shift the `partial` band threshold from ≤8 to ≤7 to compensate for condition-driven difficulty bias, and strengthen the `build_directive()` output for the `partial` band. Fix the `rules.py` module docstring which incorrectly describes crit thresholds as raw-die-only.

## Firm decisions

- `compute_band()`: `final_total <= 8` → `final_total <= 7` for partial band. (One-line change at rules.py:111.)
- `build_directive()` partial text: cost made mandatory and concretely named.
- Module docstring: corrected from "raw_die 1 → crit_fail (always, ignores modifiers)" to "final_total <= 1 → crit_fail, final_total >= 12 → crit_success."

## Status

`completed`

## Implementation — Phase 2: Band Rebalancing + Partial Directive

### Context files to load

- `ccya/rules.py` — full file (189 lines)

### Detailed steps

#### Step 2.1 — Shift partial band threshold

**File:** `ccya/rules.py`

**What:** Change line 111:
```python
# Old:
if final_total <= 8:
    return "partial"
# New:
if final_total <= 7:
    return "partial"
```

**Why:** Condition distribution across 81 turns shows 18:1 negative-to-positive ratio. Conditions bias difficulty upward (55% of rolls at hard), shifting effective distribution left. The ≤7 threshold restores the partial band's intended ~8.3% probability under typical condition load.

**Validation:** `.venv/bin/python -c "from ccya.rules import compute_band; assert compute_band(7, 7) == 'partial'; assert compute_band(8, 8) == 'success'"`

#### Step 2.2 — Fix module docstring

**File:** `ccya/rules.py`

**What:** Replace the docstring (lines 1-14) with corrected text:

```python
"""Pure-Python rules engine. No LLM, no I/O.

Dice system: 1d12 + stat_mod + difficulty_mod.
  stat_mod   = stat_value - 2  (stat range 1-4 → mod -1..+2)
  diff_mod   = DIFFICULTY_MOD[difficulty]

PbtA 7-band resolution (1d12):
  final_total <= 1  → crit_fail  (modifiers affect crit probability)
  final_total <= 5  → fail
  final_total == 6  → setback
  final_total <= 7  → partial
  final_total >= 8  → success
  final_total >= 12 → crit_success (modifiers affect crit probability)
"""
```

Note: "final_total == 6" for setback and "final_total <= 7" for partial reflect the new threshold. Crit docs corrected from "raw_die 1" (always) to "final_total <= 1" (modifier-sensitive).

**Why:** The docstring was factually wrong — `compute_band()` uses `final_total` for crit thresholds, not raw die. Conditions and skills should affect crit probability (a player in a -2 condition stack can crit-fail on raw die 3).

**Validation:** `.venv/bin/python -c "import ccya.rules; print(ccya.rules.__doc__)"` — verify text.

#### Step 2.3 — Strengthen partial directive in build_directive()

**File:** `ccya/rules.py`

**What:** The partial band currently falls through to the `_DIRECTIVE_TABLE` lookup at lines 117-123. Update the `_DIRECTIVE_TABLE` for `partial` entries to make the cost mandatory. Find the `_DIRECTIVE_TABLE` definition and update the `"partial"` values.

Specifically, the table is near the top of the file (likely lines 32-38 based on the roll band table). Change partial directives from optional-flavor text to mandatory-cost text. The exact text per verb category should follow the design spec:

```
"partial": {
    ...
}
```

If the table uses a default entry, change the default directive for partial to something equivalent to: "The [verb] partially succeeds — but the cost is mandatory and must be named concretely: a wound taken, a resource spent, leverage given to an opponent, or a new complication now in play. Do not narrate a clean success. The cost is not optional flavor."

**Why:** EV data shows partial often narrated as clean success. Strengthening the directive text makes the cost non-optional. This is a prompt-safety measure to ensure partial outcomes feel mechanically meaningful.

**Validation:** `.venv/bin/python -c "from ccya.rules import build_directive; d = build_directive('partial', 'attack', 'strength'); assert 'must' in d or 'cost is' in d"`

### Tests to write or update

No tests exist. Run `make check` after all phases complete.
