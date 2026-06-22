# 2d6 → 1d12 Dice System Swap

## Status
`completed`

## Phases

1 phase: Replace 2d6 with 1d12, recalibrate band thresholds, update UI + tooling + docs in one sweep.

## Issue

Current 2d6 system produces a bell-curve clustering around 7, yielding ~42% partial outcomes ("yes, but") — too many middling results that fail to drive the story forward in clear directions. The problem is inherent to the 2d6 distribution: strong central tendency, thin tails.

## Solution

Swap to 1d12 (uniform distribution, each face = 8.3%). New thresholds:

| Band | Condition | Notes |
|---|---|---|
| crit_fail | natural 1 | Always, ignores modifiers |
| fail | final_total ≤ 5 | |
| setback | final_total = 6 | |
| partial | final_total 7–8 | |
| success | final_total ≥ 9 | |
| crit_success | natural 12 | Always, ignores modifiers |

Near-miss (fail + roll within 1 of success): fail band with `final_total >= 5` (unchanged concept, adjusted threshold).

Resulting probabilities per skill level:

| Stat | Mod | cf | fail | set | part | suc | cfs | Fail-ish | Success-ish |
|---|---|---|---|---|---|---|---|---|---|
| 1 | −1 | 8.3% | 41.7% | 8.3% | 16.7% | 16.7% | 8.3% | 50.0% | 25.0% |
| 2 | 0 | 8.3% | 33.3% | 8.3% | 16.7% | 25.0% | 8.3% | 41.6% | 33.3% |
| 3 | +1 | 8.3% | 25.0% | 8.3% | 16.7% | 33.3% | 8.3% | 33.3% | 41.6% |
| 4 | +2 | 8.3% | 16.7% | 8.3% | 16.7% | 41.7% | 8.3% | 25.0% | 50.0% |

Partial drops from ~42% to 16.7%. Baseline (stat 2) slightly failure-biased (41.6% vs 33.3%). Stat 3 (+1) flips to success bias.

## Firm decisions

1. Natural 1 = auto crit_fail, natural 12 = auto crit_success (8.3% each).
2. `final_total` threshold bands as above. No change to modifier formulas (stat_mod = stat_value − 2, diff_mod from DIFFICULTY_MOD, cond_mod from CONDITION_MODS).
3. `dice` field in RulesOutmodel stays `list[int]` but always has exactly 1 element.
4. UI shows single d12 result with "d12" label instead of two d6 pips.
5. ev.py dice command updated to handle single-die display.
6. No backwards compatibility — old save files with dice values don't need migration (the `dice` field is per-turn, not persisted in state.yaml).
7. Momentum deltas and `MOMENTUM_DELTA` mapping unchanged — bands are the same, only thresholds changed.

## Non-goals

- No change to skill names, difficulty levels, condition mods, stat range (1-4), or any other game mechanic.
- No change to `compute_band` function signature — only its internals and callers that inspect specific threshold values.
- No change to `resolve_check` function signature.
- No change to momentum deltas per band.
- No migration code (dice field is per-turn, not durable).

## Risks, Ambiguities, and Blockers

- The `near_miss` check in `resolve_check()` currently reads `final_total >= 6` (the old fail/setback boundary). With new thresholds, near-miss should be `final_total >= 5` (within 1 of setback threshold at 6). This changes the token but preserves the semantics: "close to a better outcome."
- The `dice` field in `RulesOutcome` is `list[int]` — consumers that expect `len(dice) == 2` will break. All must be updated in this phase. No migration needed for state.yaml (dice is per-turn data only).
- Eval runs against newly generated data work without changes to existing scenario YAML (scenarios define asserts on `rolled=true/false`, not specific dice values).
- No evaluation packs need updating — they define behavior expectations, not dice math.

## Implementation — Phase 1: Core rules + all downstream consumers

### Context files to load

- `ccya/rules.py` (full file)
- `ccya/models.py` (RulesOutcome class, lines 162-176)
- `ccya/engine/turn.py` (ruling dict serialization, lines 830-920; also check near_miss usage around line 201)
- `ccya/templates/index.html` (dice display: template lines 120-140, JS lines 460-490)
- `ccya/templates/_turn_log.html` (dice display: lines 9-15)
- `scripts/debug/ev.py` (cmd_dice function, lines 2007-2072)
- `docs/repomap.md` (lines 47, 79, 198 — 2d6 references)
- `docs/architecture/step0-ruling.md` (line 27 — mermaid flowchart)
- `docs/architecture/OVERVIEW.md` (line 51 — pipeline table)

### Detailed steps

#### Step 1.1 — Replace `roll_2d6` with `roll_1d12`

**File:** `ccya/rules.py`

**What:** Replace `roll_2d6()` (returns `tuple[int, int]`) with `roll_1d12()` (returns `int`). The old function name is a `_private`-style; keep naming convention: `roll_1d12`.

```python
def roll_1d12(rng: random.Random | None = None) -> int:
    r = rng or random
    return r.randint(1, 12)
```

**Why:** Single die replaces two. Simpler return type.

**Validation:** `make check` passes.

#### Step 1.2 — Recalibrate `compute_band`

**File:** `ccya/rules.py`

**What:** Replace the `compute_band` body. The signature changes from `def compute_band(final_total: int, dice: tuple[int, int])` to `def compute_band(final_total: int, raw_die: int) -> str`.

**Threshold logic:**
- `raw_die == 1` → `"crit_fail"` (always, ignores modifiers)
- `raw_die == 12` → `"crit_success"` (always, ignores modifiers)
- `final_total <= 5` → `"fail"`
- `final_total == 6` → `"setback"`
- `final_total <= 8` → `"partial"`
- `final_total >= 9` → `"success"` (covers rolls 9–11; roll 12 is caught by natural crit above)

**Why:** New band thresholds matching the agreed probability table. Natural crits checked on raw die before modifiers.

**Validation:** `make check` passes. Run a python one-liner to verify threshold ranges cover all 12 outcomes correctly for each modifier.

#### Step 1.3 — Update `resolve_check` call site

**File:** `ccya/rules.py`

**What:** Four changes in `resolve_check()`:
1. `dice = roll_2d6(rng)` → `raw_die = roll_1d12(rng)`; `dice = [raw_die]` for output
2. `raw_total = dice[0] + dice[1]` → `raw_total = raw_die`
3. `band = compute_band(final_total, dice)` → `band = compute_band(final_total, raw_die)`
4. `near_miss = band == "fail" and final_total >= 6` → `near_miss = band == "fail" and final_total >= 5` (within 1 of setback=6)

**Why:** Single die means raw total is just the die value. Near-miss threshold shifts with new fail/setback boundary.

**Validation:** `make check` passes.

#### Step 1.4 — Update module docstring

**File:** `ccya/rules.py` line 3

**What:** `Dice system: 2d6 + stat_mod + difficulty_mod + condition_mod.` → `Dice system: 1d12 + stat_mod + difficulty_mod + condition_mod.`

**Validation:** `make check`.

#### Step 1.5 — Update `compute_band` call site in docs

**File:** `docs/architecture/step0-ruling.md` line 27

**What:** In mermaid flowchart node: `rolls 2d6 + stat_mod + cond_mod − diff_mod` → `rolls 1d12 + stat_mod + cond_mod − diff_mod`

**Validation:** Visual check.

#### Step 1.6 — Update pipeline table reference

**File:** `docs/architecture/OVERVIEW.md` line 51

**What:** `dice roll resolution (2d6 + stat + cond − diff → band)` → `dice roll resolution (1d12 + stat + cond − diff → band)`

**Validation:** Visual check.

#### Step 1.7 — Update template dice display (SSR)

**File:** `ccya/templates/index.html` lines 122-132

**What:** Replace two-die template rendering with single-die display.

Current:
```html
{% set d1 = (r.dice | default([]))[0] or 0 %}
{% set d2 = (r.dice | default([]))[1] or 0 %}
{% set raw_sum = d1 + d2 %}
<div class="roll-header">🎲 <strong>{{ (r.skill | default('') | upper) }}</strong> &nbsp;·&nbsp; {{ r.difficulty | default('') | lower }}</div>
<div class="roll-math">
    [{{ d1 }}] + [{{ d2 }}] = {{ raw_sum }}
```

New:
```html
{% set die_val = (r.dice | default([]))[0] or 0 %}
<div class="roll-header">🎲 <strong>{{ (r.skill | default('') | upper) }}</strong> &nbsp;·&nbsp; {{ r.difficulty | default('') | lower }}</div>
<div class="roll-math">
    [d12: {{ die_val }}] = {{ die_val }}
```

**Why:** Single die, labeled "d12".

**Validation:** Load a game with existing save data and verify history renders correctly. `dice` field for old turns still has 2-element lists (or may be empty) — uses `or 0` fallback.

#### Step 1.8 — Update template dice display (JS / SSE)

**File:** `ccya/templates/index.html` lines 462-465

**What:** Same change as SSR in the `_buildRollBadge()` JS function.

Current:
```js
const d1 = (payload.dice || [])[0] || 0;
const d2 = (payload.dice || [])[1] || 0;
const rawSum = d1 + d2;
const parts = ['[' + d1 + '] + [' + d2 + '] = ' + rawSum];
```

New:
```js
const dieVal = (payload.dice || [])[0] || 0;
const parts = ['[d12: ' + dieVal + '] = ' + dieVal];
```

**Validation:** Start a game, make a roll, verify new turn SSE renders correctly.

#### Step 1.85 — Update `_turn_log.html` dice display

**File:** `ccya/templates/_turn_log.html` lines 9-15

**What:** Same change as Steps 1.7-1.8 — replace two-die rendering with single-die d12 display.

Current:
```html
{% set d1 = (r.dice | default([]))[0] or 0 %}
{% set d2 = (r.dice | default([]))[1] or 0 %}
{% set raw_sum = d1 + d2 %}
...
    [{{ d1 }}] + [{{ d2 }}] = {{ raw_sum }}
```

New:
```html
{% set die_val = (r.dice | default([]))[0] or 0 %}
...
    [d12: {{ die_val }}] = {{ die_val }}
```

**Why:** Same rationale as index.html — single die display. `_turn_log.html` is the turn viewer sidebar template that renders historical roll outcomes.

**Validation:** Load a game with mixed old/new turns in history; verify both formats display correctly for their respective data.

#### Step 1.9 — Update ev.py dice command display

**File:** `scripts/debug/ev.py` lines 2024-2034, 2062

**What:** Change the `cmd_dice` dice column to show `d12: X` format for single-die data while remaining backward-compatible with old 2-element dice lists.

Around line 2062, replace:
```python
dice_str = str(r["dice"]) if r["dice"] else "[]"
```
with:
```python
dice_raw = r.get("dice", [])
if len(dice_raw) == 1:
    dice_str = f"d12:{dice_raw[0]}"
elif dice_raw:
    dice_str = str(dice_raw)  # old 2d6 format, backward compat
else:
    dice_str = "[]"
```

The `raw_total` fallback at line 2033-2034 (`if raw_total is None and isinstance(dice, list): raw_total = sum(dice) + ...`) works correctly for both old (2-element) and new (1-element) data unchanged.

**Why:** Visual consistency with new die format. Backward-compatible with old events.jsonl data.

**Validation:** Run `python scripts/debug/ev.py dice` against an existing events.jsonl file. Old data shows old format (2 elements), new data shows new format (1 element).

#### Step 1.11 — Update repomap references

**File:** `docs/repomap.md`

**What:** Three lines to update:
- Line 47: `resolve_check() (2d6+stat+cond−diff→Band)` → `resolve_check() (1d12+stat+cond−diff→Band)`
- Line 79: same contract doc change
- Line 198: `(2d6 natural: 2=crit_fail, 12=crit_success)` → `(1d12 natural: 1=crit_fail, 12=crit_success)`

**Validation:** Visual check.

#### Step 1.12 — Update README references

**File:** `README.md`

**What:** Three lines:
- Line 123: `Pure-Python dice resolver (2d6 PbtA, no LLM)` → `Pure-Python dice resolver (1d12 PbtA, no LLM)`
- Line 171: `Every turn runs a **2d6 + modifier PbtA dice system**` → `Every turn runs a **1d12 + modifier PbtA dice system**`
- Line 181: `Final roll = 2d6 + (stat − 2) + difficulty_mod + condition_mod.` → `Final roll = 1d12 + (stat − 2) + difficulty_mod + condition_mod.`

**Validation:** Visual check.

### Tests to write or update

No new tests needed. The `make check` pass validates type correctness. The existing eval scenarios assert behavioral properties (band existence, roll detection) not specific dice math. No eval scenario asserts a particular dice value or raw_total.

Verification script (manual, not committed):

```python
# Verify threshold ranges cover all 12 outcomes for mods -1, 0, +1, +2
for mod in [-1, 0, 1, 2]:
    outcomes = {"cf": 0, "fail": 0, "set": 0, "part": 0, "suc": 0, "cfs": 0}
    for die in range(1, 13):
        if die == 1:
            outcomes["cf"] += 1
        elif die == 12:
            outcomes["cfs"] += 1
        else:
            ft = die + mod
            if ft <= 5:
                outcomes["fail"] += 1
            elif ft == 6:
                outcomes["set"] += 1
            elif ft <= 8:
                outcomes["part"] += 1
            else:
                outcomes["suc"] += 1
    total = sum(outcomes.values())
    assert total == 12, f"mod={mod}: total={total}"
```

### REPOMAP updates required

- `docs/repomap.md`: Update 3 references listed in Step 1.11.
- `docs/architecture/OVERVIEW.md`: Update pipeline table (Step 1.6).
- `docs/architecture/step0-ruling.md`: Update mermaid flowchart (Step 1.5).
- `README.md`: Update 3 references (Step 1.12).
