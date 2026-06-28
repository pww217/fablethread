---
title: "Turn never starts after seed gen — no ruling/narrate calls, state reverts to T0"
status: done
urgency: 1
size: medium
created: 2026-06-26
ticket_id: B-21
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

**Root cause:** Frontend closed SSE connection on `turn_complete`, cancelling the `run_turn()` generator before async steps (sanitize + world) could run.

### The fix

**Frontend (game.js):**
- `turn_complete` handler no longer calls `es.close()` — SSE stays open
- `asyncRunning = true` set when record stream finishes (locks UI during async steps)
- `world_done` handler sets `asyncRunning = false`, closes SSE, focuses input
- Input disabled via `asyncRunning` flag while async steps run

**Backend (routes.py):**
- Removed background drain task — events flow normally to frontend since SSE stays open

**Backend (turn.py):**
- Lock released in `finally` block only — held during entire async window
- State/event saved after async window completes (world data included)
- Removed `released` flag and early lock release

**Backend (llm_client.py):**
- Added `try/finally: await stream.response.aclose()` in `chat_stream()` to ensure httpx connections are released

### Final event flow

1. Turn pipeline: ruling → narrate → extraction → `yield("complete")`
2. Frontend receives `turn_complete`, updates UI, sets `asyncRunning = true`
3. Backend continues: `yield("sanitize_start")` → sanitize → `yield("world_start")` → world → `yield("world_done")`
4. Frontend receives `world_done`, sets `asyncRunning = false`, closes SSE
5. Backend generator reaches StopAsyncIteration, `finally` releases `_inflight` lock

### The mystery (solved)

- ✅ World step wasn't hanging — it was being cancelled before it could run
- ✅ Other steps worked because they ran before `yield("complete")`
- ✅ `ev.py prompt-eval call` worked because no SSE connection to close
- ✅ Connection pool hypothesis was wrong — real issue was SSE lifecycle
- ✅ Final solution: keep SSE open after `turn_complete`, close on `world_done`
