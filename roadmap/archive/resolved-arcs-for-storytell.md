---
title: "Resolved arcs for storytell"
status: canceled
created: 2026-06-11
labels:
  - Improvement
  - World Building
---

## Status

New — needs validation. May already be done.

## Detail

Narrate already receives resolved_arcs with TTL filtering (default 3 turns), showing resolution text AND goal_context via `_arc.j2`. Storytell does NOT receive this — only narrate gets them.

## Proposed Fix

* Add resolved_arcs to `_storytell_messages()` params in `extraction.py`
* Include in storytell prompt (reuses existing `_arc.j2` logic)
* ~5 tokens cost
* Helps storytell understand why arcs ended for better successor generation
