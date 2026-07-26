# Plan: I-44 — Pre-Stream Progress Bar (Ruling + Narration TTFT)

## Design Reference

- Design: inline in this plan (Decisions below). This change is a small, well-scoped UI addition where the user specified all key decisions in advance through clarifying questions; no separate design doc was produced.
- Ticket: `roadmap/improvements/I-44-pre-stream-progress-bar.md`

## Problem Statement

The in-turn progress UI only shows the three extraction bars (scene / state / record). The ruling phase and narration time-to-first-token — both real, multi-second LLM work — have no visual feedback. The user wants a single blue progress bar that covers the pre-stream latency, visually consistent with the extraction bars below it.

## Firm decisions (from design)

1. **One bar**, not two. Covers the combined `ruling_start → first narration token` window.
2. **Color:** `--stage-narrate` (#3b82f6), the same blue used by the narrate row in the turn viewer.
3. **Label:** `Determining Outcome…` (conversational, matches the extraction-row labels).
4. **Expected duration:** backend computes `pre_stream_expected_ms = avg(ruling.total_ms, last 5) + avg(narrate.first_token_ms, last 5)` and ships it on the `ruling_start` phase event. Client falls back to 5000ms when this value is 0 (turn 1, no history) — same model as the existing extraction bars.
5. **Lifecycle:** show on `ruling_start`; complete (fill to 100%) on `narrate_first_token`; dismiss on `narrate_done` (extraction row takes over). Defensive dismiss on `turn_error` and `es.onerror`.
6. **Layout:** single-bar block, not part of the 3-row extraction table. Sits in the same per-turn block, before the extraction row.
7. **Extraction row de-wrapper (companion change):** drop the grey `background` / `border` / `border-radius` / `padding` from `.extraction-row` so the 3 colored bars sit directly against the page background. The 3 bars keep their individual 15%-mix colors and the 6px stacking gap. Fallback if removing breaks visuals: set `background: var(--bg-base)` (matches the page bg). The new pre-stream bar follows the same no-wrapper style.

## Scope

- **Phase 01:** Backend emits `pre_stream_expected_ms` on the `ruling_start` phase event.
- **Phase 02:** Frontend — pre-stream bar CSS, JS helpers, SSE event wiring.
- **Phase 03:** Documentation updates (`docs/repomap.md`, `docs/architecture/`, `AGENTS.md`).

## Status

`completed`

---

## Phase 01: Backend — ship pre-stream expected ms on `ruling_start`

### Depends on

None.

### Context files to load

- `ccya/engine/ruling.py:160-161` — where the `ruling_start` phase event is constructed.
- `ccya/engine/extraction/utils.py:234` — `_avg_event_ms(save_dir, field_path, n=5)` already averages the last 5 events with a fallback of 0 for < 2 history.
- `ccya/engine/turn.py:373` — `narrate_first_token` phase event is already emitted; the new bar will use it as the completion signal.
- `ccya/engine/turn.py:381` — `first_token_ms` is already persisted under `event.narrate.first_token_ms` per turn.

### What changes

Compute the TTFT average alongside the existing ruling average, and include the sum as a new `pre_stream_expected_ms` field on the `ruling_start` phase event payload. No new persistence, no new events — the underlying `narrate.first_token_ms` is already in `events.jsonl`.

### Where to change

`ccya/engine/ruling.py:160-161` — modify the `phase_events` initial entry.

### Before (current)

```python
exp_ruling_ms = _avg_event_ms(ctx.save_dir, "ruling.total_ms")
phase_events: list[tuple[str, Any]] = [("phase", {"phase": "ruling_start", "expected_ms": exp_ruling_ms})]
```

### After

```python
exp_ruling_ms = _avg_event_ms(ctx.save_dir, "ruling.total_ms")
exp_ttft_ms = _avg_event_ms(ctx.save_dir, "narrate.first_token_ms")
phase_events: list[tuple[str, Any]] = [("phase", {
    "phase": "ruling_start",
    "expected_ms": exp_ruling_ms,
    "pre_stream_expected_ms": exp_ruling_ms + exp_ttft_ms,
})]
```

The new field is additive — existing `expected_ms` semantics are unchanged. `_avg_event_ms` is already imported at `ccya/engine/ruling.py:12`.

### Why

- Lets the client use the same avg-based metric model as the existing extraction bars (no first-turn hack, no hardcoded number in the backend).
- The sum (ruling + TTFT) matches the actual window the bar will cover.
- The `narrate.first_token_ms` data is already in `events.jsonl` — no new logging needed.

### Validation

- Restart the server. Run a turn.
- `curl -N 'http://localhost:8765/turn?input=test'` (or any live turn) and confirm the `ruling_start` phase event payload now contains `pre_stream_expected_ms`.
- After turn 2+, verify the value reflects the sum of the previous turns' ruling + first_token averages.
- On turn 1 (no history), confirm `pre_stream_expected_ms == 0` (client will fall back to 5000ms).

---

## Phase 02: Frontend — pre-stream bar CSS, JS helpers, SSE wiring

### Depends on

Phase 01 (needs the new `pre_stream_expected_ms` field to validate against), but the JS/CSS scaffolding can be written and unit-style verified in isolation against any value, so this is light coupling.

### Context files to load

- `ccya/static/game-utils.js:358-466` — `_showExtractionRow`, `_activateExtractionBar`, `_completeExtractionBar`, `_dismissExtractionRow`, `_getFallbackExpectedMs` — the pattern to mirror.
- `ccya/static/game.js:866-919` — `phase` event handler; specifically the existing `narrate_done` branch (line 868) that calls `_showExtractionRow`, and the early-return for `ruling_start` / `narrate_start` (line 915-918) that we will replace.
- `ccya/static/game.js:858-864` — `narrative_token` SSE handler (we will NOT use this; we'll use the `narrate_first_token` phase event for the completion signal).
- `ccya/static/game.js:1104-1129` — `turn_error` and `es.onerror` handlers (need a defensive dismiss).
- `ccya/static/app-shell.css:290-348` — extraction row/bar CSS to mirror; existing `--stage-narrate` variable defined at `ccya/static/app.src.css:40`.

### What changes

1. **CSS — extraction row de-wrapper.** Remove the grey `background`, `border`, and `border-radius` from `.extraction-row` in `ccya/static/app-shell.css` so the 3 colored bars sit directly against the page background. Keep `margin-top`, `display: flex`, `flex-direction: column`, and `gap: 6px` so the bars still stack. Drop `padding` too — the inner bars carry their own visual weight, and the old padding only made sense as inner spacing for the now-removed border. **Fallback:** if removing `background` causes visual issues during implementation (e.g., the bars blend into the page bg or hit a contrast regression against surrounding turn-block content), set `background: var(--bg-base)` instead — this makes the wrapper the same color as the page bg, achieving the same visual effect while preserving the layout box. The 3 inner `.extraction-bar` colors (green/orange/pink) are unchanged.
2. **CSS — pre-stream bar.** Add a new `.pre-stream-bar` block to `ccya/static/app-shell.css` that reuses the existing `.progress-bar` / `.progress-bar-fill` patterns but uses `--stage-narrate` for color and is a standalone single-bar block (no outer wrapper — consistent with the restyled extraction row).
3. **JS helpers** in `ccya/static/game-utils.js` — add three functions: `_showPreStreamBar(payload, block)`, `_completePreStreamBar()`, `_dismissPreStreamBar()`. Plus a `_getPreStreamFallbackMs()` returning 5000.
4. **SSE wiring** in `ccya/static/game.js`:
   - `ruling_start` phase: call `_showPreStreamBar({ expected_ms: payload.pre_stream_expected_ms || 0 }, block)`.
   - `narrate_first_token` phase: call `_completePreStreamBar()`.
   - `narrate_done` phase: call `_dismissPreStreamBar()` BEFORE `_showExtractionRow(...)` (so the extraction row takes over cleanly).
   - Remove `ruling_start` and `narrate_start` from the early-return at line 915-918 (replaced by the explicit `ruling_start` handler and an explicit no-op for `narrate_start`).
   - Add `_dismissPreStreamBar()` to `turn_error` and `es.onerror` handlers (defensive — no stale bar after a failed turn).

### Where to change

- `ccya/static/app-shell.css:296-305` — modify `.extraction-row` to drop the wrapper styling (item 1 above).
- `ccya/static/app-shell.css` — append a new section after the existing extraction row styles (around line 348) for `.pre-stream-bar` (item 2 above).
- `ccya/static/game-utils.js` — append the three helpers after `_dismissExtractionRow` (around line 466).
- `ccya/static/game.js:866-919` — restructure the `phase` handler.
- `ccya/static/game.js:1104-1129` — add the defensive dismiss.

### Before (current)

```js
// game.js:915-918
if (payload && (payload.phase === 'sanitize_start' || payload.phase === 'world_start' || payload.phase === 'ruling_start' || payload.phase === 'narrate_start')) {
    // No progress UI for these phases; extraction row is shown at narrate_done.
    return;
}
```

### After

```js
// New explicit handler for ruling_start
if (payload && payload.phase === 'ruling_start') {
    _showPreStreamBar({ expected_ms: payload.pre_stream_expected_ms || 0 }, block);
    return;
}
// narrate_start: bar is already filling — no-op (explicit branch for clarity)
if (payload && payload.phase === 'narrate_start') {
    return;
}
// narrate_first_token: complete the bar
if (payload && payload.phase === 'narrate_first_token') {
    _completePreStreamBar();
    return;
}
// sanitize_start / world_start: still no UI
if (payload && (payload.phase === 'sanitize_start' || payload.phase === 'world_start')) {
    return;
}
```

And in the existing `narrate_done` branch (line 868), prepend `_dismissPreStreamBar()` before `_showExtractionRow(...)`.

### CSS contract (snippets are interface contracts — names only, full bodies in source)

```css
.pre-stream-bar { /* single 32px bar, uses --stage-narrate */ }
.pre-stream-bar .progress-bar { /* track, border --stage-narrate */ }
.pre-stream-bar .progress-bar-fill { /* fill, background --stage-narrate */ }
.pre-stream-bar[data-complete="true"] .progress-bar-fill { width: 100% !important; }
```

### JS helper contracts

```js
function _showPreStreamBar(payload, block) { /* append a .pre-stream-bar child to block, start ticking */ }
function _completePreStreamBar() { /* fill bar to 100%, set data-complete=true */ }
function _dismissPreStreamBar() { /* clear interval, fadeOutCard, remove */ }
function _getPreStreamFallbackMs() { return 5000; }
```

### Why

- Mirrors the extraction-bar pattern so the visual language is consistent and the code is easy to read alongside the existing helpers.
- Reuses existing `.progress-bar` / `.progress-bar-fill` styles where possible (only the wrapper and color differ).
- Defensive dismiss in `turn_error` / `es.onerror` prevents a stale bar from lingering after a failed turn.

### Validation

- **Extraction row de-wrapper:** the 3 colored bars (green/orange/pink) sit directly against the page dark background with no grey frame around them. Bars still stack with the existing 6px gap. Top margin from preceding content preserved. If the de-wrapper causes a visual regression (bars collide with surrounding turn-block content, or the 15% color-mix backgrounds look weaker without the elevated wrapper behind them), fall back to `background: var(--bg-base)`.
- **Pre-stream bar:** Turn 1: bar appears with "Determining Outcome…" label, ~5s expected, fills smoothly during ruling, continues filling through narrate setup, snaps to 100% on first narration token, dismisses when extraction row appears.
- **Pre-stream bar:** Turn 2+: bar uses sum of last-5-turn averages (visible in the dev console — log the value once during dev).
- **Pre-stream bar:** Color visually matches `--stage-narrate` blue.
- **Pre-stream bar:** Failure path — send a turn that errors (e.g., via the cancel button mid-flight) — bar dismisses, no leftover DOM.
- `make check` (lint + typecheck) passes — no new lint issues from the JS additions (project is JS-only here; ruff/mypy untouched).

---

## Phase 03: Documentation updates

### Depends on

Phases 01 and 02.

### Context files to load

- `docs/repomap.md` — find the "extraction row" or "progress" section to add the new bar nearby.
- `docs/architecture/` — find the step0 / ruling docs and the step1 / narrate docs.
- `AGENTS.md` — the "Conversation references" signpost already mentions extraction bars; add a sentence about the pre-stream bar.

### What changes

1. **`docs/repomap.md`** — under the section that documents the extraction bar lifecycle helpers, note (a) the extraction row is now borderless/backgroundless (de-wrapper change), and (b) add a short paragraph for the pre-stream bar with the three new helper names and the `ruling_start.pre_stream_expected_ms` payload field.
2. **`docs/architecture/`** — in the step0 (ruling) doc, note that the `ruling_start` phase event now ships `pre_stream_expected_ms` and what it means. In the step1 (narrate) doc, note that the `narrate_first_token` phase event is now consumed by the client to complete the pre-stream bar (the event itself is unchanged). In the CSS / progress-bar section, note the extraction row de-wrapper change.
3. **`AGENTS.md`** — extend the "Conversation references" bullet about extraction bars to mention the pre-stream bar and its phase-event triggers (`ruling_start`, `narrate_first_token`, `narrate_done`). Add a brief note that the extraction row no longer has an outer wrapper.

### Where to change

- `docs/repomap.md` — small addition.
- `docs/architecture/step0-ruling.md` and `docs/architecture/step1-narrate.md` (or equivalent filenames — verify exact names during execution).
- `AGENTS.md` — one sentence in the "Conversation references" section.

### Why

Documentation is mandatory per AGENTS.md ("stale docs are bugs"). The pre-stream bar is a new UI element with new phase-event semantics; both need to be findable for future maintenance.

### Validation

- `rg 'pre_stream_expected_ms|pre-stream-bar|PreStreamBar' docs/ AGENTS.md` returns expected matches.
- `rg 'ruling_start' docs/architecture/ AGENTS.md` shows the new doc coverage.
- A quick read of the changed sections confirms the wording is consistent with the codebase.

---

## Risks / non-blocking notes

- **Single-bar failure mode:** if `narrate_first_token` is never emitted (e.g., LLM errors out before first token), the bar will dismiss at `narrate_done` / `turn_error` without completing. Acceptable — same as the existing extraction bars in a hard-fail scenario.
- **Phase order assumption:** the `ruling_start` handler assumes the per-turn SSE `phase` listener is attached before the engine yields `ruling_start`. The existing wiring at `game.js:866` already satisfies this (listener is attached before `EventSource` opens at line 830 and the engine yields phases sequentially). No change needed.
- **First-token race:** the `narrate_first_token` phase event arrives strictly before any `narrative_token` SSE events, so the bar will always complete at or before the first visible token. If a future change reorders these, the bar's "complete before visible streaming" property may break — worth a comment near the handler.
