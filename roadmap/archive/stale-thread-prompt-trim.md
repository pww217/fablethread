---
title: "Stale thread prompt trim"
status: done
created: 2026-06-14
labels:
  - Improvement
  - World Building
---

## Detail

Engine may handle this now; validate and trim prompts. Currently stale threads may be included in prompts unnecessarily.

## Motivation

Trimming stale threads reduces token usage and improves prompt clarity.

## Scope

* Validate current engine behavior for stale thread handling
* Update prompts to trim stale threads if appropriate
* Test impact on token usage and quality
