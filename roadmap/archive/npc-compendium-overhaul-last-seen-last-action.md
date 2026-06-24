---
title: "[NPC] NPC compendium overhaul — last_seen, last action, alias priority"
status: done
urgency: 3
size: large
created: 2026-06-12
labels:
  - Feature
  - Extraction
---

## Status

Scoping — Feature. Consolidated from TICK-16, TICK-17, TICK-18 (canceled), TICK-31 (absorbed).

## Detail

NPC compendium UI and data model need overhaul for better temporal context, identity, activity tracking, and bio detail.

## Scope

### 1. Turn number in last_seen (TICK-16)

Compendium UI shows "Last seen: {location_name}" but no temporal context. When an NPC goes absent and returns, the narrator cannot distinguish "just here" from "absent 5 turns ago."

* Add turn number to last_seen in UI compendium sidebar
* Compute "X turns ago" server-side in template context, do NOT store as new field
* Prompt templates do NOT need turn delta — only UI display
* Keep prompt last_seen as-is (location name only)

### 2. Last action/known activity field (TICK-17)

Current `notes` field on NPC compendium entries is scene-specific attitude (cleared on departure). No mechanism to capture "the last thing this NPC was doing" when they leave a scene.

* Add one-time field for "last action / last known activity" when NPC exits scene
* Should be distinct from `notes` (scene attitude) and `departed_summary` (departure reason)
* UI compendium should show this alongside last_seen

### 3. Alias priority and naming strategy (TICK-18)

Current naming/priority: UI shows `name or node_id`. When no name exists but aliases exist, shows "Previously known as: X" only in tooltip. Fallback to machine-readable node ID is not UI-friendly.

* Scene extractor: use alias field for unnamed characters instead of placeholder names. If character later gets a proper name, append to same entry (dedup).
* UI display priority: proper name → first alias → error (NOT node ID)
* IDEAS.md alias resolution is related but this is broader — covers display priority and naming strategy

### 4. NPC bio length + physical description (TICK-31, absorbed)

NPC bios in compendium are too short. Need longer bios with physical description and more detail.

* Increase bio length in compendium tooltips and compendium view
* Add physical_description field to NPC compendium entries (ccya/models.py)
* Seed physical descriptions at game initialization (ccya/state/io.py — _assign_seed_personalities())
* Update compendium rendering templates to display expanded bio (ccya/templates/_state_left.html)
* Update any prompt templates that reference NPC bios
