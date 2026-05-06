# Plan: Post-Extraction Reconciliation

## Problem

The extractor can produce internally inconsistent deltas:
- An item added to inventory and also in the remove list
- A fact ID added that already exists verbatim
- A condition added that's already active

These arrive as valid JSON but corrupt state silently. There's no validation layer between "extractor output" and "state applied."

## Design

Add a `reconcile_delta(state, delta)` function in `ccya/state.py` that runs after extraction, before `apply_delta`. It mutates the delta in place to resolve contradictions deterministically.

```python
def reconcile_delta(state: dict, delta: dict) -> list[str]:
    """
    Validate and clean `delta` against current `state`.
    Returns a list of warning strings for logging.
    Mutates delta in place.
    """
    warnings = []

    # 1. Inventory: item in both add and remove -> drop from add
    add_ids = {i.get("id") for i in delta.get("inventory_add", [])}
    remove_ids = set(delta.get("inventory_remove", []))
    conflict = add_ids & remove_ids
    if conflict:
        delta["inventory_add"] = [i for i in delta["inventory_add"] if i.get("id") not in conflict]
        warnings.append(f"inventory conflict (add+remove same turn): {conflict}")

    # 2. Conditions: don't add a condition already active
    existing_conds = {c.get("id") for c in (state.get("pc") or {}).get("conditions") or []}
    new_conds = delta.get("pc_condition_add") or []
    dupes = [c for c in new_conds if c.get("id") in existing_conds]
    if dupes:
        delta["pc_condition_add"] = [c for c in new_conds if c.get("id") not in existing_conds]
        warnings.append(f"duplicate condition add ignored: {[c.get('id') for c in dupes]}")

    # 3. Facts: don't add a fact ID that already exists
    existing_facts = {f.get("id") for f in (state.get("scene") or {}).get("established_facts") or [] if isinstance(f, dict)}
    new_facts = delta.get("established_facts_add") or []
    dupe_facts = [f for f in new_facts if f.get("id") in existing_facts]
    if dupe_facts:
        delta["established_facts_add"] = [f for f in new_facts if f.get("id") not in existing_facts]
        warnings.append(f"duplicate fact add ignored: {[f.get('id') for f in dupe_facts]}")

    return warnings
```

### Engine integration

In `engine.py`, after extraction resolves:

```python
warnings = reconcile_delta(state, delta)
for w in warnings:
    logger.warning(f"[reconcile] turn {turn}: {w}")
apply_delta(state, delta)
```

## Notes

- Reconciliation is deterministic, not LLM-driven. It doesn't retry — it just drops the contradiction and logs it.
- Warnings surface in the debug panel so the developer can see when the extractor is producing bad deltas.
- This is a safety net, not a substitute for fixing extraction quality upstream. If the same warning fires repeatedly, it points to a prompt problem worth addressing directly.
- `recent_events` dedup (see `plans/recent-events-overhaul.md`) handles event-specific ID conflicts; this handles cross-domain state contradictions.
