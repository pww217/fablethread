# Plan: LLM-Driven Condition Effects on Roll Difficulty

## Purpose

Replace hardcoded `CONDITION_MODS` with LLM-driven difficulty adjustment in the ruling phase, rename `impossible_reason` → `reason`, and update all downstream consumers. This plan is for implementers executing each phase step-by-step.

## Problem Statement

Conditions (`pc.conditions`) are mechanically inert for most conditions. The dice resolver has a fixed `CONDITION_MODS` dict mapping exactly 5 condition IDs to per-skill integer modifiers; any condition not in this map contributes 0 to the roll. The LLM selects difficulty blind to conditions, and the `cond_mod` is applied as invisible Python math the player never sees and the LLM never accounts for. This design was brittle at small scale and unscalable — there's no viable path to enumerate every possible condition and its effect on every skill.

## Constraints

- No new LLM call. The ruling phase already runs every turn.
- No backwards compatibility. Old CONDITION_MODS references removed entirely.
- No growth in schema complexity. Reuse existing `difficulty` field.
- Terse output. `reason` field always present, max ~10 words. The LLM explains its difficulty choice every turn.
- Conditions and inventory in scope. The ruling LLM receives both and factors both into difficulty and impossibility decisions.

## Non-goals

- Adding numeric modifier fields to IntentEnvelope or RulesOutcome. All condition and inventory effects are expressed through difficulty selection.
- Changing the extraction pipeline. Conditions continue to be added/removed by turn 2b (state extract).
- Changing the narrator or storyteller prompts. They already see conditions in their context.

## Solution

Remove `CONDITION_MODS` entirely from `ccya/rules.py`, rename `impossible_reason` → `reason` across all models and consumers, teach the ruling LLM to factor conditions/inventory into difficulty via a new prompt section, update the auto-checker that was predicated on CONDITION_MODS membership, and clean up ev.py mechanics display. The dice formula simplifies from `1d12 + stat_mod + diff_mod + cond_mod` to `1d12 + stat_mod + diff_mod`.

## Firm decisions

01. **CONDITION_MODS removed entirely.** No replacement. Clean break per design decision "Remove CONDITION_MODS entirely."
02. **impossible_reason → reason.** Always present on every ruling output, max ~10 words. Covers impossibility explanations AND difficulty choices. Per design decision "reason is always required."
03. **Conditions and inventory in scope together.** The ruling LLM receives both via the existing prompt context (already rendered) and factors both into difficulty selection per design decision "conditions and inventory in scope."
04. **No circumstance_mod field.** Rejected per design — redundant with 5-point difficulty scale.
05. **resolve_check() signature unchanged** except removing cond_mod from computation. Per design: `resolve_check()` receives skill, difficulty (already adjusted by LLM), pc_stats; no longer needs pc_conditions list for modifier calculation but the parameter stays since it's passed in turn.py and may be useful elsewhere.
06. **Auto-checker replaced entirely.** Old check_orphan_conditions checked CONDITION_MODS membership — now checks that conditions present in state appear meaningfully in ruling LLM output (reason field).

## Risks, Ambiguities, and Blockers

- **Eval runs contain cond_mod/impossible_reason fields.** Events.jsonl files from previous test runs will have stale `cond_mod` keys. These are generated artifacts — they'll be regenerated on next eval run. No migration needed; the ev.py changes handle missing keys gracefully via `.get()` with defaults.
- **Auto-checker replacement logic is fuzzy.** The new assert should check: "when conditions exist in state_snapshot, does the ruling LLM's reason field mention them?" This requires parsing natural language from `reason` — a heuristic match (substring) rather than exact matching. Severity stays yellow (warning), not red (failure).
- **HTML templates compute total_mod using cond_mod.** Three template locations need updating: index.html lines 165 and 689, _turn_log.html line 10. These are UI display calculations that must drop the `cond_mod` term from their sums.

## Status
`completed`
---

# Phases (executed)

All 4 phases completed:
- Phase 1: Schema rename + prompt update — done
- Phase 2: Python cleanup + wiring — done
- Phase 3: Eval + tooling updates — done
- Phase 4: UI template cleanup — done

---

# Phases

3 phases covering schema/prompt changes (Phase 1), Python cleanup + wiring (Phase 2), and eval/tooling updates (Phase 3). Each phase independently executable with no prior context beyond completed dependencies.

---

## Implementation — Phase 1: Schema rename + prompt update

### Context files to load
- `ccya/models.py` lines 167–194 (IntentEnvelope, RulesOutcome)
- `ccya/prompts/ruling_system.j2` full file
- `ccya/prompts/narrate_user.j2` line 75

### Detailed steps

#### Step 1.1 — Rename impossible_reason → reason in IntentEnvelope and RulesOutcome

**File:** `ccya/models.py`

**What:** In `IntentEnvelope` (line 173), rename field `impossible_reason: str = ""` to `reason: str = ""`. In `RulesOutcome` (line 193), rename field `impossible_reason: str = ""` to `reason: str = ""`.

**Why:** The design decision "rename impossible_reason → reason" requires this schema change. All downstream consumers must use the new name. This is the first step because every other phase depends on `IntentEnvelope.reason` existing instead of `ImpossibleReason`.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.models import IntentEnvelope, RulesOutcome; e = IntentEnvelope(); print(e.model_fields['reason'])"
```
Should output the reason field definition without error. No `impossible_reason` should appear in either model's schema.

#### Step 1.2 — Update ruling_system.j2: add inventory/conditions section + rename impossible_reason references

**File:** `ccya/prompts/ruling_system.j2`

**What:** Three changes to this file:
1. After the "Impossibility check" section (line 33–40), insert a new "Inventory and conditions" section with guidance text instructing the LLM to factor active conditions and inventory items into difficulty selection, always include `reason`, and handle multiple factors by netting them out.
2. Line 40: change `impossible_reason` → `reason` in the instruction sentence ("write a brief reason in `reason`").
3. Lines 51–62 (JSON schema example): add `"reason": "..."` to the schema object after `"impossible"`.
4. Line 70: rename field rule from `- \`impossible_reason\`: only when \`impossible=true\`.` to a new entry explaining `reason` is always present and explains the difficulty/impossibility choice in ≤10 words.

**Why:** Teaches the ruling LLM to factor conditions/inventory into difficulty selection per design decision "conditions and inventory in scope together." The schema update ensures the LLM emits valid JSON with the renamed field.

**Validation:**
```bash
source .venv/bin/activate && python -c "from jinja2 import Environment; env = Environment(loader=__import__('os').path.dirname('ccya/prompts/ruling_system.j2')); t = env.get_template('ruling_system.j2'); print(t.render({}))" | grep -c 'reason'
```
Should show multiple occurrences of `reason` (at least 3: schema field, instruction text, field rule).

---

## Implementation — Phase 2: Python cleanup + wiring

### Context files to load
- `ccya/rules.py` lines 1–20 (docstring), 32–38 (CONDITION_MODS dict), 133–144 (conditions_modifier function), 171–223 (resolve_check)
- `ccya/engine/turn.py` lines 715–730, 800–816, 1358–1379
- `ccya/engine/ruling.py` lines 131–166

### Detailed steps

#### Step 2.1 — Delete CONDITION_MODS dict and conditions_modifier() from rules.py; update resolve_check() formula

**File:** `ccya/rules.py`

**What:** Three changes:
1. Lines 32–38: delete the entire `CONDITION_MODS` dictionary definition (including blank line after).
2. Lines 133–144: delete the entire `conditions_modifier()` function (including preceding blank lines).
3. Line 6 (docstring): update from "Dice system: 1d12 + stat_mod + difficulty_mod + condition_mod" to "Dice system: 1d12 + stat_mod + difficulty_mod." Remove the second line about cond_mod computation.
4. Inside `resolve_check()` at line 197: delete the call `cond_mod = conditions_modifier(skill, pc_conditions)`. Delete the `pc_conditions` parameter from the function signature (line 176). This simplifies resolve_check() to not need condition data for modifier calculation — it only needs skill and difficulty which are already provided by the LLM.
5. Line 202: change `final_total = raw_total + stat_mod + diff_mod + cond_mod` to `final_total = raw_total + stat_mod + diff_mod`.
6. Lines 214–215 in the RulesOutcome construction: delete `cond_mod=cond_mod,` from the constructor call.

**Why:** Removes all CONDITION_MODS machinery per design decision "CONDITION_MODS removed entirely." The dice formula simplifies to `1d12 + stat_mod + diff_mod`. Since pc_conditions is no longer needed by resolve_check(), removing it also cleans up a parameter that was only used for the deleted modifier calculation.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.rules import CONDITION_MODS" 2>&1 | grep -i 'cannot\|no module' ; echo "---" ; source .venv/bin/activate && python -c "from ccya.rules import resolve_check; import inspect; print(inspect.signature(resolve_check))"
```
First command should error (CONDITION_MODS deleted). Second should show the new signature without `pc_conditions`.

#### Step 2.2 — Remove cond_mod field from RulesOutcome in models.py

**File:** `ccya/models.py`

**What:** Line 184: delete `cond_mod: int = 0` from `RulesOutcome` class definition.

**Why:** The design decision "Remove CONDITION_MODS entirely" includes removing the cond_mod field that was populated by resolve_check(). Since resolve_check() no longer computes it, this field is dead code.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.models import RulesOutcome; o = RulesOutcome(); print('cond_mod' in o.model_fields)"
```
Should output `False`.

#### Step 2.3 — Update turn.py: impossible_reason → reason + remove cond_mod from events

**File:** `ccya/engine/turn.py`

**What:** Four changes across three locations:
1. Line 720: change `impossible_reason=intent.impossible_reason,` to `reason=intent.reason,`.
2. Line 725: change `intent.intent_verb, intent.impossible_reason,` to `intent.intent_verb, intent.reason,`.
3. Line 811: delete the `"cond_mod": outcome.cond_mod if outcome.rolled else 0,` line from phase events dict.
4. Line 1371: delete the `"cond_mod": _outcome.cond_mod,` line from ruling_event.update() call.

**Why:** Wiring `reason` through to all consumers of the renamed field (impossible path in turn.py). Removing cond_mod from event data per design decision "Remove CONDITION_MODS entirely." Events.jsonl will no longer contain cond_mod keys on new turns.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.engine.turn import _ruling_phase; print('ok')" 2>&1 | grep -i 'cannot\|error' ; echo "---" ; source .venv/bin/activate && python -c "import ast, sys; tree = ast.parse(open('ccya/engine/turn.py').read()); [print(n.name) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_ruling_phase']"
```
First should succeed (no import errors). Second confirms the function exists.

#### Step 2.4 — Update ruling.py: replace cond_mod with reason in prompts.log output

**File:** `ccya/engine/ruling.py`

**What:** Line 150: change `lines.append(f"cond_mod:     {outcome.cond_mod}")` to `lines.append(f"reason:       {intent.reason}")`. Since `_log_ruling_outcome` receives an `IntentEnvelope` object (not a dict), access the field directly via dot notation.

**Why:** The prompts.log file should show `reason` instead of `cond_mod` for ruling outcomes. This keeps debugging output consistent with the new schema.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.engine.ruling import _log_ruling_outcome; print('ok')" 2>&1 | grep -i 'cannot\|error' ; echo "---" ; source .venv/bin/activate && python -c "import ast, sys; tree = ast.parse(open('ccya/engine/ruling.py').read()); [print(n.name) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_log_ruling_outcome']"
```

---

## Implementation — Phase 3: Eval + tooling updates

### Context files to load
- `ccya/eval/universal_asserts.py` lines 767–800 (check_orphan_conditions), line 1026 (registration)
- `scripts/debug/ev.py` lines 539, 2037, 2041, 2053, 2078

### Detailed steps

#### Step 3.1 — Replace check_orphan_conditions auto-checker with new logic

**File:** `ccya/eval/universal_asserts.py`

**What:** Lines 767–799: replace the entire `check_orphan_conditions()` function with a new implementation that checks whether conditions present in state_snapshot appear meaningfully in the ruling LLM's reason field. The logic should be:
1. Read `state_snapshot.pc.conditions` from the event (same as before).
2. If no conditions exist, pass immediately.
3. Extract condition IDs from active conditions.
4. Check if any of those IDs appear (as substrings) in the ruling LLM's reason field — but since we're removing CONDITION_MODS and the auto-checker needs to work with events.jsonl data that may contain `reason` or old `impossible_reason`, handle both gracefully via `.get()`.
5. If conditions exist AND none appear in reason → return a yellow severity warning (not red) indicating "conditions present but not mentioned in ruling reason."
6. If all conditions are mentioned OR no conditions exist → pass with detail noting the check passed.

The new function should be named `check_conditions_in_reason` to reflect its inverted purpose from the old checker. The assertion name changes from `"universal.conditions.orphan"` to `"universal.conditions.in_reason"`.

**Why:** Old auto-checker was predicated on CONDITION_MODS membership — a concept that no longer exists. New assert validates the inverse: conditions should be acknowledged by the ruling LLM via its reason field. Severity stays yellow (warning) because this is guidance, not enforcement. The substring matching approach handles natural language in `reason` without requiring exact matches.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.eval.universal_asserts import check_conditions_in_reason; print('ok')" 2>&1 | grep -i 'cannot\|error' ; echo "---" ; source .venv/bin/activate && python -c "import ast, sys; tree = ast.parse(open('ccya/eval/universal_asserts.py').read()); [print(n.name) for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]" | grep orphan
```
First should succeed. Second should show no `check_orphan_conditions` function (renamed).

#### Step 3.2 — Update auto-checker registration list

**File:** `ccya/eval/universal_asserts.py`

**What:** Line 1026: change `check_orphan_conditions(event)` to `check_conditions_in_reason(event)`.

**Why:** The function was renamed in step 3.1; the call site must match.

**Validation:**
```bash
source .venv/bin/activate && python -c "import ast, sys; tree = ast.parse(open('ccya/eval/universal_asserts.py').read()); [print(n.value.func.id) for n in ast.walk(tree) if isinstance(n, ast.Call) and hasattr(getattr(n.value, 'func', None), 'id')]" | grep -E 'orphan|conditions_in_reason'
```

#### Step 3.3 — Update ev.py: replace impossible_reason with reason + remove cond_mod from mechanics display

**File:** `scripts/debug/ev.py`

**What:** Five changes across two functions:
1. Line 539 (impossible action flag in cmd_turn): change `ruling.get('impossible_reason', '')` to `ruling.get('reason', '')`.
2. Lines 2037, 2041, 2053: In `cmd_dice()`, remove all references to `cond_mod`: delete line reading `cond_mod = ruling.get("cond_mod", 0)`, update the fallback raw_total calculation (line 2041) from `sum(dice) + (stat_mod or 0) + (diff_mod or 0) + (cond_mod or 0)` to `sum(dice) + (stat_mod or 0) + (diff_mod or 0)`, and remove `"cond_mod": cond_mod or 0,` from the rows dict.
3. Line 2078: update modifier display string from `f"stat:{r['stat_mod']:+d} diff:{r['diff_mod']:+d} cond:{r['cond_mod']:+d}"` to `f"stat:{r['stat_mod']:+d} diff:{r['diff_mod']:+d}"`.

**Why:** ev.py mechanics display tool must reflect the new schema. The impossible_reason → reason rename applies here too (debug tool reads events.jsonl). Removing cond_mod from dice calculations ensures the tool works correctly with both old data (where cond_mod may be 0) and new data (where it won't exist at all).

**Validation:**
```bash
source .venv/bin/activate && python scripts/debug/ev.py --help 2>&1 | head -3 ; echo "---" ; source .venv/bin/activate && grep -n 'cond_mod\|impossible_reason' scripts/debug/ev.py
```
Second command should produce no output (all references removed).

---

## Implementation — Phase 4: UI template cleanup

### Context files to load
- `ccya/templates/index.html` lines 165, 689
- `ccya/templates/_turn_log.html` line 10

### Detailed steps

#### Step 4.1 — Remove cond_mod from roll math calculations in HTML templates

**File:** `ccya/templates/index.html` (two locations) and `_turn_log.html` (one location)

**What:** Three changes:
1. Line 165 (`index.html`): change `{% set total_mod = (r.stat_mod or 0) + (r.diff_mod or 0) + (r.cond_mod or 0) %}` to `{% set total_mod = (r.stat_mod or 0) + (r.diff_mod or 0) %}`.
2. Line 689 (`index.html`): change `const totalMod = (payload.stat_mod || 0) + (payload.diff_mod || 0) + (payload.cond_mod || 0);` to `const totalMod = (payload.stat_mod || 0) + (payload.diff_mod || 0);`.
3. Line 10 (`_turn_log.html`): change `{% set total_mod = (r.stat_mod or 0) + (r.diff_mod or 0) + (r.cond_mod or 0) %}` to `{% set total_mod = (r.stat_mod or 0) + (r.diff_mod or 0) %}`.

**Why:** UI templates compute roll totals using cond_mod which no longer exists. Dropping the term ensures correct display of modifier sums in both Jinja-rendered and JavaScript-rendered roll badges.

**Validation:**
```bash
source .venv/bin/activate && grep -n 'cond_mod' ccya/templates/index.html ccya/templates/_turn_log.html ; echo "exit: $?"
```
Should exit with code 1 (no matches found).

---

## Tests to write or update

No tests are written during this refactor per AGENTS.md test policy. The eval harness will validate behavior on next run — specifically the new `check_conditions_in_reason` auto-checker and the corrected roll math in templates.
