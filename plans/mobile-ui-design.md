# Mobile-Friendly Main UI — Design

## Purpose

This document is the design authority for the mobile UI of `index.html`. It covers layout, header simplification, drawer behavior, touch targets, modal sizing, and swipe gestures at viewports ≤ 768px. Desktop experience (>768px) is unchanged.

---

## Current State — What Exists

### Layout (`index.html` + `app.src.css`)

DOM structure (all viewports):

```
.app-shell (flex column, 100vh)
  ├── .header-bar (flex row, padding: 10px 20px, gap: 12px)
  ├── .app-body (flex, flex:1, overflow:hidden)
  │     ├── .sidebar.sidebar-left (width: var(--sidebar-w)=320px, overflow-y:auto, border-right)
  │     ├── .gutter.gutter-left (4px, cursor:col-resize)
  │     ├── .narrative-column (flex:1, min-width:0, overflow:hidden)
  │     ├── .gutter.gutter-right
  │     └── .sidebar (width: var(--sidebar-w), border-left)
  └── .sidebar-backdrop (mobile only, x-show when drawer open)
```

### Header (`index.html` lines 17–86)

Elements left to right:

| Element | Class | Sizing | Notes |
|---------|-------|--------|-------|
| Scene tagline | `.header-logo` | `flex:1` | Hidden on mobile (`display:none`) |
| Player button | `.sidebar-toggle.sidebar-toggle--right` | 36px height, padding 0 10px | Toggles right drawer; shows `←` before text |
| Chronicle | `#turn-log-toggle` | `flex:1`, centered | Icon-only on mobile (📖) |
| World button | `.sidebar-toggle.sidebar-toggle--left` | 36px height, padding 0 10px | Toggles left drawer; shows `→` after text |
| Meta group | `.header-meta` | `flex-basis: auto; flex-grow: 0` | Contains mock-dot, turn-counter, gear menu, Roll Again |

Button order in DOM: **Player → Chronicle → World** (left to right).

### Sidebar structure

**Left sidebar** = `_state_left.html` (Scene, Location, Arc, Compendium).
**Right sidebar** = `_state_right.html` (Player, Inventory, World State, Debug).

Each sidebar has a `.sidebar-close` button (✕) inside the drawer, sticky at the top.

### Sidebar behavior — desktop (`> 768px`)

- Inline layout: sidebars, gutters, narrative in a row.
- `localStorage`-persisted width + collapse state (`leftW`/`rightW`, `leftCollapsed`/`rightCollapsed`).
- Gutters with `mousedown`/`mousemove`/`mouseup` resize.
- Edge-click collapse (12px zone at outer edge).

### Mobile breakpoint (`≤ 768px`)

Single `@media (max-width: 768px)` block at `app.src.css` line 1759. Key behavior:

- Sidebars become fixed **full-screen drawers** (`100vw × 100dvh`), toggled by header buttons + backdrop.
- Gutters, mock-dot, turn-counter, reroll-btn all hidden.
- Touch-based swipe gesture (edge-swipe to open drawer).
- Modals & turn log go fullscreen.
- `body.style.overflow = 'hidden'` while a drawer is open.

---

## Implemented Solution

### 1. Breakpoint: ≤ 768px

`@media (max-width: 768px)` replaces the old `@media (max-width: 900px)`. Viewports 769px+ retain the desktop inline sidebar layout unmodified. Below 768px, sidebars become overlay drawers.

### 2. Header

On mobile:

| Change | Why |
|--------|-----|
| `.header-logo` → `display: none` | Scene tagline wastes header space; game title context is available in the `<title>` and narrative |
| `#turn-log-toggle` → `flex: 1; justify-content: center` | Centers chronicle pill perfectly between Player and World buttons |
| `.header-meta` → `flex-basis: auto; flex-grow: 0` | Prevents meta group from expanding and breaking chronicle centering |
| `.mock-dot`, `.turn-counter`, `.reroll-btn` → `display: none` | Essential declutter; gear menu replaces New Game / Roll Again |
| `.header-bar` padding → `8px 12px` with `env(safe-area-inset-*)` | Tighter fit with safe-area support |
| `.turn-log-toggle` → `font-size: 0; min-width: 36px` | Collapses to 📖 icon only |

### 3. Sidebar Drawer Toggles

Two buttons flanking the chronicle pill:

```html
<button class="sidebar-toggle sidebar-toggle--right" @click="toggleDrawer('right')"
        :aria-expanded="rightDrawerOpen" title="Open right panel" type="button">
  <span class="sidebar-toggle-label">Player</span>
</button>
<!-- Chronicle pill -->
<button class="sidebar-toggle sidebar-toggle--left" @click="toggleDrawer('left')"
        :aria-expanded="leftDrawerOpen" title="Open left panel" type="button">
  <span class="sidebar-toggle-label">World</span>
</button>
```

CSS pseudo-element arrows indicate drawer direction:

```
.sidebar-toggle--right::before → content: '←' (before label, points outward to right edge)
.sidebar-toggle--left::after  → content: '→' (after label, points outward to left edge)
```

- **Player** (right drawer opens from right side) → arrow ← on left side of button, pointing toward the right screen edge.
- **World** (left drawer opens from left side) → arrow → on right side of button, pointing toward the left screen edge.

Both arrows are `color: var(--accent); font-size: 16px` with 4px margin.

Toggle buttons themselves: `36px height, padding: 0 10px, transparent bg, border-subtle, border-radius var(--radius-sm)`.

### 4. Full-Screen Drawers

Not 320px partial drawers. Full-screen (`100vw × 100dvh`).

```css
.sidebar {
  position: fixed;
  top: 0;
  z-index: 8000;
  height: 100dvh;
  width: 100vw !important;
  width: 100dvw;
  transform: translateX(-100%);
  transition: transform 220ms ease;
  border: none;
  overflow-y: auto;
  overscroll-behavior: contain;
}
.sidebar-left { left: 0; }
.sidebar:not(.sidebar-left) { right: 0; transform: translateX(100%); }
.sidebar.sidebar--open { transform: translateX(0); }
```

**Why full-screen**: Partial drawers (320px/85vw) on 375px phones leave only 55px of the narrative visible — not enough for context. Full-screen drawers give the sidebar cards room to breathe and make close-affordance (✕ button + backdrop) unambiguous. At 768px tablets the partial drawer would overlap too much of the narrative; full-screen eliminates the layout fight.

**Close affordances:**
- `.sidebar-close` button (✕) sticky at top of each drawer
- Backdrop click closes both drawers
- Swipe inward on the narrative edge opens; swipe outward on an open drawer closes

### 5. Drawer Backdrop

```html
<div class="sidebar-backdrop"
     x-show="leftDrawerOpen || rightDrawerOpen"
     x-transition.opacity.duration.200ms
     @click="closeDrawer('left'); closeDrawer('right')"></div>
```

CSS (inside @media block):
```css
.sidebar-backdrop {
  position: fixed;
  inset: 0;
  z-index: 7500;
  background: rgba(0, 0, 0, 0.5);
}
```

Z-index stack: backdrop (7500) < drawers (8000) < modals (9400+).

### 6. Alpine State (`game()` component)

```javascript
leftDrawerOpen: false,
rightDrawerOpen: false,

toggleDrawer(side) {
  const key = side + 'DrawerOpen';
  this[key] = !this[key];
  if (!this.leftDrawerOpen && !this.rightDrawerOpen) {
    document.body.style.overflow = '';
  } else if (this[key]) {
    document.body.style.overflow = 'hidden';
  }
},

closeDrawer(side) {
  const key = side + 'DrawerOpen';
  if (this[key]) {
    this[key] = false;
    if (!this.leftDrawerOpen && !this.rightDrawerOpen) {
      document.body.style.overflow = '';
    }
  }
},
```

**Boundary watcher** in `init()`:
```javascript
this._drawerBoundary = window.matchMedia('(max-width: 768px)');
this._drawerBoundary.addEventListener('change', (e) => {
  if (!e.matches) {
    this.leftDrawerOpen = false;
    this.rightDrawerOpen = false;
    document.body.style.overflow = '';
  }
});
```

**`onSidebarClick` guard** at top:
```javascript
if (window.innerWidth <= 768) return; // mobile uses drawer toggles
```

### 7. Touch Swipe

Vertical-dominant swipe on the narrative area opens/closes drawers in a 3-slide carousel:

| Swipe direction | No drawer open | Drawer open |
|----------------|---------------|-------------|
| Swipe right (dx > 0, ≥ 40px) | Open left drawer | Close left (if open), else close right |
| Swipe left (dx < 0, ≤ -40px) | Open right drawer | Close right (if open), else close left |

Threshold: `Math.abs(dx) > Math.abs(dy) * 1.5` (horizontal-dominant) and `Math.abs(dx) ≥ 40px`.

### 8. Touch Targets (mobile)

| Element | Min height | Font size |
|---------|-----------|-----------|
| `.action-pill` | 36px | 13px |
| `.send-btn` | 36px | — |
| `.game-input` | 32px | **16px** (prevents iOS zoom) |

Design tokens not met: the 44px minimum touch target recommended by Apple HIG. Actual heights are 36px. This is a known tradeoff — 44px pills in a 6-pill row at 375px would force 3 rows of wrapping. 36px fits 2 rows of 3.

### 9. Fullscreen Modals

| Modal | Mobile style | Safe-area |
|-------|-------------|-----------|
| Pack picker | `100vw × 100dvh`, no radius, no border | Head: `padding-top: max(12px, env(safe-area-inset-top))`, left/right safe-area |
| Game over | `90vw`, padding 24px 20px | — |
| Turn log (chronicle) | Edge-to-edge (`inset: 0, border-radius: 0, border: none`), backdrop hidden | — |

### 10. Progress Strip

`flex-wrap: wrap; gap: 4px` at ≤ 768px.

---

## Decision Table

| Decision | What | Why |
|----------|------|-----|
| Breakpoint at 768px | Sidebars become overlay drawers at ≤ 768px; 769+ is desktop | Covers portrait iPad Mini (744px); above 768px the inline layout is serviceable |
| Full-screen drawers | `100vw × 100dvh`, not `min(320px, 85vw)` | Partial drawers at 375px leave useless narrative sliver; full-screen gives sidebar cards room and makes close affordance unambiguous |
| Header: hide scene tagline | `.header-logo { display: none }` on mobile | Scene tagline only useful at game start; frees critical header width |
| Header: text buttons + arrows | Buttons say "Player" and "World" with directional arrow pseudo-elements | More scannable than icon-only (☰/≡); arrows make drawer direction obvious |
| Arrows via CSS pseudo-elements | `::before`/`::after`, not inline HTML | Cleaner markup, no extra elements in DOM |
| Arrow direction: outward | Player ← on left side, → World on right side | Arrow points toward the edge each drawer pulls from (right drawer → arrow points rightwards toward edge, etc.) |
| Chronicle centered between toggles | `#turn-log-toggle { flex: 1; justify-content: center }` | Visually balanced: Player | Chronicle | World |
| Header meta pinned right | `.header-meta { flex-basis: auto; flex-grow: 0 }` | Prevents gear menu from shifting chronicle off-center |
| No `.new-game-btn` in header | Gear menu dropdown replaces it | Saves horizontal space; keeps one menu access point for all secondary actions |
| Session-only drawer state | Alpine booleans reset on page load; no `localStorage` | Drawers are ephemeral — no value remembering which was last open |
| Backdrop closes both drawers | `@click="closeDrawer('left'); closeDrawer('right')"` | Simpler than tracking which is topmost; on full-screen drawers both are hidden anyway |
| `body.style.overflow = 'hidden'` when drawer open | Prevents background scroll | Standard drawer UX |
| Boundary watcher in `init()` | `matchMedia` listener closes drawers when crossing up to >768px | Prevents stale state on orientation change |
| Touch swipe for drawer open/close | 3-slide carousel: swipe to open adjacent panel or close current | Reduces thumb reach; complements toggle buttons |
| Swipe threshold 40px | `Math.abs(dx) >= 40 && Math.abs(dx) > Math.abs(dy) * 1.5` | Avoids accidental triggers from scroll |
| Touch targets at 36px, not 44px | Action pills, send-btn, game-input at 36px min-height | 44px forces excessive wrapping in 6-pill rows at 375px; 36px fits 2×3 grid |
| `font-size: 16px` on textarea | `.game-input { font-size: 16px }` on mobile | Prevents iOS Safari auto-zoom on focus |
| `env(safe-area-inset-*)` | Header, sidebar, input-bar, pack-picker-head | Notched phone / home indicator compatibility |
| Modals go fullscreen on mobile | 100vw × 100dvh, border-radius: 0 | Eliminates double-scrollbar; modal content already scrollable |
| Chronicle goes edge-to-edge | `inset: 0; border-radius: 0; border: none; backdrop: none` | More reading room on small screen |
| Gutters hidden on mobile | `.gutter, .gutter-hint { display: none }` at ≤ 768px | Mouse-only resize events; no touch support |
| Sidebar close button (✕) | Sticky at top of each drawer, `margin-left: auto` | Clear close affordance in addition to backdrop |
| Progress strip wraps | `flex-wrap: wrap; gap: 4px` | Prevents horizontal overflow on narrow screens |

---

## What Is Removed (from old ≤ 900px breakpoint)

| Removed | File | Replaced by |
|---------|------|-------------|
| `.app-body { flex-direction: column }` at ≤ 768px | `app.src.css` former line | Not needed — sidebars are fixed overlays, not inline columns |
| `.sidebar-left { width: 100%; max-height: 40vh; border-right: none; border-bottom: ... }` | `app.src.css` former lines | Fixed full-screen drawer CSS |
| `.sidebar:not(.sidebar-left) { width: 100%; max-height: 40vh; border-left: none; border-top: ... }` | `app.src.css` former lines | Fixed full-screen drawer CSS |
| `.gutter` visible on mobile | `app.src.css` line 432 | `.gutter { display: none }` at ≤ 768px |
| Desktop `.turn-log-panel` inset on mobile | `app.src.css` line 734 | Edge-to-edge override (`inset: 0`) |
| Old 900px breakpoint block | `app.src.css` | Entire block replaced by 768px block |
| `.new-game-btn` standalone header button | `index.html` | Gear menu dropdown |
| `.reroll-btn` visibility on mobile | `index.html` line 74 | `display: none` (hidden via CSS + inline style) |

## What Is Unchanged

- All server-side code (routes, panels, templates, models, Python)
- Narrative streaming, display drain, progress indicators, roll badges, action pills, turn metrics (`submitTurn()`, `_startDisplayDrain()`, `_buildRollBadge()`, `_formatMetricsRow()`)
- Turn log overlay logic (`initTurnLogUi()` — toggle, close, refresh, keyboard Escape)
- Tooltip portal and behavior (`_bindTooltips()`, `_tooltipShow()`, `_tooltipHide()`)
- `_state_left.html` and `_state_right.html` card content and structure (all 8 `<details>` cards)
- Character creation flow (`charCreation()` Alpine component)
- World builder flow (`worldBuilder()` Alpine component)
- Pack picker logic (modal card clicks, delete handlers, start game flow)
- `stopTurn()`, `retryTurn()`, `fillFromChoice()` — no changes
- Desktop sidebar collapse/resize/persistence infrastructure (`leftW`, `rightW`, `leftCollapsed`, `rightCollapsed`, `initGutters()`, `_setupGutterResize()`) — unchanged, still active > 768px
- CSS design tokens (`:root` variables), color scheme, typography
- `.sidebar-card` open/close `localStorage` persistence (`applyCardOpenStateFromStorage()`, toggle listener)
- `.sidebar-meta-footer` — still renders inside the right sidebar drawer
- Game-over modal — minor width change (`90vw`), no structural change
- Settings panel overlay — untouched
- `<title>` tag logic — unchanged

---

## Context for Implementing LLMs

| File | Why it matters |
|------|----------------|
| `ccya/templates/index.html` | Full DOM — header bar buttons, sidebar drawer state in Alpine `game()`, backdrop element. All structural changes live here. |
| `ccya/static/app.src.css` | Entire `@media (max-width: 768px)` block (lines 1759–1932). Drawer layout, touch targets, fullscreen modals, safe-area insets. |
| `ccya/static/app.css` | Compiled output — must be regenerated from `app.src.css` (`make css` or equivalent PostCSS build step). |
| `docs/repomap.md` | Confirms no server-side changes; confirms `index.html` structure and `game()` component boundaries. |

---

## Failure Modes and Risks

1. **36px touch targets below Apple HIG (44px).** Known tradeoff; 44px pills in 6-pill rows force 3 rows of wrapping at 375px.
2. **Drawer open on orientation change → resize above 768px.** Mitigated by `matchMedia` listener in `init()`.
3. **`dvh` units not supported on older mobile browsers.** Graceful fallback to `vh`.
4. **Swipe gesture conflicts with scroll.** Threshold (`dx > dy * 1.5` and `dx ≥ 40px`) prevents accidental triggers during vertical scroll.
