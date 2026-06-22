---
title: "[NPC] Compendium last action recent notes field"
status: canceled
created: 2026-06-11
labels:
  - Feature
  - Extraction
---

## Status

Needs scoping. Feature.

## Detail

Current `notes` field on NPC compendium entries is scene-specific attitude (cleared on departure). No mechanism to capture "the last thing this NPC was doing" when they leave a scene.

## Scope

* Inventing a new one-time field for "last action / last known activity" when NPC exits scene
* Very nebulous right now — needs design work
* Should be distinct from `notes` (scene attitude) and `departed_summary` (departure reason)
* UI compendium should show this alongside last_seen
