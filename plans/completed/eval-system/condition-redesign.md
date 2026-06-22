# Condition System Redesign Plan

## Purpose

Implement the condition system redesign: remove TTL-based silent expiration, add required `condition_change_reason`, show condition age in extractor prompts, add age-based removal guidance, and clarify the authority boundary between narrator and extractor.

## Problem Statement

The condition system has three interrelated problems: TTL-based silent expiration removes conditions without narrative resolution (default 10 turns), condition changes have no required reason (unlike inventory), and the authority boundary between narrator (narration) and extractor (condition/inventory tables) is implicit, creating a re-add loop where the extractor re-adds conditions the narrator references in narration.

## Constraints

- Only the extractor may add or remove conditions. No other pipeline step modifies conditions.
- TTL is removed entirely. No `turns_remaining` field. No auto-expiration pass.
- No backward compatibility for `turns_remaining` or `_DEFAULT_CONDITION_TTL`. Clean removal.
- UI changes (condition age tooltips, change lines) are out of scope — deferred.
- Positive condition granting is out of scope — leave current prompt guidance as-is.
- The `condition_change_reason` field is separate from `inventory_change_reason`.
- Condition age (computed turns since added) is displayed in the extractor prompt.
- Design doc: `docs/design/condition-redesign-design.md` is the design authority.

## Non-goals

- UI changes: tooltips, change lines, sidebar display of condition age or reasons.
- Positive condition granting improvements.
- Rolling/difficulty system changes.
- Backward compatibility for old saves with `turns_remaining` fields.
- Condition cap enforcement (the 5-condition soft cap remains prompt-only).

## Solution

Remove the TTL decrement pass and `_DEFAULT_CONDITION_TTL` constant, delete `turns_remaining` from all models, add `condition_change_reason` to `StateExtractResult` with Pydantic validation, update the retry loop to detect condition reason errors, persist `condition_change_reason` to state, update prompts to show condition age and add age-based removal guidance, add authority boundary clarification to narrator and extractor prompts, fix the prompt schema example, and clean up dead code in ev tooling.

## Firm decisions

1. Remove TTL entirely — no `turns_remaining`, no auto-expiration pass, no `_DEFAULT_CONDITION_TTL`.
2. Add `condition_change_reason: str = ""` to `StateExtractResult`, Pydantic-enforced (required when any `pc_condition_add` or `pc_condition_remove` is present).
3. Show condition age (`turn_no - c.added_turn`) in `extract_state_user.j2`.
4. Add age-based removal guidance to `extract_state_system.j2`: fresh (≤3), moderate (4-7), old (>7) with severity consideration.
5. Add authority boundary clarification to `narrate_system.j2`: condition/inventory tables are authoritative over narration.
6. Add authority boundary clarification to `extract_state_system.j2`: extractor reconciles tables against narration.
7. Fix prompt schema example in `extract_state_system.j2:64` to remove `turns_remaining` from `pc_condition_add`.
8. Update retry loop in `extraction.py:499-500` to detect `condition_change_reason` parse errors.
9. Persist `condition_change_reason` to `state.meta.last_condition_change_reason` (analogous to `last_inventory_change_reason`).
10. Clean up dead code: remove `condition_expired` check from `is_compaction_event()`, update stale comment in `audit.py`.

## Risks, Ambiguities, and Blockers

- **LLM compliance with new reason field.** The retry loop pattern has proven reliable for `inventory_change_reason`, but this is the first time it's used for conditions. Monitor compliance rate after implementation.
- **Age-based removal guidance quality.** The LLM may produce generic reasons ("condition resolved") or over/under-remove conditions. The guidance is soft (not hard rules) — evals will determine if thresholds need adjustment.
- **Narrator compliance.** Even with explicit authority boundary guidance, the narrator may have learned patterns from training that cause it to reference removed conditions. Monitor for this and strengthen guidance if needed.
- **Old saves with `turns_remaining`.** Old save files will have `turns_remaining` fields on conditions. Pydantic's `extra: "ignore"` will silently drop them on load. No migration needed.

## Status

`completed` — All 4 phases implemented. Removed TTL-based silent expiration, added required `condition_change_reason`, showed condition age in extractor prompts, added age-based removal guidance, clarified authority boundary, cleaned up dead code.

## Phases

4 phases: [models, engine, prompts, ev tooling cleanup]

---

## Implementation — Phase 1: Models

### Context files to load
- `ccya/models.py` — Condition, ConditionAdd, StateExtractResult models

### Detailed steps

#### Step 1.1 — Remove `turns_remaining` from Condition model

**File:** `ccya/models.py:78`

**What:** Delete the `turns_remaining: int | None = None` field from the `Condition` class (line 78).

**Why:** TTL is removed entirely. No conditions should have `turns_remaining`.

**Validation:** `grep -n "turns_remaining" ccya/models.py` should return 0 matches (outside of comments).

#### Step 1.2 — Remove `turns_remaining` from ConditionAdd model

**File:** `ccya/models.py:134`

**What:** Delete the `turns_remaining: int | None = None` field from the `ConditionAdd` class (line 134).

**Why:** The LLM should no longer emit `turns_remaining` — it's no longer a valid field.

**Validation:** `grep -n "turns_remaining" ccya/models.py` should return 0 matches (outside of comments).

#### Step 1.3 — Add `condition_change_reason` to StateExtractResult

**File:** `ccya/models.py:327-333`

**What:** Add `condition_change_reason: str = ""` as the first field on `StateExtractResult`, before `inventory_change_reason`.

**Why:** Required when any condition change is present. Matches the inventory pattern.

**Validation:** Field exists at line ~328, before `inventory_change_reason`.

#### Step 1.4 — Add `_validate_condition_reason` validator to StateExtractResult

**File:** `ccya/models.py:337-341` (after `_validate_inventory_reason`)

**What:** Add a new `@model_validator(mode="after")` method `_validate_condition_reason` that raises `ValueError` when any `pc_condition_add` or `pc_condition_remove` is present but `condition_change_reason` is empty.

**Why:** Pydantic-enforced requirement. The retry loop will provide targeted recovery guidance when this fires.

**Validation:** Validator exists alongside `_validate_inventory_reason`. Test: `python -c "from ccya.models import StateExtractResult; StateExtractResult(pc_condition_add=[{'id':'test','label':'test'}])"` should raise ValueError.

### Tests to write or update

- No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Implementation — Phase 2: Engine

### Context files to load
- `ccya/engine/turn.py:1065-1089` — TTL decrement pass
- `ccya/engine/turn.py:1186-1192` — Persist inventory_change_reason (reference for condition_change_reason)
- `ccya/state/delta_builder.py:21` — `_DEFAULT_CONDITION_TTL` constant
- `ccya/state/delta_builder.py:247-263` — `apply_delta()` condition application
- `ccya/engine/extraction.py:499-500` — Retry loop for missing reason

### Detailed steps

#### Step 2.1 — Delete TTL decrement pass

**File:** `ccya/engine/turn.py:1065-1089`

**What:** Delete the entire TTL decrement pass (lines 1065-1089): the comment, the loop over conditions, the `condition_expired` event emission, and the state assignment.

**Why:** TTL is removed entirely. No auto-expiration pass needed.

**Validation:** `grep -n "condition_expired\|turns_remaining" ccya/engine/turn.py` should return 0 matches (outside of comments).

#### Step 2.2 — Delete `_DEFAULT_CONDITION_TTL` constant

**File:** `ccya/state/delta_builder.py:21`

**What:** Delete the `_DEFAULT_CONDITION_TTL = 10` constant (line 21).

**Why:** No longer used. Clean removal.

**Validation:** `grep -n "_DEFAULT_CONDITION_TTL" ccya/state/delta_builder.py` should return 0 matches.

#### Step 2.3 — Remove `turns_remaining` handling from `apply_delta()`

**File:** `ccya/state/delta_builder.py:257-260`

**What:** Remove the conditional `turns_remaining` assignment in the condition add loop (lines 257-260):
```python
if ca.turns_remaining is not None:
    cond_dict["turns_remaining"] = ca.turns_remaining
else:
    cond_dict["turns_remaining"] = _DEFAULT_CONDITION_TTL
```

**Why:** `ConditionAdd` no longer has `turns_remaining`. The condition dict should not have it either.

**Validation:** Only `id`, `label`, `description`, `added_turn` should be set on `cond_dict` in `apply_delta()`.

#### Step 2.4 — Update retry loop to detect condition_change_reason errors

**File:** `ccya/engine/extraction.py:499-500`

**What:** Add a second check alongside the existing `inventory_change_reason` check:
```python
if "condition_change_reason" in parse_error and "required" in parse_error:
    _retry_hint = " You omitted the required 'condition_change_reason' field — add a one-phrase reason for why conditions changed and re-emit."
```

**Why:** The retry loop must provide targeted recovery guidance for condition reason errors, same as inventory.

**Validation:** Both checks exist. The `_retry_hint` variable is set for either error type.

#### Step 2.5 — Persist `condition_change_reason` to state

**File:** `ccya/engine/turn.py:1186-1192` (after inventory_change_reason block)

**What:** Add a parallel block to persist `condition_change_reason`:
```python
# Persist condition change reason for debugging
if delta and (delta.pc_condition_add or delta.pc_condition_remove):
    if delta.condition_change_reason:
        meta["last_condition_change_reason"] = delta.condition_change_reason
    else:
        meta.pop("last_condition_change_reason", None)
else:
    meta.pop("last_condition_change_reason", None)
```

**Why:** `condition_change_reason` must be saved to state for debugging visibility (and future UI consumption), same pattern as `last_inventory_change_reason`.

**Validation:** Both `last_inventory_change_reason` and `last_condition_change_reason` persist logic exist side by side.

### Tests to write or update

- No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Implementation — Phase 3: Prompts

### Context files to load
- `ccya/prompts/extract_state_system.j2` — State extractor system prompt
- `ccya/prompts/extract_state_user.j2` — State extractor user prompt
- `ccya/prompts/narrate_system.j2` — Narrator system prompt

### Detailed steps

#### Step 3.1 — Update condition rendering in extract_state_user.j2 to show age

**File:** `ccya/prompts/extract_state_user.j2:1-5`

**What:** Replace the condition rendering block:
```jinja2
{% if conditions -%}
## active_conditions
{% for c in conditions %}- {{ c.id if c is mapping else c }}{% if c is mapping and c.get('description') %} — {{ c.description }}{% endif %}
{% endfor %}
{% endif -%}
```
with:
```jinja2
{% if conditions -%}
## active_conditions
{% for c in conditions %}- {{ c.id if c is mapping else c }} (age: {{ turn_no - (c.added_turn if c is mapping else 0) }} turns){% if c is mapping and c.get('description') %} — {{ c.description }}{% endif %}
{% endfor %}
{% endif -%}
```

**Why:** Gives the extractor context for removal decisions: fresh conditions need narrative resolution, old conditions can heal naturally.

**Validation:** Rendered output shows condition age: `- wounded (age: 5 turns) — arm is badly hurt`.

#### Step 3.2 — Remove duration guidance for turns_remaining

**File:** `ccya/prompts/extract_state_system.j2:99-104`

**What:** Delete the duration guidance block (lines 99-104):
```
**Duration guidance for `turns_remaining`:**
- 1–2 turns: single-event sensory/physical — winded, startled, dust in eyes
- 3–4 turns: minor debuffs within an encounter — rattled, pinned, light wound
- 5–8 turns: significant injuries or ongoing effects — injured arm, frightened, smoke inhalation
- 9+: major injuries; requires explicit narrative justification
- Omit / null: permanent, irreversible effects only
```

**Why:** `turns_remaining` no longer exists. This guidance is obsolete.

**Validation:** No duration guidance for `turns_remaining` remains in the prompt.

#### Step 3.3 — Add age-based removal guidance to extract_state_system.j2

**File:** `ccya/prompts/extract_state_system.j2` (after the existing condition guidance, before stat-to-condition heuristics)

**What:** Insert the age-based removal guidance block after line 97 (after "Only add a condition if it would plausibly affect at least one future dice roll..."):
```
**Condition removal guidance — consider age AND severity:**

- Fresh conditions (≤3 turns): Only remove with explicit narrative resolution (medical attention, bandaging, rest, etc.). Do not remove fresh conditions just because the narration moved on.
- Moderate conditions (4-7 turns): Can be removed if the situation that caused them has ended and the narration has moved past them. A scrape or being dazed may heal in this window; a serious injury likely needs explicit treatment.
- Old conditions (>7 turns): Can be removed if the narration has moved past them (off-screen healing, time transition, natural recovery). Serious injuries may still need explicit resolution — use judgment based on the condition's severity.

When in doubt, prefer removal over accumulation. If a condition hasn't been mentioned in recent narration and the situation that caused it is gone, it's likely resolved.
```

**Why:** Gives the extractor concrete bands for removal decisions while acknowledging severity matters.

**Validation:** Block exists between the condition add guidance and the stat-to-condition heuristics.

#### Step 3.4 — Fix prompt schema example to remove turns_remaining

**File:** `ccya/prompts/extract_state_system.j2:64`

**What:** Replace the schema example's `pc_condition_add` entry:
```json
"pc_condition_add": [{"id": "...", "label": "...", "description": "...", "turns_remaining": 3}]
```
with:
```json
"pc_condition_add": [{"id": "...", "label": "...", "description": "..."}]
```

**Why:** The LLM will continue emitting `turns_remaining` if it's in the schema example, even though it's no longer a valid field.

**Validation:** Schema example no longer includes `turns_remaining`.

#### Step 3.5 — Update reason field section for conditions

**File:** `ccya/prompts/extract_state_system.j2:68-74`

**What:** Update the reason field section to add condition_change_reason guidance:
```
## Reason fields — REQUIRED

`inventory_change_reason` is the anchor for inventory changes. You must decide whether inventory changed BEFORE you populate any other fields.

- If inventory changed (any of `inventory_add`, `inventory_remove`, `inventory_update` is non-empty): `inventory_change_reason` is REQUIRED. State why inventory changed this turn in one short phrase. Examples: "Player picked up from ground", "X NPC gave it to player", "Player lost pistol in a brawl". Multiple items → one reason covering all changes.
- If inventory did NOT change: `inventory_change_reason: "none"`. Omit all inventory fields.

`condition_change_reason` is the anchor for condition changes. You must decide whether conditions changed BEFORE you populate any other fields.

- If conditions changed (any of `pc_condition_add`, `pc_condition_remove` is non-empty): `condition_change_reason` is REQUIRED. State why conditions changed this turn in one short phrase. Examples: "Player received medical attention", "Injury healed after rest", "PC took a head wound". One reason covering all condition changes this turn.
- If conditions did NOT change: `condition_change_reason: "none"`. Omit all condition fields.
```

**Why:** The LLM needs clear guidance that `condition_change_reason` is required when conditions change, matching the inventory pattern.

**Validation:** Both reason fields are documented with required/optional guidance.

#### Step 3.6 — Add authority boundary clarification to extract_state_system.j2

**File:** `ccya/prompts/extract_state_system.j2` (after line 1, before "## STEP 0")

**What:** Insert authority clarification:
```
The extractor's job is to reconcile the condition and inventory tables against the current turn's narration. The tables define the current state; the narration defines what happened this turn. Decide what the final state should be by comparing the tables against the narration. The extractor is authoritative on the tables — it decides what changes to make. The narrator is authoritative on narration — it writes fiction but must respect the tables.
```

**Why:** Clarifies the extractor's role: it's actively reconciling tables against narration, not passively reading narration.

**Validation:** Authority clarification exists at the top of the prompt, before STEP 0.

#### Step 3.7 — Add authority boundary clarification to narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2` (after line 5, or integrated into the existing conditions mention)

**What:** Replace line 5:
```
Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.
```
with:
```
Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

The condition table and inventory table provided in the prompt are the authoritative source of truth for what the player has and what conditions they have. Do not narrate the player having or not having an inventory item or condition that is not listed in those tables. If a condition was removed from the table, do not narrate it persisting even if it was mentioned in prior narration. If an inventory item was removed, do not narrate the player using or referencing it.
```

**Why:** Fixes the re-add loop. The narrator must respect the mechanical state provided by the engine, not invent or deny conditions/items in narration.

**Validation:** Authority boundary guidance exists after line 5. Narrator sees conditions as authoritative over its own narration.

### Tests to write or update

- No tests to write (tests are temporarily removed during refactor per AGENTS.md).
- Manual validation: render prompts with sample data to verify condition age display and authority guidance are present.

---

## Implementation — Phase 4: Ev Tooling Cleanup

### Context files to load
- `ccya/ev/events.py:357-373` — `is_compaction_event()` function
- `ccya/ev/audit.py:22-26` — Comment referencing condition_expired

### Detailed steps

#### Step 4.1 — Remove `condition_expired` check from `is_compaction_event()`

**File:** `ccya/ev/events.py:365-366`

**What:** Delete the `condition_expired` check:
```python
if kind == "condition_expired":
    return True
```

**Why:** `condition_expired` events are no longer emitted. This is dead code.

**Validation:** `grep -n "condition_expired" ccya/ev/events.py` should return 0 matches.

#### Step 4.2 — Update `is_compaction_event()` docstring

**File:** `ccya/ev/events.py:358-362`

**What:** Update the docstring to remove the `condition_expired` reference:
```python
"""Detect compaction events (sanitizer with empty ruling, etc.).

Compaction events are events that don't represent a full turn in the pipeline.
They include sanitizer events with empty ruling,
and any event where ruling is empty and tokens_in is 0.
"""
```

**Why:** Docstring should match current behavior.

**Validation:** Docstring no longer references `condition_expired`.

#### Step 4.3 — Update stale comment in audit.py

**File:** `ccya/ev/audit.py:23`

**What:** Update the comment:
```python
# Skip side events (condition_expired, sanitizer, etc.) — they have
```
to:
```python
# Skip side events (sanitizer, etc.) — they have
```

**Why:** Comment is misleading — `condition_expired` events no longer exist.

**Validation:** Comment no longer references `condition_expired`.

### Tests to write or update

- No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Documentation updates required

- `docs/repomap.md:327-328` — Update condition shape: remove `turns_remaining` from the `pc.conditions` data shape description.
- `docs/repomap.md:360` — Update `DEFAULT_CONDITION_TTL` constant reference (remove it).
- `docs/repomap.md:376` — Note that `condition_change_reason` follows the same pattern as `inventory_change_reason` for state persistence.
- `docs/architecture/` — Update pipeline flow docs if they reference the TTL decrement pass or `condition_expired` events.
