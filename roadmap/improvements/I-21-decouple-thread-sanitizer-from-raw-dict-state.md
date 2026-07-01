---
title: "Decouple thread sanitizer from raw dict state"
status: open
type: improvement
urgency: 3
size: medium
created: 2026-06-29
ticket_id: I-21
labels: [engine, refactoring]
---

# I-21: Decouple thread sanitizer from raw dict state

## Summary

`thread_sanitizer.py` is 505 lines, tightly coupled to raw dict state. It re-implements `_find_json` from config.py and accesses state via `state.get("meta")`, `state.get("arc")`, `state.get("world_state_candidates")`, `state.get("scene", {}).get("world_state")`. Pass structured `LongTermObjective` and `ArcThread` models instead.

## Current state

- `thread_sanitizer.py` takes `state: dict[str, Any]`
- 505 lines of logic operating on untyped dicts
- Re-implements `_find_json` from config.py (duplication)
- Hard to test in isolation (needs full dict state fixture)

## Impact

Tightly coupled to dict structure, hard to test in isolation, fragile to state schema changes.

## Proposed changes

1. Replace `state: dict[str, Any]` parameter with structured `Arc` model containing `threads: list[ArcThread]`, `long_term_objective: LongTermObjective`
2. Remove `_find_json` re-implementation, import from config.py (or move to shared utils)
3. Add unit tests for sanitizer logic independent of full state dict

## Cross-ticket links

- I-17 #3 (`dict[str, Any]` state) — root cause. Once `WorldState` model exists, thread sanitizer can use it.
- I-17 #1 (duplicated utilities) — `_find_json` duplication overlaps with this ticket's scope.
- I-17 #10 — this is the dedicated ticket for I-17 #10. I-17 #10 is the audit finding; I-21 is the execution.
