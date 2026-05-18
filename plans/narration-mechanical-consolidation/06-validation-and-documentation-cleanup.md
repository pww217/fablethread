# Validation and Documentation Cleanup

## Status
`open`

## Phases

1 phase: validate all 5 prior phases executed correctly, remove dead code (unused imports, orphaned functions, stale references to removed primitives), update ARCHITECTURE.md and docs/REPOMAP/, verify `make check && make test` passes end-to-end.

## Issue (North Star)

After 01-04 implement the new unified architecture in isolation, there will inevitably be residual dead code: orphaned imports of ScenePressure or IntentEnvelope.stakes in modules that weren't directly touched by earlier phases, stale references to scene_pressure[] in compactor.py or server panels that were missed during 05's cleanup, outdated docstrings on functions whose signatures changed (e.g., _apply_thread_signals now handles unified threads not split lists), and documentation that describes the old 3-list state shape instead of unified arc.threads[]. Without a final validation pass, these inconsistencies become technical debt that confuses implementers in future sessions.

## Solution (North Star)

A systematic sweep after all architectural changes are complete: verify every removed primitive from 01-04 has been fully purged from the codebase (no orphaned imports, no commented-out fallbacks, no stale references), update ARCHITECTURE.md to reflect unified ArcThread + PacingContext architecture instead of scattered pacing functions and split thread lists, refresh docs/REPOMAP.md with new module boundaries (PacingContext in turn.py or engine/, unified arc.threads[] state shape replacing 3-list format), confirm all tests pass end-to-end.

## Firm decisions
1. Delete dead code immediately — no commented-out fallbacks, no "legacy path" flags during transition. Any remaining references to scene_pressure[] or active_threads[] in production code are bugs that should be fixed and reported here rather than worked around.
2. `make check && make test` must pass as final gate — no partial acceptance of a broken state even if 01-05 individually passed their own validation steps.

## Non-goals
- Adding new features or functionality beyond what 01-04 implement
- Refactoring unrelated modules that happen to import changed types (only touch files directly affected by the narration simplification scope)
- Writing comprehensive integration tests for every edge case — focus on critical path: a turn runs end-to-end with unified ArcThread operations and PacingContext inputs

---

## Source Validation Summary

Validating each claim from "Design Decisions Validated" against actual code state. All 5 items show stale references because phases 01-05 have NOT been executed yet — phase 06 will run after they complete, at which point these references should be gone (or caught as bugs per firm decision #1).

### Item 1: Unified ArcThread replaces ScenePressure + arc thread split
**Status:** `[STALE REFERENCES FOUND]` — expected before phases execute. Will be clean post-05.

| File | Reference | Line(s) | Notes |
|------|-----------|---------|-------|
| `ccya/engine/pressure.py` | `state.scene["scene_pressure"]` | 23, 74 | Entire module to be deleted by phase 05 |
| `ccya/state/io.py` | `state.scene["scene_pressure"]` | (backward-compat read) | Legacy save file handling — kept for backward compat |
| `ccya/engine/turn.py` | `state.scene["scene_pressure"]` | 367, 426, 452, 545, 875 | To be replaced by arc.threads[] access post-05 |
| `ccya/engine/narrate.py` | `"active_threads"` key in context dict | 57 | Narrative context key — should rename to "threads" or similar for consistency |
| `ccya/engine/compactor.py` | `state.scene["scene_pressure"]` | 210, 303, 351 | To be replaced by arc.threads[] scope=scene access post-05 |

### Item 2: PacingContext consolidates all pacing signals
**Status:** `[PARTIAL — old functions still exist]`

| Symbol | Status | File | Line(s) | Notes |
|--------|--------|------|---------|-------|
| `_compute_pacing_context()` | EXISTS (new) | turn.py:449 | Replaces separate deescalate/narrative_velocity signals |
| `_compute_narration_directive()` | STILL EXISTS (dead code) | turn.py:365 | Called internally by _compute_pacing_context — should be deleted after consolidation completes |
| `_check_floor_relief()` | STILL EXISTS (dead code) | turn.py:1448 | Same as above |
| `_compute_narrative_velocity()` | STILL EXISTS (dead code) | turn.py:331 | Same as above |

**Note:** Phase 02 created _compute_pacing_context() but the old functions are still present and called from within it. After full consolidation, these three should be deleted entirely — phase 06 catches them if they survive post-consolidation.

### Item 3: Stakes removed from IntentEnvelope
**Status:** `[CLEAN in code]` — `IntentEnvelope.stakes` field already removed from models.py (line ~452). Only stale references remain in prompt templates and docs.

| File | Reference | Line(s) | Notes |
|------|-----------|---------|-------|
| `ccya/prompts/rules_system.j2` | `"stakes": ""` in output schema + instructions | 57, 67, 85 | Prompt template still references stakes field — needs cleanup |
| `ccya/prompts/SYSTEM_PROMPTING.md` | Description of IntentEnvelope.stakes | 107-109 | Documentation stale |

### Item 4: Beat_disposition removed from ProgressExtractResult
**Status:** `[STALE REFERENCES IN EVAL CODE]` — ProgressExtractResult still has `beat_disposition` field (or it was already cleaned up). Eval code references remain.

| File | Reference | Line(s) | Notes |
|------|-----------|---------|-------|
| `ccya/engine/turn.py` | Comment about beat_disposition removal | 1027 | Just a comment — fine to keep as historical note |
| `ccya/eval/universal_asserts.py` | `check_pending_gm_beat_disposition_respected()` function | 94-99, 820 | Test assertion code referencing removed field |
| `evals/scenarios/gm_beat_lifecycle.py` | Assertions about beat_disposition presence | 37, 40, 49 | Eval scenario tests — should be updated to reflect new approach |

### Item 5: Scope-aware expiration rules replace 3 separate functions
**Status:** `[NOT YET IMPLEMENTED]` — `_manage_thread_lifecycle()` does not exist yet. Old pressure functions still present in turn.py and pressure.py. Phase 05 must implement this consolidation before phase 06 can validate it.

| Symbol | Status | File | Line(s) |
|--------|--------|------|---------|
| `_expire_scene_pressures()` | EXISTS (old) | pressure.py:13, __init__.py:24/36 | To be deleted by phase 05+06 |
| `_purge_scene_pressures()` | EXISTS (old) | pressure.py:62 | To be deleted by phase 05+06 |
| `_manage_thread_lifecycle()` | DOES NOT EXIST YET | — | Phase 05 must create this |

---

## Decision Table

| # | Decision | What | Why |
|---|----------|------|-----|
| D1 | Stakes cleanup in prompt templates | Remove `stakes` field from rules_system.j2 output schema (line 67) and update instructions (lines 57, 85) | IntentEnvelope.stakes already removed from models.py; leaving it in prompts causes LLM confusion when the field is silently dropped by Pydantic validation |
| D2 | Narrative context key rename | Rename `"active_threads"` → `"threads"` in narrate.py:53-64 (current_arc_ctx dict) | The key name implies a split-list model; unified arc.threads[] already filters active threads via the `active` bool flag — renaming eliminates conceptual confusion for LLM consumers |
| D3 | Eval code cleanup scope | Update universal_asserts.py and gm_beat_lifecycle scenario to reflect beat_disposition removal from ProgressExtractResult | Test/assertion code must match current model shape; leaving stale references causes test failures when phases execute |
| D4 | Documentation update priority | ARCHITECTURE.md first (most outdated), then REPOMAP.md, then SYSTEM_PROMPTING.md | ARCHITECTURE.md has the most extensive stale references to old primitives and is the primary onboarding doc for future implementers |

---

## What Is Removed

| # | Symbol / Field | File(s) | Replaced By |
|---|----------------|---------|-------------|
| R1 | `_expire_scene_pressures()` re-export from engine/__init__.py | __init__.py:24, 36 | Deleted — function consolidated into _manage_thread_lifecycle() in turn.py (phase 05) |
| R2 | `pressure.py` module | ccya/engine/pressure.py | Entire file deleted by phase 05; all functionality moved to turn.py |
| R3 | Stakes field from rules_system.j2 output schema | prompts/rules_system.j2:67 | Removed — IntentEnvelope.stakes already removed from models.py |
| R4 | "active_threads" key in narrate.py narrative context | ccya/engine/narrate.py:53-64 | Renamed to "threads" (D2) — same data, clearer naming for unified model |

---

## What Is Unchanged

1. **StateDelta schema** — already updated by phase 01; no further changes needed
2. **ArcThread model shape** — already has scope/active/urgency fields from phases 01-05 (resolution_state added per plan 05 D2)
3. **PacingContext class** — exists in turn.py:449 with correct fields; no structural changes needed after consolidation completes
4. **CompactorSanitizationResult.pressure_remove field name** — kept as-is but semantics change to refer to arc.threads[] scope=scene (plan 05 D5)
5. **EngineConfig pressure-related constants** — renamed from scene_pressure_* to thread_urgency_* per plan 05 Q2 decision

---

## Risks, Ambiguities, and Blockers

- **Risk:** Phase 01's backward-compatible read logic needs a real save file to validate against. Default: use an existing test fixture that has scene_pressure[], active_threads[], and latent_threads[] populated with realistic data (urgency levels, turn_added timestamps) to verify the conversion produces correct unified ArcThread entries in state.arc.threads[].
- **Risk:** ARCHITECTURE.md may not exist at repo root — if it does, update it; if not, note that documentation gap for manual follow-up rather than creating a new file (AGENTS.md says "no proactive docs unless explicitly requested").
- **Blocker:** If `make check && make test` fails on the final pass, 05 must be revisited to identify which dead code or stale references were missed. Do not accept a failing state — block until clean.

## Dependencies

All phases (01 through 04) must complete successfully before this phase can begin. 05's cleanup of production code references is a prerequisite for 06's systematic sweep, since 05 may leave edge cases that 06 catches during the full-codebase scan.
