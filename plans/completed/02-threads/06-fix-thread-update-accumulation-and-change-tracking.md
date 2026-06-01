# Fix: thread_update accumulation bug and change tracker gaps

## Purpose

Fix two confirmed bugs in the thread system: the `_apply_thread_updates` accumulator that silently drops earlier updates in multi-update turns, and the `summarize_changes` tracker that misses `progress` field changes.

## Problem Statement

`_apply_thread_updates` silently corrupts thread state when the storyteller emits 2+ `thread_update` entries in a single turn. Each iteration rebuilds `remaining_threads` from the original `arc.threads`, so earlier iterations' changes are overwritten. Separately, `summarize_changes` only diffs `active`, `urgency`, and `summary` — not `progress` — making progress-only thread mutations invisible in the event log.

## Constraints

- No model changes. The `ThreadUpdate.progress` field already exists and works correctly.
- No prompt changes. The storytell prompt already emits `progress` in `thread_update`.
- Fixes must be minimal — change only the broken line/condition, not the surrounding logic.

## Non-goals

- No changes to the changes tracker's `inventory`, `player`, `facts`, or `momentum` sections.
- No changes to the `_apply_arc_resolve` or `_apply_thread_resolutions` functions.
- No changes to model definitions, prompts, or configuration.
- Not adding tests (tests are temporarily removed during refactor).

## Solution

Fix the accumulator in `_apply_thread_updates` by switching the list comprehension source from `arc.threads` to `remaining_threads`. Then add `progress` change detection to `summarize_changes` in the same branch that already handles `active`, `urgency`, and `summary`.

## Firm decisions

1. The `found_idx` search on line 172 correctly uses the original `arc.threads` — thread IDs don't change between iterations, and the index stays valid because each update replaces its thread in-place preserving list order.
2. The changes tracker should surface progress changes with the same `kind: "updated"` pattern as other thread mutations.
3. Both fixes are in separate files — they are independent and can be executed in either order.

## Risks, Ambiguities, and Blockers

None. Both changes are <5 line modifications with no side effects.

## Status

`completed`

## Phases

2 phases: fix the accumulator bug in `turn.py`, then fix the change tracker gap in `changes.py`. Independent — order does not matter.

## Implementation — Phase 1: Fix multi-update accumulator in `_apply_thread_updates`

### Context files to load

- `ccya/engine/turn.py` lines 139-206 (`_apply_thread_updates`)

### Detailed steps

#### Step 1.1 — Fix list comprehension source

**File:** `ccya/engine/turn.py` line 195

**What:** Change the list comprehension in the `for` loop body from `enumerate(arc.threads)` to `enumerate(remaining_threads)`.

Current:
```python
remaining_threads = [t for i2, t in enumerate(arc.threads) if i2 != found_idx]
```

Changed to:
```python
remaining_threads = [t for i2, t in enumerate(remaining_threads) if i2 != found_idx]
```

**Why:** Each iteration must build from the *accumulated* thread list (`remaining_threads`), which includes updates from prior iterations in the same turn. Using the original `arc.threads` discards those earlier mutations.

**Validation:** Run the reproduction script from the investigation:
```python
from ccya.models import ArcThread, CampaignArc, ThreadUpdate
threads = [
    ArcThread(id='t1', summary='one', scope='arc', progress='step 1'),
    ArcThread(id='t2', summary='two', scope='arc', progress='step 1'),
]
arc = CampaignArc(visible_goal='g', thematic_question='q', threads=threads, completed_threads=[])
remaining = list(arc.threads)
for update in [ThreadUpdate(id='t1', progress='t1 step 2'), ThreadUpdate(id='t2', progress='t2 step 2')]:
    found_idx = next(i for i, t in enumerate(arc.threads) if t.id == update.id)
    u = {k: v for k, v in [('progress', update.progress)] if v is not None}
    remaining = [t for i2, t in enumerate(remaining) if i2 != found_idx]
    remaining.insert(found_idx, arc.threads[found_idx].model_copy(update=u))
result = arc.model_copy(update={'threads': remaining})
assert result.threads[0].progress == 't1 step 2'
assert result.threads[1].progress == 't2 step 2'
```

### Tests to write or update

None (tests are temporarily removed).

## Implementation — Phase 2: Add `progress` to changes tracker

### Context files to load

- `ccya/engine/changes.py` lines 286-300 (thread update detection in `summarize_changes`)

### Detailed steps

#### Step 2.1 — Add progress change detection

**File:** `ccya/engine/changes.py` line 293 (after the `summary` check)

**What:** Add a `progress` change check in the `elif po and pr:` branch. Insert after the `summary` check on line 293:

Current block (lines 286-300):
```python
elif po and pr:
    changes = []
    if po.get("urgency") != pr.get("urgency"):
        changes.append(f"urgency: {pr.get('urgency', '?')}→{po.get('urgency', '?')}")
    if po.get("active") != pr.get("active"):
        changes.append("reactivated" if po.get("active") else "dormant")
    if po.get("summary") and po.get("summary") != pr.get("summary"):
        changes.append("summary updated")
    if changes:
        threads.append({
            "kind": "updated",
            "id": tid,
            "summary": po.get("summary", ""),
            "detail": "; ".join(changes),
        })
```

Add after line 293:
```python
    if po.get("progress") and po.get("progress") != pr.get("progress"):
        changes.append("progress updated")
```

**Why:** Without this check, progress-only thread mutations produce no `changes.threads` entry, making them invisible. Adding it makes progress changes visible in the `kind: "updated"` entry with `detail: "progress updated"`.

Note: The check uses `po.get("progress")` (truthy) rather than `po.get("progress") != pr.get("progress")` alone to avoid emitting "progress updated" when both pre and post are empty strings `""` — a no-op transition should not appear as a change.

**Validation:** Run a script that compares pre/post state with a thread whose `progress` changed:
```python
pre = {"arc": {"threads": [{"id": "t1", "progress": "", "active": True, "urgency": "normal", "summary": "s", "scope": "arc"}]}}
post = {"arc": {"threads": [{"id": "t1", "progress": "found evidence", "active": True, "urgency": "normal", "summary": "s", "scope": "arc"}]}}
from ccya.engine.changes import summarize_changes
ch = summarize_changes(pre, post, {}, [])
assert len(ch["threads"]) == 1
assert ch["threads"][0]["kind"] == "updated"
assert "progress updated" in ch["threads"][0]["detail"]
```

### Tests to write or update

None (tests are temporarily removed).
