---
title: "Stacked turn progress-bar UI with per-phase cards"
status: in-progress
urgency: 3
size: medium
created: 2026-07-11
ticket_id: F-35
labels: [frontend, UI, turn-pipeline]
design:
  url: ../../docs/design/turn-progress-cards-design.md
plan:
  url: ../../plans/completed/frontend/turn-progress-cards-plan.md
pr:
  url:
  branch: turn-progress-cards
---

## Description

Replace the single horizontal progress strip (`<div class="progress-strip" data-phase="...">`) with a stack of per-phase cards, each showing its own progress bar and filled as that phase completes.

### Desired behavior

**Phase 1 — Pre-narration (one card at a time):**
- Ruling card (violet, `--stage-ruling`): appears on `ruling_start`, fills, fades at `narrate_start`.
- Narration card (blue, `--stage-narrate`): appears on `narrate_start`, fills, fades at `narrate_done`.
- Each card has its own progress bar, spinner, and elapsed timer. Fills at `elapsed / expectedMs`.

**Phase 2 — Post-narration (extraction row):**
- All three extraction bars (scene, state, record) appear together in a single row when `narrate_done` fires.
- Three bars, each with its own color: scene (green), state (amber), record (pink).
- All three remain visible throughout while bars fill sequentially.
- When record fills, the entire row fades and outcome summary appears.

### Remaining issues (2026-07-12)

- **Bar height**: Progress bars are ~4px tall, need ~8px for visibility.
- **Timing accuracy**: Extraction bars do not reliably use per-phase expected_ms from server events — some fall back to hardcoded values. Ruling/narration cards also need validation that they use server-provided timing correctly.
- **Ruling card format**: Still uses `_showProgressCard` / `_createProgressCardHTML` machinery instead of the cleaner `.extraction-bar` single-row layout used by extraction bars.

### Color tokens

| Token | Hex | Role |
|-------|-----|------|
| `--stage-ruling` | `#8b5cf6` | Ruling card (violet) |
| `--stage-narrate` | `#3b82f6` | Narration card (blue) |
| `--stage-scene` | `#10b981` | Scene extraction bar (green) |
| `--stage-state` | `#f59e0b` | State extraction bar (amber) |
| `--stage-storytell` | `#ec4899` | Record extraction bar (pink) |

### Turn pipeline phases (SSE `phase` events)

| # | Phase | Emitted At |
|---|-------|------------|
| 1 | `ruling_start` | `ruling.py:158` |
| 2 | `ruling_done` | `ruling.py:304` |
| 3 | `narrate_start` | `turn.py:307` |
| 4 | `narrate_first_token` | `turn.py:343` |
| 5 | `narrate_done` | `turn.py:360` |
| 6 | `extract_start` | `turn.py:369` |
| 7 | `extract_stream_start(scene)` | `pipeline.py:65` |
| 8 | `extract_stream_done(scene)` | `pipeline.py:110` |
| 9 | `extract_stream_start(state)` | `pipeline.py:65` |
| 10 | `extract_stream_done(state)` | `pipeline.py:110` |
| 11 | `extract_stream_start(record)` | `pipeline.py:65` |
| 12 | `extract_stream_done(record)` | `pipeline.py:110` |
| 13 | `extract_done` | `turn.py:457` |
| 14 | `persist` | `turn.py:228` |
| 15 | `sanitize_start` | `turn.py:760` |
| 16 | `sanitize_done` | `turn.py:776` |
| 17 | `world_start` | `turn.py:786` |
| 18 | `world_done` | `turn.py:855` |

### Implementation notes

- Functions live in `ccya/static/game-utils.js`: `_showProgressCard`, `_fadeOutCard`, `_showExtractionRow`, `_activateExtractionBar`, `_completeExtractionBar`, `_dismissExtractionRow`.
- Cards via `_createProgressCardHTML` generate `.extraction-bar` single-row HTML.
- Extraction bars via `_showExtractionRow` generate `.extraction-row` → `.extraction-bar` → `.progress-bar` → `.progress-bar-fill`.
- Cards use `<progress>`-less CSS bars (no native `<progress>` element).
- Each card manages its own `setInterval` elapsed timer independently.
- When no server-side history exists (first turn), use fallback estimates: ruling 3s, narration 8s, scene 3s, state 3s, record 6s. `_avg_event_ms()` from server takes over after first turns.
- After turn completes, all progress indicators are gone. What remains: narration text, outcome summary, and band summary.
