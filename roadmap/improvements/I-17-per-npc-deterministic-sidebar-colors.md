---
title: "Per-NPC deterministic sidebar colors for NPC identification"
status: scoping
urgency: 3
size: small
created: 2026-07-04
ticket_id: I-17
labels:
  - Improvement
  - UI
---

## Problem

NPCs in the sidebar and narration are hard to visually distinguish and track across turns. The sidebar uses a uniform style for all NPC entries, making it difficult to identify which NPC is which at a glance.

## Solution

Assign each NPC a deterministic color from a palette of 12 muted, distinguishable colors. The color is derived from the NPC's ID via SHA256 hash, ensuring the same NPC always gets the same color regardless of roster position or story turn.

### Scope

- **`ccya/models/state.py`** — Add `color: str | None = None` field to `NPCEntry`
- **`ccya/engine/seed.py`** — Assign color during seed sanitization for seed-time NPCs
- **`ccya/engine/npc_roster.py`** — Assign color in `build_npc_roster()` for roster entries; fallback to hash if not set
- **`ccya/server/app.py`** — Add `npc_color` Jinja filter using SHA256 hash
- **`ccya/templates/_state_left.html`** — Apply `border-left-color` to present NPCs, nearby NPCs, and compendium NPCs
- **`ccya/static/game-utils.js`** — Add `_npcColor()` function matching Python hash; apply color in `_renderNpcListItem()` sidebar and `_highlightEntities()` narration
- **`ccya/prompts/context.py`** — Verify `NPCRosterEntryBlock` does NOT include `color` field (Pydantic drops it)

### Color palette

12 muted, distinguishable colors for dark backgrounds (Dracula/One Dark palette):
`#e06c75`, `#c67b40`, `#e5c07b`, `#98c379`, `#56b6c2`, `#61afef`, `#bb85f0`, `#be5046`, `#d19a66`, `#98c379`, `#528bff`, `#c678dd`

### Hash algorithm

Python: `sha256(npc_id.encode()).hexdigest()` → first 8 hex chars → `int(..., 16) % 12`
JavaScript: djb2-style hash → `Math.abs(h) % 12`

### Safety

- `color` field is purely for UI rendering — must NOT leak into LLM prompts
- `NPCRosterEntryBlock` in `prompts/context.py` explicitly lists fields — `color` is not included
- SSE `panel_update` includes `color` via `entry.model_dump()` — client-only, not sent to LLM
- Existing saves without `color` field will get colors from hash fallback

### Validation

- [ ] NPCs in sidebar have distinct border-left colors
- [ ] Same NPC always gets same color across turns and restarts
- [ ] Narration entity highlights use per-NPC colors
- [ ] Nearby (non-present) NPCs keep default border color
- [ ] No `color` field in LLM context or prompts
- [ ] Existing saves (without `color` field) work correctly
