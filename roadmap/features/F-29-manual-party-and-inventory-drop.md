---
title: "Manual party management and inventory drop"
status: done
urgency: 2
size: medium
created: 2026-07-04
ticket_id: F-29
plan: plans/F-29-manual-party-and-inventory-drop.md
labels:
  - ui
  - api
  - npc
  - inventory
---

## Problem

The `party` boolean field exists on `NPCEntry` and `CompendiumNpcUpdate`, but the LLM never sets it. The scene extractor prompt has a "Party assignment" section that instructs the model to set `party: true` for companions, but this is unreliable in practice.

The player needs direct control over party membership and inventory management.

## Scope

### Party management

- **Remove** the "Party assignment" section from `extract_scene_system.j2` (prompt instructions for LLM to set `party`).
- **Remove** `party` from `CompendiumNpcUpdate` in `models/extraction.py` (no longer emitted by LLM).
- **Keep** `party: bool = False` on `NPCEntry` in `models/state.py` (still used by delta builder for auto-demotion exemption).
- **Add** a party toggle button (blue icon) on each NPC in the scene panel for `present` and `nearby` NPCs.
- Clicking toggles `party` instantaneously (no confirmation).
- Visual state: hollow/grey when `party: false`, blue when `party: true`. Always visible (not hover-only).
- Party toggle is only available for `present` and `nearby` NPCs (not compendium).

### Inventory drop

- **Add** drop buttons on hover over the inventory panel.
- **Add** a "Drop All" button visible on hover.
- **Add** a "Drop N" popup for items with `amount > 1` — number input to select quantity, no second confirmation needed.
- **Add** a confirmation dialog for single-quantity items (amount == 1).
- Dropped items are removed from state entirely (not placed in scene).

### API

- `POST /api/npc/{id}/toggle-party` — toggles `party` on an NPC entry. Returns updated state or error.
- `POST /api/inventory/drop` — accepts `{item_id, amount?}`. If `amount` is omitted, removes the entire item. Returns updated state or error.

### Frontend

- Both toggles use fire-and-forget fetch to the API + optimistic UI update.
- Party icon: small blue circle/roster icon, aligned right on the NPC card.
- Inventory drop buttons: right-aligned, appear only on panel hover.
- Confirmation for single-item drop: styled modal overlay (consistent with existing tooltip patterns).

## Out of scope

- Party roster UI (list of current party members).
- Party-based mechanics (combat bonuses, shared inventory, etc.).
- Picking up dropped items.
- Named vs unnamed NPC distinction for party toggle (applies to all present/nearby NPCs equally).

## Files to touch

- `ccya/prompts/extract_scene_system.j2` — remove party assignment section
- `ccya/models/extraction.py` — remove `party` from `CompendiumNpcUpdate`
- `ccya/server.py` — add two new route handlers
- `ccya/templates/_state_left.html` — add party toggle icon to NPC cards
- `ccya/static/game-utils.js` — add party toggle click handler, inventory drop UI
- `ccya/static/app.src.css` — party icon styling, hover reveal for inventory buttons
- `ccya/templates/_state_right.html` — add hover container for inventory drop buttons
- `docs/architecture/` — update pipeline docs (remove party from scene extractor output)
- `docs/repomap.md` — update module boundaries
