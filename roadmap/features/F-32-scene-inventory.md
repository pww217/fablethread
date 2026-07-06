---
title: "Scene inventory — seed-declared location items as strings"
status: idea
urgency: 4
size: large
created: 2026-07-06
ticket_id: F-32
design: docs/design/scene-inventory.md
labels:
  - engine
  - seed
  - narration
  - extraction
---

## Problem

Inventory in CCYA is strictly PC-owned. `state.inventory` contains items the PC carries. When the narrator writes "You see a rusted key on the table" or "The weapon lies abandoned on the floor," that item exists narratively but has no state representation. This creates several issues:

1. **Narrator inconsistency:** The narrator may describe items that ruling didn't know about, creating dissonance if the player tries to interact with them.
2. **No ruling awareness:** Ruling's impossibility check only sees PC inventory. If the narrator describes a weapon on the wall and the player tries to pick it up, ruling has no context that the weapon exists.
3. **No state fidelity:** Items that exist in the world but not on the PC's person are ephemeral — they exist only in prose, not in state.
4. **Seed waste:** Seed generates rich location descriptions but no structured data about what's actually at each location.

The canceled B-12 ticket proposed `nearby_interactable_items` as a scene extraction concept but was never implemented. This ticket revisits the idea with a seed-declared string approach instead of runtime extraction.

## Goals

1. **Seed-declared location items:** Each key location's seed data includes a list of items present at that location as seed-declared strings (not a model). These are seed-declared, not LLM-extracted at runtime. Each string is a short phrase like "rusted key on desk" or "abandoned rifle leaning against wall" (~20-30 chars).

2. **Narrator exposition:** When the player arrives at a location for the first time, the narrator should describe the location's items as environmental details. This is the primary use case — exposition, not gameplay mechanics.

3. **Ruling awareness:** One ruling prompt instruction: if player's action involves interacting with a location item (pick up, examine, use), ruling should NOT mark it as impossible just because the item isn't in PC inventory. This is the same ruling awareness as F-31's location details — location items are a subset of location details.

4. **PC pickup via existing extraction:** When the player picks up a location item, step2b should extract it as a PC inventory change via existing `inventory_add` mechanism. The extraction prompt needs guidance: "If the narration describes the PC taking an item that was present at this location (seed-declared), treat it as inventory_add." No new extraction fields needed.

## Design

Full design doc: [docs/design/scene-inventory.md](../design/scene-inventory.md)

## Related Tickets

- [F-31: Location expansion](../features/F-31-location-expansion.md) — seed-declared location details as strings, first-visit flag, narrator exposition (prerequisite — F-32's seed-declared items ARE F-31's seed-declared details; no separate model needed)
- [F-33: Location threads](../features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival (independent, both build on location expansion foundation)
- [B-12: Scene interactive inventory items](../bugs/B-12-scene-interactive-inventory-items.md) — canceled, proposed nearby_interactable_items as scene extraction concept (this ticket revisits with seed-declared string approach instead)
