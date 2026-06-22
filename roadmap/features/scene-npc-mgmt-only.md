---
title: "Scene = NPC mgmt only"
status: idea
urgency: 4
size: unknown
created: 2026-06-14
labels:
  - Feature
  - World Building
---

## Detail

Move location to state extractor to spread load. Currently scene handles both NPC management and location, which concentrates too much responsibility.

## Motivation

Separating concerns: scene handles NPC management, state handles location. This spreads extraction load and clarifies responsibilities.

## Scope

* Move location extraction to state extractor
* Refactor scene extraction to focus on NPC management
* Update prompts accordingly
