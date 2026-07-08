---
title: "Evals produce wrong turn count and missing narrative in events"
status: done
urgency: 1
size: medium
created: 2026-07-03
ticket_id: B-28
labels:
  - engine
  - eval
---

## Symptom

Running `ev.py play --llm --turns 5` produces **13 turn entries** (turns 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26) instead of 5 player turns. The last turns show `selected_beat: null — no fit` and empty pacing deltas.

## Evidence

### Turn count is wrong
- `--turns 5` should produce 5 player turns (turns 2, 4, 6, 8, 10)
- Actual: 13 entries spanning turns 2 through 26
- Turn numbers increment by 2 (even only) — convention is odd=seed, even=player, so this part is correct
- But the **count** is wrong: 13 turns instead of 5

### No top-level narrative in events
Every event in `events.jsonl` has:
- `last_turn_state` with actions (player choice)
- `narrate_prompt.output` with 1100-1700 chars of prose (LLM IS generating narrative)
- **No top-level `narrative` field**

Old convention had narrative at the event root level. This is broken.

### Duplicate entries per turn
Turns 10, 20 each have **two entries**: a `sanitizer` event and a regular event. This is expected for sanitizer runs, but the regular events on those turns have empty pacing deltas and `selected_beat: null — no fit`.

### Last turns are degenerate
Turns 24 and 26 (last two) show:
- `selected_beat: null — no fit`
- No world beat candidates generated
- No pacing deltas
- No state changes
- No ruling metrics (tokens_in=0, tokens_out=0)

This looks like the turn pipeline is running but **not reaching the ruling/narrate LLM calls**, or the state is broken by that point.

## What's broken

The turn number counter is incrementing by 2 per player turn instead of 1. This means:
- `state.set_turn(state.meta.turn + 1)` in `_persist_and_async_cleanup` is being called twice per player decision
- Or the turn number is being incremented somewhere else in addition to the main path

### Suspected cause: recent commits

This is NOT how it always worked. The regression was introduced between the last working eval and now. Likely candidates:

1. **`2aa46cc` I-23/I-24: Engine core tech debt consolidation** — moved `_start_turn`/`_signal_turn_done` to lazy import inside `run_turn()`
2. **`6ccc8b6` I-19: Extract phased subroutines from monolithic run_turn** — restructured turn pipeline into subroutines
3. **`b8363ba` I-17: WorldState model migration** — immutable state mutations via typed methods

The turn number doubling suggests `state.set_turn()` is being called twice:
- Once in the main pipeline path
- Once somewhere in async cleanup or error handling

### Turn number tracking

`state.meta.turn` starts at 0 after seed. Each player turn should increment by 1:
- Turn 1 = seed (prepare_seed + narrate_seed)
- Turn 2 = player 1 decision
- Turn 3 = player 2 decision
- etc.

But we're seeing turns 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26 — incrementing by 2 each time. This means **each player decision is triggering TWO turn increments**.

## Investigation steps

1. **Trace turn number increments**: Add logging to `state.set_turn()` calls to find where the double-increment happens
2. **Check `_persist_and_async_cleanup`**: This is where `state.set_turn(state.meta.turn + 1)` happens (turn.py:585). Is it being called twice?
3. **Check error/retry paths**: Is there a retry path that re-yields and re-increments?
4. **Check the generator completion**: `run_turn()` is an async generator. Is the generator being consumed twice somewhere?
5. **Verify `_ensure_seed_generated`**: This runs seed at session start. Does it leave state at turn 1 or turn 0?
6. **Compare with old working saves**: Check `saves/noir--1930s-2026-06-30/events.jsonl` — it also has even-only turns (2, 4, 6, 8, 10, 12, 14, 16, 18, 20) and no top-level narrative. This means the even-only convention and missing narrative field may be **older behavior**, and the real bug is the **turn count** (13 turns for --turns 5).

## Files to check

- `ccya/engine/turn.py` — `run_turn()` generator, `_persist_and_async_cleanup` (turn 585)
- `ccya/engine/turn_state.py` — turn state tracking
- `ccya/models/state.py` — `WorldState.set_turn()`
- `ccya/ev/play.py` — `_llm_session()` loop, how it consumes `run_turn()`
- `ccya/server/routes.py` — how server consumes `run_turn()`
- `ccya/server/tv.py` — turn viewer (reads narrative from `narrate_prompt.output`, not top-level)

## Root cause

### Bug 1: Double `state.set_turn()` — turn number increments by 2 per turn

`turn.py` had **two** `state.set_turn(state.meta.turn + 1)` calls:
- Line 218: inside `run_turn()`, after `_apply_phase`
- Line 585: at start of `_persist_and_async_cleanup()`

Both had the comment `# Turn increment (single source of truth: here)` — copy-paste duplication.

Execution flow:
1. `run_turn()` line 218: `state = state.set_turn(state.meta.turn + 1)` — turn N → N+1
2. `run_turn()` line 226: calls `_persist_and_async_cleanup()` with state where turn = N+1
3. `_persist_and_async_cleanup()` line 585: `state = state.set_turn(state.meta.turn + 1)` — turn N+1 → N+2
4. Event written: `"turn": state.meta.turn` — this is N+2

Result: Event turn numbers are 2, 4, 6, 8... instead of 1, 2, 3...

### Bug 2: `prompt_context.py` convention mismatch — always empty narrations

`ev/prompt_context.py` reads `narrate.output` but convention is `narrate.prose` (set in `turn.py:644`). This means:
- Line 111: `narration = (turn_ev.get("narrate") or {}).get("output", "")` → **always empty string**
- Line 160: `narr = (ev.get("narrate") or {}).get("output", "")` → **always empty string**

Impact: Storytell prompt gets no memory of prior turns. World/Scene/State prompts get no narrative context. This was broken when convention changed from `narrate.output` to `narrate.prose` but `prompt_context.py` was never updated.

## Fix

### Bug 1: Double `state.set_turn()` — NOT YET FIXED

The fix was documented but never applied. Line 218 in `run_turn()` still has the duplicate `state.set_turn()` call.

**Fix applied:** Removed the `state.set_turn()` call at `ccya/engine/turn.py:218`. Single source of truth is `_persist_and_async_cleanup()` at line 585.

### Bug 2: `prompt_context.py` convention mismatch

`ccya/ev/prompt_context.py:111` — changed `.get("output", "")` to `.get("prose", "")`
`ccya/ev/prompt_context.py:160` — changed `.get("output", "")` to `.get("prose", "")`

`make check` passes (ruff + mypy + YAML validation + vulture).
