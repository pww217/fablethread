# Compactor Findings — pressure_remove → unified threads migration

## Status
`open`

## Summary

The compaction system references `pressure_remove` in two places that need updating for the unified threads model. Since `scene_pressure[]` is merged into `arc.threads[]`, there is no longer a direct "remove" operation for pressures — threads are resolved and moved to `completed_threads`.

## Current References

### 1. tv.py — `_turn_viewer_data()` compaction sanitization check
**File:** `ccya/server/tv.py` line ~309-314

```python
has_sanitization = bool(san and any(
    san.get(k) for k in (
        "npc_merge", "inventory_remove",
        "pressure_remove", "condition_remove"  # ← pressure_remove is stale
    )
))
```

**Impact:** The `has_sanitization` badge on compaction cards will still work correctly — it checks if ANY of the listed keys have truthy values. Since old events may still contain `"pressure_remove": [...]`, this check won't break; it just means old compaction entries that had pressure removals will show the badge while new ones without any other sanitization won't.

**Fix:** Remove `"pressure_remove"` from the tuple (Phase 1 Step 1.2 of plan). New events won't have this key, and old events with it will simply not trigger a badge for that specific field — which is correct since pressure removal no longer exists as a concept.

### 2. _turn_viewer.html — compaction sanitization display section
**File:** `ccya/templates/_turn_viewer.html` lines ~75-76

```html
<template x-if="t.sanitization.pressure_remove && t.sanitization.pressure_remove.length">
    <div class="tv-compaction-san-row">Pressures removed: <span x-text="t.sanitization.pressure_remove.length"></span></div>
</template>
```

**Impact:** This template block will never render on new events (since compactor won't emit `pressure_remove`). On old events that have this key, it would still display — but since we're dropping the field entirely per user decision #3, remove this dead UI code.

**Fix:** Delete the entire `<template>` block (Phase 2 Step 2.2 of plan).

## What Replaces pressure_remove?

Unified threads don't have a direct "remove" operation. The lifecycle is:
1. **thread_advance** — Python increments progress by 1 on matched ArcThread
2. **thread_resolve** — Thread moved to `completed_threads` with resolution_state (resolved/failed/abandoned)
3. **Age-based demotion** — Silent threads get `active=False` after 5+ turns without being advanced

The compactor's sanitization actions track mutations that happened during compaction, not runtime lifecycle changes. Since thread resolution is a per-turn engine operation (not a compaction concern), there's no direct replacement needed for pressure_remove in the compaction context.

## Recommendation

Drop `pressure_remove` entirely from both references without adding a replacement field. The unified threads model doesn't produce compaction-level sanitization actions that correspond to old scene_pressure removals. If future compaction logic needs thread-related metrics, they should be added as new keys (e.g., `"threads_compacted_count"`) rather than retrofitting pressure semantics onto the unified model.
