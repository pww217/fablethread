---
title: "[Frontend] Split monolithic index.html and app.src.css into domain files"
status: validated
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
