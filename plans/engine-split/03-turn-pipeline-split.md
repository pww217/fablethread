# Plan: Turn Pipeline Stage Split

## Purpose

Split `ccya/engine/turn.py` (1672 lines) into 5 files aligned to pipeline stages: `turn_context.py` (dataclasses), `_pacing.py` (phase engine), `turn_state.py` (state application), `ruling.py` (ruling stage), `narrate.py` (narrate stage), with a thinned `turn.py` (orchestrator only).

## Problem Statement

`turn.py` has 17 top-level symbols mixing unrelated concerns: dataclass definitions, phase engine computation, pipeline stage orchestration, post-extraction state application, validation, and utilities. An agent working on thread resolution must load 1600 lines of ruling/pacing/narrate code. The real bug is that stage implementation (`_ruling_phase`, `_narrate_setup`) lives in `turn.py` while the prompt/parse/retry helpers for those stages live in their respective files (`ruling.py`, `narrate.py`) — same concern, split file.

## Constraints

- All `ccya/engine/__init__.py` re-exports preserved unchanged.
- No behavioral changes — function bodies move verbatim (except the inline `_apply_state_updates` extraction).
- `run_turn()` signature stays identical.
- Each phase must leave `make check` passing.

## Non-goals

- Changes to prompt templates, config keys, or state shape.
- Changes to `engine/__init__.py` re-exports.
- Changes to `docs/` — handled as a final task after all 3 plans complete.

## Solution

Move functions from `turn.py` into their pipeline-stage files in 3 ordered phases: (1) context dataclasses + phase engine, (2) state application (biggest chunk), (3) ruling + narrate stage functions + final import cleanup. Each phase adds functions to target files and removes them from `turn.py`, keeping the file importable at every step.

## Firm decisions

1. `turn_context.py` is created first — it is a dependency for `narrate.py`'s `TYPE_CHECKING` import.
2. `_validate()` moves to `turn_state.py` with its sole caller.
3. `_strip_fallback()` stays in `turn.py`.
4. `_apply_state_updates()` is a new function extracting ~260 lines of inline code from `run_turn()`. It uses the exact same logic in the exact same order — no simplification or restructuring.
5. Each move is additive (copy to target, remove from turn.py, update import if needed) to keep the file importable at every intermediate state.

## Risks, Ambiguities, and Blockers

- **Dependency chain:** Phase 2 imports `PacingContext` from `turn_context.py` (Phase 1). Phase 2 also moves `_validate` which is called inside the `_apply_state_updates` block. Phase 3 moves `_ruling_phase` and `_narrate_setup` which call functions from across the engine. All phases must be executed in order.
- **`_apply_state_updates` inlined extraction:** The ~260-line block runs across lines ~1130-1490 of `run_turn()`. The executor must identify the exact boundary (after extraction pipeline yields, before TurnResult build) and not accidentally include or exclude adjacent logic. The line ranges in this plan are approximate — the executor should verify exact start/end by reading the fresh source.
- **`narrate.py` TYPE_CHECKING import:** Currently imports `PacingContext` from `ccya.engine.turn`. After Phase 1, it imports from `ccya.engine.turn_context`. This must be updated in Phase 1, not deferred — otherwise `narrate.py` imports from `turn.py` which no longer defines `PacingContext`.
- **Import ordering:** After Phase 3, `turn.py` no longer imports from `extraction` directly (wait — it still does; the extraction import is for `_run_extraction_pipeline` which stays in `turn.py`). But `turn.py` no longer imports `_validate`, `_pacing` computation functions, etc. The phased approach ensures imports are pruned at the right time.

## Status
`open`

## Phases

3 phases, ordered by dependency.

---

## Implementation — Phase 1: Context dataclasses + phase engine

### Context files to load

- `ccya/engine/turn.py` lines 73–108 — `TurnContext` and `PacingContext` definitions
- `ccya/engine/turn.py` lines 426–590 — `_compute_narration_directive`, `_compute_pacing_context`, `_compute_ages`, `_compute_scene_phase`, `_recent_turn_count`
- `ccya/engine/_pacing.py` — current file (141 lines) to understand where to add the new functions
- `ccya/engine/narrate.py` lines 16–17 — TYPE_CHECKING import of `PacingContext`
- `docs/design/engine-file-splitting-design.md` — "Turn pipeline split" section

### Detailed steps

#### Step 1.1 — Create `ccya/engine/turn_context.py`

**File:** `ccya/engine/turn_context.py` (new)

**What:** Copy `TurnContext` dataclass (lines 73–97) and `PacingContext` dataclass (lines 98–108) from `turn.py` into the new file.

Original imports to carry over: `from __future__ import annotations`, `from dataclasses import dataclass, field`, `from pathlib import Path`, `from typing import Any`.

Original symbols referenced by `TurnContext`: `EngineConfig` (from `ccya.engine.config`), `IntentEnvelope`, `RulesOutcome` (from `ccya.models`).

**Why:** These dataclasses are consumed by `narrate.py` (via `TYPE_CHECKING`), `ruling.py`, and `turn_state.py`. Extracting them into their own file eliminates the circular-import-prone path through `turn.py`.

**Validation:** `python -c "from ccya.engine.turn_context import TurnContext, PacingContext; print('ok')"` prints "ok".

#### Step 1.2 — Update `narrate.py` TYPE_CHECKING import

**File:** `ccya/engine/narrate.py` line 17

**What:** Change:
```python
if TYPE_CHECKING:
    from ccya.engine.turn import PacingContext
```
to:
```python
if TYPE_CHECKING:
    from ccya.engine.turn_context import PacingContext
```

**Why:** `PacingContext` no longer lives in `turn.py`. The `TYPE_CHECKING` guard means this change has zero runtime cost.

**Validation:** `python -c "from ccya.engine.narrate import _narrate_messages; print('ok')"` prints "ok".

#### Step 1.3 — Move phase engine functions to `_pacing.py`

**File:** `ccya/engine/_pacing.py` (append) and `ccya/engine/turn.py` (remove)

**What:** Copy these 5 functions from `turn.py` to `_pacing.py`, then remove them from `turn.py`:

- `_compute_narration_directive(scene_phase, thread_urgency_count, effective_scene_age, scene_pressure_threshold, scene_imperative_threshold)` → str
- `_compute_pacing_context(scene_phase, thread_urgency_count, effective_scene_age, scene_motion, scene_pressure_threshold, scene_imperative_threshold)` → `PacingContext`
- `_compute_ages(state)` → dict[str, int]
- `_compute_scene_phase(state, ages, config, convergence_score)` → dict[str, Any]
- `_recent_turn_count(state)` → int

Add imports to `_pacing.py` for any new dependencies: `PacingContext` from `ccya.engine.turn_context`, `ceil` from `math`, etc. — check what each function currently imports in `turn.py`.

Add imports to `turn.py` for the moved functions: `_compute_ages`, `_compute_scene_phase`, `_compute_pacing_context`, `_compute_narration_directive`, `_recent_turn_count` from `ccya.engine._pacing` (since `_ruling_phase` and `_narrate_setup` still call them and haven't moved yet).

Remove the function definitions from `turn.py` and prune any imports that were only needed for the moved functions (but keep the call sites — `_ruling_phase` calls `_compute_ages`, `_narrate_setup` calls `_compute_scene_phase` and `_compute_pacing_context`).

**Why:** Phase engine computation is a cohesive domain that already has its own file (`_pacing.py`). The 5 functions are purely computational (no I/O, no LLM calls). Moving them keeps `turn.py` focused on orchestration.

**Validation:**
1. `python -c "from ccya.engine._pacing import _compute_scene_phase, _compute_pacing_context, _compute_narration_directive, _compute_ages, _recent_turn_count; print('ok')"` prints "ok".
2. `python -c "from ccya.engine.turn import run_turn; print('ok')"` prints "ok" (turn.py still importable after removals).

#### Step 1.4 — Run `make check`

**What:** Verify lint and typecheck pass.

**Why:** Phase 1 makes structural changes to 4 files — need to verify no missed imports or type breaks.

**Validation:** `make check` exits 0.

---

## Implementation — Phase 2: State application (`turn_state.py`)

### Context files to load

- `ccya/engine/turn.py` lines 112–434 — `_apply_thread_updates`, `_apply_arc_resolve`, `_apply_thread_resolutions` function bodies
- `ccya/engine/turn.py` lines 1115–1490 (approximate) — the inline state application block in `run_turn()` that becomes `_apply_state_updates`
- `ccya/engine/turn.py` lines 1607–1672 — `_validate` function
- `ccya/engine/turn.py` lines 1–72 — all imports (to identify which need to move to `turn_state.py`)
- `ccya/engine/changes.py` — `_summarize_applied` function (called by `run_turn()` after `_apply_state_updates` returns)
- `docs/design/engine-file-splitting-design.md` — `_apply_state_updates` interface

### Detailed steps

#### Step 2.1 — Create `ccya/engine/turn_state.py`

**File:** `ccya/engine/turn_state.py` (new)

**What:** Move these functions from `turn.py`:
- `_apply_thread_updates(state, storyteller_result, config, dedup_rejections)` → `ArcThread | None`
- `_apply_arc_resolve(state, storyteller_result, config)` → `CampaignArc | None`
- `_apply_thread_resolutions(state, storyteller_result)` → `CampaignArc | None`
- `_validate(state, delta)` → `list[dict[str, Any]]`

Add required imports from `turn.py` that these functions use: `CampaignArc`, `ArcThread`, `ProgressEntry`, `StorytellerResult`, `StateDelta`, `ErrorKind` from models and errors; `_merge_arc_update` from `ccya.state.delta_builder`; `resolve_inventory_remove_target` from `ccya.state`; `EngineConfig` from `ccya.engine.config`; `logging`, `copy`, `typing`.

**Why:** Thread operations and validation are the state application concern — they apply storyteller output to the state dict. Grouping them in one file aligns with the pipeline-stage principle.

**Validation:** `python -c "from ccya.engine.turn_state import _apply_thread_updates, _apply_arc_resolve, _apply_thread_resolutions, _validate; print('ok')"` prints "ok".

#### Step 2.2 — Extract `_apply_state_updates()` in `turn_state.py`

**File:** `ccya/engine/turn_state.py` (append)

**What:** Create a new function with this signature:

```python
def _apply_state_updates(
    state: dict[str, Any],
    delta: StateDelta | None,
    storyteller_result: StorytellerResult | None,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
) -> tuple[dict[str, Any], StateDelta | None, dict[str, Any], list[dict[str, Any]], list[str]]:
```

Extract the inline code from `run_turn()` spanning from the `if delta is not None:` block (after extraction pipeline yields) through the NPC lifecycle section (nearby decay + departed archive), excluding the `_strip_fallback` call and everything after it.

The blocks to include, in order:
1. `if delta is not None:` → validate + reconcile + apply_delta (includes `_validate`, `reconcile_delta`, `apply_delta`)
2. Beat history: snapshot `pending_gm_beat` to `recent_beats`
3. Persist `last_inventory_change_reason` and `last_condition_change_reason`
4. NPC compendium stamping: `last_presence_turn`, `last_seen_location`
5. Arc director: `chapter_end`, `_apply_thread_updates`, `goal_update`, conflict detection, `_apply_arc_resolve`, `_apply_thread_resolutions`, `thread_add` with cap eviction, auto-dormant culling
6. NPC lifecycle: nearby decay (`nearby` → `known`), departed archive (`departed` → `archived`)

The function returns the mutated `state`, `delta`, `applied`, `rejected`, and `reconcile_warnings`.

Imports needed by the extracted code: `CampaignArc`, `ArcThread`, `StorytellerResult`, `StateDelta`, `ErrorKind`; `apply_delta`, `reconcile_delta`, `resolve_inventory_remove_target` from `ccya.state`; `_merge_arc_update` from `ccya.state.delta_builder`; `EngineConfig` from `ccya.engine.config`; `asyncio`, `copy`, `logging`, `Path`, `ceil`, `typing`.

**Why:** Currently ~260 lines of inline code with no function boundary. Extracting it makes the orchestrator composition visible: the stage functions are called, then `_apply_state_updates` is called, then the result is persisted.

**Validation:** `python -c "from ccya.engine.turn_state import _apply_state_updates; print('ok')"` prints "ok".

#### Step 2.3 — Update `run_turn()` to call `_apply_state_updates()`

**File:** `ccya/engine/turn.py`

**What:** Compute `state_pre_apply = copy.deepcopy(state)` before the call, then replace the ~260-line inline state application block in `run_turn()` with:

```python
state_pre_apply = copy.deepcopy(state)
state, delta, applied, rejected, reconcile_warnings = _apply_state_updates(
    state, delta, storyteller_result, config, trace_id, turn_no,
)
# Handle blocking rejections (error handling was inline, now after the call)
blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
if blocking:
    errors.append({
        "kind": ErrorKind.DELTA_VALIDATION_FAILED,
        "trace_id": trace_id,
        "message": f"Delta validation failed ({len(blocking)} rejection(s)).",
    })
    narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"
```

Remove the variables that are now handled inside `_apply_state_updates`: `thread_dedup_rejections`. Keep `state_pre_apply` — it is still needed for `summarize_changes(state_pre_apply, state, rejected)` which runs after this block.

**Why:** The orchestrator now reads as a sequence of stage calls → state application → persist.

**Validation:** `python -c "from ccya.engine.turn import run_turn; print('ok')"` prints "ok".

#### Step 2.4 — Run `make check`

**What:** Verify lint and typecheck pass.

**Why:** Phase 2 is the largest change — extracting ~260 lines and creating a new file with complex logic.

**Validation:** `make check` exits 0.

---

## Implementation — Phase 3: Ruling + narrate stage moves + final cleanup

### Context files to load

- `ccya/engine/turn.py` lines 592–739 — `_ruling_phase` function body + its imports
- `ccya/engine/turn.py` lines 741–873 — `_narrate_setup` function body + its imports
- `ccya/engine/turn.py` lines 1–72 — current imports (to prune after moves)
- `ccya/engine/ruling.py` — existing file (184 lines) to know where to place `_ruling_phase`
- `ccya/engine/narrate.py` — existing file (134 lines) to know where to place `_narrate_setup`
- `ccya/engine/turn.py` lines 875–1610 — `run_turn()` function to verify import pruning doesn't break call sites

### Detailed steps

#### Step 3.1 — Move `_ruling_phase` to `ruling.py`

**File:** `ccya/engine/ruling.py` (append) and `ccya/engine/turn.py` (remove)

**What:** Copy `_ruling_phase` (async function, 148 lines) from `turn.py` to `ruling.py`, then remove it from `turn.py`.

Add imports to `ruling.py` that `_ruling_phase` needs:
- `_pacing.py`: already imported? No — `ruling.py` currently imports from `ccya.engine.config`, `ccya.llm_client`, `ccya.models`. It needs `build_npc_roster` (`ccya.engine.npc_roster`), `_compute_ages` (`ccya.engine._pacing`), `resolve_check`/`build_directive` (`ccya.rules`), `asyncio`, `logging`.
- The function references `TurnContext` — add `from ccya.engine.turn_context import TurnContext`.

**Why:** `_ruling_phase` completes the ruling stage — it calls `_ruling_messages` and `_call_ruling` which already live in `ruling.py`. The stage is now self-contained.

**Validation:** `python -c "from ccya.engine.ruling import _ruling_phase; print('ok')"` prints "ok".

#### Step 3.2 — Move `_narrate_setup` to `narrate.py`

**File:** `ccya/engine/narrate.py` (append) and `ccya/engine/turn.py` (remove)

**What:** Copy `_narrate_setup` (async function, 133 lines) from `turn.py` to `narrate.py`, then remove it from `turn.py`.

Add imports to `narrate.py` that `_narrate_setup` needs:
- Already imports: `RulesOutcome` from `ccya.models`, `_fmt_progress` from `ccya.prompts.context`, `build_npc_roster` from `ccya.engine.npc_roster`.
- Needs new imports: `generate_npc_names_split` (`ccya.engine.names`), `ArcThread` (`ccya.models`), `compute_convergence_score`/`detect_spiral` (`ccya.engine._pacing`), `_compute_scene_phase` (`ccya.engine._pacing`), `_compute_pacing_context` (`ccya.engine._pacing`), `build_npc_roster` (`ccya.engine.npc_roster`), `ARCHETYPES` (`ccya.personality`).
- The function references `TurnContext` and `PacingContext` — add `from ccya.engine.turn_context import TurnContext, PacingContext`.
- The existing `TYPE_CHECKING` import of `PacingContext` from `ccya.engine.turn_context` (updated in Phase 1 step 1.2) can stay under `TYPE_CHECKING` — `_narrate_setup` returns `tuple[Any, Any]` and does not use `PacingContext` in its signature. The `PacingContext` import is only needed for type checking.

**Why:** `_narrate_setup` completes the narrate stage — it calls `_narrate_messages` which already lives in `narrate.py`. The stage is now self-contained.

**Validation:** `python -c "from ccya.engine.narrate import _narrate_setup; print('ok')"` prints "ok".

#### Step 3.3 — Prune imports in `turn.py`

**File:** `ccya/engine/turn.py`

**What:** Remove imports that are no longer needed because the corresponding functions have been moved:

- `from ccya.engine.narrate import _narrate_messages` — no, wait. `turn.py` still imports `_narrate_messages` for... actually let me check. In the current code, `_narrate_setup` (which called `_narrate_messages`) has moved to `narrate.py`. Does `run_turn()` call `_narrate_messages` directly? No — it calls `_narrate_setup`. So this import can be removed.
- Similarly, `_ruling_messages` and `_call_ruling` — used by `_ruling_phase` which moved. Remove if `run_turn()` doesn't import them directly.
- `generate_npc_names_split` from `ccya.engine.names` — only used by `_narrate_setup`. Remove.
- `compute_convergence_score`, `derive_allowed_beat_types`, `detect_spiral` from `ccya.engine._pacing` — check if `run_turn()` calls any of these directly. Looking at the current code: `run_turn()` calls `derive_allowed_beat_types` at line ~1455 for the event's `allowed_beat_types` field. So `derive_allowed_beat_types` stays. `compute_convergence_score` and `detect_spiral` are called by `_narrate_setup` — remove those.
- `build_npc_roster` from `ccya.engine.npc_roster` — called by `_ruling_phase`. Remove.
- `ARCHETYPES` from `ccya.personality` — used by `_ruling_phase` and `_narrate_setup`. Remove.
- `resolve_check`, `build_directive` from `ccya.rules` — used by `_ruling_phase`. Remove.
- `_apply_thread_updates`, `_apply_arc_resolve`, `_apply_thread_resolutions`, `_validate` — all moved to `turn_state.py`.
- `_context_meta`, `_avg_event_ms` from `ccya.engine.extraction` — still used by `run_turn()` for event metadata building. Keep.
- `_compute_narration_directive`, `_compute_pacing_context`, `_compute_ages`, `_compute_scene_phase`, `_recent_turn_count` — all moved to `_pacing.py`. Remove.
- Add `from ccya.engine.turn_state import _apply_state_updates, _apply_thread_updates, _apply_arc_resolve, _apply_thread_resolutions` (wait, `run_turn()` doesn't call individual thread functions anymore — it calls `_apply_state_updates` which calls them internally. So only `_apply_state_updates` needs to be imported by `run_turn()`.)
- Add `from ccya.engine.turn_context import TurnContext` (wait — `TurnContext` is constructed in `run_turn()`. So yes, import it.)

The executor must carefully verify each import by reading `run_turn()`'s current source. The above is guidance, not a complete list.

**Why:** Dead imports cause lint warnings and confuse LLM agents reading import lists.

**Validation:** `python -c "from ccya.engine.turn import run_turn, warmup; print('ok')"` prints "ok". Then `make check` exits 0.

#### Step 3.4 — Final import verification

**What:** Verify no function was left behind in `turn.py` that should have moved, and no function was moved but still referenced in `turn.py`.

**Why:** Full consistency check before marking the plan complete.

**Validation:**
```bash
# Verify moved functions are NOT in turn.py
for fn in _ruling_phase _narrate_setup _apply_thread_updates _apply_arc_resolve _apply_thread_resolutions _compute_narration_directive _compute_pacing_context _compute_ages _compute_scene_phase _recent_turn_count TurnContext PacingContext _validate; do
  if rg "^async def $fn|^def $fn|^class $fn" ccya/engine/turn.py; then
    echo "ERROR: $fn still in turn.py"
  fi
done

# Verify moved functions ARE in their target files
rg "^async def _ruling_phase|^def _ruling_phase" ccya/engine/ruling.py     # must exist
rg "^async def _narrate_setup|^def _narrate_setup" ccya/engine/narrate.py     # must exist
rg "^def _apply_thread_updates" ccya/engine/turn_state.py     # must exist
rg "^class TurnContext" ccya/engine/turn_context.py     # must exist
rg "^class PacingContext" ccya/engine/turn_context.py     # must exist
rg "^def _compute_scene_phase" ccya/engine/_pacing.py     # must exist
```

#### Step 3.5 — Run `make check` (final)

**What:** Final verification that all 3 phases together pass lint and typecheck.

**Why:** If any import was missed or a function reference is broken, `make check` will catch it.

**Validation:**
```bash
make check
```
Exit code 0.

### Tests to write or update

No tests — tests are temporarily removed. Validation relies on `make check` and grep-based presence verification.

---

## Documentation Update (Final — After All 3 Plans)

These updates are not part of any single plan phase. They are performed once after the last plan executes.

### `docs/repomap.md`

Replace all references to `ccya/engine/turn.py` functions with their new file locations:
- `TurnContext`, `PacingContext` → `ccya/engine/turn_context.py`
- `_compute_scene_phase`, `_compute_narration_directive`, `_compute_pacing_context`, `_compute_ages` → `ccya/engine/_pacing.py`
- `_ruling_phase` → `ccya/engine/ruling.py`
- `_narrate_setup` → `ccya/engine/narrate.py`
- `_apply_thread_updates`, `_apply_arc_resolve`, `_apply_thread_resolutions`, `_apply_state_updates`, `_validate` → `ccya/engine/turn_state.py`
- `run_turn`, `warmup`, `_strip_fallback` → `ccya/engine/turn.py` (unchanged)

Replace the module table row for `ccya/engine/extraction.py` with the subpackage structure:
- `ccya/engine/extraction/pipeline.py` — orchestrator
- `ccya/engine/extraction/scene.py` — scene message builder
- `ccya/engine/extraction/state.py` — state message builder
- `ccya/engine/extraction/storytell.py` — storytell message builder
- `ccya/engine/extraction/context.py` — extraction context
- `ccya/engine/extraction/utils.py` — shared utilities

Replace the module table row for `ccya/models.py` with the subpackage structure:
- `ccya/models/state.py` — state/thread models
- `ccya/models/extraction.py` — extraction result models
- `ccya/models/rules.py` — rules models
- `ccya/models/config.py` — config types + TurnResult + load/save
- `ccya/models/compactor.py` — dormant compactor stubs

### `docs/architecture/OVERVIEW.md`

Update any pipeline overview file references that point to `ccya/engine/turn.py` and `ccya/engine/extraction.py` to reflect the new file locations.

### `AGENTS.md` (this file)

No changes needed — `AGENTS.md` references `ccya/engine` package-level functions, not submodule paths. The `# Repo map` cross-cutting task section is already covered by `docs/repomap.md`.
