# Save Management

## Purpose

Add a "Load Save" modal to the gear menu that lists all available saves with metadata (name, pack, turn count, last modified) and lets users switch between them seamlessly without server restart.

## Problem Statement

The engine currently hardcodes `SAVE_DIR = Path("saves/default")` at module import time, with auto-resume of the newest non-default save directory. There is no UI to list or switch between saves. Users must restart the server to change saves, and `saves/default` is a magic excluded name. This makes it impossible to switch between multiple active games or revisit older saves.

## Constraints

- No "save" button — `save_state()` already runs every turn automatically.
- No "delete save" — out of scope for this phase.
- Must follow existing UI patterns: backdrop + modal with head/body, Alpine.js for interactivity, HTMX where applicable.
- Changing saves must not require a server restart.
- Must handle stale turn locks, in-progress turns, and orphaned SSE connections.
- `saves/default` must remain a valid, loadable save.
- No test writing during refactor phase.

## Non-goals

- Delete saves (future phase).
- Rename saves (future phase).
- Per-save config overrides (config.yaml is global).
- Save naming/editing.
- Save export/import.
- Save deduplication or archival.

## Solution

Add a `/api/saves` endpoint that lists all save directories with metadata (name, pack, turn count, last modified, PC name, location). Add a `POST /api/switch-save` endpoint that validates no turn is in progress, clears stale engine locks, updates `_app_mod.SAVE_DIR`, and returns the new save's state. Add a "Load Save" item to the gear menu that opens a modal listing saves as cards (matching pack picker styling), with a "New Game" button that opens the existing pack picker flow. On selection, the modal calls `switch-save`, then reloads the page.

## Firm decisions

1. Modal follows pack picker pattern: backdrop + modal with head/body, ESC to close, click-away to close.
2. "New Game" opens the existing pack picker modal (reuses `openPackPicker()`).
3. "Load Save" opens a new save list modal.
4. Switch endpoint blocks if `is_turn_in_progress()` returns true — shows "Turn in progress, try again later."
5. On switch: call `clear_all_turn_locks()` (clears `_inflight._locks`, `_cancel_requested`, `_turn_done`, `_persist_started`) before updating `SAVE_DIR`.
6. Page reloads after successful switch (simplest approach, consistent with "New Game" behavior).
7. Save cards show: save directory name, pack name, turn count, last modified date, PC name.
8. `saves/default` is included in the list (no longer magic-excluded from listing).
9. The `_find_latest_save()` exclusion at server startup remains unchanged — it only affects initial selection.

## Risks, Ambiguities, and Blockers

- **SSE connections:** Turn viewer SSE clients (`/turn_viewer/stream`) stay connected to the old events.jsonl. On page reload they reconnect to the new save automatically. No explicit cleanup needed since reload tears down all connections.
- **Stale engine dicts:** `_inflight._locks`, `_cancel_requested`, `_turn_done`, and `_persist_started` all accumulate per-save-dir entries. `clear_all_turn_locks()` clears all four on switch to prevent memory leak over long sessions.
- **`_find_latest_save()` exclusion:** `saves/default` is excluded from auto-resume scan. This is fine — it's the fallback. The save list should include it normally.
- **Ambiguous:** Should "New Game" show a confirmation dialog? It already does via `startNewGame()` which calls `confirm('Reset the current game?')`. No change needed.

## Status
`open`

## Phases

2 phases: (1) Backend API for listing and switching saves, (2) Frontend modal UI for save selection.

---

## Implementation — Phase 1: Backend API

### Context files to load
- `ccya/server/routes.py` — existing route handlers, imports
- `ccya/server/app.py` — `_app_mod` reference, `SAVE_DIR` variable
- `ccya/engine/config.py` — `_inflight`, `_cancel_requested`, `_turn_done` dicts
- `ccya/state/io.py` — `load_state`, `init_save_dir`

### Detailed steps

#### Step 1.1 — Add `_list_saves()` helper

**File:** `ccya/server/routes.py`

**What:** Add a module-level function `_list_saves()` that scans `saves/` directory and returns a list of dicts with metadata for each save directory. Each dict: `{name, pack, turn_count, last_modified, pc_name, location_name}`. Use `load_state()` to read metadata from each `state.yaml`. Sort by `last_modified` descending.

**Why:** Centralizes save listing logic. Both the API endpoint and future UI need this.

**Validation:** `python -c "from ccya.server.routes import _list_saves; print(_list_saves())"` — returns list of dicts with expected keys.

#### Step 1.2 — Add `GET /api/saves` endpoint

**File:** `ccya/server/routes.py`

**What:** Add `@_app_mod.app.get("/api/saves")` handler that calls `_list_saves()` and returns JSON.

**Why:** Frontend needs an API to fetch the save list.

**Validation:** `curl http://localhost:8000/api/saves` — returns JSON array of save objects.

#### Step 1.3 — Export lock-clearing from engine module

**File:** `ccya/engine/config.py`, `ccya/engine/__init__.py`

**What:** Add `clear_all_turn_locks()` function to `ccya/engine/config.py` that clears `_inflight._locks`, `_cancel_requested`, `_turn_done`, and `_persist_started`. Export it from `ccya/engine/__init__.py`.

**Why:** Keeps lock management encapsulated in the engine module rather than exposing internal dicts to routes. `_persist_started` is dead code (per `plans/completed/dead-code/dead-code-removal.md`) but should be cleared alongside the others to prevent confusion.

**Validation:** `python -c "from ccya.engine import clear_all_turn_locks; clear_all_turn_locks(); print('ok')"`

#### Step 1.4 — Add `POST /api/switch-save` endpoint

**File:** `ccya/server/routes.py`

**What:** Add `@_app_mod.app.post("/api/switch-save")` handler that:
1. Reads `save_name` from request JSON body
2. Constructs `save_dir = Path("saves") / save_name`
3. Validates `save_dir` exists and is a directory
4. Checks `is_turn_in_progress(str(_app_mod.SAVE_DIR))` — returns 409 if true
5. Calls `clear_all_turn_locks()` from `ccya.engine` to clear stale engine locks
6. Sets `_app_mod.SAVE_DIR = save_dir`
7. Loads state from new save dir via `load_state(save_dir)`
8. Returns JSON with `{ok: true, save_dir: ..., state: ...}`

**Why:** This is the core switch operation. Must be atomic (no partial state) and safe (block during turns, clear stale locks). Using `clear_all_turn_locks()` encapsulates lock cleanup in the engine module.

**Validation:** `curl -X POST http://localhost:8000/api/switch-save -H "Content-Type: application/json" -d '{"save_name": "test-save"}'` — returns state object.

### Tests to write or update

None — tests are temporarily removed during refactor.

---

## Implementation — Phase 2: Frontend Modal UI

### Context files to load
- `ccya/templates/index.html` — gear menu, game() Alpine component, pack picker modal pattern
- `ccya/static/app.src.css` — pack picker modal CSS classes
- `ccya/server/routes.py` — `/api/saves` endpoint path

### Detailed steps

#### Step 2.1 — Add "Load Save" item to gear menu

**File:** `ccya/templates/index.html`

**What:** Add a `<button type="button" class="gear-menu-item" @click="menuOpen = false; openSavePicker()">Load Save</button>` to the gear menu dropdown, positioned before "New Game". This calls `openSavePicker()` which does not exist yet.

**Why:** User-facing entry point for save selection.

**Validation:** Gear menu shows "Load Save" button before "New Game".

#### Step 2.2 — Add save picker modal HTML

**File:** `ccya/templates/index.html`

**What:** Add save picker modal HTML after the settings modal block. Structure mirrors pack picker:
```html
<div id="save-picker-backdrop" class="pack-picker-backdrop hidden"></div>
<div id="save-picker-modal" class="pack-picker-modal hidden">
    <div class="pack-picker-head">
        <span id="save-picker-title" class="pack-picker-title">Load Save</span>
        <button id="save-picker-close" type="button" class="pack-picker-close" aria-label="Close">×</button>
    </div>
    <div id="save-picker-body" class="pack-picker-body">
        <p class="empty-state">Loading saves…</p>
    </div>
    <div class="pack-picker-foot">
        <button type="button" class="save-picker-new-game-btn" @click="menuOpen = false; openPackPicker()">
            + New Game
        </button>
    </div>
</div>
```

**Why:** Provides the modal shell. "New Game" button at bottom opens existing pack picker flow.

**Validation:** Modal HTML renders correctly with backdrop, head, body, and footer.

#### Step 2.3 — Add `openSavePicker()` to game() Alpine component

**File:** `ccya/templates/index.html`

**What:** Add `openSavePicker()` method to the `game()` function. This method:
1. Shows backdrop and modal (same pattern as `openPackPicker()`)
2. Fetches `/api/saves` to get save list
3. Renders save cards in `#save-picker-body` — each card shows: save name, pack, turn count, last modified, PC name
4. Attaches click handlers to each card that call `switchSave(saveName, closeModal)`
5. Closes modal on backdrop click, close button, or ESC key

**Why:** Core UI logic for displaying and selecting saves.

**Validation:** Modal opens, fetches saves, renders cards. Clicking a card calls switch-save API.

#### Step 2.4 — Add `switchSave()` to game() Alpine component

**File:** `ccya/templates/index.html`

**What:** Add `switchSave(saveName, closeModal)` method that:
1. Calls `closeModal()` to close the modal
2. Shows loading indicator in narrative panel (same pattern as `startNewGame()`)
3. POSTs to `/api/switch-save` with `{save_name: saveName}`
4. On success: `window.location.reload()`
5. On failure: shows error message in loading div

**Why:** Executes the switch and reloads page to reflect new save state.

**Validation:** Clicking a save card switches to that save and reloads the page.

#### Step 2.5 — Add save card CSS

**File:** `ccya/static/app.src.css`

**What:** Add CSS for save picker cards. Reuse pack picker card styling (`pack-card`, `pack-card-header`, `pack-card-name`, etc.) since the visual design should match. Add `.pack-picker-foot` style for the modal footer container (bottom padding, border-top, flex layout) and `.save-picker-new-game-btn` style for the "New Game" button (full-width, accent color, padding). The existing pack-picker-modal has no footer element — this is a new structural addition.

**Why:** Visual consistency with existing modal patterns. The pack-picker-modal currently has no footer; adding one requires new CSS since no existing styles cover it.

**Validation:** Save cards match pack picker card styling. Footer button styled appropriately.

### Tests to write or update

None — tests are temporarily removed during refactor.

---

## Documentation updates

- `docs/repomap.md` — Add `/api/saves` and `/api/switch-save` to routes section; add `clear_all_turn_locks()` to engine module; add `_list_saves()` to routes module
- `AGENTS.md` — No changes needed (no build/test command changes)
