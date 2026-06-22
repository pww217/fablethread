---
title: "[Scene] Interactive inventory items"
status: idea
urgency: 4
size: medium
created: 2026-06-14
labels:
  - Bug
  - Extraction
---

## Detail

Nearby interactable items should be a separate concept from inventory items. Currently all items are treated the same, but nearby items that can be interacted with are different from owned items.

## Motivation

Separating nearby interactable items from inventory items allows the narrator to reference them appropriately and gives the player more meaningful choices about what to interact with.

## Scope

* **In scope:** Add nearby_interactable_items concept to scene extraction, update narrator prompts
* **Out of scope:** Inventory model changes, UI changes

## Systems Affected

* — scene extraction
* — scene and narrator prompts
