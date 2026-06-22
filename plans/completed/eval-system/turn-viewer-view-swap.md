# Turn Viewer — View Swap + Output Pill Cleanup

## Purpose

Replace the rigid two-column (56/44) layout with a single-column view that swaps between pipeline and deltas, simplify each pipeline stage to an output-only pill, add sessionStorage preference persistence, and add mobile swipe support.

## Problem Statement

The turn viewer's fixed two-column layout makes both columns too narrow for comfortable reading, lacks mobile support, forces prompt/output tab switching to see content, and has no preference persistence.

## Constraints

- Alpine.js only. All state in `tvRoot()`.
- sessionStorage for preference persistence.
- Mobile swipe only (no header button on small screens).
- Touch gesture scoped to `#tv-root` element, not document-level.
- `x-transition.opacity.duration.220ms` for view transitions (consistent with existing `index.html:288` pattern).
- No server-side, API, or data pipeline changes.
- No changes to `index.html`.

## Non-goals

- No per-turn view preference (global only).
- No animated drag preview during swipe.
- No pull-to-refresh or other gestures.
- No tablet-specific breakpoints.
- No changes to input pills, filter bar, turn card headers, live update, or JSON highlighting.

## Solution

Add `activeView` state to `tvRoot()` with sessionStorage persistence, restructure the column containers into two `x-show`-guarded `.tv-view-panel` divs (one per view), add a toggle button in the header (desktop) and swipe gesture (mobile), simplify each pipeline stage body to show output directly (removing prompt/output tabs), and update CSS for full-width single-column layout.

## Firm decisions

1. `activeView` state: `'delta'` (default) or `'pipeline'` — global single value.
2. sessionStorage key: `tv_active_view`.
3. Desktop: toggle button `⇆` in `.turn-viewer-header`, hidden on mobile (`@media (max-width: 768px)`).
4. Mobile: swipe right → pipeline, swipe left → deltas, with dot indicator only.
5. View transitions: `x-transition.opacity.duration.220ms`.
6. Output pills: stage bodies simplified to show output only (no prompt/output tabs). Input pills kept.
7. All output pills collapsed by default when turn expands.

## Risks, Ambiguities, and Blockers

- sessionStorage may throw (private browsing iOS) — wrapped in try/catch.
- `x-transition` and `x-show` on the same element: Alpine handles this correctly.
- Swipe/passive listeners: touch listeners on `#tv-root` using `{ passive: true }` — no scroll blocking.
- No existing mobile turn viewer CSS — adding from scratch.

## Status

`completed`

## Phases

One phase covering both template and CSS changes (tightly coupled — cannot test one without the other).

## Implementation — Phase 1: Column restructure, Alpine state, stage simplification, CSS

### Context files to load

| File | Lines | What |
|---|---|---|
| `ccya/templates/_turn_viewer.html` | 26–34 | Header: toggle button insertion point |
| `ccya/templates/_turn_viewer.html` | 127–351 | Column structure + stage bodies to restructure |
| `ccya/templates/_turn_viewer.html` | 393–583 | `tvRoot()` function — state, init, methods |
| `ccya/static/app.src.css` | 2832–2849 | `.tv-turn-columns`, `.tv-pipeline`, `.tv-diff-panel` |
| `ccya/static/app.src.css` | 2906–2970 | `.tv-pipeline`, `.tv-stage-header` and related |
| `ccya/static/app.src.css` | 1833–1882 | Existing `@media (max-width: 768px)` block — extend |

### Detailed steps

#### Step 1.1 — Add `activeView` state, `setView()`, `_initView()` to `tvRoot()`

**File:** `ccya/templates/_turn_viewer.html`

**What:** After line 404 (`inputPillOpen: {},`), add:
```javascript
activeView: 'delta',
_swipeStartX: 0,
_swipeStartY: 0,
```

After line 483 (closing brace of `toggleInputPill`), add two new methods before `navToIdx`:

```javascript
setView(which) {
    this.activeView = which;
    try { sessionStorage.setItem('tv_active_view', which); } catch(e) {}
},
_initView() {
    try {
        var saved = sessionStorage.getItem('tv_active_view');
        if (saved === 'pipeline' || saved === 'delta') this.activeView = saved;
    } catch(e) {}
},
```

**Why:** Design decision: global preference stored in sessionStorage, default `'delta'`.

**Validation:** Open page — `activeView` in Alpine dev tools shows `'delta'` (or previously saved value). Toggling is verified in Step 1.3.

#### Step 1.2 — Call `_initView()` and `_initSwipe()` in `init()`

**File:** `ccya/templates/_turn_viewer.html`

**What:** In the `init()` function (line 409), after `this.startLive();` (line 419), add:
```javascript
this._initView();
this._initSwipe();
```

Then add `_initSwipe()` method after `_initView()`:

```javascript
_initSwipe() {
    var tvRootEl = document.getElementById('tv-root');
    if (!tvRootEl) return;
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
        if (dx > 0) {
            self.setView('pipeline');
        } else {
            self.setView('delta');
        }
    }, { passive: true });
},
```

**Why:** Initialize view from sessionStorage on load. Register swipe gesture listeners scoped to `#tv-root`.

**Validation:** Load page on mobile viewport (≤768px) — swipe right toggles to pipeline view, swipe left back to deltas. No console errors.

#### Step 1.3 — Add toggle button to header

**File:** `ccya/templates/_turn_viewer.html`

**What:** Between line 28 (`.turn-viewer-meta` closing span) and line 29 (`.turn-viewer-actions` opening div), insert:

```html
<button
    type="button"
    class="tv-view-toggle"
    @click="setView(activeView === 'pipeline' ? 'delta' : 'pipeline')"
    :title="activeView === 'pipeline' ? 'Show Deltas' : 'Show Pipeline'"
>⇆</button>
```

**Why:** Desktop swap control. Hidden on mobile via CSS in Step 1.6.

**Validation:** Click button in desktop viewport — pipeline/delta views swap. Button tooltip updates.

#### Step 1.4 — Restructure columns into view-panel wrappers

**File:** `ccya/templates/_turn_viewer.html`

**What:** Replace the current `.tv-turn-columns` block (lines 127–351):

**Current structure (covers lines 127–351):**
```html
<div class="tv-turn-columns" x-show="!isTurnCollapsed(t.turn)">
    <div class="tv-pipeline">
        <!-- ... stage rows with prompt/output tabs ... -->
    </div>
    <div class="tv-diff-panel">
        <!-- ... failures, pacing, state changes ... -->
    </div>
</div>
```

**New structure:**
```html
<div x-show="!isTurnCollapsed(t.turn)">
    <div x-show="activeView === 'pipeline'" x-transition.opacity.duration.220ms>
        <div class="tv-pipeline">
            <!-- ... stage rows (SIMPLIFIED — see Step 1.5) ... -->
        </div>
    </div>
    <div x-show="activeView === 'delta'" x-transition.opacity.duration.220ms>
        <div class="tv-diff-panel">
            <!-- ... failures, pacing, state changes (UNCHANGED) ... -->
        </div>
    </div>
</div>
```

Remove the outer `.tv-turn-columns` class. The div wrapping both panels serves only as a collapse-triggered visibility container.

**Why:** Two full-width panels, only one shown at a time via `x-show` + opacity transition. The `.tv-view-panel` wrappers get `width: 100%` from CSS in Step 1.6.

**Validation:** Page renders without `.tv-turn-columns` class. Toggling the button switches which panel is visible. No horizontal scrollbar.

#### Step 1.5 — Simplify each pipeline stage to output-only

**File:** `ccya/templates/_turn_viewer.html`

**What:** Replace the stage body content (lines 194–228 — the `x-show="!t.streams[stage].skipped"` block inside each stage) with output-only content.

**Before (current):**
```html
<div x-show="!t.streams[stage].skipped">
    <template x-if="stage === 'ruling' && t.ruling_intent">
        <dl class="tv-rules-dl">...</dl>
    </template>
    <div x-show="t.prompts[stage] && (t.prompts[stage].system || t.prompts[stage].user || t.prompts[stage].output)">
        <div class="tv-prompt-output-tabs">
            <button ...>Prompt</button>
            <button ...>Output</button>
        </div>
        <div class="tv-content-panel" x-show="tabKey(...) !== 'output'">...</div>
        <div class="tv-content-panel" x-show="tabKey(...) === 'output'">...</div>
    </div>
    <div class="tv-no-prompt" ...>No data available</div>
</div>
```

**After (simplified):**
```html
<div x-show="!t.streams[stage].skipped">
    <template x-if="stage === 'ruling' && t.ruling_intent">
        <dl class="tv-rules-dl">...</dl>
    </template>
    <template x-if="stage === 'narrate' && t.prompts.narrate && t.prompts.narrate.output">
        <div class="tv-output-text markdown" x-html="mdNarrative(t)"></div>
    </template>
    <template x-if="stage !== 'narrate' && t.prompts[stage] && t.prompts[stage].output">
        <pre class="tv-pre"><code class="language-json" x-effect="tvInitJsonBlock($el, t.prompts[stage].output)"></code></pre>
    </template>
    <div class="tv-no-prompt" x-show="!t.prompts[stage] || !t.prompts[stage].output">No output data available</div>
</div>
```

Specifically:
1. Remove the entire `.tv-prompt-output-tabs` block (`<div class="tv-prompt-output-tabs">`)
2. Remove the prompt-content panel (`x-show="tabKey(...) !== 'output'">`)
3. Replace the output-content panel with direct rendering (no wrapper `tv-content-panel`)
4. Show ruling intent `dl` only for ruling stage (unchanged behavior)
5. For narrate: render markdown output via existing `mdNarrative()` helper
6. For other stages: render JSON output via `tvInitJsonBlock()`
7. Fallback text: "No output data available" when no output exists

Keep the `tv-rules-dl` block — it appears BEFORE the output content. Keep the `tv-skipped` div above. Keep the input pills row above the stage header — unchanged.

**Why:** Design decision: each pipeline stage shows a single output pill. No prompt/output tabs. Input pills preserved.

**Validation:** Expand a stage — output content appears directly (no tabs). Narrate stage shows markdown. Other stages show JSON. Ruling stage shows intent block + JSON output.

#### Step 1.6 — Add swipe dot indicator inside each turn card

**File:** `ccya/templates/_turn_viewer.html`

**What:** After the closing `</div>` of the new view-panel-container step (after the two view-panel divs), before the `.tv-turn-card` closing div, add:

```html
<div class="tv-swipe-dots" x-show="!isTurnCollapsed(t.turn)">
    <span class="tv-swipe-dot" :class="{ active: activeView === 'delta' }"></span>
    <span class="tv-swipe-dot" :class="{ active: activeView === 'pipeline' }"></span>
</div>
```

This goes inside the `<template x-if="t.row_kind !== 'seed' && t.row_kind !== 'sanitizer'">` block, after the closing `</div>` of the collapse-triggered wrapper, inside the `.tv-turn-card`.

**Why:** Mobile-only visual indicator of which view is active. Desktop hidden via CSS.

**Validation:** Open page at mobile width — dots appear below each expanded turn card. Active dot filled, inactive outlined.

#### Step 1.7 — CSS for desktop single-column layout

**File:** `ccya/static/app.src.css`

**What:** Replace the existing `.tv-turn-columns`, `.tv-pipeline`, `.tv-diff-panel` rules (lines 2832–2849) with:

```css
.tv-turn-columns {
    /* no flex — single column block layout */
}
.tv-pipeline {
    width: 100%;
}
.tv-diff-panel {
    width: 100%;
    min-width: 0;
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius);
    padding: 16px;
}
```

Key deletions from `.tv-diff-panel`: `flex: 0 0 44%`, `position: sticky`, `top: 16px`, `max-height: 80vh`, `overflow-y: auto`.

The `.tv-turn-columns` class is kept (empty) for backward compatibility — any remaining references won't break.

**Why:** Remove flex layout and sticky sidebar. Both panels become full-width block elements in a single-column stack.

**Validation:** Desktop (>768px): pipeline view shows stage rows full-width. Delta view shows diff panel full-width. No sticky behavior. No horizontal scroll.

#### Step 1.8 — CSS for mobile breakpoint (≤768px)

**File:** `ccya/static/app.src.css`

**What:** Extend the existing `@media (max-width: 768px)` block (line 1833) with turn viewer styles. Append before the closing `}` of that block:

```css

  /* ── Turn viewer mobile ── */
  .tv-view-toggle { display: none; }

  .tv-swipe-dots {
    display: flex;
    justify-content: center;
    gap: 6px;
    padding: 6px 0 2px;
  }
  .tv-swipe-dot {
    display: inline-block;
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: transparent;
    border: 1px solid var(--text-muted);
    transition: background 150ms;
  }
  .tv-swipe-dot.active {
    background: var(--text-muted);
  }
```

**Why:** Hide the toggle button on mobile (swipe-only). Show dot indicator with active state.

**Validation:** Mobile viewport (≤768px): toggle button hidden, dots visible below each expanded turn card. Clicking dots not required — they're passive indicators.

#### Step 1.9 — Stage output pills full-width styling

**File:** `ccya/static/app.src.css`

**What:** Add after the `.tv-pipeline` rule (around line 2906):

```css
.tv-pipeline-stage {
    width: 100%;
}
```

Verify there's no `max-width` constraint on `.tv-prompt-text` or `.tv-output-text` that would prevent content from stretching. The `tvInitJsonBlock` rendered `<pre>` elements should already stretch.

**Why:** Each pipeline stage and its output content takes full available width in the single-column layout.

**Validation:** Pipeline view — stage content stretches edge-to-edge within the turn card.

### Tests to write or update

N/A during refactor phase per AGENTS.md constraint.
