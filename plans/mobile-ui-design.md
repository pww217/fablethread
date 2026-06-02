# Mobile-Friendly Main UI — Design

## Purpose

This document is the design authority for transforming the main game UI (`index.html`) into a mobile-friendly page while keeping the desktop experience unchanged. It covers layout, touch targets, sidebar behavior, header simplification, and modal sizing for viewports ≤ 768px wide.

## Problem Statement

The current UI is a three-column desktop layout (left sidebar | narrative | right sidebar) with a single 900px responsive breakpoint that simply stacks the three columns vertically. On mobile:

- Sidebars consume most of the viewport (each capped at 40vh but still push narrative down)
- Gutter drag-resize handles are 4px — unusable on touch, and `_setupGutterResize()` registers `mousedown`/`mousemove`/`mouseup` only — no `touchstart`/`touchmove`
- Header has 5+ buttons + turn counter — overflows at 375px width
- Action pills (`padding: 5px 14px`) and header buttons (`padding: 5px 12px`) are below the 44px minimum touch target
- Sidebar `<details>` card density (8 cards across both panels) is overwhelming in stacked 40vh containers
- No `env(safe-area-inset-*)` for notched phones

## Constraints

- **No SPA, no npm, no build step.** App is server-rendered Jinja2 + htmx + Alpine.js. All changes must be CSS + inline JS in `index.html` and `app.src.css`.
- **No backwards compatibility required.** Old mobile behavior (stacked layout) is replaced entirely. Desktop experience must remain identical — no regression on viewports > 768px.
- **Minimal JS.** Leverage existing Alpine.js `game()` component. Add ~30 lines of new JS for drawer toggles and the resize-boundary watcher.
- **8k token context limit** for working sessions.

## Non-goals

- Touch/swipe gestures beyond basic drawer open/close
- Mobile browser chrome / homescreen / PWA
- Landscape/tablet optimization beyond the 768px drawer boundary
- Changing sidebar card content or structure (Scene, Location, Arc, Compendium, Player, Inventory, World State, Debug — all stay as `<details>`)
- Server-side changes (no routes, panels, templates other than `index.html`, no Python)
- Turn viewer (`_turn_viewer.html`) — explicitly excluded
- Turn log / chronicle overlay — it already works as an absolute overlay on `.narrative-column` (position: relative; turn-log-panel anchored with inset: 16px)
- Light mode or theme changes

## Current State — What Exists

### Layout (`index.html` + `app.src.css` line 15–203)

DOM structure:
```
.app-shell (flex column, 100vh)
  └── .header-bar (flex row, padding: 10px 20px, gap: 12px)
  └── .app-body (flex, flex:1, overflow:hidden)
        ├── .sidebar.sidebar-left (width: var(--sidebar-w)=320px, overflow-y:auto, border-right)
        ├── .gutter.gutter-left (4px, cursor:col-resize, background:transparent → accent-soft on hover)
        ├── .narrative-column (flex:1, min-width:0, overflow:hidden) ← position:relative for turn-log overlay
        ├── .gutter.gutter-right
        └── .sidebar (width: var(--sidebar-w), border-left)
```

Sidebar resize behavior (`game()` Alpine component, `index.html` lines 724–790):
- Width stored in `Alpine.leftW`/`Alpine.rightW`, persisted in `localStorage` as `ccya_panel_left_w`/`ccya_panel_right_w`
- Collapse: set `leftW`/`rightW` to `null`, `leftCollapsed`/`rightCollapsed` to `true`, CSS becomes `width: 0; overflow: hidden`
- Restore via edge-click (`onSidebarClick` checks `clientX` within 12px of sidebar edge, or auto-toggles on `window.innerWidth <= 900`)
- Gutter drag: `_setupGutterResize()` — `mousedown`/`mousemove`/`mouseup` only, no touch events (`app.src.css` line 432)
- Collapsed-panel hints: `.gutter-hint` (position: fixed, 3px×40vh, opacity:0→1 on mouse proximity to left/right 20px zone) — desktop only

Existing single responsive breakpoint (`app.src.css` line 1675, `@media (max-width: 900px)`):
- `.app-body` → `flex-direction: column`
- `.narrative-panel` padding → `20px 22px` (was `32px 40px`)
- `.pills-row`, `.input-bar` padding → `22px` (was `40px`)
- `.sidebar-left` → `width: 100%; border-right: none; border-bottom: 1px solid var(--border-subtle); max-height: 40vh`
- `.sidebar:not(.sidebar-left)` → `width: 100%; border-left: none; border-top: 1px solid var(--border-subtle); max-height: 40vh`
- `.turn-counter` → `display: none`
- `.header-logo` → `font-size: 13px; max-width: 55vw`

### Header (`index.html` lines 18–51)

Elements left to right: `.header-logo` (flex:1, font-size:14px, font-weight:700, accent color) | `.turn-log-toggle` (blue pill with 📖 Chronicle, `padding: 5px 14px`) | `.mock-dot` (8px circle) | `.turn-counter` | Retry button (↻ Retry, `padding: 5px 12px`) | New Game button | Roll Again button.

### Modals

| Modal | CSS | Size |
|---|---|---|
| Pack picker (`app.src.css` line 1378) | `position: fixed; left:50%; top:50%; transform:translate(-50%,-50%)` | `width: min(580px, 94vw)`, `max-height: min(80vh, 640px)` |
| Character creation | Same modal shell, swaps content via HTMX | Same |
| World builder | Same modal shell, swaps content via HTMX | Same |
| Game over (`app.src.css` line 1710) | `position: fixed; left:50%; top:50%; transform:translate(-50%,-50%)` | `width: min(400px, 90vw)` |

### Sidebar content structure

**Left sidebar** `_state_left.html` (146 lines):
- `<details>` Scene (present NPCs with tooltip bios)
- `<details>` Location (name + description)
- `<details>` Arc (visible_goal with goal_context tooltip, active threads with urgency styling, completed threads, resolved arcs)
- `<details>` Compendium (all known NPCs with tooltip bios/motivations/bonds)

**Right sidebar** `_state_right.html` (93 lines):
- `<details>` Player (name, tagline, stats grid 2×3, condition pills)
- `<details>` Inventory (items with amounts, credits pinned to top)
- `<details>` World State (persistent + permanent facts)
- `<details>` Debug (performance metrics, errors)
- `.sidebar-meta-footer` (turn number, model name)

### Problems with Current State

1. **900px breakpoint is too coarse for true mobile.** The stacked layout at 600px is just as broken as at 899px. A phone (375–414px) makes both sidebars unusable at 40vh each — the narrative column gets squeezed between them.
2. **No touch-friendly drawer mechanism.** Collapsing to `width: 0; overflow: hidden` leaves no visible affordance to restore. Mobile users cannot open a collapsed sidebar — the edge-click zone is invisible and the gutter hints (`pointer-events: none`) are not tappable.
3. **Header overflows on small screens.** At 375px width, 5+ buttons + logo + dot + counter exceed the viewport.
4. **Gutters are mouse-only.** `_setupGutterResize()` uses `mousedown`/`mousemove`/`mouseup` with no `touchstart`/`touchmove` fallback. On mobile they render as inert 4px columns.
5. **Sidebar card density exceeds mobile inline capacity.** 8 `<details>` cards inside a 40vh container with `overflow-y: auto` makes the narrative a secondary concern.
6. **No `env(safe-area-inset-*)`** for notched or home-indicator phones.
7. **`game-input` font-size is 14px** — iOS Safari will zoom the page on focus because the font-size is below 16px.

## Proposed Solution

### Core Changes

#### 1. Existing 900px Breakpoint → 768px Breakpoint with Drawers

Replace the existing `@media (max-width: 900px)` block with `@media (max-width: 768px)`. The layout rules change from "stack vertically" to "fixed overlay drawers."

The existing inline sidebar layout at 769–900px is already acceptable (it's the same as desktop but slightly narrower). No changes needed for that range.

**Drawer CSS** (new block inside `@media (max-width: 768px)`):

```css
@media (max-width: 768px) {
  /* ── Hide desktop-only elements ── */
  .gutter { display: none; }
  .gutter-hint { display: none; }
  .mock-dot { display: none; }
  .turn-counter { display: none; }
  .reroll-btn { display: none; }
  .sidebar-toggle--desktop { display: none; }

  /* ── Header ── */
  .header-bar {
    padding: 8px 12px;
    padding-left: max(12px, env(safe-area-inset-left));
    padding-right: max(12px, env(safe-area-inset-right));
    gap: 8px;
  }
  .header-logo { font-size: 13px; max-width: 40vw; }
  .header-meta { gap: 6px; }
  .new-game-btn { padding: 6px 10px; font-size: 13px; min-height: 36px; }
  .turn-log-toggle { font-size: 0; padding: 5px 10px; min-height: 36px; min-width: 36px; justify-content: center; }
  .turn-log-toggle-label { font-size: 18px; } /* 📖 only */

  /* ── Sidebar drawer toggles (header buttons) ── */
  .sidebar-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: transparent;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 18px;
    flex-shrink: 0;
    -webkit-tap-highlight-color: transparent;
    transition: border-color 120ms, color 120ms;
    padding: 0;
  }
  .sidebar-toggle:hover { border-color: var(--border-strong); color: var(--text-primary); }
  .sidebar-toggle[aria-expanded="true"] { border-color: var(--accent); color: var(--accent); }

  /* ── Drawer overlay layout ── */
  .sidebar {
    position: fixed;
    top: 0;
    z-index: 8000;
    height: 100dvh;
    width: min(320px, 85vw);
    transform: translateX(-100%);
    transition: transform 220ms ease;
    border: none;
    box-shadow: 4px 0 24px rgba(0,0,0,0.5);
    overflow-y: auto;
    overscroll-behavior: contain;
    /* preserve --sidebar-w for backward compat but override width here */
  }
  .sidebar-left {
    left: 0;
    border-right: none;
  }
  .sidebar:not(.sidebar-left) {
    right: 0;
    transform: translateX(100%);
    border-left: none;
    box-shadow: -4px 0 24px rgba(0,0,0,0.5);
  }
  .sidebar.sidebar--open {
    transform: translateX(0);
  }
  /* No-op the existing @click.self on sidebar — backdrop handles close */
  .sidebar { pointer-events: auto; }

  /* ── Drawer backdrop ── */
  .sidebar-backdrop {
    position: fixed;
    inset: 0;
    z-index: 7500;
    background: rgba(0, 0, 0, 0.5);
  }

  /* ── Narrative column ── */
  .narrative-panel { padding: 16px; }
  .pills-row {
    padding: 8px 16px;
    padding-bottom: max(8px, env(safe-area-inset-bottom));
  }
  .input-bar {
    padding: 10px 16px;
    padding-bottom: max(10px, env(safe-area-inset-bottom));
  }
  .narrative-block { padding-left: 12px; margin-bottom: 24px; }
  .narrative-text { font-size: 16px; }

  /* ── Touch targets ── */
  .action-pill {
    padding: 10px 16px;
    font-size: 14px;
    min-height: 44px;
  }
  .send-btn {
    padding: 0 18px;
    min-height: 44px;
    height: auto;
  }
  .game-input {
    min-height: 44px;
    font-size: 16px; /* prevent iOS zoom on focus */
  }

  /* ── Progress strip wrapping ── */
  .progress-strip { flex-wrap: wrap; gap: 4px; }

  /* ── Modals: fullscreen ── */
  .pack-picker-modal {
    width: 100vw;
    width: 100dvw;
    height: 100dvh;
    left: 0;
    top: 0;
    transform: none;
    border-radius: 0;
    border: none;
    max-width: none;
    max-height: none;
  }
  .pack-picker-backdrop { display: none !important; }
  .pack-picker-head {
    padding-top: max(12px, env(safe-area-inset-top));
    padding-left: max(16px, env(safe-area-inset-left));
    padding-right: max(16px, env(safe-area-inset-right));
  }
  .pack-picker-body { height: calc(100dvh - 52px); }
  .game-over-modal {
    width: 90vw;
    padding: 24px 20px;
  }

  /* ── Turn log / chronicle: fullscreen ── */
  .turn-log-panel {
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 0;
    border: none;
  }
  .turn-log-backdrop { display: none; } /* panel is edge-to-edge, no backdrop needed */

  /* ── Sidebar cards ── */
  .sidebar-meta-footer { padding: 6px 12px; }
}
```

#### 2. Alpine.js Additions to `game()` Component

Add to the existing `game()` return object (after `rightCollapsed`):

```javascript
leftDrawerOpen: false,
rightDrawerOpen: false,

toggleDrawer(side) {
  const key = side + 'DrawerOpen';
  this[key] = !this[key];
  document.body.style.overflow = this[key] ? 'hidden' : '';
},

closeDrawer(side) {
  const key = side + 'DrawerOpen';
  if (this[key]) {
    this[key] = false;
    document.body.style.overflow = '';
  }
},
```

Add a `resize` listener in `init()`:

```javascript
// Close drawers when crossing the 768px boundary
this._drawerBoundary = window.matchMedia('(max-width: 768px)');
this._drawerBoundary.addEventListener('change', (e) => {
  if (!e.matches) {
    this.leftDrawerOpen = false;
    this.rightDrawerOpen = false;
    document.body.style.overflow = '';
  }
});
```

#### 3. DOM Additions to `index.html`

**Two toggle buttons** in the header (between logo and chronicle button):

```html
<button class="sidebar-toggle sidebar-toggle--left"
        @click="toggleDrawer('left')"
        :aria-expanded="leftDrawerOpen"
        title="Open left panel"
        type="button">☰</button>
<button class="sidebar-toggle sidebar-toggle--right"
        @click="toggleDrawer('right')"
        :aria-expanded="rightDrawerOpen"
        title="Open right panel"
        type="button">≡</button>
```

**Drawer backdrop** (before `.app-body`, or at end of `.app-shell`):

```html
<div class="sidebar-backdrop"
     x-show="leftDrawerOpen || rightDrawerOpen"
     x-transition.opacity.duration.200ms
     @click="closeDrawer('left'); closeDrawer('right')"></div>
```

Note: `x-show` manages `display` on the backdrop — no CSS `display` rules needed. `x-transition` is part of core Alpine (no plugin required). The `.sidebar-backdrop` CSS class only provides positioning, z-index, and background color.

**`onSidebarClick` suppressed on mobile.** Add a width guard at the top of the existing `onSidebarClick(side, e)` method in the Alpine `game()` component:

```javascript
onSidebarClick(side, e) {
  // Mobile uses drawer toggles — suppress edge-click/auto-collapse
  if (window.innerWidth <= 768) return;
  // … existing body unchanged …
},
```

`@click.self` on `.sidebar` remains in the DOM — on desktop it fires the existing collapse/restore logic; on mobile the early return makes it a no-op. The backdrop handles drawer closing.

#### 4. Sidebar Backdrop Z-Index Layering

```
z-index: 7500  →  .sidebar-backdrop
z-index: 8000  →  .sidebar (drawer)
z-index: 9400  →  .pack-picker-backdrop
z-index: 9500  →  .pack-picker-modal
z-index: 9600  →  .game-over-backdrop
z-index: 9700  →  .game-over-modal
```

This places drawers below all modals, which is correct — if a modal opens, it should be on top of any drawer.

#### 5. Turn Log / Chronicle

On mobile, the turn log panel goes edge-to-edge (no inset, no border-radius, no backdrop). The panel already has a head with close button and scrollable body. The `initTurnLogUi()` function in `index.html` needs no changes — it toggles `hidden` on `.turn-log-shell` which remains an absolute overlay on `.narrative-column`.

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| **Bottom tab bar** (Narrative / Character / World / Map tabs) | Significant JS complexity to restructure sidebar content into tab views. Deviates from desktop UX. Too heavy for the value. |
| **Accordion sidebar** (single sidebar with tab buttons to switch left/right content) | Cheaper than drawers, but breaks the two-panel mental model (left=world/scene, right=character/inventory). Users expect both available. |
| **Keep stacked layout with improved breakpoints** | The 40vh cap per sidebar still buries the narrative. Root problem is content density, not layout order. |
| **Swipe gesture library** | Overkill. The app has no other swipe interactions. A simple backdrop + button toggle is robust. The edge-click zone on the old collapse mechanism is invisible and mobile-unfriendly. |
| **Drawer at 600px** | 768px covers portrait tablets (iPad Mini is 744px). Above 768px the inline layout is serviceable; below it's definitively broken. |

## Decision Table

| Decision | What | Why |
|---|---|---|
| Drawer sidebar on ≤ 768px | Sidebars become fixed overlay panels (`transform: translateX`), toggled by header buttons, closed by backdrop click | Preserves 8 cards' worth of content without layout fight; touch-friendly; no swipe library needed |
| Desktop unchanged | No change to `.sidebar` inline layout, gutter resize, edge-click collapse, or `localStorage` persistence above 768px | Zero regression risk for desktop users |
| Session-only drawer state | No `localStorage` for drawer open/close; Alpine booleans `leftDrawerOpen`/`rightDrawerOpen` reset on page load | Drawers are ephemeral — no value remembering which was last open |
| Old 900px breakpoint changed to 768px | The existing `@media (max-width: 900px)` block's contents are replaced by drawer CSS. `turn-counter` hiding and `header-logo` shrinking move to the new 768px block | Clean line: 769px+ is desktop, ≤768px is mobile with drawers |
| Header simplification on mobile | Hide `.mock-dot`, `.turn-counter`, `.reroll-btn`; collapse Chronicle button to 📖 icon only; add two 36px drawer toggle buttons | Frees horizontal space for essential controls — 5+ items don't fit at 375px |
| Gutter resizers hidden on mobile | `.gutter { display: none }` at ≤ 768px | Mouse-only events (`mousedown`/`mousemove`/`mouseup`), no touch support, meaningfully fixing touch support isn't worth it |
| Chronicle overlay goes fullscreen | `.turn-log-panel` becomes `inset: 0; border-radius: 0; border: none;` | More reading room; backdrop is redundant when panel is edge-to-edge |
| Modals go fullscreen on mobile | Pack picker / char creation / world builder become `100vw × 100dvh`, `border-radius: 0` | Eliminates double-scrollbar; modal content already scrollable |
| `font-size: 16px` on textarea | `.game-input { font-size: 16px; }` on mobile | Prevents iOS Safari auto-zoom on focus |
| `env(safe-area-inset-*)` | Apply to header, sidebar, input-bar, pack-picker-head padding | Notched phone / home indicator compatibility |
| Resize boundary watcher | Alpine init adds `matchMedia('(max-width: 768px)')` listener that closes drawers when crossing up to >768px | Prevents stale drawer state when rotating from portrait to landscape on a large phone |
| `body.style.overflow = 'hidden'` when drawer open | Prevents background scroll behind the drawer | Standard drawer UX pattern |
| `onSidebarClick` returns early on mobile | Guard clause: `if (window.innerWidth <= 768) return;` at top of existing method | Prevents old collapse mechanism from firing underneath drawer mode; drawer toggle buttons + backdrop handle everything |

## Failure Modes and Risks

1. **Sidebar backdrop intercepts narrative clicks.** The backdrop `z-index: 7500` is below sidebar (`8000`) but above narrative content. The `x-show` directive with `x-transition.opacity` ensures it appears/disappears with the drawer. Backdrop has `@click` handler to close both drawers.
2. **Drawer open on orientation change → resize above 768px.** Mitigated by the `matchMedia` listener in `init()` — if the media query no longer matches, both drawers are closed and body scroll restored.
3. **Chronicle button + drawer toggles overflow at ≤ 360px.** At 360px: logo (~40vw = 144px) + 2 toggle buttons (2×36px = 72px) + chronicle icon (36px) + new game button (~60px) = ~312px. Fits. The gap-8px adds some stretch but should fit within 360px. If not, the sidebar toggles could be merged into a single button that opens an overflow menu.
4. **`dvh` units not supported on older mobile browsers.** `100dvh` gracefully falls back to `100vh` on browsers that don't support it. The difference is minor (address bar height).
5. **Turn log backdrop hidden on mobile.** The `.turn-log-backdrop` is hidden on mobile because the panel is edge-to-edge. If the user needs to dismiss the chronicle, the close button in `.turn-log-head` is always available.
6. **Pack-picker body height calc with fullscreen modal.** `height: calc(100dvh - 52px)` assumes `.pack-picker-head` is ~52px tall. The head has `padding: 12px 16px` + content. 52px is a safe estimate.
7. ~~Auto-collapse `onSidebarClick` on mobile.~~ **Resolved.** `onSidebarClick` now returns early when `window.innerWidth <= 768`, so it's a no-op on mobile.

## Open Questions

None remaining. The two questions from the initial draft were resolved:
- Breakpoint: 768px (accepted)
- Chronicle overlay on mobile: fullscreen (accepted)

## What Is Removed

The existing `@media (max-width: 900px)` CSS block's contents are not removed — they are repurposed. The new `@media (max-width: 768px)` block replaces the stacking behavior with drawer behavior. Specifically, the old rules that are removed:

| Removed | From | Notes |
|---|---|---|
| `.app-body { flex-direction: column; }` at ≤ 768px | `app.src.css` line 1677 | No longer needed — sidebars are fixed overlays, not inline columns |
| `.sidebar-left { width: 100%; max-height: 40vh; border-right: none; border-bottom: ... }` at ≤ 768px | `app.src.css` lines 1681–1686 | Replaced by fixed drawer CSS |
| `.sidebar:not(.sidebar-left) { width: 100%; max-height: 40vh; border-left: none; border-top: ... }` at ≤ 768px | `app.src.css` lines 1687–1692 | Replaced by fixed drawer CSS |
| `.gutter` visibility on mobile | `app.src.css` line 432 | `.gutter { display: none; }` at ≤ 768px |
| `.gutter-hint` visibility on mobile | `app.src.css` line 445 | `.gutter-hint { display: none; }` at ≤ 768px |
| `.mock-dot` visibility on mobile | `index.html` line 24 | `.mock-dot { display: none; }` at ≤ 768px |
| `.turn-counter` visibility on mobile | `index.html` line 25 | `.turn-counter { display: none; }` at ≤ 768px (moved from old 900px block) |
| `.reroll-btn` visibility on mobile | `index.html` line 39 | `.reroll-btn { display: none; }` at ≤ 768px |
| Desktop `.turn-log-panel` inset styling on mobile | `app.src.css` line 734 | `.turn-log-panel { top:0; left:0; right:0; bottom:0; border-radius:0; border:none; }` overrides |

## What Is Unchanged

- All server-side code (routes, panels, templates, models, Python)
- Narrative streaming, display drain, progress indicators, roll badges, action pills, turn metrics (`submitTurn()`, `_startDisplayDrain()`, `_buildRollBadge()`, `_formatMetricsRow()`)
- Turn log overlay logic (`initTurnLogUi()` — toggle, close, refresh, keyboard Escape)
- Tooltip portal and tooltip behavior (`_bindTooltips()`, `_tooltipShow()`, `_tooltipHide()`)
- `_state_left.html` and `_state_right.html` card content and structure (all 8 `<details>` cards)
- Character creation flow (`charCreation()` Alpine component)
- World builder flow (`worldBuilder()` Alpine component)
- Pack picker logic (modal card clicks, delete handlers, start game flow)
- `stopTurn()`, `retryTurn()`, `fillFromChoice()` — no changes
- Desktop sidebar collapse/resize/persistence infrastructure (`leftW`, `rightW`, `leftCollapsed`, `rightCollapsed`, `initGutters()`, `_setupGutterResize()`) — unchanged, still the code path on viewports > 768px
- Desktop `.gutter` resize behavior — still active above 768px
- CSS design tokens (`:root` variables), color scheme, typography
- `.sidebar-card` open/close `localStorage` persistence (`applyCardOpenStateFromStorage()`, toggle listener)
- `.sidebar-meta-footer` — still renders inside the right sidebar drawer
- Game-over modal — minor width change (`90vw` already in use), no structural change

## Context for Implementing LLMs

| File | Why it matters |
|---|---|
| `ccya/templates/index.html` | Full DOM structure — header, sidebar toggle buttons, sidebar backdrop element, and Alpine `game()` component additions go here. All changes are within this file. |
| `ccya/static/app.src.css` | All responsive rules, drawer CSS, touch target sizing, safe-area insets, fullscreen modals — largest change surface. The entire `@media (max-width: 768px)` block is new. |
| `ccya/static/app.css` | Compiled output — must be regenerated from `app.src.css` (run `make css` or the relevant PostCSS build step). |
| `docs/repomap.md` | Confirms no server-side changes needed; confirms `index.html` structure and `game()` component boundaries. |
