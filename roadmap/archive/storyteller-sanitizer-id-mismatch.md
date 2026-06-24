---
title: "Storyteller→sanitizer ID mismatch"
status: canceled
urgency: 2
size: small
created: 2026-06-14
labels:
  - Bug
  - World Building
---

## Detail

Storyteller thread_add creates threads with IDs that don't match sanitizer's thread IDs. Same root cause as pacing gate (TICK-50) — gate blocks storyteller, sanitizer adds different ID.

## Status

Canceled — root cause was identified and addressed in TICK-50 fix.
