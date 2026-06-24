---
title: "[State] Choices show IDs/present tense"
status: done
urgency: 4
size: small
created: 2026-06-14
labels:
  - Bug
  - Extraction
---

## Detail

Choice options render inventory IDs and reference past items in present tense. This breaks immersion and confuses the player.

## How to Replicate

1. Have an inventory item in the game
2. Take an action that generates choices
3. Observe choice options show raw IDs instead of human-readable names

## Evidence

* Choice rendering templates need to use human-readable names, not internal IDs
* Present tense references to past items need to be corrected
