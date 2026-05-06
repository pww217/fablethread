# Plan: Streaming UI Improvements

## Goals

1. **Smooth scroll-to-narration** — when narration begins streaming, smoothly animate
   `#narrative-panel`'s `scrollTop` so the top of the new `.narrative-block` (the `> input`
   echo line) aligns flush with the top of the panel viewport. No force-drag during streaming.
   User can scroll freely at any time; if they scroll up the animation aborts immediately.

2. **Smooth text materialization (bonus)** — decouple the LLM token-arrival rate from the
   visual display rate. Buffer received tokens and drain them at a fixed, comfortable speed
   (~6 characters per animation frame at 60 fps ≈ 360 chars/sec). On `narrate_done`, flush
   the remaining queue instantly and do a final clean render.

Both changes are purely in `ccya/templates/index.html`. No backend changes. No new files.
No new dependencies.

---

## Affected Code — Overview

Everything lives in the large `<script>` block in `ccya/templates/index.html` (lines 196–1506).

The two locations that must be changed are structurally identical: `submitTurn()` (line ~801)
and `retryTurn()` (line ~1024). Both build the same SSE streaming flow.

Several module-level helpers also need to be changed or replaced.

---

## Part 1 — Smooth Scroll to Narration Start

### 1.1 — What exists and why it's wrong

**`_scrollNarrativeToReadingAnchor`** (lines 335–344):

```js
function _scrollNarrativeToReadingAnchor(container, anchorEl, ratio) {
    if (!container || !anchorEl) return;
    const r = ratio == null ? 0.25 : ratio;
    const cRect = container.getBoundingClientRect();
    const eRect = anchorEl.getBoundingClientRect();
    const desiredTop = cRect.top + r * cRect.height;
    const delta = eRect.top - desiredTop;
    if (Math.abs(delta) < 6) return;
    container.scrollTop += delta;   // ← instant jump, no animation
}
```

This is called on the first token of narration (inside `_renderStreaming`, line ~887–892):

```js
if (!didScrollToNarrationStart && streamBuf.length > 0) {
    didScrollToNarrationStart = true;
    requestAnimationFrame(() => {
        _scrollNarrativeToReadingAnchor(np, textDiv);  // instant jump
        _startStreamFollow(np, textDiv);                // then drag starts
    });
}
```

**`_startStreamFollow`** (lines 351–376): A `requestAnimationFrame` loop that runs for the
entire duration of streaming, advancing `scrollTop` by up to 28px per frame to keep the
bottom of `textDiv` near the bottom of the panel. This continuously forces the view down as
the LLM writes, preventing the user from reading earlier content.

**The combined effect:** Instant snap to ~25% down the panel, then continuous forced
downward drag through the entire narration. Both behaviours are wrong.

---

### 1.2 — Replace `_scrollNarrativeToReadingAnchor` with an eased animator

**Delete** the entire `_scrollNarrativeToReadingAnchor` function (lines 334–344) and
replace it with:

```js
/**
 * Smoothly animate #narrative-panel's scrollTop so targetEl's top edge
 * aligns with the container's top edge (scrollTop = offsetTop of targetEl
 * relative to the container's scrollable content).
 *
 * If the user scrolls during the animation (detected by external scrollTop
 * change exceeding ABORT_THRESHOLD), the animation cancels immediately.
 *
 * @param {HTMLElement} container  The scrollable element (#narrative-panel).
 * @param {HTMLElement} targetEl   The element whose top we want at the top of the viewport.
 * @param {number}      duration   Animation duration in ms (default 420).
 */
function _smoothScrollContainerToTop(container, targetEl, duration) {
    if (!container || !targetEl) return;
    duration = duration == null ? 420 : duration;

    const startScrollTop = container.scrollTop;

    // targetScrollTop: how far the container needs to be scrolled so that
    // targetEl's top is at the container's visible top edge.
    // targetEl.getBoundingClientRect().top - container.getBoundingClientRect().top
    // gives the current pixel distance between the two tops (in viewport coords).
    // Adding startScrollTop converts that to an absolute scrollTop target.
    const containerTop = container.getBoundingClientRect().top;
    const targetTop    = targetEl.getBoundingClientRect().top;
    const targetScrollTop = startScrollTop + (targetTop - containerTop);

    const delta = targetScrollTop - startScrollTop;
    if (Math.abs(delta) < 4) return;   // already close enough — don't animate

    // Clamp to valid scroll range
    const maxScroll = container.scrollHeight - container.clientHeight;
    const finalScrollTop = Math.max(0, Math.min(maxScroll, targetScrollTop));

    const startTime = performance.now();
    const ABORT_THRESHOLD = 8;   // px of unexpected scrollTop change = user scrolled
    let lastKnownScrollTop = startScrollTop;
    let rafId;

    // easeInOutCubic — smooth acceleration then deceleration
    function ease(t) {
        return t < 0.5
            ? 4 * t * t * t
            : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    function tick(now) {
        // Abort if user has scrolled during animation
        const currentScrollTop = container.scrollTop;
        if (Math.abs(currentScrollTop - lastKnownScrollTop) > ABORT_THRESHOLD) {
            cancelAnimationFrame(rafId);
            return;
        }

        const elapsed  = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        container.scrollTop = startScrollTop + delta * ease(progress);
        lastKnownScrollTop  = container.scrollTop;

        if (progress < 1) {
            rafId = requestAnimationFrame(tick);
        }
    }

    rafId = requestAnimationFrame(tick);
}
```

**Place this function at the same location** where `_scrollNarrativeToReadingAnchor` was —
immediately above the `// Stream-follow scroll:` comment block (around line 334).

---

### 1.3 — Remove `_startStreamFollow` and `_stopStreamFollow`

**Delete** the following functions entirely (lines 349–383):

- `let _streamFollowRafId = null;`
- `function _startStreamFollow(np, textDiv) { ... }`
- `function _stopStreamFollow() { ... }`

These will be replaced by no-ops where they are called. Any remaining calls to
`_stopStreamFollow()` in the file must also be removed (see §1.5 below).

---

### 1.4 — Update the scroll trigger in `submitTurn()` (primary turn flow)

Find this block inside `submitTurn()` (inside `const _renderStreaming = () => { ... }`),
approximately lines 887–893:

```js
// BEFORE
if (!didScrollToNarrationStart && streamBuf.length > 0) {
    didScrollToNarrationStart = true;
    requestAnimationFrame(() => {
        _scrollNarrativeToReadingAnchor(np, textDiv);
        _startStreamFollow(np, textDiv);
    });
}
```

Replace with:

```js
// AFTER
if (!didScrollToNarrationStart && streamBuf.length > 0) {
    didScrollToNarrationStart = true;
    requestAnimationFrame(() => {
        _smoothScrollContainerToTop(np, block);
    });
}
```

Note: The scroll target is `block` (the `.narrative-block` div that contains both `echo`
and `textDiv`), NOT `textDiv`. `block` includes the `> input` echo line, so the user sees
the full context at the top.  `block` is defined earlier in `submitTurn()` and is in closure
scope here — no change needed to capture it.

---

### 1.5 — Remove all remaining `_stopStreamFollow()` calls in `submitTurn()`

After removing `_startStreamFollow` and `_stopStreamFollow`, the following calls to
`_stopStreamFollow()` in `submitTurn()` must be deleted (they will be runtime errors
otherwise):

1. **Line ~910** — inside `es.addEventListener('phase', ...)`, in the `narrate_done` branch:
   ```js
   // DELETE this line only:
   _stopStreamFollow();
   ```

2. **Line ~934** — inside `es.addEventListener('turn_complete', ...)`:
   ```js
   // DELETE this line only:
   _stopStreamFollow();
   ```

3. **Line ~1009** — inside `es.onerror`:
   ```js
   // DELETE this line only:
   _stopStreamFollow();
   ```

Do not delete the surrounding code — only the `_stopStreamFollow()` lines.

---

### 1.6 — Update `retryTurn()` (identical pattern)

`retryTurn()` is a near-copy of `submitTurn()` with one structural difference: it does NOT
have the `didScrollToNarrationStart` guard in `_renderStreaming`. It also never calls
`_startStreamFollow`.

In `retryTurn()`'s `_renderStreaming` (lines ~1098–1103):

```js
// BEFORE
const _renderStreaming = () => {
    streamRafPending = false;
    _configureMarked();
    const html = _renderMarkdown(streamBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
};
```

Replace with:

```js
// AFTER
let didScrollToNarrationStart = false;   // declare just before _renderStreaming
const _renderStreaming = () => {
    streamRafPending = false;
    _configureMarked();
    const html = _renderMarkdown(streamBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
    if (!didScrollToNarrationStart && streamBuf.length > 0) {
        didScrollToNarrationStart = true;
        requestAnimationFrame(() => {
            _smoothScrollContainerToTop(np, block);
        });
    }
};
```

`np` and `block` are already in closure scope in `retryTurn()` — `np` is obtained at the
top of `retryTurn()` via `_narrativePanelEl()` and `block` is constructed just before the
SSE setup.

The `_stopStreamFollow()` call inside `retryTurn()`'s `narrate_done` handler (line ~1119)
must also be deleted:

```js
// Inside retryTurn(), es.addEventListener('phase', ...), narrate_done branch:
// DELETE this line only:
_stopStreamFollow();
```

And line ~1138 in `retryTurn()`'s `turn_complete` handler:

```js
// DELETE this line only:
_stopStreamFollow();
```

And line ~1212 in `retryTurn()`'s `onerror` handler:

```js
// DELETE this line only:
_stopStreamFollow();
```

---

## Part 2 — Smooth Text Materialization (Bonus Goal)

### 2.1 — What exists and why it's jarring

The current approach in both `submitTurn()` and `retryTurn()`:

```js
let streamBuf = '';
let streamRafPending = false;

const _renderStreaming = () => {
    streamRafPending = false;
    _configureMarked();
    const html = _renderMarkdown(streamBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
    // ...scroll logic...
};

const _scheduleStreamRender = () => {
    if (streamRafPending) return;
    streamRafPending = true;
    setTimeout(_renderStreaming, 120);   // batch renders at most ~8×/sec
};

es.addEventListener('narrative_token', (e) => {
    const data = JSON.parse(e.data);
    streamBuf += (data.chunk || '');
    _scheduleStreamRender();
});
```

**The problem:** Token chunks from a local LLM arrive in bursts. A single chunk may be 10–60
characters. Each 120ms render fires `marked.parse()` on the full buffer and replaces
`textDiv.innerHTML` wholesale. The text snaps forward in large irregular jumps — jarring
because the reader's eye loses its place and the rendering feels mechanical.

---

### 2.2 — The fix: a display drain queue

Add a second buffer (`displayBuf` / `pendingQueue`) alongside the existing `streamBuf`.
Incoming tokens still accumulate in `streamBuf` (which becomes the source of truth for the
final flush). A separate `requestAnimationFrame` drain loop moves characters from
`pendingQueue` → `displayBuf` at a fixed rate and re-renders after each step.

This completely decouples "how fast the LLM delivers tokens" from "how fast text appears on
screen."

---

### 2.3 — New module-level drain state and functions

Add the following immediately below the `_stopStreamFollow` function block (or wherever it
was, after §1.3 removal — place it in the same area, around the former line 383):

```js
// ---------------------------------------------------------------------------
// Display drain: decouples token arrival from visual text reveal.
// pendingQueue accumulates raw text; the drain loop reveals it at CHARS_PER_FRAME
// characters per animation frame (~60 fps). Completely display-agnostic —
// the caller supplies the render function so both submitTurn and retryTurn can use it.
// ---------------------------------------------------------------------------
let _drainRafId  = null;
let _drainRender = null;   // function(displayBuf) → void, set by caller

const CHARS_PER_FRAME = 6;   // ~360 chars/sec at 60 fps. Increase for faster reveal.

/**
 * Start draining pendingQueue into displayBuf at CHARS_PER_FRAME chars/frame.
 * Idempotent — safe to call on every token event.
 *
 * @param {object} state  Shared mutable object with keys:
 *                          pendingQueue {string}
 *                          displayBuf   {string}
 * @param {function} renderFn  Called after each drain step with the current displayBuf.
 */
function _startDisplayDrain(state, renderFn) {
    if (_drainRafId !== null) return;   // already running

    function drain() {
        if (state.pendingQueue.length === 0) {
            _drainRafId  = null;
            _drainRender = null;
            return;
        }
        const chunk = state.pendingQueue.slice(0, CHARS_PER_FRAME);
        state.pendingQueue = state.pendingQueue.slice(CHARS_PER_FRAME);
        state.displayBuf  += chunk;
        renderFn(state.displayBuf);
        _drainRafId = requestAnimationFrame(drain);
    }

    _drainRender = renderFn;
    _drainRafId  = requestAnimationFrame(drain);
}

/** Stop the drain loop immediately. Does NOT flush pendingQueue. */
function _stopDisplayDrain() {
    if (_drainRafId !== null) {
        cancelAnimationFrame(_drainRafId);
        _drainRafId  = null;
        _drainRender = null;
    }
}
```

---

### 2.4 — Rewrite the streaming block in `submitTurn()`

Replace the entire streaming state setup and `_renderStreaming` / `_scheduleStreamRender`
/ `narrative_token` handler in `submitTurn()`.

**Find** (lines ~879–904, all of this is inside `submitTurn()`):

```js
// Streaming markdown: keep raw buffer, re-render via marked at most ~5×/s.
let streamBuf = '';
let streamRafPending = false;
let didScrollToNarrationStart = false;
const _renderStreaming = () => {
    streamRafPending = false;
    _configureMarked();
    const html = _renderMarkdown(streamBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
    if (!didScrollToNarrationStart && streamBuf.length > 0) {
        didScrollToNarrationStart = true;
        requestAnimationFrame(() => {
            _scrollNarrativeToReadingAnchor(np, textDiv);
            _startStreamFollow(np, textDiv);
        });
    }
};
const _scheduleStreamRender = () => {
    if (streamRafPending) return;
    streamRafPending = true;
    setTimeout(_renderStreaming, 120);
};

es.addEventListener('narrative_token', (e) => {
    const data = JSON.parse(e.data);
    streamBuf += (data.chunk || '');
    _scheduleStreamRender();
});
```

**Replace with** (this includes the Part 1 scroll fix already applied):

```js
// Streaming: two-buffer architecture.
// streamBuf  — complete LLM output so far (source of truth for final flush).
// drainState — mutable object shared with _startDisplayDrain drain loop.
let streamBuf = '';
let didScrollToNarrationStart = false;
const drainState = { pendingQueue: '', displayBuf: '' };

const _drainRenderFn = (currentDisplayBuf) => {
    _configureMarked();
    const html = _renderMarkdown(currentDisplayBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
    if (!didScrollToNarrationStart && currentDisplayBuf.length > 0) {
        didScrollToNarrationStart = true;
        requestAnimationFrame(() => {
            _smoothScrollContainerToTop(np, block);
        });
    }
};

es.addEventListener('narrative_token', (e) => {
    const data = JSON.parse(e.data);
    const chunk = data.chunk || '';
    streamBuf            += chunk;
    drainState.pendingQueue += chunk;
    _startDisplayDrain(drainState, _drainRenderFn);   // idempotent
});
```

---

### 2.5 — Update the `narrate_done` handler in `submitTurn()`

**Find** (lines ~907–916):

```js
es.addEventListener('phase', (e) => {
    const payload = JSON.parse(e.data);
    if (payload && payload.phase === 'narrate_done') {
        _stopStreamFollow();
        streamRafPending = false;
        textDiv.classList.remove('streaming');
        textDiv.innerHTML = _renderMarkdown(streamBuf);
    }
    _setProgressFromPhase(strip, payload);
});
```

**Replace with:**

```js
es.addEventListener('phase', (e) => {
    const payload = JSON.parse(e.data);
    if (payload && payload.phase === 'narrate_done') {
        // Stop the drain loop and flush any remaining queued characters instantly.
        _stopDisplayDrain();
        drainState.displayBuf   += drainState.pendingQueue;
        drainState.pendingQueue  = '';
        // Final authoritative render from streamBuf (handles any edge-case drift).
        textDiv.classList.remove('streaming');
        _configureMarked();
        textDiv.innerHTML = _renderMarkdown(streamBuf);
    }
    _setProgressFromPhase(strip, payload);
});
```

---

### 2.6 — Update `_turnCancel` in `submitTurn()` to stop the drain

Inside `this._turnCancel = function () { ... }` in `submitTurn()` (lines ~842–872), add one
call at the very top of the cancel body:

```js
this._turnCancel = function () {
    _stopDisplayDrain();    // ← ADD THIS as the first line inside the cancel body
    const t = self._turnEs;
    // ... rest of existing cancel body unchanged ...
};
```

This prevents the drain loop from continuing to render after the user stops a turn.

---

### 2.7 — Rewrite the streaming block in `retryTurn()`

`retryTurn()`'s streaming block (lines ~1096–1113) is simpler (no scroll logic originally).
Apply the same pattern.

**Find:**

```js
let streamBuf = '';
let streamRafPending = false;
const _renderStreaming = () => {
    streamRafPending = false;
    _configureMarked();
    const html = _renderMarkdown(streamBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
};
const _scheduleStreamRender = () => {
    if (streamRafPending) return;
    streamRafPending = true;
    setTimeout(_renderStreaming, 120);
};

es.addEventListener('narrative_token', (e) => {
    const data = JSON.parse(e.data);
    streamBuf += (data.chunk || '');
    _scheduleStreamRender();
});
```

**Replace with:**

```js
let streamBuf = '';
let didScrollToNarrationStart = false;
const drainState = { pendingQueue: '', displayBuf: '' };

const _drainRenderFn = (currentDisplayBuf) => {
    _configureMarked();
    const html = _renderMarkdown(currentDisplayBuf);
    textDiv.innerHTML = html + '<span class="streaming-cursor"></span>';
    if (!didScrollToNarrationStart && currentDisplayBuf.length > 0) {
        didScrollToNarrationStart = true;
        requestAnimationFrame(() => {
            _smoothScrollContainerToTop(np, block);
        });
    }
};

es.addEventListener('narrative_token', (e) => {
    const data = JSON.parse(e.data);
    const chunk = data.chunk || '';
    streamBuf               += chunk;
    drainState.pendingQueue += chunk;
    _startDisplayDrain(drainState, _drainRenderFn);
});
```

---

### 2.8 — Update the `narrate_done` handler in `retryTurn()`

**Find** (lines ~1116–1124):

```js
es.addEventListener('phase', (e) => {
    const payload = JSON.parse(e.data);
    if (payload && payload.phase === 'narrate_done') {
        _stopStreamFollow();
        streamRafPending = false;
        textDiv.classList.remove('streaming');
        textDiv.innerHTML = _renderMarkdown(streamBuf);
    }
    _setProgressFromPhase(strip, payload);
});
```

**Replace with:**

```js
es.addEventListener('phase', (e) => {
    const payload = JSON.parse(e.data);
    if (payload && payload.phase === 'narrate_done') {
        _stopDisplayDrain();
        drainState.displayBuf   += drainState.pendingQueue;
        drainState.pendingQueue  = '';
        textDiv.classList.remove('streaming');
        _configureMarked();
        textDiv.innerHTML = _renderMarkdown(streamBuf);
    }
    _setProgressFromPhase(strip, payload);
});
```

---

### 2.9 — Update `_turnCancel` in `retryTurn()`

Same as §2.6 — add `_stopDisplayDrain()` as the first line inside the cancel body:

```js
this._turnCancel = function () {
    _stopDisplayDrain();    // ← ADD THIS as the first line
    const t = self._turnEs;
    // ... rest of existing cancel body unchanged ...
};
```

---

### 2.10 — CSS: "materialising" fade-in effect (cosmetic, optional but recommended)

The drain loop produces smoother pacing on its own. Adding a CSS animation per-render gives
the "magic cloud platform" feel — new text fades in softly rather than just appearing.

The complication: `marked.parse()` rebuilds the full HTML each render, which recreates all
DOM nodes. A CSS animation keyed to the element's existence (e.g. `animation-name` on
`.narrative-text` itself) will restart on every render, causing a full flicker.

The correct approach: animate a `::after` pseudo-element on `.narrative-text.streaming` that
acts as a soft leading-edge gradient mask. This creates the "text crystallising out of mist"
effect without touching individual tokens or fighting DOM reconstruction.

**Add to `app.src.css`** (after the `.narrative-text.streaming` rule, around line 197):

```css
/* Streaming text materialisation: a soft gradient mask on the leading edge.
   The mask slides down as text grows, making new content appear to dissolve in
   rather than snap into existence. No JS required — pure CSS on the container. */
.narrative-text.streaming {
    white-space: pre-wrap;   /* existing rule — preserve */
    -webkit-mask-image: linear-gradient(
        to bottom,
        black 0%,
        black 70%,
        rgba(0,0,0,0.3) 88%,
        transparent 100%
    );
    mask-image: linear-gradient(
        to bottom,
        black 0%,
        black 70%,
        rgba(0,0,0,0.3) 88%,
        transparent 100%
    );
}
```

**Important:** `.narrative-text.streaming` is added during streaming (via `textDiv.classList`)
but it is NOT currently added in the new flow. The existing code has references to
`textDiv.classList.remove('streaming')` but never `textDiv.classList.add('streaming')`.
You must add it in both `submitTurn()` and `retryTurn()` immediately after creating `textDiv`:

```js
// In submitTurn() and retryTurn(), after:
//   const textDiv = document.createElement('div');
//   textDiv.className = 'narrative-text';
//   textDiv.innerHTML = '<span class="streaming-cursor"></span>';
// ADD:
textDiv.classList.add('streaming');
```

This ensures the CSS mask is active during streaming and removed on `narrate_done` (which
already calls `textDiv.classList.remove('streaming')`).

---

## Complete Change Summary

### Functions deleted

| Name | Lines (approx) | Reason |
|---|---|---|
| `_scrollNarrativeToReadingAnchor` | 335–344 | Replaced by `_smoothScrollContainerToTop` |
| `let _streamFollowRafId = null` | 349 | Follows deleted function |
| `_startStreamFollow` | 351–376 | Follow-drag removed entirely |
| `_stopStreamFollow` | 378–383 | No longer needed |

### Functions added (module-level)

| Name | Location | Purpose |
|---|---|---|
| `_smoothScrollContainerToTop` | Replace `_scrollNarrativeToReadingAnchor` | Eased scroll animation |
| `let _drainRafId` | After former `_stopStreamFollow` block | Drain RAF handle |
| `let _drainRender` | Same | Debug/cleanup reference |
| `const CHARS_PER_FRAME = 6` | Same | Speed tuning constant |
| `_startDisplayDrain(state, renderFn)` | Same | Starts drain loop |
| `_stopDisplayDrain()` | Same | Stops drain loop |

### Changes to `submitTurn()` (inside `game()`)

| What | Change |
|---|---|
| Streaming state vars | Replace `streamBuf`/`streamRafPending`/`didScrollToNarrationStart` with `streamBuf`/`didScrollToNarrationStart`/`drainState` |
| `_renderStreaming` + `_scheduleStreamRender` | Deleted; replaced by `_drainRenderFn` |
| `narrative_token` handler | Route chunk to both `streamBuf` and `drainState.pendingQueue`; call `_startDisplayDrain` |
| `narrate_done` branch in `phase` handler | Replace `_stopStreamFollow()`/`streamRafPending = false` with `_stopDisplayDrain()` + queue flush |
| `turn_complete` handler | Remove `_stopStreamFollow()` call |
| `onerror` handler | Remove `_stopStreamFollow()` call |
| `_turnCancel` body | Add `_stopDisplayDrain()` as first line |
| `textDiv` creation | Add `textDiv.classList.add('streaming')` |

### Changes to `retryTurn()` (inside `game()`)

| What | Change |
|---|---|
| Streaming state vars | Same as `submitTurn()` |
| `_renderStreaming` + `_scheduleStreamRender` | Deleted; replaced by `_drainRenderFn` (now includes scroll trigger) |
| `narrative_token` handler | Same as `submitTurn()` |
| `narrate_done` branch | Same as `submitTurn()` |
| `turn_complete` handler | Remove `_stopStreamFollow()` call |
| `onerror` handler | Remove `_stopStreamFollow()` call |
| `_turnCancel` body | Add `_stopDisplayDrain()` as first line |
| `textDiv` creation | Add `textDiv.classList.add('streaming')` |
| `didScrollToNarrationStart` | Declare before `_renderStreaming`; add first-token scroll trigger |

### Changes to `app.src.css`

| What | Change |
|---|---|
| `.narrative-text.streaming` rule | Add `mask-image` / `-webkit-mask-image` gradient |

---

## Tuning Parameters

| Constant | Location | Default | Effect |
|---|---|---|---|
| `CHARS_PER_FRAME` | Module-level | `6` | Characters revealed per ~16ms frame. 6 ≈ 360 chars/sec. Raise to 10–12 for faster models; lower to 3–4 for more dramatic "typewriter" feel. |
| `duration` in `_smoothScrollContainerToTop` | Call site | `420` (ms) | Scroll animation length. 300ms = snappier; 600ms = cinematic. Adjust at the `requestAnimationFrame` call in `_drainRenderFn`. |
| `ABORT_THRESHOLD` in `_smoothScrollContainerToTop` | Inside function | `8` (px) | How much the user must scroll during animation before it aborts. Lower = more sensitive; 8px is enough to ignore layout reflow noise. |
| CSS mask gradient stops | `app.src.css` | `70% / 88% / 100%` | Controls how much of the text "fades out" at the bottom edge during streaming. `black 80%, transparent 100%` is subtler; `black 60%, transparent 95%` is more dramatic. |

---

## Common Issues and Likely Obstacles

### Issue 1: `block` not in scope inside `_drainRenderFn`

**Symptom:** `ReferenceError: block is not defined` inside `_drainRenderFn` or the scroll
trigger.

**Cause:** `_drainRenderFn` is defined as a `const` inside `submitTurn()` or `retryTurn()`
and closes over `block`. However, in `retryTurn()`, the `block` variable is declared and
assigned only a few lines before `_drainRenderFn`. Ensure the declaration order is:

```
const block = document.createElement('div');
// ... build block ...
let didScrollToNarrationStart = false;
const drainState = { ... };
const _drainRenderFn = (currentDisplayBuf) => { /* uses block */ };
```

`_drainRenderFn` must come AFTER `block` is declared. This is naturally the case in
`submitTurn()` but double-check in `retryTurn()` if you restructure anything.

---

### Issue 2: Drain loop singleton conflict between `submitTurn` and `retryTurn`

**Symptom:** Starting a retry immediately after a regular turn (or vice versa) leaves the
old drain loop running, rendering into a stale or removed `textDiv`.

**Cause:** `_drainRafId` is a module-level variable. If a turn ends abnormally (error,
cancel) and `_stopDisplayDrain()` was not called, the RAF loop may still hold a reference to
the old render function and continue firing.

**Fix:** `_stopDisplayDrain()` is already placed in `_turnCancel`, `narrate_done`, and the
`onerror` handler. Verify all three are present. Also confirm that `submitTurn()` guards
against being called while `this.submitting === true` (it already does — `if (!this.input.trim() || this.submitting || !this.gameStarted) return;`).

If you see the issue during testing, add a defensive `_stopDisplayDrain()` call at the very
beginning of both `submitTurn()` and `retryTurn()`, before any state is set up:

```js
submitTurn() {
    if (!this.input.trim() || this.submitting || !this.gameStarted) return;
    _stopDisplayDrain();   // defensive: kill any orphaned drain from prior turn
    // ... rest of function
```

---

### Issue 3: `textDiv` detached from DOM mid-drain

**Symptom:** The drain loop continues running after the block was removed (e.g. turn
cancelled), writing into a detached DOM node (harmless but wasteful), or throws because
`textDiv.innerHTML` is inaccessible.

**Cause:** `_turnCancel` removes `block` from the DOM (`if (block.parentNode) block.remove()`)
after calling `_stopDisplayDrain()`. If the drain RAF had already been queued for the next
frame before `_stopDisplayDrain()` ran, it will fire once more on the detached node.

**Fix:** Inside `_startDisplayDrain`'s drain function, add a guard:

```js
function drain() {
    if (!state._textDivRef || !state._textDivRef.isConnected) {
        _drainRafId = null;
        return;
    }
    // ... rest of drain
}
```

This requires passing `textDiv` into `drainState` as `drainState._textDivRef = textDiv`
before calling `_startDisplayDrain`. Alternatively, because `_turnCancel` calls
`_stopDisplayDrain()` first, in practice the RAF will have been cancelled before the DOM
removal — this is a belt-and-suspenders check if you want to be safe.

---

### Issue 4: Scroll animation fights layout reflow during first render

**Symptom:** The scroll animation starts, but `block`'s `getBoundingClientRect().top` is
measured before `textDiv` has been laid out (it's empty or has only the cursor span), so
the target position is slightly wrong. After the first drain-render adds text, the block
grows and the scroll target shifts.

**Cause:** `_smoothScrollContainerToTop` is called on the first non-empty `displayBuf`
render. At that point `block` is already in the DOM and `echo` is populated, but `textDiv`
may only have a few characters. The block height is near-zero and the target `scrollTop`
undershoots. As text arrives and the block grows taller, the scroll target increases — but
the animation already finished.

**This is actually acceptable behaviour** — the animation scrolls `block.top` to the
panel's top. As text grows downward, the user sees the echo line at the top and narration
filling in below. This is the desired reading position.

If you find the block starts partially off-screen (very fast LLMs generating many chars
before the first paint), delay the scroll trigger to fire after a slightly longer buffer:

```js
// Change the trigger condition from:
if (!didScrollToNarrationStart && currentDisplayBuf.length > 0) {
// To:
if (!didScrollToNarrationStart && currentDisplayBuf.length >= 40) {
```

40 characters is enough for one short sentence — the block will have a stable height by
then and the scroll target will be accurate.

---

### Issue 5: `narrate_done` fires before drain queue empties

**Symptom:** The final flush in the `narrate_done` handler runs correctly, but users notice
a small jump where the last few characters that were in `pendingQueue` suddenly appear all
at once rather than trickling in.

**Cause:** This is expected and intentional — when the LLM has finished, we flush the
remaining queue instantly so the UI reaches its final state cleanly and the progress strip
can be removed without a delay.

**If the jump is noticeable:** The drain speed (`CHARS_PER_FRAME`) is too low relative to
the average chunk size arriving before `narrate_done`. Increase `CHARS_PER_FRAME` to 10–15.
Alternatively, let the drain continue running after `narrate_done` and only do the
authoritative flush on `turn_complete` (the SSE event after all extraction is done):

```js
// Alternative: don't flush on narrate_done; keep drain running
if (payload && payload.phase === 'narrate_done') {
    textDiv.classList.remove('streaming');
    // No flush — drain loop continues
    // _stopDisplayDrain() and flush happen only on turn_complete
}
```

In `turn_complete`:
```js
es.addEventListener('turn_complete', (e) => {
    _stopDisplayDrain();
    drainState.displayBuf   += drainState.pendingQueue;
    drainState.pendingQueue  = '';
    // ... existing turn_complete logic using result.narrative (authoritative)
});
```

This approach means the blinking cursor and mask gradient remain visible through extraction
(which can be several seconds). Weigh the smoothness tradeoff against the UX of showing
the progress strip without the mask obscuring text.

---

### Issue 6: `app.src.css` vs compiled `app.css`

**Symptom:** CSS changes to `app.src.css` have no effect.

**Cause:** `app.src.css` is the source file. If there is a build step (e.g. Tailwind, PostCSS,
or a `Makefile` target), the compiled output `app.css` is what the browser actually loads
(referenced in `index.html` as `/static/app.css?v={{ css_v|default(0) }}`).

**Check the `Makefile`** for a CSS build command. If there is one, run it after editing
`app.src.css`. If `app.css` IS `app.src.css` (i.e. the same file served directly), the
reference in `index.html` still uses the `.css` extension — confirm the static directory
contains `app.css` and that it is either symlinked to or the same as `app.src.css`.

A safe approach: make the CSS changes directly in `app.css` (the served file) and then
mirror them in `app.src.css` afterward for source consistency.

---

### Issue 7: `_drainRafId` is shared — concurrent turns corrupt state

**Symptom:** If somehow two turns run concurrently (which the `submitting` guard should
prevent), the drain loop for the second turn reuses the module-level `_drainRafId`,
immediately killing the first turn's drain.

**Cause:** `_drainRafId` is a module-level singleton. The `submitting` flag prevents two
turns from running simultaneously, so this should not occur in practice. However, if that
guard is ever relaxed or bypassed, this will silently break.

**Mitigation:** The current architecture is safe. Do not expose `submitTurn` to external
callers without the submitting guard.

---

### Issue 8: Performance with very fast models (>500 chars/sec token delivery)

**Symptom:** With a fast local model or a very short response, `pendingQueue` fills faster
than the drain loop empties it. The visual display lags noticeably behind the LLM, and the
queue may still have hundreds of characters when `narrate_done` fires — causing a large
flush jump.

**Fix:** Increase `CHARS_PER_FRAME`. At 60 fps, `CHARS_PER_FRAME = 6` gives 360 chars/sec.
For a model running at 800 chars/sec, use `CHARS_PER_FRAME = 14`. The principle: set it
to roughly `(model_chars_per_sec / 60) * 1.2` to keep the queue from growing unboundedly.
Add a log during development:

```js
es.addEventListener('narrative_token', (e) => {
    const data = JSON.parse(e.data);
    const chunk = data.chunk || '';
    streamBuf               += chunk;
    drainState.pendingQueue += chunk;
    console.debug('queue depth:', drainState.pendingQueue.length);  // remove before commit
    _startDisplayDrain(drainState, _drainRenderFn);
});
```

If the queue depth grows monotonically, increase `CHARS_PER_FRAME`.

---

## Testing Checklist

After implementing all changes, verify the following manually:

- [ ] Submit a turn. The `> input` echo line scrolls smoothly to the top of the narrative
      panel. No snap or jump. Takes approximately 420ms.
- [ ] During streaming, the view does NOT force-scroll downward. The user can scroll freely.
- [ ] Scrolling upward during the 420ms animation cancels the animation immediately.
- [ ] Text appears at a steady, readable pace — not in large chunks.
- [ ] When `narrate_done` fires, any remaining queued text flushes instantly. The final
      rendered markdown matches what was received (no truncation, no duplication).
- [ ] The blinking cursor disappears correctly on `narrate_done`.
- [ ] Clicking "Stop" (the stop button during a turn) cancels the drain loop and removes
      the block cleanly.
- [ ] Clicking "↻ Retry" works identically to a regular turn for scroll and drain behaviour.
- [ ] Rapid retries (two retries in quick succession) do not leave orphaned drain loops.
- [ ] The CSS fade gradient is visible during streaming and disappears on `narrate_done`
      (because `.streaming` class is removed).
- [ ] Page reload with existing history shows history correctly (no streaming code runs on
      static history — confirmed because the SSE listener is only set up inside `submitTurn`
      and `retryTurn`).

---

## Files Changed

| File | Type of change |
|---|---|
| `ccya/templates/index.html` | All JS changes (scroll, drain, cleanup) |
| `ccya/static/app.src.css` | Add mask gradient to `.narrative-text.streaming` |
| `ccya/static/app.css` | Same CSS change (if separate from `app.src.css`) |
