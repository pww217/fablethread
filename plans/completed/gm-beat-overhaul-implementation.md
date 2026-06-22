# GM Beat Overhaul — Implementation Plan

**Design authority:** `docs/design/gm-beat-overhaul-design.md`
**Status:** Draft
**Estimated scope:** Small — most changes already implemented

## Pre-flight: Design vs. Current Code Discrepancies

The design doc was written against a codebase state that was already partially migrated. The following items from the design are **already done** in the current source:

| Design item | Current state |
|---|---|
| `GMBeat.effect` field | Already present (`extraction.py:209`) |
| `GMBeat.driver` with `bond` + `personality` | Already present (`extraction.py:211`) |
| `narrate_user.j2` rendering `effect` | Already done (`narrate_user.j2:88`) |
| `storytell_user.j2` rendering `effect` | Already done (`storytell_user.j2:54`) |
| `storytell_system.j2` schema with `effect` | Already done (`storytell_system.j2:17`) |
| `turn_state.py` recent_beats with `effect` | Already done (`turn_state.py:475`) |
| `pipeline.py` null-effect-with-npc_id retry | Already done (`pipeline.py:188-219`) |
| `npc_roster.py` slim=True mode | Already done (`npc_roster.py:44-49`) |
| `llm_checkers.py` `beat_narrative_chain` using `effect` | Already done (`llm_checkers.py:132`) |
| `_npc_context.j2` deletion | File does not exist |
| `recent_beats.py` checker update | File does not exist |
| `pacing.py` surface_as checker removal | Checker does not exist (file is 89 lines) |

**Remaining gap:** Phase 0 — `SceneExtractResult` still has `candidate_npc_ids: list[str]` + `effect: str` (separate fields). The design calls for replacing these with `candidate_npcs: list[{id: str, type: str, effect: str}]`. This is the only structural change not yet implemented.

## [QUESTION: candidate_npcs migration scope]

The design calls for `candidate_npcs: list[{id, type, effect}]` in `SceneExtractResult`, `_ExtractionContext`, and the storytell prompt. Currently:
- `SceneExtractResult` has `candidate_npc_ids: list[str]` + `effect: str` (separate)
- `_ExtractionContext` has `candidate_npc_ids: list[str]` + `scene_effect: str` (separate)
- `storytell_user.j2` renders them as two separate variables (lines 10-15)

The migration requires:
1. Replacing `candidate_npc_ids` + `effect` in `SceneExtractResult` with `candidate_npcs: list[dict]`
2. Replacing `candidate_npc_ids` + `scene_effect` in `_ExtractionContext` with `candidate_npcs: list[dict]`
3. Updating `_build_extraction_context()` to copy `candidate_npcs` instead of the two separate fields
4. Updating `storytell_user.j2` to render the new `candidate_npcs` list
5. Updating `storytell_system.j2` to reference `candidate_npcs` instead of `candidate_npc_ids` + `scene_effect`
6. Updating `storytell.py` to pass `candidate_npcs` from `extraction_ctx`
7. Updating `extract_scene_system.j2` to emit the new format

**Question:** Should this be done as a single atomic change (direct swap, per AGENTS.md no-backwards-compat policy), or should we keep the old fields alongside the new one for a transition period? The design says "direct swap, no backwards compatibility."

**Recommended:** Single atomic change. The design explicitly rejects migration paths.

## [QUESTION: Scene prompt output format]

The design shows scene output as:
```json
{
  "candidate_npcs": [
    { "id": "aris_thorne", "type": "motivation", "effect": "Aris protective of the vaccine" },
    ...
  ]
}
```

The current `extract_scene_system.j2` (line 12-13) instructs the LLM to emit `candidate_npc_ids: ["npc_id_1", "npc_id_2"]` and `effect: "vague psychological pressure ~5-7 words"`.

The new format requires the LLM to produce per-NPC driver types AND per-NPC effect strings. This is a significant change to the scene prompt's output schema and instructions.

**Question:** Should the scene prompt be updated to produce per-NPC driver types (motivation/fear/leverage/bond/personality) and per-NPC effect strings, or should the scene still produce a single vague effect and the driver assignment happen in storytell? The design says "Scene has the full psychological fields in the compendium and can accurately assign drivers."

**Recommended:** Follow the design — scene produces per-NPC driver types and per-NPC effect strings. This is the core value proposition: scene has the compendium data and can assign drivers accurately; storytell shouldn't guess.

## Phases

### Phase 0: Models — Replace candidate_npc_ids+effect with candidate_npcs

**Description:** Replace the two separate fields (`candidate_npc_ids: list[str]`, `effect: str`) in `SceneExtractResult` and `_ExtractionContext` with a single `candidate_npcs: list[dict[str, Any]]` field containing `{id, type, effect}` objects.

**Files touched:**
- `ccya/models/extraction.py` — `SceneExtractResult`
- `ccya/engine/extraction/context.py` — `_ExtractionContext` + `_build_extraction_context()`
- `ccya/engine/extraction/pipeline.py` — `_build_extraction_context()` call (no change needed, passes scene_result)
- `ccya/engine/extraction/storytell.py` — pass `candidate_npcs` from `extraction_ctx`
- `ccya/prompts/extract_scene_system.j2` — new output schema + instructions
- `docs/architecture/step2a-scene.md` — update output schema
- `docs/architecture/step2c-storytell.md` — update input description
- `docs/architecture/state-models.md` — update SceneExtractResult model
- `docs/repomap.md` — update SceneExtractResult description

**Tasks:**

1. **0.1** Update `SceneExtractResult` in `ccya/models/extraction.py`: replace `candidate_npc_ids: list[str]` and `effect: str` with `candidate_npcs: list[dict[str, Any]] = Field(default_factory=list)`. Add docstring: `candidate_npcs format: [{"id": "npc_id", "type": "motivation|fear|leverage|bond|personality", "effect": "vague psychological pressure ~5 words"}, ...]`.

2. **0.2** Update `_ExtractionContext` in `ccya/engine/extraction/context.py`: replace `candidate_npc_ids: list[str]` and `scene_effect: str` with `candidate_npcs: list[dict[str, Any]] = field(default_factory=list)`. Update docstring.

3. **0.3** Update `_build_extraction_context()` in `context.py`: change `candidate_npc_ids=list(scene_result.candidate_npc_ids or [])` and `scene_effect=scene_result.effect or ""` to `candidate_npcs=list(scene_result.candidate_npcs or [])`.

4. **0.4** Update `storytell.py`: change `candidate_npc_ids: extraction_ctx.candidate_npc_ids` and `scene_effect: extraction_ctx.scene_effect` to `candidate_npcs: extraction_ctx.candidate_npcs`.

5. **0.5** Update `extract_scene_system.j2`: rewrite output schema (lines 9-14) and beat candidate selection section (lines 17-22) to produce `candidate_npcs: [{id, type, effect}]` format. Update field rules to explain per-NPC driver assignment.

6. **0.6** Update `docs/architecture/step2a-scene.md`: update output schema in flowchart and beat candidate selection section.

7. **0.7** Update `docs/architecture/step2c-storytell.md`: update input description to reference `candidate_npcs` instead of `candidate_npc_ids` + `scene_effect`. Update GM Beat section to reference `candidate_npcs`.

8. **0.8** Update `docs/architecture/state-models.md`: update SceneExtractResult model description.

9. **0.9** Update `docs/repomap.md`: update SceneExtractResult responsibility description.

**Verification:**
- `make check` passes (lint + typecheck)
- `ev.py prompt-eval dump` renders scene prompt with new schema
- `ev.py prompt-eval dump` renders storytell prompt with `candidate_npcs` variable
- Manual play test: scene extracts produce `candidate_npcs` list with id/type/effect objects

**Dependencies:** None (first phase)

### Phase 1: Storytell templates — Update to reference candidate_npcs

**Description:** Update storytell system and user prompts to reference `candidate_npcs` (new format) instead of `candidate_npc_ids` + `scene_effect`. Update the beat generation instructions to reflect the three patterns (deliver as-is, combine, thread-apply).

**Files touched:**
- `ccya/prompts/storytell_system.j2` — beat section instructions
- `ccya/prompts/storytell_user.j2` — Scene Input section
- `docs/architecture/step2c-storytell.md` — update prompt description

**Tasks:**

10. **1.1** Update `storytell_system.j2` (lines 76-99): change `candidate_npc_ids` and `scene_effect` references to `candidate_npcs`. Update beat generation instructions to describe the three patterns (deliver as-is, combine, thread-apply) using `candidate_npcs` as the input. Update the schema example (line 17) if needed.

11. **1.2** Update `storytell_user.j2` (lines 10-16): replace the Scene Input section to render `candidate_npcs` as a formatted list (id, type, effect) instead of `candidate_npc_ids` + `scene_effect`.

12. **1.3** Update `docs/architecture/step2c-storytell.md`: update prompt description to reflect the new `candidate_npcs` format.

**Verification:**
- `make check` passes
- `ev.py prompt-eval dump` renders storytell system prompt with updated beat instructions
- `ev.py prompt-eval dump` renders storytell user prompt with `candidate_npcs` list

**Dependencies:** Phase 0 (models must produce `candidate_npcs` before templates can reference it)

### Phase 2: Documentation — Finalize architecture docs

**Description:** Ensure all architecture docs accurately reflect the post-overhaul state. This phase also covers any remaining stale references to `surface_as`, `candidate_npc_ids`, or `scene_effect` in documentation.

**Files touched:**
- `docs/architecture/step2c-storytell.md` — GM Beat section (already partially updated, verify completeness)
- `docs/architecture/state-models.md` — verify GMBeat and SceneExtractResult descriptions
- `docs/architecture/cross-pipeline.md` — verify data flow references
- `docs/architecture/cross-module-contracts.md` — verify extraction routing
- `docs/repomap.md` — verify module descriptions
- `AGENTS.md` — verify any references to surface_as or old field names

**Tasks:**

13. **2.1** Audit `docs/architecture/step2c-storytell.md`: verify all references to `surface_as` are removed, `candidate_npc_ids`/`scene_effect` are replaced with `candidate_npcs`, and the GM Beat schema is accurate.

14. **2.2** Audit `docs/architecture/state-models.md`: verify GMBeat model description includes `effect`, `npc_id`, `driver` (with all 5 values), and `beat_expires_turn`. Verify SceneExtractResult description reflects `candidate_npcs`.

15. **2.3** Audit `docs/architecture/cross-pipeline.md`: verify data flow references `candidate_npcs` through `_ExtractionContext`.

16. **2.4** Audit `docs/architecture/cross-module-contracts.md`: verify extraction routing description is accurate.

17. **2.5** Audit `docs/repomap.md`: verify SceneExtractResult and `_ExtractionContext` descriptions are accurate.

18. **2.6** Audit `AGENTS.md`: verify no stale references to `surface_as`, `candidate_npc_ids`, or `scene_effect`.

**Verification:**
- `make check` passes
- All architecture docs reference `candidate_npcs` (not `candidate_npc_ids` + `scene_effect`)
- All architecture docs reference `effect` (not `surface_as`)
- All architecture docs reference `driver` with 5 values (motivation/fear/leverage/bond/personality)

**Dependencies:** Phase 0 (models must be updated before docs can be accurate)

## Summary

| Phase | Description | Tasks | Files | Dependencies |
|---|---|---|---|---|
| 0 | Models: Replace candidate_npc_ids+effect with candidate_npcs | 9 | 5 source + 4 docs | None |
| 1 | Storytell templates: Update to reference candidate_npcs | 3 | 2 prompts + 1 doc | Phase 0 |
| 2 | Documentation: Finalize architecture docs | 6 | 6 docs | Phase 0 |

**Total tasks:** 18
**Total files touched:** ~13 (8 source/prompts + 5 docs)

## Notes

- All other items from the design doc (effect field, driver field expansion, surface_as removal, retry logic, slim npc_roster, narrate_user changes, turn_state changes, llm_checkers changes) are already implemented in the current codebase.
- The `recent_beats.py` and `_npc_context.j2` items mentioned in the design do not exist in the current codebase — no action needed.
- The `pacing.py` surface_as checker mentioned in the design (lines 128-159) does not exist — the file is only 89 lines and contains no surface_as references.
- The `driver` field on `GMBeat` already includes `bond` and `personality` in its Literal — no change needed.
