---
title: "Thread ID mismatch — Storyteller emits creature_ambush_threat, sanitizer adds creature_ambush"
status: done
created: 2026-06-12
labels:
  - Bug
  - World Building
---

## Bug

Storyteller emits `thread_add` with id `creature_ambush_threat` at T10, but sanitizer adds `creature_ambush` (without `_threat`) at T10. The storyteller's thread_add never syncs to state — `creature_ambush_threat` never appears in any `state_snapshot.arc.threads`.

## Evidence

- `ev.py deltas` shows 27 turns with thread mutations in `changes.threads`
- Sanitizer at T10 adds `creature_ambush` to state, not `creature_ambush_threat`
- This is a storyteller→sanitizer ID sync failure
- Same bug appears in §8 (Sanitizer Lifecycle)

## Scope

* Fix sanitizer to use the ID from storyteller's thread_add
* Add validation that storyteller thread IDs match sanitizer output
* Add checkers to detect thread ID mismatches

## Files

* `ccya/engine/extraction.py` — storyteller extraction
* `ccya/engine/thread_sanitizer.py` — thread sanitization (line 217-223 area)
* `ccya/prompts/` — storyteller prompts
* `ccya/ev/checkers/` — thread lifecycle checker

## Validation

Confirmed in `docs/ev/cordyceps-findings.md §2a, §8` — storyteller emits `creature_ambush_threat`, sanitizer adds `creature_ambush`, creating orphan thread reference.
