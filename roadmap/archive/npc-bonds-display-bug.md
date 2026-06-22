---
title: "[NPC] NPC bonds display bug"
status: done
created: 2026-06-14
labels:
  - Improvement
  - Extraction
---

## Detail

UI shows bond ID instead of description. Currently NPC bonds are displayed as raw IDs rather than human-readable descriptions.

## How to Replicate

1. Have an NPC with a bond in the compendium
2. View the NPC in the UI
3. Observe bond field shows ID instead of description

## Evidence

* Bond rendering templates need to use description, not ID
* Bond model needs to expose description field to templates
