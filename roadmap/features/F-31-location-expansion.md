---
title: "Location expansion — seed-declared details, narrator exposition, first-visit flag"
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
---

## Problem

Locations are an afterthought in seed generation. Each seed produces:
- One starting location as `state.location` (LocationRef: id/name/description)
- 4-5 key locations as `world.locations` (KeyLocation: id/name/description/status/tags)

The key locations exist as seed-declared world map data but are never shown to the narrator, never referenced by ruling, and serve no function beyond being seed-declared facts. Players have no incentive to visit them. Location changes only replace `state.location` — there's no memory of visited places, no exposition about what's interesting at a location, and no narrator guidance toward exploring.

Currently the narrator only describes the current location's seed description string. There's no structured seed data about what makes a location interesting or worth visiting.

## Goals

1. **Seed-declared location details:** Each key location gets a `scene_details: list[str]` field (max 3 items). These are short narrative hooks seed-declared at seed time (e.g., "rusted key on desk", "fresh boot prints in mud", "radio crackling with static"). Each ~20-30 chars. Total ~90 tokens max.

2. **First-visit flag:** Track whether the player's current location is a first visit via a boolean flag `first_visit_location: bool` on `state.scene`. Set to `True` on location change if location ID differs from previous location's ID. Same place where `turn_entered` and `location_entered_turn` are already stamped.

3. **Narrator exposition guidance:** Narrate prompt includes a new location context section showing seed-declared details + first_visit flag. On first visit: narrator should describe details as environmental details the player notices. On revisit: narrator should note details may have changed if the player interacted with them.

4. **Ruling awareness:** One ruling prompt instruction: if player's action involves interacting with a location detail (pick up, examine, use), ruling should NOT mark it as impossible just because the detail isn't in PC inventory. This keeps ruling's impossibility check focused on PC inventory for PC-owned items while allowing location interactions as a separate category.

## Design

Full design doc: [docs/design/location-expansion.md](../design/location-expansion.md)

## Related Tickets

- [F-32: Scene inventory](../features/F-32-scene-inventory.md) — seed-declared location items as strings (builds on this foundation)
- [F-33: Location threads](../features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival (deferred; seed-declared details alone should make locations feel alive)
- [B-1: Location description overwritten by empty location_change delta](../bugs/B-1.md) — fixed, guard condition prevents empty deltas from overwriting seed data
