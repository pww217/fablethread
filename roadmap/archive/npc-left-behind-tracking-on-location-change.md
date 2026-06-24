---
title: "NPC left-behind tracking on location change"
status: canceled
urgency: 4
size: medium
created: 2026-06-11
labels:
  - Feature
  - Extraction
---

## Status

Partially fixed - grounded-state-extraction added position field to CompendiumNpcUpdate for spatial positioning. Dedicated left behind state tracking still deferred.

## Detail

When player changes locations, characters who should logically stay behind aren't tracked. Example: companion stays at home while PC goes across town - they shouldn't appear in the new scene.

## Fix

* Explicit state for left behind NPCs with last known location
* Narrator can reference left-behind NPCs appropriately
* Party members exempt from left-behind logic unless explicitly separated by narrative events
