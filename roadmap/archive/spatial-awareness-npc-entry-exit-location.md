---
title: "[NPC] Spatial awareness — NPC entry/exit, location announcement"
status: canceled
created: 2026-06-12
labels:
  - Feature
  - Extraction
---

## Detail

Narrator needs more spatial awareness of characters, especially entry and exit. Characters should always have an announced, concise location, and when they leave, mention where they go. This requires a location system in state.

## Scope

* Add location tracking to NPC compendium entries (position field already exists, needs expansion)
* Narrator prompt guidance: announce where NPCs enter from and where they exit to
* Consider building a location web (chess board model) — locations connected to nearby locations
* UI: show location proximity in sidebar (nearby NPCs, touching locations)
* No map needed — just narrative cohesion through location awareness
* New places/quests can be invented at location transitions

## Files

* `ccya/models.py` — NPC model (expand position field, add location references)
* `ccya/engine/extraction.py` — scene extraction (location awareness)
* `ccya/prompts/` — narrator prompts (spatial awareness guidance)
* `ccya/templates/_state_left.html` — location/proximity rendering
* `ccya/state/delta_builder.py` — location change handling

## Related

* TICK-10: NPC left-behind tracking on location change (Completed, partial)
* TICK-26: [ev] location_change checker uses non-existent field names
