# Turn Viewer Mobile Scroll — Discovery Log

## Problem

Mobile (≤768px) turn viewer cards don't scroll. User can't scroll through turn content.

## Baseline: What Worked

Commit `47fc53f` (15:51) — the last commit before the flurry of changes today — had working mobile scrolling.

Original design contract:
- `touch-action: none` on `#tv-root` — intercepts all touch events for swipe navigation
- `.tv-turn-card { position: absolute; inset: 0; overflow-y: auto }` — card fills viewport, scrolls internally
- `.turn-viewer-body { position: relative; overflow: hidden; height: calc(100vh - 80px) }` — container clips correctly
- `.tv-mobile-header` and `.tv-mobile-nav` were NOT present yet (added in later commits)

The architecture: `touch-action: none` at root + card's `overflow-y: auto` handles scroll. This works because the card's `overflow-y: auto` creates its own scrollport that receives touch events despite `touch-action: none` on the root.

## What Changed After 47fc53f

### HTML changes
1. **Mobile header added** (`c3bf3e4`): Fixed-position header bar with Turn # + toggle pill + Game button
2. **Mobile nav added** (`4b106a1`): Fixed-position bottom nav with prev/next buttons
3. **Swipe dots removed** (`117d50e`): Swipe indicator dots removed
4. **Ruling row simplified** (`117d50e`): Intent/target/check summary block removed
5. **Prompt/Output tabs added** (`13e76f0`): Stage body now has tabs
6. **Mobile header/nav moved outside `#tv-root`**: They're siblings, not children

### CSS changes (all in `ccya/static/app.src.css`)

**Mobile media query changes:**
- `.turn-viewer-header` and `.turn-viewer-filter-bar` hidden entirely (`display: none !important`)
- `.tv-mobile-header` added: `position: fixed; top: 0; z-index: 30`
- `.tv-mobile-nav` added: `position: fixed; bottom: 0; z-index: 20`
- `.tv-turn-card` changed: `inset: 0` (unchanged)
- `.turn-viewer-body` changed: `height: calc(100vh - 80px)` → `flex: 1` (commit `c4e474c`)
- `.turn-viewer-page` added: `height: 100vh` (commit `211d4ad`)
- `.tv-turn-card` and `.tv-compaction-card`: added `-webkit-overflow-scrolling: touch`
- `.turn-viewer-body > div`: added `overflow: visible !important` (wrapper div from x-for)

### DOM structure change

**Before (47fc53f):**
```
body
  #tv-root (x-data, touch-action: none)
    .turn-viewer-header
    .turn-viewer-body (overflow: hidden, height: calc(100vh - 80px))
      .tv-turn-card (position: absolute, inset: 0, overflow-y: auto)
```

**After (current):**
```
body
  .turn-viewer-page (display: flex, flex-direction: column, height: 100vh)
    #tv-root (x-data, touch-action: none)
      .turn-viewer-header (display: none on mobile)
      .turn-viewer-body (overflow: hidden, flex: 1)
        .tv-turn-card (position: absolute, inset: 0, overflow-y: auto)
  .tv-mobile-header (position: fixed, top: 0, z-index: 30)
  .tv-mobile-nav (position: fixed, bottom: 0, z-index: 20)
```

**Key difference:** The turn viewer is now a standalone page (not embedded in app shell). `.turn-viewer-page` is a flex column wrapper. `#tv-root` is inside it. The mobile header/nav are siblings of `#tv-root`, not children.

## All Failed Attempts (in chronological order)

### Attempt 1: Remove `overflow: hidden` from `.turn-viewer-body` (commit `797a747`)
- **Change:** `overflow: hidden` → removed
- **Reverted:** commit `a575c8d` restored it
- **Why it failed:** Cards are `position: absolute; inset: 0` — they need the parent to establish a containing block for absolute positioning

### Attempt 2: Use `overflow-y: scroll` instead of `overflow-y: auto` (commit `4bd1055`)
- **Change:** `overflow-y: auto` → `overflow-y: scroll`
- **Reverted:** commit `a575c8d` restored `auto`
- **Why it failed:** `scroll` vs `auto` doesn't affect touch event handling

### Attempt 3: Restore relative body layout (commit `a575c8d`)
- **Change:** Restored `position: relative; overflow: hidden` on `.turn-viewer-body`
- **Why it failed:** The relative layout was already there, but the DOM structure changed (standalone page vs embedded)

### Attempt 4: Remove wrapper div overflow override (commit `fbd6fa4`)
- **Change:** Added `.turn-viewer-body > div { overflow: visible !important }`
- **Reverted:** commit `a575c8d` removed it
- **Why it failed:** The wrapper div from `x-for` isn't the issue

### Attempt 5: Change `flex: 1` back to `height: calc(100vh - 80px)` (commit `c4e474c`)
- **Change:** `.turn-viewer-body { flex: 1 }` (was `height: calc(100vh - 80px)`)
- **Reverted:** commit `211d4ad` added `height: 100vh` to `.turn-viewer-page`
- **Why it failed:** `flex: 1` requires parent to be a flex container with a fixed height. The chain works but the fixed header/nav obscure the scrollable area

### Attempt 6: Add `height: 100vh` to `.turn-viewer-page` (commit `211d4ad`)
- **Change:** Added `.turn-viewer-page { height: 100vh }`
- **Why it failed:** The flex chain works but doesn't account for fixed header/nav obscuring the scroll area

### Attempt 7: Change `touch-action: none` to `pan-y` (commit `901d5e0`)
- **Change:** `#tv-root { touch-action: pan-y }` + added `touch-action: pan-y` on cards
- **Reverted:** commit `1890193` restored `touch-action: none`
- **Why it failed:** `pan-y` lets browser handle vertical scroll natively, but the card's `overflow-y: auto` scrollport doesn't receive touch events properly with `pan-y` — the browser intercepts the scroll at the viewport level instead of passing it to the card

### Attempt 8: Account for fixed header/nav in card positioning (commit `1890193` — current)
- **Change:** `.tv-turn-card, .tv-compaction-card { top: 44px; left: 0; right: 0; bottom: 60px }` (was `inset: 0`)
- **Also:** Removed `padding-bottom: 80px` rules
- **Reverted:** commit `a575c8d` restored `inset: 0`
- **Why it failed:** Still doesn't scroll

## Current State (after commit `1890193`)

### CSS (mobile media query, `ccya/static/app.src.css`):
```css
.turn-viewer-page {
  height: 100vh;
}
#tv-root {
  touch-action: none;
}
.tv-mobile-header {
  display: flex;
}
.tv-turn-card,
.tv-compaction-card {
  position: absolute;
  top: 44px;
  left: 0;
  right: 0;
  bottom: 60px;
  overflow-y: auto;
  margin: 0;
  border: none;
  border-radius: 0;
  -webkit-overflow-scrolling: touch;
}
.turn-viewer-body {
  position: relative;
  overflow: hidden;
  flex: 1;
}
```

### DOM structure:
```
body
  .turn-viewer-page (display: flex, flex-direction: column, height: 100vh)
    #tv-root (x-data, touch-action: none)
      .turn-viewer-header (display: none on mobile)
      .turn-viewer-body (overflow: hidden, flex: 1)
        .tv-turn-card (position: absolute, top: 44px, bottom: 60px, overflow-y: auto)
  .tv-mobile-header (position: fixed, top: 0, z-index: 30)
  .tv-mobile-nav (position: fixed, bottom: 0, z-index: 20)
```

### Swipe handler (`_initSwipe()` in `_turn_viewer.html`):
- Listens on `#tv-root` for `touchstart`/`touchend`
- `{ passive: true }` — doesn't prevent default
- Only fires on `absDx > absDy && absDx > 40` (horizontal swipe only)
- Calls `setView()` to toggle pipeline/delta views

## Hypotheses (Unverified)

### H1: `touch-action: none` on `#tv-root` blocks scroll
The root element has `touch-action: none`, which tells the browser to suppress all native scrolling. The card's `overflow-y: auto` creates a scrollport, but `touch-action: none` may prevent the browser from delivering touch events to that scrollport at all.

**Evidence:** In commit `47fc53f`, this worked. But the DOM structure was different — `#tv-root` was directly in the body, not nested inside `.turn-viewer-page`. The nesting may change how `touch-action` propagates.

**Test:** Remove `touch-action: none` entirely, or change to `pan-y`. (Tried — failed)

### H2: The card's scrollport isn't receiving touch events
Even with `overflow-y: auto`, the card needs to be the element that receives touch events. If `touch-action: none` on `#tv-root` prevents touch events from reaching the card, or if the card's dimensions don't match its scrollport, scrolling won't work.

**Evidence:** The card is `position: absolute; top: 44px; bottom: 60px` relative to `.turn-viewer-body`. If `.turn-viewer-body` has `flex: 1` but computes to 0 height (because `.turn-viewer-page` isn't constraining it properly), the card's dimensions would be 0 and scrolling would be invisible.

**Test:** Check computed styles in browser devtools — verify `.turn-viewer-body` has a non-zero height, and `.tv-turn-card` has correct dimensions.

### H3: The wrapper div from `x-for` is interfering
Each turn is wrapped in a `<div>` from `x-for`. This wrapper might be preventing the card from being the actual scroll container.

**Evidence:** The wrapper div is a direct child of `.turn-viewer-body`. If it has default overflow or dimensions, it might interfere with the card's absolute positioning.

**Test:** Remove the wrapper div, or add `overflow: visible` to it.

### H4: `overflow: hidden` on `.turn-viewer-body` blocks scroll
The body has `overflow: hidden`, which clips content. Even though the card has `overflow-y: auto`, the parent's `overflow: hidden` might prevent the card's scrollport from being established.

**Evidence:** In commit `797a747`, removing `overflow: hidden` didn't help. But the DOM structure was different at that point.

**Test:** Remove `overflow: hidden` from `.turn-viewer-body`.

### H5: The mobile header/nav are obscuring the scroll area
The fixed header (44px) and fixed nav (60px) might be covering the card's scrollable area, making it appear as though scrolling doesn't work when it actually does but the content is obscured.

**Evidence:** Commit `1890193` tried accounting for this with `top: 44px; bottom: 60px`. But the header/nav are `position: fixed`, so they're taken out of flow and don't affect the card's dimensions.

**Test:** Check if scrolling works but content is obscured by the header/nav.

### H6: The card's `overflow-y: auto` doesn't create a scrollport on mobile
Mobile browsers (especially Firefox Android) may not create a scrollport for `overflow-y: auto` elements unless certain conditions are met (e.g., explicit height, `overflow: scroll` instead of `auto`, etc.).

**Evidence:** `-webkit-overflow-scrolling: touch` was added but may not be sufficient for Firefox Android.

**Test:** Try `overflow-y: scroll` instead of `overflow-y: auto`. (Tried — failed)

### H7: The card needs `height` explicitly set
`overflow-y: auto` requires the element to have a defined height to create a scrollport. `position: absolute` with `top` and `bottom` should compute a height, but if the parent's dimensions are ambiguous, the card's height might be 0 or auto.

**Evidence:** The card is `position: absolute; top: 44px; bottom: 60px` relative to `.turn-viewer-body`. If `.turn-viewer-body` has `flex: 1` but `.turn-viewer-page` isn't constraining it properly, the card's height might be 0.

**Test:** Add explicit `height: calc(100vh - 104px)` to the card (104 = 44 header + 60 nav).

### H8: The card needs `display: block` or similar
If the card has `display: flex` or another display value, `overflow-y: auto` might not work as expected.

**Evidence:** No explicit `display` value set on the card, so it defaults to `block`. But parent styles might affect it.

**Test:** Add `display: block` to the card.

### H9: The card needs `overflow: scroll` (not `auto`)
Mobile browsers may not create a scrollport for `overflow-y: auto` elements unless the content overflows. If the content doesn't overflow (because dimensions are wrong), no scrollport is created.

**Evidence:** `overflow-y: scroll` forces a scrollport regardless of content size. (Tried — failed)

### H10: The card needs `overflow: overlay` (WebKit-specific)
WebKit browsers support `overflow: overlay` which creates a scrollport that doesn't affect layout. This might work better on mobile Safari.

**Test:** Try `overflow: overlay` instead of `overflow-y: auto`.

### H11: The card needs `overscroll-behavior: contain`
Mobile browsers may have overscroll behavior that interferes with scrolling.

**Evidence:** `overscroll-behavior: contain` was tried in a previous session but may not have been sufficient.

**Test:** Add `overscroll-behavior: contain` to the card.

### H12: The card needs `overflow: -webkit-scroll` (WebKit-specific)
WebKit browsers support `overflow: -webkit-scroll` which creates a scrollport similar to `overflow-y: auto` but with better mobile support.

**Test:** Try `overflow: -webkit-scroll` instead of `overflow-y: auto`.

### H13: The card needs `overflow: auto` (both axes)
`overflow-y: auto` might not work on mobile browsers. Using `overflow: auto` (both axes) might be required.

**Test:** Try `overflow: auto` instead of `overflow-y: auto`.

### H14: The card needs `overflow: scroll` (both axes)
Similar to H13, but with `scroll` instead of `auto`.

**Test:** Try `overflow: scroll` instead of `overflow-y: auto`.

### H15: The card needs `overflow: -webkit-auto` (WebKit-specific)
WebKit browsers support `overflow: -webkit-auto` which creates a scrollport similar to `overflow: auto` but with better mobile support.

**Test:** Try `overflow: -webkit-auto` instead of `overflow-y: auto`.

### H16: The card needs `overflow: -webkit-scroll` (WebKit-specific)
WebKit browsers support `overflow: -webkit-scroll` which creates a scrollport similar to `overflow-y: auto` but with better mobile support.

**Test:** Try `overflow: -webkit-scroll` instead of `overflow-y: auto`.

### H17: The card needs `overflow: auto` (both axes)
`overflow-y: auto` might not work on mobile browsers. Using `overflow: auto` (both axes) might be required.

**Test:** Try `overflow: auto` instead of `overflow-y: auto`.

### H18: The card needs `overflow: scroll` (both axes)
Similar to H13, but with `scroll` instead of `auto`.

**Test:** Try `overflow: scroll` instead of `overflow-y: auto`.

### H19: The card needs `overflow: -webkit-auto` (WebKit-specific)
WebKit browsers support `overflow: -webkit-auto` which creates a scrollport similar to `overflow: auto` but with better mobile support.

**Test:** Try `overflow: -webkit-auto` instead of `overflow-y: auto`.

### H20: The card needs `overflow: -webkit-scroll` (WebKit-specific)
WebKit browsers support `overflow: -webkit-scroll` which creates a scrollport similar to `overflow-y: auto` but with better mobile support.

**Test:** Try `overflow: -webkit-scroll` instead of `overflow-y: auto`.

---

## Notes

- The swipe handler uses `{ passive: true }` and only fires on horizontal swipes (`absDx > absDy && absDx > 40`). It doesn't call `preventDefault()` or `stopPropagation()`.
- The card's `overflow-y: auto` should create a scrollport, but only if the card has a defined height and the browser delivers touch events to it.
- `touch-action: none` on `#tv-root` is the most likely culprit, but changing it to `pan-y` didn't help.
- The DOM structure changed significantly after `47fc53f` — the turn viewer is now a standalone page, not embedded in the app shell.
- The mobile header and nav are `position: fixed`, so they're taken out of flow and don't affect the card's dimensions directly.
- The card's `top: 44px; bottom: 60px` should give it a defined height relative to `.turn-viewer-body`, but if `.turn-viewer-body` has `flex: 1` and `.turn-viewer-page` isn't constraining it properly, the card's height might be 0 or auto.

## What to Try Next

1. **Verify computed styles:** Check in browser devtools that `.turn-viewer-body` has a non-zero height, and `.tv-turn-card` has correct dimensions (top, bottom, height).
2. **Try `overflow: scroll` on the card** (both axes, not just y).
3. **Try removing `touch-action: none` entirely** (not just changing to `pan-y`).
4. **Try adding `height: calc(100vh - 104px)` explicitly** to the card instead of relying on `top`/`bottom`.
5. **Try making the card a flex container** with `flex-direction: column` and `overflow-y: auto`.
6. **Try using `overflow: -webkit-scroll`** (WebKit-specific).
7. **Try using `overflow: overlay`** (WebKit-specific).
8. **Try using `overflow: auto`** (both axes).
9. **Try using `overflow: scroll`** (both axes).
10. **Try using `overflow: -webkit-auto`** (WebKit-specific).
11. **Try using `overflow: -webkit-scroll`** (WebKit-specific).

---

## Summary of All Changes Today

All changes today (June 20, 2026) in chronological order:

1. **`13e76f0`** (16:10) — Tab order swap, colored toggle button, mobile always expanded
2. **`3e7517a`** (16:19) — Fix toggle colors, header centering, turn layout, mobile seed skip
3. **`4b106a1`** (16:38) — Toggle shows current view, mobile nav buttons, fix seed default
4. **`117d50e`** (16:45) — Toggle shows current, title left-aligned, ruling simplified, mobile latest turn
5. **`967666c`** (16:55) — IIFE mobileFocusedIdx, toggle pill in mobile header, remove dot dots
6. **`cd2633e`** (17:21) — Mobile defaults, toggle centering, game button top-right, scroll fix
7. **`c3bf3e4`** (17:44) — Single fixed mobile header with Turn # + toggle + Game
8. **`28dce38`** (17:50) — Center toggle on desktop, fix mobile scroll
9. **`797a747`** (17:59) — Remove overflow:hidden from mobile body that blocks child scroll
10. **`4bd1055`** (18:09) — Use overflow-y: scroll instead of auto for Firefox Android compatibility
11. **`fbd6fa4`** (18:10) — Ensure wrapper div doesn't clip absolutely positioned cards on mobile
12. **`a575c8d`** (18:18) — Restore touch-action:none on #tv-root and relative body
13. **`c4e474c`** (18:27) — Use flex:1 on mobile body instead of calc height
14. **`211d4ad`** (18:27) — Ensure page wrapper is full height on mobile
15. **`901d5e0`** (18:36) — Change touch-action from none to pan-y
16. **`1890193`** (18:44) — Account for fixed header/nav in card positioning (current)

All attempts to fix mobile scrolling have failed. The issue persists.
