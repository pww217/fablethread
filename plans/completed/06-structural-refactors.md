# Structural Refactors — Monoliths, Boundaries, State Versioning

## Status
`open`

## Phases

4 phases: extract NPC management from `apply_delta()` into `state/npcs.py`, refactor `run_turn()` into composable phases, fix circular dependency between `engine` and `state` packages, add state schema versioning.

## Issue

Three structural problems prevent unit testing and block safe pipeline extension:

1. **`apply_delta()`** at `state/delta.py:125-545` is a 420-line function with 5 nested closures. NPC scene management alone is ~220 lines (lines 323-539) with closures capturing `state`, `comp`, and other local variables. The function handles inventory, location, conditions, scene events, NPCs, and arc updates in one deeply nested body.

2. **`run_turn()`** at `engine/turn.py:654-1457` is an 800-line async generator monolith handling ~15 distinct responsibilities: ruling, dice resolution, narration, memory loading, extraction pipeline orchestration, delta application, arc thread management, narrator arc update extraction, condition aging, NPC stamping, recently_left decay, persisting (3 file writes), compaction, error recovery, metrics aggregation, and SSE event yielding. The `try/except/finally` wrapping the entire body makes partial-failure recovery opaque.

3. **Circular dependency** between engine and state packages: `engine/extraction.py:74` uses a local import (`from ccya.state.delta import apply_delta`) to avoid the cycle, and `engine/turn.py:65` imports `_merge_arc_update` — a private function from another package.

4. **No state schema versioning.** The IO layer at `state/io.py:28-78` already has an ad-hoc regex fix for old YAML serialization (line 87-92), proving the schema has evolved without a versioning mechanism.

## Solution

Extract NPC scene management from `apply_delta()` into `state/npcs.py` as module-level functions with explicit parameter passing. This is the highest-impact extraction because it removes ~220 lines of nested closures. Refactor `run_turn()` into 5-7 async phase functions composed in a single orchestrator. Fix the circular dependency by moving `_build_extraction_context()` and related data-flow functions to a shared module or by inverting the dependency direction. Add a `schema_version` field to the state dict with a minimal migration registry.

## Firm decisions

1. `state/npcs.py` is a new file, not a class. It exports module-level functions: `apply_npc_scene_management(state, scene_result, comp, current_turn_no) -> dict[str, Any]`.
2. `run_turn()` phases communicate through a `TurnContext` dataclass, not through closure-captured local variables. Each phase reads from and writes to the context.
3. The circular dependency fix moves `_build_extraction_context()` to `state/delta_builder.py` — a new shared module that both engine and state can import.
4. State schema version starts at 1 for new saves. Legacy saves without a version field are assumed version 0 and read by the existing code path.

## Non-goals

- Not changing the SSE yield protocol or the async iterator shape of `run_turn()`.
- Not adding a migration framework. The versioning fix is minimal: a version field on write, a warning on read for mismatched versions, a simple dict-based migration registry.
- Not touching `apply_delta()` beyond extracting NPC management. The remaining function is still ~200 lines.

## Risks, Ambiguities, and Blockers

- `run_turn()` refactor has the highest risk. The async generator yields narrative tokens to an SSE stream. Changing the yield points risks breaking the streaming contract. Each phase must yield through a shared helper.
- The NPC extraction from `apply_delta()` requires reading the ~220 lines of nested closures carefully. Some closures reference both `state` and `comp` — threading these as explicit parameters is mechanical but error-prone.
- The circular dependency fix may require updating imports in `eval/engine_mirror.py` and other files that import from the current locations.
- **Dependency on plan 04:** Phase 3 moves `reconcile_delta()` which plan 04 Phase 2 changes to return `tuple[StateDelta, list[str]]` instead of `list[str]`. Must execute after plan 04 is complete, or merge the changes.
- Phases 1-3 should run sequentially. Phase 4 (schema versioning) is independent and can run in parallel.
- No blocker, but each phase is 4-8 hours of work.

---

## Implementation — Phase 1: Extract NPC management from apply_delta()

### Context files to load
- `ccya/state/delta.py` — `apply_delta()` function, lines 125-545. Specifically:
  - The 5 nested closures: `_by_id()` (line 135), `_hydrate_npc_text()` (~line 200), `_resolve_npc_id()` (~line 300), `_find_npc_by_name()` (~line 310), `_apply_npc_to_present()` (~line 320)
  - The NPC scene management block (~lines 323-539)
- `ccya/models.py` — `NpcAdd`, `NpcUpdate`, `NpcRemove`, `CompendiumNpcUpdate` model definitions
- `ccya/engine/extraction.py` — how NPC state flows from extraction to delta

### Detailed steps

#### Step 1.1 — Create `ccya/state/npcs.py` with extracted NPC functions

**File:** new file `ccya/state/npcs.py`

**What:** Create a new module `ccya/state/npcs.py` containing extracted versions of the NPC-management functions from `apply_delta()`. The module exports:

```python
# Interface contract
def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
) -> dict[str, Any]:
    """Apply NPC scene deltas: add, remove, update present NPCs and compendium.
    
    Returns the mutated state dict. NPC_SCENE_CAP is enforced here.
    """
    ...
```

Extract the following closures into module-level functions:
- `_hydrate_npc_text(npc_add: NpcAdd, comp: dict[str, Any]) -> dict[str, Any]` — hydrate NPC identity from compendium
- `_resolve_npc_id(npc_add: NpcAdd, comp: dict[str, Any]) -> str` — resolve NPC ID from compendium
- `_find_npc_by_name(name: str, comp: dict[str, Any]) -> str | None` — fuzzy name match against compendium
- `_apply_npc_to_present(present_list: list[dict], action: str, npc: dict) -> list[dict]` — add/remove/update a single NPC in present list

**Why:** NPC scene management is ~220 lines of `apply_delta()` that has no business being inside a function that also handles inventory, conditions, and arc updates. Extracting it makes both the caller and the extracted module independently testable.

**Validation:** `python3 -c "import ccya.state.npcs"` succeeds. `make check` passes.

#### Step 1.2 — Replace inline NPC management with call to extracted module

**File:** `ccya/state/delta.py`

**What:** Remove the NPC scene management block (~lines 323-539) from `apply_delta()`. Replace with:

```python
from ccya.state.npcs import apply_npc_scene_management
...
# In apply_delta(), after scene delta handling:
if delta.npc_add or delta.npc_remove or delta.npc_update or delta.compendium_npc_update:
    state = apply_npc_scene_management(state, SceneExtractResult(
        npc_add=delta.npc_add,
        npc_remove=delta.npc_remove,
        npc_update=delta.npc_update,
        compendium_npc_update=delta.compendium_npc_update,
        scene_tags=delta.scene_tags,
        scene_tagline=delta.scene_tagline,
        location_change=delta.location_change,
        location_description=delta.location_description,
    ), current_turn_no=current_turn_no)
```

Also remove the `NPC_SCENE_CAP = 8` local variable from `apply_delta()` — move it to module level in `delta.py` or `npcs.py`.

**Why:** The goal is to make `apply_delta()` shorter and more focused. After extraction, it drops from 420 to ~200 lines. The extracted NPC logic becomes independently testable.

**Validation:** `make check && make test` passes. Run a game turn that triggers NPC add/remove/update — confirm NPC state changes are identical to before the extraction.

### Tests to write or update

- `tests/test_npcs.py`: New test file. Test `apply_npc_scene_management` with:
  - Adding a new NPC (not in present, not in compendium)
  - Adding a known NPC (in compendium, should hydrate)
  - Removing a present NPC
  - Updating a present NPC's notes
  - Updating compendium with new bio/aliases
  - Enforcing NPC_SCENE_CAP (exceeding limit should truncate)

### REPOMAP updates required

- `ccya/state/delta.py`: Remove NPC closures, add import of `apply_npc_scene_management`.
- `ccya/state/npcs.py`: New file — added to REPOMAP.

---

## Implementation — Phase 2: Refactor `run_turn()` into composable phases

### Context files to load
- `ccya/engine/turn.py` — the full `run_turn()` function (lines 654-1457). Pay special attention to:
  - The `AsyncIterator` yield protocol for SSE streaming
  - The `try/except/finally` error recovery (around line 1456)
  - The `recent_turns` loading logic
  - The 5-call pipeline orchestration (ruling → narrate → extraction)
  - The arc thread management blocks
  - The persistence and compaction logic

### Detailed steps

#### Step 2.1 — Define a TurnContext dataclass

**File:** `ccya/engine/turn.py`

**What:** Add a `TurnContext` dataclass at the top of the turn module (before `run_turn()`):

```python
@dataclass
class TurnContext:
    state: dict[str, Any]
    user_input: str
    turn_no: int
    trace_id: int
    config: EngineConfig
    chronicle_tail: list[str]
    pending_gm_beat: dict[str, Any] | None
    ruling_result: IntentEnvelope | None = None
    rules_outcome: RulesOutcome | None = None
    pacing_ctx: PacingContext | None = None
    narrative: str | None = None
    extraction_context: _ExtractionContext | None = None
    scene_result: SceneExtractResult | None = None
    state_result: StateExtractResult | None = None
    storytell_result: StorytellerResult | None = None
    delta: StateDelta | None = None
    rejections: list[dict[str, Any]] | None = None
```

**Why:** `run_turn()` currently passes data between phases through closure-captured local variables (~30 variables scattered across 800 lines). A context object makes the data flow explicit, enables step-by-step execution, and makes each phase independently callable.

**Validation:** `python3 -c "from ccya.engine.turn import TurnContext"` succeeds.

#### Step 2.2 — Extract each phase into an async function

**File:** `ccya/engine/turn.py`

**What:** Extract these functions from `run_turn()`, each taking a `TurnContext` and returning an updated one:

- `async def _phase_ruling(ctx: TurnContext) -> TurnContext` — Step 0: rules call, dice resolution, momentum update
- `async def _phase_narrate(ctx: TurnContext) -> TurnContext` — Step 1: narrate LLM call, narrative generation, SSE yield
- `async def _phase_extraction(ctx: TurnContext) -> TurnContext` — Steps 2a-2c: scene, state, storytell extraction pipeline
- `async def _phase_delta_apply(ctx: TurnContext) -> TurnContext` — validate + reconcile + apply_delta
- `async def _phase_arc_threads(ctx: TurnContext) -> TurnContext` — thread signals, resolutions, promotions, narrator arc merge
- `async def _phase_persist(ctx: TurnContext) -> TurnContext` — state.yaml, events.jsonl, chronicle.md writes
- `async def _phase_compact(ctx: TurnContext) -> TurnContext` — compaction check and execution

**Why:** 15 distinct responsibilities in one function prevents unit testing, obscures error paths, and makes adding new pipeline steps a full-understanding task. Each phase function can be independently unit-tested with a mock TurnContext.

**Validation:** `run_turn()` becomes a composition of 7 async calls. Run the full pipeline end-to-end and compare output state, events, and chronicle with the pre-refactor version. No behavioral difference should exist.

### Tests to write or update

- `tests/test_run_turn_phases.py`: Test each `_phase_*` function independently with a constructed `TurnContext`. For `_phase_ruling`, assert IntentEnvelope + RulesOutcome are set on the context. For `_phase_extraction`, assert extraction results match mock LLM output.

### REPOMAP updates required

- `ccya/engine/turn.py`: Structure changed from one 800-line function to one orchestrator + 7 phase functions.
- `ccya/engine/turn.py`: Add `TurnContext` dataclass definition.

---

## Implementation — Phase 3: Fix circular dependency between engine and state

### Context files to load
- `ccya/engine/extraction.py` — the local import at line 74 (`from ccya.state.delta import apply_delta`)
- `ccya/engine/turn.py` — the import of private `_merge_arc_update` at line 65
- `ccya/state/delta.py` — `apply_delta()`, `reconcile_delta()`, `_merge_arc_update()`

### Detailed steps

#### Step 3.1 — Move `apply_delta()`, `reconcile_delta()`, and `_merge_arc_update()` to `state/delta_builder.py`

**File:** new file `ccya/state/delta_builder.py`

**What:** Create a new module `ccya/state/delta_builder.py` that contains:
- `apply_delta(state, delta) -> tuple[dict[str, Any], bool]` — moved from `state/delta.py`
- `reconcile_delta(state, delta) -> tuple[StateDelta, list[str]]` — moved from `state/delta.py`
- `_merge_arc_update(arc, arc_update) -> CampaignArc | None` — moved from `state/delta.py`

The old functions in `state/delta.py` become thin wrappers that delegate to `delta_builder.py` using an in-function import (e.g., `from ccya.state.delta_builder import apply_delta as _apply_delta; return _apply_delta(state, delta)`) to avoid circular re-import.

**File:** `ccya/engine/extraction.py`

**What:** Change the local import from `from ccya.state.delta import apply_delta` to a top-level import `from ccya.state.delta_builder import apply_delta`. Remove the local import.

**File:** `ccya/engine/turn.py`

**What:** Change `from ccya.state.delta import _merge_arc_update` to `from ccya.state.delta_builder import _merge_arc_update`. The private function import remains non-ideal, but this at least removes the circular dependency pressure.

**Why:** The circular dependency exists because both `engine` and `state` need to share state-manipulation code during extraction. Moving the delta application logic to a third module that both can import breaks the cycle.

**Validation:** Remove the local import from `extraction.py:74`. Confirm no module fails to import. `make check && make test` passes.

### Tests to write or update

- Update existing test imports that reference `ccya.state.delta.apply_delta` to import from `ccya.state.delta_builder`.

### REPOMAP updates required

- `ccya/state/delta_builder.py`: New file — added to REPOMAP.
- `ccya/state/delta.py`: Remove moved functions, keep thin wrappers with in-function imports.
- `ccya/state/__init__.py`: Update re-exports — `reconcile_delta` is imported from `ccya.state.delta_builder` now, not `ccya.state.delta`. Both `delta.py` (thin wrapper) and `delta_builder.py` must be in the import chain, or change the export to point directly at `delta_builder`.
- `ccya/engine/extraction.py`: Update import path.
- `ccya/engine/turn.py`: Update import path.

---

## Implementation — Phase 4: Add state schema versioning

### Context files to read
- `ccya/state/io.py` — `_default_state()` (line 28), `save_state()` (line 46), `load_state()` (line 78)

### Detailed steps

#### Step 4.1 — Add schema version to default state

**File:** `ccya/state/io.py`

**What:** Add `"schema_version": 1` to the dict returned by `_default_state()`.

**Why:** Without a version field, any future schema change requires ad-hoc regex fixes (like the one already at line 87-92). A version field enables migration checks on load.

**Validation:** `python3 -c "from ccya.state.io import _default_state; print(_default_state().get('schema_version'))"` prints `1`.

#### Step 4.2 — Add version check to load_state()

**File:** `ccya/state/io.py`

**What:** In `load_state()`, after loading the YAML (line 86), check for `schema_version`:

```python
# Schema version migration
loaded_version = state.get("schema_version", 0)
if loaded_version == 0:
    # Legacy file — apply known migration(s), then upgrade version
    state = _migrate_v0_to_v1(state)
elif loaded_version > CURRENT_SCHEMA_VERSION:
    _log.warning(
        "state schema version %d is newer than engine version %d — loading anyway",
        loaded_version, CURRENT_SCHEMA_VERSION,
    )
```

Define `CURRENT_SCHEMA_VERSION = 1` at module level. Define `_migrate_v0_to_v1()` that applies the existing regex fix (line 87-92) and any other known migrations.

**Why:** The existing regex fix for old YAML serialization is fragile (assumes specific indentation). A structured migration function can handle the same case with clear error messages and extend to future migrations.

**Validation:** Load a legacy state file (no `schema_version`). Confirm it passes through `_migrate_v0_to_v1` and loads successfully. Save a new state file — confirm `schema_version: 1` is written.

### Tests to write or update

- `tests/test_state_io.py`: Test loading a legacy state file (no schema_version) and confirm it migrates to version 1. Test loading a state file with a newer version and confirm the warning fires. Test that a freshly created state file has `schema_version: 1`.

### REPOMAP updates required

- `ccya/state/io.py`: Add `CURRENT_SCHEMA_VERSION`, `_migrate_v0_to_v1()`, update `_default_state()` and `load_state()`.
