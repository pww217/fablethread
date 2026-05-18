# Thread Resolve Wiring + ArcThread Resolution State (Phase 05 Completion)

## Status
`open`

## Phases

2 tasks: (1) add `resolution_state: str | None` field to ArcThread model, (2) wire ProgressExtractResult.thread_resolve processing into turn.py's delta application pipeline so resolved/failed/abandoned threads move from arc.threads[] to arc.completed_threads[].

## Issue (North Star)

After phases 01-06 implement unified ArcThread + PacingContext architecture, `ProgressExtractResult.thread_resolve` is never processed by the engine — Mismatch 3 from phase 05 design doc identified this gap: ProgressExtractResult has a `thread_resolve: list[ThreadResolution]` field but turn.py never processes it. This means resolved/failed/abandoned threads stay in arc.threads[] indefinitely instead of being moved to arc.completed_threads[]. Additionally, ArcThread lacks the `resolution_state` field (Decision D2 from phase 05) needed to preserve structured resolution metadata on completed threads for narrative context and eval rubrics.

## Solution (North Star)

1. Add `resolution_state: str | None = None` field to ArcThread model in models.py — optional, set when thread_resolve processes resolved/failed/abandoned threads from ProgressExtractResult. This preserves LLM-emitted structured state on the thread for narrative context and eval rubrics.

2. Wire thread_resolve processing into turn.py's delta application pipeline: after `_apply_thread_signals()` handles arc mutations (thread_advance), add a new block that processes `progress_result.thread_resolve` — when non-empty, find matching threads in `arc.threads[]`, set their resolution_state from ThreadResolution objects, move them to `arc.completed_threads[]`. This fills the gap left by phases 01-04 which defined ThreadResolution but never wired it into state mutation.

## Firm decisions
1. **Thread resolve processing location:** Add thread_resolve handling in turn.py alongside `_apply_thread_signals()`, NOT in apply_delta()/delta.py. ProgressExtractResult.thread_resolve is already consumed by the engine pipeline at the point where arc mutations happen; delta.py handles StateDelta merges which don't include progress-level operations (Decision D1 from phase 05).

2. **Resolution state preservation:** ArcThread gains `resolution_state: str | None` field set when thread_resolve processes resolved/failed/abandoned threads. This preserves LLM-emitted structured state on the thread for narrative context and eval rubrics. Do NOT create a separate completion record — completed_threads already holds resolved threads (Decision D2 from phase 05).

3. **ThreadResolution mapping:** ThreadResolution objects have `id: str` and `resolution_state: Literal["resolved", "failed", "abandoned"]`. When processing, find the matching ArcThread in arc.threads[] by id, set its resolution_state field, then move it to arc.completed_threads[]. If a thread ID from thread_resolve doesn't exist in arc.threads[], log a warning and skip (defensive — LLM may reference threads already expired/removed).

## Risks, Ambiguities, and Blockers
- **Risk:** Thread IDs from ProgressExtractResult.thread_resolve might not match existing ArcThread ids if there's drift between what the LLM extracted and current state. Must handle missing thread IDs gracefully (log warning + skip) rather than crashing.
- **Ambiguity:** Should completed_threads be deduplicated? If a thread already exists in both arc.threads[] AND completed_threads from a previous run, adding it again would create duplicates. Decision: check if thread id already exists in completed_threads before appending; if duplicate found, update the existing entry's resolution_state instead of creating a second copy.
- **Blocker:** None identified. This phase only touches models.py (add field) and turn.py (wire processing).

## Dependencies
Phases 01-06 must complete — ProgressExtractResult.thread_resolve and ThreadResolution model already exist from phases 01/04; Phase 05 Completion wires them into state mutation but does not change the model shapes. ArcThread.model_exists with unified shape is required for resolution_state field addition.

---

## Implementation Steps

### Step 05c.1 — Add resolution_state field to ArcThread model

**File:** `ccya/models.py` (ArcThread class, lines 52-66)

**What:** Add one new field to the ArcThread dataclass:
```python
resolution_state: str | None = None  # set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads for narrative context and eval rubrics
```
Place it after `promotes` (line 65) or at a logical position within the "Fields from old ArcThread" section. Update docstring if one exists to note this field is Python-managed when thread_resolve operations are applied.

**Why:** Decision D2 from phase 05 design: ThreadResolution.resolution_state must be preserved on the ArcThread object when it's moved to completed_threads[]. This enables eval rubrics and narrative context to know how a thread was resolved (resolved/failed/abandoned) without re-querying ProgressExtractResult.

**Validation:** Read models.py after changes to confirm: `resolution_state: str | None = None` exists on ArcThread class; field is optional with default None; no required positional argument added that would break existing code creating ArcThread objects. Run `python -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='test'); print(t.resolution_state)"` — verify defaults to None without error.

### Step 05c.2 — Wire thread_resolve processing into turn.py delta application pipeline

**File:** `ccya/engine/turn.py`

**What:** Add a new function `_apply_thread_resolutions()` and call it from the same location where `_apply_thread_signals()` is called (post-extraction, before compaction). The function:
1. Check if `progress_result.thread_resolve` is non-empty; return early if empty
2. Get arc from state via `[state.get("arc") or CampaignArc()]` 
3. For each ThreadResolution in progress_result.thread_resolve:
   a. Find matching ArcThread in `arc.threads[]` by id (use list comprehension/filter)
   b. If found: set thread.resolution_state = resolution_obj.resolution_state; remove from arc.threads[]; append to arc.completed_threads[] with updated resolution_state
   c. If not found: log warning "thread_resolve references unknown thread ID {tid}" and skip
4. Handle deduplication in completed_threads: if id already exists, update existing entry's resolution_state instead of creating duplicate

**Why:** This fills the gap identified by Mismatch 3 from phase 05 design doc — ProgressExtractResult.thread_resolve was defined but never wired into state mutation. The function mirrors `_apply_thread_signals()` pattern (reads arc from state, mutates it in-place) and processes thread_resolve at the correct pipeline location (after LLM extraction completes).

**Validation:** Read turn.py after changes to confirm: new `_apply_thread_resolutions()` function exists with clear logic; called alongside `_apply_thread_signals()` in delta application section; handles missing thread IDs gracefully (warning log + skip); deduplicates completed_threads entries. Check that no existing code path is broken by the addition.

### Step 05c.3 — Update compactor sanitization: handle resolution_state on completed threads

**File:** `ccya/engine/compactor.py`

**What:** Review `_apply_sanitization()` and any compaction logic that touches arc.threads[] or arc.completed_threads[]. Ensure completion thread handling preserves the new `resolution_state` field when compacting — if a resolved thread is kept in context during compaction, its resolution_state should be retained for narrative continuity.

Check if there's existing code that filters/moves completed threads and update it to handle the new field (likely no changes needed since adding an optional field doesn't break serialization).

**Why:** Compactor may strip or filter arc.completed_threads[] entries during history compression. If resolution_state is dropped, eval rubrics lose structured completion metadata. This step ensures compaction preserves the field for threads that remain in context.

**Validation:** Read compactor.py after changes to confirm: no data loss of resolution_state when completing/compacting resolved threads; if existing code filters completed_threads by id or scope, it doesn't accidentally drop the new field. Run `make check` to verify serialization still works correctly.

### Step 05c.4 — Update models.py comments referencing scene_pressure removal

**File:** `ccya/models.py`

**What:** Clean up stale migration comments:
- Line 73 (CampaignArc.threads): Remove trailing "age-based demotion (active: True → False) replaces the active/latent migration logic in design decisions implemented from plan document" — simplify to clean description of unified threads[] with scope-aware lifecycle rules
- Line 74 (CampaignArc.completed_threads): Replace `# scene_pressure removed from state.yaml schema, models.py StateDelta, apply_delta(), delta.py — migrated to arc.threads[] with scope: scene for backward compatibility during transition period` with cleaner comment noting resolution_state field added in Phase 05 Completion
- Line 312 (IntentEnvelope): Update `# scene_pressure_remove and scene_pressure_update REMOVED — now on ProgressExtractResult` if still relevant or remove entirely

**Why:** Stale migration comments create confusion about what's been completed. Clean documentation helps future developers understand the current state without having to cross-reference multiple phase plans.

**Validation:** Read models.py after changes to confirm: no outdated "transition period" language; comments accurately reflect current unified model state; resolution_state field presence noted where relevant.

### Step 05c.5 — Final validation: run make check after all changes

**What:** Run `make check && make typecheck` as the final gate for Phase 05 Completion (lint + typecheck). Fix any errors from new ArcThread.field or changed pipeline logic.

**Why:** Adding a field to ArcThread and wiring thread_resolve processing touches models.py, turn.py, compactor.py — multiple modules with different serialization expectations. A single validation run catches cross-module inconsistencies before Phase 07 begins.

---

## Tests to write or update

### Test: `test_thread_resolve_moves_to_completed`
**File:** `ccya/tests/test_turn.py` (new test function)  
**What:** Create a state with an ArcThread in arc.threads[], create a ThreadResolution for that thread's id, call `_apply_thread_resolutions()`. Assert the thread is removed from arc.threads[] and added to arc.completed_threads[]. Assert completion entry has resolution_state set correctly ("resolved"/"failed"/"abandoned").

### Test: `test_thread_resolve_missing_id_graceful`
**File:** `ccya/tests/test_turn.py` (new test function)  
**What:** Create a state with no matching thread for a ThreadResolution id. Call `_apply_thread_resolutions()`. Assert no crash; verify warning logged and arc unchanged.

### Test: `test_thread_resolve_dedup_completed_threads`
**File:** `ccya/tests/test_turn.py` (new test function)  
**What:** Create a state where a thread already exists in both arc.threads[] AND arc.completed_threads[]. Call `_apply_thread_resolutions()` for the duplicate id. Assert completed_threads has exactly one entry with updated resolution_state, not two copies.

### Test: `test_arcthread_resolution_state_default`
**File:** `ccya/tests/test_models.py` (new test function)  
**What:** Create ArcThread without specifying resolution_state. Assert it defaults to None. Verify serialization/deserialization round-trips correctly with optional field present but null.

---

## REPOMAP updates required

Update `docs/repomap.md` with the following changes:
- **ArcThread model section:** Note that Phase 05 Completion added `resolution_state: str | None` field for preserving structured completion metadata from ProgressExtractResult.thread_resolve operations.
- **Turn pipeline section:** Update delta application description to note thread_resolve processing alongside _apply_thread_signals() — resolved threads move from arc.threads[] to arc.completed_threads[].

(End of file)
