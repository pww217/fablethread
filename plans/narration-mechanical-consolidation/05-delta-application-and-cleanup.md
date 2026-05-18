# Delta Application and Cleanup

## Status
`open`

## Phases

1 phase: update `apply_delta()` and related state mutation logic to handle unified thread signals with scope-aware expiration rules, remove/consolidate `_expire_scene_pressures()` / `_purge_scene_pressures()` from pressure.py into a single lifecycle management function for unified arc.threads[], clean up remaining references to old split lists in compactor.py and other modules that touch threads or pressures.

## Issue (North Star)

After 03+04 change the LLM outputs (no more scene_pressure_add/remove/update, no beat_disposition), the state mutation layer still expects those fields in StateDelta. Additionally, `_apply_thread_signals()` handles split lists (active_threads vs latent_threads) with separate lifecycle rules — needs scope-aware expiration logic for unified arc.threads[] where scene-scoped threads expire on location change and arc-scoped ones persist across scenes. The compactor has a `CompressorSanitizationResult.pressure_remove` field that maps to the old scene_pressure concept, not the unified thread model.

## Solution (North Star)

State mutation layer converges with 01's unified schema: `apply_delta()` handles unified thread operations (`thread_advance`, `thread_resolve`, `thread_add`) instead of the old 6-field schema (scene_pressure_add/remove/update + advanced_threads/candidate_opportunity). `_expire_scene_pressures()` / `_purge_scene_pressures()` in pressure.py are deleted and replaced with a single `_manage_thread_lifecycle()` function that applies scope-aware rules: scene-scoped threads expire on location change; arc-scoped ones persist across scenes until resolved or aged out via age-based demotion rules. Age-based demotion (`active: True → False`) replaces the active/latent migration logic in `_apply_thread_signals()`. All compactor.py and other module references to `scene_pressure[]`, `active_threads[]`, or `latent_threads[]` are removed — all state access goes through unified `arc.threads[]`.

## Firm decisions
1. Scope-aware expiration rules are the single source of truth for thread lifecycle: scene-scoped threads expire on location change (matching old scene_pressure purge behavior); arc-scoped ones persist across scenes until resolved or aged out via age-based demotion rules (`active: True → False`). This replaces 3 separate functions with a unified entry point.
2. `_manage_thread_lifecycle()` replaces 3 separate functions (`_expire_scene_pressures()`, `_purge_scene_pressures()`, and the active/latent migration logic in `_apply_thread_signals()`) — a single entry point for all thread lifecycle management after Progress Extract outputs are applied, eliminating duplicate code paths that handled scene_pressure vs arc_threads differently.

## Non-goals
- Pacing computation (handled in 02)
- Prompt template changes (handled in 03+04)
- Model/schema definitions (handled in 01)

## Design Decisions Implemented From Plan Document
This phase implements the following decisions from `plans/narration-simplification-design.md`:
1. `_apply_thread_signals()` function remains but handles unified threads instead of the split lists — scope-aware expiration rules replace separate lifecycle management for active_threads[] vs latent_threads[], age-based demotion (active: True → False) replaces the active/latent migration logic
2. Remove scene_pressure[] from state.yaml schema, models.py StateDelta, apply_delta(), delta.py — migrated to arc.threads[] with scope: scene in 01's unified model
3. Migration Notes for State Files executed on load (from 01) ensures 05 never sees unmigrated format at runtime after 01 is applied

## Risks, Ambiguities, and Blockers
- **Ambiguity:** compactor.py has `CompressorSanitizationResult.pressure_remove` field — needs clarification on whether this maps to unified thread resolution or a separate purge mechanism. Default: pressure entries that are scene-scoped threads get handled by `_manage_thread_lifecycle()` location change expiry, not manual compaction removal. The compactor should not directly reference the old `scene_pressure[]` key after 01 migration runs on load.
- **Blocker:** Must verify no server routes or CLI commands directly read/write `scene_pressure[]` outside of engine/turn.py pipeline (e.g., a debug panel that shows pressure status). REPOMAP mentions `_debug_context()` in panels.py — needs checking for direct state access patterns that reference the old 3-list format. Delete tests for removed compactor fields rather than retrofitting them to work with unified thread operations.

## Dependencies
01: unified ArcThread shape + StateDelta schema must exist so apply_delta() can accept the new field names from 04's LLM outputs, and migration function runs on load before any turn pipeline code executes (so 05 never sees unmigrated format at runtime). 02: PacingContext inputs needed by scope-aware expiration rules (gate values influence whether scene-scoped threads get purged on location change). 03+04: LLM outputs have changed (no more scene_pressure operations, no beat_disposition) so the delta application logic needs to match what Progress actually emits after these phases.
