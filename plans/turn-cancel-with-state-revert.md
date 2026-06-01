# Cancel in-flight turn with full state revert

## Purpose

Give the cancel button (send-btn when `submitting`) the same behavior as retry: revert state, remove event, remove chronicle, and prevent the turn viewer from showing a blank entry.

## Problem Statement

The cancel button (clicked while a turn is streaming) only closes the EventSource client-side and removes the DOM block. The server-side async generator continues running to completion: it appends an event to `events.jsonl`, saves state, and appends to `chronicle.md`. The turn viewer sees this orphaned event and renders a blank turn. There is no server-side cancel mechanism and no cleanup path for partially-persisted turns.

## Constraints

- Must not modify the LLM call path (no interrupt signals to the server).
- Must share the same cleanup path as `POST /turn/delete` (snapshot restore, event/chronicle removal) — but only when persist has started.
- The inflight lock must always be released — no leak paths.
- Frontend change must be minimal (fire-and-forget fetch, no async refactor of `stopTurn`).
- The turn viewer SSE polling (1s interval) is the existing refresh mechanism; no new SSE events.

## Non-goals

- Not adding an abort/interrupt to the LLM server — the server-side generator runs to its next check point or completion.
- Not replacing the turn viewer SSE with a different push mechanism.
- Not changing the retry path — snapshot/restore is already deployed.

## Solution

Introduce per-save-dir `asyncio.Event` signals read by `run_turn()` at each phase boundary. When set, the generator returns early (skipping persist, falling through to `finally`). A new `POST /turn/cancel` endpoint sets the cancel signal, awaits `_turn_done` (set by `finally`), then runs cleanup: remove last event/chronicle turn, and (only if persist had started) restore state snapshot. The frontend's `stopTurn()` fires a fire-and-forget `POST /turn/cancel` before closing the EventSource.

## Firm decisions

1. `_inflight` (the per-save-dir `asyncio.Lock`) remains the sole mutual-exclusion mechanism — no new locks.
2. Cancel signal is an `asyncio.Event` per save_dir stored alongside `_inflight` in `engine/config.py`.
3. `register_turn()` is called BEFORE `_inflight.acquire()` so `_turn_done` always exists while a turn could be in progress.
4. `run_turn()` checks the cancel signal at every `yield` point — if set, it `return`s (skipping persist, falling to `finally`).
5. A `_persist_started: dict[str, bool]` flag is set right before `snapshot_state()`. The cancel endpoint checks this flag before calling `restore_snapshot_state()` — preventing double-revert for turns that were cancelled before persist.
6. `signal_turn_done()` (called in `finally`) cleans up ALL per-save-dir lifecycle dict entries (`_cancel_requested`, `_turn_done`, `_persist_started`) — no leaks.
7. Cleanup is idempotent: `remove_last_event` returns False if no event was written.
8. Frontend change: one line — `fetch('/turn/cancel', {method:'POST'})` before `_turnCancel()`.

## Risks, Ambiguities, and Blockers

- **Generator cancellation by disconnect:** FastAPI/SSE-starlette may cancel the async generator when the HTTP connection drops. If this happens before `run_turn()` checks the cancel signal, `finally` still runs (asyncio guarantees this for `CancelledError`). `_turn_done` is set, cancel endpoint proceeds with cleanup.
- **Cancel after persist already started:** `_persist_started` flag is set before `snapshot_state`. If cancel arrives between `append_event` and `save_state`, the event is already written but state_snapshot reflects pre-turn state — cleanup handles both correctly.
- **Race: cancel + new turn submission:** The inflight lock prevents starting a new turn while one is in progress. After cleanup releases the lock, new submission is safe.

## Status

`open`

## Phases

2 phases: cancel signal infrastructure + endpoint and frontend wiring

## Implementation — Phase 1: Cancel signal infrastructure and generator check points

### Context files to load

- `ccya/engine/config.py` — `_EventLock`, `_inflight`, `is_turn_in_progress`
- `ccya/engine/turn.py` — `run_turn()` generator structure, yield points, exception blocks, `finally`

### Detailed steps

#### Step 1.1 — Add lifecycle signal dicts to `engine/config.py`

**File:** `ccya/engine/config.py`

**What:** Define three per-save-dir containers alongside `_inflight`:

```python
_cancel_requested: dict[str, asyncio.Event] = {}
_turn_done: dict[str, asyncio.Event] = {}
_persist_started: dict[str, bool] = {}
```

Add functions:

```python
def request_cancel(save_dir: str) -> None: ...
def is_cancel_requested(save_dir: str) -> bool: ...
def register_persist(save_dir: str) -> None: ...   # set _persist_started[save_dir] = True
def clear_cancel(save_dir: str) -> None: ...
def register_turn(save_dir: str) -> None: ...   # create _turn_done event
def signal_turn_done(save_dir: str) -> None: ...  # set event, clean ALL per-save entries
def await_turn_done(save_dir: str, timeout: float = 30.0) -> bool: ...  # returns False on timeout/missing
```

**Why:** The generator and the cancel endpoint need an async-safe side-channel. asyncio.Event is zero-cost when not set and O(1) to check.

**Validation:** `from ccya.engine.config import request_cancel, is_cancel_requested, register_persist, clear_cancel, register_turn, signal_turn_done, await_turn_done` succeeds, mypy passes.

#### Step 1.2 — Register and check lifecycle signals in `run_turn()`

**File:** `ccya/engine/turn.py`

**What:**
- Before `_inflight.acquire()` (line 830), call `register_turn(str(save_dir))`.
- At each yield point inside the `try` block (lines 853, 869, 910-911, 930, 934, 958, 980, 1169), call `is_cancel_requested(str(save_dir))`. If True, `return` — this stops the generator and `finally` still runs.
- Before `snapshot_state(save_dir)` (the call added in the retry fix), call `register_persist(str(save_dir))`.
- In `finally` (line 1327), after `_inflight.release(str(save_dir))`, call `signal_turn_done(str(save_dir))`.

**Why:** `return` inside an async generator's `try` block triggers `finally` but stops iteration — no new yield, no persist. This is simpler and more robust than raising a custom exception. The `_TurnCancelled` exception approach from earlier drafts is discarded.

**Validation:** Trace through the generator:
- Cancel fires before "persist" yield → `return`, `finally` runs, no event/chronicle/state written.
- Cancel fires after "persist" but before "complete" → persist already ran (event + snapshot + state + chronicle written) → cleanup handled by cancel endpoint using `_persist_started` flag.

#### Step 1.3 — Export new symbols

**File:** `ccya/engine/__init__.py`

**What:** Add `request_cancel`, `is_cancel_requested`, `register_persist`, `clear_cancel`, `register_turn`, `signal_turn_done`, `await_turn_done` to the module's public API.

**Validation:** `from ccya.engine import request_cancel, is_cancel_requested, register_persist, clear_cancel, register_turn, signal_turn_done, await_turn_done` works.

### Tests to write or update

None for this phase; tested manually by end-to-end flow in Phase 2.

## Implementation — Phase 2: Cancel endpoint, cleanup, and frontend wiring

### Context files to load

- `ccya/server/routes.py` — `delete_last_turn()`, `event_stream()` in `GET /turn`
- `ccya/templates/index.html` — `stopTurn()`, `_turnCancel()`, the send-btn markup (lines 190-197)
- `ccya/engine/turn.py` — `run_turn()` (already loaded in Phase 1)
- `ccya/state/chronicle.py` — `remove_last_event`, `remove_last_chronicle_turn`
- `ccya/state/io.py` — `restore_snapshot_state`
- `ccya/engine/config.py` — cancel scope functions (already loaded in Phase 1)

### Detailed steps

#### Step 2.1 — Add `POST /turn/cancel` route

**File:** `ccya/server/routes.py`

**What:** New route after `GET /turn` (after line 207):

```python
@_app_mod.app.post("/turn/cancel")
async def cancel_turn():
    if not is_turn_in_progress(str(_app_mod.SAVE_DIR)):
        return JSONResponse({"ok": True})  # nothing to cancel

    request_cancel(str(_app_mod.SAVE_DIR))
    released = await await_turn_done(str(_app_mod.SAVE_DIR), timeout=30.0)
    if not released:
        _log.warning("cancel_turn timeout waiting for turn to finish")
    clear_cancel(str(_app_mod.SAVE_DIR))

    # Idempotent cleanup — always remove event/chronicle if written
    remove_last_event(_app_mod.SAVE_DIR)
    remove_last_chronicle_turn(_app_mod.SAVE_DIR)
    # Only restore snapshot if persist phase had started (snapshot was taken for this turn)
    register_persist_flag = ...  # _persist_started.pop(str(_app_mod.SAVE_DIR), False) — see Step 1.1
    if ...:
        restore_snapshot_state(_app_mod.SAVE_DIR)

    return JSONResponse({"ok": True})
```

The `register_persist_flag` check is implemented by calling `_persist_started.pop(str(_app_mod.SAVE_DIR), False)` — if the flag was set (persist started), restore the snapshot; otherwise skip it.

**Why:** Cleanup is idempotent. If the generator stopped before persist, `remove_last_event` is a no-op (no event was written), and `restore_snapshot_state` is skipped (flag was never set). If persist already ran, cleanup removes event/chronicle and reverts state to the snapshot taken during persist.

**Validation:** Start a turn, cancel it mid-stream, verify `curl -X POST http://localhost:8000/turn/cancel` returns 200. Verify `events.jsonl` has no orphaned entry. Verify `state.yaml` matches pre-turn state.

#### Step 2.2 — Wire cancel into frontend `stopTurn()`

**File:** `ccya/templates/index.html`

**What:** In `stopTurn()` (line 1516), before calling `this._turnCancel()`, fire a fire-and-forget POST:

```javascript
stopTurn() {
    if (!this.submitting || typeof this._turnCancel !== 'function') return;
    fetch('/turn/cancel', { method: 'POST' }).catch(() => {});
    this._turnCancel();
},
```

**Why:** Fire-and-forget avoids making `stopTurn` async. The server handles cleanup even if the EventSource close races with the fetch. `.catch()` prevents unhandled rejection if the server is unreachable.

**Validation:** Click cancel mid-turn. Turn disappears from narrative panel. State panels revert to pre-turn state. Turn viewer shows no orphaned entry. Next turn works normally.

#### Step 2.3 — Import new symbols in routes

**File:** `ccya/server/routes.py`

**What:** Add `request_cancel`, `clear_cancel`, `await_turn_done` to the existing `from ccya.engine import (...)` block. These are the only three new functions used by `cancel_turn()` — `is_cancel_requested`, `register_turn`, `register_persist`, and `signal_turn_done` are used only in `turn.py` (already imported via `from ccya.state import ...` or accessed directly in `engine/`).

**Validation:** `make check` passes.

### Tests to write or update

None. Tested manually via end-to-end flow: start turn, cancel, verify no blank turn in TV, verify state reverted, verify next turn proceeds normally.
