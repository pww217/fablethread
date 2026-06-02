# Event-based state restore for sequential turn deletion

## Purpose

Allow unlimited sequential `POST /turn/delete` calls (back to turn 1) by storing the pre-delta state in each event, replacing the single-slot file snapshot mechanism.

## Problem Statement

`state_snapshot.yaml` is a single file overwritten each turn. After `restore_snapshot_state()` copies it to `state.yaml`, both are identical. The next delete reads the same unchanged snapshot and cannot rewind further. Only the most recent turn's delta can be reverted, making sequential deletion impossible — the second delete is a no-op for state (events/chronicle rewind correctly, but state stays at the same point).

## Constraints

- No new file formats, no new filesystem artifacts beyond the existing events.jsonl
- Existing save directories must continue loading (events without `state_snapshot` gracefully skip state restore)
- Must not add yield points or slow the hot path beyond one extra `load_state()` call per turn

## Non-goals

- Not fixing the cancel route's pre-existing bug where `remove_last_event` fires even when the in-flight turn wrote no event. The old behavior is preserved for that path.
- Not changing SSE polling, turn viewer rendering, or frontend behavior.

## Solution

Store the full pre-delta state dict (loaded from `state.yaml` on disk at persist time, which hasn't been updated yet) in each event as `event["state_snapshot"]`. On delete, read this field from the event being removed, write it to `state.yaml` via the existing `save_state()`, then remove the event and chronicle entry. This gives every event its own revert point — unlimited sequential deletes work.

The file snapshot functions (`snapshot_state`, `restore_snapshot_state`, the `state_snapshot.yaml` file) are removed from the active code path — no longer read or written. The function definitions may be kept in `io.py` for external import safety but removed from `ccya.state.__init__` exports.

## Firm decisions

1. `load_state(save_dir)` at persist time reads `state.yaml` on disk, which has not yet been updated by this turn's `save_state()`. It returns the pre-delta state — the correct revert point. This is guaranteed race-free by the per-save-dir `_inflight` lock.
2. Each event stores its own full revert point. No diff, no partial snapshot, no chain.
3. Events without `state_snapshot` (played before this change) are handled gracefully: log a warning, skip state restore, still delete event/chronicle.
4. `snapshot_state()` call is removed from `turn.py:1288` — replaced by `load_state()` into the event dict. The file-based mechanism is dead code.
5. `restore_snapshot_state()` calls in both delete routes are replaced by event-based restore.
6. The cancel route's old `pop_persist_started()` + `restore_snapshot_state()` block is replaced by reading `state_snapshot` from the last event. The pre-existing unconditional `remove_last_event` is preserved (not regressed).

## Risks, Ambiguities, and Blockers

- **JSON serialization of state dict**: The state contains nested dicts, lists, strings, numbers, and booleans — all JSON-safe. No datetime, set, or custom objects. Confirmed safe.
- **Event size increase**: Each `state_snapshot` field adds ~14KB per event to events.jsonl. For 100 turns that's ~1.4MB extra in a file that would already be ~10MB. Acceptable.
- **Existing events lack `state_snapshot`**: Delete on old events won't revert state. This is a one-time transition — after playing one new turn, all future deletes have full revert.

## Status
`completed`

## Phases

One phase — all changes are tightly coupled (changing the storage in turn.py without updating the consumers in routes.py would break both delete endpoints).

## Implementation — Phase 1: Store pre-delta state in events and switch consumers

### Context files to load
- `ccya/engine/turn.py` lines 53-60 (import block), 1200-1295 (persist phase), and 1355-1365 (finally block)
- `ccya/server/routes.py` lines 20-28 (engine config imports), 31-37 (state imports), 214-256 (`cancel_turn` and `delete_last_turn`)
- `ccya/state/__init__.py` (full — exports list)
- `ccya/state/io.py` lines 99-131 (`load_state`, `save_state`) and 142-163 (`snapshot_state`, `restore_snapshot_state` to be removed)

### Detailed steps

#### Step 1.1 — Store pre-delta state in the event

**File:** `ccya/engine/turn.py`

**What:** After the event dict is fully built (after line 1284, before `append_event` at 1285), insert:
```python
event["state_snapshot"] = load_state(save_dir)
```

Remove the `snapshot_state(save_dir)` call at line 1288. Remove `snapshot_state` from the import block at line 59 (line reads `snapshot_state,`).

**Why:** `load_state(save_dir)` reads `state.yaml`, which at this point still holds the pre-delta state (the last completed turn's data). This is the state we want when reverting this turn. The file-based snapshot is now redundant.

**Validation:** `grep` confirms `snapshot_state` is no longer referenced in `turn.py`. `load_state` is already imported at line 55.

#### Step 1.2 — Remove snapshot function definitions and exports

**File:** `ccya/state/io.py`

**What:** Remove the `snapshot_state()` function (lines 142-152) and the `restore_snapshot_state()` function (lines 155-163).

**File:** `ccya/state/__init__.py`

**What:** Remove `restore_snapshot_state` and `snapshot_state` from the imports block (lines 24, 26) and from `__all__` (lines 51, 53). Keep `save_state` and `load_state` in both places (they're still used).

**Why:** These functions are dead code — no callers remain. AGENTS.md requires removing dead code immediately.

**Validation:** `grep -r "restore_snapshot_state\|snapshot_state" ccya/ --include="*.py"` returns no results after cleanup.

#### Step 1.3 — Rewrite `delete_last_turn` to use event-based restore

**File:** `ccya/server/routes.py`

**What:** In the state import block (lines 31-37), replace `restore_snapshot_state` with `save_state`. In the engine config import block (line 25), remove `pop_persist_started,` (no longer used). Then rewrite the delete function body at lines 235-256:

```python
@_app_mod.app.post("/turn/delete")
async def delete_last_turn():
    if is_turn_in_progress(str(_app_mod.SAVE_DIR)):
        return JSONResponse(
            {"error": "Turn already in progress"}, status_code=409
        )

    last_events = load_recent_turns(_app_mod.SAVE_DIR, 1)
    if not last_events:
        return JSONResponse(
            {"error": "No previous turn to delete"}, status_code=400
        )

    last_event = last_events[-1]
    actions = last_event.get("actions", [])
    pre_turn_state = last_event.get("state_snapshot")

    remove_last_event(_app_mod.SAVE_DIR)
    remove_last_chronicle_turn(_app_mod.SAVE_DIR)

    if pre_turn_state is not None:
        save_state(_app_mod.SAVE_DIR, pre_turn_state)
    else:
        _log.warning(
            "delete_last_turn state_snapshot missing for turn=%s — state not reverted",
            last_event.get("turn"),
        )

    _log.info("delete_last_turn turn=%s", last_event.get("turn"))
    return JSONResponse({"actions": actions, "turn": last_event.get("turn")})
```

**Why:** The `state_snapshot` in the event (captured at persist time) contains the state before this turn's delta. `save_state()` writes it to `state.yaml`. The snapshot file is no longer involved. Each event carries its own revert point, so any number of sequential deletes work — each delete reads from the new last event.

**Validation:** Manual. Play a turn, verify `state_snapshot` exists in its event. Delete the turn, verify `state.yaml` reverts to the pre-turn state. Delete again, verify it reverts one more turn.

#### Step 1.4 — Rewrite `cancel_turn` to use event-based restore

**File:** `ccya/server/routes.py`

**What:** Remove `pop_persist_started` from the engine config import (line 25). Replace the cancel handler body (lines 214-232) to read `state_snapshot` from the last event before removing it:

```python
@_app_mod.app.post("/turn/cancel")
async def cancel_turn():
    if not is_turn_in_progress(str(_app_mod.SAVE_DIR)):
        return JSONResponse(
            {"error": "No turn in progress"}, status_code=400
        )

    request_cancel(str(_app_mod.SAVE_DIR))
    released = await await_turn_done(str(_app_mod.SAVE_DIR), timeout=30.0)
    clear_cancel(str(_app_mod.SAVE_DIR))

    last_events = load_recent_turns(_app_mod.SAVE_DIR, 1)
    if last_events:
        event = last_events[-1]
        pre_turn_state = event.get("state_snapshot")
        remove_last_event(_app_mod.SAVE_DIR)
        remove_last_chronicle_turn(_app_mod.SAVE_DIR)
        if pre_turn_state is not None:
            save_state(_app_mod.SAVE_DIR, pre_turn_state)
        else:
            _log.warning(
                "cancel_turn state_snapshot missing for turn=%s — state not reverted",
                event.get("turn"),
            )

    return JSONResponse({"ok": True})
```

**Why:** The old `pop_persist_started()` check always returned False (the generator's `finally` consumed the key), making state restore dead code. Reading `state_snapshot` directly from the event replaces both the file-snapshot restore and the useless flag check. The pre-existing unconditional `remove_last_event` bug (fires even if the in-flight turn wrote nothing) is preserved — not regressed.

**Validation:** Submit a long turn, let it complete → click stop after the fact → verify the last event is removed and state.yaml reverts to pre-turn state.

### Tests to write or update

Tests are temporarily removed per AGENTS.md. No tests to write.

### Cleanup verification

After all changes, run `make check` (lint + typecheck) to confirm no import errors or unused symbols.
