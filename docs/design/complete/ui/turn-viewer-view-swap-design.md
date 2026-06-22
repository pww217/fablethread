# Turn Viewer — Pipeline/Deltas View Swap

## Purpose

Redesign the turn viewer column layout to use a single-view approach with a swap control, replacing the rigid two-column (56/44) side-by-side display. Default to the deltas view on first load. Persist the user's view preference per browser session.

## Problem Statement

The current two-column layout is fixed: pipeline (stages, prompts, outputs) always occupies 56% of width and diff panel 44%, simultaneously. On desktop this wastes horizontal space — each column is too narrow for comfortable prompt reading. There is no way to focus on one view at a time.

## Constraints

- Alpine.js only (no React/Vue). All state in `tvRoot()` component.
- sessionStorage for preference persistence (session-scoped, not localStorage).
- Mobile uses swipe gestures only — no header button on small screens.
- Touch gesture detection scoped to `#tv-root` element (not document-level).
- CSS transitions at 220ms for view changes.
- Existing turn viewer CSS classes and design tokens are reused; no new design system.

## Non-goals

- No animated swipe-drag preview of the outgoing panel.
- No per-turn view preference — global only.
- No pull-to-refresh or other gestures beyond left/right swipe.
- No tablet-specific breakpoints.
- No changes to the server, API, or data pipeline.
- No changes to the `index.html` game UI.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Two views only | Pipeline view (5 stage rows with output pills) and Deltas view (failures, pacing, state changes). | Simple binary choice; no third "split" mode. |
| Global preference | Single `activeView` state in `tvRoot()`, not per-turn. | Simpler UX; matches the user's mental model of "what am I looking at". |
| Default: deltas | `activeView = 'delta'` on init. | Per user request — deltas is the landing page. |
| sessionStorage key | `tv_active_view` with value `'pipeline'` or `'delta'`. | Scoped to turn viewer; survives page refresh within session. |
| Desktop swap control | Single toggle button in `.turn-viewer-header`, between title and actions. Icon: `⇆` or similar. Active view shown via `title` attribute. | Minimal chrome; clear affordance. |
| Mobile swap control | Touch swipe only. No button. | Maximizes screen real estate on small viewports. |
| Mobile indicator | Two 4px dots below turn header, centered. Active dot filled, inactive outlined. | Minimal cue that swipeable panels exist. |
| All pills collapsed by default | Each output pill (`x-show` on stage body) starts collapsed when a turn expands. | Clean slate; user opens what they need. Per existing `expanded` state — `toggleExpandAllForTurn` opens all on demand. |
| Input pills preserved | `inputs_snapshot` pills remain above each stage row, unchanged. | No information loss; user retains access to input context. |

## Open Questions

None — all decisions resolved via question phase.

## Current State — What Exists

### Column layout (`_turn_viewer.html:127–351`)

```
.tv-turn-columns { display: flex; gap: 16px; }
.tv-pipeline    { flex: 0 0 56%; }   ← left column: 5 stage rows
.tv-diff-panel  { flex: 0 0 44%; }  ← right column: failures, pacing, state diff
```

Both columns are always visible on desktop. On mobile (≤768px) there is no responsive behavior — the columns overflow horizontally.

### Pipeline stage rows (`_turn_viewer.html:136–234`)

Each stage (ruling, narrate, scene, state, storytell) renders:
1. Input pills row (collapsible, above stage header) — `t.inputs_snapshot[stage]`
2. Stage header row (click to toggle stage body)
3. Stage body: prompt/output tabs → system/user prompt blocks + output block

The stage body uses `x-show="expandedKey(t.turn, stage)"` to toggle. All start collapsed.

### Alpine state (`_turn_viewer.html:395–408`)

```
expanded: {},         // t{turn}-{stage} → bool
stageTabs: {},        // {turn}-{stage} → 'prompt' | 'output'
systemOpenMap: {},    // {turn}-{stage} → bool
turnCollapsed: {},    // turn → bool
inputPillOpen: {},   // t{turn}-{stage}-{src} → bool
```

### CSS for columns (`app.src.css:2832–2849`)

`.tv-pipeline` and `.tv-diff-panel` both have fixed flex basis. Diff panel is `position: sticky`.

## Proposed Solution

### Core Changes

#### 1. New Alpine state in `tvRoot()`

```javascript
activeView: 'delta',   // 'pipeline' | 'delta'
_initView() {
    try {
        var saved = sessionStorage.getItem('tv_active_view');
        if (saved === 'pipeline' || saved === 'delta') this.activeView = saved;
    } catch(e) {}
},
setView(which) {
    this.activeView = which;
    try { sessionStorage.setItem('tv_active_view', which); } catch(e) {}
},
```

#### 2. Header toggle button

In `.turn-viewer-header`, after the title/meta span, add:

```html
<button
    type="button"
    class="tv-view-toggle"
    @click="setView(activeView === 'pipeline' ? 'delta' : 'pipeline')"
    :title="activeView === 'pipeline' ? 'Show Deltas' : 'Show Pipeline'"
>⇆</button>
```

#### 3. Column containers refactored

Replace `.tv-turn-columns` flex layout with two full-width containers, one per view:

```html
<!-- Pipeline view (active when activeView === 'pipeline') -->
<div class="tv-view-panel" x-show="activeView === 'pipeline'">
    <!-- .tv-pipeline content, unchanged -->
</div>

<!-- Delta view (active when activeView === 'delta') -->
<div class="tv-view-panel" x-show="activeView === 'delta'">
    <!-- .tv-diff-panel content, unchanged -->
</div>
```

Both `.tv-view-panel` elements have `width: 100%`. The outer `.tv-turn-columns` flex container is removed (or kept only as a wrapper with no layout role).

#### 4. Desktop CSS

- `.tv-view-panel { width: 100%; }` — single column, full width.
- `.tv-pipeline`, `.tv-diff-panel` inside each panel lose their `flex: 0 0 N%` and become block-level (or `width: 100%`).
- Remove sticky from `.tv-diff-panel` (it no longer competes with adjacent column).
- Prompt content gets more horizontal breathing room: `.tv-prompt-block` `max-width: none` (currently none set, but confirm it stretches).
- Remove the old `.tv-turn-columns { display: flex; }` block or repurpose it.

#### 5. Mobile: swipe gesture + dot indicator

In `tvRoot.init()` after other initialization:

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
    if (Math.abs(dx) < Math.abs(dy) * 1.5) return;   // reject vertical
    if (Math.abs(dx) < 40) return;                    // reject short
    if (dx > 0) {
        self.setView('pipeline');   // swipe right → pipeline
    } else {
        self.setView('delta');      // swipe left  → deltas
    }
}, { passive: true });
```

Dot indicator (inside each `.tv-turn-card`, visible only on mobile):

```html
<div class="tv-swipe-dots" x-show="!isTurnCollapsed(t.turn)">
    <span class="tv-swipe-dot" :class="{ active: activeView === 'delta' }"></span>
    <span class="tv-swipe-dot" :class="{ active: activeView === 'pipeline' }"></span>
</div>
```

#### 6. Stage rows: full-width output pills

The pipeline stage rows already render one stage body at a time. No structural change to stage HTML — just CSS width:
- `.tv-pipeline-stage` gets `width: 100%` (already block, confirm).
- Prompt blocks and output blocks stretch to fill available width.
- Add `padding: 0 4px` adjustment if needed to maximize content area.

### Alternatives Considered and Rejected

| Alternative | Why rejected |
|---|---|
| Tabs inside the pipeline (Prompt \| Output per stage) | Already exists as `stageTabs`. Not the issue — the issue is the two-column desktop layout. |
| Slide-over panel (pipeline slides left to reveal deltas) | More complex JS; requires managing two simultaneous panels in DOM. Simpler to use `x-show` + CSS transitions. |
| URL hash to encode view (`#pipeline` / `#deltas`) | Overkill for a session-only preference. sessionStorage is simpler and doesn't affect browser history. |

## Failure Modes and Risks

- **sessionStorage unavailable**: Wrap in try/catch. Graceful degradation — default view still works, just doesn't persist on refresh.
- **Flash of wrong view on load**: `sessionStorage` read happens synchronously in `init()` before first render. Alpine's `x-cloak` on `.tv-view-panel` prevents flash. If issues persist, use `x-init` to set view before Alpine hydrates.
- **Swipe conflicts with page scroll**: The `Math.abs(dx) < Math.abs(dy) * 1.5` check rejects predominantly vertical gestures. Passive listeners prevent scroll blocking.
- **x-show on panels vs x-show on stage bodies**: Both are independent `x-show` — panels toggle view, stage bodies toggle within a view. No interaction.
- **Mobile viewport detection**: Both CSS (`@media`) and JS (`window.innerWidth > 768`) must agree. JS gates swipe; CSS hides/show dot indicator.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `.tv-turn-columns { display: flex; gap: 16px; }` | `app.src.css` | Flex container no longer needed; replaced by single-column `.tv-view-panel` wrappers. |
| `flex: 0 0 56%` on `.tv-pipeline` | `app.src.css` | Replaced by `width: 100%` in `.tv-view-panel` context. |
| `flex: 0 0 44%`, `position: sticky` on `.tv-diff-panel` | `app.src.css` | No longer sidebar-sticky; full-width within its panel. |

## What Is Unchanged

- `tvRoot()` Alpine component function and all existing state (`expanded`, `stageTabs`, `turnCollapsed`, `inputPillOpen`, `focusedTurnIdx`, etc.).
- `stages: ['ruling', 'narrate', 'scene', 'state', 'storytell']` — stage names and order unchanged.
- Input pills (`inputs_snapshot`) — preserved above each stage row, unchanged.
- All filter bar checkboxes (`onlyRejected`, `onlyRetried`, etc.).
- Turn card header structure, chevron, collapse/expand behavior.
- `prompts[stage]` data shape — system/user/output blocks inside stage body unchanged.
- `failures`, `pacing_context`, `state_diff` data shapes in the delta panel.
- `toggleExpandAllForTurn` and `allExpandedForTurn` — work unchanged per-stage within the pipeline view.
- Live update (`EventSource`) and `mergeTurnsFromServer`.
- `tv-refresh` button behavior.
- `hlAllVisibleJson()` and all JSON highlighting logic.

## New Model Shapes

No new data models. Alpine state additions:

```javascript
activeView: 'delta',   // string: 'pipeline' | 'delta'
setView(which),        // method: writes sessionStorage, updates activeView
_initView(),           // init helper: reads sessionStorage into activeView
```

```javascript
// Mobile swipe state (not reactive, just instance fields)
_swipeStartX: 0,
_swipeStartY: 0,
```

## Context for Implementing LLMs

- `ccya/templates/_turn_viewer.html` lines 26–40 (header), 127–351 (column structure), 395–583 (tvRoot function and all methods)
- `ccya/static/app.src.css` lines 2832–2909 (column and pipeline CSS)
- `ccya/server/tv.py` — unchanged; provides data to turn viewer
- `ccya/server/routes.py:684–733` (`/turn_viewer` route) — unchanged
