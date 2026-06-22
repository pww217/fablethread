# Fix: B1 + MB-5 + B3

> **Plan review status:** `request changes` — B1 scope understated, MB-5
> insertion point slightly off, B3 hypothesis stale (archival mechanism already
> exists). Fixes applied below. [QUESTION: B3] remains for user input.
>
> See [REVIEW-fix-b1-mb5-b3.md](REVIEW-fix-b1-mb5-b3.md) for full findings.

---

## B1 — Inventory decrement silently dropped

**Root cause:** `extract_state_system.j2` line 44 tells LLM to use `inventory_update` for amount changes, but `InventoryUpdate` model (`models.py:231-234`) has no `amount` field. Pydantic silently drops the key. `delta_builder.py:203-211` never patches amount on update.

**Fix — two prompt changes:**

1. **Line 44** — Remove "amount changes" from `inventory_update` description:
   - Before: `inventory_update: patches to existing items — amount changes, name changes, notes updates, damage, upgrades. name and notes are optional within an update entry.`
   - After: `inventory_update: patches to existing items — name changes, notes updates, damage, upgrades. name and notes are optional within an update entry. Does not support amount changes — use inventory_remove instead.`

2. **Line 46** — Clarify `inventory_remove` supports partial amount:
   - Before: `inventory_remove: items lost, used up, destroyed, or spent. Omit amount to remove the entire stack.`
   - After: `inventory_remove: items lost, used up, destroyed, or spent. Set amount to the count consumed (e.g. "amount": 1 for pistol_rounds). Omit amount to remove the entire stack.`

3. **Line 52** — Change `inventory_update` to `inventory_add` for ammo additions:
   - Before: `If compatible ammo already exists in inventory, use inventory_update instead.`
   - After: `If compatible ammo already exists in inventory, use inventory_add — it merges with the existing stack.`

**Risk:** Low — LLM already computes the delta, just emits wrong operation name.
No code changes.

---

## MB-5 — Pressure counter reads pre-floor-relief beat

**Root cause:** `turn.py:1291-1294` reads `storyteller_result.gm_beat.type` (raw
LLM output) instead of the stored `pending_gm_beat` type (which may have been
overridden by floor relief). Counter continues climbing through breathing_room
injections.

**Fix:** Move pressure counter logic after floor relief injection. Read from
`state["meta"]["pending_gm_beat"]` instead of `storyteller_result.gm_beat.type`.

**Exact changes to `ccya/engine/turn.py`:**

1. **Delete** lines 1289-1301 (the old pressure counter block at end of function).

2. **Insert** after line 1073 (end of floor relief injection, before `if is_cancel_requested`), inside the existing `if _extract_result is not None` guard:

```python
            # Consecutive pressure counter: reads post-floor-relief pending_gm_beat
            _current_beat = state.get("meta", {}).get("pending_gm_beat")
            _beat_type = _current_beat.get("type") if _current_beat else None
            meta = state.setdefault("meta", {})
            current_pressure = meta.get("consecutive_pressure_turns", 0)
            if _beat_type in PRESSURE_BEAT_TYPES:
                meta["consecutive_pressure_turns"] = current_pressure + 1
            else:
                meta["consecutive_pressure_turns"] = 0
```

**Why this insertion point works:**
- Line 1055-1072: storyteller beat written + floor relief override applied
- Line 1073: `state["meta"]["pending_gm_beat"]` now has the correct (potentially
  overridden) beat type
- Lines 1074+: cancel check, phase yield, condition age pass (state not touched
  by counter logic here)
- Lines 1133-1158: `apply_delta` runs — doesn't touch `consecutive_pressure_turns`
- Lines 1167-1178: beat history append — uses the same corrected beat source

**Risk:** Low — logic identical, just different data source and earlier timing.

---

## B3 — Resolved threads not recorded as completed

**Root cause investigation needed — hand edit from review:**

Source inspection reveals that BOTH archival mechanisms already exist:

- **Main pipeline** (`turn.py:331-420`): `_apply_thread_resolutions()` moves
  resolved threads from `threads[]` to `completed_threads[]` with `resolution_state`
- **Sanitizer** (`thread_sanitizer.py:410-448`): moves resolved threads into
  `completed_threads[]` with proper archival
- **Sanitizer removed_threads** (`thread_sanitizer.py:453-464`): **DESTROYS**
  threads from BOTH lists without archival — this is the likely candidate

The `removed_threads` path exists because the sanitizer prompt
(`sanitize_thread.j2:73-75`) offers it as a valid operation. When the LLM marks
a thread as `removed_threads` instead of `resolved_threads`, it's deleted
entirely from both `threads[]` and `completed_threads[]` with no record.

### Paths where threads can vanish:

| Path | Archival? | When used |
|------|-----------|-----------|
| `_apply_thread_resolutions` | YES — `completed_threads[]` | Storytell `thread_resolve` |
| `_apply_arc_resolve` | YES — `resolved_arcs[]` + `completed_threads[]` | Storytell `arc_resolve` |
| Sanitizer `resolved_threads` | YES — `completed_threads[]` | Sanitizer marks thread resolved |
| **Sanitizer `removed_threads`** | **NO — complete deletion** | Sanitizer marks thread removed |

**[QUESTION: B3]** Need to decide: should we (a) eliminate `removed_threads`
from the sanitizer prompt and code (force all resolutions through
`resolved_threads`), or (b) make `removed_threads` write an archival record
before deletion? Option (a) is simpler and preserves history. Option (b) is
only useful if thread deletion with "reason" serves a real narrative purpose
distinct from resolution.

**Recommended fix** (if option a):
1. Delete `removed_threads` section from `sanitize_thread.j2` prompt
2. Delete `removed_threads` handling from `thread_sanitizer.py:453-464`
3. Update the sanitizer's `_checklist` to remove "removed" entry
4. Verify that `_apply_thread_resolutions` and `_apply_arc_resolve` catch all
   resolution cases

**Risk:** Low — the LLM should always resolve threads, not delete them. Edge
case: irrelevant threads that were accidentally created by the system could be
harmlessly kept in `completed_threads[]` with a "superseded" or "abandoned"
state.
