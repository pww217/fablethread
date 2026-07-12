# Plan Review: Beat Generation Split

## Summary

This plan splits Storytell (Step 2c) into three focused steps: Record (backward-looking scribe), World (async beat-candidate generation after turn completion), and Ruling (beat selection from candidates). The plan is technically sound and aligns with the design doc's intent.

**Verdict:** `approved`

## Fixes Applied

### Critical Fix: Step 4.4 — Corrected async generator lock behavior

**What was wrong:** The original plan incorrectly stated that `finally` runs immediately after `yield("complete")` resumes, which would release the lock before World runs. This contradicted the design doc's explicit statement that the lock stays held.

**Root cause:** Misunderstanding of Python async generator semantics. The `finally` block in an async generator runs when the generator is **exhausted** (all yields consumed), not after each `yield`. The SSE route's `async for` loop continues iterating after receiving `complete`, so the generator hasn't returned yet, and the lock stays held.

**What I changed:**
- Rewrote Step 4.4 to place World AFTER `yield("complete")` (matching the design doc's code snippet)
- Removed the incorrect "restructure try/finally" language
- Added detailed explanation of lock behavior: generator yields `complete`, route sends to UI, generator resumes and runs Sanitize+World, yields phase events, then returns → `StopAsyncIteration` → loop ends → `finally` releases lock
- Updated "Firm decisions" section to remove the incorrect claim about restructuring
- Updated Step 4.5 validation to reflect correct position (after `yield("complete")`)

**Design doc alignment:** The design doc (D5) explicitly states: "If World runs *inside* `run_turn`'s body after `yield ("complete")`, the lock is NOT released until `run_turn`'s generator fully returns (the `finally` at turn.py:568 only fires when the generator is closed/exhausted)." The plan now matches this.

### Critical Fix: Step 5.2b — Added missing routes.py stream key update

**What was wrong:** The plan didn't mention updating `routes.py:351` where `storytell_skipped = (streams.get("storytell") or {}).get("skipped", False)` references the old stream key. After renaming to `"record"`, this check would never trigger, breaking the "all extraction streams failed" error handling.

**What I changed:** Added Step 5.2b to update `routes.py:351` and `routes.py:353` to use `"record"` instead of `"storytell"`.

**Impact:** Without this fix, if all extraction streams fail, the UI would show a success state instead of an error message.

### Critical Fix: Step 4.8 — Initialize `scene_result` to prevent NameError

**What was wrong:** The plan's Step 4.4 passes `scene_result` to `_run_world_step` after `yield("complete")`. But `scene_result` is only defined if the extraction pipeline succeeds (line 268 unpack). If the pipeline throws, `scene_result` is undefined, causing a NameError.

**What I changed:** Updated Step 4.8 to initialize `scene_result = None` at line 230 alongside other variable initializations. Updated Step 4.3's `_run_world_step` signature to accept `scene_result: Any | None` and handle None gracefully (empty `candidate_npcs`).

**Impact:** Without this fix, an extraction pipeline failure would cause a NameError in the World step, preventing the turn from completing cleanly.

### Critical Fix: Step 4.4 — Wrap Sanitize in try/except

**What was wrong:** The plan wrapped World in try/except but not Sanitize. If `sanitize_threads` throws after `yield("complete")`, the outer except block would catch it and yield a second `("complete", ...)`, causing the UI to receive two `turn_complete` events.

**What I changed:** Added try/except wrapper around the Sanitize step in Step 4.4's code snippet.

**Impact:** Without this fix, a Sanitize failure would send duplicate `turn_complete` events to the UI.

### Minor Fix: Step 2.4 — Added missing metrics rollup updates

**What was wrong:** Step 2.4 didn't mention updating `turn.py` metrics rollup tuples that reference `"storytell"` as a stream key (lines 289, 293, 297, 312, 316, 457). Without this, metrics would silently report zeros for the record stream.

**What I changed:** Added item 8 to Step 2.4's "What" section, explicitly listing the lines to update and explaining the consequence of missing them.

### Minor Fix: Step 2.4 — Added extraction __init__.py docstring update

**What was wrong:** Step 2.4 didn't mention updating the docstring in `ccya/engine/extraction/__init__.py` which still says "storytell".

**What I changed:** Added item 9 to Step 2.4's "What" section.

### Minor Fix: Step 4.3 — Clarified candidate_npcs sourcing

**What was wrong:** Step 4.3 said "from `scene_result` (SceneExtractResult.candidate_npcs or equivalent from extraction_ctx)" which was ambiguous.

**What I changed:** Clarified that `candidate_npcs` comes from `scene_result.candidate_npcs` (the `SceneExtractResult` field, which is a `list[dict]` with max 3 entries).

### Minor Fix: Step 4.8 — Added missing call site

**What was wrong:** Step 4.8 didn't mention updating the `_apply_state_updates` call site at line 335.

**What I changed:** Added line 335 to the list of references to update, and clarified that `_apply_state_updates` in `turn_state.py` keeps its parameter name `storyteller_result` (it's a local parameter name, not a contract).

## Findings Requiring User Input

None. All issues were fixable without design decisions.

## Contract Checks

- [x] **Signature of `_record_messages` matches call sites** — pass. The signature in Step 2.3 matches the call site in Step 2.4.
- [x] **Signature of `_run_world_step` matches call sites** — pass. The signature in Step 4.3 (updated to accept `scene_result: Any | None`) matches the call site in Step 4.4.
- [x] **Signature of `_call_ruling` 5-tuple matches call sites** — pass. Only one call site at line 234, updated in Step 3.5.
- [x] **Signature of `_ruling_messages` matches call sites** — pass. Only one call site at line 214, updated in Step 3.3.
- [x] **Template variables all provided by render calls** — pass. Step 2.3 lists all context variables for Record templates. Step 4.3 lists all context variables for World templates. Step 3.3 adds `beat_candidates` to ruling.
- [x] **Schema keys match** — pass. `selected_beat` schema in Step 3.1 matches the extraction logic in Step 3.4. `beat_candidates` schema in Step 4.2 matches the validation in Step 4.3.
- [x] **Field names match access points** — pass. All `gm_beat`, `beat_expires_turn`, `pending_gm_beat`, `beat_candidates`, `recent_beats` references are consistent.
- [x] **Stream key consistency** — pass. All references to `"storytell"` stream key are updated to `"record"` in pipeline.py, turn.py, routes.py, and extraction/__init__.py.

## Scope Violations

None. The plan stays within the design doc's scope. EV-side cleanup is explicitly deferred per OQ9.

## Format Issues

None. The plan follows the required format:
- Correct section order: Purpose → Design Reference → Constraints → Non-goals → Solution → Firm decisions → Risks → Phase Summary → Phases → Implementation per phase
- Each phase has: Context files to load, Dependencies, Detailed steps (with File/What/Why/Validation)
- Steps use interface contracts (field names, types, signatures) rather than implementation bodies
- Each step is atomic and independently verifiable

## Documentation Assessment

The plan accounts for updating:
- [x] `docs/architecture/OVERVIEW.md` — Step 6.1
- [x] `docs/architecture/step2c-storytell.md` → `step2c-record.md` — Step 6.1
- [x] `docs/repomap.md` — Step 6.2
- [x] `AGENTS.md` — Step 6.3

All mandatory documentation updates are in scope.

## Conclusion

The plan is ready for execution. All critical issues have been fixed:
1. Async generator lock behavior corrected to match design doc
2. routes.py stream key update added
3. `scene_result` initialization added to prevent NameError
4. Sanitize wrapped in try/except to prevent duplicate `turn_complete` events

No blocks to execution remain.
