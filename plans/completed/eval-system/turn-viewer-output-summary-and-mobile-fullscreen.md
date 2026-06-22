# Turn Viewer — Output Summary Pills + Mobile Full-Screen

## Purpose

Simplify each pipeline stage to one labeled Output Summary pill (removing input pills), and redesign mobile to show one full-screen turn at a time with up/down swipe navigation and minimal chrome.

## Problem Statement

Pipeline stages still show multiple collapsible input pills per stage alongside the output, cluttering the view. On mobile, the scrollable turn list wastes screen real estate on turn card headers and stage header chrome, leaving little room for actual content.

## Constraints

- Desktop unchanged for turn list (scrollable cards with expand/collapse).
- Mobile full-screen mode applies only at `@media (max-width: 768px)`.
- Left/right swipe for delta/pipeline toggle preserved on mobile.
- Alpine.js only. State in `tvRoot()`.
- sessionStorage for view preference (already done).
- No server changes.

## Non-goals

- No changes to delta panel content.
- No changes to desktop turn list layout.
- No animated drag preview during swipe.
- No pull-to-refresh.
- No changes to seed/sanitizer row types.

## Solution

Phase 1: Remove input pills and their associated Alpine state/methods. Add an "Output Summary" label above each stage's output content. Clicking stage header toggles output visibility as before.

Phase 2: On mobile, replace the scrollable turn card list with a single-turn full-screen view. A thin status bar shows turn number. Swipe up/down navigates turns. Stage headers become compact (stage name only). Left/right swipe still toggles delta/pipeline views.

## Firm decisions

1. Input pills (`inputs_snapshot` rows) removed entirely — no replacement.
2. Each stage output section labeled "Output Summary" — a small label above the content.
3. Mobile: exactly one turn visible at a time, fills the viewport.
4. Mobile: thin status bar — turn number only (e.g., "3 / 12"), no user input, no trace ID, no timing, no badges.
5. Mobile: swipe up = newer turn (higher idx), swipe down = older turn (lower idx).
6. Mobile: stage headers show stage name only — no status badge, no token bar, no timing, no chevron.
7. Desktop: completely unchanged from current state.
8. `focusedTurnIdx` reused as `mobileFocusedIdx` on mobile (already exists, initialized to 0).

## Risks, Ambiguities, and Blockers

- Mobile swipe up/down must not conflict with browser's native scroll. Solution: `overflow: hidden` on the mobile turn container, `touch-action: none` prevents scroll. Gesture detection math (dx vs dy) already rejects diagonals.
- Desktop scrollable list should still work normally. All mobile changes scoped to `@media (max-width: 768px)`.
- Seed/sanitizer rows: on mobile, these are non-turn rows. Should they appear as full-screen cards too? Current plan: keep them in the list, accessible via swipe until you reach them. If they show up in the turn cycle, they get a compact display too.

## Status

`open`

## Phases

2 phases: (1) per-stage Output Summary simplification, (2) mobile full-screen turn view.

## Implementation — Phase 1: Output Summary pills

Remove input pills. Label stage output as "Output Summary."

### Context files to load

| File | Lines | What |
|---|---|---|
| `_turn_viewer.html` | 142–209 | Stage loop: input pills, stage header, stage body |
| `_turn_viewer.html` | 382–450 | Alpine state: `inputPillOpen`, `isInputPillOpen`, `toggleInputPill` |
| `_turn_viewer.html` | 426–431 | `toggleExpandAllForTurn` refs stage header expand — confirm unchanged |
| `app.src.css` | 2832–2870 | Column CSS (not touched in this phase — output is already full-width) |

### Detailed steps

#### Step 1.1 — Remove input pills from stage template

**File:** `ccya/templates/_turn_viewer.html`

**What:** Delete lines 144–163 (the `inputs_snapshot` template block rendered above each stage header). Remove the `tv-stage-wrap--no-inputs` class logic from the stage wrapper (line 143).

**Before:**
```html
<div class="tv-stage-wrap" :class="{'tv-stage-wrap--no-inputs': !t.inputs_snapshot || !t.inputs_snapshot[stage] || !Object.keys(t.inputs_snapshot[stage]).length}">
    <template x-if="t.inputs_snapshot && t.inputs_snapshot[stage] && Object.keys(t.inputs_snapshot[stage]).length">
        <div class="tv-inputs-row">
            <template x-for="([srcKey, lines], idx) in Object.entries(t.inputs_snapshot[stage])" :key="srcKey">
                <div class="tv-input-pill" ...>
                    ...
                </div>
            </template>
        </div>
    </template>
    <div class="tv-pipeline-stage" ...>
```

**After:**
```html
<div class="tv-stage-wrap">
    <div class="tv-pipeline-stage" ...>
```

**Why:** Design decision — one Output Summary pill per stage. Input pills removed.

**Validation:** Turn viewer loads. Pipeline view shows five stage rows. No input pills appear above any stage.

#### Step 1.2 — Remove input pill Alpine state and methods

**File:** `ccya/templates/_turn_viewer.html`

**What:** Remove `inputPillOpen: {},` from the state object (line 384). Remove `isInputPillOpen()` method (lines 444–446). Remove `toggleInputPill()` method (lines 447–449).

**Why:** Dead code after input pill removal in Step 1.1.

**Validation:** Alpine dev tools shows no `inputPillOpen` state. No console errors.

#### Step 1.3 — Add "Output Summary" label to stage body

**File:** `ccya/templates/_turn_viewer.html`

**What:** Inside the `.tv-stage-body` `x-show` div (line 184), before the output content, add a small label:

```html
<div class="tv-stage-body" x-show="expandedKey(t.turn, stage)">
    <div class="tv-output-summary-label">Output Summary</div>
    ...
</div>
```

Add CSS:
```css
.tv-output-summary-label {
    font-size: 0.71rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 8px;
}
```

Place this after `.tv-prompt-label` in `app.src.css` (~line 3020).

**Why:** Labels each stage's output section clearly. Matches the user's naming.

**Validation:** Expand a stage — "Output Summary" label appears above the output content.

#### Step 1.4 — Clean up `tv-stage-wrap--no-inputs` CSS

**File:** `ccya/static/app.src.css`

**What:** Search for `.tv-stage-wrap--no-inputs` rules and remove them. The class is no longer used after Step 1.1.

**Why:** Dead CSS removal.

**Validation:** Run `make check` — no errors.

### Tests to write or update

N/A during refactor phase.

## Implementation — Phase 2: Mobile full-screen turn view

Single-turn-at-a-time on mobile with up/down swipe navigation and thin status bar.

### Context files to load

| File | Lines | What |
|---|---|---|
| `_turn_viewer.html` | 41–338 | Turn list rendering: body, x-for, turn cards, headers, columns |
| `_turn_viewer.html` | 375–500 | Alpine state and methods: `focusedTurnIdx`, `navToIdx`, `_initSwipe` |
| `app.src.css` | 1833–2050 | Existing `@media (max-width: 768px)` block — extend |
| `app.src.css` | 2832–2970 | Turn card, header, stage CSS — mobile overrides needed |

### Detailed steps

#### Step 2.1 — Add mobile Alpine state

**File:** `ccya/templates/_turn_viewer.html`

**What:** In `tvRoot()` return object, after `activeView`, add:
```javascript
mobileFocusedIdx: 0,
```

In `_collapseTurns()`, after the existing logic, set `mobileFocusedIdx` to the last (most recent) turn index:
```javascript
this.mobileFocusedIdx = Math.max(0, this.turns.length - 1);
```

Add method:
```javascript
navMobileTurn(delta) {
    var vt = this.visibleTurns();
    if (!vt.length) return;
    var newIdx = this.mobileFocusedIdx + delta;
    newIdx = Math.max(0, Math.min(newIdx, vt.length - 1));
    this.mobileFocusedIdx = newIdx;
},
```

**Why:** Tracks which turn is currently visible in full-screen mobile mode. Starts at the most recent turn. The `navMobileTurn` method handles clamped navigation.

**Validation:** Load page on mobile — `mobileFocusedIdx` equals `turns.length - 1` (most recent).

#### Step 2.2 — Mobile full-screen turn rendering

**File:** `ccya/templates/_turn_viewer.html`

**What:** In the `x-for` loop body (starting at line 105), the turn card div gets a mobile display binding:

```html
<template x-if="t.row_kind !== 'seed' && t.row_kind !== 'sanitizer'">
    <div
        class="tv-turn-card"
        :id="'tv-turn-' + t.turn"
        :class="{ 'tv-mobile-hidden': window.innerWidth <= 768 && $refs.turnIdx !== mobileFocusedIdx }"
    >
```

But `$refs` won't work in `x-for`. Better approach: use `x-show` instead, but `x-show` is expensive in a long list. Alternative: compute a derived array.

Simpler approach: wrap the `x-for` body in a template that checks visibility. But the cleanest approach for mobile is to use `x-show` on the outer turn-card div scoped to `idx` matching `mobileFocusedIdx`:

```html
<div
    class="tv-turn-card"
    :id="'tv-turn-' + t.turn"
    x-show="window.innerWidth > 768 || idx === mobileFocusedIdx"
>
```

Where `idx` comes from `(t, idx) in visibleTurns()`. The `x-for` already has `idx` (line 51). Pass it through.

On line 105:
```html
<template x-if="t.row_kind !== 'seed' && t.row_kind !== 'sanitizer'">
    <div :id="'tv-turn-' + t.turn" x-show="window.innerWidth > 768 || idx === mobileFocusedIdx">
```

Same pattern for seed and sanitizer rows — show them on mobile only when `idx === mobileFocusedIdx`.

**Why:** On mobile, only the turn matching `mobileFocusedIdx` is visible. Desktop unaffected.

**Validation:** Mobile: only one turn card visible. Desktop: all turns visible as scrollable list.

#### Step 2.3 — Mobile thin status bar (replaces turn header)

**File:** `ccya/templates/_turn_viewer.html`

**What:** Replace the current `.tv-turn-header` block (lines 107–131) with a conditional — desktop shows full header, mobile shows thin bar:

```html
<div class="tv-turn-header" @click="toggleTurnCollapsed(t.turn)">
    <!-- Desktop: full header unchanged -->
    <div class="tv-turn-header-desktop">
        <div class="tv-turn-number">Turn <span x-text="t.turn"></span></div>
        <div class="tv-turn-input" x-text="t.user_input"></div>
        <div class="tv-turn-meta">...</div>
    </div>
    <!-- Mobile: thin bar -->
    <div class="tv-turn-header-mobile">
        <span class="tv-mobile-turn-num" x-text="'Turn ' + t.turn"></span>
        <span class="tv-mobile-turn-count" x-text="(idx + 1) + ' / ' + visibleTurns().length"></span>
    </div>
    <span class="tv-turn-chevron" ...>▶</span>
</div>
```

CSS: `.tv-turn-header-desktop` visible on desktop, hidden on mobile. `.tv-turn-header-mobile` hidden on desktop, visible on mobile. `.tv-turn-chevron` hidden on mobile.

```css
@media (max-width: 768px) {
    .tv-turn-header-desktop { display: none !important; }
    .tv-turn-chevron { display: none !important; }
    .tv-turn-header-mobile {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 4px 12px;
        font-size: 0.71rem;
        color: var(--text-muted);
        border-bottom: 1px solid var(--border-subtle);
    }
    /* Also hide the main turn-viewer header bar filter/actions on mobile */
    .turn-viewer-header .turn-viewer-meta,
    .turn-viewer-header .turn-viewer-actions,
    .turn-viewer-header .turn-viewer-title {
        display: none;
    }
    .turn-viewer-header .tv-view-toggle {
        display: none !important;
    }
}
```

But wait — there's already a `.tv-view-toggle { display: none; }` in the mobile CSS from Phase 1/previous plan. That's fine.

**Why:** Maximizes screen real estate on mobile. Thin bar shows turn number + position in list.

**Validation:** Mobile — turn header shows only "Turn 3" + "3 / 12". No user input, trace ID, timing, or badges.

#### Step 2.4 — Mobile compact stage headers

**File:** `ccya/templates/_turn_viewer.html` + `app.src.css`

**What:** On mobile, stage headers show only the stage name. The status badge, token bar, timing text, and chevron are hidden.

Add to the `@media (max-width: 768px)` block:
```css
.tv-stage-header .tv-stage-status,
.tv-stage-header .tv-stage-badge,
.tv-stage-header .tv-stage-chevron {
    display: none !important;
}
.tv-stage-header {
    padding: 6px 12px !important;
    font-size: 0.79rem;
}
.tv-stage-name {
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
```

**Why:** Stage chrome takes ~1/3 of screen on mobile. Removing non-essential info leaves more room for content.

**Validation:** Mobile — stage headers show only stage name (e.g., "RULING") with minimal padding.

#### Step 2.5 — Add up/down swipe gesture for turn navigation

**File:** `ccya/templates/_turn_viewer.html`

**What:** Extend `_initSwipe()` method to also handle vertical swipes on mobile for turn navigation.

The current `_initSwipe()` handles left/right swipes for view toggle. Add vertical swipe detection that fires `navMobileTurn(delta)`:

The touchstart handler stays the same. The touchend handler currently only checks dx. Add vertical check:

```javascript
// After existing left/right swipe logic:
// Check for vertical swipe (turn navigation)
var absDx = Math.abs(dx);
var absDy = Math.abs(dy);
if (absDy > absDx && absDy > 40) {
    // Reject near-diagonal: require dy to be dominantly vertical
    if (absDy > absDx * 1.5) {
        // Ensure this wasn't already handled by horizontal swipe
        if (absDx < absDy * 1.5) {
            // Only fire if we didn't trigger a horizontal swipe
        }
    }
}
```

But this is getting complicated. Since we already reject diagonals for the horizontal swipe (abs(dx) < abs(dy) * 1.5), and vertical swipes don't pass that check, any vertical-dominant swipe (>1.5x) will be rejected by the horizontal handler. So vertical swipes naturally fall through.

The cleanest approach: after the horizontal swipe check returns early, add a vertical swipe check:

```javascript
// After existing horizontal logic (or replacing the existing checks):
var absDx = Math.abs(dx);
var absDy = Math.abs(dy);

if (absDy > absDx && absDy > 40) {
    // Vertical swipe — navigate turns
    if (dy < 0) {
        self.navMobileTurn(1);   // swipe up → newer turn
    } else {
        self.navMobileTurn(-1);  // swipe down → older turn
    }
    return;
}

if (absDx > absDy && absDx > 40) {
    // Horizontal swipe — toggle view
    if (dx > 0) {
        self.setView('pipeline');
    } else {
        self.setView('delta');
    }
}
```

Replace the entire existing touchend logic with this combined handler. Reject diagonal swipes by not handling either branch when neither axis is clearly dominant.

**Why:** Single swipe handler for both horizontal (view toggle) and vertical (turn navigation). Diagonal swipes are rejected by the dominance check.

**Validation:** Mobile — swipe up goes to next turn, swipe down goes to previous turn, swipe left/right toggles delta/pipeline. Diagonal swipe does nothing.

#### Step 2.6 — Mobile body overflow hidden, prevent native scroll

**File:** `ccya/static/app.src.css`

**What:** In the `@media (max-width: 768px)` block, add:
```css
.turn-viewer-body {
    overflow: hidden !important;
    touch-action: pan-y;
}
```

But we actually want to prevent vertical scroll entirely (swipe navigation replaces it). Use `touch-action: none` on the viewer:
```css
#tv-root {
    touch-action: none;
}
```

And for the turn card container to fill the viewport:
```css
.tv-turn-card {
    position: absolute;
    inset: 0;
    overflow-y: auto;
    margin: 0;
    border: none;
    border-radius: 0;
}
.turn-viewer-body {
    position: relative;
    overflow: hidden;
    height: calc(100vh - 80px); /* subtract header + filter bar height */
}
```

**Why:** Override browser native scroll. Swipe gestures handle turn navigation. Turn card fills the viewport.

**Validation:** Mobile — no scrollbar. Swipe up/down changes turns. Content within a turn (stage bodies, json blocks) scrolls independently via `overflow-y: auto`.

### Tests to write or update

N/A during refactor phase.
