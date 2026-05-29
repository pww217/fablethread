# Resizable & Collapsible Sidebars + Smaller Input

## Status
`completed`

## Phases

3 phases: drag-resize sidebars with collapse/expand toggle and hover hints; halve input box height; polish and build.

## Issue

Sidebars are fixed at 320px each, taking up space users may not need (e.g., when reading long narratives or focusing on one panel). The input textarea is also tall (`min-height: 96px`, ~3 rows), leaving excessive dead space when the user has only a short command.

## Solution

Add narrow drag gutters between narrative and sidebars for resize, click-to-collapse on sidebar edges, hover-reveal hints when collapsed, and reduce the input textarea from `min-height: 96px` to `48px`. All panel state persisted in localStorage. Center narrative column fills freed space automatically via flexbox reflow.

## Firm decisions

1. **Alpine.js reactive state** — Add `leftW`, `rightW`, `leftCollapsed`, `rightCollapsed` properties on the existing `game()` scope, initialized synchronously from localStorage so Alpine hydrates correct values on first render. No separate JS module or framework.
2. **localStorage persistence** — Same pattern as card open states: keys `ccya_panel_left_w`, `ccya_panel_right_w`, `ccya_panel_left_collapsed`, `ccya_panel_right_collapsed`. Restored synchronously in the `game()` return statement; imperative restore also available after Alpine init for edge cases.
3. **Gutter resize** — 4px-wide invisible gutters between narrative and each sidebar. During drag, apply inline `style="width: ..."` on the `<aside>`, overriding CSS variable. Clamp against actual container bounds on every mousemove tick (not just initial calculation) so window resizes during drag don't cause overflow or negative widths.
4. **Collapse by clicking collapsed panel or gutter area** — When a sidebar is collapsed (0px), hovering near that screen edge shows a thin highlight bar as a hint; clicking it restores to default width. Clicking an already-expanded sidebar's outer 12px toggles collapse. On narrow screens (<900px), always collapse since sidebars stack vertically anyway.
5. **Minimum sidebar width: 180px** when not fully collapsed — prevents content from becoming unreadable during resize.
6. **Default widths**: left = 320px, right = 320px (current values). If no persisted state exists or stored value is invalid, fall back to defaults.
7. **Input box halved** — `min-height: 48px` from current `96px`. Change `rows="3"` → `rows="2"`. The textarea still expands as user types or focuses; native `<textarea>` behavior with `resize: none` means it won't grow beyond content, but 2 rows is a good default for short commands.
8. **No top bar collapsing** — out of scope per user request.

## Non-goals

- No keyboard shortcuts for collapse/resize (e.g., Cmd+Shift+B).
- No animation on resize or collapse (instant reflow only; no transition on width changes to avoid jank during drag).
- No responsive breakpoint changes at 900px — existing mobile stack behavior unchanged.
- No server-side changes — all state is client-only in localStorage.

## Risks, Ambiguities, and Blockers

1. **Inline style override vs CSS variable** — The `.sidebar` rule uses `width: var(--sidebar-w)`. Inline styles will take precedence during drag/collapsed states. Need to ensure collapsing (0px width) doesn't break sidebar scroll or content rendering.
2. **Gutter click target is tiny (4px)** — During normal use, gutters are invisible and only become cursor targets when hovering near the edge. This is intentional for minimalism but may feel finicky on first use. The hover hint when collapsed mitigates discoverability.
3. **Alpine.js reactivity with inline styles** — Alpine's `:style` binding works fine for width, but during drag we'll set `.style.width` directly (imperative) rather than reactive to avoid thrashing the virtual DOM or triggering unwanted re-renders on every mousemove tick.

## Implementation — Phase 1: Drag-resize gutters + collapse/expand

### Context files to load
- `ccya/templates/index.html` — main template, Alpine.js game() scope (lines ~707-1386), DOMContentLoaded handler (lines ~1580-1639)
- `ccya/static/app.src.css` — sidebar and layout CSS

### Detailed steps

#### Step 1.1 — Add gutter divs to template HTML

**File:** `ccya/templates/index.html`

**What:** Insert a narrow `<div class="gutter gutter-left"></div>` between the left aside and main, and a `<div class="gutter gutter-right"></div>` between main and right aside. Place them inside `.app-body`, after each sidebar's closing tag:

```html
<div class="app-body">
    <aside class="sidebar sidebar-left" ...>...</aside>
    <div class="gutter gutter-left"></div>

    <main class="narrative-column">...</main>

    <div class="gutter gutter-right"></div>
    <aside class="sidebar">...</aside>
</div>
```

**Why:** Gutters are the drag handles for resizing. They sit between columns as clickable/draggable divs.

#### Step 1.2 — Add Alpine.js reactive state to game() scope, initialized from localStorage

**File:** `ccya/templates/index.html`, inside `game()` return object (~line ~708)

**What:** Replace or augment the existing return statement with these properties and helpers:

```js
// Width state (px or null for collapsed/using default).
// Initialize synchronously from localStorage so Alpine hydrates correct values on first render.
leftW: (() => {
    if (localStorage.getItem('ccya_panel_left_collapsed') === '1') return null;
    const w = parseInt(localStorage.getItem('ccya_panel_left_w') || '320', 10);
    return isNaN(w) ? null : Math.max(180, w);
})(),

rightW: (() => {
    if (localStorage.getItem('ccya_panel_right_collapsed') === '1') return null;
    const w = parseInt(localStorage.getItem('ccya_panel_right_w') || '320', 10);
    return isNaN(w) ? null : Math.max(180, w);
})(),

leftCollapsed: localStorage.getItem('ccya_panel_left_collapsed') === '1',
rightCollapsed: localStorage.getItem('ccya_panel_right_collapsed') === '1',

// Computed width string for :style binding on <aside> elements.
get leftStyle() { return this.leftCollapsed ? 'width: 0; overflow: hidden;' : (this.leftW !== null ? `width: ${this.leftW}px;` : ''); },
get rightStyle() { return this.rightCollapsed ? 'width: 0; overflow: hidden;' : (this.rightW !== null ? `width: ${this.rightW}px;` : ''); },

// Toggle collapse for a given side ('left' or 'right').
toggleCollapse(side) { ... },

// Restore collapsed panel to last saved width or default.
restorePanel(side) { ... },

// Persist current non-null width before collapsing or resizing.
saveWidth(side) { ... },

// Click handler on sidebar — receives $event from template binding.
onSidebarClick(side, e) { ... },

// Initialize gutter drag-resize listeners after DOM is ready.
initGutters() { _setupGutterResize('left', '.gutter-left'); _setupGutterResize('right', '.gutter-right'); },
```

**Why:** Synchronous initialization from localStorage ensures Alpine hydrates correct values on first render, avoiding the timing problem where imperative restore after DOMContentLoaded gets overwritten by initial null/default values. The `initGutters()` method is called from DOMContentLoaded once gutter elements exist in the DOM.

#### Step 1.3 — Bind styles and click handlers to asides

**File:** `ccya/templates/index.html`, left aside (~line ~58) and right aside (~line ~185)

**What:** Add Alpine.js bindings to each `<aside>`. Pass `$event` explicitly so the handler receives it:

Left sidebar:
```html
<aside class="sidebar sidebar-left" :style="leftStyle" @click.self="onSidebarClick('left', $event)">
```

Right sidebar:
```html
<aside class="sidebar" :style="rightStyle" @click.self="onSidebarClick('right', $event)">
```

**Why:** `:style` applies dynamic width. `.self` modifier ensures click only fires when the aside itself is clicked, not its children — this lets us detect clicks on collapsed panels or near edges for restore/toggle. Passing `$event` explicitly avoids relying on a global `event` variable which Alpine.js doesn't expose.

#### Step 1.4 — Implement gutter drag-resize logic

**File:** `ccya/templates/index.html`, add as standalone functions or methods on the game() scope

**What:** Add `_setupGutterResize(side, selector)` and supporting state:

```js
// Drag state (shared across all gutters; only one active at a time).
_dragging: null,  // { side, startX, startW, gutterEl } or null

_setupGutterResize(side, selector) {
    const gutter = document.querySelector(selector);
    if (!gutter) return;

    gutter.addEventListener('mousedown', (e) => {
        e.preventDefault();
        const gi = window._gameInstance;
        if (!gi || gi[side + 'Collapsed']) return; // don't drag collapsed panels

        const sidebarW = gi[side === 'left' ? 'leftW' : 'rightW'] || 320;
        const containerRect = document.querySelector('.app-body').getBoundingClientRect();

        this._dragging = {
            side,
            startX: e.clientX,
            startW: sidebarW,
            gutterEl: gutter,
        };

        // During active drag, set col-resize cursor and disable text selection.
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        gutter.classList.add('active');

        // Global listeners — avoid losing the drag if cursor leaves the gutter or window resizes mid-drag.
        const onMouseMove = (e2) => {
            let delta = e2.clientX - this._dragging.startX;

            // Direction: left sidebar shrinks when dragging right (+delta),
            // right sidebar shrinks when dragging left (-delta).
            if (side === 'right') delta = -delta;

            const newW = Math.max(180, this._dragging.startW + delta);

            // Clamp against actual container bounds on every tick — not just initial calculation.
            // This handles window resizes during drag gracefully: re-read available space each frame.
            if (side === 'left') {
                const maxW = containerRect.width - 400; // narrative min + right sidebar min
                gi.leftW = Math.min(newW, max(180, maxW));
            } else {
                const mainColWidth = document.querySelector('.narrative-column').getBoundingClientRect().width;
                const maxW = containerRect.width - 400; // narrative min + left sidebar min
                gi.rightW = Math.min(newW, Math.max(180, maxW));
            }

            // Persist width as user drags so it survives page reload mid-drag.
            this.saveWidth(side);
        };

        const onMouseUp = () => {
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
            gutter.classList.remove('active');
            if (this._dragging) {
                this.saveWidth(this._dragging.side);
                this._dragging = null;
            }
            // Remove global listeners — use named functions so we can detach them.
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);

            // Clean up if page unloads or tab switches mid-drag.
            window.removeEventListener('beforeunload', onBeforeUnload);
        };

        const onBeforeUnload = () => {
            this.saveWidth(side);
        };

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        window.addEventListener('beforeunload', onBeforeUnload);
    });
},
```

Key constraints during drag:
- Left gutter moves horizontally; delta is relative to initial position (dragging right increases left sidebar, dragging left decreases it)
- Right gutter moves horizontally; direction reversed since gutter sits between main and right sidebar (dragging left shrinks right sidebar, dragging right expands it)
- Clamp minimum width to 180px when not collapsed
- During active drag, set `document.body.style.cursor = 'col-resize'` and disable text selection via `user-select: none`
- **Window resize during drag**: re-read container/narrative bounds on every mousemove tick rather than caching them at drag start. This prevents stale calculations from causing negative widths or overflow if the user resizes their browser mid-drag.
- **Page unload / tab switch cleanup**: `beforeunload` listener saves current width; global listeners removed in onMouseUp to prevent memory leaks

**Why:** Standard split-pane resize pattern. Using global mousemove/mouseup avoids losing the drag if cursor leaves the gutter element or window resizes during interaction.

#### Step 1.5 — Implement collapse/restore logic

**File:** `ccya/templates/index.html`, inside game() scope

**What:** Add these methods to game():

```js
toggleCollapse(side) {
    const key = side + 'Collapsed';
    if (this[key]) {
        // Currently collapsed → restore to last saved width or default 320px.
        this.restorePanel(side);
    } else {
        // Currently expanded → collapse, persisting current width first.
        this.saveWidth(side);   // save current non-null width before collapsing
        this[key] = true;
        if (side === 'left') this.leftW = null;
        else this.rightW = null;
        localStorage.setItem('ccya_panel_' + side + '_collapsed', '1');
    }
},

restorePanel(side) {
    const key = side + 'Collapsed';
    const savedW = parseInt(localStorage.getItem('ccya_panel_' + side + '_w') || '320', 10);
    if (side === 'left') this.leftW = Math.max(180, isNaN(savedW) ? 320 : savedW);
    else this.rightW = Math.max(180, isNaN(savedW) ? 320 : savedW);
    this[key] = false;
    localStorage.setItem('ccya_panel_' + side + '_collapsed', '0');
},

saveWidth(side) {
    const wKey = 'ccya_panel_' + side + '_w';
    if (side === 'left' && this.leftW !== null) {
        try { localStorage.setItem(wKey, String(this.leftW)); } catch {} // guard against quota exceeded
    } else if (side === 'right' && this.rightW !== null) {
        try { localStorage.setItem(wKey, String(this.rightW)); } catch {}
    }
},
```

**Why:** Collapse saves current width to localStorage so restore returns to the last used size. Default fallback is 320px. Try/catch on localStorage guards against quota exceeded or private browsing modes.

#### Step 1.6 — Implement onSidebarClick handler

**File:** `ccya/templates/index.html`, inside game() scope

**What:** Add an `onSidebarClick(side, e)` method that receives `$event` from the template binding:

```js
onSidebarClick(side, e) {
    if (this[side + 'Collapsed']) {
        // Clicking anywhere on a collapsed sidebar restores it.
        this.restorePanel(side);
    } else {
        // Only toggle collapse if click is near the outer edge of the sidebar.
        const selector = side === 'left' ? '.sidebar-left' : '.sidebar';
        const rect = document.querySelector(selector).getBoundingClientRect();
        const isOuterEdge = side === 'left'
            ? (e.clientX - rect.left) < 12   // within 12px of left screen edge
            : (rect.right - e.clientX) < 12;  // within 12px of right screen edge
        if (isOuterEdge || window.innerWidth <= 900) {
            this.toggleCollapse(side);
        }
    }
}
```

**Why:** Clicking near the outer edge of an expanded sidebar collapses it. Clicking anywhere on a collapsed sidebar restores it. On narrow screens (<900px), always collapse since sidebars stack vertically anyway. Uses `$event` parameter from template binding instead of bare `event`.

#### Step 1.7 — Add hover hint for collapsed panels

**File:** `ccya/templates/index.html`, in DOMContentLoaded or as part of initGutters

**What:** When a panel is collapsed, show a thin vertical bar near the screen edge on hover. Use CSS class `.gutter-hint` that appears when hovering within 20px of the left/right screen edges and no sidebar is expanded there. Wider than initial 15px for better discoverability; hint bar widens from 3px to 6px when visible.

Add to DOMContentLoaded (after Alpine init, after gutter setup):
```js
// Track mouse position for edge hover detection — show hints near screen edges when panels are collapsed.
(function setupCollapsedHints() {
    const LEFT_ZONE = 20;   // px from left edge to trigger hint
    const RIGHT_ZONE = 20;  // px from right edge

    function showHint(side, visible) {
        const hint = document.getElementById('hint-' + side);
        if (!hint) return;
        if (visible && !hint.classList.contains('visible')) {
            hint.classList.add('visible');
        } else if (!visible && hint.classList.contains('visible')) {
            hint.classList.remove('visible');
        }
    }

    document.addEventListener('mousemove', (e) => {
        const gi = window._gameInstance;
        if (!gi) return;

        // Left side: show hint when mouse is near left edge AND left panel is collapsed.
        if (e.clientX < LEFT_ZONE && gi.leftCollapsed) {
            showHint('left', true);
        } else {
            showHint('left', false);
        }

        // Right side: show hint when mouse is near right edge AND right panel is collapsed.
        const fromRight = window.innerWidth - e.clientX;
        if (fromRight < RIGHT_ZONE && gi.rightCollapsed) {
            showHint('right', true);
        } else {
            showHint('right', false);
        }
    });

    // Click on hint restores the collapsed panel.
    document.getElementById('hint-left')?.addEventListener('click', () => window._gameInstance?.restorePanel('left'));
    document.getElementById('hint-right')?.addEventListener('click', () => window._gameInstance?.restorePanel('right'));
})();
```

Add hint elements to template body:
```html
<div id="hint-left" class="gutter-hint gutter-hint--left"></div>
<div id="hint-right" class="gutter-hint gutter-hint--right"></div>
```

**Why:** Provides discoverability for collapsed panels without cluttering the UI when sidebars are visible. 20px hover zone and 6px visible width make hints easier to hit than a thin invisible line. Click handlers wired directly on hint elements so they work even if `window._gameInstance` isn't available yet (null-safe via optional chaining).

#### Step 1.8 — Wire initGutters into DOMContentLoaded

**File:** `ccya/templates/index.html`, in DOMContentLoaded handler (~line ~1580)

**What:** Add a call to `initGutters()` near the end of DOMContentLoaded, after Alpine has initialized and gutter elements exist:

```js
// After existing DOMContentLoaded setup...
window._gameInstance?.initGutters();  // set up drag-resize listeners on gutters
```

**Why:** Gutter elements must be in the DOM before `_setupGutterResize` can query them. Placing after Alpine init ensures both `window._gameInstance` and gutter divs exist. Synchronous localStorage reads during game() return (step 1.2) already handle initial state; this step only wires up event listeners.

### Tests to write or update
N/A — tests are temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
None — no new modules or files added; all changes are in existing template and CSS files.

## Implementation — Phase 2: Halve input box height

### Context files to load
- `ccya/templates/index.html` — input bar HTML (~lines 164-180)
- `ccya/static/app.src.css` — `.game-input` styles (~lines 336-352)

### Detailed steps

#### Step 2.1 — Reduce textarea min-height and rows

**File:** `ccya/static/app.src.css`, `.game-input` rule (line ~338)

**What:** Change:
```css
.game-input {
    flex: 1;
    min-height: 48px;   /* was 96px */
    ...
}
```

Also change `rows="3"` to `rows="2"` in the template HTML (~line ~169):
```html
<textarea id="player-input" rows="2" ...>
```

**Why:** Halves from ~96px to ~48px. The textarea still expands as user types or focuses (native `<textarea>` behavior with `resize: none` means it won't grow beyond content, but 2 rows is a good default for short commands).

#### Step 2.2 — Adjust input-bar padding if needed

**File:** `ccya/static/app.src.css`, `.input-bar` rule (~line ~327)

**What:** Review whether the current `padding: 14px 40px;` still looks good with a shorter textarea. If the send button (fixed at 42px height) appears misaligned or cramped, adjust padding-top/bottom by -4px each to compensate.

**Why:** Ensure visual balance between input and send button after shrinking.

### Tests to write or update
N/A — tests are temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
None.

## Implementation — Phase 3: Polish, build CSS, lint check

### Context files to load
- `ccya/static/app.src.css` — add gutter and hint styles

### Detailed steps

#### Step 3.1 — Add gutter and hint CSS

**File:** `ccya/static/app.src.css`, add after sidebar section (~after line ~427)

**What:** Add these rules:

```css
/* =========================================================
   GUTTERS — drag-resize handles between columns
   ========================================================= */

.gutter {
    flex-shrink: 0;
    width: 4px;
    cursor: col-resize;
    background: transparent;
    transition: background 150ms;
    user-select: none;
}
.gutter:hover, .gutter.active {
    background: var(--accent-soft);
}

/* Hover hints for collapsed panels */
.gutter-hint {
    position: fixed;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 40vh;
    background: var(--accent);
    opacity: 0;
    pointer-events: none;
    border-radius: 2px;
    transition: opacity 150ms ease, transform 150ms ease;
}

.gutter-hint--left { left: 8px; }
.gutter-hint--right { right: 8px; }

/* Widened and visible when user hovers near collapsed panel edge. */
.gutter-hint.visible {
    opacity: 0.7;
    pointer-events: auto;
    cursor: ew-resize;
    width: 6px;   /* wider target for easier clicking to restore */
}

.gutter-hint:hover {
    opacity: 1;
}
```

**Why:** Gutters are invisible by default, show a subtle highlight on hover or during active drag. Hints appear near screen edges when panels are collapsed and user hovers nearby — wider (6px) and more opaque when visible for easier clicking to restore the panel.

#### Step 3.2 — Add gutter hint elements to template body

**File:** `ccya/templates/index.html`, add before closing `</body>` tag (~before line ~1642)

**What:**
```html
<!-- Panel resize hints -->
<div id="hint-left" class="gutter-hint gutter-hint--left"></div>
<div id="hint-right" class="gutter-hint gutter-hint--right"></div>
```

#### Step 3.3 — Build CSS and run checks

**What:** Run:
```bash
npx --yes @tailwindcss/cli -i ccya/static/app.src.css -o ccya/static/app.css --minify && make check
```

**Why:** Compile Tailwind source to final CSS, then verify linting and typechecking pass.

### Tests to write or update
N/A — tests are temporarily removed during refactor per AGENTS.md.

### REPOMAP updates required
None.
