---
title: "[NPC] Party designation"
status: done
completed: 2026-06-24
urgency: 4
size: medium
created: 2026-06-14
ticket_id: F-16
labels:
  - Improvement
  - Extraction
---

## Detail

Boolean on NPC model for auto-tracking across location changes. Party members should stay with the player across location changes without manual tracking.

## Motivation

Currently party members need manual tracking across location changes. A party designation would automate this and reduce errors.

## Scope

* **In scope:** Add party designation to NPC model, update location change logic
* **Out of scope:** UI changes, prompt changes

## Systems Affected

* — NPC model
* — location change handling
* — location change delta
