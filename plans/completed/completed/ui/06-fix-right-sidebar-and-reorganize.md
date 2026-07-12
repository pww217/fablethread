# Fix Right Sidebar and Reorganize Panels

## Status
`completed` — committed in 9cb8733.

## Phases

1 phase: recreate missing `_state_right.html`, move Player card from left to right, add inventory/world_state/debug sections.

## Issue

`_state_right.html` was deleted during Phase 0 (it rendered `recent_events` which was removed), but the template is still referenced by `index.html` and the `/panels/state-right` route. This causes a `TemplateNotFound` 500 error on every page load and HTMX refresh after each turn.

## Solution

Recreate `_state_right.html` with the new right-panel layout: Player bio on top, then Inventory, then World State, then Debug. Remove the Player card from `_state_left.html` so it's not duplicated. The left-side content (Scene, Location, Arc, Compendium) shifts up naturally.

## Firm decisions

1. Player card moves entirely to right panel — no duplication
2. Inventory renders inline from state data (no HTMX sub-request)
3. World state renders inline via existing `_world_state.j2` partial
4. Debug panel reuses existing `_debug.html` content but embedded in the right sidebar panel rather than loaded as a separate HTMX target

## Non-goals

- Does NOT restyle or refactor existing sidebar cards
- Does NOT change the left sidebar card content or structure beyond removing Player
- Does NOT change the `/panels/debug` route or its HTMX wiring (the debug _content_ is embedded in the right sidebar, but the debug-panel route stays for toggling)

## Risks, Ambiguities, and Blockers

- `_state_right.html` does not exist — creating it from scratch. No prior art to evolve from.
- The debug section in the right panel needs `turns`, `errors`, `mock_mode`, `log_llm_io`, `log_prompts`, `log_file` context variables — these are provided by `_debug_context()` in the `/panels/state-right` route.

## Implementation — Phase 1: Create right panel and reorganize

### Context files to load

1. `ccya/templates/_state_left.html` (current left sidebar — Player card to remove)
2. `ccya/templates/_debug.html` (debug panel content to embed)
3. `ccya/server/routes.py` (lines 356-359 — state-right route handler)
4. `ccya/prompts/sections/_world_state.j2` (world state rendering partial)

### Detailed steps

#### Step 1.1 — Remove Player card from left sidebar

**File:** `ccya/templates/_state_left.html`

**What:** Delete lines 1–48 (the Player `<details>` card: the `{% set pc_tag %}`, the NPC/present logic, and the `#card-player` details block up to its closing `</details>`). Keep everything from the `{% if (state.scene.tags or []) or present_npcs %}` Scene card onward.

The four `{% set ... %}` lines at the top (pc_tag, comp, _present, present_npcs) are used by Scene and Compendium cards — keep those. Only remove the Player card block.

**Why:** Player bio moves to the right panel. Left sidebar content shifts up naturally.

**Validation:** `grep -c 'card-player' ccya/templates/_state_left.html` returns 0. Template renders without error.

#### Step 1.2 — Create right panel template

**File:** `ccya/templates/_state_right.html`

**What:** Create a new template with four sections in order:

1. **Player card** — name, tagline, stats grid, conditions pills. Matches the removed block from `_state_left.html` but without the NPC `{% set %}` helpers (those stay in left).
2. **Inventory card** — renders `state.inventory` as a list. Each item shows name, amount, notes. Credits (id="credits") pinned to top.
3. **World state card** — renders via `{% include "sections/_world_state.j2" %}` with `state.scene.world_state`.
4. **Debug card** — embedded `_debug.html` content (turns table, status, errors). Collapsible `<details>`.

Context variables available (from `_debug_context()` in the route handler): `state`, `turns`, `errors`, `mock_mode`, `log_llm_io`, `log_prompts`, `log_file`.

**Why:** This replaces the deleted recent_events panel with the new layout. TemplateNotFound error is resolved.

**Validation:** `curl -s http://localhost:8765/` returns 200. Right sidebar renders inventory and world state correctly.

### Tests to write or update

None — UI-only change, tests deferred per AGENTS.md.

### REPOMAP updates required

None.
