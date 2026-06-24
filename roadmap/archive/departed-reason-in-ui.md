---
title: "[NPC] Departed reason in UI"
status: done
urgency: 4
size: small
created: 2026-06-14
labels:
  - Improvement
  - Extraction
---

## Detail

1-2 sentence summary when NPC departs (died, sailed away, etc.). Currently no departure reason is shown in the UI.

## Motivation

Players need to know why NPCs left. Without a departure reason, departures feel arbitrary and confusing.

## Scope

* **In scope:** Add departure reason to NPC model, update UI to show it
* **Out of scope:** Engine changes, prompt changes

## Systems Affected

* — NPC model
* — NPC rendering templates
* — NPC departure extraction
