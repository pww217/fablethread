---
title: "Engine model and pipeline naming audit"
status: scoping
urgency: 3
size: large
created: 2026-07-05
ticket_id: I-29
labels: [engine, models, naming]
---

## Problem

Engine models, extraction results, pipeline context types, and seed models use names that don't match their role in the pipeline. This creates confusion about data flow, ownership, and where things belong. Names collide across pipeline stages (e.g., `world_state` in both `Scene` and `SeedScene` means the same thing but lives in two hierarchies). Old names linger after renames (e.g., `StorytellerResult` after step renamed to Record).

## Findings

### State models (`ccya/models/state.py`)

| Model/Field | Current Name | Issue |
|---|---|---|
| `Scene.world_state` | `world_state: list[dict]` | Persistent world facts, not scene-specific. Owned by thread sanitizer, read-only in Record. Should be `world_facts` or live at root `WorldState` level. |
| `ThreadResolution.world_state_candidate` | `world_state_candidate` | Single world fact, not full world state. Should be `world_fact_candidate`. |
| `SanitizedWorldStateFact` | (class) | Identical schema to `WorldStateFact`; only semantic distinction ("confirmed by sanitizer"). Should be `ConfirmedWorldFact` or merged. |
| `WorldState.world_state_candidates` | `world_state_candidates` | Candidates are world facts, not "world state". Should be `world_facts_candidates` or `pending_world_facts`. |

### Extraction models (`ccya/models/extraction.py`)

| Model/Field | Current Name | Issue |
|---|---|---|
| `StorytellerResult` | (class) | Step renamed from "Storytell" to "Record" but class name lingers. Should be `RecordResult`. |
| `StateDelta` | (class) | It's a merge container for heterogeneous extraction results, not a traditional state delta/diff. Arch docs call it "StateMerge schema". Should be `StateMerge` or `ExtractionMerge`. |

### Pipeline context types

| Model/Field | Current Name | Issue |
|---|---|---|
| `_ExtractionContext` | (class, `engine/extraction/context.py`) | Carries post-delta scene+state derived state into Record. Docstring still says "storytell stream". Should be `_PostDeltaContext` or `_SceneStateContext`. |
| `_ExtractionResult` | (class, `engine/extraction/pipeline.py`) | Accumulator for three extraction streams, not a result. Should be `_ExtractionAccumulator` or `_StreamResults`. |
| `_ExtractionVariant` | (class, `engine/extraction/pipeline.py`) | Stream configuration descriptor, not a variant. Should be `_ExtractionStreamConfig` or `_ExtractionStreamSpec`. |

### Turn pipeline result types (`engine/turn.py`)

| Model | Current Name | Issue |
|---|---|---|
| `NarrateResult` | (class) | Step is "Narrate" but pipeline convention uses gerund names (Ruling, Narration, Scene, State, Record, World). Should be `NarrationResult`. Fields `pc` and `new_scene` typed as `Any`. |
| `ExtractResult` | (class) | Merged result from all three extraction streams, not a single extraction result. Should be `ExtractionResult`. |
| `PersistResult` | (class) | End-of-turn result; name too generic. Should be `TurnCompleteResult` or `PostPersistResult`. |

### Prompt context block types (`prompts/context.py`)

| Model | Current Name | Issue |
|---|---|---|
| `WorldStateBlock` | (class) | Only wraps `scene.world_state` (world facts), not the root `WorldState`. Should be `WorldFactsBlock`. |
| `PacingBlock` | (class) | Only holds `directive` (single field), not the full `PacingContext`. Should be `DirectiveBlock` or `PacingDirectiveBlock`. |
| `NarratorBoundary.state` | `dict[str, Any]` | Untyped; should expose specific sub-fields (`location`, `inventory`, `scene`) as typed fields. |
| `ArcThreadSummary` | (class) | Used as a collection type in `ArcThreadBlock.threads`. Should be `ArcThreadSummaryItem` or collection should be `ArcThreadSummaries`. |

### Seed pipeline models (`pack.py`)

| Model/Field | Current Name | Issue |
|---|---|---|
| `SeedStateEnvelope` / `SeedEnvelope` | (two classes) | Nearly identical envelope types for the same pipeline stage. One should be removed. |
| `SeedScene.world_state` | `world_state` | Same name as `Scene.world_state` in live state. They're the same concept (world facts) but live in two hierarchies. Should be `world_facts` in both. |
| `SeedState.world` | `dict[str, Any]` | Holds `world_factions` and `world_locations`. Too vague. Should be `world_info` or `world_data`. |
| `SeedPC.drive` | `drive` | Same role as `PC.directive`. Should be aligned to `directive`. |
| `CompendiumEntry.bond` | `bond` | Runtime uses `tie` (`CompendiumNpcUpdate.tie`); seed uses `bond`. `ScenarioBrief` uses `npc_bonds`. Three names for the same concept across seed/runtime/extraction layers. |

### Config (`models/config.py`)

| Model | Issue |
|---|---|
| `TurnResult` | Final output of `run_turn()`. Misleadingly placed in `models/config.py` alongside `EngineConfig`. Should live with turn pipeline results in `turn.py`. |

### Cascading renames (from core model changes)

| File | Issue |
|---|---|
| `engine/turn_state.py` | Imports `StorytellerResult` and `StateDelta`; parameter names use `storyteller_result` in 6 functions (`_apply_thread_updates`, `_apply_arc_resolve`, `_apply_thread_resolutions`, `_apply_state_updates`). Cascading renames from core model changes. |
| `engine/_pacing.py` | Module docstring says "storytell context" (line 5). Outdated after step rename. |
| `state/delta_builder.py` | Imports `StateDelta`; `apply_delta()` and `reconcile_delta()` use it as parameter type. Comment on line 277 says "Persist storyteller actions as rolling window". |
| `pack.py` | Comment on line 64 says "StateDelta.inventory_add has max_length=6". Outdated reference. |

### Untyped return types

| File | Function | Issue |
|---|---|---|
| `engine/seed.py` | `narrate_seed()` | Returns `dict[str, Any]` but actually returns exactly `{"opening_narrative", "actions", "outcome_summary"}`. Should use a typed dataclass or `NamedTuple`. |
| `engine/world.py` | `_run_world_step()` | Returns `tuple[WorldState, list[dict[str, Any]], str, str, str, dict[str, int]]` — untyped tuple with 6 elements. Should use a typed dataclass. |
| `engine/extraction/utils.py` | `_call_stream()` | Returns `tuple[Any, dict[str, Any], int, list[str]]` — untyped tuple. Same issue. |

## Scope

This is a pure naming refactoring with no behavior changes. Each item:
1. Rename the model/field
2. Update all references across engine, prompts, ev checkers, server, UI templates
3. Update arch docs to reflect new names
4. Update repomap

## Suggested execution order

1. **Core model renames** (foundation — everything else cascades): `StorytellerResult` → `RecordResult`, `StateDelta` → `StateMerge` (rename class + all imports + parameter names in `turn_state.py`, `delta_builder.py`, `pipeline.py`, `context.py`, `turn.py`)
2. **Low-risk renames** (single model, no field): `_ExtractionResult` → `_ExtractionAccumulator`, `_ExtractionVariant` → `_ExtractionStreamConfig`, `_ExtractionContext` → `_PostDeltaContext`, `ExtractResult` → `ExtractionResult`, `PersistResult` → `TurnCompleteResult`, `NarrateResult` → `NarrationResult`, `WorldStateBlock` → `WorldFactsBlock`, `PacingBlock` → `DirectiveBlock`, `ArcThreadSummary` → `ArcThreadSummaryItem`
3. **Field renames**: `Scene.world_state` → `world_facts`, `ThreadResolution.world_state_candidate` → `world_fact_candidate`, `SeedPC.drive` → `directive`, `SeedState.world` → `world_info`
4. **Structural changes**: Merge `SeedStateEnvelope`/`SeedEnvelope`, merge `SanitizedWorldStateFact`/`WorldStateFact`, align `CompendiumEntry.bond` → `tie`, move `TurnResult` to `turn.py`
5. **Doc updates**: Arch docs, repomap, state-models.md, cross-pipeline.md
6. **Cleanup**: Fix outdated "storytell" references in `engine/_pacing.py` docstring, `state/delta_builder.py` comment, `pack.py` comment
