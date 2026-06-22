---
title: "Sanitizer dormant vs resolve"
status: done
created: 2026-06-14
labels:
  - Improvement
  - World Building
---

## Detail

Set threads dormant rather than resolving them. Currently threads are resolved when they expire, but dormant state may be more appropriate.

## Motivation

Dormant threads can be reactivated if the topic comes up again. Resolved threads are permanently closed, which may be too aggressive.

## Scope

* Evaluate dormant vs resolve semantics
* Update sanitizer to use dormant for expired threads
* Ensure UI handles dormant threads appropriately
