---
title: "NPC ghosting — NPCs vanish from compendium state with zero departure tracking"
status: canceled
urgency: 2
size: medium
created: 2026-06-12
labels:
  - Bug
  - Extraction
---

## Bug

NPCs vanish from `state_snapshot.compendium.npcs` without `recently_left` scene tags, `JUST_LEFT` presence tags, or any scene compendium data.

## Evidence

13 turns of confirmed ghosting in cordyceps-year-twenty-2026-06-11 save:
- T4: david_fisher disappears, no scene data
- T5: alexis_henson, joseph_gill disappear, no scene data
- T10: alexis_henson disappears, no scene data
- T12: alexis_henson, pale_creature_upstream disappear, no scene data
- T15: alexis_henson, pale_creature_upstream disappear, no scene data
- T17: alexis_henson disappears, no scene data
- T18: alexis_henson, silas_vane, patrol_soldiers disappear, no scene data
- T19: patrol_soldiers disappear, no scene data
- T20: alexis_henson, silas_vane disappear, no scene data
- T23-T25: alexis_henson, silas_vane, elias_thorne disappear, no scene data
- T27: joseph_gill disappears, no scene data

## Scope

* Investigate why NPCs disappear from compendium without departure tracking
* Ensure scene output includes departure tracking for NPCs that leave
* Add validation in checkers to detect ghosting

## Files

* `ccya/engine/extraction.py` — scene extraction
* `ccya/engine/sanitizer.py` — compendium NPC handling
* `ccya/state/` — compendium state management
* `ccya/ev/checkers/` — NPC presence checker

## Validation

Confirmed in `docs/ev/cordyceps-findings.md §6` — 13 turns of confirmed ghosting with zero scene data for any departure tracking.
