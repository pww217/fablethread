---
title: "NPC presence does not decay after location change"
status: done
urgency: 3
size: medium
created: 2026-07-10
ticket_id: B-42
labels: []
design:
plan:
  url: plans/b-42-npc-location-demotion-fix-plan.md
  branch:
pr:
  url:
  branch:
----

## Description

When a player changes location, non-party NPCs that were present at the old location are demoted to `nearby` by the location-change handler (`delta_builder.py:225-229`). However, two随后的 bugs prevent this demotion from sticking: the extractor auto-stamps all mentioned NPCs with `last_seen_location` set to the current location, and `apply_npc_scene_management` overrides the demotion with `presence: present`. This means NPCs are effectively never demoted after location changes.

## Evidence

- **Save:** `saves/cordyceps-year-twenty-2026-07-10` (17 turns, Turn 17)
- **Commands:** `trace npc_updates`, `diff 2 17 --section npcs`, `turn <N> --json`, `deltas <N>`

### Trace (Turn 15)

Player arrested, transported from `Central Farmstead` to `holding_cells`.

- T15 START: Daniel Meyer is `presence: present`, `last_seen_location: Central Farmstead` (correct — he was at T14)
- T15 NARRATION: Narrator (seeing Daniel as present) mentions Daniel Meyer in the narration at Central Farmstead
- T15 EXTRACT: Extractor outputs `compendium_npc_update` with Daniel Meyer as `presence: present` (from narration mention)
- T15 STAMPING: `turn_state.py:529` sets Daniel's `last_seen_location = current location` = `Holding Cells` (WRONG — he was at Central Farmstead)
- T15 DEMOTION: `delta_builder.py:225-229` checks `last_seen_location` ... but by this point `last_seen_location` has been stamped to Holding Cells, so demotion doesn't fire (or fires then immediately overridden by `apply_npc_scene_management`)
- T15 END: Daniel Meyer is `presence: present`, `last_seen_location: Holding Cells` (should be `nearby`, `last_seen_location: Central Farmstead`)

Result: Daniel Meyer never gets demoted. He stays at `presence: present` through T16, T17, and beyond.

Compare: `farm_laborers` WAS correctly demoted to `nearby` at T15 because they were NOT in the extractor's compendium update. The demotion worked for them. Daniel Meyer was in the compendium update, so the override happened.

## Root Cause

Three bugs in sequence:

1. **`turn_state.py:529` — location auto-stamping.** The loop stamps `last_seen_location = state.location.name` for EVERY NPC in `compendium_npc_update`, overwriting their tracked old location. This is unconditional — it doesn't check if the extractor set `last_seen_location` explicitly or if it's being auto-inferred.

2. **`state/npcs.py:97-98` — compendium overrides demotion.** When the extractor outputs `compendium_npc_update` with `presence: present`, `apply_npc_scene_management` sets the compendium to `presence: present` AFTER the location demotion fires. The demotion's `nearby` gets overwritten back to `present` in the same pipeline run.

3. **`extract_scene_system.j2` — no `last_seen_location` in output schema.** The extractor prompt doesn't include `last_seen_location` as an output field. The LLM can't explicitly say "NPC stayed at old location" or "NPC followed me to new location" — location is auto-stamped by bug #1 regardless of whether the entity actually moved.

## Affected Components

- `ccya/engine/turn_state.py:526-530` — unconditional `last_seen_location` stamping on ALL compendium updates
- `ccya/state/npcs.py:69-72, 97-112` — compendium updates with `presence` override demotion for old-location NPCs
- `ccya/prompts/extract_scene_system.j2` — extractor output schema missing `last_seen_location`
- `ccya/prompts/narrate_system.j2:39` — narrator instruction about nearby NPCs (already exists but needs strengthening)
- `ccya/state/delta_builder.py:225-229` — location demotion (correct logic, gets overridden by bugs #2)