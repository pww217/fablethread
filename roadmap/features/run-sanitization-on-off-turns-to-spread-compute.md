---
title: "[Storytell] Run sanitization on off turns to spread compute"
status: idea
urgency: 3
size: small
created: 2026-06-12
labels:
  - Improvement
  - World Building
---

## Detail

Sanitization runs every turn, adding to LLM load. Running it on off turns (every other turn) would spread out the compute and reduce per-turn latency.

## Scope

* Add config option for sanitization frequency (e.g., `sanitize_every: 2` for every other turn)
* Default to current behavior (every turn) or change default to every other turn
* Consider: is per-turn sanitization actually necessary, or is it overkill?
* Coordinate with TICK-8 (sanitizer lifecycle fix)

## Files

* `ccya/engine/thread_sanitizer.py` — sanitization trigger logic
* `ccya/engine/config.py` — EngineConfig (add sanitize_frequency field)
* `ccya/engine/turn.py` — sanitization call site

## Related

* TICK-8: [ev] Fix sanitizer_lifecycle — per-turn runner hides sanitizer events
