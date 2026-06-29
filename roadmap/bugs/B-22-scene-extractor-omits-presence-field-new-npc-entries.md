---
title: "Scene extractor omits presence field on new NPC entries"
status: canceled
canceled: 2026-06-29
canceled_reason: "Superseded by B-24 (consolidated extraction reliability ticket). Fix applied via prompt update."
urgency: 2
size: small
created: 2026-06-28
ticket_id: B-22
labels:
  - engine
  - npc
superseded_by: roadmap/bugs/B-24-extraction-reliability-null-fields-missing-required-data.md
---

## Summary

Scene extractor sometimes omits the `presence` field when creating new NPC entries, violating the extraction mandate that requires `presence="present"` or `presence="nearby"` for all new NPCs.

## Reproduction

In noir-1930s/driven 15-turn eval run (2026-06-28_0.30.0-53-ge6b746b4_e6b746b), turn 11:
- `unnamed_pursuer` extracted with `name`, `bio`, `motivation` but `presence=None` and empty `position`
- Narration clearly places NPC in scene: "A rhythmic, methodical tapping of footsteps echoes from the darkness behind you"
- Expected: `presence="present"` or `presence="nearby"`

## Root Cause

LLM not following prompt instruction: "New name → create entry with presence='present' (in scene) or presence='nearby' (same location, not interacting)."

The prompt says "omit unchanged fields" which may be confusing the LLM into thinking presence can be omitted for new NPCs.

## Fix Applied

Updated `ccya/prompts/extract_scene_system.j2` line 50 to add explicit requirement:
> **Presence is REQUIRED for every NPC update — never omit it.**

## Verification Needed

- Run eval scenarios to verify new NPCs always get presence set
- Check that known NPCs with only position changes still omit presence (correct behavior)
- Verify no regression in NPC presence tracking

## Related

- I-11: World step reads NPC profiles directly from compendium
- B-6: Empty NPC presence brackets (resolved)
- B-15: User-reported NPC/system gaps and hallucinations (resolved)
