---
title: "Scene scoping causes thread/arcs duplication"
status: canceled
created: 2026-06-12
labels:
  - Bug
  - World Building
---

## Detail

Scene scoping causes duplicate threads and arcs, likely a sanitizer issue. Related to TICK-8 (sanitizer lifecycle).

## Scope

* Investigate thread duplication in scene-scoped threads
* Check if sanitizer is creating duplicate threads instead of updating existing ones
* Review scene-scoped thread lifecycle (active→latent→removed at 5/10 silent turns)
* Coordinate with TICK-8 (sanitizer lifecycle fix)

## Files

* `ccya/engine/thread_sanitizer.py` — thread sanitization logic
* `ccya/state/delta_builder.py` — scene-scoped thread purging on location change
* `ccya/engine/turn.py` — scene age computation, scene pressure directives

## Related

* TICK-8: [ev] Fix sanitizer_lifecycle — per-turn runner hides sanitizer events
* TICK-11: Proactive NPC agency + GM beats redesign
