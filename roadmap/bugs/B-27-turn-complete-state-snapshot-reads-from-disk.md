---
title: "turn_complete state snapshot reads from disk — panels show stale data after turn"
status: done
urgency: 2
size: small
created: 2026-06-29
ticket_id: B-27
labels:
  - turn-pipeline
  - sse
  - frontend
  - state
---

## Problem

When a turn completes, the frontend receives `turn_complete` with a `state` snapshot that is **one turn behind**. Panels that were showing live updates via `panel_update` events during extraction (NPCs, inventory, conditions) revert to their pre-turn values.

The frontend then HTMX-refreshes `/panels/state-left` and `/panels/state-right` to get the real data, but this is a workaround for a backend bug.

## Root cause

**`turn_complete` state snapshot reads from disk instead of using in-memory state.**

`routes.py:330` calls `_load_current_state()` → `load_state(save_dir)` which reads `state.yaml` from disk. But `save_state(save_dir, state)` doesn't happen until `turn.py:599`, which is **after** `yield("complete")` at line 519.

The sequence:
1. `yield("complete", result_obj)` fires at turn.py:519
2. `routes.py:330` calls `_load_current_state()` → reads disk → gets **previous turn's state**
3. Frontend receives `turn_complete` with stale state
4. `save_state(save_dir, state)` executes at turn.py:599 (after async window)
5. Frontend HTMX-refreshes panels to get real data from disk

**`panel_update` events use preview copies** (pipeline.py:109/170/277) — `copy.deepcopy(state)` + `apply_delta()` on the copy. These are intentional (live preview without committing), but the frontend sees preview data then gets stale state on `turn_complete`, creating a jarring revert.

**World step mutates state after `yield("complete")`** (turn.py:575 sets `beat_candidates`) but `world_done` at line 622 only includes `metrics`, no state. Frontend can't see beat candidates.

## Fix

**Pass the in-memory state snapshot from `run_turn` into `TurnResult`** instead of having routes.py do a separate disk read.

### Option A (minimal diff): Add `state_snapshot` to `TurnResult`

1. Add `state_snapshot: dict[str, Any]` field to `TurnResult` (models/config.py)
2. In `turn.py:519`, build `TurnResult` with `state_snapshot=state` (the already-mutated dict after `_apply_state_updates` at line 343)
3. In `routes.py:330`, use `result.state_snapshot` instead of `_load_current_state()`

### Option B (cleaner): Remove `_load_current_state` from turn_complete

1. Add `state_snapshot` to `TurnResult`
2. Use it in routes.py
3. Remove `_load_current_state()` call from the turn_complete SSE payload
4. Keep `_load_current_state()` for panel endpoints (HTMX refreshes still need disk reads)

## Implementation notes

- `state` at line 343 already includes all extraction + apply changes. No additional mutation needed.
- World step mutations (beat_candidates at line 575) happen after `yield("complete")` — these won't be in the snapshot. This is acceptable; beat_candidates are generated for the NEXT turn.
- `panel_update` events remain as-is (preview copies are intentional for progressive UI updates).
- Frontend should no longer need to HTMX-refresh panels after `turn_complete` — the state snapshot will already be correct.

## Files to touch

- `ccya/models/config.py` — add `state_snapshot` field to `TurnResult`
- `ccya/engine/turn.py` — pass `state_snapshot=state` in `TurnResult` at line 500
- `ccya/server/routes.py` — use `result.state_snapshot` instead of `_load_current_state()` at line 330

## Related

- `roadmap/bugs/B-21-turn-never-starts-after-seed-gen-no-rulingnarrate-calls-s....md` — async window / SSE lifecycle (same turn.py changes)
- `roadmap/bugs/B-22-scene-extractor-omits-presence-field-new-npc-entries.md` — panel data accuracy
