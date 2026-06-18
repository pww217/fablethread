# Condition System Redesign

## Purpose

Redesign the condition system to remove TTL-based silent expiration, add required change reasons, and clarify the authority boundary between narrator (narration) and extractor (condition/inventory tables). This document is the design authority for plans implementing this redesign.

## Problem Statement

The condition system has three interrelated problems:

1. **TTL-based silent expiration.** Conditions auto-expire when `turns_remaining` hits 0 (default 10 turns). This removes conditions without narrative resolution, making the game easier than intended. Players don't get to experience the consequences of conditions — they just vanish.

2. **No change reason for conditions.** Inventory changes require `inventory_change_reason` (Pydantic-enforced). Condition changes have no equivalent — the LLM can add or remove conditions silently without explaining why. This makes debugging extraction decisions difficult and gives the LLM no incentive to reason about condition changes.

3. **Authority boundary confusion.** The narrator sees conditions in its prompt but has no explicit instruction that the condition table is authoritative over its own narration. This creates a loop: the extractor removes a condition, the narrator's narration still references it (from prior context), the extractor sees the narration and re-adds the condition. The extractor and narrator have opposite responsibilities — the extractor is authoritative on condition/inventory tables (respecting narration), while the narrator is authoritative on narration (respecting condition/inventory tables) — but this boundary is not enforced in prompts.

## Constraints

- Only the extractor may add or remove conditions. No other pipeline step modifies conditions.
- TTL is removed entirely. No `turns_remaining` field. No auto-expiration pass.
- No backward compatibility for `turns_remaining` or `_DEFAULT_CONDITION_TTL`. Clean removal.
- UI changes (condition age tooltips, change lines) are out of scope — deferred to a separate effort.
- Positive condition granting is out of scope — leave current prompt guidance as-is.
- The `condition_change_reason` field is separate from `inventory_change_reason`, not combined.
- Condition age (computed turns since added) is displayed in the extractor prompt to inform removal decisions.

## Non-goals

- UI changes: tooltips, change lines, sidebar display of condition age or reasons.
- Positive condition granting improvements.
- Rolling/difficulty system changes (though conditions affect difficulty, the difficulty calculation itself is unchanged).
- Backward compatibility for old saves with `turns_remaining` fields.
- Condition cap enforcement (the 5-condition soft cap remains prompt-only, as it is today).

## Decision Table

| Decision | What | Why |
|---|---|---|
| Remove TTL entirely | Delete `_DEFAULT_CONDITION_TTL`, the TTL decrement pass in `turn.py`, and `turns_remaining` from all models. | Silent expiration makes the game too easy. Conditions should persist until narratively resolved or explicitly removed by the extractor. |
| Add `condition_change_reason` | New field on `StateExtractResult`, Pydantic-enforced (required when any `pc_condition_add` or `pc_condition_remove` is present). Separate from `inventory_change_reason`. | Matches the inventory pattern. Forces the LLM to reason about condition changes. Provides debugging visibility. Separate field preserves granularity for future UI display. |
| Condition table is authoritative over narrator | Add explicit guidance to `narrate_system.j2`: the condition table in the prompt is the source of truth. If a condition is not listed, do not narrate it persisting. | Fixes the re-add loop. The narrator writes fiction but must respect the mechanical state provided by the engine. |
| Extractor is authoritative over condition/inventory tables | Add explicit guidance to `extract_state_system.j2`: the extractor reconciles the condition/inventory tables against the narration. It decides what the final state should be. | Clarifies the extractor's role: it is not passively reading narration — it is actively reconciling tables against narration to produce the correct final state. |
| Show condition age in extractor prompt | Display computed age (current turn - `added_turn`) for each condition in `extract_state_user.j2`. | Gives the extractor context for removal decisions: fresh conditions need narrative resolution to remove; old conditions can heal naturally. |
| Age-based removal guidance | Prompt guidance: conditions >5 turns old can be removed if narration has moved past them (off-screen healing, time transition). Fresh conditions (≤3 turns) require explicit narrative resolution (medical attention, bandaging, etc.). | Makes the game harder for fresh conditions while allowing natural decay for long-standing ones. Balances difficulty with realism. |

## Open Questions

- [OPEN: Should the age-based removal guidance have a specific turn threshold for "old" conditions? Proposed: >5 turns for removal consideration, >10 turns for automatic removal if narration has moved on. Should this be a hard rule or soft guidance?]

## Current State — What Exists

### Condition Model

**`ccya/models.py:73-78`** — `Condition` model:
```
id: str
label: str
description: str = ""
added_turn: int = 0
turns_remaining: int | None = None
```

**`ccya/models.py:130-148`** — `ConditionAdd` (with `turns_remaining`) and `ConditionRemove` (id only).

**`ccya/models.py:327-356`** — `StateExtractResult` with `pc_condition_add` (max 2) and `pc_condition_remove`. No reason field for conditions.

### TTL Decrement Pass

**`ccya/engine/turn.py:1065-1089`** — Runs every turn post-extraction:
- Iterates all conditions with `turns_remaining` not None
- Decrements by 1
- Removes when reaching 0, logs `condition_expired` event
- `None` = permanent (never expires)

### Default TTL

**`ccya/state/delta_builder.py:21`** — `_DEFAULT_CONDITION_TTL = 10`. Applied when `turns_remaining` is None on a `ConditionAdd`.

### Condition Application

**`ccya/state/delta_builder.py:236-263`** — `apply_delta()`:
- Deduplicates by condition ID
- Removes conditions matching `pc_condition_remove` IDs
- Adds new conditions from `pc_condition_add`, setting `added_turn` to current turn
- Sets `turns_remaining` to provided value or `_DEFAULT_CONDITION_TTL`

### Prompt Guidance

**`ccya/prompts/extract_state_system.j2:93-112`** — Duration guidance for `turns_remaining` (1-2, 3-4, 5-8, 9+, null for permanent). Stat-to-condition heuristics including positive conditions on decisive/critical success.

**`ccya/prompts/extract_state_user.j2:1-5`** — Renders current conditions for the extractor. Only shows `id` and `description`. No age information.

**`ccya/prompts/narrate_user.j2:6`** — Renders conditions as comma-separated list in the Player Character section.

**`ccya/prompts/narrate_system.j2:5`** — "The rules engine handles dice and conditions; the narrator handles fiction." No explicit authority boundary about the condition table being authoritative.

### Authority Boundary

The extractor sees conditions in the user prompt and the current turn's narration. It decides what to add/remove. The narrator sees conditions in its prompt (from previous turn's state) and writes narration. There is no explicit instruction that either party's output is authoritative over the other's domain. This creates the re-add loop: narrator references a removed condition in narration → extractor sees it in narration → extractor re-adds it.

### Inventory Reason Pattern (Reference)

**`ccya/models.py:328, 337-341`** — `inventory_change_reason` is required when any inventory change is present, enforced by a Pydantic model validator. The retry loop in `extraction.py:499-500` provides targeted recovery guidance when the reason is missing.

### Problems with Current State

- **TTL causes silent removal.** Conditions vanish at turn 10 (default) without narrative resolution. The `condition_expired` event is logged but not surfaced to the player or narrator.
- **No condition change reason.** Unlike inventory, condition changes have no required reason. The LLM can add/remove silently.
- **Authority boundary is implicit.** `narrate_system.j2:5` mentions conditions but doesn't establish the condition table as authoritative over narration. The extractor has no explicit instruction that it is reconciling tables against narration.
- **No age visibility for the extractor.** The extractor sees condition IDs and descriptions but not how long they've been active. Cannot make informed removal decisions based on condition age.
- **`turns_remaining` on `ConditionAdd` is misleading.** It suggests the LLM should set durations, but the real mechanism (TTL decrement) is hidden from the LLM's view. The LLM doesn't understand what happens when TTL hits 0.

## Proposed Solution

### Core Changes

#### 1. Remove TTL entirely

Delete the TTL decrement pass from `ccya/engine/turn.py:1065-1089`. Delete `_DEFAULT_CONDITION_TTL` from `ccya/state/delta_builder.py:21`. Remove `turns_remaining` from `Condition`, `ConditionAdd`, and the prompt schema example.

Conditions persist indefinitely until the extractor explicitly removes them via `pc_condition_remove`.

#### 2. Add `condition_change_reason` field

Add `condition_change_reason: str = ""` to `StateExtractResult` in `ccya/models.py`. Add a Pydantic model validator (analogous to `_validate_inventory_reason`) that raises `ValueError` when any `pc_condition_add` or `pc_condition_remove` is present but `condition_change_reason` is empty.

Update the retry loop in `ccya/engine/extraction.py:499-500` to detect `condition_change_reason` parse errors (same pattern as the existing `inventory_change_reason` check) and provide targeted retry guidance: "You omitted the required 'condition_change_reason' field — add a one-phrase reason for why conditions changed and re-emit."

Persist `condition_change_reason` to `state.meta.last_condition_change_reason` in `ccya/engine/turn.py` (analogous to `last_inventory_change_reason` at lines 1186-1192) for debugging visibility.

#### 3. Show condition age in extractor prompt

Update `ccya/prompts/extract_state_user.j2` to display computed age for each condition:

```
## active_conditions
{% for c in conditions %}- {{ c.id }} (age: {{ turn_no - c.added_turn }} turns) — {{ c.description }}
{% endfor %}
```

This gives the extractor context: a condition that's 15 turns old and hasn't been mentioned in recent narration is a candidate for natural healing.

#### 4. Add age-based removal guidance to extractor prompt

Update `ccya/prompts/extract_state_system.j2` with removal guidance:

```
**Condition removal guidance — consider age AND severity:**

- Fresh conditions (≤3 turns): Only remove with explicit narrative resolution (medical attention, bandaging, rest, etc.). Do not remove fresh conditions just because the narration moved on.
- Moderate conditions (4-7 turns): Can be removed if the situation that caused them has ended and the narration has moved past them. A scrape or being dazed may heal in this window; a serious injury likely needs explicit treatment.
- Old conditions (>7 turns): Can be removed if the narration has moved past them (off-screen healing, time transition, natural recovery). Serious injuries may still need explicit resolution — use judgment based on the condition's severity.

When in doubt, prefer removal over accumulation. If a condition hasn't been mentioned in recent narration and the situation that caused it is gone, it's likely resolved.
```

#### 5. Clarify authority boundary in narrator prompt

Update `ccya/prompts/narrate_system.j2` to add explicit guidance:

"The condition table and inventory table provided in the prompt are the authoritative source of truth for what the player has and what conditions they have. Do not narrate the player having or not having an inventory item or condition that is not listed in those tables. If a condition was removed from the table, do not narrate it persisting even if it was mentioned in prior narration. If an inventory item was removed, do not narrate the player using or referencing it."

#### 6. Clarify extractor's reconciliation role

Update `ccya/prompts/extract_state_system.j2` to clarify the extractor's role:

"The extractor's job is to reconcile the condition and inventory tables against the current turn's narration. The tables define the current state; the narration defines what happened this turn. Decide what the final state should be by comparing the tables against the narration. The extractor is authoritative on the tables — it decides what changes to make. The narrator is authoritative on narration — it writes fiction but must respect the tables."

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Raise default TTL to 20-30 turns | Keeps the silent expiration mechanism. The user explicitly wants conditions to persist until narratively resolved, not just for longer. |
| Combined `state_change_reason` for inventory + conditions | Loses granularity. The user wants separate reasons for independent UI display. Inventory and conditions have different semantic domains. |
| Keep `turns_remaining` for backward compatibility | The user explicitly said no backward compatibility. Old saves with `turns_remaining` will have the field ignored (extra fields are ignored by Pydantic's `model_config`). |
| Hard rule: auto-remove conditions >N turns | Too rigid. The user wants the extractor to decide based on narration context, not a fixed threshold. |

## Failure Modes and Risks

- **Extractor may over-remove old conditions.** Without TTL, the extractor might remove conditions too eagerly when it sees they're old. The age-based removal guidance mitigates this by requiring narration context (condition must have moved past).
- **Extractor may under-remove conditions.** Conversely, the extractor might keep conditions indefinitely if it's too conservative. The removal guidance should address this by explicitly encouraging removal of old conditions when narration has moved on.
- **Narrator may still reference removed conditions.** Even with explicit guidance, the narrator may have learned patterns from training that cause it to reference removed conditions. Monitor for this and strengthen guidance if needed.
- **Condition accumulation.** Without TTL, conditions could accumulate over many turns. The 5-condition soft cap (prompt-only) and the "prefer removal over accumulation" guidance should mitigate this.
- **Reason field quality.** The LLM may produce low-quality or generic reasons ("condition resolved"). The retry loop should provide targeted guidance if the reason is too vague.
- **Ev tooling cleanup.** Removing `condition_expired` events leaves dead code in `ccya/ev/events.py:365` (`is_compaction_event()` check) and a stale comment in `ccya/ev/audit.py:23`. These should be cleaned up in the same commit.
- **Prompt schema mismatch.** The JSON schema example in `extract_state_system.j2:64` includes `turns_remaining` in the `pc_condition_add` example. This must be updated to match the new model shape, or the LLM will continue emitting `turns_remaining` even though it's no longer a valid field.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `_DEFAULT_CONDITION_TTL` | `ccya/state/delta_builder.py:21` | Deleted with no replacement |
| `turns_remaining` field | `ccya/models.py:78` (Condition), `ccya/models.py:134` (ConditionAdd) | Deleted with no replacement |
| TTL decrement pass | `ccya/engine/turn.py:1065-1089` | Deleted with no replacement |
| `condition_expired` event | `ccya/engine/turn.py:1075-1084` | No longer emitted (conditions don't auto-expire) |
| Duration guidance for `turns_remaining` | `ccya/prompts/extract_state_system.j2:99-104` | Replaced with age-based removal guidance |
| `condition_expired` event kind | Events | No longer emitted |
| `condition_expired` check | `ccya/ev/events.py:365` | Dead code — `is_compaction_event()` no longer needs this check |
| `turns_remaining` handling | `ccya/state/delta_builder.py:257-260` | Remove conditional TTL assignment in `apply_delta()` |

## What Is Unchanged

- **Condition model structure** — `id`, `label`, `description`, `added_turn` remain. Only `turns_remaining` is removed.
- **ConditionAdd/ConditionRemove models** — Only `turns_remaining` is removed from `ConditionAdd`. `ConditionRemove` is unchanged.
- **Condition coercion helpers** — `_coerce_condition_str`, `_coerce_condition_add_item`, `_coerce_condition_remove_item` remain unchanged (they don't reference `turns_remaining`).
- **Condition deduplication** — ID-based dedup in `delta_builder.py` remains unchanged.
- **5-condition soft cap** — Prompt-only enforcement remains unchanged.
- **Ruling step** — Conditions are still factored into difficulty via `ruling_system.j2:44-46`. Unchanged.
- **Narrator prompt rendering** — `narrate_user.j2:6` still renders conditions (format may change slightly with age display, but the concept is unchanged).
- **Storyteller prompt** — `storytell_user.j2:5-9` still renders conditions. Unchanged.
- **Positive condition guidance** — `extract_state_system.j2:110-111` remains as-is (out of scope).
- **Inventory system** — `inventory_change_reason`, inventory models, inventory delta application all unchanged. Only the new `condition_change_reason` is added alongside it.
- **Delta reconciliation** — `reconcile_delta()` in `delta_builder.py` remains unchanged (condition dedup logic). Only the `turns_remaining` assignment in `apply_delta()` is removed.
- **UI templates** — `_state_right.html` condition rendering is out of scope (deferred). However, `condition_change_reason` should be persisted to state (like `inventory_change_reason`) for future UI consumption.
- **Ev tooling** — `is_compaction_event()` in `events.py:365` will have a dead code path for `condition_expired` check. The audit.py comment at line 23 referencing `condition_expired` becomes stale but the skip logic (`if ev.get("kind")`) still works correctly.

## New Model Shapes

### StateExtractResult (modified)

```
condition_change_reason: str = ""
inventory_change_reason: str = ""
inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
inventory_remove: list[InventoryRemove] = Field(default_factory=list)
inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)
pc_condition_add: list[ConditionAdd] = Field(default_factory=list, max_length=2)
pc_condition_remove: list[ConditionRemove] = Field(default_factory=list)
```

### Condition (modified)

```
id: str
label: str
description: str = ""
added_turn: int = 0
```

### ConditionAdd (modified)

```
id: str
label: str
description: str = ""
```

### New validator on StateExtractResult

```python
@model_validator(mode="after")
def _validate_condition_reason(self) -> "StateExtractResult":
    if (self.pc_condition_add or self.pc_condition_remove) and not self.condition_change_reason:
        raise ValueError("condition_change_reason is required when condition changes are present")
    return self
```

## Context for Implementing LLMs

| File | What it contains | Why it matters |
|---|---|---|
| `ccya/models.py:73-148` | Condition, ConditionAdd, ConditionRemove models | Remove `turns_remaining`, add `condition_change_reason` to StateExtractResult |
| `ccya/models.py:327-356` | StateExtractResult with inventory/condition fields | Add new field and validator |
| `ccya/engine/turn.py:1065-1089` | TTL decrement pass | Delete this entire pass |
| `ccya/state/delta_builder.py:21` | `_DEFAULT_CONDITION_TTL` constant | Delete this constant |
| `ccya/state/delta_builder.py:236-263` | `apply_delta()` condition application | Remove `turns_remaining` handling |
| `ccya/prompts/extract_state_system.j2` | State extractor system prompt | Add age-based removal guidance, clarify authority boundary, remove duration guidance |
| `ccya/prompts/extract_state_user.j2` | State extractor user prompt | Add age display for conditions |
| `ccya/prompts/narrate_system.j2` | Narrator system prompt | Add authority boundary guidance (condition/inventory tables are authoritative) |
| `ccya/engine/extraction.py:499-500` | Retry loop for missing inventory reason | Must be updated to also detect condition_change_reason parse errors |
| `ccya/engine/turn.py:1186-1192` | Persist inventory_change_reason to state | Same pattern for persisting condition_change_reason |
| `ccya/ev/events.py:365` | is_compaction_event() checks for condition_expired | Dead code path — should be removed |
| `ccya/prompts/extract_state_system.j2:64` | JSON schema example includes turns_remaining | Must be updated to remove turns_remaining from pc_condition_add example |
