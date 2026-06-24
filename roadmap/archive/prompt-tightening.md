---
title: "[Prompt] Prompt tightening"
status: canceled
urgency: 4
size: small
created: 2026-06-14
labels:
  - Improvement
  - Extraction
---

## Detail

Stop inferring TTL-removed conditions from narration. Currently the narrator may reference conditions that were silently removed by the engine, creating inconsistency.

## Motivation

If the engine removes conditions by TTL, the narrator should not reference them. Prompt guidance should clarify this boundary.

## Scope

* **In scope:** Update prompt guidance to clarify TTL removal boundary
* **Out of scope:** Engine changes, model changes

## Systems Affected

* — narrator prompts
