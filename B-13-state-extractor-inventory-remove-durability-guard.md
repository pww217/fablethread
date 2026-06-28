---
created: 2026-06-25
ticket_id: B-13
labels:
- state-extractor
- durability
- inventory
size: small
status: done
title: State extractor inventory_remove durability guard
urgency: 3
---


# State extractor inventory_remove durability guard

## Problem

The state extractor (LLM) can emit `inventory_remove` entries for items that don't exist in the current inventory. Currently, `_validate()` catches this as a `missing_target` rejection, which is a **blocking** rejection — it rejects the **entire delta**, including any valid changes (condition updates, NPC updates, arc updates, etc.).

The post-hoc guard in `apply_delta()` (delta_builder.py:179-185) silently skips missing targets, but that code path is never reached because `_validate()` blocks the delta first.

The prompt instructs the LLM to match items against existing inventory (extract_state_system.j2:49-56), but this is an adherence issue — the LLM ignores it, and the system over-reacts by rejecting everything.

## Current flow

```
LLM emits delta with inventory_remove for non-existent item
  -> _validate() catches missing_target (blocking)
  -> delta is NOT applied (pass at turn_state.py:451)
  -> run_turn() sees blocking rejection
  -> entire turn fails with DELTA_VALIDATION_FAILED error
  -> user sees "That action didn't resolve as expected"
```

## Desired flow

```
LLM emits delta with inventory_remove for non-existent item
  -> durability guard pre-filters invalid inventory_remove entries
  -> logs warning for each filtered entry
  -> _validate() runs on cleaned delta (no missing_target)
  -> valid delta changes are applied
  -> user sees successful turn with filtered removals in changes summary
```

## Solution

Add a durability guard function that runs **before** `_validate()` in `_apply_state_updates()`:

1. **`_filter_inventory_removes(state, delta)`** — filters `delta.inventory_remove` to remove entries for items not found in current inventory
2. Returns the cleaned delta and a list of filtered entries (for logging)
3. Called at the start of the delta application path in `_apply_state_updates()` (before line 448)

The existing `_validate()` and `apply_delta()` guards remain as defense-in-depth.

## Implementation details

### New function in `ccya/engine/turn_state.py`

```python
def _filter_inventory_removes(
    state: dict[str, Any], delta: StateDelta
) -> tuple[StateDelta, list[dict[str, Any]]]:
    """Pre-filter inventory_remove entries for non-existent items.

    Returns (cleaned_delta, filtered_entries) where filtered_entries
    contains dicts with 'id' and 'reason' for each removed entry.
    """
    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    filtered: list[dict[str, Any]] = []
    remaining: list[InventoryRemove] = []

    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            filtered.append({"id": rem.id, "reason": "Item not found in inventory"})
        else:
            remaining.append(rem)

    if not filtered:
        return delta, []

    cleaned = delta.model_copy(update={"inventory_remove": remaining})
    return cleaned, filtered
```

### Call site in `_apply_state_updates()` (turn_state.py:447)

Before the existing `_validate()` call:

```python
if delta is not None:
    # Durability guard: pre-filter invalid inventory_remove entries
    delta, filtered = _filter_inventory_removes(state, delta)
    for f in filtered:
        _log.warning(
            "inventory_remove durability guard: filtered item=%r %s",
            f["id"], f["reason"],
            extra={"trace_id": trace_id, "turn": turn_no},
        )
    rejected = _validate(state, delta)
    # ... rest unchanged
```

The filtered entries are logged but not surfaced as rejections — they are silently removed. The `summarize_changes()` UI already handles `missing_target` rejections as `failed_remove` items, but since we're filtering before validation, those won't appear. If UI visibility is desired, the filtered entries can be added to the rejected list with a different kind (e.g., `filtered_remove`).

## Files to touch

- `ccya/engine/turn_state.py` — add `_filter_inventory_removes()`, call in `_apply_state_updates()`
- `docs/architecture/step2b-extraction.md` — update delta validation section to document the durability guard

## Done when

- `_filter_inventory_removes()` is implemented and called before `_validate()`
- Invalid inventory_remove entries are pre-filtered with warning logs
- Valid delta changes still apply when only inventory_remove is invalid
- Documentation updated
