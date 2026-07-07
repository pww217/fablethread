# Plan: Engine Model and Pipeline Naming Audit (I-29)

**Status: scoping**

**Ticket:** I-29

## Design Reference

`roadmap/improvements/I-29-engine-model-naming-audit.md`

## Purpose

Rename engine models, extraction results, pipeline context types, and seed models to match their role in the pipeline. Each rename is mechanical find/replace — no behavior changes.

## Constraints

- No behavioral change — all renames are purely naming
- Each phase independently verifiable with `make check`
- Each phase touches a shared concern (same module/state-shape)
- Each phase declares dependencies on prior phases

## Risks, Ambiguities, and Blockers

- `SanitizedWorldStateFact` vs `WorldStateFact` merge: The ticket suggests merging or renaming to `ConfirmedWorldFact`. The two classes have identical schemas. Decision point: merge into `WorldStateFact` (simpler) or rename to `ConfirmedWorldFact` (preserves semantic distinction). Plan assumes merge into `WorldStateFact` — the sanitizer output is still a `WorldStateFact`, just one that passed sanitizer validation.
- `SeedStateEnvelope` vs `SeedEnvelope` merge: The ticket says "nearly identical" but grep shows they serve different purposes — `SeedStateEnvelope` wraps `SeedState` without narrative min_length constraints, `SeedEnvelope` wraps `SeedState` + narrative fields. The merge may not be safe. Plan defers this to Phase 6 for careful review.
- `TurnResult` move: Moving from `models/config.py` to `turn.py` changes import paths across the codebase. Each import site needs updating.

## Phases

### Phase 1: Core models (`StorytellerResult` → `RecordResult`, `StateDelta` → `StateMerge`)

**Dependencies:** None

### Phase 2: Extraction pipeline internals (`_ExtractionResult` → `_ExtractionAccumulator`, `_ExtractionVariant` → `_ExtractionStreamConfig`, `_ExtractionContext` → `_PostDeltaContext`, `ExtractResult` → `ExtractionResult`)

**Dependencies:** Phase 1

### Phase 3: Turn pipeline results & prompt context blocks

**Dependencies:** Phase 1

### Phase 4: Seed pipeline

**Dependencies:** Phase 1

### Phase 5: Cascading renames (parameter names, docstrings, configs)

**Dependencies:** Phase 1

### Phase 6: Cross-cutting audit (ev checkers, server, scripts, prompt templates, state I/O)

**Dependencies:** All previous phases

### Phase 7: Docs & cleanup

**Dependencies:** All previous phases

---

## Implementation — Phase 1: Core models

### Context files to load

- `ccya/models/extraction.py` lines 83-90 (`StateDelta`), lines 216-270 (`StorytellerResult`)
- `ccya/models/__init__.py` lines 10-11 (exports)
- `ccya/engine/extraction/pipeline.py` lines 1-30 (imports), lines 142-331 (usages)
- `ccya/engine/extraction/context.py` lines 1-10 (imports), line 46 (usage)
- `ccya/engine/turn_state.py` lines 1-20 (imports), lines 19-531 (parameter names)
- `ccya/engine/turn.py` lines 1-40 (imports), lines 84-549 (parameter names)
- `ccya/state/delta_builder.py` lines 1-15 (imports), lines 67-113 (parameter names)
- `ccya/pack.py` line 64 (comment)
- `docs/architecture/OVERVIEW.md` lines 67-70, 138-159
- `docs/architecture/state-models.md` lines 64-90, 100, 128-129
- `docs/architecture/cross-module-contracts.md` lines 54-55, 69
- `docs/architecture/step2c-record.md` lines 5-25, 91-93, 100, 200-247
- `docs/architecture/delta-validate.md` lines 1-19
- `docs/architecture/cross-pipeline.md` line 28
- `docs/repomap.md` lines 22, 132
- `docs/ev/STATE-REFERENCE.md` lines 163, 215
- `docs/engine-overhaul-checklist.md` lines 12, 75-76, 87-88, 94, 132-134, 242-244, 256-257, 260-261
- `README.md` line 189

### Detailed steps

#### Step 1.1 — Rename `StorytellerResult` → `RecordResult`

**File:** `ccya/models/extraction.py`

**What:** Rename class `StorytellerResult` to `RecordResult` (line 216). Update self-referencing type annotations: `_nullify_empty_arc_resolve(self) -> "RecordResult"`, `_nullify_empty_thread_add(self) -> "RecordResult"`, `_warn_empty_actions(self) -> "RecordResult"`.

**Why:** The step was renamed from "Storytell" to "Record" but the Pydantic class name lingers.

**Validation:** `make check` passes.

#### Step 1.2 — Rename `StateDelta` → `StateMerge`

**File:** `ccya/models/extraction.py`

**What:** Rename class `StateDelta` to `StateMerge` (line 83).

**Why:** It's a merge container for heterogeneous extraction results, not a traditional state delta/diff. Arch docs already call it "StateMerge schema".

**Validation:** `make check` passes.

#### Step 1.3 — Update exports in `ccya/models/__init__.py`

**File:** `ccya/models/__init__.py`

**What:** Update exports:
- `StateDelta as StateMerge` (line 11)
- `StorytellerResult as RecordResult` (line 11)

**Why:** All downstream imports go through `__init__.py`.

**Validation:** `make check` passes.

#### Step 1.4 — Update `engine/extraction/pipeline.py`

**File:** `ccya/engine/extraction/pipeline.py`

**What:**
- Imports: `StateMerge` (line 27), `RecordResult` (line 29)
- Line 142: `StateMerge` in return type annotation, `RecordResult` in return type annotation
- Line 162: `RecordResult()` → `RecordResult()`
- Line 183: `RecordResult()` → `RecordResult()`
- Line 186: `StateDelta` → `StateMerge`
- Line 226-227: `StateDelta(` → `StateMerge(`
- Line 264: `StateDelta(` → `StateMerge(`
- Line 288: `StateDelta(` → `StateMerge(`
- Line 318: `RecordResult` → `RecordResult`
- Line 331: `RecordResult()` → `RecordResult()`

**Why:** All usages of the renamed models.

**Validation:** `make check` passes.

#### Step 1.5 — Update `engine/extraction/context.py`

**File:** `ccya/engine/extraction/context.py`

**What:**
- Import: `StateMerge` (line 9)
- Line 46: `StateDelta(` → `StateMerge(`

**Why:** Context builds a StateMerge from scene+state stream results.

**Validation:** `make check` passes.

#### Step 1.6 — Update `engine/turn_state.py`

**File:** `ccya/engine/turn_state.py`

**What:**
- Import: `RecordResult`, `StateMerge` (line 9)
- Parameter renames: `storyteller_result: RecordResult` (lines 19, 171, 231)
- Parameter renames: `delta: StateMerge | None` (lines 314, 421, 427)
- All references to `storyteller_result` parameter name: `storyteller_result.thread_update` → `record_result.thread_update`, `storyteller_result.arc_resolve` → `record_result.arc_resolve`, `storyteller_result.thread_resolve` → `record_result.thread_resolve`, `storyteller_result.thread_add` → `record_result.thread_add`, `storyteller_result.goal_update` → `record_result.goal_update`, `storyteller_result.actions` → `record_result.actions`
- All references to `delta` parameter name: `delta.location_change` → `delta.location_change`, etc.

**Why:** All functions that process Record output and merge deltas.

**Validation:** `make check` passes.

#### Step 1.7 — Update `engine/turn.py`

**File:** `ccya/engine/turn.py`

**What:**
- Import: `RecordResult`, `StateMerge` (lines 39-40)
- Parameter renames: `delta: StateMerge | None` (lines 84, 402, 500, 503, 549)

**Why:** Turn pipeline uses RecordResult and StateMerge.

**Validation:** `make check` passes.

#### Step 1.8 — Update `state/delta_builder.py`

**File:** `ccya/state/delta_builder.py`

**What:**
- Import: `StateMerge` (line 14)
- Parameter renames: `delta: StateMerge` (lines 67, 113)
- Comment on line 277: "Persist storyteller actions" → "Persist record actions"

**Why:** Delta builder applies merge results to state.

**Validation:** `make check` passes.

#### Step 1.9 — Update `pack.py`

**File:** `ccya/pack.py`

**What:** Comment on line 64: "StateDelta.inventory_add" → "StateMerge.inventory_add"

**Why:** Outdated reference.

**Validation:** `make check` passes.

#### Step 1.10 — Update `engine/_pacing.py`

**File:** `ccya/engine/_pacing.py`

**What:** Module docstring line 5: "storytell context" → "record context"

**Why:** Outdated after step rename.

**Validation:** `make check` passes.

#### Step 1.11 — Update arch docs

**Files:** All docs listed above

**What:**
- `docs/architecture/OVERVIEW.md`: `StorytellerResult` → `RecordResult` (lines 67, 138), `StateDelta` → `StateMerge` (lines 70, 157, 159)
- `docs/architecture/state-models.md`: `StorytellerResult` → `RecordResult` (lines 64, 90, 116), `StateDelta` → `StateMerge` (lines 86-88, 129)
- `docs/architecture/cross-module-contracts.md`: `StorytellerResult` → `RecordResult` (line 54), `StateDelta` → `StateMerge` (line 55)
- `docs/architecture/step2c-record.md`: `StorytellerResult` → `RecordResult` (lines 5, 25, 28, 91)
- `docs/architecture/delta-validate.md`: `StateDelta` → `StateMerge` (lines 3, 17-19)
- `docs/architecture/cross-pipeline.md`: `StateDelta` → `StateMerge` (line 28)
- `docs/repomap.md`: `StorytellerResult` → `RecordResult` (lines 22, 132)
- `docs/ev/STATE-REFERENCE.md`: `StorytellerResult` → `RecordResult` (line 163), `StateDelta` → `StateMerge` (line 215)
- `docs/engine-overhaul-checklist.md`: All references updated
- `README.md`: `StateDelta` → `StateMerge` (line 189)

**Why:** Arch docs must reflect new names.

**Validation:** `make check` passes.

#### Step 1.12 — Update test files (deferred)

**Files:** `tests/test_schema.py`, `tests/test_smoke.py`

**What:**
- `test_schema.py` line 28: `RecordResult` import, lines 470-516, 574: `RecordResult` usages
- `test_smoke.py` line 64: `state_merge` reference

**Why:** Tests import and use the renamed models.

**Validation:** `make check` passes.

> **Note:** AGENTS.md says "Tests are temporarily removed during refactor." Keep test refs as reminder to update when tests return.

### Verification

- `make check` passes (lint + typecheck)
- Grep for `StorytellerResult` returns 0 matches in `ccya/` (only in git history)
- Grep for `StateDelta` returns 0 matches in `ccya/` (only in git history)
- All imports resolve correctly

---

## Implementation — Phase 2: Extraction pipeline internals

### Context files to load

- `ccya/engine/extraction/pipeline.py` lines 1-15 (imports), lines 37-63 (class definitions), lines 142-316 (usages)
- `ccya/engine/extraction/context.py` lines 1-15 (imports), line 15 (class definition), line 36 (class definition), line 65 (class usage)
- `ccya/engine/extraction/record.py` lines 1-11 (imports), line 25 (parameter)
- `ccya/engine/turn.py` lines 152-225 (class usages), lines 287-560 (class definitions)
- `docs/architecture/OVERVIEW.md` line 108
- `docs/ev/STATE-REFERENCE.md` lines 80, 211
- `docs/engine-overhaul-checklist.md` line 81
- `docs/design/complete/prompt/narration-simplification-design.md` lines 25, 53, 168, 201, 227-228, 354
- `docs/design/complete/tooling-infra/engine-file-splitting-design.md` lines 113, 213, 383

### Detailed steps

#### Step 2.1 — Rename `_ExtractionResult` → `_ExtractionAccumulator`

**File:** `ccya/engine/extraction/pipeline.py`

**What:** Rename class `_ExtractionResult` to `_ExtractionAccumulator` (line 37). Update:
- Field `extraction_ctx: _PostDeltaContext | None = None` (line 41) — references `_PostDeltaContext` from Step 2.3
- All usages: `container = _ExtractionAccumulator()` (line 164), `container: _ExtractionAccumulator` (lines 256, 280, 313)

**Why:** It's an accumulator for three extraction streams, not a result.

**Validation:** `make check` passes.

#### Step 2.2 — Rename `_ExtractionVariant` → `_ExtractionStreamConfig`

**File:** `ccya/engine/extraction/pipeline.py`

**What:** Rename class `_ExtractionVariant` to `_ExtractionStreamConfig` (line 45). Update:
- Parameter `variant: _ExtractionStreamConfig` (line 59)
- All usages: `variant = _ExtractionStreamConfig(` (lines 258, 282, 316)

**Why:** It's a stream configuration descriptor, not a variant.

**Validation:** `make check` passes.

#### Step 2.3 — Rename `_ExtractionContext` → `_PostDeltaContext`

**File:** `ccya/engine/extraction/context.py`

**What:** Rename class `_ExtractionContext` to `_PostDeltaContext` (line 15). Update:
- `_build_extraction_context` return type: `_PostDeltaContext` (line 36)
- All usages: `_PostDeltaContext(` (line 65)

**File:** `ccya/engine/extraction/pipeline.py`

**What:** Update import: `_PostDeltaContext` (line 15). Update return type annotation: `_PostDeltaContext` (line 142).

**File:** `ccya/engine/extraction/record.py`

**What:** Update import: `_PostDeltaContext` (line 11). Update parameter: `extraction_ctx: _PostDeltaContext` (line 25).

**File:** `ccya/engine/extraction/context.py`

**What:** Rename function `_build_extraction_context` → `_build_post_delta_context` (line 32). Update return type: `_PostDeltaContext` (line 36). Update all callers.

**Why:** It carries post-delta scene+state derived state into Record. The docstring still says "storytell stream" — the rename implicitly fixes that.

**Validation:** `make check` passes.

#### Step 2.4 — Rename `ExtractResult` → `ExtractionResult`

**File:** `ccya/engine/turn.py`

**What:** Rename class `ExtractResult` to `ExtractionResult` (line 548). Update:
- `_extract_phase` parameter: `extract_result: ExtractionResult` (line 393)
- All usages: `_extract_result_container = ExtractionResult()` (line 183)

**Why:** It's the merged result from all three extraction streams, not a single extraction result.

**Validation:** `make check` passes.

#### Step 2.5 — Update arch docs

**Files:** All docs listed above

**What:**
- `docs/architecture/OVERVIEW.md` line 108: `_ExtractionContext` → `_PostDeltaContext`
- `docs/ev/STATE-REFERENCE.md` lines 80, 211: `_ExtractionContext` → `_PostDeltaContext`
- `docs/engine-overhaul-checklist.md` line 81: `_ExtractionContext` → `_PostDeltaContext`
- `docs/design/complete/prompt/narration-simplification-design.md`: All references updated
- `docs/design/complete/tooling-infra/engine-file-splitting-design.md` lines 113, 213, 383: `_ExtractionContext` → `_PostDeltaContext`

**Why:** Arch docs must reflect new names.

**Validation:** `make check` passes.

### Verification

- `make check` passes
- Grep for `_ExtractionResult` returns 0 matches in `ccya/`
- Grep for `_ExtractionVariant` returns 0 matches in `ccya/`
- Grep for `_ExtractionContext` returns 0 matches in `ccya/`
- Grep for `ExtractResult` returns 0 matches in `ccya/` (only `SceneExtractResult`, `StateExtractResult` remain)

---

## Implementation — Phase 3: Turn pipeline results & prompt context blocks

### Context files to load

- `ccya/engine/turn.py` lines 1-10 (imports), lines 152-153 (class usages), lines 225-226 (class usages), lines 287-288 (class usages), lines 537-563 (class definitions), lines 580-581 (parameter)
- `ccya/prompts/context.py` lines 77-192 (class definitions), lines 123-124, 131-135, 147, 158, 162, 170, 173-175, 189-192, 248 (usages)
- `docs/architecture/OVERVIEW.md` line 100-101 (NarrateResult/PersistResult references)
- `docs/ev/STATE-REFERENCE.md` lines 140-141 (NarrateResult/PersistResult references)
- `docs/engine-overhaul-checklist.md` lines 94-96 (NarrateResult/PersistResult references)

### Detailed steps

#### Step 3.1 — Rename `NarrateResult` → `NarrationResult`

**File:** `ccya/engine/turn.py`

**What:** Rename class `NarrateResult` to `NarrationResult` (line 537). Update:
- Line 152: `_narrate_result = NarrateResult()` → `_narrate_result = NarrationResult()`
- Line 225: `_narrate_result = NarrateResult()` → `_narrate_result = NarrationResult()`
- Line 287: `_narrate_phase(ctx: TurnContext, narrate_result: NarrateResult)` → `_narrate_phase(ctx: TurnContext, narrate_result: NarrationResult)`

**Why:** The name should match the phase name "narrate" → "narration" for consistency.

**Validation:** `make check` passes.

#### Step 3.2 — Rename `PersistResult` → `TurnCompleteResult`

**File:** `ccya/engine/turn.py`

**What:** Rename class `PersistResult` to `TurnCompleteResult` (line 560). Update:
- Line 225: `_persist_result = PersistResult()` → `_persist_result = TurnCompleteResult()`
- Line 580: `persist_result: PersistResult` → `persist_result: TurnCompleteResult`

**Why:** The class represents the result of persisting a turn, not a generic "persist" operation. `TurnCompleteResult` better describes its role.

**Validation:** `make check` passes.

#### Step 3.3 — Rename `WorldStateBlock` → `WorldFactsBlock`

**File:** `ccya/prompts/context.py`

**What:** Rename class `WorldStateBlock` to `WorldFactsBlock` (line 167). Update:
- Line 170: `entries: list[str]` comment: "raw world state strings from scene.world_state[]" → "raw world facts from scene.world_facts[]"
- Line 173-175: `from_state` method return type and implementation: `WorldStateBlock` → `WorldFactsBlock`, `state.get("scene", {}).get("world_state", [])` → `state.get("scene", {}).get("world_facts", [])`

**File:** `ccya/prompts/context.py`

**What:** Update `NarratorBoundary` class:
- Line 246: `state: dict[str, Any]` comment: "covers state.location, state.inventory, state.scene.world_state" → "covers state.location, state.inventory, state.scene.world_facts"

**File:** `tests/test_schema.py`

**What:** Update:
- Line 47: `WorldStateBlock` import → `WorldFactsBlock`
- Lines 161-171: All `WorldStateBlock` usages → `WorldFactsBlock`

**Why:** The block represents world facts, not the full world state. The field name `Scene.world_state` is also being renamed to `world_facts` in Phase 4.

**Validation:** `make check` passes.

> **Note:** AGENTS.md says "Tests are temporarily removed during refactor." Keep test refs as reminder to update when tests return.

#### Step 3.4 — Rename `PacingBlock` → `DirectiveBlock`

**File:** `ccya/prompts/context.py`

**What:** Rename class `PacingBlock` to `DirectiveBlock` (line 189). Update:
- Line 192: `directive: str | None = None` comment: "used by narrate_user.j2 line 80"
- Line 248: `pacing_context: PacingBlock | None = None` → `pacing_context: DirectiveBlock | None = None`

**Why:** The block represents the pacing directive, not general pacing context. The field name `directive` already exists on the class.

**Validation:** `make check` passes.

#### Step 3.5 — Rename `ArcThreadSummary` → `ArcThreadSummaryItem`

**File:** `ccya/prompts/context.py`

**What:** Rename class `ArcThreadSummary` to `ArcThreadSummaryItem` (line 77). Update:
- Line 123: `threads: list[ArcThreadSummary]` → `threads: list[ArcThreadSummaryItem]`
- Line 124: `completed_threads: list[ArcThreadSummary]` → `completed_threads: list[ArcThreadSummaryItem]`
- Lines 131-135, 147, 158, 162: All `ArcThreadSummary` usages → `ArcThreadSummaryItem`

**File:** `tests/test_schema.py`

**What:** Update:
- Line 32: `ArcThreadSummary` import → `ArcThreadSummaryItem`
- Lines 120-128, 155: All `ArcThreadSummary` usages → `ArcThreadSummaryItem`

**Why:** The class represents a single item in the thread summary list, not the summary itself. The parent class `ArcThreadBlock` already represents the summary container.

**Validation:** `make check` passes.

> **Note:** AGENTS.md says "Tests are temporarily removed during refactor." Keep test refs as reminder to update when tests return.

### Verification

- `make check` passes
- Grep for `NarrateResult` returns 0 matches in `ccya/`
- Grep for `PersistResult` returns 0 matches in `ccya/`
- Grep for `WorldStateBlock` returns 0 matches in `ccya/`
- Grep for `PacingBlock` returns 0 matches in `ccya/`
- Grep for `ArcThreadSummary` returns 0 matches in `ccya/`

---

## Implementation — Phase 4: Seed pipeline

### Context files to load

- `ccya/models/state.py` lines 56-66 (`Scene` class), line 58 (`world_state` field)
- `ccya/pack.py` lines 22-29 (`SeedPC`), lines 56-59 (`SeedScene`), lines 61-78 (`SeedState`)
- `ccya/engine/seed.py` lines 1-100 (usages), lines 360-374 (world_state usages)
- `ccya/engine/turn.py` lines 130-135 (world_state usages)
- `ccya/engine/thread_sanitizer.py` lines 148-151 (world_state usages)
- `ccya/engine/changes.py` lines 192-193 (world_state usages)
- `ccya/engine/_pacing.py` line 314 (world_state usages)
- `ccya/engine/extraction/record.py` line 58 (world_state usages)
- `ccya/prompts/context.py` lines 170, 173-175, 246 (world_state usages)
- `ccya/ev/checkers/state.py` lines 72, 98-102 (world_state usages)
- `docs/architecture/state-models.md` lines 78-80, 118-119 (Scene.world_state references)
- `docs/architecture/out-of-band.md` line 54 (Scene.world_state reference)

### Detailed steps

#### Step 4.1 — Rename `Scene.world_state` → `Scene.world_facts`

**File:** `ccya/models/state.py`

**What:** Rename field `world_state` to `world_facts` in `Scene` class (line 58).

**Why:** The field contains world facts, not the full world state. Aligns with `WorldFactsBlock` rename from Phase 3.

**Validation:** `make check` passes.

#### Step 4.2 — Update all `Scene.world_state` usages

**File:** `ccya/engine/turn.py`

**What:** Line 133: `state.scene.world_state` → `state.scene.world_facts`

**File:** `ccya/engine/thread_sanitizer.py`

**What:** Line 151: `state.scene.world_state` → `state.scene.world_facts`

**File:** `ccya/engine/changes.py`

**What:** Lines 192-193: `pre.scene.world_state` → `pre.scene.world_facts`, `post.scene.world_state` → `post.scene.world_facts`

**File:** `ccya/engine/_pacing.py`

**What:** Line 314: `world_state=list(scene.world_state)` → `world_facts=list(scene.world_facts)`

**File:** `ccya/engine/extraction/record.py`

**What:** Line 58: `world_state = list(scene.world_state)` → `world_facts = list(scene.world_facts)`

**File:** `ccya/models/state.py`

**What:** Line 210: `self.scene.world_state` in `WorldState.expire_conditions()` → `self.scene.world_facts`

**File:** `ccya/prompts/context.py`

**What:** Line 170: comment "raw world state strings from scene.world_state[]" → "raw world facts from scene.world_facts[]"
- Line 175: `state.get("scene", {}).get("world_state", [])` → `state.get("scene", {}).get("world_facts", [])`
- Line 246: comment "covers state.location, state.inventory, state.scene.world_state" → "covers state.location, state.inventory, state.scene.world_facts"

**File:** `ccya/ev/checkers/state.py`

**What:** Line 72: `requires_fields=["last_turn_state.scene.world_state"]` → `requires_fields=["last_turn_state.scene.world_facts"]`

**Why:** All downstream consumers of the scene's world facts field.

**Validation:** `make check` passes.

#### Step 4.3 — Rename `SeedScene.world_state` → `SeedScene.world_facts`

**File:** `ccya/pack.py`

**What:** Line 58: `world_state: list[WorldStateFact | str]` → `world_facts: list[WorldStateFact | str]`

**File:** `ccya/engine/seed.py`

**What:** Lines 47-49: `seed_state.scene.world_state` → `seed_state.scene.world_facts`
- Line 363: `state_envelope.seed_state.scene.world_state` → `state_envelope.seed_state.scene.world_facts`
- Line 374: `state_envelope.seed_state.scene.world_state` → `state_envelope.seed_state.scene.world_facts`

**Why:** Seed scene's world facts field needs the same rename.

**Validation:** `make check` passes.

#### Step 4.4 — Rename `SeedPC.drive` → `SeedPC.directive`

**File:** `ccya/pack.py`

**What:** Line 28: `drive: str = ""` → `directive: str = ""`

**Why:** The field represents the PC's directive, not a drive. Aligns with `PacingBlock` → `DirectiveBlock` rename from Phase 3.

**Validation:** `make check` passes.

#### Step 4.5 — Rename `SeedState.world` → `SeedState.world_info`

**File:** `ccya/pack.py`

**What:** Line 77: `world: dict[str, Any]` → `world_info: dict[str, Any]`

**Why:** The field contains world information, not the full world state. The name `world` is too generic and conflicts with the `World` model in state.py.

**Validation:** `make check` passes.

### Verification

- `make check` passes
- Grep for `Scene\.world_state` returns 0 matches in `ccya/`
- Grep for `SeedScene\.world_state` returns 0 matches in `ccya/`
- Grep for `SeedPC\.drive` returns 0 matches in `ccya/`
- Grep for `SeedState\.world` returns 0 matches in `ccya/`

---

## Implementation — Phase 5: Cascading renames

### Context files to load

- `ccya/engine/turn_state.py` lines 1-15 (imports), lines 19-170, 171-230, 231-310, 421-531 (parameter names)
- `ccya/state/delta_builder.py` lines 1-15 (imports), lines 67-113 (parameter names)
- `ccya/models/config.py` lines 1-50 (`TurnResult` dataclass)
- `ccya/engine/turn.py` lines 1-10 (imports), lines 270-271, 561, 718-719 (TurnResult usages)
- `ccya/models/__init__.py` line 14 (TurnResult export)
- `ccya/ev/play.py` lines 15-16 (imports), lines 72-73 (TurnResult usages)
- `ccya/errors.py` line 7 (TurnResult reference)
- `tests/test_integration.py` lines 4-5, 91, 118, 169, 252, 317 (TurnResult references)
- `tests/test_smoke.py` lines 4-5, 54-74, 124-141 (TurnResult references)
- `docs/architecture/state-models.md` line 100 (TurnResult reference)
- `docs/architecture/logging-standards.md` line 55 (TurnResult reference)
- `docs/architecture/cross-module-contracts.md` line 9 (TurnResult reference)

### Detailed steps

#### Step 5.1 — Rename `storyteller_result` parameter → `record_result`

**File:** `ccya/engine/turn_state.py`

**What:** Rename parameter `storyteller_result` to `record_result` in:
- `_apply_thread_updates` (line 19): `storyteller_result: StorytellerResult` → `record_result: RecordResult`
- `_apply_arc_resolve` (line 171): `storyteller_result: StorytellerResult` → `record_result: RecordResult`
- `_apply_thread_resolutions` (line 231): `storyteller_result: StorytellerResult` → `record_result: RecordResult`
- `_apply_state_updates` (line 422): `storyteller_result: StorytellerResult | None` → `record_result: RecordResult | None`
- All references within these functions: `storyteller_result.thread_update` → `record_result.thread_update`, `storyteller_result.arc_resolve` → `record_result.arc_resolve`, `storyteller_result.thread_resolve` → `record_result.thread_resolve`, `storyteller_result.thread_add` → `record_result.thread_add`, `storyteller_result.goal_update` → `record_result.goal_update`, `storyteller_result.actions` → `record_result.actions`

**Why:** The parameter name should match the new class name `RecordResult` from Phase 1.

**Validation:** `make check` passes.

#### Step 5.2 — Rename `state_delta` parameter → `state_merge`

**File:** `ccya/state/delta_builder.py`

**What:** Rename type annotations from `StateDelta` → `StateMerge`:
- `reconcile_delta` (line 67): `delta: StateDelta` → `delta: StateMerge`
- `apply_delta` (line 113): `delta: StateDelta` → `delta: StateMerge`

**Why:** The parameter name should match the new class name `StateMerge` from Phase 1.

**Validation:** `make check` passes.

#### Step 5.3 — Move `TurnResult` from `models/config.py` to `turn.py`

**File:** `ccya/models/config.py`

**What:** Delete the `TurnResult` dataclass definition (lines 24-49). Keep `load_config` and `save_config` functions.

**File:** `ccya/engine/turn.py`

**What:** Append the `TurnResult` dataclass definition at the end of the file (after `TurnCompleteResult`).

**File:** `ccya/models/__init__.py`

**What:** Update import:
- Remove: `from ccya.models.config import ... TurnResult as TurnResult ...` (line 14)
- Add: `from ccya.engine.turn import TurnResult as TurnResult`

**File:** `ccya/engine/turn.py`

**What:** Update import:
- Remove: `from ccya.models import TurnResult` (line 40)
- The `TurnResult` is now defined in this file, so no import needed

**File:** `ccya/ev/play.py`

**What:** Update import:
- Line 15: `from ccya.models import TurnResult` → `from ccya.engine.turn import TurnResult`

**File:** `ccya/errors.py`

**What:** Update comment on line 7: "like TurnResult.errors" stays the same (no code reference, just comment)

**File:** `tests/test_integration.py`

**What:** Update import:
- Line 4: `TurnResult` import → `from ccya.engine.turn import TurnResult`

**File:** `tests/test_smoke.py`

**What:** Update import:
- Line 4-5: `TurnResult` import → `from ccya.engine.turn import TurnResult`

**Why:** `TurnResult` is a turn pipeline result, not a config type. Moving it to `turn.py` is more semantically correct.

**Validation:** `make check` passes.

> **Note:** AGENTS.md says "Tests are temporarily removed during refactor." Keep test refs as reminder to update when tests return.

#### Step 5.4 — Rename `TurnResult.state_delta` field → `TurnResult.state_merge`

**File:** `ccya/models/config.py`

**What:** Rename the `state_delta: dict[str, Any]` field (line 29) to `state_merge: dict[str, Any]`.

**File:** `ccya/engine/turn.py`

**What:** Update `TurnResult` constructor calls:
- Line 274: `state_delta={}` → `state_merge={}`
- Line 722: `state_delta=applied` → `state_merge=applied`

**Why:** The field holds the merge result (renamed from `StateDelta` in Phase 1), not a traditional delta/diff.

**Validation:** `make check` passes.

### Verification

- `make check` passes
- Grep for `storyteller_result` returns 0 matches in `ccya/`
- Grep for `state_delta` parameter returns 0 matches in `ccya/` (only `TurnResult.state_delta` field remains)
- `TurnResult` is importable from `ccya.engine.turn`
- `TurnResult` is NOT importable from `ccya.models.config`

---

## Implementation — Phase 6: Cross-cutting audit

### Context files to load

- `ccya/ev/checkers/state.py` lines 1-100 (world_state references)
- `ccya/server/routes.py` lines 470-529 (SeedEnvelope usages)
- `ccya/ev/play.py` lines 268-281 (SeedEnvelope usages)
- `ccya/state/io.py` lines 1-76 (state I/O)
- `ccya/prompts/` directory (prompt templates)
- `ccya/engine/thread_sanitizer.py` lines 1-15 (SanitizedWorldStateFact import), lines 296-312, 480 (SanitizedWorldStateFact usages)
- `ccya/engine/seed.py` lines 17-18 (WorldStateFact import), lines 369-372 (WorldStateFact usages)
- `ccya/pack.py` line 16 (WorldStateFact import)
- `docs/architecture/state-models.md` lines 78-80, 118-119 (SanitizedWorldStateFact references)
- `docs/architecture/out-of-band.md` line 54 (Scene.world_state reference)

### Detailed steps

#### Step 6.1 — Merge `SanitizedWorldStateFact` into `WorldStateFact`

**File:** `ccya/models/state.py`

**What:** Delete the `SanitizedWorldStateFact` class (lines 412-419). All references to `SanitizedWorldStateFact` should use `WorldStateFact` instead.

**Why:** The two classes have identical schemas. The "sanitized" prefix is misleading — the thread sanitizer validates facts but the output is still a `WorldStateFact`. The validation happens at the point of use, not in the type itself.

**File:** `ccya/models/__init__.py`

**What:** Remove `SanitizedWorldStateFact` from exports (line 5).

**File:** `ccya/engine/thread_sanitizer.py`

**What:** Update import: `SanitizedWorldStateFact` → `WorldStateFact` (line 14)
- Line 296: comment "validate each entry against SanitizedWorldStateFact" → "validate each entry against WorldStateFact"
- Line 312: `SanitizedWorldStateFact.model_validate(ws_copy)` → `WorldStateFact.model_validate(ws_copy)`
- Line 480: `SanitizedWorldStateFact(**ws)` → `WorldStateFact(**ws)`

**File:** `ccya/engine/seed.py`

**What:** Update import: `WorldStateFact` stays the same (line 17)

**File:** `ccya/pack.py`

**What:** Update import: `WorldStateFact` stays the same (line 16)

**Validation:** `make check` passes.

#### Step 6.2 — Update ev checkers

**File:** `ccya/ev/checkers/state.py`

**What:** Line 72: `requires_fields=["last_turn_state.scene.world_state"]` → `requires_fields=["last_turn_state.scene.world_facts"]`

**Why:** The scene field was renamed to `world_facts` in Phase 4.

**Validation:** `make check` passes.

#### Step 6.3 — Update server routes

**File:** `ccya/server/routes.py`

**What:** Review SeedEnvelope usages (lines 479-486, 519-526) for any field references that need updating. The `SeedEnvelope` model wraps `SeedState` + narrative fields, so no changes expected if the merge was deferred.

**Why:** Verify no field references need updating after Phase 4 renames.

**Validation:** `make check` passes.

#### Step 6.4 — Update ev/play.py

**File:** `ccya/ev/play.py`

**What:** Review SeedEnvelope usages (lines 276-281) for any field references that need updating.

**Why:** Verify no field references need updating after Phase 4 renames.

**Validation:** `make check` passes.

#### Step 6.5 — Update prompt templates

**File:** `ccya/prompts/` directory

**What:** Update specific template references:
- `narrate_user.j2` line 19: `{% if scene.world_state -%}` → `{% if scene.world_facts -%}`
- `sections/_world_state.j2` line 2: comment "state (dict with scene.world_state)" → "state (dict with scene.world_facts)"
- `sections/_world_state.j2` line 6: `{% for fact in (state.scene.world_state or []) %}` → `{% for fact in (state.scene.world_facts or []) %}`
- `templates/_state_right.html` lines 91-95: `state.scene.world_state` → `state.scene.world_facts`

**Why:** Prompt templates may reference the renamed fields.

**Validation:** `make check` passes.

#### Step 6.6 — Update state I/O

**File:** `ccya/state/io.py`

**What:** Review state loading/saving for any field references that need updating. The `WorldState` model uses `Scene` which has `world_facts` now.

**Why:** Verify serialization/deserialization still works with renamed fields.

**Validation:** `make check` passes.

### Verification

- `make check` passes
- Grep for `SanitizedWorldStateFact` returns 0 matches in `ccya/`
- Grep for `scene\.world_state` returns 0 matches in `ccya/`
- All prompt templates updated
- All ev checkers updated

---

## Implementation — Phase 7: Docs & cleanup

### Context files to load

- All `docs/architecture/` markdown files
- `docs/repomap.md`
- `docs/ev/STATE-REFERENCE.md`
- `docs/engine-overhaul-checklist.md`
- `docs/design/` directory
- `README.md`
- All `plans/` directory files

### Detailed steps

#### Step 7.1 — Update architecture docs

**Files:** All `docs/architecture/` markdown files

**What:** Update all references to renamed models and fields:
- `StorytellerResult` → `RecordResult`
- `StateDelta` → `StateMerge`
- `_ExtractionResult` → `_ExtractionAccumulator`
- `_ExtractionVariant` → `_ExtractionStreamConfig`
- `_ExtractionContext` → `_PostDeltaContext`
- `ExtractResult` → `ExtractionResult`
- `NarrateResult` → `NarrationResult`
- `PersistResult` → `TurnCompleteResult`
- `WorldStateBlock` → `WorldFactsBlock`
- `PacingBlock` → `DirectiveBlock`
- `ArcThreadSummary` → `ArcThreadSummaryItem`
- `Scene.world_state` → `Scene.world_facts`
- `SanitizedWorldStateFact` → `WorldStateFact`
- `TurnResult` location: `ccya/models/config.py` → `ccya/engine/turn.py`

**Why:** Arch docs must reflect new names.

**Validation:** `make check` passes.

#### Step 7.2 — Update repomap

**File:** `docs/repomap.md`

**What:** Update module index and extraction routing descriptions to reflect new names.

**Why:** Repomap is the primary navigation aid for the codebase.

**Validation:** `make check` passes.

#### Step 7.3 — Update ev state reference

**File:** `docs/ev/STATE-REFERENCE.md`

**What:** Update all model references to new names.

**Why:** State reference docs must match current code.

**Validation:** `make check` passes.

#### Step 7.4 — Update engine overhaul checklist

**File:** `docs/engine-overhaul-checklist.md`

**What:** Update all model references to new names.

**Why:** Checklist must reflect current code.

**Validation:** `make check` passes.

#### Step 7.5 — Update design docs

**Files:** All `docs/design/` markdown files

**What:** Update all model references to new names.

**Why:** Design docs must reflect current code.

**Validation:** `make check` passes.

#### Step 7.6 — Update plans

**Files:** All `plans/` markdown files

**What:** Update all model references to new names.

**Why:** Plans must reflect current code.

**Validation:** `make check` passes.

#### Step 7.7 — Update README

**File:** `README.md`

**What:** Update `StateDelta` → `StateMerge` reference (line 189).

**Why:** README must reflect current code.

**Validation:** `make check` passes.

### Verification

- `make check` passes
- Grep for old names returns 0 matches in `docs/` (only in git history)
- All docs reflect new names
