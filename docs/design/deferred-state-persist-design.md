---
title: Deferred state persistence — single atomic write at turn end
status: reviewed
design: docs/design/deferred-state-persist-design.md
created: 2026-06-24
---

# Deferred State Persist Design

## Purpose

This document is the design authority for moving all turn pipeline state writes to a single atomic point at turn end, enabling clean cancel/retry and progressive UI updates from in-memory state.

## Problem Statement

The turn pipeline (`run_turn()` in `ccya/engine/turn.py`) writes state to disk 3+ times per turn:

| Write | Location | What |
|---|---|---|
| 1 | Line 437 | `save_state(save_dir, state)` — full state after all extractions applied |
| 2 | Line 492 | `save_state(save_dir, state)` — after `prior_history` bullet appended |
| 3 | Line 505 | `save_state(save_dir, state)` — after thread sanitizer |

`state_snapshot` is captured at line 438 (after write 1), so it excludes prior_history (write 2) and sanitizer (write 3) changes. The cancel endpoint (`POST /turn/cancel`, `routes.py:400`) and delete endpoint (`POST /turn/delete`, `routes.py:428`) restore from this stale snapshot, producing incorrect state after revert.

Additional orphaned artifacts:
- `chroncle.md` entry written at line 478 (between writes 1 and 2)
- `prompts.jsonl` entries written at line 476 (between writes 1 and 2)
- Sanitizer events appended at line 505 (after write 3) — orphaned on cancel

The UI receives turn data only at `yield ("complete", ...)` (line 530), meaning NPC compendium, state, and arc changes all appear at once rather than progressively as each extraction phase completes.

## Target State

1. **Single atomic write block** at the end of the turn pipeline. State, events, chronicle, prompts, prior_history, and sanitizer results are all written in one sequence after all phases complete. If a crash occurs before or during this block, the on-disk state reflects the end of the last completed turn — no partial-turn corruption.

2. **Progressive SSE updates** from in-memory state. After each extraction phase (scene → state → storytell), a `panel_update` SSE event carries the computed panel data. The frontend updates the matching panel immediately. Narrative tokens continue to stream as today.

3. **Cancel = memory discard.** No file cleanup needed. The UI receives a `panel_update` resetting all panels to the pre-turn state (read from the previous turn's written state).

4. **Retry = delete + rerun.** `POST /turn/delete` removes the last turn's event/chronicle/prompts and invalidates it from the in-memory state view. The next turn start sees the clean pre-turn state. Same surface behavior, simpler implementation.

5. **`state_snapshot` → `last_turn_state`.** Renamed for clarity. Captured at the single write point, reflecting the full post-turn state (including prior_history and sanitizer). EV checkers are updated to reference the new field name.

## Constraints

- Pipeline phase order is unchanged: ruling → narrate → scene extract → state extract → storytell extract → apply → sanitizer
- Narrative token streaming is unchanged — tokens arrive at the frontend as they do today
- The inflight lock (`_inflight` in `engine/config.py`) stays as the sole mutual-exclusion mechanism
- Cancel signal infrastructure (`asyncio.Event` per save_dir) stays as-is
- No LLM path changes — no interrupt signals, no new LLM calls
- `prompts.jsonl` entries are part of the atomic write block (they are consumed offline by EV tooling, not by the live server)

## Non-goals

- Async / background execution for any pipeline step
- Changing the LLM call interface or extraction models
- Rewriting the frontend SSE consumer beyond adding `panel_update` event handling
- Adding state versioning or `state_N.yaml` history files
- Replacing `events.jsonl` — it remains the canonical turn record

## Decision Table

### Core architecture

| Decision | What | Why |
|---|---|---|
| Single atomic write at turn end | All `save_state`, `append_event`, `append_chronicle`, `append_prompts`, prior_history, and sanitizer writes happen in one contiguous block after all LLM phases complete. | Eliminates partial-turn corruption on crash. Cancel has no files to revert. |
| Sanitizer runs in-memory before final write | Sanitizer executes at the same pipeline position (after storytell, before yield complete). Its mutations land on the in-memory state dict. The single write block includes sanitizer changes. | Simplest migration path — no timing change, no behavioral change to sanitizer logic. |
| prior_history moves into deferred write | The prior_history bullet is computed in memory and appended to the state dict. The single write block persists it. | Removes the write-2 partial write point. No behavioral change to prior_history content. |
| Crash resilience tradeoff accepted | A crash mid-turn loses the current turn entirely. On-disk state is clean at the last completed turn. | Preferable to current behavior where crash produces half-written state that cancel/delete may not fully revert. |

### Cancel and retry

| Decision | What | Why |
|---|---|---|
| Cancel = memory discard + SSE reset | `POST /turn/cancel` sets cancel flag, waits for generator to return (via `finally`), then sends a `panel_update` SSE event resetting all panels to the pre-turn state. No files touched. | Eliminates the entire snapshot-revert code path. Cancel is O(1) — just stop and push a reset event. |
| Cancel signal check points removed | The `is_cancel_requested()` checks at each yield point stay, but they `return` immediately (no persist has happened yet). | The generator exits cleanly via `finally`. No partial-persist concern. |
| `register_persist` removed | `pop_persist_started` was already removed in completed plan `tooling-infra/dead-code-removal.md`. `register_persist` existed to prevent double-revert in the old cancel path. With no revert needed, it has no purpose. | Dead code removal. |
| `remove_last_event` not called on cancel | No event was written — nothing to remove. | The cancel endpoint becomes: set flag, await done, send SSE reset, return. |
| `POST /turn/delete` unchanged | Delete still removes the last turn's event/chronicle/prompts from disk. Since there's only one write block, there is exactly one event and one chronicle entry to remove. | The delete endpoint already works correctly for fully-persisted turns. No change needed. |

### SSE progressive updates

| Decision | What | Why |
|---|---|---|
| New `panel_update` SSE event type | After each extraction phase completes, the pipeline yields `("panel_update", {"panel": "scene"|"state"|"arc", "data": {...}})`. The frontend listens for this event type and swaps the matching panel's HTML. | Decouples panel refreshes from phase lifecycle. Frontend handles one event type uniformly. |
| Panel data is rendered from in-memory state | Each panel receives the state tree subset relevant to it (scene → NPC compendium + location; state → PC state + conditions + inventory; arc → threads + goals + beats). | No disk reads for UI updates. The data is already in memory. |
| Narrative streaming unchanged | Token SSE events (`type: "narrative"`) continue as today. | No change to the narration streaming path. |
| `turn_complete` SSE event still fires | The `yield ("complete", turn_result)` at line 530 remains. It carries the final TurnResult and signals narrative drain. | Existing frontend depends on this for finalizing the turn view. |

### State snapshot naming

| Decision | What | Why |
|---|---|---|
| Rename `state_snapshot` to `last_turn_state` | In event N, `last_turn_state` = the complete state dict after turn N completed. It is the state that turn N+1 starts from. | `state_snapshot` implies a temporary freeze. `last_turn_state` is accurate and self-documenting. This is the state of the previous turn, accessible for EV tooling and prompt re-rendering. |
| EV checkers updated in scope | All 15+ checkers, `prompt_context.py`, `state_tools.py`, `events.py`, and `audit.py` that reference `state_snapshot` are migrated to `last_turn_state`. | Keeping both names would cause confusion. One name, one semantics. |

### Prompt context correction

| Decision | What | Why |
|---|---|---|
| `prompt_context.py` uses `prev_snap` for turn N's prompt | Turn N's prompt was built using turn N-1's state. With `last_turn_state` including sanitizer, turn N's prompt context must still use turn N-1's `last_turn_state` for all fields except turn-specific metadata (band, scene_phase). | Using turn N's `last_turn_state` would include turn N's own sanitizer mutations in turn N's prompt — semantically wrong. The engine fed turn N-1's state to the LLM for turn N's prompt. |

### Checker correction

| Decision | What | Why |
|---|---|---|
| Remove `_apply_sanitizer_changes_to_arc()` | This function reconstructs sanitizer state from `changes_detail` because `state_snapshot` didn't include sanitizer. With `last_turn_state` including sanitizer, it would double-apply. | Simpler code, correct behavior. The checker reads `last_turn_state` directly for thread existence validation. |

## Interface Boundaries

### Event schema change

Current event field:
```python
event["state_snapshot"] = load_state(save_dir)
```

New event field:
```python
event["last_turn_state"] = state  # the already-computed state dict (includes prior_history + sanitizer)
```

No `load_state` call needed — the state dict is already in memory at the write point. This is cheaper (one less YAML serialization round-trip) and correct by construction.

### SSE event additions

```python
# After scene extraction applied to in-memory state:
yield ("panel_update", {
    "panel": "scene",
    "data": _render_scene_panel(state),
})

# After state extraction applied to in-memory state:
yield ("panel_update", {
    "panel": "state",
    "data": _render_state_panel(state),
})

# After storytell extraction applied to in-memory state (before sanitizer):
yield ("panel_update", {
    "panel": "arc",
    "data": _render_arc_panel(state),
})
```

Panel render functions are extracted from the existing template rendering path — they read from the state dict and return the HTML fragment for that panel.

### Cancel endpoint change

Current (`routes.py:400-425`):
- Request cancel → await turn done → read last event → get state_snapshot → remove event → remove chronicle → save state from snapshot

New:
- Request cancel → await turn done → send `panel_update` reset SSE → return

### Delete endpoint

Unchanged. It removes the last turn's event and chronicle from disk. Since there is only one write block, there is exactly one event and one chronicle entry. The delete handler already works correctly.

### `register_persist`

Removed entirely. `pop_persist_started` was already removed in completed plan `tooling-infra/dead-code-removal.md`. `register_persist` existed only to prevent double-revert in cancel. With no revert path, it is dead.

## Rejected Alternatives

| Alternative | Rejected because |
|---|---|
| Keep state_snapshot as-is, fix timing | Fixing the capture point (move after sanitizer) would still leave the cancel/delete revert path in place. The snapshot would no longer be stale, but the atomicity concern and orphaned artifact risk remain. Does not enable progressive UI. |
| Versioned state files (`state_N.yaml`) | Adds a new file per turn and a cleanup policy. The single state dump in the event is sufficient for EV tooling. State file versioning solves a problem no one has. |
| Frontend fetches panel data via HTMX after each phase | Adds N extra HTTP round-trips per turn. The SSE stream already has the connection open — pushing data through it is cheaper. |
| Abort the LLM server on cancel | Changes the LLM path, requires interrupt support from the LLM backend, and provides no benefit over simply discarding the in-memory state after the generator finishes. |

## Risks, Ambiguities, and Blockers

- **Race: cancel after write starts.** The atomic write block is not truly atomic across multiple files (`events.jsonl`, `state.yaml`, `chroncle.md`, `prompts.jsonl`). `server_errors.jsonl` is written by `ccya/server/app.py` (route-level error handlers), not by `turn.py`, so it cannot be part of turn's atomic write. If cancel arrives after `append_event` but before `save_state`, the event is on disk but state is from the previous turn. Mitigation: check cancel flag at the top of the write block. If set, skip the entire block and return. The cancel endpoint waited for `_turn_done` — if the generator exits without writing, cancel sees nothing to revert.
- **Panel render HTML generation.** The `_render_scene_panel(state)` etc. functions must produce HTML matching the current Jinja2 templates. These are extracted from the existing template rendering path (e.g., HTMX partial swaps). If templates change, panel render functions must be kept in sync.
- **SSE event ordering.** The frontend receives narrative tokens interleaved with `panel_update` events. The frontend must handle `panel_update` independently of narrative streaming — no ordering assumption beyond "panel_update for panel X arrives after its phase completes."
- **EV tooling migration.** Renaming `state_snapshot` to `last_turn_state` touches ~15 files. Each change is a mechanical find-and-replace, but the `prompt_context.py` reader logic must be carefully verified: the semantics change from "frozen copy of pre-sanitizer state" to "complete post-turn state including sanitizer."

## Files to change

### Core engine
- `ccya/engine/turn.py` — restructure write block, add `panel_update` yields, remove `register_persist` usage
- `ccya/engine/config.py` — remove `register_persist` (and `_persist_started` dict). `pop_persist_started` was already removed in completed plan `tooling-infra/dead-code-removal.md`.
- `ccya/engine/__init__.py` — remove deleted symbols from exports

### Server
- `ccya/server/routes.py` — simplify `cancel_turn()` (remove snapshot revert logic), update `delete_last_turn()` field reference
- `ccya/templates/index.html` — add `panel_update` SSE event handler in frontend JS

### State management
- `ccya/state/io.py` — `restore_snapshot_state` was already removed in completed plan `tooling-infra/dead-code-removal.md`. Consider removing the orphaned `state_snapshot.yaml` cleanup at line 136 (no file is ever written by that name anymore).
- `ccya/state/chronicle.py` — `remove_last_event()` (verify no orphaned event concern with single-write model)

### EV tooling (in scope)
- `ccya/ev/prompt_context.py` — `state_snapshot` → `last_turn_state`; extend `prev_snap` usage to cover all fields except turn-specific metadata (band, scene_phase, curtain_call, allowed_beat_types)
- `ccya/ev/events.py` — same rename
- `ccya/ev/audit.py` — same rename
- `ccya/ev/state_tools.py` — same rename
- `ccya/ev/checkers/thread_resolution_validity.py` — `state_snapshot` → `last_turn_state`; **remove `_apply_sanitizer_changes_to_arc()` entirely** (no longer needed, would double-apply sanitizer); remove `needs_non_turn_events=True` flag
- `ccya/ev/checkers/*.py` — same rename across ~14 other checker files (no behavioral changes needed)

### Roadmap and documentation
- `docs/repomap.md` — update state_snapshot references
- `docs/architecture/` — update data shape docs if they reference state_snapshot

## Pipeline flow (new)

```
ruling ──→ narrate ──→ scene extract ──→ state extract ──→ storytell extract
                │              │                 │                │
            SSE tokens      panel_update      panel_update    panel_update
                            (scene)           (state)          (arc)

                                                    │
                                                    ↓
                                          apply to in-memory state
                                          prior_history computed
                                          sanitizer runs in-memory
                                                    │
                                                    ↓
                                          ┌─────────────────────┐
                                          │  Atomic write block │
                                          │  ─ save_state       │
                                          │  ─ append_event     │
                                          │  ─ append_chronicle │
                                          │  ─ append_prompts   │
                                          └─────────────────────┘
                                                    │
                                                    ↓
                                            yield ("complete", ...)
```

## Cancel behavioral change

Currently, `cancel_turn()` (routes.py:395-425) **does** remove files: `remove_last_event()` and `remove_last_chronicle_turn()`. The new design removes this cleanup entirely. Canceled turns' events and chronicle entries will accumulate on disk indefinitely. This is a deliberate tradeoff (simpler cancel path), not a regression, but it means `events.jsonl` and `chronicle.md` grow without bound for games with many cancellations. Consider whether a periodic cleanup or lazy cleanup on turn start is needed.

## EV tooling impact analysis

### `state_snapshot` → `last_turn_state` rename

The rename is a mechanical find-and-replace across ~15 files. The **semantics shift** (pre-sanitizer → post-sanitizer) is the real concern. Most consumers are unaffected or benefit, but two files have critical issues:

#### [CRITICAL] `thread_resolution_validity.py` — double-applies sanitizer

This checker has `_apply_sanitizer_changes_to_arc()` (lines 12-89) that explicitly reconstructs sanitizer state from `changes_detail` because "The state_snapshot captured at the end of a turn doesn't include sanitizer changes (which run after the snapshot)." With `last_turn_state` already including sanitizer, this checker **double-applies** sanitizer thread changes.

**Fix:** Remove `_apply_sanitizer_changes_to_arc()` entirely. The checker should use `last_turn_state` directly for thread existence validation. The `prev_sanitizer` tracking and `changes_detail` fallback are no longer needed. The checker's `needs_non_turn_events=True` flag can be removed since it no longer reads sanitizer events.

#### [CRITICAL] `prompt_context.py` — uses turn N's own state for turn N's prompt

`build_prompt_context(events, turn_no, stream)` uses `turn_ev.get("state_snapshot")` (turn N's event) for most fields when re-rendering turn N's prompt. Currently this is pre-sanitizer state (what the engine actually fed to the LLM). With `last_turn_state` (post-sanitizer), turn N's prompt context would include turn N's own sanitizer mutations — **semantically wrong**. Turn N's prompt should be built from turn N-1's `last_turn_state`.

**Fix:** Use `prev_snap` (turn N-1's `last_turn_state`) for all fields except turn-specific metadata (band, scene_phase, curtain_call, allowed_beat_types). The current code already correctly uses `prev_snap` for `pending_beat` and `recent_beats` (lines 171-173, 250-251). Extend this pattern: for `storytell` stream, use `prev_snap` for `arc`, `inventory`, `conditions`, `location`, `compendium`, `pc`. For `scene` stream, use `prev_snap` for `pc`, `compendium`, `location`. For `state` stream, use `prev_snap` for `pc`, `inventory`, `conditions`, `location`. For `ruling` and `narrate` streams, use `prev_snap` for `arc`, `compendium`, `pc`, `location`, `inventory`, `scene`, `meta`. The `turn_ev.get("state_snapshot")` should only be used for turn-specific metadata that is set during turn N itself (band from ruling outcome, scene_phase from pacing_context).

### Checkers likely unaffected or improved

| File | Impact | Notes |
|---|---|---|
| `threads.py` | OK | Reads `state_snapshot` for thread existence. Post-sanitizer state is actually more correct. |
| `arc_goals.py` | OK | Reads `state_snapshot` for goal existence. Post-sanitizer state is more correct. |
| `goal_update_validity.py` | OK | Captures previous turn's `state_snapshot` for comparison. Post-sanitizer is fine. |
| `inventory.py` | OK | Reads `state_snapshot` for inventory/location. Sanitizer doesn't touch inventory. |
| `compendium_lifecycle.py` | OK | Reads `state_snapshot` for NPC lifecycle. Sanitizer doesn't touch compendium. |
| `gm_beat.py` | OK | Reads `state_snapshot` for `pending_gm_beat`. Sanitizer doesn't touch beats. |
| `state.py` | OK | Reads `state_snapshot` for location/scene. Sanitizer doesn't touch these. |
| `conditions.py` | OK | Reads `state_snapshot` for conditions. Sanitizer doesn't touch conditions. |
| `npc_presence.py` | OK | Reads `state_snapshot` for NPC presence. Sanitizer doesn't touch presence. |
| `new_thread_validity.py` | OK | Reads `state_snapshot` for thread existence. Post-sanitizer is fine. |
| `arc_resolution_validity.py` | OK | Reads `state_snapshot` for arc state. Post-sanitizer is fine. |
| `llm_checkers.py` | OK | Reads `state_snapshot.meta.pending_gm_beat`. Sanitizer doesn't touch beats. |
| `sanitizer.py` | OK | Reads `changes_detail` directly from sanitizer events, not `state_snapshot`. |

### EV tools likely unaffected or improved

| File | Impact | Notes |
|---|---|---|
| `state_tools.py` | OK/Improved | Reads `state_snapshot` for thread lifecycle, beat data, pending beats, pressure estimation. Post-sanitizer state is actually more accurate for display. |
| `events.py` | OK | `assign_scene_ids` reads `state_snapshot` for location. Sanitizer doesn't change location. |
| `audit.py` | OK | `detect_npc_ghosting` reads `state_snapshot` for NPC compendium. Sanitizer doesn't add/remove NPCs. |

## What I fear

### 1. `prompt_context.py` refactoring is the highest-risk change

Extending `prev_snap` usage across 5 stream branches (scene, state, storytell, ruling, narrate) is a large refactoring with many individual field-level decisions. Easy to miss one field or use the wrong source (prev_snap vs turn_ev). This is not a find-and-replace — it's a logic change that could silently produce wrong prompt context for LLM evals. **Mitigation:** write a regression test or `ev.py` comparison that renders turn N's prompt before and after the change and diffs the output.

### 2. Canceled turns accumulate without bound

The design removes cleanup on cancel. In practice, a user who cancels and retries 20 times gets 20 extra events and 20 extra chronicle entries. The turn viewer (`tv.py`) loads all events for analysis. This could get slow or break UI for games with heavy cancel/retry usage. **Mitigation:** consider lazy cleanup on turn start (remove events with `turn > current_turn` and `kind == "turn"` that don't have a corresponding `state.yaml` entry), or a periodic cleanup command.

### 3. Panel render extraction is fragile

The design says `_render_scene_panel(state)` etc. are "extracted from the existing template rendering path." The current frontend uses HTMX to fetch `/panels/state-left` and `/panels/state-right` via HTTP GET, which calls `_render("_state_left.html", ...)` with Jinja2. Extracting HTML generation from Jinja2 templates into Python functions that take a raw state dict is non-trivial. Jinja2 templates have logic (loops, conditionals, filters) that must be replicated in Python. If templates change and render functions don't, the UI will show stale or incorrect data. **Mitigation:** consider sending raw JSON state data in `panel_update` events and letting the frontend render via JS, rather than pushing pre-rendered HTML.

### 4. Atomic write block handles cancel but not crashes

The design mitigates cancel mid-write (check flag, skip block). But if the process crashes mid-write (e.g., `save_state` succeeds but `append_event` crashes), you still get partial corruption — event on disk but state not updated, or vice versa. The cancel flag check doesn't help here. **Mitigation:** use atomic file operations (write to temp files, then rename) for `events.jsonl` and `chronicle.md` too, or accept this limitation and document it.

### 5. `clear_all_turn_locks()` still references `_persist_started`

Removing `register_persist` means `clear_all_turns_locks()` in `config.py:83` (`_persist_started.pop(save_dir, None)`) becomes dead code. Must be removed too, or it will silently do nothing and confuse future maintainers.

### 6. Delete reverts to post-sanitizer state

With `last_turn_state` including sanitizer mutations, `delete_last_turn()` reverts to a state that includes sanitizer changes. This is actually more correct (undoes the full turn), but it's a behavioral change. Users who delete a turn expect to undo to the state before that turn. With sanitizer mutations included, they undo further. This could surprise users or break workflows that depend on specific pre-sanitizer state. **Mitigation:** document this behavioral change explicitly in the delete endpoint docs or UI.
