# Delta Application and Cleanup — Fleshed Design

## Status
`completed`

**Last validated against source:** 2026-05-17 (full grep/read audit)

---

## Source Validation Summary

The design doc makes several claims that do not match the current codebase state. These are **not errors in the design intent** — they indicate work needed beyond what the original doc described:

### MISMATCH 1: `scene_pressure[]` still actively read/written across multiple modules
- **Doc claim:** "Remove scene_pressure[] from state.yaml schema" and "05 never sees unmigrated format at runtime after 01 is applied."
- **Source reality:** `state.scene["scene_pressure"]` is read by: turn.py (lines 367, 426, 452, 545, 875), pressure.py (lines 23, 74), compactor.py (lines 210, 303, 351), narrate.py (line 91). The `_default_state()` no longer creates it, but old saved games retain it.
- **Impact:** Phase 05 must handle both the new unified `arc.threads[]` AND backward-compatible reads from legacy `state.scene["scene_pressure"]`. Old saved games may have legacy scene_pressure[] data; phase 05 code operates on unified threads and handles both formats at runtime if needed.

### MISMATCH 2: `_expire_scene_pressures()` and `_purge_scene_pressures()` still exist and are called
- **Doc claim:** These functions "are deleted."
- **Source reality:** Both exist in `pressure.py` (lines 13–95) and are imported/called from turn.py lines 30, 1054–1060. The NOTE comments say operations will be consolidated into unified thread operations in later phases — phase 05 IS that consolidation.
- **Impact:** Phase 05 must delete these functions AND remove their call sites from turn.py.

### MISMATCH 3: `thread_resolve` is NOT handled anywhere in the pipeline
- **Doc claim (implicit):** `apply_delta()` handles unified thread operations including `thread_advance`, `thread_resolve`, `thread_add`.
- **Source reality:** ProgressExtractResult has `thread_resolve: list[ThreadResolution]` but turn.py never processes this field. There is zero code that moves resolved threads from active/latent into completed_threads with their resolution_state applied. This is a gap in phases 01–04, not phase 05's fault — but phase 05 must implement it.
- **Impact:** Phase 05 must add thread_resolve processing to turn.py (the place where `_apply_thread_signals()` already handles arc mutations).

### MISMATCH 4: Compactor still reads/writes `state.scene["scene_pressure"]` directly
- **Doc claim:** "All compactor.py references to scene_pressure[] are removed — all state access goes through unified arc.threads[]."
- **Source reality:** compactor.py line 303 reads `pressures = list((state.get("scene") or {}).get("scene_pressure") or [])` and lines 349–352 write back to `scene["scene_pressure"]`. This is in `_apply_sanitization()`, called during compaction.
- **Impact:** Phase 05 must update the compactor's sanitization logic to operate on arc.threads[] with scope=scope="scene" instead of scene_pressure[].

### MISMATCH 5: `pressure_remove` field still exists and is used by eval infra
- **Source reality:** CompactorSanitizationResult.pressure_remove (models.py line 418) is coerced, checked in `_sanitization_nonempty()` (compactor.py line 239), serialized to events.jsonl (compactor.py line 140), and read by eval/universal_asserts.py (line 808). The compaction rubric references it.
- **Impact:** Phase 05 must decide: rename `pressure_remove` → something like `thread_resolve_compact`, or keep the field but change its semantics to operate on arc.threads[] with scope=scene.

---

## Phases

1 phase: update thread signal application in turn.py to handle all three unified operations (`thread_advance`, `thread_resolve`, `thread_add`) including processing ThreadResolution for resolved threads, delete `_expire_scene_pressures()` / `_purge_scene_pressures()` from pressure.py and remove their call sites from turn.py, consolidate into a single `_manage_thread_lifecycle()` function that applies scope-aware expiration rules (scene-scoped threads expire on location change; arc-scoped ones persist until resolved or aged out via age-based demotion), update compactor.py to operate on unified `arc.threads[]` instead of `state.scene["scene_pressure"]`, clean up remaining references to old split lists and pressure fields across all modules, rename EngineConfig scene_pressure_* constants to thread_urgency_* (or remove if unused after consolidation).

---

## Issue (North Star)

Old saved games may have legacy scene_pressure[] data but phase 05 code operates on unified threads; compaction and pressure handling are updated to use arc.threads[].

---

## Solution (North Star)

1. **Add thread_resolve processing** to turn.py: when ProgressExtractResult.thread_resolve is non-empty, move resolved/failed/abandoned threads from arc.threads[] to arc.completed_threads[], preserving their resolution_state on a new field or as metadata. This fills the gap left by phases 01–04 which defined ThreadResolution but never wired it into state mutation.

2. **Delete pressure.py functions:** Remove `_expire_scene_pressures()` and `_purge_scene_pressures()` from pressure.py (the entire file can be deleted if no other callers exist). Replace their functionality with a single `_manage_thread_lifecycle(state, delta, config)` function that:
   - Filters arc.threads[] for scope=scene threads → removes them when location_changed is True (replacing old _purge behavior)
   - Applies age-based urgency escalation to all threads based on EngineConfig thresholds (replacing old _expire behavior)
   - Handles active→latent demotion via `active: False` flag when arc-scoped threads go silent for N turns

3. **Update compactor sanitization:** In `_apply_sanitization()`, replace the pressure_remove block that reads/writes `state.scene["scene_pressure"]` with logic that filters `arc.threads[]` where scope=scene, removing entries whose IDs appear in CompactorSanitizationResult.pressure_remove (renamed to thread_resolve_compact or kept as-is but reinterpreted).


4. **Clean up all references:** Remove imports of pressure module from turn.py, remove scene_pressure reads from narrate context building (replace with arc.threads[] scope=scene filter), update eval/universal_asserts.py and server/tv.py to handle unified thread model instead of separate pressures list.

---

## Decision Table

| # | Decision | What | Why |
|---|----------|------|-----|
| D1 | Thread resolution processing location | Add `thread_resolve` handling in turn.py alongside `_apply_thread_signals()`, NOT in apply_delta()/delta.py | ProgressExtractResult thread_resolve is already consumed by the engine pipeline at the point where arc mutations happen; delta.py handles StateDelta merges which don't include progress-level operations |
| D2 | ThreadResolution resolution_state persistence | Add `resolution_state: str | None` field to ArcThread model (optional, set when resolved/failed/abandoned) | The LLM emits structured resolution state — it should be preserved on the thread for narrative context and eval rubrics. Do NOT create a separate completion record; completed_threads already holds resolved threads |
| D3 | Scope-aware expiration trigger | Scene-scoped threads expire when `state.location.id` changes from previous turn (same check as location_changed in current code) | Matches old _purge_scene_pressures(location_changed=True) behavior: leaving a location invalidates scene-local pressures/threads. Arc-scoped threads persist across locations |
| D4 | Age-based demotion threshold | Use existing `_EXPIRE_SILENT_TURNS` constant (5 turns) for arc-scoped thread active→latent demotion when not listed in thread_advance | Reuses current logic already present in _apply_thread_signals(); no new config needed. This IS the age-based demotion — "age" = silent turns without advancement |
| D5 | Compactor pressure_remove field name | Keep `pressure_remove` as-is on CompactorSanitizationResult but change its semantics: IDs refer to arc.threads[] with scope=scene, not scene_pressure[]. Update compaction.md rubric accordingly | Renaming would cascade changes through eval infra (universal_asserts.py line 808, tv.py line 311, panels.html lines 74-75). Keeping the name but changing semantics is lower risk and clearer: "pressures to remove" = scene-scoped threads to purge |
| D6 | pressure.py file fate | Delete the entire pressure.py module after consolidating its functions into _manage_thread_lifecycle() in turn.py | No other callers exist outside engine/turn.py and engine/__init__.py (which re-exports for test use). The module's sole purpose is scene_pressure lifecycle management, which becomes thread lifecycle management |
| D7 | Narrate context from pressures | Replace `scene_pressure` parameter to narrate functions with a derived list built from arc.threads[] where scope=scene and active=True | Narration needs urgency data for pacing directives. The old code passed state.scene["scene_pressure"] directly; the new code should derive equivalent urgency info from unified threads |

---

## Firm decisions
1. Scope-aware expiration rules are the single source of truth for thread lifecycle: scene-scoped threads expire on location change (matching old scene_pressure purge behavior); arc-scoped ones persist across scenes until resolved or aged out via age-based demotion rules (`active: True → False`). This replaces 3 separate functions with a unified entry point.
2. `_manage_thread_lifecycle()` replaces 3 separate functions (`_expire_scene_pressures()`, `_purge_scene_pressures()`, and the active/latent migration logic in `_apply_thread_signals()`) — a single entry point for all thread lifecycle management after Progress Extract outputs are applied, eliminating duplicate code paths that handled scene_pressure vs arc_threads differently.
3. **NEW:** `thread_resolve` processing is added to turn.py alongside existing _apply_thread_signals(). ThreadResolution objects move their corresponding threads from active/latent into completed_threads with resolution_state preserved on the thread object. This was a gap in phases 01–04 (model defined but never wired).

---

## What Is Removed

| # | Symbol / Field | File(s) | Replaced By |
|---|----------------|---------|-------------|
| R1 | `_expire_scene_pressures()` function | pressure.py:13–60 | `_manage_thread_lifecycle()` in turn.py (age-based urgency escalation on arc.threads[]) |
| R2 | `_purge_scene_pressures()` function | pressure.py:62–95 | `_manage_thread_lifecycle()` in turn.py (location-change expiry for scope=scene threads) |
| R3 | `pressure.py` module (entire file) | ccya/engine/pressure.py | Deleted — functionality consolidated into turn.py. Re-export from engine/__init__.py also removed |
| R4 | Import of pressure functions in turn.py | turn.py:30 | Removed after consolidation |
| R5 | Call sites for _purge_scene_pressures / _expire_scene_pressures | turn.py:1054–1060 | Single call to `_manage_thread_lifecycle(state, delta, config)` at same pipeline location (post-extraction) |
| R6 | `state.scene["scene_pressure"]` reads in compactor._apply_sanitization() | compactor.py:303, 349–352 | Filter arc.threads[] where scope=scene by IDs from CompactorSanitizationResult.pressure_remove |
| R7 | `state.scene["scene_pressure"]` read for narrate context | turn.py:875 (via _build_extraction_context → narrate.py) | Derive urgency list from arc.threads[] with scope=scope="scene" and active=True |
| R8 | Legacy split-list references in doc comments | Various (active_threads/latent_threads mentions in code comments) | Update to reference unified arc.threads[] with ArcThread.active bool flag |

---

## What Is Unchanged

The following components are NOT modified by phase 05:

- **CampaignArc model shape** — defined in models.py lines 68–76, already has unified `threads: list[ArcThread]`. No changes needed.
- **ProgressExtractResult schema** — thread_advance (list[str]), thread_resolve (list[ThreadResolution]), thread_add (ArcThread | None) already exist from phases 01/04. Phase 05 wires them into state mutation but does not change the model.
- **StateDelta model** — already has no scene_pressure fields (removed in phase 01). No changes needed.
- **apply_delta() / delta.py** — handles arc_update merges via _merge_arc_update(). Thread operations from ProgressExtractResult are handled by turn.py before StateDelta is finalized, not within apply_delta itself. This architecture does NOT change.
- **_apply_thread_signals() function signature and location in turn.py** — it remains at line 100, receives state + progress_result. Its internal logic evolves to handle unified threads (already partially done) but its call site and role as arc mutation orchestrator stays.
- **CompactorSanitizationResult.pressure_remove field definition** — kept for backward compat with compaction LLM output format; semantics change from "scene_pressure IDs" to "arc.thread IDs where scope=scene". The coercion validator at models.py:424 remains unchanged.
- **_candidate_to_latent_thread() function** — already operates on unified arc.threads[] (line 283). No changes needed.

---

## Model Shapes

### ArcThread (models.py:52–66) — modified by phase 05: adds `resolution_state` field

```python
class ArcThread(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]  # replaces scene_pressure + arc threads split
    active: bool = True  # False = dormant/latent; set by Python, not LLM
    urgency: Literal["background", "normal", "urgent"] = "normal"
    tags: list[str] = Field(default_factory=list)
    progress: int = 0
    last_seen_turn: int | None = None
    added_turn: int | None = None
    unlock_if: str | None = None
    promotes: list[str] = Field(default_factory=list)
    resolution_state: str | None = None  # set when thread_resolve processes resolved/failed/abandoned
```

### CampaignArc (models.py:68–76) — no changes, shown for reference

```python
class CampaignArc(BaseModel):
    visible_goal: str = ""
    thematic_question: str = ""
    hidden_truths: list[str] = Field(default_factory=list)
    discovered_truths: list[str] = Field(default_factory=list)
    threads: list[ArcThread] = Field(default_factory=list)  # unified — replaces active_threads/latent_threads split
    completed_threads: list[ArcThread] = Field(default_factory=list)
    pc_drive: str = ""
```

### ThreadResolution (models.py:438–441) — no changes, shown for reference

```python
class ThreadResolution(BaseModel):
    """Structured resolution for a thread — replaces scene_pressure_remove semantics."""
    id: str
    resolution_state: Literal["resolved", "failed", "abandoned"]
```

### NEW: _manage_thread_lifecycle() signature (to be added to turn.py)

```python
def _manage_thread_lifecycle(
    state: dict[str, Any],
    delta: StateDelta | None,
    config: EngineConfig | None = None,
    *,
    location_changed: bool = False,
    combat_ended: bool = False,
) -> CampaignArc | None:
```

Returns a mutated CampaignArc if any threads were expired/demoted/escalated. Operates on arc.threads[] with scope-aware rules. This replaces the return-less void functions in pressure.py (which modified state dicts in-place).

---

## Context for Implementing LLMs

- **Read `ccya/engine/turn.py`** — specifically `_apply_thread_signals()` (line 100) and its call site at line 1174. This is where thread_advance processing already happens; phase 05 adds thread_resolve handling here too.
- **Read `ccya/engine/pressure.py`** in full — the entire file gets deleted, but you need to understand what _expire_scene_pressures and _purge_scene_pressures currently do (urgency escalation + location-change skipping) to implement equivalent logic as scope-aware expiration on unified threads.
- **Read `ccya/models.py` lines 52–76** — ArcThread and CampaignArc shapes are already correct; no changes needed but you must use them correctly when filtering by scope=scene vs scope=arc.
- **Read `ccya/engine/compactor.py` lines 290–354** — _apply_sanitization() has a pressure_remove block that reads/writes state.scene["scene_pressure"]. This is the compaction code path you must update to use arc.threads[] with scope=scope="scene" instead.
- **Read `ccya/engine/narrate.py` line 38 and turn.py lines 875–887** — narrate context building passes scene_pressure list; replace with derived urgency data from unified threads.

---

## Risks, Ambiguities, and Blockers

### Resolved (from source validation)
- **Ambiguity resolved:** compactor.py `CompressorSanitizationResult.pressure_remove` maps to arc.threads[] scope=scene IDs — kept the field name but changed semantics (Decision D5). The compaction LLM prompt already says "pressure_remove" and should continue outputting pressure-like IDs; phase 05 code interprets them as scene-scoped thread IDs.
- **Blocker resolved:** panels.py `_debug_context()` does NOT directly access scene_pressure or split lists — it loads full state via _load_current_state(). No changes needed there.

### Remaining open questions requiring user input:

1. **RESOLVED by D2:** ArcThread gains `resolution_state: str | None` field (set when thread_resolve processes resolved/failed/abandoned). This preserves LLM-emitted structured state on the thread for narrative context and eval rubrics.

2. **DECIDED:** Rename EngineConfig scene_pressure_building_at → thread_urgency_building_at, scene_pressure_immediate_at → thread_urgency_immediate_at (and related constants). Scene pressure is gone; urgency escalation on unified threads uses the same thresholds but with clearer naming.

---

## Dependencies
01: unified ArcThread shape + StateDelta schema must exist so apply_delta() can accept the new field names from 04's LLM outputs.
02: PacingContext inputs needed by scope-aware expiration rules (gate values influence whether scene-scoped threads get purged on location change).
03+04: LLM outputs have changed (no more scene_pressure operations, no beat_disposition) so the delta application logic needs to match what Progress actually emits after these phases. **Note:** thread_resolve from 01/04 is NOT yet wired into state mutation — phase 05 must implement this processing.
