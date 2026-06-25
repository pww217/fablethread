---
title: Deferred state persistence — single best-effort atomic write at turn end
status: reviewed
design: docs/design/deferred-state-persist-design.md
created: 2026-06-24
---

# Deferred State Persist Design

## Purpose

This document is the design authority for moving all turn pipeline state writes to a single point at turn end, enabling clean cancel/retry and progressive UI updates from in-memory state.

## MVP boundary

Two changes are bundled here but can ship independently:

1. **Deferred atomic write** (correctness fix). Consolidates 3+ disk writes into one best-effort atomic block at turn end. Eliminates stale `state_snapshot`, orphaned artifacts on cancel, and partial-turn corruption. **Shippable alone.**
2. **Progressive SSE panel updates** (UX improvement). Pushes structured panel data via SSE after each extraction phase. Frontend renders panels from JSON. **Depends on #1** (needs in-memory state at phase boundaries) but can be deferred without blocking #1.

If panel render extraction turns out messier than expected, #1 ships without #2. The cancel correctness fix and stale snapshot fix are not contingent on progressive UI.

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

1. **Single best-effort atomic write block** at the end of the turn pipeline. State, events, chronicle, prompts, prior_history, and sanitizer results are all written in one sequence after all phases complete. `state.yaml` uses `os.replace` for true atomicity. `events.jsonl` and `chronicle.md` are append-only — written to temp then renamed in sequence. If a crash occurs before or during this block, the on-disk state reflects the end of the last completed turn — no partial-turn corruption.

2. **Progressive SSE updates** from in-memory state. After each extraction phase (scene → state → storytell), a `panel_update` SSE event carries the computed panel data. The frontend updates the matching panel immediately. Narrative tokens continue to stream as today.

3. **Cancel = memory discard + frontend reset.** No file cleanup needed. `POST /turn/cancel` returns `{"ok": true, "cancelled": true}`. The frontend interprets this as a signal to reset all panels to the pre-turn state (read from the previous turn's written `last_turn_state`). No SSE push needed — cancel and turn SSE streams are separate connections.

4. **Canceled turns: lazy cleanup on turn start.** Canceled turns' events and chronicle entries accumulate on disk. On the next successful turn start, the engine removes events whose `turn` number exceeds the current `meta.turn` and whose `kind` is not `sanitizer`. This keeps `events.jsonl` bounded without adding complexity to the cancel path. The turn viewer (`tv.py`) should also filter out canceled turns from its display.

5. **Retry = delete + rerun.** `POST /turn/delete` removes the last turn's event/chronicle/prompts and invalidates it from the in-memory state view. The next turn start sees the clean pre-turn state. Same surface behavior, simpler implementation.

6. **`state_snapshot` → `last_turn_state`.** Renamed for clarity. Captured at the single write point, reflecting the full post-turn state (including prior_history and sanitizer). EV checkers are updated to reference the new field name.

## Constraints

- Pipeline phase order is unchanged: ruling → narrate → scene extract → state extract → storytell extract → apply → sanitizer
- Narrative token streaming is unchanged — tokens arrive at the frontend as they do today
- The inflight lock (`_inflight` in `engine/config.py`) stays as the sole mutual-exclusion mechanism
- Cancel signal infrastructure (`asyncio.Event` per save_dir) stays as-is
- No LLM path changes — no interrupt signals, no new LLM calls
- `prompts.jsonl` entries are part of the best-effort atomic write block (they are consumed offline by EV tooling, not by the live server)

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
| Single best-effort atomic write at turn end | All `save_state`, `append_event`, `append_chronicle`, `append_prompts`, prior_history, and sanitizer writes happen in one contiguous block after all LLM phases complete. `state.yaml` uses `os.replace` (true atomicity). `events.jsonl` and `chronicle.md` written to temp then renamed in sequence (best-effort). | Eliminates partial-turn corruption on crash. Cancel has no files to revert. |
| Sanitizer runs in-memory before final write | Sanitizer executes at the same pipeline position (after storytell, before yield complete). Its mutations land on the in-memory state dict. The single write block includes sanitizer changes. | Simplest migration path — no timing change, no behavioral change to sanitizer logic. |
| prior_history moves into deferred write | The prior_history bullet is computed in memory and appended to the state dict. The single write block persists it. | Removes the write-2 partial write point. No behavioral change to prior_history content. |
| Crash resilience tradeoff accepted | A crash mid-turn loses the current turn entirely. On-disk state is clean at the last completed turn. | Preferable to current behavior where crash produces half-written state that cancel/delete may not fully revert. |

### Cancel and retry

| Decision | What | Why |
|---|---|---|
| Cancel = memory discard + frontend reset | `POST /turn/cancel` sets cancel flag, waits for generator to return (via `finally`), returns `{"ok": true, "cancelled": true}`. The frontend resets panels to the pre-turn state. No files touched. Lazy cleanup of canceled events happens on next turn start. | Eliminates the entire snapshot-revert code path. Cancel is O(1) — just stop and return a flag. |
| Cancel signal check points removed | The `is_cancel_requested()` checks at each yield point stay, but they `return` immediately (no persist has happened yet). | The generator exits cleanly via `finally`. No partial-persist concern. |
| `register_persist` removed | `pop_persist_started` was already removed in completed plan `tooling-infra/dead-code-removal.md`. `register_persist` existed to prevent double-revert in the old cancel path. With no revert needed, it has no purpose. | Dead code removal. |
| `remove_last_event` not called on cancel | No event was written — nothing to remove. | The cancel endpoint becomes: set flag, await done, return `{"ok": true, "cancelled": true}`. Frontend handles panel reset. |
| `POST /turn/delete` unchanged | Delete still removes the last turn's event/chronicle/prompts from disk. Since there's only one write block, there is exactly one event and one chronicle entry to remove. | The delete endpoint already works correctly for fully-persisted turns. No change needed. |

### SSE progressive updates

| Decision | What | Why |
|---|---|---|
| New `panel_update` SSE event type | After each extraction phase completes, the pipeline yields `("panel_update", {"panel": "scene"|"state"|"arc", "data": {...}})`. The frontend listens for this event type and renders the matching panel from the JSON data. | Decouples panel refreshes from phase lifecycle. Frontend handles one event type uniformly. |
| Panel data is raw JSON from in-memory state | Each panel receives the state tree subset relevant to it (scene → NPC compendium + location; state → PC state + conditions + inventory; arc → threads + goals + beats). The frontend (Alpine.js) renders the panel from this data. | No template sync fragility. No Jinja2 extraction. The SSE stream already has the connection open — pushing structured data through it is cheaper than HTMX round-trips. |
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
| `prompt_context.py` uses `prev_snap` for turn N's prompt | Turn N's prompt was built using turn N-1's state. With `last_turn_state` including sanitizer, turn N's prompt context must use turn N-1's `last_turn_state` for all state fields; turn-specific metadata (band, scene_phase, curtain_call, allowed_beat_types) comes from turn N's event. | Using turn N's `last_turn_state` would include turn N's own sanitizer mutations in turn N's prompt — semantically wrong. The engine fed turn N-1's state to the LLM for turn N's prompt. |

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
    "data": {
        "npcs": state.get("compendium", {}).get("npcs", {}),
        "location": state.get("location"),
    },
})

# After state extraction applied to in-memory state:
yield ("panel_update", {
    "panel": "state",
    "data": {
        "pc": state.get("pc"),
        "inventory": state.get("inventory"),
        "conditions": state.get("pc", {}).get("conditions"),
    },
})

# After storytell extraction applied to in-memory state (before sanitizer):
yield ("panel_update", {
    "panel": "arc",
    "data": {
        "arc": state.get("arc"),
        "scene": state.get("scene"),
        "meta": state.get("meta"),
    },
})
```

Panel data is raw JSON. The frontend (Alpine.js) renders panels from this data, matching the current Jinja2 templates. This avoids template-sync fragility — no need to extract Jinja2 logic into Python functions.

### Cancel endpoint change

Current (`routes.py:400-425`):
- Request cancel → await turn done → read last event → get state_snapshot → remove event → remove chronicle → save state from snapshot

New:
- Request cancel → await turn done → return `{"ok": true, "cancelled": true}`
- Frontend interprets `cancelled: true` and resets all panels to the pre-turn state (from previous turn's `last_turn_state`)
- Lazy cleanup of canceled events happens on next successful turn start (removes events with `turn > meta.turn`)

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

- **Atomic write block — cancel vs crash.** The best-effort atomic write block handles cancel mid-write (check flag, skip block). But `events.jsonl` and `chronicle.md` are append-only files — you can't `os.replace` them with a temp file without losing every prior turn's events. `state.yaml` works because it's a single-file snapshot. `prompts.jsonl` is small enough to treat like `state.yaml` (write to temp, rename). **Mitigation:** write `events.jsonl` and `chronicle.md` to temp files first, then rename all files in sequence. If a crash hits mid-sequence, you get a mismatch (e.g., `state.yaml` updated but `events.jsonl` not), but this is astronomically rare — requires a crash *between* two `os.replace` calls, not during a write. `server_errors.jsonl` is written by `ccya/server/app.py` (route-level error handlers), not by `turn.py`, so it cannot be part of turn's atomic write.
- **SSE event ordering.** The frontend receives narrative tokens interleaved with `panel_update` events. The frontend must handle `panel_update` independently of narrative streaming — no ordering assumption beyond "panel_update for panel X arrives after its phase completes."
- **EV tooling migration.** Renaming `state_snapshot` to `last_turn_state` touches ~15 files. Each change is a mechanical find-and-replace, but the `prompt_context.py` reader logic must be carefully verified: the semantics change from "frozen copy of pre-sanitizer state" to "complete post-turn state including sanitizer."
- **Frontend panel rendering accuracy.** The frontend must render panels from raw JSON to match the current Jinja2 templates. If templates change, the frontend rendering logic must be kept in sync. **Mitigation:** the frontend rendering logic should be extracted into reusable functions (not inline in the SSE handler) so it can be compared against the Jinja2 templates during review.

## Files to change

### Core engine
- `ccya/engine/turn.py` — restructure write block, add `panel_update` yields, remove `register_persist` usage
- `ccya/engine/config.py` — remove `register_persist` (and `_persist_started` dict). `pop_persist_started` was already removed in completed plan `tooling-infra/dead-code-removal.md`. Also remove `_persist_started.pop(save_dir, None)` from `clear_all_turn_locks()` (line 83).
- `ccya/engine/__init__.py` — remove deleted symbols from exports

### Server
- `ccya/server/routes.py` — simplify `cancel_turn()` (remove snapshot revert logic, return `{"ok": true, "cancelled": true}`), update `delete_last_turn()` field reference (`state_snapshot` → `last_turn_state`)
- `ccya/templates/index.html` — add `panel_update` SSE event handler in frontend JS (renders panels from JSON), add cancel handling (reset panels on `cancelled: true` response)

### State management
- `ccya/state/io.py` — `restore_snapshot_state` was already removed in completed plan `tooling-infra/dead-code-removal.md`. Consider removing the orphaned `state_snapshot.yaml` cleanup at line 136 (no file is ever written by that name anymore).
- `ccya/state/chronicle.py` — `remove_last_event()` (verify no orphaned event concern with single-write model); update `append_event` and `append_chronicle` to write to temp files then `os.replace` for maximum crash resilience

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
                 │
             SSE tokens
             (narrative)

                                                     │
                                                     ↓
                                           apply to in-memory state
                                           prior_history computed
                                           sanitizer runs in-memory
                                                     │
                                    ┌───────────────┼───────────────┐
                                    │               │               │
                              panel_update    panel_update    panel_update
                              (scene)         (state)         (arc)
                                    │               │               │
                                    └───────────────┼───────────────┘
                                                    │
                                                    ↓
                                       ┌─────────────────────────┐
                                       │  Best-effort atomic     │
                                       │  write block            │
                                       │  ─ save_state           │
                                       │  ─ write_event*         │
                                       │  ─ write_chronicle*     │
                                       │  ─ write_prompts        │
                                       └─────────────────────────┘
                                       * Write to temp file, then os.replace
                                       * events.jsonl and chronicle.md are
                                       * append-only — true atomicity not
                                       * possible, but crash gap is negligible
                                                    │
                                                    ↓
                                             yield ("complete", ...)
```

## Cancel behavioral change

Currently, `cancel_turn()` (routes.py:395-425) **does** remove files: `remove_last_event()` and `remove_last_chronicle_turn()`. The new design defers this cleanup: canceled turns' events and chronicle entries accumulate on disk until the next successful turn start, when the engine removes events whose `turn` number exceeds the current `meta.turn` (excluding sanitizer events). The turn viewer (`tv.py`) should also filter out canceled turns from its display. This keeps the cancel path simple (O(1) flag return) while keeping `events.jsonl` bounded.

## EV tooling impact analysis

### `state_snapshot` → `last_turn_state` rename

The rename is a mechanical find-and-replace across ~15 files. The **semantics shift** (pre-sanitizer → post-sanitizer) is the real concern. Most consumers are unaffected or benefit, but two files have critical issues:

#### [CRITICAL] `thread_resolution_validity.py` — double-applies sanitizer

This checker has `_apply_sanitizer_changes_to_arc()` (lines 12-89) that explicitly reconstructs sanitizer state from `changes_detail` because "The state_snapshot captured at the end of a turn doesn't include sanitizer changes (which run after the snapshot)." With `last_turn_state` already including sanitizer, this checker **double-applies** sanitizer thread changes.

**Fix:** Remove `_apply_sanitizer_changes_to_arc()` entirely. The checker should use `last_turn_state` directly for thread existence validation. The `prev_sanitizer` tracking and `changes_detail` fallback are no longer needed. The checker's `needs_non_turn_events=True` flag can be removed since it no longer reads sanitizer events.

#### [CRITICAL] `prompt_context.py` — uses turn N's own state for turn N's prompt

`build_prompt_context(events, turn_no, stream)` uses `turn_ev.get("state_snapshot")` (turn N's event) for most fields when re-rendering turn N's prompt. Currently this is pre-sanitizer state (what the engine actually fed to the LLM). With `last_turn_state` (post-sanitizer), turn N's prompt context would include turn N's own sanitizer mutations — **semantically wrong**. Turn N's prompt should be built from turn N-1's `last_turn_state`.

**Fix:** Use `prev_snap` (turn N-1's `last_turn_state`) for all state fields. Use `turn_ev` only for turn-specific metadata set during turn N itself (band from ruling outcome, scene_phase from pacing_context, curtain_call from scene phase logic, allowed_beat_types from pacing). Implementation details (which exact fields per stream branch) belong in the plan document.

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

### 2. Frontend panel rendering accuracy

The frontend must render panels from raw JSON to match the current Jinja2 templates. If templates change, the frontend rendering logic must be kept in sync. **Mitigation:** extract rendering logic into reusable functions (not inline in the SSE handler) so it can be compared against the Jinja2 templates during plan review.

### 3. Atomic write block handles cancel but not crashes

The best-effort atomic write block handles cancel mid-write (check flag, skip block). But `events.jsonl` and `chronicle.md` are append-only files — you can't `os.replace` them with a temp file without losing every prior turn's events. `state.yaml` works because it's a single-file snapshot. `prompts.jsonl` is small enough to treat like `state.yaml` (write to temp, rename). **Mitigation:** write `events.jsonl` and `chronicle.md` to temp files first, then rename all files in sequence. If a crash hits mid-sequence, you get a mismatch (e.g., `state.yaml` updated but `events.jsonl` not), but this is astronomically rare — requires a crash *between* two `os.replace` calls, not during a write. Accept this limitation and document it.

### 4. Delete reverts to post-sanitizer state

With `last_turn_state` including sanitizer mutations, `delete_last_turn()` reverts to a state that includes sanitizer changes. This is actually more correct (undoes the full turn), but it's a behavioral change. Users who delete a turn expect to undo to the state before that turn. With sanitizer mutations included, they undo further. This could surprise users or break workflows that depend on specific pre-sanitizer state. **Mitigation:** document this behavioral change explicitly in the delete endpoint docs or UI.

## Review Findings (2026-06-25)

### Problem framing: VALIDATED

- **3+ saves per turn** — Confirmed in `turn.py:437`, `turn.py:492`, `turn.py:505`. All three `save_state()` calls are in the turn pipeline.
- **`state_snapshot` is stale** — Confirmed at `turn.py:438`: `event["state_snapshot"] = load_state(save_dir)` reads from disk after write 1, excluding prior_history (write 2) and sanitizer (write 3).
- **Cancel/delete restore from stale snapshot** — Confirmed in `routes.py:414`: `pre_turn_state = event.get("state_snapshot")` reads the stale snapshot. Both cancel (line 417-418) and delete (line 450-451) restore from it.
- **UI receives turn data only at yield ("complete")** — Confirmed at `turn.py:530`: `yield ("complete", result_obj)` is the only complete signal. No intermediate panel updates.
- **`register_persist` is dead code** — Confirmed: `turn.py:436` calls `register_persist(str(save_dir))`, which sets `_persist_started[save_dir] = True` in `config.py:55-56`. `_persist_started` is only read in `clear_all_turn_locks()` at `config.py:83` (pops the key). No other consumer exists.
- **`_persist_started` in `clear_all_turn_locks`** — Confirmed at `config.py:83`: `_persist_started.pop(save_dir, None)` becomes dead code when `register_persist` is removed.

### Proposed solutions: VALIDATED

- **Single atomic write block** — `io.py:115-121` already uses `os.replace` for atomicity. Consolidating the three `save_state()` calls into one point after all phases is correct. The atomic write block should include: `save_state()`, `append_event()`, `append_chronicle()`, `append_prompts()`.
- **`panel_update` SSE events** — `routes.py:307-391` yields three event types: `("token", chunk)`, `("phase", payload)`, `("complete", result_obj)`. Adding `("panel_update", {...})` after each extraction phase is correct. The frontend at `index.html:1766-1789` listens for `narrative_token`, `phase`, and `turn_complete` events via EventSource. A new `panel_update` listener should be added.
- **Cancel = memory discard** — **GAP IDENTIFIED**: The cancel endpoint (`routes.py:394-425`) is a POST endpoint that returns `JSONResponse`. It cannot push SSE events through the open SSE connection (which is a separate GET endpoint). The design says cancel should "send a `panel_update` reset SSE event," but the cancel endpoint has no reference to the SSE stream. **Fix**: The cancel endpoint should return `{"ok": true, "cancelled": true}` and the frontend should interpret this as a signal to reset panels to the previous turn's `last_turn_state`. No SSE push needed.
- **`register_persist` removal** — Confirmed correct. Remove from: `turn.py:15` (import), `turn.py:436` (call), `config.py:36` (dict), `config.py:55-56` (function), `config.py:83` (pop in `clear_all_turn_locks`), `engine/__init__.py:9,28` (export).
- **`state_snapshot` → `last_turn_state` rename** — Confirmed ~100 references across EV tooling. The rename is mechanical but the semantics shift (pre-sanitizer → post-sanitizer) is the real concern.
- **`prompt_context.py` fix** — **VALIDATED**: Current code at `prompt_context.py:101` uses `state_snapshot = turn_ev.get("state_snapshot")` (turn N's event) for most fields. The design correctly identifies that turn N's prompt should use `prev_snap` (turn N-1's state) for all fields except turn-specific metadata. Currently `prev_snap` is only used for `pending_beat` and `recent_beats` in storytell (lines 171-173) and narrate (line 250) streams. The fix should extend `prev_snap` usage to: `arc`, `inventory`, `conditions`, `location`, `compendium`, `pc` across all 5 stream branches.
- **`_apply_sanitizer_changes_to_arc()` removal** — **VALIDATED**: `thread_resolution_validity.py:12-89` reconstructs sanitizer state from `changes_detail` because `state_snapshot` didn't include sanitizer. With `last_turn_state` including sanitizer, this function would double-apply. Remove entirely. The checker should use `last_turn_state` directly. Also remove `needs_non_turn_events=True` flag at line 96.
- **`io.py:136` orphaned cleanup** — **VALIDATED**: `(save_dir / "state_snapshot.yaml").unlink(missing_ok=True)` removes a file that is no longer written. Safe to remove.

### Additional findings

- **Cancel endpoint architecture gap** (see above): The cancel endpoint at `routes.py:394-425` currently: (1) loads last events before cancel, (2) sets cancel flag, (3) awaits turn done, (4) loads last events after cancel, (5) if a new turn was written, removes it and restores state. The new design should simplify to: (1) set cancel flag, (2) await turn done, (3) clear cancel, (4) return `{"ok": true, "cancelled": true}`. The frontend handles panel reset.
- **Delete endpoint field reference** — `routes.py:445`: `pre_turn_state = last_event.get("state_snapshot")` should become `last_event.get("last_turn_state")`.
- **`register_persist` import in turn.py** — `turn.py:15`: `from ccya.engine.config import EngineConfig, _build_jinja_env, _inflight, _log_llm_io, _log_prompts, is_cancel_requested, register_persist, register_turn, signal_turn_done` — `register_persist` should be removed from this import.
- **`register_persist` export in engine/__init__.py** — `engine/__init__.py:9,28`: `register_persist` is imported and exported. Both should be removed.
- **`_persist_started` dict in config.py** — `config.py:36`: `_persist_started: dict[str, bool] = {}` should be removed.
- **`register_persist` function in config.py** — `config.py:55-56`: The function should be removed.
- **`clear_all_turn_locks` cleanup** — `config.py:83`: `_persist_started.pop(save_dir, None)` should be removed.
- **`register_persist` call in turn.py** — `turn.py:436`: `register_persist(str(save_dir))` should be removed.
- **`load_state` call for event snapshot** — `turn.py:438`: `event["state_snapshot"] = load_state(save_dir)` should become `event["last_turn_state"] = state` (the in-memory dict, no `load_state` call needed).
- **`prior_history` write** — `turn.py:492`: `save_state(save_dir, state)` after prior_history bullet should be removed (moved to single atomic write block).
- **Sanitizer write** — `turn.py:505`: `save_state(save_dir, state)` after sanitizer should be removed (moved to single atomic write block).
- **`_format_ts` in routes.py** — `routes.py:158-164`: Used in cancel endpoint? No, only in `turn_complete` SSE at line 360. Unchanged.
- **`_load_current_state` in routes.py** — `routes.py:374`: `"_load_current_state()"` is called in the `turn_complete` SSE event. This reads from disk. With progressive panel updates, this could be replaced with in-memory state from the turn result. However, this is a minor optimization — the turn_complete event already has the full state in `result_obj`.

### Risks reassessment

- **Atomic write block cancel vs crash** — Design's mitigation (temp files + os.replace) is correct. `state.yaml` is already atomic. `events.jsonl` and `chronicle.md` are append-only — true atomicity not possible, but crash gap is negligible.
- **Panel render HTML generation** — Design correctly identifies this as fragile. The mitigation (send raw JSON state data in `panel_update` events, let frontend render via JS) is recommended over extracting Jinja2 templates to Python functions.
- **SSE event ordering** — Design correctly identifies that frontend must handle `panel_update` independently of narrative streaming.
- **EV tooling migration** — Design correctly identifies ~15 files to update. The `prompt_context.py` logic change is the highest risk (validated above).
- **Canceled turns accumulate** — Design correctly identifies this tradeoff. Lazy cleanup on turn start is a good mitigation.
- **`clear_all_turn_locks` references `_persist_started`** — **CONFIRMED**: `config.py:83` must be updated.
- **Delete reverts to post-sanitizer state** — Design correctly identifies this behavioral change. Document it.

### Verdict

**Design is sound. Proceed to planning.**

All problem claims are validated against source. All proposed solutions are correct. The one gap (cancel endpoint SSE push) is architectural and easily resolved by having the cancel endpoint return a JSON flag and the frontend handle panel reset. No design decisions need to change.
