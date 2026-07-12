# Plan: Arc/Thread Overhaul — Phase 2: Engine

## Purpose

Update `ccya/engine/turn.py` to wire in the new model shapes: always-append progress in `_apply_thread_updates`, `goal_update` in the arc director sequence, auto-close arc-scoped threads on `arc_resolve`, and same-turn conflict detection.

## Problem Statement

`_apply_thread_updates` replaces `thread.progress` entirely on every update, losing past entries. The arc director has no `goal_update` path — the only way to update `visible_goal` is through `arc_resolve`, which never fires. `_apply_arc_resolve` carries arc-scoped threads forward into the successor arc, creating unbounded prompt growth. The LLM occasionally emits both `thread_resolve` and `thread_update` for the same thread id in a single turn, producing contradictory state with no warning.

## Constraints

- Pipeline order is fixed: narrate → extraction → arc director. `goal_update` applies between thread updates and arc resolve.
- `_merge_arc_update` always replaces `threads[]` unconditionally — `goal_update` must apply via direct dict assignment, NOT through `_merge_arc_update`.
- Phase 1 (models) must be complete before this phase starts.
- `delta.arc_update` is built correctly — the executor must preserve the delta wiring.

## Non-goals

- No model shape changes (Phase 1).
- No prompt template changes (Phase 3).
- No changes to the pacing gate, beat_locked, or floor relief mechanisms.

## Solution

1. Rewrite `_apply_thread_updates` progress handling to always append to `list[str]` and set `last_updated_turn`. 2. Insert `goal_update` application into the arc director sequence between thread updates and arc resolve. 3. Rewrite `_apply_arc_resolve` to auto-resolve all arc-scoped threads (state `"superseded"`) and carry scene-scoped threads forward to the successor arc. 4. Add a warning-level log when both `thread_update` and `thread_resolve` reference the same thread id in a single turn.

## Firm decisions

1. `goal_update` is applied directly to `state["arc"]["visible_goal"]` — NOT through `_merge_arc_update`.
2. `goal_update` applies before `arc_resolve`. If both fire on the same turn, `arc_resolve` wins.
3. Arc-scoped threads auto-resolve with state `"superseded"` on arc end. Scene-scoped threads carry forward to the successor arc.
4. Successor arc starts with scene-scoped threads from the old arc (minus any in `resolution.drop_threads`). Arc-scoped threads do NOT carry forward. The storyteller re-creates relevant arc-scoped threads via `thread_add` or `arc_resolve.new_threads`.
5. `progress` is always appended. No boolean, no kind enum. Set `last_updated_turn` to current turn on every mutation.

## Risks, Ambiguities, and Blockers

- `_apply_arc_resolve` previously carried all threads forward (opt-out via `drop_threads`). Now: arc-scoped threads auto-close, scene-scoped threads carry forward minus `drop_threads`. `drop_threads` is kept in `ArcResolution` model for scene-scoped thread filtering and LLM output parsing compat. The engine applies `drop_threads` to scene-scoped threads only before carry-over; arc-scoped thread IDs in `drop_threads` are logged as warnings (no-ops).
- `_apply_arc_resolve` currently stores `thematic_question` in `resolved_arc_entry`. This field is removed in Phase 1. The executor must remove the `resolved_arc_entry["thematic_question"]` line and not reference it in the new arc's construction.
- The `_apply_arc_resolve` function currently builds `resolved_arc_entry` with `goal_context` from `resolution.goal_context`. This is correct — `goal_context` is still valid (UI-only). Keep it.

## Status

`completed`

## Phases

Single phase. This changes only `ccya/engine/turn.py`.

## Implementation — Phase 2: Engine

### Context files to load

- `ccya/engine/turn.py` lines 139-208 (`_apply_thread_updates`)
- `ccya/engine/turn.py` lines 211-286 (`_apply_arc_resolve`)
- `ccya/engine/turn.py` lines 1142-1202 (arc director sequence + gate)
- `ccya/models.py` lines 29-48 (`ArcThread`, `CampaignArc`)
- `docs/design/arc-thread-system-design.md` sections "Core Changes" 1, 3, 8, 9

### Detailed steps

#### Step 2.1 — Rewrite progress handling in `_apply_thread_updates`

**File:** `ccya/engine/turn.py` lines 185-208 (`_apply_thread_updates`)

**What:** Change the progress update logic from single-string replacement to always-append. Specifically:

- In the `updates: dict[str, Any]` block (lines 185-193), remove the unconditional `updates["progress"] = update.progress` assignment.
- Replace with: when `update.progress` is not None, get the existing thread's progress list, append the new value, and assign the modified list to `updates["progress"]`. Use `thread.progress` which is now a `list`.
- After building `updates`, if any field changed, set `updates["last_updated_turn"] = turn_no`.

Pseudocode:
```
if update.progress is not None:
    current_progress = list(thread.progress)  # copy
    current_progress.append(update.progress)
    updates["progress"] = current_progress
```
And after the updates dict is finalized:
```
if updates:
    updates["last_updated_turn"] = turn_no
```

**Why:** Always-append preserves the investigative trail. `last_updated_turn` enables urgency decay visibility.

**Validation:** `make check` passes. No behavioral regression — existing tests (when restored) should pass.

#### Step 2.2 — Add `goal_update` apply to arc director sequence

**File:** `ccya/engine/turn.py` lines 1142-1163

**What:** Insert a `goal_update` block between `_apply_thread_updates` (lines 1144-1152) and `_apply_arc_resolve` (lines 1154-1163):

```
# Apply goal_update (mid-arc visible_goal change, separate from arc_resolve)
if storyteller_result.goal_update:
    state.setdefault("arc", {})["visible_goal"] = storyteller_result.goal_update
    _log.info(
        "goal_update trace_id=%d visible_goal='%s'",
        trace_id, storyteller_result.goal_update,
        extra={"trace_id": trace_id},
    )
```

Apply directly to `state["arc"]` dict — NOT through `_merge_arc_update`. This avoids the thread-list-wipe behavior.

**Why:** `_merge_arc_update` replaces `threads[]` unconditionally, which would clear the thread list. Direct dict assignment is correct and minimal.

**Validation:** `make check` passes. Log line visible in debug output when `goal_update` is set.

#### Step 2.3 — Rewrite `_apply_arc_resolve` for auto-close behavior

**File:** `ccya/engine/turn.py` lines 211-286

**What:** Rewrite the function body to:

1. Validate and parse the old arc (unchanged — lines 222-240).
2. Partition old arc threads into arc-scoped and scene-scoped:
   - Arc-scoped threads: move to `completed_threads[]` with `resolution_state="superseded"` and `resolved_turn=turn_no`. These do NOT carry forward.
   - Scene-scoped threads: keep in a `surviving_scene_threads` list. These carry forward to the successor arc, minus any IDs in `resolution.drop_threads`.
3. Apply `resolution.drop_threads` to `surviving_scene_threads`: remove any scene-scoped thread whose ID appears in the list. Log arc-scoped thread IDs in `drop_threads` as warnings (they're auto-closed already — no-op).
4. Store the resolved arc entry in `state["resolved_arcs"]` — remove `thematic_question` from the entry dict (field removed in Phase 1). Keep `visible_goal`, `resolution`, `goal_context`, `resolved_turn`.
5. Create the new arc with `CampaignArc(visible_goal=resolution.visible_goal, goal_context=resolution.goal_context, threads=surviving_scene_threads, completed_threads=[], last_thread_created_turn=turn_no)`.
6. Append `resolution.new_threads` to the new arc's `threads` (alongside survivors).
7. Log the resolution with thread counts (arc-closed, scene-dropped, new-threads).

**Why:** Arc-scoped threads auto-close on arc end (prevents unbounded prompt growth). Scene-scoped threads carry forward because they represent location/encounter-level dynamics independent of the campaign arc. `drop_threads` lets the storyteller clean up stale scene threads at arc boundaries without manual `thread_resolve` emissions.

**Validation:** `make check` passes. Log lines show thread count moving from active to completed on resolution.

#### Step 2.4 — Add same-turn conflict debug log warning

**File:** `ccya/engine/turn.py` — after `_apply_thread_updates` returns, before `_apply_thread_resolutions`

**What:** After the `_apply_thread_updates` call (line 1144), check for overlapping thread IDs between `storyteller_result.thread_update` and `storyteller_result.thread_resolve`:

```
update_ids = {u.id for u in (storyteller_result.thread_update or [])}
resolve_ids = {r.id for r in (storyteller_result.thread_resolve or [])}
conflict_ids = update_ids & resolve_ids
if conflict_ids:
    _log.warning(
        "thread_same_turn_conflict trace_id=%d ids=%s — thread_update and thread_resolve for same id",
        trace_id, sorted(conflict_ids), extra={"trace_id": trace_id},
    )
```

This runs before `_apply_thread_resolutions` (line 1166) to catch the conflict before resolution processes it. The processing order (updates → resolve) means resolution wins, which is correct — the log warning is for monitoring.

**Why:** Finding 2.7 confirmed the LLM emits contradictory thread instructions. A warning surfaces this for monitoring without changing pipeline behavior.

**Validation:** `make check` passes. Log line visible in debug output when conflict exists.

#### Step 2.5 — Remove `thematic_question` from `delta_builder.py`

**File:** `ccya/state/delta_builder.py` lines 57-58

**What:** Delete the two lines in `_merge_arc_update` that reference `au.thematic_question`. After Phase 1, `CampaignArc` no longer has this field — accessing it raises `AttributeError`.

Change from:
```python
if au.thematic_question:
    arc["thematic_question"] = au.thematic_question
```
To: (delete both lines)

**Why:** Phase 1 removes `thematic_question` from `CampaignArc`. Any code accessing it on a model instance will crash.

**Validation:** `make check` passes. `grep -rn "thematic_question" ccya/state/delta_builder.py` returns nothing.

#### Step 2.6 — Update narrate prompt thread context for new `ArcThread` shape

**File:** `ccya/engine/narrate.py` lines 57-67 (thread dict builder) and lines 73-91 (user_ctx)

**What:** Two changes:

1. Add `progress` and `last_updated_turn` to the thread dict builder (lines 57-67). Remove the dead `tags` field (not a model field). The current builder only includes `summary`, `urgency`, `tags`, `scope`, `id`, `active` — it misses fields the Phase 3 `_thread_list.j2` template needs.

Updated thread builder (replaces lines 57-67):
```python
            "threads": [
                {
                    "summary": t.get("summary", "") if isinstance(t, dict) else getattr(t, "summary", ""),
                    "urgency": t.get("urgency", "normal") if isinstance(t, dict) else getattr(t, "urgency", "normal"),
                    "scope": t.get("scope", "arc") if isinstance(t, dict) else getattr(t, "scope", "arc"),
                    "id": t.get("id", "") if isinstance(t, dict) else getattr(t, "id", ""),
                    "active": t.get("active", True) if isinstance(t, dict) else getattr(t, "active", True),
                    "progress": t.get("progress", []) if isinstance(t, dict) else (t.progress if hasattr(t, "progress") else []),
                    "last_updated_turn": t.get("last_updated_turn") if isinstance(t, dict) else getattr(t, "last_updated_turn", None),
                }
                for t in all_threads if not (isinstance(t, dict) and t.get("active") is False) or not hasattr(t, "active") or getattr(t, "active", True)
            ],
```

2. Add `turn_no` and `gate` to the user_ctx dict (after line 83):
```python
        "pacing_context": pacing_context,
        "turn_no": turn_no,
        "gate": pacing_context.gate if pacing_context else None,
```

**Why:** The Phase 3 `_thread_list.j2` template (included from `narrate_user.j2`) iterates `t.progress` as a list and accesses `t.last_updated_turn`. If these fields are not in the thread dict, Jinja2 will raise `UndefinedError` on iteration. The `gate` variable is needed for the gate-status header line. `turn_no` is needed for `turns_since_last_update` display.

**Validation:** `make check` passes. Server renders narrate prompt without Jinja2 errors. The `_thread_list.j2` section shows progress and `turns_since_last_update` correctly.

#### Step 2.7 — Add `gate` to storytell render context

**File:** `ccya/engine/extraction.py` lines 252-273 (storytell_user.j2 render context)

**What:** Add `gate` to the storytell context dict so `_thread_list.j2` can access it when included from `storytell_user.j2` (added in Phase 3 Step 3.14).

Change from:
```python
        "band": band,
```
To:
```python
        "band": band,
        "gate": pacing_context.gate if pacing_context else None,
```

Add after the `"band"` line, before the closing `}`.

**Why:** Phase 3 unifies thread rendering by switching `storytell_user.j2` to include `_thread_list.j2`. That template accesses `gate` for the gate-status header. Without this addition, Jinja2 will receive `Undefined` for `gate` in the storytell context.

**Validation:** `make check` passes. Server renders storytell prompt without Jinja2 errors.

### Tests to write or update

No test files exist in the current repo. Run `make check` for validation.
