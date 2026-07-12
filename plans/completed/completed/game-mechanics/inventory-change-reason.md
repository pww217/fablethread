# Inventory Change Reason

## Purpose

Force the state extraction LLM to provide a 5-7 word justification whenever it emits inventory changes, making inventory mutations auditable and reducing silent/unjustified additions/removals.

## Problem Statement

The state extraction phase (`StateExtractResult`) can silently add, remove, or update inventory items without any explanation. There's no field requiring the LLM to state why an item was acquired or lost. This makes it impossible to debug inventory issues and allows the LLM to make inventory decisions without grounding them in the narration.

## Constraints

- Only inventory changes require a reason — `inventory_update` and `pc_condition_*` are exempt.
- Single reason field covers both adds and removes in one turn.
- The field must appear first in the schema so the LLM sees it before the inventory arrays.
- `StateExtractResult` uses `model_config = {"extra": "ignore"}` — the field must be explicitly declared.
- Pydantic v2 validation errors trigger retry — a `model_validator` that raises `ValueError` will cause automatic retry.
- `StateDelta` must carry the reason through to events.jsonl persistence.
- No tests to write (tests are temporarily removed during refactor).

## Non-goals

- NPC add/remove reasons (deferred to a future phase).
- Per-add or per-remove granularity — one reason covers all inventory changes.
- Reason length enforcement beyond prompt guidance (5-7 words).
- Persisting the reason to `state.yaml` — it's an extraction artifact, not game state.

## Solution

Add `inventory_change_reason: str = ""` to `StateExtractResult` as the first field, with a `@model_validator(mode="after")` that raises `ValueError` when any inventory add/remove exists but the reason is empty. Update the system prompt to show the field first in the schema with examples. Propagate the field through `StateDelta` and the merge step so it persists in `events.jsonl`.

## Firm decisions

1. **One field, not two.** Single `inventory_change_reason` covers both adds and removes. The LLM can explain both in one sentence.
2. **Model validator, not field validator.** Uses `@model_validator(mode="after")` to check cross-field constraints (reason present iff inventory changes exist).
3. **Reason field on `StateDelta` too.** Propagated to `StateDelta` so it's visible in events.jsonl output.
4. **Reason is optional on `StateDelta`.** Default `""` — downstream code doesn't need to change.
5. **Reason goes first in `StateExtractResult`.** Pydantic preserves declaration order; LLM sees it before inventory arrays.
6. **Reason excluded from `model_dump(exclude_none=True)` in events.** Empty string serializes as `""` which is fine — it's visible in events for debugging.

## Risks, Ambiguities, and Blockers

- **Retry loop risk:** If the LLM consistently fails to produce a valid reason, it could retry indefinitely. Mitigated by the existing retry cap (`config.max_llm_retries`) and the retry prompt asking it to re-emit matching the schema.
- **Reason quality:** The validator only checks non-emptiness, not quality. The prompt guidance (examples, word count) is the quality control mechanism.
- **Schema drift:** The prompt's JSON schema example must stay in sync with the model declaration. If the prompt schema shows a field the model doesn't have, the LLM will emit it and it'll be silently ignored by `extra: "ignore"` — but the validator won't fire. The field must be in both places.

## Status
`completed`

## Phases

N/A — single phase.

## Implementation — Phase 1: Add inventory_change_reason to StateExtractResult

### Context files to load
- `ccya/models.py` — Pydantic models
- `ccya/prompts/extract_state_system.j2` — State extraction system prompt
- `ccya/engine/extraction.py` — Merge logic (lines 633-646)
- `docs/repomap.md` — Documentation update

### Detailed steps

#### Step 1.1 — Add field to `StateExtractResult`

**File:** `ccya/models.py` (lines 326-348)

**What:** Add `inventory_change_reason: str = ""` as the first field of `StateExtractResult`. Add a `@model_validator(mode="after")` that raises `ValueError("inventory_change_reason is required when inventory changes are present")` if `inventory_add` or `inventory_remove` is non-empty and `self.inventory_change_reason` is empty.

**Why:** Forces the LLM to provide a reason whenever it emits inventory changes. The validator fires after all fields are parsed, so it can cross-check reason against inventory arrays. Pydantic v2 validation errors trigger the retry mechanism in `_call_stream()`.

**Validation:** The field declaration order matters — `inventory_change_reason` must be first so Pydantic preserves it in the schema order the LLM sees.

```python
class StateExtractResult(BaseModel):
    inventory_change_reason: str = ""
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)
    inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)
    pc_condition_add: list[ConditionAdd] = Field(default_factory=list, max_length=2)
    pc_condition_remove: list[ConditionRemove] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def _validate_inventory_reason(self) -> "StateExtractResult":
        if (self.inventory_add or self.inventory_remove) and not self.inventory_change_reason:
            raise ValueError("inventory_change_reason is required when inventory changes are present")
        return self
```

Keep existing field validators unchanged.

**Validation:** `make typecheck` passes. No other code references `StateExtractResult` field order — it's only used for LLM output parsing.

#### Step 1.2 — Add field to `StateDelta`

**File:** `ccya/models.py` (lines 270-302)

**What:** Add `inventory_change_reason: str = ""` to `StateDelta` as the first field. No validator needed — `StateDelta` is constructed programmatically, not by the LLM.

**Why:** Propagates the reason through to `events.jsonl` so it's visible in turn events and the turn viewer.

**Validation:** `make typecheck` passes. `StateDelta` is constructed in `extraction.py` line 634 — the field will be passed through in the merge step.

#### Step 1.3 — Update state extraction prompt

**File:** `ccya/prompts/extract_state_system.j2`

**What:** 
1. Move `inventory_change_reason` to the first position in the JSON schema example (lines 33-39).
2. Add a "Reason field" section after the schema with:
   - "State why inventory changed this turn. Be very concise — a short phrase, not a sentence. Examples: 'Player picked up from ground', 'X NPC gave it to player', 'Player lost pistol in a brawl', 'Tool was destroyed by electric surge'"
   - "If multiple items were added or removed, explain all changes in one reason. Cover both adds and removes together."
   - "Required whenever `inventory_add` or `inventory_remove` is non-empty. Not required for `inventory_update` or `pc_condition_*` changes alone."
3. Add a "Reason field" line to the field rules section.

**Why:** The LLM needs to see the field first in the schema and understand what kind of explanation is expected. Examples ground the format. The prompt should emphasize conciseness while allowing coverage of multiple changes.

**Validation:** Read the file after editing to confirm the schema example matches the model field order.

#### Step 1.4 — Propagate reason through merge

**File:** `ccya/engine/extraction.py` (lines 633-646)

**What:** Add `inventory_change_reason=state_result.inventory_change_reason` to the `StateDelta(...)` constructor call at line 634.

**Why:** The merged delta is what gets yielded and persisted to events.jsonl. Without this, the reason is lost after parsing.

**Validation:** The field is first in `StateDelta`, so it goes first in the merged object. No downstream code reads `StateDelta.inventory_change_reason` yet — it's for observability in events.jsonl.

#### Step 1.5 — Update documentation

**File:** `docs/repomap.md`

**What:** Update the "StateExtractResult" entry in the "Extraction field routing" section (line 209) to include `inventory_change_reason`. Update the `ccya/models.py` entry to mention the new field.

**Why:** Mandatory doc update per AGENTS.md — any model field change requires repomap update.

**Validation:** The repomap entry for `StateExtractResult` should now read: `inventory_change_reason, inventory_add/remove/update, pc_condition_add/remove`.

### Tests to write or update

None — tests are temporarily removed during refactor.
