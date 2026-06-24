---
title: "[User-Reported] NPC/Character System Gaps and Hallucinations"
status: new
urgency: 3
size: medium
created: 2026-06-24
labels:
  - engine
  - extraction
  - npc
  - scene-management
---
## Problem

Character extraction and management has multiple issues:

1. **All characters need motivation** — Every character (including unnamed NPCs) must have a `motivation` field
2. **Named NPCs need richer profiles** — Named characters should always have: `personality` + `motivation` + 2 of [`fear`, `leverage`, `bond`]
3. **Candidate hints too prescriptive/hallucinating** — Extraction inventing psych states for unnamed NPCs, creating fields that don't exist, hallucinating regular fields
4. **Location drift / NPC persistence** — NPCs not properly managed on location change (scene motion expunging? Setting to nearby?). NPCs drift across locations incorrectly.

## Root Cause Estimate

- Extraction prompts at `ccya/prompts/` not enforcing the named vs. unnamed NPC schema correctly
- Scene transition logic (`ccya/engine/step/` or `scene.py`) not cleaning up or relocating NPCs properly
- Candidate hint generation conflating "psych state" with actual character fields

## Impact

- Bloated/inaccurate character compendium
- Narrative inconsistency (NPCs appearing in wrong locations)
- Hallucinated fields pollute state and downstream prompts

## Suggested Fix

1. Update extraction schema/prompts: enforce named NPC = personality + motivation + 2 of [fear, leverage, bond]; unnamed = motivation only
2. Audit scene transition logic: ensure NPCs are expunged or moved to `nearby` on location change
3. Restrict candidate hints to only valid schema fields; remove psych-state invention for unnamed NPCs