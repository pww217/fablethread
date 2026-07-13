---
title: "Stacked turn progress-bar UI with per-phase cards"
status: done
urgency: 3
size: medium
created: 2026-07-11
completed: 2026-07-12
ticket_id: F-35
labels: [frontend, UI, turn-pipeline]
design:
  url: ../../docs/design/turn-progress-cards-design.md
plan:
  url: ../../plans/completed/frontend/turn-progress-cards-plan.md
pr:
  url: https://github.com/pww217/ccya/pull/15
  branch: turn-progress-cards
---

## Description

Replace the single horizontal progress strip with stacked per-phase cards with progress bars.

### Desired behavior

**Phase 1 — Pre-narration (one card at a time):**
- Ruling card (violet, `--stage-ruling`): appears on `ruling_start`, fills, fades at `narrate_start`.
- Narration card (blue, `--stage-narrate`): appears on `narrate_start`, fills, fades at `narrate_done`.

**Phase 2 — Post-narration (extraction row):**
- Three extraction bars (scene/stage/record) appear together when `narrate_done` fires.
- When record fills, row fades and outcome summary appears.

### Implementation notes

- Functions in `ccya/static/game-utils.js`: `_showRulingCard`, `_showProgressCard`, `_showExtractionRow`, `_fadeOutCard`, `_dismissExtractionRow`.
- Cards use CSS bars (no `<progress>` element).
- Each card manages its own `setInterval` elapsed timer.
- Server sends `expected_ms` in ruling/narration events; `scene/state/record_expected_ms` in `narrate_done`.
- First-turn fallback via `_getFallbackExpectedMs()` returns scene 3000, state 3000, record 6000.

### Remaining issues (2026-07-12)

- **Ruling card format broken**: ruling card renders as full-width pill instead of constrained card. Overrides everything on screen. Attempted `.extraction-bar` format (flat slot-row layout) — broke layout. Reverted to `.progress-card` format but ruling card still overlays entire page. Root cause likely DOM placement (`block.firstChild` inserts into full-width container). Needs proper constrained container or fixed DOM insertion logic.
