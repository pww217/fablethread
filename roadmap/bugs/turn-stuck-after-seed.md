---
title: "Turn never starts after seed gen — no ruling/narrate calls, state reverts to T0"
status: new
urgency: 1
size: medium
created: 2026-06-26
labels:
  - turn-pipeline
  - engine
  - async-steps-recording
  - debugging
---

## Problem

After generating a new game from seed (dynamic or static), the first turn never completes. The server logs show seed generation succeeds, but no ruling/narrate/extraction calls are made. The frontend polls `_turn_viewer_data` showing `events=1` (just the seed event) and `turns=1` in recent history, but the turn never progresses. The game reverts to turn 0.

## Root cause

**World step LLM call hangs indefinitely.** The `llm_chat` call at `world.py:82` has no `max_tokens` limit and uses 1200s timeout. The MLX server hangs on the world step request (small prompt ~1300 tokens), never returning a response. This blocks the save at `turn.py:592`, so state is never persisted.

The debug logs show:
```
chat: request sent, waiting for response...
→ [no response received — hangs for 20+ minutes]
```

The frontend shows the extraction result (from `yield ("complete", result_obj)` at line 518), but the async window (sanitize + world) never completes, so:
- `world_done` event never fires → input box stays blocked
- `save_state` never executes → state reverts on refresh

## Fix

1. **Save event/state BEFORE async window** — State is persisted immediately after `yield ("complete")`, before sanitize/world run. If world hangs, state is still saved.

2. **Add `max_tokens=500` and `timeout=60.0` to world step** — Prevents indefinite hang. If the model generates a long response or the MLX server is slow, the call fails after 60s instead of 20 minutes.

3. **Add `asyncio.sleep(0.1)` before world step** — Gives MLX server time to clean up after extraction pipeline. The world step fires 22ms after record completes, which may be too fast.

## Implementation

### Logging added (turn.py)

**INFO level (turn completions):**
- `turn.ruling_complete` — after ruling phase (trace_id, turn, intent, outcome)
- `turn.narrate_complete` — after narrate (trace_id, turn, narr_ms, narr_tokens_in, narr_tokens_out)
- `turn.extraction_complete` — after extraction (trace_id, turn, ext_ms, ext_tokens_in, ext_tokens_out)
- `turn.complete` — after final save (trace_id, turn)

**DEBUG level (transitions):**
- `turn.pre_complete` — before yield("complete") (state_turn)
- `turn.async_save_start` — before save in async window
- `turn.async_save_complete` — after save in async window
- `turn.async_window_start` — after yield("complete")
- `turn.sanitize_complete` — after sanitize (sanitize_ran)
- `turn.sanitize_skipped` — when sanitize_every=0
- `turn.sanitize_failed` — if sanitize raises
- `turn.world_start` — before world step (candidate_npcs count)
- `turn.world_complete` — after world (beats count, world_ms)
- `turn.world_failed` — if world raises

### Logging added (world.py)

- `world.step_start` — before LLM call (candidate_npcs count)
- `world.step_failed` — if LLM call raises
- `world.step_no_json` — if no valid JSON in response
- `world.step_complete` — after parsing (valid_beats count)

### Logging added (llm_client.py)

- `chat: sending request` — before HTTP call (host, model, timeout)
- `chat: request sent, waiting for response...` — after HTTP call sent
- `chat: response received, extracting content...` — after response received

### Code changes (turn.py)

- Moved `append_event` + `save_state` to BEFORE async window (after `yield ("complete")`)
- Added second `save_state` after world step to persist beat_candidates
- Added `asyncio.sleep(0.1)` before world step

### Code changes (world.py)

- Added `max_tokens=500` to `llm_chat` call (prevents indefinite generation)
- Changed `timeout` from `config.request_timeout_s` (1200s) to `60.0` (fails fast)
- Added `asyncio.sleep(0.1)` before `llm_chat` call (gives MLX server time to clean up)
- Added token usage capture from LLM response (tokens_in, tokens_out)
- Updated return type to 5-tuple: `(beat_candidates, system_text, user_text, raw_response, usage)`

### Code changes (turn.py)

- Moved `append_event` + `save_state` to BEFORE async window (after `yield ("complete")`)
- Added second `save_state` after world step to persist beat_candidates
- Updated world step call to handle 5-tuple return value
- Updated `extraction_event["world"]` to use actual token usage from world step

### Code changes (_turn_viewer.html)

- Fixed `storytell` → `record` in stages array (line 415)

### Comments added (turn.py)

1. `turn_no` pre-increment explanation (line 122-124)
2. `yield("complete")` before save explanation (line 519-523)
3. Async window lock holding explanation (line 522-523)
4. World step timing explanation (line 547-548)
5. CRITICAL: Save event/state FIRST comment (line 520-523)

## Investigation steps

1. Check if frontend is sending input after seed gen (browser console, network tab)
2. Add the logging above and reproduce ✅ (logging added)
3. Check if world step is timing out or failing silently ✅ (confirmed hang)
4. Verify record stream isn't failing (check extraction_event["record"]) ✅ (record succeeds)

## Files changed

- `ccya/engine/turn.py` — Added INFO-level completion logging + DEBUG logging at key points + explanatory comments + moved save before async window + updated world step call to handle 5-tuple return
- `ccya/engine/world.py` — Added logging for world step start/complete/failure + added max_tokens=500 + timeout=60.0 + asyncio.sleep(0.1) + added token usage capture + updated return type to 5-tuple
- `ccya/engine/extraction/pipeline.py` — Added comment explaining record stream failure handling
- `ccya/llm_client.py` — Added debug logging for request/response timing
- `ccya/templates/_turn_viewer.html` — Fixed `storytell` → `record` in stages array

## Related

- `roadmap/features/async-steps-recording.md` — Design doc for async step recording
- `roadmap/bugs/beat-candidates-disconnect.md` — Beat generation split (same PR)
- `roadmap/bugs/orphaned-sanitizer-events.md` — Sanitizer event cleanup

## Resolution

**Root cause identified:** SSE generator lifecycle issue, not connection pool exhaustion.

### The actual problem

The frontend closes the SSE connection immediately upon receiving `turn_complete` event (line 972 in game.js). This cancels the `run_turn()` generator before it can complete the async window (sanitize + world steps) and reach the `finally` block that releases the `_inflight` lock.

**Sequence of events:**
1. Turn pipeline runs: ruling → narrate → extraction → `yield ("complete")`
2. Routes.py yields `turn_complete` event to frontend
3. Frontend receives `turn_complete`, calls `es.close()` to close SSE connection
4. SSE connection closure cancels the `run_turn()` generator mid-execution
5. Generator never reaches async window (sanitize + world) or the `finally` block
6. `_inflight` lock is never released → UI stays locked

**Why world step appeared to hang:** It wasn't hanging — it was being cancelled before it could run. The logs showed "world LLM call cancelled" immediately after "world.step_before_llm", confirming the generator was cancelled.

### What's been fixed

**1. Background task to drain generator (routes.py)**
After yielding `turn_complete`, spawn a background task to continue consuming the generator:
```python
async def _drain():
    async for _ in run_turn_generator:
        pass
asyncio.create_task(_drain())
```
This allows the async window to complete even though the frontend closed the SSE connection.

**2. Explicit stream close in chat_stream() (llm_client.py)**
Added `try/finally: await stream.response.aclose()` to ensure httpx connections are released even if the consumer breaks out early.

**3. Moved state/event save to after async window (turn.py)**
Following existing pattern: extraction data goes in the main event, saved once after all extraction (including world) completes. Removed the "save early" workaround that was added when world appeared to hang.

### Current state

- ✅ World step completes successfully (4.7s, 3 beats)
- ✅ World data appears in events.jsonl
- ✅ Turn viewer shows world step
- ❌ UI lock remains after turn completes — `_inflight` lock not releasing
- ❌ User must manually refresh browser to unlock UI

### Remaining issue: lock release

The `_inflight` lock is released in the `finally` block of `run_turn()`:
```python
finally:
    await _inflight.release(str(save_dir))
```

When the background task drains the generator, the `finally` block should execute. But it's not releasing the lock. Possible causes:
- Background task completes but doesn't trigger generator cleanup properly
- `generator.aclose()` not being called explicitly
- Asyncio task lifecycle not ensuring finally blocks run
- Lock release is async but background task exits before it completes

**Next steps:**
1. Investigate why `finally` block isn't releasing the lock when generator is drained by background task
2. Consider explicit `await generator.aclose()` in the background task
3. Add logging to confirm when lock is acquired/released
4. Test if the lock releases after a delay (race condition?)

### The mystery (solved)

- ✅ Why the world step specifically hangs in this context — frontend closes SSE on turn_complete, cancelling generator before async window
- ✅ Why other steps (ruling, narrate, extraction) work fine — they run before yield("complete")
- ✅ Why `ev.py prompt-eval call` works — no SSE connection, no premature cancellation
- ✅ Whether the singleton client is causing issues — no, connection pool hypothesis was wrong
- ✅ The real issue: SSE generator lifecycle + frontend closing connection too early
