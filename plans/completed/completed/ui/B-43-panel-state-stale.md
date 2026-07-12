# Plan: B-43 — Left panel (scene/NPCs) not updating correctly after turn ends

## Design Reference

- **Bug:** `roadmap/bugs/panel-state-stale.md`
- **Validation:** Hand-read source files, confirmed all three root causes, zero engine changes

## Problem Statement

After a turn ends, the left state panel (scene NPCs with present/nearby distinction, objective, compendium) does not reflect the actual post-extraction state. Specifically: (1) the `world_done` handler only re-fetches the right panel, (2) a premature HTMX re-fetch during arc panel_update reads stale pre-turn data and overwrites scene updates, and (3) scene panel updates miss post-delta NPC lifecycle decay (`nearby→known`, `departed→archived`).

## Root Cause Summary

Three issues in the UI's event handling flow:

1. **`world_done` re-fetches only right panel** — `game.js:903` missing `/panels/state-left` re-fetch
2. **Arc `panel_update` triggers stale HTMX re-render** — `game.js:982` calls HTMX AJAX during extraction when `state.yaml` still has pre-turn data
3. **Scene `panel_update` misses post-delta decay** — JS panel_update uses pre-apply state; NPC decay runs in `_apply_state_updates()` after extraction

All three are purely UI-side (SSE event handling ordering). Zero engine changes required.

## Scope

**Single phase:** One file (`ccya/static/game.js`), three targeted changes to the SSE event handler chain.

| Change | Line | What | Problem solved |
|--------|------|------|----------------|
| A | ~982 | Suppress premature HTMX re-fetch in arc handler | Fixes issue 2 |
| B | ~1070 | Add left panel re-fetch in turn_complete | Fixes issues 1 + 3 |
| C | ~903 | Remove left panel re-fetch from world_done | Avoids redundant re-fetch |

No engine, template, or route changes needed.

---

## Phase 01: Fix left panel re-sync ordering

### Depends on

None

### Context files to load

- `ccya/static/game.js:899-916` — `world_done` SSE handler
- `ccya/static/game.js:924-984` — `panel_update` SSE handler
- `ccya/static/game.js:986-1080` — `turn_complete` SSE handler
- `ccya/static/game-utils.js:835-857` — `_renderNpcListItem()` (used by existing scene panel JS)
- `ccya/templates/_state_left.html:1-205` — left panel template (what HTMX re-fetch renders)
- `ccya/server/routes.py:598-604` — `/panels/state-left` route (reads `state.yaml` via `_load_current_state()`)
- `ccya/engine/turn.py:728-749` — where `state_snapshot` is captured (post-apply, pre-async)
- `ccya/engine/turn.py:832` — where `save_state()` writes `state.yaml` (before `world_done`)
- `ccya/engine/turn_state.py:661-676` — NPC lifecycle decay (`nearby→known`, `departed→archived`)

### What changes

Three changes to `ccya/static/game.js`. All in the SSE event handler chain. No engine changes.

### Where to change: A — Suppress stale arc panel_update re-fetch

**File:** `ccya/static/game.js:981-982`

**Before (current):**
```js
} else if (data.panel === 'arc' && data.data) {
    htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
}
```

**After:**
```js
} else if (data.panel === 'arc' && data.data) {
    // Arc data synced via HTMX re-fetch at turn_complete. No early re-render needed.
}
```

**Why:** The arc panel_update fires during extraction when `state.yaml` on disk still has pre-turn data. This HTMX call reads stale state and overwrites the JS-rendered scene NPC updates (which were written via `innerHTML` at line 934). The arc's objective/thread data will sync correctly via the turn_complete HTMMX re-fetch.

### Where to change: B — Add left panel re-fetch in turn_complete

**File:** `ccya/static/game.js`

**Location:** Inside the `turn_complete` handler (lines 986-1080), after `this.submitting = false` (line 1072) and before the close-to-input logic (line 1076). Specifically: insert after line 1072 (`this.submitting = false;`).

**Before (current):**
```js
                _prependTurnLogTurn(result.turn, result.change_lines || [], result.ruling);

                this.submitting = false;

                if (result.game_over) {
```

**After:**
```js
                _prependTurnLogTurn(result.turn, result.change_lines || [], result.ruling);

                this.submitting = false;

                // Re-render left panel now that state.yaml has post-extraction state
                // (compendium with NPC presence, location, objective, compendium).
                // This syncs scene NPCs (issue 1: left panel never updated),
                // objective threads (from record extraction), compendium, and the
                // NPC lifecycle decay that runs after extraction (issue 3).
                if (typeof htmx !== 'undefined') {
                    htmx.ajax('GET', '/panels/state-left', { target: '#state-panel-left' });
                }

                if (result.game_over) {
```

**Why:** This is the cure for all three issues:
- **Issue 3 (NPC decay):** `turn_complete`'s `state_snapshot` (turn.py:746) has post-apply state. By this point, `_apply_state_updates()` (turn_state.py:661-676) has run and applied NPC lifecycle decay. `save_state()` (turn.py:832) writes `state.yaml` before `world_done`. So when HTMX calls `/panels/state-left`, it reads the file with correct post-decay state.
- **Issue 1 (left panel stale):** Re-fetching the left panel at turn_complete ensures it reflects post-extraction state immediately.
- **Scene NPC flash:** Any flash from the premature arc handler (issue 2) gets overwritten by this clean re-render. The user sees one correct HTMX render for the entire left panel.

### Why not use result.state JSON for JS-only update instead of HTMX?

`result.state` in the `turn_complete` event (passsed from `TurnResult.state_snapshot.to_dict()` at routes.py:323) includes the compendium with correct NPC presence. However, the left panel template has complex rendering logic (present/nearby split, goal/threads/resolved threads, compendium entries with tooltips) that lives in `_state_left.html`. The existing `panel_update:scene` JS path only renders the present NPC list, not the full left panel (arc, compendium, etc.). HTMX re-fetch is the correct approach because it re-renders the complete left panel with all sections.

### Where to change: C — Remove redundant left panel re-fetch from world_done

**File:** `ccya/static/game.js:899-916`

**Before (current):**
```js
                if (payload && payload.phase === 'world_done') {
                    self.asyncRunning = false;
                    // Re-fetch state panels now that async window (sanitize + world) has completed
                    if (typeof htmx !== 'undefined') {
                        htmx.ajax('GET', '/panels/state-right', { target: '#state-panel-right' });
                    }
                    // Update metrics display with async step timings
                    if (payload.metrics) {
                        const met = document.querySelector('.turn-metrics');
                        if (met) met.textContent = _formatMetricsRow(payload.metrics);
                    }
                    es.close();
                    self._turnEs = null;
                    self._turnCancel = null;
                    if (window.innerWidth > 768) {
                        setTimeout(() => document.getElementById('player-input')?.focus(), 100);
                    }
                }
```

**After:**
```js
                if (payload && payload.phase === 'world_done') {
                    self.asyncRunning = false;
                    // Re-fetch right panel, now that async window (sanitize + world) has completed.
                    // Left panel was already re-fetched at turn_complete with post-extraction state.
                    if (typeof htmx !== 'undefined') {
                        htmx.ajax('GET', '/panels/state-right', { target: '#state-panel-right' });
                    }
                    // Update metrics display with async step timings
                    if (payload.metrics) {
                        const met = document.querySelector('.turn-metrics');
                        if (met) met.textContent = _formatMetricsRow(payload.metrics);
                    }
                    es.close();
                    self._turnEs = null;
                    self._turnCancel = null;
                    if (window.innerWidth > 768) {
                        setTimeout(() => document.getElementById('player-input')?.focus(), 100);
                    }
                }
```

**Why:** The left panel was already re-rendered at turn_complete. Adding a second HTMX re-fetch at world_done would be redundant — and could cause an unwanted re-layout flash. The right panel re-fetch stays because it wasn't addressed by the turn_complete re-fetch (which only covers the left panel).

### Sequence of events after this fix

```
1. Extraction: panel_update:scene → JS innerHTML → present NPCs shown (pre-decay)
2. Extraction: panel_update:arc → NOOP (issue 2 fixed — no stale HTMX re-fetch)
3. Extraction: panel_update:state → JS innerHTML → inventory/PC updated
4. Extraction completes → delta applied → NPC decay applied (turn_state.py:661-676)
5. save_state() → state.yaml written
6. SSE: turn_complete → HTMX re-fetch /panels/state-left (issue 1+3 fixed)
   → full left panel re-rendered with correct decay state
7. Async window: sanitize + world step (mutates state.yaml)
8. SSE: world_done → HTMX re-fetch /panels/state-right only
   → right panel shows post-async state
   → left panel already correct from step 6
```

### Why

Post-extraction state with correct NPC presence values renders too late (or not at all) because:
- The arc handler's premature HTMX re-fetch (issue 2) rewrites the JS-rendered scene panel with stale pre-turn data
- The `world_done` handler (issue 1) never re-fetches the left panel at all
- The extraction-time `panel_update` (issue 3) doesn't include post-delta NPC decay

The fix reorders and deduplicates HTMX re-fetches so the left panel gets one clean re-render at the earliest safe point (turn_complete) and the right panel gets its own re-render at world_done (where it's the only panel being updated).

### Validation

- `make check` passes — no syntax or lint issues
- Run a turn with a known NPC becoming present. The scene panel should show the NPC with no flicker
- Run a turn where an NPC should decay (`nearby` for 2+ turns). The NPC should not appear in the scene panel
- The compendium cards (all NPCs, presence in tooltip) should appear correctly after HTMX re-render
- Objective threads should remain stable during the re-render

---

## Documentation updates

- **`docs/repomap.md`** — Update "SSE event emission" and "UI panel rendering" sections to reflect the corrected turn_complete → HTMX re-fetch flow and the removal of the arc panel_update re-render trigger
- No `docs/architecture/` changes needed — the pipeline flow is unchanged; only the UI event handling is modified

---

## Status

Completed. Three changes to `game.js`: suppressed premature arc panel_update re-fetch, added left panel HTMX re-fetch at turn_complete, updated world_done comment. `make check` passes. No deviations.
