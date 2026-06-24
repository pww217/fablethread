---
title: "[NPC] NPC presence gaps"
status: done
urgency: 3
size: medium
created: 2026-06-14
labels:
  - Feature
  - Extraction
---

## Detail

Some NPCs still absent when they should be present. Needs scoping to determine root cause.

## How to Replicate

1. Have an NPC that should be present in a scene
2. Observe the NPC is absent from the scene panel
3. Check compendium for presence tracking

## Evidence

* Needs investigation to determine if this is an extraction issue, a sanitizer issue, or a UI rendering issue
* May be related to TICK-43 (NPC ghosting) but needs separate investigation
