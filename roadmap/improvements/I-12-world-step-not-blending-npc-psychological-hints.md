---
title: "World step not blending NPC psychological hints into story beats"
status: canceled
urgency: 3
size: medium
created: 2026-06-29
ticket_id: I-12
labels: [world-step, npc, narrative]
---

## Description

World step uses NPC hints separately instead of blending them into coherent story points. Environmental fallbacks are used instead of character-driven beats. `candidate_npcs` is empty on ~20% of turns due to scene extractor LLM failure.

## Canceled

Superseded by I-11. The `candidate_npcs` field was removed from the scene extractor entirely — world step now reads NPC profiles directly from compendium via `build_npc_roster()`. The problem described in this ticket no longer exists.

## Symptoms

- Empty `candidate_npcs` on ~20% of turns (scene extractor LLM failure)
- World step uses hints separately instead of blending into coherent story points
- Environmental fallbacks used instead of character-driven beats
- Beats lack NPC-driven narrative when hints are available

## Root Causes

### Scene extractor LLM failure
- Scene extractor sometimes fails to output `candidate_npcs` field
- Results in empty `candidate_npcs` list passed to world step
- World step then uses environmental fallbacks instead of character-driven beats

### World step not blending hints
- World step receives hints from scene extractor but uses them separately
- No grouping of hints by NPC for better blending
- No instruction to create coherent story points from multiple NPC hints
- World prompt could be strengthened to explicitly blend NPC psychological hints into beats

## Fix Needed

### Scene extractor reliability
- Strengthen prompt guidance for `candidate_npcs` field
- Add validation/retry if `candidate_npcs` is empty when NPCs are present
- Consider adding presence requirement to `candidate_npcs` entries (similar to B-22 fix)

### World step blending
- Add explicit instruction to world prompt to group hints by NPC
- Add guidance to create coherent story points from multiple NPC hints
- Add fallback to NPC profiles from compendium when hints are empty
- Consider adding NPC-driven beat types when `candidate_npcs` is populated

## Related

- I-11: World step reads NPC profiles directly from compendium
- B-22: Scene extractor omits presence field (fixed via prompt update)
- B-24: Extraction reliability — `npcs` field always empty in beats

## Files to Review

- `ccya/prompts/extract_scene_system.j2` — `candidate_npcs` guidance
- `ccya/prompts/world_system.j2` — hint blending instructions
- `ccya/engine/world.py` — hint processing, NPC blending logic
- `ccya/engine/extraction/scene.py` — scene extraction, `candidate_npcs` output