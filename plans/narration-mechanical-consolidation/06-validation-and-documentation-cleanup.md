# Validation and Documentation Cleanup

## Status
`open`

## Phases

1 phase: validate all 5 prior phases executed correctly, remove dead code (unused imports, orphaned functions, stale references to removed primitives), update ARCHITECTURE.md and docs/REPOMAP/, verify `make check && make test` passes end-to-end.

## Issue (North Star)

After 01-04 implement the new unified architecture in isolation, there will inevitably be residual dead code: orphaned imports of ScenePressure or IntentEnvelope.stakes in modules that weren't directly touched by earlier phases, stale references to scene_pressure[] in compactor.py or server panels that were missed during 05's cleanup, outdated docstrings on functions whose signatures changed (e.g., _apply_thread_signals now handles unified threads not split lists), and documentation that describes the old 3-list state shape instead of unified arc.threads[]. Without a final validation pass, these inconsistencies become technical debt that confuses implementers in future sessions.

## Solution (North Star)

A systematic sweep after all architectural changes are complete: verify every removed primitive from 01-04 has been fully purged from the codebase (no orphaned imports, no commented-out fallbacks, no stale references), update ARCHITECTATION.md to reflect unified ArcThread + PacingContext architecture instead of scattered pacing functions and split thread lists, refresh docs/REPOMAP.md with new module boundaries (PacingContext in turn.py or engine/, unified arc.threads[] state shape replacing 3-list format), confirm all tests pass end-to-end including the 01 migration function on a real save file that has scene_pressure[], active_threads[], and latent_threads[].

## Firm decisions
1. Delete dead code immediately — no commented-out fallbacks, no "legacy path" flags during transition. The 01 migration function handles state file conversion on load; after that the engine never sees unmigrated format at runtime. Any remaining references to scene_pressure[] or active_threads[] in production code are bugs that should be fixed and reported here rather than worked around.
2. `make check && make test` must pass as final gate — no partial acceptance of a broken state even if 01-05 individually passed their own validation steps.

## Non-goals
- Adding new features or functionality beyond what 01-04 implement
- Refactoring unrelated modules that happen to import changed types (only touch files directly affected by the narration simplification scope)
- Writing comprehensive integration tests for every edge case — focus on critical path: a turn runs end-to-end with unified ArcThread operations and PacingContext inputs

## Design Decisions Validated From Plan Document
This phase validates the following decisions from `plans/narration-simplification-design.md` were correctly implemented across 01-05:
1. Unified ArcThread replaces ScenePressure + arc thread split — verify no scene_pressure[] or active_threads/latent_threads references remain in production code after 01 migration runs on load
2. PacingContext consolidates all pacing signals — verify _compute_narration_directive(), _check_floor_relief(), and _compute_narrative_velocity() are deleted (not just renamed) from turn.py, replaced by single _compute_pacing_context() call in 02
3. Stakes removed from IntentEnvelope — verify no rules templates or progress prompts still reference stakes field after 01+03+04 implement the removal
4. Beat_disposition removed from ProgressExtractResult — verify Python inference logic exists (gm_beat presence + turn expiry) and no LLM outputs attempt to emit beat_disposition after 04 implements unified operations
5. Scope-aware expiration rules in _manage_thread_lifecycle replace 3 separate functions — verify scene-scoped threads expire on location change, arc-scoped ones persist across scenes until resolved or aged out via age-based demotion

## Risks, Ambiguities, and Blockers
- **Risk:** 01 migration function needs a real save file to validate against. Default: use an existing test fixture that has scene_pressure[], active_threads[], and latent_threads[] populated with realistic data (urgency levels, turn_added timestamps) to verify the 1:1 mapping produces correct unified ArcThread entries in state.arc.threads[].
- **Risk:** ARCHITECTURE.md may not exist at repo root — if it does, update it; if not, note that documentation gap for manual follow-up rather than creating a new file (AGENTS.md says "no proactive docs unless explicitly requested").
- **Blocker:** If `make check && make test` fails on the final pass, 05 must be revisited to identify which dead code or stale references were missed. Do not accept a failing state — block until clean.

## Dependencies
All phases (01 through 04) must complete successfully before this phase can begin. 05's cleanup of production code references is a prerequisite for 06's systematic sweep, since 05 may leave edge cases that 06 catches during the full-codebase scan.
