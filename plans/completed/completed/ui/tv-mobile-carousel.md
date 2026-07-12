# Turn Viewer Mobile Swipe Carousel

## Purpose

Add swipe-to-cycle between pipeline and diff panel columns on mobile (≤768px) in the turn viewer, making it usable on narrow viewports without horizontal overflow.

## Problem Statement

The turn viewer uses a rigid two-column layout (56% pipeline / 44% sticky diff panel) with zero responsive breakpoints. On viewports ≤768px this causes horizontal overflow and makes both columns unusable simultaneously — users can't see either column properly on mobile devices.

## Constraints

- Only affects `@media (max-width: 768px)` breakpoint; desktop layout is untouched.
- Reuse existing CSS variables, font families, and design tokens from `app.src.css`.
- Swipe logic mirrors the narration UI's touch gesture pattern (`index.html:1125-1161`).
- Alpine.js component already uses `tvRoot()` function in `_turn_viewer.html` — no new framework dependencies.
- Touch targets bumped to 36px minimum on mobile only (via media query).
- No server-side changes, API changes, or template structure changes beyond bindings and classes.

## Non-goals

- No pull-to-refresh or other gestures.
- No animated swipe-drag preview of the panel being swiped (only snap to final position).
- No keyboard navigation for carousel on mobile (j/k already navigate between turns).
- No tablet-specific breakpoints (768px is the single cutoff, matching narration UI).

## Solution

Add a `@media (max-width: 768px)` block in `app.src.css` that switches `.tv-turn-columns` from flexbox to a hidden/overflow container with two absolutely-positioned child columns. Wire Alpine reactive state (`mobileColumnIndex`) into the template's column containers for transform positioning and visibility toggling. Add touch swipe detection scoped to the turn viewer root element (not document-level) in `tvRoot()`. Compress turn headers under mobile breakpoint by truncating user input, hiding trace ID/timing bar, reducing padding.

## Firm decisions

1. **Swipe direction:** Right swipe → show diff panel from pipeline view; Left swipe → show pipeline from diff view. Constrained at boundaries (can't swipe past edges).
2. **Default column on mobile:** Diff panel is visible by default when expanding a turn card (`mobileColumnIndex = 0` maps to diff panel position, `1` maps to pipeline — matching the carousel order: [diff] ↔ [pipeline]).
3. **Header compression:** Truncate long user input with ellipsis (single line), hide trace ID span and latency waterfall bar on mobile, reduce header padding from `14px 18px` → `10px 12px`. Keep turn number and status badges visible.
4. **Swipe boundary:** Constrained — users cannot swipe past the first or last panel in the carousel.
5. **Touch targets:** All stage headers, tab buttons, expand-all button, input pill headers get `min-height: 36px` under mobile breakpoint. Input font set to `16px` (prevents iOS zoom-on-focus).

## Risks, Ambiguities, and Blockers

- **Sticky positioning conflict:** The diff panel uses `position: sticky; top: 16px; max-height: 80vh`. Under mobile carousel this must be removed since the container handles scrolling. If not handled, the sticky element will break out of the carousel viewport.
- **Alpine x-show vs transform:** Using both `x-show` and CSS `transform` on the same elements can cause layout thrashing during transitions. Prefer `x-show` for conditional rendering + `transform: translateX()` for positioning within a hidden container, or use `x-bind:class` to toggle between visible/hidden states without animating visibility changes mid-swipe.
- **Touch event propagation:** Swipe detection must not interfere with scrolling the page vertically. The existing narration UI uses `Math.abs(dx) < Math.abs(dy) * 1.5` which rejects diagonal swipes — this is sufficient but should be scoped to the turn viewer container only, not document-level (to avoid conflicts if other components add touch listeners).

## Status
`completed`

## Phases

2 phases: mobile carousel CSS + Alpine state/swipe wiring in a single coherent change set touching `_turn_viewer.html` and `app.src.css`.

---

## Implementation — Phase 1: Mobile carousel CSS, header compression, touch targets

### Context files to load
- `/Users/pwilson/repos/ccya/ccya/static/app.src.css` (lines 2346–3450 for turn viewer styles)
- `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html` (template structure reference only, no changes in this phase)

### Detailed steps

#### Step 1.1 — Add `@media (max-width: 768px)` block after existing mobile breakpoint

**File:** `/Users/pwilson/repos/ccya/ccya/static/app.src.css`

**What:** Insert a new media query block immediately after the closing brace of the existing `@media (max-width: 768px)` block (after line 1950). This keeps all mobile styles together in one place. The block contains:

a) **Column container swap** — `.tv-turn-columns` switches from flexbox to a relative-positioned overflow-hidden container with height based on the visible child only:
```css
.tv-turn-columns {
    position: relative;
    display: block;
    overflow: hidden;
}
```

b) **Column positioning** — Both `.tv-pipeline` and `.tv-diff-panel` switch from flex children to absolute-positioned full-width columns within the container, with `transform: translateX()` for carousel positioning. Remove sticky positioning on diff panel (sticky breaks out of carousel viewport):
```css
.tv-pipeline {
    position: absolute;
    inset: 0;
    transform: translateX(100%);   /* default off-screen right */
    transition: transform 220ms ease;
    flex: none;                     /* undo flex: 0 0 56%; */
}

.tv-diff-panel {
    position: absolute;
    inset: 0;
    transform: translateX(-100%);   /* default off-screen left */
    transition: transform 220ms ease;
    flex: none;                     /* undo flex: 0 0 44%; */
    max-height: none;               /* remove sticky height constraint */
    overflow-y: auto;               /* scroll content within panel */
}
```

c) **Visible column state** — When `x-show` is true (controlled by Alpine), the visible column gets `transform: translateX(0)` and the hidden one stays off-screen. This uses a CSS class approach tied to Alpine's reactive state rather than inline styles for cleaner separation. The actual transform values are set via Alpine bindings in Phase 1 step 2, but the base carousel positioning (both off-screen by default) is defined here so that when `x-show` toggles visibility, the container doesn't flash content during transition.

d) **Turn header compression** — Reduce padding, truncate user input to single line with ellipsis, hide trace ID and latency waterfall:
```css
.tv-turn-header {
    padding: 10px 12px;
}

.tv-turn-input {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;                   /* allow flex-shrink */
}

.tv-turn-meta span:first-child,   /* trace ID */
.tv-latency-waterfall             /* timing bar */
{
    display: none !important;
}

/* Keep token counts and status badges visible but compact */
.tv-turn-tokens { font-size: 9px; }
```

e) **Touch target bump** — Stage headers, tab buttons, expand-all button, input pill headers get `min-height: 36px`:
```css
.tv-stage-header   { min-height: 36px; padding-top: 8px; padding-bottom: 8px; }
.tv-tab-btn        { min-height: 36px; padding-top: 10px; padding-bottom: 10px; font-size: 12px; }
.tv-expand-all-btn { min-height: 36px; padding: 8px 14px; font-size: 11px; }
.tv-input-pill-header { min-height: 36px; padding-top: 8px; padding-bottom: 8px; }

/* Prevent iOS zoom-on-focus on any inputs within turn viewer */
.turn-viewer-page input,
.turn-viewer-page textarea { font-size: 16px; }
```

f) **Safe area insets** — Apply `env(safe-area-inset-*)` to the turn card container for notched devices (matching narration UI pattern):
```css
.tv-turn-card { margin-bottom: 8px; border-radius: var(--radius-sm); }
```

g) **Column width reset** — Undo any fixed widths from desktop styles that would cause overflow in carousel mode. Both columns should be `width: 100%` within the container (inherited by absolute positioning's `inset: 0`).

**Why:** This is all visual/layout changes with zero template/JS modifications. The CSS defines the mobile layout independently of Alpine state, making it safe to verify in isolation once the bindings are added in Phase 2.

**Validation:** Open turn viewer on a viewport ≤768px (browser dev tools device emulation). Verify:
- No horizontal overflow on `.tv-turn-columns`
- Both columns hidden by default (container shows empty space or collapsed state) — actual visibility controlled by Alpine bindings from Phase 2
- User input text truncates with ellipsis at narrow widths
- Trace ID and latency waterfall are hidden
- Touch targets are visibly larger (36px minimum height on stage headers, tabs, buttons)

### Tests to write or update
N/A during refactor phase. Tests deferred per AGENTS.md constraints.

---

## Implementation — Phase 2: Alpine carousel state + swipe gesture detection

### Context files to load
- `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html` (lines 324–516 for `tvRoot()` function, lines 99–282 for column HTML structure)

### Detailed steps

#### Step 2.1 — Add carousel reactive state to `tvRoot()`

**File:** `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html`

**What:** In the `tvRoot()` return object (line ~326), add:
- `mobileColumnIndex: 0` — tracks which panel is visible. Index `0` = diff panel, index `1` = pipeline. Default to `0` per user's choice (diff panel by default on mobile).
- `_isMobile()` helper method that returns `window.innerWidth <= 768`.

**Why:** Alpine reactive state drives the carousel position bindings in the template and determines swipe direction logic. Starting at `0` means diff panel is visible when a turn card first expands on mobile.

#### Step 2.2 — Wire carousel index into column containers' transform styles

**File:** `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html`

**What:** On the two column `<div>` elements inside `.tv-turn-columns`:
- Add `:style="'transform: translateX(' + (mobileColumnIndex === 0 ? '-100%' : mobileColumnIndex === 1 ? '0' : '-100%') + ')'"` to `.tv-pipeline` — this shows pipeline when index is `1`, hides it otherwise.
- Add `:style="'transform: translateX(' + (mobileColumnIndex === 0 ? '0' : mobileColumnIndex === 1 ? '100%' : '0') + ')'"` to `.tv-diff-panel` — this shows diff panel when index is `0`, hides it otherwise.

Actually, cleaner approach using a computed-style helper method on the Alpine component:
- Add `carouselTransform(column)` method that returns `'translateX(' + (column === this.mobileColumnIndex ? '0' : (column === 0 ? '-100%' : '100%')) + ')'`.
- Bind `:style="'transform:' + carouselTransform('pipeline')"` on `.tv-pipeline` and `:style="'transform:' + carouselTransform('diff')" ` on `.tv-diff-panel`.

**Why:** Keeps transform logic in the Alpine component rather than inline template expressions. The CSS transition (220ms ease) handles smooth animation between positions.

#### Step 2.3 — Set default mobile column when expanding a turn card

**File:** `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html`

**What:** In `toggleTurnCollapsed(turn)` method, after setting the collapsed state to false (expanding), add logic that if `_isMobile()`, sets `mobileColumnIndex = 0` (diff panel). This ensures every time a user expands a turn card on mobile they see the diff panel by default.

**Why:** Per user's choice — diff panel is the default view when expanding turns on mobile. Users can swipe left to see pipeline if needed.

#### Step 2.4 — Add touch swipe detection scoped to `#tv-root`

**File:** `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html`

**What:** In the `init()` method of `tvRoot()`, after existing initialization, add:
- Store `_swipeStartX = 0` and `_swipeStartY = 0` on the component instance.
- Add `touchstart` listener to `document.getElementById('tv-root')` (not document-level) that records `clientX/clientY`. Only active when `window.innerWidth <= 768`.
- Add `touchend` listener on the same element that computes delta, rejects diagonal swipes (`Math.abs(dx) < Math.abs(dy) * 1.5`) and short swipes (<40px), then:
  - If `dx > 0` (swipe right): increment `mobileColumnIndex`, clamped to max value of `1`.
  - If `dx < 0` (swipe left): decrement `mobileColumnIndex`, clamped to min value of `0`.

```javascript
var tvRootEl = document.getElementById('tv-root');
if (!tvRootEl) return;
this._swipeStartX = 0;
this._swipeStartY = 0;
var self = this;
tvRootEl.addEventListener('touchstart', function(e) {
    if (window.innerWidth > 768) return;
    var t = e.touches[0];
    self._swipeStartX = t.clientX;
    self._swipeStartY = t.clientY;
}, { passive: true });
tvRootEl.addEventListener('touchend', function(e) {
    if (window.innerWidth > 768) return;
    var dx = e.changedTouches[0].clientX - self._swipeStartX;
    var dy = e.changedTouches[0].clientY - self._swipeStartY;
    if (Math.abs(dx) < Math.abs(dy) * 1.5) return;
    if (Math.abs(dx) < 40) return;
    if (dx > 0 && self.mobileColumnIndex < 1) {
        self.mobileColumnIndex++;   // swipe right → pipeline
    } else if (dx < 0 && self.mobileColumnIndex > 0) {
        self.mobileColumnIndex--;   // swipe left → diff panel
    }
}, { passive: true });
```

**Why:** Reuses the same gesture detection pattern from narration UI but scoped to `#tv-root` element only (not document-level). Constrained at boundaries via clamped index. Passive listeners prevent scroll blocking.

#### Step 2.5 — Add a small visual indicator for carousel position (optional, lightweight)

**File:** `/Users/pwilson/repos/ccya/ccya/templates/_turn_viewer.html`

**What:** Insert a tiny dot indicator row between the turn header and columns showing which panel is active:
```html
<div class="tv-carousel-dots" x-show="!isTurnCollapsed(t.turn)">
    <span :class="{ 'active': mobileColumnIndex === 0 }"></span>
    <span :class="{ 'active': mobileColumnIndex === 1 }"></span>
</div>
```

Style in CSS media query: two small dots (4px diameter), the active one filled, inactive outlined. Positioned centered between header and columns.

**Why:** Gives users a visual cue that there are swappable panels without needing to discover the gesture by trial-and-error. Minimal code (~5 lines HTML + ~10 lines CSS). Only visible under mobile breakpoint.

**Validation:** Test on actual device or Chrome DevTools device emulation:
- Expand a turn card → diff panel is visible (not pipeline)
- Swipe right → pipeline appears with smooth transition
- Swipe left from pipeline → diff panel reappears
- Cannot swipe past boundaries (swiping further in either direction does nothing)
- Vertical scroll still works normally (diagonal swipes rejected, vertical scrolls not intercepted)
- Desktop viewport (>768px): both columns visible side-by-side as before, no carousel behavior

### Tests to write or update
N/A during refactor phase. Tests deferred per AGENTS.md constraints.
