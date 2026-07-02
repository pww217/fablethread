---
title: "Extract phased subroutines from monolithic run_turn"
status: done
type: improvement
urgency: 2
size: large
created: 2026-06-29
ticket_id: I-19
labels: [engine, refactoring]
plan: plans/completed/I-19-extract-phased-subroutines.md
pr:
  url: https://github.com/pww217/ccya/pull/10
  branch: i19-extract-phased-subroutines
---

# I-19: Extract phased subroutines from run_turn

## Summary

`turn.py`'s `run_turn` is 586 lines handling the full turn lifecycle. Extract phased subroutines to improve readability, testability, and modifiability.

## Current state

`turn.py:60-646` — 586 lines of orchestration. Handles:
- Setup
- Ruling
- Narration
- Extraction
- Delta application
- Persistence
- Async cleanup
- Lock release

Some phases are partially extracted already (`_ruling_phase`, `_narrate_setup`, `_apply_state_updates`, `_run_world_step`).

## Impact

Hard to read, hard to test, hard to modify without breaking other phases.

## Proposed structure

Extract into:
- `_ruling_phase(ctx)` — ruling + narration setup
- `_narrate_phase(ctx)` — prose narration
- `_extract_phase(ctx)` — scene, state, record extraction
- `_apply_phase(ctx)` — delta application + state mutation
- `_async_cleanup_phase(ctx)` — world step + persistence + lock release

Each subroutine takes `TurnContext`, returns updated context or results. Clear phase boundaries.

## Cross-ticket links

- I-17 #4 (`dict[str, Any]` state) makes this harder — phase boundaries are unclear because state is untyped. I-17 #4 will clarify what each phase actually needs.
- I-17 #12 (event logging scattered) overlaps — `_persist_turn` extraction could be part of `_async_cleanup_phase`.
