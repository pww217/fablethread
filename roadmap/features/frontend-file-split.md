---
title: "[Frontend] Split monolithic index.html and app.src.css into domain files"
status: done
urgency: 3
size: medium
created: 2026-06-25
labels:
  - Frontend
  - Tech Debt
---

## Detail

`index.html` (2602 lines) and `app.src.css` (4467 lines) are monolithic files that combine template markup, game logic, rendering utilities, and styling for every surface. Split into domain-scoped files to improve readability for humans and LLM agents.

## Motivation

Files over 2500 lines are hard to navigate. The script block in `index.html` (~2100 lines) contains three distinct concerns (pure rendering utilities, the `game()` Alpine component, and DOM initialization wiring) that are conceptually independent. The CSS has a clear separation between the main game surface and the standalone turn-viewer page.

## Split Plan

### `index.html` (2602 → 3 files)

| New file | Lines | Content |
|----------|-------|---------|
| `index.html` | ~460 | Jinja2 template markup only (header, body layout, sidebars, modals) |
| `static/game-utils.js` | ~700 | Pure functions: markdown rendering, entity highlighting, outcome badges, progress strip, display drain, tooltips, metrics formatting, change line grouping |
| `static/game.js` | ~700 | `game()` Alpine component: panel state, drawers, pack picker, new game flows, turn submission/streaming, settings |
| `static/app-init.js` | ~400 | `charCreation` + `worldBuilder` Alpine components, `initTurnLogUi`, DOMContentLoaded wiring (health check, card persistence, htmx handlers, pills, gutters, hints) |

### `app.src.css` (4467 → 4 files)

| New file | Lines | Content |
|----------|-------|---------|
| `static/tokens.css` | ~55 | Design tokens, base reset, fluid typography |
| `static/app-shell.css` | ~2700 | Shell layout, header, narrative, input bar, sidebars, cards, sidebar content, modals, settings panel, responsive, entity highlighting, landing page |
| `static/turn-viewer.css` | ~1320 | Standalone full-page debug view (line 2592+) |
| `static/chronicle.css` | ~390 | Chronicle/turn-log overlay |

### Build integration

Keep `app.src.css` as the monolithic entry point (unchanged). The 4 CSS files are extracted alongside it for human readability. Tailwind v4 CLI does not support `@import` resolution, so the split files are mirrors — the build input and output are byte-identical to pre-split. No build step changes.

### Template changes

Replace the inline `<script>` block in `index.html` with three script tags (in `<head>`, using `defer` to match vendor script pattern):
```html
<script defer src="/static/game-utils.js"></script>
<script defer src="/static/game.js"></script>
<script defer src="/static/app-init.js"></script>
```

## Risks

1. **Script load order** — `game-utils.js` must load before `game.js`, which must load before `app-init.js`. Same order as the current inline block.
2. **`window._gameInstance` references** — `app-init.js` references `window._gameInstance` extensively. Must load after `game.js` defines it.
3. **`Alpine.initTree()` calls** — `app-init.js` uses `Alpine.initTree()` for AJAX-injected modals. `Alpine` is already loaded in `<head>`. No risk.
4. **`_configureMarked()` timing** — idempotent, returns early if `marked` not loaded. No risk.
5. **CSS extraction** — `app.src.css` stays monolithic; split CSS files are mirrors for human readability. Tailwind v4 CLI doesn't resolve `@import`, so CDD approach avoids build changes entirely.

## Post-merge fix

The original split committed Jinja2 template syntax (`{{ }}`) directly inside `game.js`, which is served as a static file and never processed by Jinja2. This caused a JavaScript syntax error that broke all Alpine initialization (`game is not defined`).

Fix: moved Jinja2-rendered initialization values into a small inline `<script>` block at the top of `<head>` that defines `window.__CCYA_INITIAL_STATE__`, then had `game.js` read from that object. Also reordered scripts so `game.js` loads before Alpine (Alpine was loading first and trying to evaluate `x-data="game()"` before the function was defined).

## Follow-up fix: SSE panel updates

The frontend file split also broke mid-turn SSE panel updates. All extraction results (NPC position changes, inventory updates, condition changes) were only visible at `turn_complete`, not incrementally after each extraction stream.

**Root causes:**

1. **No `panel_update` listener in `game.js`** — The pipeline yielded `panel_update` events after each stream, but the frontend had no handler. Events were silently dropped.

2. **`panel_update` events carried pre-mutation state** — The state dict wasn't updated with extraction results until `_apply_state_updates` in `turn.py` (after all 3 streams). Position changes from scene extraction weren't visible in panel_update data.

3. **`apply_delta` returns a new dict, never mutates in-place** — Building a preview state with `apply_delta` required capturing the return value. Discarding it left the preview unmodified.

4. **`StateDelta` validators rejected the event** — `inventory_change_reason` and `condition_change_reason` are required when there are inventory/condition changes. Missing them caused `ValueError`, which was swallowed by the outer exception handler in `turn.py`, silently aborting all state panel updates.

5. **Manual inventory/condition application was buggy** — `inventory_remove` has an `amount` field (`amount: 1` means "subtract 1", not "remove entire stack"). Manual code ignored `amount`, so ammo stacks disappeared mid-turn.

6. **Location changes come from state extractor** — The state panel_update didn't include location data, so location changes weren't visible until turn end.

**Fix:** Apply extraction results to a deep-copied preview state per-stream using the real `apply_delta` function, then yield `panel_update` events with the preview data. Frontend `panel_update` listener renders DOM directly from event data. Added `_renderInventoryItem`, `_renderConditionPill`, `_renderNpcListItem` helpers.

**Commit:** `4a4e60e`

**Files changed:**
- `ccya/engine/extraction/pipeline.py`
- `ccya/static/game.js`
- `ccya/static/game-utils.js`

## Systems Affected

* — `ccya/templates/index.html`
* — `ccya/static/game-utils.js` (new)
* — `ccya/static/game.js` (new)
* — `ccya/static/app-init.js` (new)
* — `ccya/static/tokens.css` (new)
* — `ccya/static/app-shell.css` (new)
* — `ccya/static/turn-viewer.css` (new)
* — `ccya/static/chronicle.css` (new)

## Done when

* All 7 new files exist in `ccya/static/`
* `index.html` loads the 3 new JS files via `<script>` tags (inline block removed)
* `app.src.css` stays monolithic — 4 CSS files extracted alongside it for human readability (build unchanged)
* No functional changes — same behavior, same network requests (1 CSS + 3 JS vs 1 CSS + 1 inline script)
* `make check` passes
