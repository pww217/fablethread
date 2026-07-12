# Fuzzy inventory_remove with silent cancellation

## Status
`completed`

## Phases

1 phase: Add fuzzy matching as final fallback in `resolve_inventory_remove_target()`, suppress rejections for non-existent items (DEBUG log only).

## Issue

When the state extractor produces `inventory_remove` for an item the player doesn't have, the system generates a rejection record with `kind: "warn_missing_item"` that appears in the UI with a "rejected" badge. This is noisy and unhelpful — the extractor often hallucinates removals for items that were mentioned in narration but never added to inventory, or uses names that don't match exactly. There's no fuzzy matching in the remove path, so near-misses also get rejected.

## Solution

Add `_fuzzy_match_inventory()` as a final fallback in `resolve_inventory_remove_target()` (threshold 0.6, same as inventory_add). When no match is found at any stage (canonical → name → fuzzy), suppress the rejection record entirely and log at DEBUG level instead. The player never sees UI noise for attempted removals of items they don't have.

## Firm decisions

1. Fuzzy match threshold is 0.6 — consistent with existing `inventory_add` duplicate detection.
2. Fuzzy match is added inside `resolve_inventory_remove_target()` — single resolution function, no scattered logic.
3. Non-existent item removals produce no rejection record, no UI badge — DEBUG log only.
4. No changes to `inventory_add` fuzzy matching — it already works.
5. No backward compatibility or migration.

## Non-goals

- Changing the durability gate (that's roadmap item 3, separate).
- Adding new model fields or config keys.
- Rewriting the extraction prompt to prevent hallucinated removes.
- Changing `inventory_add` behavior.

## Risks, Ambiguities, and Blockers

- **Fuzzy match false positives:** Threshold 0.6 could match unrelated items with common tokens (e.g., "key" matching "skeleton key"). This is the same risk as `inventory_add` — acceptable tradeoff. If it becomes a problem, raise threshold later.
- **`_fuzzy_match_inventory` is private:** It's prefixed with underscore but used within the same module. Moving it to `resolve_inventory_remove_target` keeps it internal — no API change.

## Implementation — Phase 1: Fuzzy remove with silent cancellation

### Context files to load

- `ccya/state/inventory.py` (full file — 102 lines)
- `ccya/engine/turn.py` (lines 1737-1791 — `_validate` function)
- `ccya/state/delta_builder.py` (lines 192-199 — `apply_delta` inventory_remove loop)

### Detailed steps

#### Step 1.1 — Add fuzzy fallback to `resolve_inventory_remove_target()`

**File:** `ccya/state/inventory.py`, function `resolve_inventory_remove_target()` (lines 57-68)

**What:** After the name fallback loop (line 67) and before `return None`, add a call to `_fuzzy_match_inventory(raw_id, inventory)`. If it returns a match, return that canonical ID.

Also update the module docstring (lines 13-16): change "matches against item names (fallback for items without aliases)" to "matches against item names, then falls back to fuzzy token-overlap matching (threshold 0.6)". Change "detecting duplicates during inventory_add" to "detecting duplicates during inventory_add and as a fallback for inventory_remove".

**Why:** Gives the remove path the same fuzzy matching capability as the add path. Near-miss names like "iron coin" → "iron_coins" resolve correctly instead of being rejected.

**Validation:** `make check` passes. `_fuzzy_match_inventory` is already defined in the same file at line 71 — no import changes.

#### Step 1.2 — Suppress rejection for non-existent items in `_validate()`

**File:** `ccya/engine/turn.py`, function `_validate()` (lines 1737-1791)

**What:** Replace the rejection block for `canonical is None` (lines 1746-1754) with a DEBUG log and `continue`. Remove the rejection dict append:

```python
for rem in delta.inventory_remove:
    canonical = resolve_inventory_remove_target(inv_list, rem.id)
    if canonical is None:
        _log.debug(
            "inventory_remove target %r not found in inventory (turn %s) — skipping",
            rem.id, state.get("meta", {}).get("turn", 0),
        )
        continue
    # ... rest of validation unchanged
```

**Why:** When no match is found (canonical → name → fuzzy), the item doesn't exist. No rejection record needed — the extractor hallucinated or referenced something not in inventory. Player shouldn't see a "rejected" badge for this.

**Validation:** `make check` passes. Run a turn where extractor tries to remove a non-existent item — no rejection appears in UI, DEBUG log entry exists.

#### Step 1.3 — Downgrade WARNING to DEBUG in `apply_delta()`

**File:** `ccya/state/delta_builder.py`, function `apply_delta()` (lines 192-199)

**What:** Change the `_log.warning()` call to `_log.debug()` for the case where `canonical` is `None`:

```python
for rem in delta.inventory_remove:
    canonical = resolve_inventory_remove_target(inv, rem.id)
    if not canonical:
        _log.debug(
            "inventory_remove target %r not found in inventory (turn %s)",
            rem.id, state.get("meta", {}).get("turn", 0),
        )
        continue
```

**Why:** Consistent with Step 1.2 — non-existent item removals are not errors, they're expected noise from the extractor. WARNING level is too loud.

**Validation:** `make check` passes. No WARNING log for non-existent item removals.

### Tests to write or updated

No tests to write or update (tests are temporarily removed during refactor).

### REPOMAP updates required

- `docs/repomap.md` — update `resolve_inventory_remove_target()` description to note it now uses fuzzy matching as final fallback (threshold 0.6)
- Note that non-existent item removals produce no rejection — DEBUG log only
