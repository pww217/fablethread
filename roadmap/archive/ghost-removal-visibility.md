---
title: "[Conditions] Ghost removal visibility"
status: canceled
created: 2026-06-14
labels:
  - Feature
  - Extraction
---

## Detail

When engine removes conditions by TTL, surface this in UI (delta or log). Currently conditions disappear silently without any indication to the player.

## Motivation

Players need to know why conditions disappeared. Silent removal creates confusion and breaks the sense of cause and effect.

## Scope

* **In scope:** Add UI indication when conditions are removed by TTL
* **Out of scope:** Engine changes, prompt changes

## Systems Affected

* — condition rendering templates
* — condition delta building
