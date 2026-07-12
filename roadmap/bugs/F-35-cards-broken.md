---
title: "F-35 turn progress cards broken — DOM insertion bug, missing event handlers, missing tick timers, styling mismatches"
status: in_progress
urgency: 1
size: medium
created: 2026-07-12
ticket_id: B-44
labels: [frontend, bug, F-35-blocker]
design: ../../docs/design/turn-progress-cards-design.md
plan: ../../plans/completed/frontend/turn-progress-cards-plan.md
---

## Description

F-35 turn progress cards implementation is fully broken. User sees the old "Determining outcome…" progress strip for the entire turn — no ruling card, no narration card, no extraction row, no progress bars, no colors.

Runs on the `turn-progress-cards` branch (worktree at `ccya-turn-progress-cards`). Server running from worktree at `localhost:8765`.

## Symptom

User submits a turn → sees "Determining outcome…" in the old horizontal strip → nothing else happens → turn eventually completes but no cards ever appear.

## Root Cause Analysis

### Bug 1 — DOM insertion into wrong block (CRITICAL)

`_showProgressCard()` (`game-utils.js:483-484`) and `_showExtractionRow()` (`game-utils.js:563-564`) both use:

```js
var strip = document.querySelector('.progress-strip');
var block = document.querySelector('.narrative-block');
```

`document.querySelector('.narrative-block')` matches the **first** `.narrative-block` in the DOM — which is the opening block or the first historical turn block. The ruling card, narration card, and extraction row are silently inserted into that wrong block instead of the live turn's new block.

The `block` variable is already available locally in the turn submission function (`game.js:774`) but is never passed to these helper functions.

**Fix:** Pass `block` as a parameter to `_showProgressCard` and `_showExtractionRow`, use it directly for DOM insertion instead of `document.querySelector`.

### Bug 2 — `extract_stream_start` SSE events never handled

The SSE `phase` handler (`game.js:880-943`) handles:
- `narrate_done` (line 882)
- `extract_stream_done` (line 901)
- `world_done` (line 909)
- `sanitize_start` / `world_start` (line 928)

But there is **no handler for `extract_stream_start`** events (one emitted per sub-stream: scene, state, record). Bars appear at `narrate_done` via `_showExtractionRow()` but never start spinning or filling because `extract_stream_start` is never listened to.

**Fix:** Add handler for `extract_stream_start` in the SSE phase handler that calls `_activateExtractionBar()`.

### Bug 3 — `_activateExtractionBar()` does not exist

Design doc specifies this function: transitions a bar from inactive (empty outline, no spinner) → active (spinner visible, progress bar fills based on elapsed time). Not implemented.

**Fix:** Implement `_activateExtractionBar(streamName)` that starts the tick timer and spinner for a specific extraction bar.

### Bug 4 — `_fadeInCard()` does not exist

Design doc specifies cards should fade in (`opacity: 0 → 1`, 200ms ease-out) on appearance. `_showProgressCard()` currently creates cards that appear instantly (default `opacity: 1`).

**Fix:** Implement `_fadeInCard(element)` and call it from both `_showProgressCard()` and `_showExtractionRow()`. Add `fadeInCard` keyframe to CSS.

### Bug 5 — Extraction bars have no tick timer

`_showExtractionRow()` creates DOM elements with `data-complete="false"` but never starts a `setInterval` to update `.progress-bar-fill` width. Bars stay at 0% fill until `_completeExtractionBar()` is called, then snap all the way to 100% instantly.

Design expects smooth progress fill per bar: `fill = min(100%, elapsed / expectedMs * 100)` ticking every 250ms.

**Fix:** Each extraction bar needs its own tick timer started on `extract_stream_start` (which is Bug 2's missing handler), updating `.progress-bar-fill` width every 250ms until that bar completes.

### Bug 6 — `_setProgressFromPhase()` is dead code and old strip is never cleared during active turn

`_setProgressFromPhase()` (`game-utils.js:367`) — the old function that cycles the single strip's label on every phase event — is never called from anywhere (confirmed: zero call sites outside its definition). However, the initial strip created at `game.js:791-792` with `data-phase="ruling"` and `_progressStripHTML()` ("Determining outcome…") persists through the entire turn. It's only cleared at `turn_complete` (line 1039), not during active phases.

The new cards are **supposed** to replace the strip visually during pre-narration. But because: (a) cards go into the wrong block, and (b) strip isn't hidden during active turn phases, users see only the old strip.

**Fix:** Clear/hide the progress strip at `ruling_start` (when ruling card appears), and clear it again at `narrate_done`. Also fix Bug 1 so cards actually appear.

## Affected Files

- `ccya/static/game-utils.js` — `_showProgressCard()`, `_showExtractionRow()`, `_progressStripHTML()`, `_clearProgressStrip()`
- `ccya/static/game.js` — SSE `phase` handler (lines 880-943), turn submission (lines 774-797)
- `ccya/static/app.src.css` — missing `fadeInCard` keyframe (if extracting from `app-shell.css`)

## Design Reference

- [`docs/design/turn-progress-cards-design.md`](../../docs/design/turn-progress-cards-design.md)
- [`roadmap/features/F-35-turn-progress-cards.md`](../../roadmap/features/F-35-turn-progress-cards.md)

## Priority

**P1 — Viewed Per Turn.** Every turn the user performs. Makes F-35 completely non-functional. Blocker for merging to main until fixed.

## Remaining Issues

### Card styling must match extraction row

The Ruling card and Narration card (`<div class="progress-card">`) do not visually match the Extraction row styling (`<div class="extraction-row">`). The extraction row has 3 nuclear bars with visual bars (scene/state/record) with nuclear glyphs and nuclear-colored left borders. The ruling and narration cards should also use the nuclear glyph + accent-color bar treatment to be consistent.

Colors should be sourced from the turn viewer palette in `app-shell.css`:
- `--stage-rules` (#8b5cf6) for the ruling card
- `--stage-narrate` (#3b82f6) for the narration card
- `--stage-scene` (#10b981) for the scene extraction bar
- `--stage-state` (#f59e0b) for the state extraction bar
- `--stage-progress` (#ec4899) for the record extraction bar

These same colors are used in the turn viewer for each phase label badge.

### Progress bars not filling up

The extraction bars' `.progress-bar-fill` elements are not visually advancing. The tick timer logic exists but the CSS may be preventing the fill from rendering — likely the `.progress-bar-fill` has a default width of 0% and the inline style is not being applied or is being overridden.

Need to verify:
1. The tick timer (`_barTimers[streamName].timer`) actually fires at 250ms intervals
2. The `fill.style.width` assignment actually updates the DOM element
3. CSS isn't overriding the inline style (e.g. a separate CSS rule for `.progress-bar-fill` that uses `important` or a competing specificity rule)
4. MS isn't overriding the inline style (e.g. a separate CSS rule for `.progress-bar-fill` that uses `important` or a competing specificity rule)

Fix: ensure the fill width is updated, that the CSS class for `.progress-bar` provides the background track, and `.progress-bar-fill` fills horizontally across the track. May need to adjust CSS for `.progress-bar-fill` to use `transition: width 0.25s linear` for visual continuity.

## Priority

**P1 — Viewed Per Turn.** Every turn the user performs. F-35 is partially non-functional — cards appear but are visually inconsistent and progress bars don't animate.
