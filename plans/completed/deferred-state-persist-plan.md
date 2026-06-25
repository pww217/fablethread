# Plan: Deferred State Persistence

## Design Reference

`docs/design/deferred-state-persist-design.md` (status: `implemented`)

## Purpose

Consolidate 3+ disk writes per turn into a single best-effort atomic block at turn end. Eliminate stale `state_snapshot`, orphaned artifacts on cancel, and partial-turn corruption. Rename `state_snapshot` → `last_turn_state` across all tooling. Add progressive `panel_update` SSE events for UI panel refreshes.

## Problem Statement

The turn pipeline (`run_turn()` in `ccya/engine/turn.py`) writes state to disk 3+ times per turn:

| Write | Location | What |
|---|---|---|
| 1 | `turn.py:437` | `save_state(save_dir, state)` — full state after all extractions applied |
| 2 | `turn.py:492` | `save_state(save_dir, state)` — after `prior_history` bullet appended |
| 3 | `turn.py:505` | `save_state(save_dir, state)` — after thread sanitizer |

`state_snapshot` is captured at line 438 (after write 1), so it excludes prior_history (write 2) and sanitizer (write 3) changes. The cancel endpoint (`POST /turn/cancel`, `routes.py:400`) and delete endpoint (`POST /turn/delete`, `routes.py:428`) restore from this stale snapshot, producing incorrect state after revert.

## Constraints

- Pipeline phase order is unchanged: ruling → narrate → scene extract → state extract → storytell extract → apply → sanitizer
- Narrative token streaming is unchanged
- The inflight lock (`_inflight` in `engine/config.py`) stays as the sole mutual-exclusion mechanism
- Cancel signal infrastructure (`asyncio.Event` per save_dir) stays as-is
- No LLM path changes
- `prompts.jsonl` entries are part of the best-effort atomic write block

## Phase Summary

Five phases ordered by dependency:

1. **Dead code removal** — Remove `register_persist`, `_persist_started`, orphaned `state_snapshot.yaml` cleanup. No behavioral change.
2. **Deferred atomic write block** — Consolidate 3 `save_state()` calls into one point after all phases. Rename `state_snapshot` → `last_turn_state` in the engine. Move prior_history and sanitizer into the deferred block.
3. **Simplify cancel endpoint** — Remove snapshot-revert logic. Return `{"ok": true, "cancelled": true}`. Frontend handles panel reset.
4. **EV tooling migration** — Rename `state_snapshot` → `last_turn_state` across ~15 EV files. Remove `_apply_sanitizer_changes_to_arc()` from `thread_resolution_validity.py`. Fix `prompt_context.py` to use `prev_snap` for all state fields.
5. **Progressive SSE panel updates** — Add `panel_update` SSE events after each extraction phase. Frontend renders panels from JSON.

## Phases

### Phase 1: Dead code removal

**Files:** `ccya/engine/config.py`, `ccya/engine/__init__.py`, `ccya/engine/turn.py`, `ccya/state/io.py`

**Dependencies:** None

#### Step 1.1 — Remove `register_persist` from config.py

**File:** `ccya/engine/config.py`

**What:**
- Remove line 36: `_persist_started: dict[str, bool] = {}`
- Remove lines 55-56: `register_persist` function
- Remove line 83: `_persist_started.pop(save_dir, None)` from `clear_all_turn_locks()`

**Why:** `register_persist` was used to prevent double-revert in the old cancel path. With no revert needed, it is dead code.

**Validation:** No references to `register_persist` or `_persist_started` remain in the codebase.

#### Step 1.2 — Remove `register_persist` from engine/__init__.py

**File:** `ccya/engine/__init__.py`

**What:**
- Remove line 9: `register_persist` from the import
- Remove line 28: `register_persist` from `__all__`

**Why:** Symbol no longer exists in config.py.

**Validation:** `make check` passes. No import errors.

#### Step 1.3 — Remove `register_persist` import and call from turn.py

**File:** `ccya/engine/turn.py`

**What:**
- Remove `register_persist` from the import at line 15
- Remove line 436: `register_persist(str(save_dir))`

**Why:** Symbol no longer exported. No longer needed in the turn pipeline.

**Validation:** `make check` passes.

#### Step 1.4 — Remove orphaned `state_snapshot.yaml` cleanup

**File:** `ccya/state/io.py`

**What:** Remove line 136: `(save_dir / "state_snapshot.yaml").unlink(missing_ok=True)`

**Why:** No file is ever written by that name anymore. The cleanup is orphaned.

**Validation:** No references to `state_snapshot.yaml` remain in the codebase.

---

### Phase 2: Deferred atomic write block

**Files:** `ccya/engine/turn.py`

**Dependencies:** Phase 1 (register_persist removed)

#### Step 2.1 — Consolidate save_state calls into single write block

**File:** `ccya/engine/turn.py`

**What:** Restructure the post-extraction section (lines 435-505) into a single deferred write block:

**Before (current):**
```python
# Line 435-438
register_persist(str(save_dir))
save_state(save_dir, state)
event["state_snapshot"] = load_state(save_dir)
append_event(save_dir, event)

# ... chronicle and prompts writes (lines 478-481) ...

# Line 483-492: prior_history
if outcome_summary and outcome_summary.strip():
    ...
    save_state(save_dir, state)

# Line 494-505: sanitizer
if config.sanitize_every > 0:
    ...
    save_state(save_dir, state)
```

**After (new):**
```python
# Single deferred write block after all phases (sanitizer included)
# Lines 435-438: Build event dict (unchanged up to line 434)
# Line 435: Remove register_persist call (done in Phase 1)
# Line 436: Remove save_state (moved to deferred block)
# Line 437: Rename field and use in-memory state (no load_state call needed)
event["last_turn_state"] = state  # in-memory dict, includes prior_history + sanitizer
append_event(save_dir, event)

# Write stripped prompts to prompts.jsonl (lines 441-476, unchanged)
append_prompts(save_dir, prompts_list)

# Chronicle entry (lines 478-481, unchanged)
append_chronicle(save_dir, ...)

# Deferred: prior_history + sanitizer + final save_state
# These now happen in-memory before the single save_state call
if outcome_summary and outcome_summary.strip():
    turn_no = state["meta"]["turn"]
    bullet = f"- [T{turn_no}] {outcome_summary}"
    meta = state.setdefault("meta", {})
    prior = meta.setdefault("prior_history", [])
    prior.append(bullet)
    if len(prior) > 20:
        meta["prior_history"] = prior[-20:]

# Thread sanitizer (after prior_history, before yield complete)
if config.sanitize_every > 0:
    t_sanitize = asyncio.get_running_loop().time()
    state, sanitize_ran = await sanitize_threads(
        save_dir, state, config, trace_id=trace_id,
    )
    if sanitize_ran:
        yield ("phase", {"phase": "sanitize_start", "expected_ms": 0})
        yield ("phase", {"phase": "sanitize_done", "ms": round(
            (asyncio.get_running_loop().time() - t_sanitize) * 1000, 1
        )})

# Single atomic write block
save_state(save_dir, state)
```

**Key changes:**
1. `event["state_snapshot"] = load_state(save_dir)` → `event["last_turn_state"] = state` (in-memory dict, no disk read)
2. Remove `save_state(save_dir, state)` at line 437 (the first of 3 saves)
3. Move prior_history computation (lines 484-492) to before sanitizer — it now modifies in-memory state only
4. Move sanitizer (lines 494-505) to same position — it now modifies in-memory state only
5. Single `save_state(save_dir, state)` at the end of the block (after sanitizer)
6. The event dict now captures `last_turn_state` BEFORE prior_history/sanitizer are applied to the in-memory state — this is the state at the point where the event was built (post-extraction, pre-prior_history, pre-sanitizer). **Wait:** The design says `last_turn_state` should include prior_history and sanitizer. Let me re-read the design.

Actually, re-reading the design doc:
> `event["last_turn_state"] = state` (the in-memory dict, no `load_state` call needed)
> The single write block includes sanitizer changes.

So `last_turn_state` should be the full post-turn state including prior_history and sanitizer. The event dict is built before prior_history/sanitizer, so we need to capture `last_turn_state` AFTER those modifications.

**Corrected order:**
```python
# Build event dict (lines 390-434, unchanged)
event = { ... }

# Write event (without last_turn_state yet — it will be added after all modifications)
append_event(save_dir, event)

# Write prompts (lines 441-476, unchanged)
append_prompts(save_dir, prompts_list)

# Chronicle entry (lines 478-481, unchanged)
append_chronicle(save_dir, ...)

# Apply prior_history to in-memory state
if outcome_summary and outcome_summary.strip():
    ...

# Run sanitizer (modifies in-memory state)
if config.sanitize_every > 0:
    ...

# Now capture full post-turn state and save
event["last_turn_state"] = state
save_state(save_dir, state)
```

**Why:** `last_turn_state` must reflect the complete post-turn state (including prior_history and sanitizer) so that cancel/delete/revert operations have the correct reference point.

**Validation:** `make check` passes. The three `save_state()` calls are consolidated into one. `event["last_turn_state"]` is set from the in-memory dict.

#### Step 2.2 — Verify cancel signal checks still work

**File:** `ccya/engine/turn.py`

**What:** Verify that cancel signal checks at yield points (lines 360-362) still correctly abort before the write block. The `is_cancel_requested()` check at line 360 happens before the event is built, so cancel mid-turn discards everything.

**Why:** No behavioral change to cancel — cancel still aborts the turn. The cancel endpoint simplification is in Phase 3.

**Validation:** No new cancel signal checks needed. Existing checks at lines 214-215, 220-221, 255-256, 281-282, 360-361 remain.

---

### Phase 3: Simplify cancel endpoint

**Files:** `ccya/server/routes.py`

**Dependencies:** Phase 2 (last_turn_state field exists)

#### Step 3.1 — Simplify cancel_turn()

**File:** `ccya/server/routes.py` lines 394-425

**What:** Replace the current cancel logic with:
```python
@app.post("/turn/cancel")
async def cancel_turn():
    if err := _require_save():
        return err
    if not is_turn_in_progress(str(_app_mod.SAVE_DIR)):
        return JSONResponse({"ok": True})

    request_cancel(str(_app_mod.SAVE_DIR))
    released = await await_turn_done(str(_app_mod.SAVE_DIR), timeout=30.0)
    if not released:
        _log.warning("cancel_turn timeout waiting for turn to finish")
    clear_cancel(str(_app_mod.SAVE_DIR))

    return JSONResponse({"ok": True, "cancelled": True})
```

Remove:
- Lines 401-402: `last_events_before` loading
- Lines 410-423: `last_events_after` loading, state_snapshot revert logic, `remove_last_event`, `remove_last_chronicle_turn`

**Why:** With deferred atomic write, no files were written during the in-flight turn. Cancel is O(1) — just return a flag. Lazy cleanup of canceled events happens on next turn start (deferred to a future plan if needed; stale events are benign).

**Validation:** `make check` passes. The cancel endpoint returns `{"ok": true, "cancelled": true}`.

#### Step 3.2 — Update delete_last_turn() field reference

**File:** `ccya/server/routes.py`

**What:**
- Line 445: `last_event.get("state_snapshot")` → `last_event.get("last_turn_state")`
- Line 454: Log message `"delete_last_turn state_snapshot missing"` → `"delete_last_turn last_turn_state missing"`

**Why:** Field renamed. Delete still removes the last turn's event/chronicle and reverts to `last_turn_state`.

**Validation:** `make check` passes.

---

### Phase 4: EV tooling migration

**Files:** ~15 files across `ccya/ev/`

**Dependencies:** Phase 2 (last_turn_state field exists in events)

#### Step 4.1 — Rename `state_snapshot` → `last_turn_state` across all EV checkers

**Files:** All checker files in `ccya/ev/checkers/` that reference `state_snapshot`:

| File | Lines/References |
|---|---|
| `conditions.py` | Line 19: `extract_field(ev, "state_snapshot")` |
| `llm_checkers.py` | Lines 120, 131-132: `requires_fields` and `extract_field` |
| `inventory.py` | Lines 45, 48, 81, 93: `extract_field` calls |
| `state.py` | Lines 20, 30-31, 72, 82-83: `requires_fields` and `extract_field` |
| `gm_beat.py` | Lines 18, 29-30: `requires_fields` and `extract_field` |
| `arc_resolution_validity.py` | Line 14: `requires_fields` |
| `arc_goals.py` | Lines 14, 34-35, 38: `requires_fields` and comments + `extract_field` |
| `new_thread_validity.py` | Lines 14, 48: `requires_fields` and `extract_field` |
| `threads.py` | Lines 18, 27-29, 32-33, 40-41, 58, 60, 65: `requires_fields`, comments, `extract_field` |
| `goal_update_validity.py` | Lines 14, 23-25, 29-30, 55: `requires_fields`, comments, `extract_field` |
| `npc_presence.py` | Line 25: `extract_field` |
| `compendium_lifecycle.py` | Line 14: `requires_fields`; Line 28: `extract_field` |
| `thread_resolution_validity.py` | Lines 15, 17, 94, 105-106, 111-112: docstrings, `requires_fields`, comments, direct access |
| `sanitizer.py` | Lines 35-36: direct access `ev["state_snapshot"]` |

**What:** Mechanical find-and-replace: `state_snapshot` → `last_turn_state` in all references (field names, `requires_fields` strings, comments, docstrings).

**Why:** The field is renamed. Keeping both names would cause confusion.

**Validation:** `make check` passes. No remaining references to `state_snapshot` in EV tooling.

#### Step 4.2 — Rename in `prompt_context.py`

**File:** `ccya/ev/prompt_context.py`

**What:**
- Line 82: Comment `state_snapshot` → `last_turn_state`
- Line 96: Comment `state_snapshot` → `last_turn_state`
- Line 98: `prev_ev.get("state_snapshot")` → `prev_ev.get("last_turn_state")`
- Line 101: `turn_ev.get("state_snapshot")` → `turn_ev.get("last_turn_state")`
- All subsequent `state_snapshot` variable references → `last_turn_state`

**Critical logic change:** Extend `prev_snap` usage to cover all state fields except turn-specific metadata. Currently `prev_snap` is only used for `pending_beat` and `recent_beats` in storytell (lines 171-173) and narrate (line 250). The fix should extend `prev_snap` usage to: `arc`, `inventory`, `conditions`, `location`, `compendium`, `pc` across all 5 stream branches.

**Implementation per stream:**

**scene stream (lines 105-116):**
- `pc` → `prev_snap.get("pc") or {}`
- `compendium` → `prev_snap.get("compendium", {}).get("npcs", {})`
- `location` → `prev_snap.get("location") or {}`
- Keep `narration` from `turn_ev` (narration is turn N's own)
- Keep `turn_no` from parameter

**storytell stream (lines 118-182):**
- `arc` → `prev_snap.get("arc") or {}`
- `scene` → `prev_snap.get("scene") or {}`
- `meta` → `prev_snap.get("meta") or {}`
- `pc` → `prev_snap.get("pc") or {}`
- `compendium` → `prev_snap.get("compendium", {}).get("npcs", {})`
- `location` → `prev_snap.get("location") or {}`
- `inventory` → `prev_snap.get("inventory") or []`
- `conditions` → `list(pc.get("conditions") or [])` (pc from prev_snap)
- Keep `narration` from `turn_ev`
- Keep `intent` from `turn_ev`
- Keep `pacing_context` from `turn_ev`
- Keep `band` from `turn_ev` (turn-specific metadata)
- Keep `scene_phase` from `scene` (scene from prev_snap — scene_phase is set during ruling which is turn N)
  - **Wait:** `scene_phase` is set during ruling (turn N), so it should come from `turn_ev`, not `prev_snap`. Let me check.
  - Actually, the design says: "Use `turn_ev` only for turn-specific metadata set during turn N itself (band from ruling outcome, scene_phase from pacing_context, curtain_call from scene phase logic, allowed_beat_types from pacing)."
  - So `scene_phase` should come from `turn_ev.get("pacing_context", {}).get("scene_phase", "SETUP")` or from the pacing_context in turn_ev.
  - But `scene` dict also contains `world_state`, `climax_turn_count`, etc. which are turn N-1's values. The `scene_phase` is the one turn-specific value.
  - **Implementation:** Use `prev_snap.get("scene", {})` for `world_state`, `climax_turn_count`, etc. Use `turn_ev.get("pacing_context", {}).get("scene_phase", "SETUP")` for `scene_phase`.
- Keep `allowed_beat_types` from `turn_ev` (turn-specific metadata)
- Keep `curtain_call` computed from `scene_phase` (which now comes from turn_ev)
- Keep `recent_turns` from events (not from state)
- Keep `prior_history` from `meta` (meta from prev_snap — but the design says to use `[:-1]` to exclude current turn's bullet)
  - Actually, `prior_history` in prev_snap already excludes the current turn's bullet (it was appended after the snapshot). So `list(prev_meta.get("prior_history") or [])` is correct.
- `state` → `last_turn_state` (the full post-turn state from turn_ev)

**Wait, I need to reconsider.** The `state` field at the end of the storytell return is `state_snapshot` (now `last_turn_state`). This is the full state dict. For prompt_context, the `state` field is passed to the prompt template. The design says:

> Turn N's prompt should be built from turn N-1's `last_turn_state` for all state fields; turn-specific metadata (band, scene_phase, curtain_call, allowed_beat_types) comes from turn N's event.

So `state` in the return dict should be `prev_snap` (turn N-1's full state), not `last_turn_state` (turn N's full state).

**Corrected storytell stream:**
- `state` → `prev_snap` (full turn N-1 state)
- All individual fields from `prev_snap` as described above
- Turn-specific metadata from `turn_ev`

**ruling stream (lines 184-204):**
- `compendium` → `prev_snap.get("compendium", {}).get("npcs", {})`
- `arc` → `prev_snap.get("arc") or {}`
- `pc` → `prev_snap.get("pc") or {}`
- `location` → `prev_snap.get("location") or {}`
- `inventory` → `prev_snap.get("inventory") or []`
- `scene_phase` → `prev_snap.get("scene", {}).get("scene_phase", "SETUP")`
  - **Wait:** scene_phase is turn-specific. But ruling is the FIRST phase of turn N. At ruling time, scene_phase hasn't been updated yet for turn N. So prev_snap's scene_phase IS the correct value (it's turn N-1's scene_phase, which is what ruling sees).
  - Actually, ruling happens at the START of turn N. The ruling prompt should see the state as it was at the end of turn N-1. So prev_snap is correct for ALL fields in ruling.
- `state` → `prev_snap`

**narrate stream (lines 206-265):**
- `compendium` → `prev_snap.get("compendium", {}).get("npcs", {})`
- `arc` → `prev_snap.get("arc") or {}`
- `scene` → `prev_snap.get("scene") or {}`
- `meta` → `prev_snap.get("meta") or {}`
- `pc` → `prev_snap.get("pc") or {}`
- `location` → `prev_snap.get("location") or {}`
- `inventory` → `prev_snap.get("inventory") or []`
- `conditions` → `list(pc.get("conditions") or [])` (pc from prev_snap)
- `scene_phase` → `prev_snap.get("scene", {}).get("scene_phase", "SETUP")`
  - Narrate happens right after ruling. At this point, scene_phase may have been updated by ruling. But the prompt_context is for RE-RENDERING the narrate prompt, which was built using turn N-1's state. So prev_snap is correct.
- `state` → `prev_snap`
- Keep `rules_outcome` from `turn_ev` (ruling outcome is turn N's)
- Keep `pacing_context` from `turn_ev` (turn N's pacing)

**state stream (lines 267-278):**
- `pc` → `prev_snap.get("pc") or {}`
- `conditions` → `list(pc.get("conditions") or [])` (pc from prev_snap)
- `inventory` → `prev_snap.get("inventory") or []`
- `location` → `prev_snap.get("location") or {}`
- `state` → `prev_snap`
- Keep `narration` from `turn_ev` (narration is turn N's)
- Keep `intent` from `turn_ev` (turn-specific)

**Validation:** `make check` passes. Prompt rendering for turn N uses turn N-1's state for all state fields.

#### Step 4.3 — Rename in `events.py`, `audit.py`, `state_tools.py`

**Files:**
- `ccya/ev/events.py` — Lines 389, 409-410: `state_snapshot` → `last_turn_state`
- `ccya/ev/audit.py` — Lines 24, 32: `state_snapshot` → `last_turn_state`
- `ccya/ev/state_tools.py` — Lines 187, 200-201, 362-363, 435, 438, 543-544, 621: `state_snapshot` → `last_turn_state`

**What:** Mechanical find-and-replace.

**Why:** Consistency.

**Validation:** `make check` passes.

#### Step 4.4 — Remove `_apply_sanitizer_changes_to_arc()` from `thread_resolution_validity.py`

**File:** `ccya/ev/checkers/thread_resolution_validity.py`

**What:**
- Remove lines 12-89: `_apply_sanitizer_changes_to_arc()` function entirely
- Line 94: `requires_fields=["extraction.storytell", "state_snapshot"]` → `requires_fields=["extraction.storytell", "last_turn_state"]`
- Line 96: Remove `needs_non_turn_events=True`
- Lines 102: Remove `prev_sanitizer: dict[str, Any] | None = None`
- Lines 113-114: Remove sanitizer event tracking (`if ev.get("kind") == "sanitizer": prev_sanitizer = ev`)
- Line 125: Remove `snap = _apply_sanitizer_changes_to_arc(snap, prev_sanitizer_for_this)` — use `snap` directly (it already includes sanitizer via `last_turn_state`)

**Logic change:** The checker now reads `last_turn_state` directly for thread existence validation. No sanitizer reconstruction needed.

**Updated flow:**
```python
for ev in events:
    prev_snap_for_this = prev_snap
    if ev.get("kind") is None and "last_turn_state" in ev:
        prev_snap = ev["last_turn_state"]

    # prev_snap_for_this now already includes sanitizer (it's last_turn_state)
    snap = prev_snap_for_this or {}
    arc = snap.get("arc") or {}
    # ... rest unchanged
```

**Validation:** `make check` passes. The checker reads `last_turn_state` directly.

---

### Phase 5: Progressive SSE panel updates

**Files:** `ccya/engine/turn.py`, `ccya/engine/extraction/pipeline.py`, `ccya/server/routes.py`, `ccya/templates/index.html`

**Dependencies:** Phase 2 (deferred write block in place)

#### Step 5.1 — Add `panel_update` yields after extraction phases in pipeline.py

**File:** `ccya/engine/extraction/pipeline.py`

**What:** After each extraction stream completes (scene, state, storytell), yield a `panel_update` event with the relevant panel data from the in-memory `state` dict.

**After scene stream (line 108, after `yield ("phase", {"phase": "extract_stream_done", "stream": "scene"})`):**
```python
yield ("panel_update", {
    "panel": "scene",
    "data": {
        "npcs": state.get("compendium", {}).get("npcs", {}),
        "location": state.get("location"),
    },
})
```

**After state stream (line 152, after `yield ("phase", {"phase": "extract_stream_done", "stream": "state"})`):**
```python
yield ("panel_update", {
    "panel": "state",
    "data": {
        "pc": state.get("pc"),
        "inventory": state.get("inventory"),
        "conditions": state.get("pc", {}).get("conditions"),
    },
})
```

**After storytell stream (line 275, after `yield ("phase", {"phase": "extract_stream_done", "stream": "storytell"})`):**
```python
yield ("panel_update", {
    "panel": "arc",
    "data": {
        "arc": state.get("arc"),
        "scene": state.get("scene"),
        "meta": state.get("meta"),
    },
})
```

**Why:** The frontend needs structured panel data to update UI panels immediately after each extraction phase completes.

**Validation:** `make check` passes. The pipeline yields `("panel_update", {...})` events in addition to existing `("phase", {...})` and `("token", chunk)` events.

#### Step 5.2 — Pass panel_update events through turn.py

**File:** `ccya/engine/turn.py`

**What:** The `_run_extraction_pipeline` generator already yields all events through `yield _evt` at line 257. No changes needed — `panel_update` events flow through automatically.

**Validation:** No changes. Existing passthrough handles new event type.

#### Step 5.3 — Handle `panel_update` SSE events in routes.py

**File:** `ccya/server/routes.py` lines 307-391

**What:** Add a handler for `kind == "panel_update"` in the SSE event stream:
```python
elif kind == "panel_update":
    yield {
        "event": "panel_update",
        "data": json.dumps(payload),
    }
```

**Why:** The frontend needs to receive `panel_update` SSE events.

**Validation:** `make check` passes. The SSE stream now handles three event types: `token`, `phase`, `complete`, and `panel_update`.

#### Step 5.4 — Add `panel_update` SSE handler in frontend

**File:** `ccya/templates/index.html`

**What:** Add a `panel_update` event listener in the EventSource handler alongside existing `narrative_token`, `phase`, and `turn_complete` handlers. The listener should:
1. Parse the JSON payload
2. Identify the panel type (`scene`, `state`, `arc`)
3. Update the corresponding Alpine.js component/data
4. Trigger a re-render of the panel

**Implementation approach:** Use Alpine.js `$dispatch` or direct data mutation to update the panel data, then let Alpine's reactivity handle the DOM update. The panel rendering logic should match the current Jinja2 templates.

**Why:** Progressive UI updates — panels refresh immediately after each extraction phase rather than waiting for the full turn to complete.

**Validation:** Manual testing. Panels update after each extraction phase. Narrative streaming continues uninterrupted.

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `prompt_context.py` logic change produces wrong prompts | Regression test: render turn N's prompt before and after, diff the output |
| Frontend panel rendering accuracy vs Jinja2 templates | Extract rendering logic into reusable functions for comparison during review |
| `events.jsonl` and `chronicle.md` are append-only — true atomicity not possible | Write to temp files then `os.replace` in sequence. Crash gap between two `os.replace` calls is astronomically rare. |
| Delete reverts to post-sanitizer state (behavioral change) | Document this change. Post-sanitizer state is more correct. |

## Documentation updates required

- `docs/architecture/persist.md` — Update state_snapshot → last_turn_state, update cancel/delete flow diagrams
- `docs/architecture/OVERVIEW.md` — Update state_snapshot references
- `docs/architecture/prompts-architecture.md` — Update build_prompt_context description
- `docs/architecture/narration-ui.md` — Update cancel/delete endpoint descriptions
- `docs/ev/STATE-REFERENCE.md` — Update state_snapshot → last_turn_state
- `docs/ev/COMMANDS.md` — Update .state_snapshot references
- `docs/ev/RUBRIC.md` — Update state_snapshot references
- `docs/ev/CHECKERS.md` — Update state_snapshot references
- `docs/repomap.md` — Update state_snapshot references
