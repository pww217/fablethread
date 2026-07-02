# Plan: Global Mutable State Migration

**Status: scoping**

**Ticket:** I-23 (Engine core tech debt consolidation)

## Design Reference

I-23 plan: `roadmap/improvements/I-23-engine-core-tech-debt-consolidation.md`

## Purpose

Move turn lifecycle state (in-flight lock, cancel signal, turn-done signal) from module-level dicts in `config.py` to server-owned state in `server/app.py`, passed via `TurnContext` to the engine. The server is single-save (SAVE_DIR is a global Path | None), so the dict-keyed-by-save_dir is overkill. The state is a server concern (preventing concurrent turns, cancel endpoint), not an engine concern.

**Goal:** Eliminate module-level state from `config.py`, reduce state access from 15+ call sites across 3 modules to a clean ownership model: server owns state, engine reads cancel signal via context.

## Constraints

- No behavioral change — cancel flow must work identically
- Server is single-save (SAVE_DIR global in app.py) — no multi-save support needed
- The cancel endpoint (`/turn/cancel`) is called from a separate HTTP request while a turn is running — it needs access to the running state
- The engine must not own state — it only reads a cancel signal
- `config.py` must not import from `server/` (engine must not depend on server)

## Phase 1: Move state to server

**Files:** `server/app.py`

**Dependencies:** None

### Step 1.1 — Add state variables to server/app.py

**File:** `server/app.py`

**What:**
- Add after `SAVE_DIR` declaration:
  ```python
  _turn_lock: asyncio.Lock | None = None
  _cancel_event: asyncio.Event | None = None
  _turn_done_event: asyncio.Event | None = None
  ```
- Add helper functions (module-level, server-only):
  ```python
  def _start_turn() -> tuple[asyncio.Lock, asyncio.Event, asyncio.Event]:
      global _turn_lock, _cancel_event, _turn_done_event
      _turn_lock = asyncio.Lock()
      _cancel_event = asyncio.Event()
      _turn_done_event = asyncio.Event()
      return _turn_lock, _cancel_event, _turn_done_event

  def _signal_turn_done() -> None:
      global _turn_lock, _cancel_event, _turn_done_event
      if _turn_done_event:
          _turn_done_event.set()
      if _cancel_event:
          _cancel_event.set()
      if _turn_lock:
          _turn_lock.release()
      _turn_lock = _cancel_event = _turn_done_event = None

  def _is_cancel_requested() -> bool:
      return _cancel_event is not None and _cancel_event.is_set()

  def _is_turn_in_progress() -> bool:
      return _turn_lock is not None and _turn_lock.locked()

  async def _await_turn_done(timeout: float = 30.0) -> bool:
      if _turn_done_event is None:
          return False
      try:
          await asyncio.wait_for(_turn_done_event.wait(), timeout=timeout)
          return True
      except asyncio.TimeoutError:
          return False
  ```

**Why:** The server owns the state. The helpers are simple accessors. `_signal_turn_done` does everything that `signal_turn_done` + `clear_cancel` do in config.py (sets turn_done, sets cancel so the running turn sees it, releases lock, cleans up).

### Step 1.2 — Export state helpers from server/app.py

**File:** `server/app.py`

**What:**
- The helpers are module-level functions, accessible via `from ccya.server.app import _is_cancel_requested, _is_turn_in_progress, _await_turn_done`
- No need to add to `__init__.py` or `engine/__init__.py` — they are server-only

**Why:** The cancel endpoint in routes.py needs them. The engine does not.

## Phase 2: Update server routes

**Files:** `server/routes.py`

**Dependencies:** Phase 1

### Step 2.1 — Replace engine state imports with server state imports

**File:** `server/routes.py`

**What:**
- Remove from imports: `await_turn_done, clear_cancel, is_turn_in_progress, request_cancel`
- Add: `from ccya.server.app import _is_cancel_requested as _is_cancel, _is_turn_in_progress as _is_in_progress, _await_turn_done as _await_done`
- Update `cancel_turn()` (line 344-357):
  ```python
  @_app_mod.app.post("/turn/cancel")
  async def cancel_turn():
      if err := _require_save():
          return err
      if not _is_in_progress():
          return JSONResponse({"ok": True})
      if _cancel_event:
          _cancel_event.set()
      released = await _await_done(timeout=30.0)
      if not released:
          _log.warning("cancel_turn timeout waiting for turn to finish")
      return JSONResponse({"ok": True, "cancelled": True})
  ```
- Update `delete_last_turn()` (line 360-369):
  ```python
  if _is_in_progress():
      return JSONResponse({"error": "Turn already in progress"}, status_code=409)
  ```

**Why:** The cancel endpoint now uses server-owned state directly. No more engine state access from server.

## Phase 3: Update engine to receive state via context

**Files:** `engine/turn_context.py`, `engine/turn.py`, `engine/narrate.py`

**Dependencies:** Phase 1

### Step 3.1 — Add state fields to TurnContext

**File:** `engine/turn_context.py`

**What:**
- Add to `TurnContext` dataclass:
  ```python
  _cancel_event: asyncio.Event | None = None
  ```
- Import `asyncio` from `asyncio`

**Why:** The engine needs to check cancel during turn execution. The state is passed via context, not accessed from module-level.

### Step 3.2 — Update run_turn to create state and pass via context

**File:** `engine/turn.py`

**What:**
- Remove from imports: `_inflight, is_cancel_requested, register_turn, signal_turn_done`
- Add: `from ccya.server.app import _start_turn`
- In `run_turn` (around line 83-85):
  ```python
  try:
      _turn_lock, _cancel_event, _turn_done_event = _start_turn()
      await _turn_lock.acquire()
  ```
- Update TurnContext creation (around line 91-100):
  ```python
  ctx = TurnContext(
      state=state, user_input=user_input, turn_no=0, trace_id=trace_id,
      config=config, recent_turns=recent_turns,
      save_dir=save_dir, packing={...}, _env=env,
      _cancel_event=_cancel_event,
  )
  ```
- Replace all `is_cancel_requested(str(save_dir))` with `is_cancel_requested(ctx)` (new helper)
- In finally block (around line 633-635):
  ```python
  finally:
      _signal_turn_done()
  ```
- Remove `register_turn` and `signal_turn_done` calls (handled by `_start_turn` / `_signal_turn_done`)

**Why:** The engine no longer accesses module-level state. It receives cancel state via context.

### Step 3.3 — Add cancel check helper

**File:** `engine/turn.py`

**What:**
- Add module-level helper:
  ```python
  def is_cancel_requested(ctx: TurnContext) -> bool:
      return ctx._cancel_event is not None and ctx._cancel_event.is_set()
  ```

**Why:** Replaces all `is_cancel_requested(str(save_dir))` calls. The helper is inline, no module-level state access.

### Step 3.4 — Update narrate.py

**File:** `engine/narrate.py`

**What:**
- Remove from imports: `is_cancel_requested`
- Update `_narrate_setup` (line 146):
  ```python
  if is_cancel_requested(ctx):
      return None, None
  ```

**Why:** The narrate function now uses the context-local cancel check.

## Phase 4: Clean up config.py

**Files:** `engine/config.py`, `engine/__init__.py`

**Dependencies:** Phase 3

### Step 4.1 — Remove state management from config.py

**File:** `engine/config.py`

**What:**
- Remove: `_EventLock` class, `_inflight`, `_cancel_requested`, `_turn_done`
- Remove: `is_turn_in_progress`, `request_cancel`, `is_cancel_requested`, `clear_cancel`, `register_turn`, `signal_turn_done`, `clear_all_turn_locks`, `await_turn_done`
- Keep: `EngineConfig` dataclass, `_build_jinja_env`, `_render`

**Why:** The engine no longer owns state. All state management is in server/app.py.

### Step 4.2 — Update engine/__init__.py

**File:** `engine/__init__.py`

**What:**
- Remove from imports: `is_cancel_requested, signal_turn_done, await_turn_done`
- Remove from `__all__`: `"is_cancel_requested", "signal_turn_done", "await_turn_done"`

**Why:** These functions no longer exist in config.py.

## Verification

- `make typecheck` passes
- `make lint` passes
- Server starts and `/` loads
- `/turn/cancel` endpoint works (cancel a running turn)
- `/turn/delete` endpoint works (delete last turn, checks in-progress)
- `ev.py turn 3 --save-dir evals/runs/latest` produces identical results
- No behavioral change: cancel flow identical to before

## Files changed

| File | Before | After | Delta |
|------|--------|-------|-------|
| `config.py` | 437 lines | ~340 lines | -97 |
| `app.py` | 197 lines | ~230 lines | +33 |
| `routes.py` | 1048 lines | ~1048 lines | 0 |
| `turn.py` | 667 lines | ~667 lines | 0 |
| `turn_context.py` | 50 lines | ~55 lines | +5 |
| `narrate.py` | 247 lines | ~247 lines | 0 |
| `__init__.py` (engine) | ~40 lines | ~30 lines | -10 |

## Done when

- State moved from config.py to server/app.py
- TurnContext has `_cancel_event` field
- run_turn creates state via `_start_turn`, passes via context
- All cancel checks use context-local helper
- Cancel endpoint uses server state directly
- `config.py` state functions removed
- `make check` passes
- `docs/repomap.md` updated if module boundaries change
