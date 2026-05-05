# Plan: New-NPC Compendium Guarantee

> **Status: Deferred from P1.** The LRU + placeholder approach is a bandaid on a
> compendium architecture that will be replaced. A future location-keyed NPC storage
> system (not yet planned) will solve the injection scope problem structurally. Until
> then, the entity dedup plan (`entity-dedup.md`) handles the duplicate creation problem
> via alias matching and extractor prompt guidance.

---

## Original Problem

`_known_characters_for_extract` pulls up to 10 NPCs by LRU order. NPCs present in the
*current scene* can be evicted from context by less-recent but more-frequently-seen NPCs.
A newly-introduced NPC with no compendium entry gets zero context — the extractor has no
stable identity to attach extracted facts to.

This causes:
- Extractor creates a duplicate NPC entry instead of enriching the existing one
- First-encounter NPCs get no compendium row, so their traits are never persisted
- `present_npcs` references IDs the extractor has never seen

## Future Direction: Location-Keyed NPC Storage

Rather than fixing the LRU injection heuristic, the long-term solution is to scope NPC
context by location:

- NPCs are stored per location, not in a flat global compendium
- When the player enters a location, NPCs known to be there are loaded
- The extractor writes new NPCs to the current location's list
- A lightweight global index (ID + home location only, no detail) handles cross-location
  references
- Mobile NPCs (followers, recurring characters) have a home location + "currently at"
  override

This bounds the comparison problem to 3–5 NPCs per scene rather than the full compendium,
eliminating the LRU problem entirely.

## Interim Mitigation

Until location-keyed storage is implemented, `entity-dedup.md` provides:
- Canonical ID format rules that prevent descriptor-based IDs like `scarred_soldier`
- Extractor match instruction to check existing entries before adding
- Alias registry so name revelations route to `npc_update` rather than `npc_add`
- Engine fuzzy match as a safety net

These mitigations don't guarantee new NPCs get compendium entries when evicted from LRU
context, but they prevent the duplicate creation problem.
