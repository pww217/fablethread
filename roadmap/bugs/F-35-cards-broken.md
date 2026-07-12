---
title: "F-35 turn progress extraction row — resolved"
status: resolved
urgency: 1
size: medium
created: 2026-07-12
ticket_id: B-44
labels: [frontend, bug, F-35-blocker]
design: ../../docs/design/turn-progress-cards-design.md
plan: ../../plans/completed/frontend/turn-progress-cards-plan.md
---

## Description

Resolved. The original turn progress cards implementation was broken; the UI has been simplified to a post-narration extraction row only.

## Final Implementation

- Removed ruling and narration progress cards. These phases complete too quickly to be useful UI.
- Removed the legacy `.progress-strip` creation from `submitTurn()` and deleted dead strip helper code.
- Extraction row (scene/state/record bars) appears at `narrate_done`, fills sequentially, and fades at `turn_complete`.
- Extraction bars activate on `extract_stream_start`, tick every 250ms using server-provided `expected_ms`, and use fallback estimates on first turn.
- Bars use turn-viewer palette colors: `--stage-scene` (green), `--stage-state` (amber), `--stage-storytell` (pink).
- Bars render at 8px height with a flex-filled track.

## Affected Files

- `ccya/static/game-utils.js` — `_showExtractionRow()`, `_activateExtractionBar()`, `_completeExtractionBar()`, `_dismissExtractionRow()`
- `ccya/static/game.js` — SSE `phase` handler, `submitTurn()`
- `ccya/static/app.src.css` / `ccya/static/app-shell.css` — extraction row styles
- `ccya/static/app.css` — regenerated from `app.src.css`

## Design Reference

- [`docs/design/turn-progress-cards-design.md`](../../docs/design/turn-progress-cards-design.md)
- [`roadmap/features/F-35-turn-progress-cards.md`](../../roadmap/features/F-35-turn-progress-cards.md)

## Priority

**P1 — Viewed Per Turn.** Resolved.
