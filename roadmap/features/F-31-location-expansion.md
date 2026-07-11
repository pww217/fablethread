---
title: "Location expansion — seed-declared opportunities, first-visit flag, NPC location pinning"
status: idea
urgency: 3
size: large
created: 2026-07-06
ticket_id: F-31
design: docs/design/location-expansion.md
labels:
  - engine
  - seed
  - narration
  - npc
---

## Problem

Locations are an afterthought in seed generation. Each seed produces:
- One starting location as `state.location` (LocationRef: id/name/description)
- 4-5 key locations as `world.locations` (KeyLocation: id/name/description/status/tags)

The key locations exist as seed-declared world map data but are never shown to the narrator, never referenced by ruling, and serve no function beyond being seed-declared facts. Players have no incentive to visit them. Location changes only replace `state.location` — there's no memory of visited places, no exposition about what's interesting at a location, and no narrator guidance toward exploring.

Currently the narrator only describes the current location's seed description string. There's no structured seed data about what makes a location interesting or worth visiting.

## Goals

1. **Seed-declared location opportunities:** Each key location gets a `location_opportunities: list[str]` field (1-2 items). These are narrative opportunities/things the player can do at the location (e.g., "scout from watchtower to survey terrain", "talk to the town alderman about rumors", "visit the local tavern for gossip"). Each ~20-30 chars. Distinct from scene inventory — these are actions/narrative nodes, not physical objects.

2. **First-visit flag:** Track whether the player's current location is a first visit via a boolean flag `first_visit_location: bool` on `state.scene`. Set to `True` on location change if location ID differs from previous location's ID. Same place where `turn_entered` and `location_entered_turn` are already stamped. Used as a signal to the narrator to introduce opportunities into narration when relevant.

3. **Narrator exposition guidance:** Narrate prompt includes a new location context section showing seed-declared opportunities + first_visit flag. Opportunities are permanent context when at a key location — shown on every turn at that location. On first visit (flag True): narrator weaves some opportunities naturally into narration as relevant, not a list. On retrieval (flag False): narrator may note opportunities if narratively appropriate.

4. **NPC location pinning:** `last_seen_location` pinned to `state.location` on state change — NPCs anchored to where they were last seen, won't auto-move when the PC moves. When the extractor detects narration indicating an NPC moved, it overrides the pin and updates `last_seen_location` accordingly. Pin is authoritative but overrideable.

## Scope Decisions

- **Key locations = spatial boundary.** Sub-areas handled through description granularity, not separate location IDs.
- **No extraction schema changes.** Location opportunities feed the seed → narrate pipeline; no runtime extraction.
- **No global extraction changes.** The field is for key locations only.
- **No UI changes in this phase.**
- **Location pinning = one trailing field behavior change.** `last_seen_location` becomes the canonical anchor point for NPCs after location changes.
- **No ruling prompt change.**

## Design

Full design doc: [docs/design/location-expansion.md](../design/location-expansion.md)

## Related Tickets

- [F-32: Scene inventory](../features/F-32-scene-inventory.md) — seed-declared location items as strings (builds on this foundation)
- [F-33: Location threads](../features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival (deferred; seed-declared opportunities alone should make locations feel alive)
- [B-1: Location description overwritten by empty location_change delta](../bugs/B-1.md) — fixed, guard condition prevents empty deltas from overwriting seed data
