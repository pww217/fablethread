---
title: "Stacked turn progress-bar UI with per-phase cards"
status: up-next
urgency: 3
size: medium
created: 2026-07-11
ticket_id: F-35
labels: [frontend, UI, turn-pipeline]
design:
  url: ../../docs/design/turn-progress-cards-design.md
plan:
  url: ../../plans/turn-progress-cards-plan.md
pr:
  url:
  branch:
---

## Description

Replace the single horizontal progress strip (game.js:787-794) (`<div class="progress-strip" data-phase="...">`) with a stack of per-phase cards, each showing its own progress bar and filled as that phase completes.

### Current behavior

A single `progress-strip` div lives inside each narrative block (created at `game.js:787-794`). On every `phase` SSE event, `_setProgressFromPhase` (`game-utils.js:367-428`) overwrites the label text. The strip cycles through 15 distinct phases during a turn — ruling, narration, extraction, persist, async cleanup — one after another, replacing the label each time. User sees: "Determining outcome…" → "Composing narrative…" → "Updating game state…" → "Refreshing scene…" → "Updating state…" → "Recording Outcome…" → "Saving…" → "Sanitizing state…" → empty (async), with a spinner, ETA, and elapsed counter.

### Desired behavior (hybrid two-phase layout)

A hybrid approach combining the best of both worlds:

**Phase 1 — Pre-narration (one card at a time):**
- Ruling card (violet, `--stage-ruling`): appears on `ruling_start`, fills, fades at `narrate_start`.
- Narration card (blue, `--stage-narrate`): appears on `narrate_start`, fills, fades at `narrate_done`.
- Each card has its own progress bar, spinner, and elapsed timer. Fills at `elapsed / expectedMs`.

**Phase 2 — Post-narration (extraction row):**
- All three extraction bars (scene, state, record) appear together in a single horizontal row when `narrate_done` fires.
- Three bars, each with its own color: scene (green), state (amber), record (pink).
- Only one bar fills at a time. When one completes, the next takes over.
- All three remain visible throughout — user can see each fill up sequentially.
- When record fills (all three complete), the entire row fades and roll pill (outcome summary) appears.

By end of turn: brief ruling card, brief narration card, then 3 colored bars that fill one after another. Visual snapshot of what was in the pipeline.

## Context

### Turn pipeline phases (emitted in order via SSE `phase` events)

| # | Phase | Emitted At | Frontend Handler (`_setProgressFromPhase`) |
|---|-------|------------|-------------------------------------------|
| 1 | `ruling_start` | `ruling.py:158` | "Determining outcome…" |
| 2 | `ruling_done` | `ruling.py:304` | Label cleared |
| 3 | `narrate_start` | `turn.py:307` | "Composing narrative…" |
| 4 | `narrate_first_token` | `turn.py:343` | ETA shows first-token time |
| 5 | `narrate_done` | `turn.py:360` | "Reviewing outcome…" |
| 6 | `extract_start` | `turn.py:369` | "Updating game state…" |
| 7 | `extract_stream_start(scene)` | `pipeline.py:65` | "Refreshing scene…" |
| 8 | `extract_stream_done(scene)` | `pipeline.py:110` | ETA cleared |
| 9 | `extract_stream_start(state)` | `pipeline.py:65` | "Updating state…" |
| 10 | `extract_stream_done(state)` | `pipeline.py:110` | ETA cleared |
| 11 | `extract_stream_start(record)` | `pipeline.py:65` | "Recording Outcome…" |
| 12 | `extract_stream_done(record)` | `pipeline.py:110` | ETA cleared |
| 13 | `extract_done` | `turn.py:457` | "Saving…" |
| 14 | `persist` | `turn.py:228` | "Saving…" |
| 15 | `sanitize_start` | `turn.py:760` | Cleared (async window) |
| 16 | `sanitize_done` | `turn.py:776` | Cleared |
| 17 | `world_start` | `turn.py:786` | Cleared (async window) |
| 18 | `world_done` | `turn.py:855` | Cleared + `asyncRunning = false` |

Extraction streams always run sequentially: `scene → state → record`. No branching or skipping.

### Color tokens (from `tokens.css:39-44`)

| Token | Hex | Role |
|-------|-----|------|
| `--stage-ruling` | `#8b5cf6` | Ruling card (violet) |
| `--stage-narrate` | `#3b82f6` | Narration card (blue) |
| `--stage-scene` | `#10b981` | Scene extraction bar (green) |
| `--stage-state` | `#f59e0b` | State extraction bar (amber) |
| `--stage-storytell` | `#ec4899` | Record extraction bar (pink) |
| `--stage-world` | `#6366f1` | Indigo (not used — async steps hidden) |

### Existing CSS to reuse

- `.progress-spinner` — spinner animation (copy `@keyframes spin` too)
- `.progress-label` — label text
- `.progress-elapsed` — monospace timer
- `.progress-metas` — right-aligned meta group
- Other cards can introduce `.progress-bar` (native `<progress>` element or CSS `height` bar)

### Stacking pattern precedent

- `_state_left.html` / `_state_right.html`: `<details class="sidebar-card">` with `<summary>` and `<div class="sidebar-card-body">` — the dominant card stacking convention in this codebase.
- `_turn_log.html`: `<div class="turn-log-block">` — compact vertical stack, relevant if cards land inside the turn log overlay.

### Existing component state handling

- `_clearProgressStrip` (`game-utils.js:431-437`) clears and removes the strip on `turn_complete`, `turn_error`, `es.onerror`, and user cancel. New stacked-card component needs equivalent cleanup logic.
- Phase events arrive via `EventSource` SSE: `es.addEventListener('phase', ...)` at `game.js:878`.
- `submitting` flag prevents concurrent turns (one progress indicator active).

## Implementation notes

- New component functions should live in `game-utils.js`: `_createRulingCard()`, `_createNarrationCard()`, `_fadeInExtractionBar()`, `_fillExtractionBar()`, `_dismissExtractionRow()`.
- Cards use **fade-in** (no slide animation). Layout lets each card occupy its own space.
- Should not touch any template files — purely JS/CSS in the existing static assets.
- Reuse `--stage-*` CSS variables from `tokens.css` for color consistency with the turn-viewer.
- Progress bars: native `<progress>` element or CSS `height` bar with `background: linear-gradient()`.
- Each card manages its own `setInterval` based elapsed timer independently.
- Extraction bars should remain visible throughout; only the active bar fills — waiting bars stay as empty outlines.
- Extraction row uses a shared container `<div class="extraction-row">` with border/background so it appears/fades as unified panel.
- When no history exists (first turn), use fallback estimates: ruling 3s, narration 8s, scene 3s, state 3s, record 6s. `_avg_event_ms()` takes over after first turns.
- After turn completes, all progress indicators are gone. What remains: narration text, outcome summary, and band summary (identical to current behavior).
