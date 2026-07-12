---
title: "Sidebar bugs: departed reason, scene panel, and party toggle race condition"
status: testing
urgency: 3
size: small
created: 2026-07-12
ticket_id: B-43
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Bugs Fixed

Three sidebar UI bugs fixed in `_state_left.html` and `game-utils.js`.

### 1. Departed reason hidden after NPC archived

When a departed NPC was auto-archived (presence changes to "archived" after TTL), the departed reason stopped showing in the compendium tooltip. The departed reason is a permanent field stored on the NPC entry.

**Fix:** Changed `is_departed` condition from `entry.presence.value == 'departed'` → `entry.departed_reason is not none`.

### 2. Scene panel invisible when only nearby NPCs (legacy scene.tags)

Two issues:
- Scene card condition referenced `state.scene.tags` which no longer exist
- Scene card only opened when `present_npcs` existed; nearby-only scenes were invisible
- Nearby NPC section was gated behind `{% if present_npcs %}` so it never displayed when present NPCs left first

**Fix:** Scene card now opens on `present_npcs or nearby_npcs`. Removed `state.scene.tags`. Removed `present_npcs` gate from nearby section. Restored "No one else is around." empty state when neither group exists.

### 3. Party toggle flickers on rapid click + submit

When user clicked the party toggle button and immediately submitted a turn, the HTMX panel reload (triggered by turn completion) happened before the toggle API response. The response handler then ran `classList.toggle()` on a DOM node that had been replaced, so the visual state appeared inconsistent even though the server had the correct data.

**Fix:** Button gets `.toggling` class + `pointer-events: none` on click, re-enabled on API response. Prevents user-visible flicker during concurrent operations.

## Files Changed

- `ccya/templates/_state_left.html` — scene card visibility, nearby NPC gating, departed reason, empty state
- `ccya/static/game-utils.js` — `toggleNpcParty()` race condition guard