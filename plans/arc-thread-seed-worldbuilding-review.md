# Arc Thread Seed-Worldbuilding Review

**Scope:** 3 plans in `plans/` and 3 design docs in `docs/design/` labeled 01, 02, 03.
**Method:** Document-only review. No codebase inspection.
**Date:** 2026-06-23

---

## 1. Faithfulness: Plans vs. Their Design Docs

### Primitives Plan → 01-Primitives

**Verdict: Faithful.** All firm decisions in the plan are present in the design doc. All phases map to mechanical corrections in the design doc.

**Minor observations:**
- Design doc D8 (`CampaignArc` → `LongTermObjective`) and D8's mechanical corrections are fully covered by plan Phase 02.
- Design doc's "Kept" table (`urgency_set_turn`) is acknowledged in the plan's out-of-scope but not explicitly called out in a phase. This is fine — it's a deletion decision, not an implementation phase.
- Design doc's `turns_since` warning guard deletion (C8, C13, C12) maps to plan Phase 01 (deletions) and Phase 06 (dormant threshold). The plan's Phase 06 references `turn_state.py:116` for the threshold change but does not explicitly call out removing the `turns_since` warning guard block at `turn_state.py:225-233`. This is covered by Phase 01's "delete `turns_since` warning guard" in turn_state.py, but the plan's Phase 01 file list mentions turn_state.py broadly without specifying which lines. **Recommendation: verify in codebase that Phase 01's deletion scope includes the warning guard block.**

### Arc System Plan → 02-Arc System Redesign

**Verdict: Faithful.** All firm decisions in the plan are present in the design doc. All phases are validation or implementation phases that directly implement design decisions.

**Minor observations:**
- Design doc's "Thread → world state promotion" section (two-step system) maps to plan Phase 02. The plan correctly notes that sanitizer evaluation is in the seed worldbuilding plan.
- Design doc's TTL filtering maps to plan Phase 06 (validation). The plan correctly delegates TTL implementation to primitives Phase 07.
- Design doc's "arc_resolve field contract" maps to plan Phase 03 (validation) and Phase 04-05 (prompt schema updates).
- Design doc's "No auto-arc-resolve" (D9) is a firm decision in the plan but requires no implementation phase — correctly noted as "no mechanical corrections needed" in the design doc.
- Design doc's "Thread type stability" maps to plan Phase 05 (adding `reason` field to thread_update schema).

### Seed Worldbuilding Plan → 03-Seed Worldbuilding Redesign

**Verdict: Faithful.** All firm decisions in the plan are present in the design doc. All phases map to workstream sections in the design doc.

**Minor observations:**
- Design doc's funnel ordering (Workstream 1) maps to plan Phase 03.
- Design doc's `WorldStateFact` replacement (Workstream 2) maps to plan Phase 05.
- Design doc's sanitizer extension (Workstream 2) maps to plan Phases 08-10.
- Design doc's TTL expiry (Workstream 2) maps to plan Phase 07.
- Design doc's `arc_origin` placement (D6 in primitives, also in this design) maps to plan Phase 01 and Phase 13.

---

## 2. Cross-Plan Conflicts and Contradictions

### 2.1 Execution Order — Consistent

All three plans agree on execution order: **Primitives → Arc System → Seed Worldbuilding.**

- Primitives plan: No dependencies listed.
- Arc system plan: "Depends on: Primitives Plan."
- Seed worldbuilding plan: "Depends on: Primitives Plan, Arc System Plan."

This is consistent with the design docs' execution order section (01-primitives explicitly states "Primitives → Arc System → Seed Worldbuilding").

### 2.2 `arc_origin` Placement — Consistent

All three plans agree:
- **Firm decision in primitives plan:** "`arc_origin` on seed model only. Never on LongTermObjective or ArcResolution. Never regenerated. Never injected into narrate, storytell, or ruling prompts."
- **Arc system plan:** "arc_origin on seed model only" in firm decisions and out-of-scope.
- **Seed worldbuilding plan:** "arc_origin on seed model only" in firm decisions. Phase 01 adds it to `SeedState`. Phase 13 renders it in UI.

**No conflict.**

### 2.3 `goal_context` Deletion — Consistent

All three plans agree `goal_context` is deleted everywhere and replaced by `arc_origin` on the seed model only.

- Primitives plan Phase 01: "Delete all removed fields" including `goal_context` from all callsites.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.4 TTL Strategy — Consistent

All three plans agree on TTL strategy:
- Completed/abandoned threads: 3-turn TTL in prompts, kept in data forever.
- Dormant threshold: 8 turns (up from 4).
- Archival: 13 turns (8 dormant + 5).
- No resurfacing hints.

- Primitives plan Phase 06 (dormant threshold), Phase 07 (TTL filtering in context builder).
- Arc system plan Phase 06 (validates TTL filtering).
- Seed worldbuilding plan Phase 07 (TTL expiry pass for world state facts).

**No conflict.** Note: Primitives TTL applies to threads; Seed TTL applies to world state facts. These are separate TTL systems in separate domains.

### 2.5 Pressure Score System — Consistent

Only in primitives plan (Phase 08-09). Not in arc system or seed worldbuilding plans. Both other plans correctly list it as out of scope.

**No conflict.**

### 2.6 `major_update_signal` Values — Consistent

All agree: `advancement` / `setback` only. `shift` removed.

- Primitives plan Phase 02 (rename `progress_kind` → `major_update_signal`).
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.7 Thread → World State Promotion — Consistent

Two-step system: storyteller flags (`world_state_candidate`), sanitizer confirms.

- Primitives plan Phase 03 (adds `world_state_candidate` to ThreadResolution model), Phase 04 (sets `resolved_turn`).
- Arc system plan Phase 02 (collects `world_state_candidate` from ThreadResolution into `world_state_candidates` list).
- Seed worldbuilding plan Phase 09 (extends sanitizer to evaluate candidates), Phase 10 (updates sanitizer prompt).

**No conflict.** The division of labor is clear: primitives adds model fields, arc system collects candidates, seed worldbuilding extends sanitizer.

### 2.8 `pc.situation` — Consistent

- Primitives plan Phase 10 (adds to ruling context).
- Seed worldbuilding plan Phase 02 (adds to `_default_state()` and `SeedPC`), Phase 03 (funnel ordering includes pc.situation).
- Arc system plan: Out of scope (delegated to primitives and seed worldbuilding).

**No conflict.**

### 2.9 `goal_update` Format — Consistent

All agree: `dict | None` with `long_term_objective` key only. No `arc_origin`.

- Primitives plan Phase 05.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.10 World State Fact Model — Consistent

- Primitives plan Phase 03 (adds `world_state_candidates` to `_default_state()`), but does NOT explicitly define the new `WorldStateFact` schema in a phase. The design doc's C83 replacement is referenced in the "World State Model Replacement" section but not mapped to a specific primitives phase.
- Seed worldbuilding plan Phase 05 (replaces `WorldStateFact` model), Phase 06 (updates code that branches on old tier values).

**Potential gap in primitives plan:** The design doc has a detailed "World State Model Replacement (C83)" section with old/new schemas and files to update, but the primitives plan does not have a phase that explicitly implements this replacement. The primitives plan Phase 03 mentions adding `world_state_candidates` to `_default_state()` but not replacing `WorldStateFact` itself.

**This is not a conflict** — the seed worldbuilding plan's Phase 05 covers the replacement. But the primitives plan's "Mechanical Corrections" section (C83) suggests the replacement should be in primitives. The execution order (primitives first) means primitives should handle the model replacement, and seed worldbuilding should handle the downstream effects (sanitizer, TTL, rendering).

**Recommendation: Clarify in primitives plan that Phase 03 or a new phase handles `WorldStateFact` replacement, not just `world_state_candidates` initialization.**

### 2.11 NPC Roster Limit — Consistent

- Primitives plan Phase 11: "Bump NPC roster limit from 10 to 12."
- Seed worldbuilding design doc "Confirmed Decisions": "NPC roster limit — 12."
- Arc system plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.12 Key Locations — Consistent

- Primitives plan: Out of scope (delegated to seed worldbuilding).
- Seed worldbuilding plan Phase 04 (adds `KeyLocation` model), Phase 03 (funnel ordering includes key locations).
- Arc system plan: Out of scope (delegated to seed worldbuilding).

**No conflict.**

### 2.13 Pack Update — Consistent

- Primitives plan: Out of scope (delegated to seed worldbuilding).
- Seed worldbuilding plan Phase 14 (updates golden-piracy pack).
- Arc system plan: Out of scope (delegated to seed worldbuilding).

**No conflict.**

### 2.14 Documentation Updates — Consistent

- Primitives plan: No documentation phase.
- Arc system plan Phase 09: Updates design doc status, OVERVIEW.md, step2c-storytell.md, repomap.md, AGENTS.md.
- Seed worldbuilding plan Phase 15: Updates state-models.md, cross-module-contracts.md, step2c-storytell.md, step2a-scene.md, repomap.md, OVERVIEW.md, AGENTS.md.

**Potential overlap:** Both arc system and seed worldbuilding plans update `step2c-storytell.md`, `repomap.md`, `OVERVIEW.md`, and `AGENTS.md`. Since arc system runs before seed worldbuilding, the arc system's doc updates will be overwritten/referenced by the seed worldbuilding's doc updates. This is acceptable given the execution order, but the arc system's Phase 09 should be scoped to arc-specific documentation, and the seed worldbuilding's Phase 15 should be the comprehensive final update.

**Recommendation: Arc system Phase 09 should explicitly scope to arc-specific docs (OVERVIEW.md world_state_candidates section, step2c-storytell.md extraction fields, repomap.md world_state_candidates key). Seed worldbuilding Phase 15 should be the comprehensive final documentation update.**

### 2.15 `_apply_arc_resolve` Validation — Consistent

- Primitives plan Phase 01: Removes `drop_threads` filtering, `new_threads`, `goal_context` from successor arc construction.
- Arc system plan Phase 01: Validates that primitives correctly removed these.

**No conflict.** The arc system's Phase 01 is a validation phase that checks primitives' Phase 01 work.

### 2.16 `started_turn` — Consistent

- Primitives plan Phase 03 (adds field to model), Phase 04 (sets at construction time).
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.17 `reason` Field on ThreadUpdate — Consistent

- Primitives plan Phase 03 (adds to model).
- Arc system plan Phase 05 (updates thread_update schema in storyteller prompt to include `reason`).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.** Primitives adds the model field; arc system reflects it in the prompt schema.

### 2.18 `resolved_turn` — Consistent

- Primitives plan Phase 03 (adds to ThreadResolution model), Phase 04 (sets at resolution time, passes to sanitizer).
- Arc system plan Phase 02 (implicitly validates via world_state_candidate collection).
- Seed worldbuilding plan Phase 09 (sanitizer uses `resolved_turn` for TTL evaluation).

**No conflict.** Primitives adds and sets the field; arc system validates collection; seed worldbuilding validates sanitizer usage.

### 2.19 TTL Filtering Implementation Location — Consistent

- Primitives plan Phase 07: "Implement TTL filtering in context builder" in `storytell.py` and `narrate.py`.
- Arc system plan Phase 06: Validates TTL filtering in context builder.
- Seed worldbuilding plan: No TTL filtering for threads (delegated to primitives).

**No conflict.** Primitives implements TTL for threads; arc system validates it.

### 2.20 Sanitizer Extension — Consistent

- Primitives plan: No sanitizer extension phase.
- Arc system plan: No sanitizer extension phase (delegated to seed worldbuilding).
- Seed worldbuilding plan Phase 09 (extends sanitizer to maintain world state), Phase 10 (updates sanitizer prompt).

**No conflict.** Primitives adds model fields; seed worldbuilding extends sanitizer.

### 2.21 `_apply_goal_update` — Consistent

- Primitives plan Phase 05: Updates `_apply_goal_update` to use `long_term_objective` key only.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.22 `major_updates` Rename — Consistent

- Primitives plan Phase 02: Renames `progress` → `major_updates` in ArcThread model.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.23 `_arc.j2` Template Changes — Consistent

- Primitives plan Phase 07: TTL filtering in context builder, removes `[:15]` cap in template.
- Arc system plan Phase 06: Validates TTL filtering in context builder and template.
- Seed worldbuilding plan: No `_arc.j2` changes (delegated to primitives).

**No conflict.** Primitives implements; arc system validates.

### 2.24 `storytell_system.j2` Schema Updates — Consistent

- Primitives plan Phase 01: Removes `goal_context`, `drop_threads`, `new_threads`, `chapter_end`, `promote_to_world_state` from schema examples.
- Primitives plan Phase 02: Renames `visible_goal` → `long_term_objective` in schema.
- Arc system plan Phase 03: Validates primitives' schema updates.
- Arc system plan Phase 04: Updates thread_resolve schema to include `resolved_turn` and `world_state_candidate`.
- Arc system plan Phase 05: Updates thread_update schema to use `major_update_signal` and add `reason`.
- Arc system plan Phase 07: Validates arc resolution guidance in storyteller prompt.
- Arc system plan Phase 08: Validates thread type in schema examples.

**No conflict.** Primitives does the heavy lifting; arc system validates and adds new fields to schema.

### 2.25 `generate_seed_system.j2` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` references.
- Primitives plan Phase 02: Renames `visible_goal` → `long_term_objective`, `goal_context` → `arc_origin`.
- Seed worldbuilding plan Phase 03: Rewrites funnel ordering (which restructures the prompt).
- Seed worldbuilding plan Phase 12: Adds valence requirement.

**No conflict.** Primitives does field-level changes; seed worldbuilding does structural changes.

### 2.26 UI Template Changes — Consistent

- Primitives plan Phase 02: Renames `visible_goal` → `long_term_objective`, `goal_context` → `arc_origin` in `_state_left.html` and `_save_picker.html`.
- Seed worldbuilding plan Phase 13: Renders `arc_origin` in UI sidebar and save picker.

**Potential overlap:** Primitives Phase 02 renames `goal_context` → `arc_origin` in UI templates. Seed worldbuilding Phase 13 renders `arc_origin` in UI. Since primitives runs first, the rename happens first, then the rendering logic is added. This is correct execution order.

**No conflict.**

### 2.27 `turn_state.py` Changes — Consistent

- Primitives plan Phase 01: Deletes removed fields from turn_state.py.
- Primitives plan Phase 02: Updates references to renamed fields in turn_state.py.
- Primitives plan Phase 04: Sets `started_turn` in `_apply_arc_resolve()`.
- Primitives plan Phase 05: Updates `goal_update` application in turn_state.py.
- Primitives plan Phase 06: Updates dormant threshold in turn_state.py.
- Arc system plan Phase 01: Validates `_apply_arc_resolve()` carries all threads forward.
- Arc system plan Phase 02: Collects `world_state_candidate` in turn_state.py.

**No conflict.** Primitives does the implementation; arc system validates and adds collection logic.

### 2.28 `thread_sanitizer.py` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` from sanitizer.
- Primitives plan Phase 05: Updates `_apply_goal_update` in sanitizer.
- Seed worldbuilding plan Phase 08: Adds `SanitizedWorldStateFact` model.
- Seed worldbuilding plan Phase 09: Extends sanitizer to maintain world state.
- Seed worldbuilding plan Phase 10: Updates sanitizer prompt.

**No conflict.** Primitives does cleanup; seed worldbuilding extends.

### 2.29 `state/io.py` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` from `_default_state()`.
- Primitives plan Phase 03: Adds `started_turn` initialization and `world_state_candidates` to `_default_state()`.
- Seed worldbuilding plan Phase 02: Adds `pc.situation` to `_default_state()`.
- Seed worldbuilding plan Phase 04: Adds `world.locations` to `_default_state()`.

**No conflict.** Each plan adds to `_default_state()` in sequence. Primitives runs first, then seed worldbuilding.

### 2.30 `ruling.py` Changes — Consistent

- Primitives plan Phase 10: Adds `pc.situation` to ruling context.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.31 `engine/hints.py` — Consistent

- Primitives plan Phase 08: Creates new file with pressure score functions.
- Primitives plan Phase 09: Wires hints into narrator and storyteller.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.32 `turn.py` Changes — Consistent

- Seed worldbuilding plan Phase 07: Adds TTL expiry pass to turn pipeline start.
- Primitives plan: No turn.py changes (TTL for threads is in context builder, not turn pipeline).
- Arc system plan: No turn.py changes.

**No conflict.** Seed worldbuilding's TTL expiry is for world state facts, not threads.

### 2.33 `pack.py` Changes — Consistent

- Seed worldbuilding plan Phase 01: Adds `arc_origin` to `SeedState`.
- Seed worldbuilding plan Phase 02: Adds `pc.situation` to `SeedPC`, adds `pc_situation_schema` to `ScenarioBrief`.
- Primitives plan: No pack.py changes.
- Arc system plan: No pack.py changes.

**No conflict.**

### 2.34 `models/state.py` Changes — Consistent

- Primitives plan Phase 01: Deletes fields from models.
- Primitives plan Phase 02: Renames in models.
- Primitives plan Phase 03: Adds new fields to models.
- Seed worldbuilding plan Phase 04: Adds `KeyLocation` model.
- Seed worldbuilding plan Phase 05: Replaces `WorldStateFact` model.
- Seed worldbuilding plan Phase 08: Adds `SanitizedWorldStateFact` model.

**No conflict.** Primitives does renames/additions; seed worldbuilding adds new models.

### 2.35 `prompts/context.py` Changes — Consistent

- Primitives plan Phase 07: TTL filtering in context builder.
- Primitives plan Phase 11: Bumps NPC roster limit.
- Arc system plan Phase 06: Validates TTL filtering.

**No conflict.** Primitives implements; arc system validates.

### 2.36 `narrate.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Primitives plan Phase 09: Wires hints into narrator.
- Primitives plan Phase 07: TTL filtering in narrate.py (already present, no change needed).
- Arc system plan: No narrate.py changes (delegated to primitives).
- Seed worldbuilding plan: No narrate.py changes (delegated to primitives).

**No conflict.**

### 2.37 `extraction/storytell.py` Changes — Consistent

- Primitives plan Phase 07: TTL filtering in storytell.py.
- Primitives plan Phase 09: Wires hints into storyteller.
- Arc system plan Phase 02: Collects `world_state_candidate` in turn_state.py (not storytell.py — the storyteller emits the field, turn_state collects it).

**No conflict.** Primitives implements TTL and hints; arc system validates and adds collection in turn_state.

### 2.38 `ev/` tools Changes — Consistent

- Primitives plan Phase 01: Removes deleted fields from ev tools.
- Primitives plan Phase 02: Updates references to renamed fields in ev tools.
- Arc system plan: No ev/ changes (delegated to primitives).
- Seed worldbuilding plan: No ev/ changes (delegated to primitives).

**No conflict.**

### 2.39 `server/tv.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.40 `state/delta_builder.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.41 `engine/changes.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.42 `engine/extraction/pipeline.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.43 `ev/checkers/` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` validation from checkers.
- Primitives plan Phase 02: Updates checkers to use renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.44 `prompts/sections/_arc.j2` Changes — Consistent

- Primitives plan Phase 02: Renames `current_arc` → `current_objective`, `visible_goal` → `long_term_objective`.
- Primitives plan Phase 07: TTL filtering, removes `[:15]` cap, renames "Previously Resolved Arcs" to "Recently Resolved Arcs".
- Arc system plan Phase 06: Validates TTL filtering and template changes.

**No conflict.** Primitives implements; arc system validates.

### 2.45 `prompts/sections/_world_state.j2` Changes — Consistent

- Seed worldbuilding plan Phase 11: Replaces `fact.tier == "permanent"` check with `fact.permanent` boolean, renders tier/valence badges.
- Primitives plan: No _world_state.j2 changes (delegated to seed worldbuilding).
- Arc system plan: No _world_state.j2 changes (delegated to seed worldbuilding).

**No conflict.**

### 2.46 `prompts/storytell_user.j2` Changes — Consistent

- Seed worldbuilding plan Phase 11: Renders tier/valence badges.
- Primitives plan: No storytell_user.j2 changes.
- Arc system plan: No storytell_user.j2 changes.

**No conflict.**

### 2.47 `prompts/narrate_user.j2` Changes — Consistent

- Primitives plan Phase 01: Removes "Past Resolutions" section.
- Arc system plan: No narrate_user.j2 changes (delegated to primitives).
- Seed worldbuilding plan: No narrate_user.j2 changes (delegated to primitives).

**No conflict.**

### 2.48 `prompts/sanitize_thread.j2` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` from sanitizer prompt.
- Primitives plan Phase 06: Updates dormant threshold references ("4+ turns" → "8+ turns").
- Seed worldbuilding plan Phase 10: Adds world state instructions to sanitizer prompt.

**No conflict.** Primitives does cleanup and threshold updates; seed worldbuilding adds world state instructions.

### 2.49 `prompts/ruling_user.j2` Changes — Consistent

- Primitives plan Phase 10: Adds `pc.situation` section to ruling prompt.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.50 `templates/_state_left.html` Changes — Consistent

- Primitives plan Phase 02: Renames `visible_goal` → `long_term_objective`, `goal_context` → `arc_origin`.
- Seed worldbuilding plan Phase 13: Renders `arc_origin` in UI sidebar.

**No conflict.** Primitives renames; seed worldbuilding adds rendering.

### 2.51 `templates/_state_right.html` Changes — Consistent

- Seed worldbuilding plan Phase 06: Updates tier-based display logic to use new `tier`/`permanent` fields.
- Primitives plan: No _state_right.html changes.
- Arc system plan: No _state_right.html changes.

**No conflict.**

### 2.52 `templates/_save_picker.html` Changes — Consistent

- Primitives plan Phase 02: Renames `visible_goal` → `long_term_objective` (with a [QUESTION] in the plan about whether to render `arc_origin` instead).
- Seed worldbuilding plan Phase 13: Renders `arc_origin` in save picker.

**Potential conflict in primitives plan Phase 02:** The plan has a `[QUESTION]` about `_save_picker.html:29` — "rename `visible_goal` to `long_term_objective` (shows goal) or render `arc_origin` (shows origin story)? Design doc says arc_origin, but code references `visible_goal` not `goal_context`."

The seed worldbuilding plan Phase 13 resolves this by rendering `arc_origin` in the save picker. But the primitives plan's Phase 02 still has the question unresolved. Since primitives runs first, the primitives plan should either:
(a) Render `arc_origin` in the save picker (matching the design doc), or
(b) Defer the save picker change to the seed worldbuilding plan.

**This is a minor inconsistency.** The primitives plan's Phase 02 should not have the question — it should make a decision. The design doc (D6) says "render `arc_origin` in UI sidebar for initial arc display" and mentions `_save_picker.html` in the mechanical corrections. So the decision should be to render `arc_origin`.

### 2.53 `packs/golden-piracy/scenario.yaml` Changes — Consistent

- Primitives plan: Out of scope (delegated to seed worldbuilding).
- Seed worldbuilding plan Phase 14: Updates golden-piracy pack.
- Arc system plan: Out of scope (delegated to seed worldbuilding).

**No conflict.**

### 2.54 `config.py` Changes — Consistent

- Primitives plan: No explicit config.py phase, but design doc C12 mentions removing `thread_completion_threshold` from `EngineConfig`.
- Arc system plan: No config.py changes.
- Seed worldbuilding plan: No config.py changes.

**Potential gap in primitives plan:** The design doc's "Threshold Updates" section (C12) calls for removing `thread_completion_threshold: int = 3` from `config.py:184`. This is not explicitly called out in any primitives phase. Phase 01 mentions deletions broadly but doesn't list config.py.

**Recommendation: Add a phase or sub-step in primitives to remove `thread_completion_threshold` from config.py.**

### 2.55 `seed.py` Changes — Consistent

- Primitives plan Phase 04: Sets `started_turn` in seed pipeline.
- Seed worldbuilding plan: No explicit seed.py phase (funnel ordering is in the prompt, not seed.py).
- Arc system plan: No seed.py changes.

**No conflict.**

### 2.56 `ev/play.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.57 `ev/prompt_context.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.58 `ev/state_tools.py` Changes — Consistent

- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.59 `ev/audit.py` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` references.
- Primitives plan Phase 02: Updates references to renamed fields.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.60 `ev/checkers/arc_resolution_validity.py` Changes — Consistent

- Primitives plan Phase 01: Removes `goal_context` validation.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.61 `ev/checkers/goal_update_validity.py` Changes — Consistent

- Primitives plan Phase 02: Updates to use `long_term_objective`.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

### 2.62 `ev/checkers/arc_goals.py` Changes — Consistent

- Primitives plan Phase 02: Updates to use `long_term_objective`.
- Arc system plan: Out of scope (delegated to primitives).
- Seed worldbuilding plan: Out of scope (delegated to primitives).

**No conflict.**

---

## 3. Documentation Update Steps as Last Phase

### Primitives Plan
**No documentation phase.** The plan has no Phase 12 or similar for documentation updates. This is a gap. The design doc's "Mechanical Corrections" section references many files but does not explicitly call out documentation updates. Per AGENTS.md, "any code change touching a module, config key, model field, prompt, or public API requires corresponding updates to docs/architecture/ (pipeline/data shapes), docs/repomap.md (module boundaries/APIs), or AGENTS.md."

**Recommendation: Add a documentation phase to the primitives plan.** This should update:
- `docs/architecture/state-models.md` — all renames, deletions, additions
- `docs/architecture/cross-module-contracts.md` — thread lifecycle, extraction routing, state model references
- `docs/architecture/step2c-storytell.md` — extraction fields, new model fields
- `docs/architecture/step2a-scene.md` — thread_update fields
- `docs/architecture/OVERVIEW.md` — TTL strategy, pressure score system, state data shapes
- `docs/repomap.md` — module boundaries, signatures, public APIs
- `AGENTS.md` — build commands, signposts, conventions if needed

### Arc System Plan
**Phase 09: Documentation updates.** Covers design doc status, OVERVIEW.md, step2c-storytell.md, repomap.md, AGENTS.md. Good.

**Recommendation: Scope to arc-specific docs only.** The seed worldbuilding plan's Phase 15 will do comprehensive documentation updates. The arc system's Phase 09 should focus on:
- Design doc status update
- OVERVIEW.md: `world_state_candidates` section
- step2c-storytell.md: `world_state_candidate` on ThreadResolution
- repomap.md: `state["world_state_candidates"]` key, `_apply_thread_resolutions` signature

### Seed Worldbuilding Plan
**Phase 15: Documentation updates.** Comprehensive — covers state-models.md, cross-module-contracts.md, step2c-storytell.md, step2a-scene.md, repomap.md, OVERVIEW.md, AGENTS.md. Good.

**Recommendation: This should be the final documentation phase.** Since it runs last, it should be the comprehensive update that catches anything the arc system's Phase 09 missed.

---

## 4. Summary of Issues Found

### Resolved Issues (Decisions Made 2026-06-23)

1. **Primitives plan missing documentation phase.** → **RESOLVED.** Add Phase 12 to primitives plan covering state-models.md, cross-module-contracts.md, step2c-storytell.md, step2a-scene.md, OVERVIEW.md, repomap.md, AGENTS.md.

2. **Primitives plan missing `thread_completion_threshold` removal from config.py.** → **RESOLVED.** Add a sub-step in primitives Phase 01 or a new phase to remove `thread_completion_threshold` from config.py.

3. **Primitives plan Phase 02 has unresolved `[QUESTION]` about `_save_picker.html:29`.** → **RESOLVED.** Primitives Phase 02 should rename `visible_goal` → `long_term_objective` in _save_picker.html. Seed worldbuilding Phase 13 renders `arc_origin` in save picker separately.

4. **Primitives plan does not explicitly call out `WorldStateFact` replacement.** → **RESOLVED.** Primitives Phase 03 should add `WorldStateFact` replacement (old→new schema). Seed worldbuilding Phase 05 handles downstream effects (code that branches on old values, rendering).

### No Conflicts Found

All three plans are consistent with each other on:
- Execution order
- `arc_origin` placement
- `goal_context` deletion
- TTL strategy
- Pressure score system
- `major_update_signal` values
- Thread → world state promotion (two-step)
- `pc.situation`
- `goal_update` format
- NPC roster limit
- Key locations
- Pack update
- Documentation update division (arc system = arc-specific, seed worldbuilding = comprehensive final)
- All file-level changes across all modules

---

## 5. Questions for Further Research in Codebase

The following items need codebase verification to confirm the plans are faithful to the actual code:

1. **`_save_picker.html:29`** — Does the current code reference `visible_goal` or `goal_context`? The primitives plan's `[QUESTION]` suggests it references `visible_goal`, but the design doc says to render `arc_origin`. Need to verify.

2. **`config.py:184`** — Does `thread_completion_threshold: int = 3` exist in EngineConfig? Primitives plan should remove it but no phase calls it out.

3. **`turn_state.py:225-233`** — Does the `turns_since` warning guard exist? Primitives plan Phase 01 should delete it.

4. **`turn_state.py:161-182`** — Does auto-completion block exist? Design doc says to delete it but no primitives phase calls it out explicitly.

5. **`config.py:184`** — Does `thread_completion_threshold` exist? Design doc C12 calls for removal but no phase implements it.

6. **`narrate_user.j2:59-61`** — Does "Past Resolutions" section exist? Primitives plan Phase 01 should delete it.

7. **`_arc.j2:21`** — Does `[:15]` hard cap exist? Primitives plan Phase 07 should remove it.

8. **`storytell_system.j2:68`** — Does stale `drop_threads` prohibition exist? Arc system plan Phase 07 should validate its removal.

9. **`turn_state.py:341-349`** — Does `promote_to_world_state` handling exist? Primitives plan Phase 01 should delete it.

10. **`turn_state.py:346,348`** — Does old tier value branching (`"persistent"`) exist? Seed worldbuilding plan Phase 06 should update it.

11. **`seed.py:404`** — Does old tier value branching (`"permanent"`) exist? Seed worldbuilding plan Phase 06 should update it.

12. **`_state_right.html:75,78`** — Does old tier value branching exist? Seed worldbuilding plan Phase 06 should update it.

13. **`storytell_system.j2:46`** — Does "permanent world fact" text reference exist? Seed worldbuilding plan Phase 06 should update it.

14. **`thread_sanitizer.py:238-240`** — Does "shift" coercion exist? Primitives plan should remove it.

15. **`prompt_context.py:25-53`** — Does NPC roster limit of 10 exist? Primitives plan Phase 11 should bump to 12.

16. **`turn_state.py:116`** — Does `dormant_threshold = 4` exist? Primitives plan Phase 06 should change to 8.

17. **`sanitize_thread.j2:51`** — Does "4+ turns" dormant guidance exist? Primitives plan Phase 06 should change to "8+ turns".

18. **`packs/golden-piracy/scenario.yaml`** — Does it currently have deleted fields (`goal_context`, `chapter_end`, etc.)? Seed worldbuilding plan Phase 14 should remove them.

19. **`packs/golden-piracy/scenario.yaml`** — Does it currently have `pc_situation_schema`? Seed worldbuilding plan Phase 14 should add it.

20. **`state.py:150-154`** — Does old `WorldStateFact` schema exist? Seed worldbuilding plan Phase 05 should replace it.

21. **`state.py:79-85`** — Does `CampaignArc` class exist? Primitives plan Phase 02 should rename to `LongTermObjective`.

22. **`state.py:80`** — Does `visible_goal` field exist in CampaignArc? Primitives plan Phase 02 should rename to `long_term_objective`.

23. **`state.py:43`** — Does `progress: list[ProgressEntry]` exist in ArcThread? Primitives plan Phase 02 should rename to `major_updates`.

24. **`state.py:170`** — Does `progress_kind` exist in ThreadUpdate? Primitives plan Phase 02 should rename to `major_update_signal`.

25. **`state.py:22`** — Does `Literal["advancement", "setback", "shift"]` exist in ProgressEntry? Primitives plan Phase 02 should remove "shift".

26. **`extraction.py:231`** — Does `goal_update: str | None` exist in StorytellerResult? Primitives plan Phase 05 should change to `dict | None`.

27. **`state/io.py:93`** — Does `_default_state()` have `state["arc"]` key? Primitives plan Phase 02 should rename to `state["long_term_objective"]`.

28. **`state/io.py:93`** — Does `_default_state()` have `goal_context`? Primitives plan Phase 01 should remove it.

29. **`state/io.py:93`** — Does `_default_state()` have `world_state_candidates`? Primitives plan Phase 03 should add it.

30. **`state/io.py`** — Does `_default_state()` have `pc.situation`? Seed worldbuilding plan Phase 02 should add it.

31. **`state/io.py`** — Does `_default_state()` have `world.locations`? Seed worldbuilding plan Phase 04 should add it.

32. **`pack.py`** — Does `SeedState` have `arc_origin`? Seed worldbuilding plan Phase 01 should add it.

33. **`pack.py`** — Does `SeedPC` have `pc.situation`? Seed worldbuilding plan Phase 02 should add it.

34. **`pack.py`** — Does `ScenarioBrief` have `pc_situation_schema`? Seed worldbuilding plan Phase 02 should add it.

35. **`turn.py`** — Does TTL expiry pass exist? Seed worldbuilding plan Phase 07 should add it.

36. **`engine/hints.py`** — Does it exist? Primitives plan Phase 08 should create it.

37. **`ruling.py`** — Does `pc.situation` exist in ruling context? Primitives plan Phase 10 should add it.

38. **`ruling_user.j2`** — Does `pc.situation` section exist? Primitives plan Phase 10 should add it.

39. **`_arc.j2:12-16`** — Does "Previously Resolved Arcs" exist? Primitives plan Phase 07 should rename to "Recently Resolved Arcs".

40. **`_arc.j2:3,6,9`** — Does `current_arc` variable exist? Primitives plan Phase 02 should rename to `current_objective`.

41. **`_arc.j2:3,6,9`** — Does `visible_goal` exist in _arc.j2? Primitives plan Phase 02 should rename to `long_term_objective`.

42. **`storytell_system.j2:14`** — Does arc_resolve example have `goal_context`, `drop_threads`, `new_threads`? Primitives plan Phase 01 should remove them.

43. **`storytell_system.j2:14`** — Does arc_resolve example have `visible_goal`? Primitives plan Phase 02 should rename to `long_term_objective`.

44. **`storytell_system.j2:11`** — Does thread_resolve example have `promote_to_world_state`? Primitives plan Phase 01 should remove it.

45. **`storytell_system.j2:11`** — Does thread_resolve example have `resolved_turn` and `world_state_candidate`? Arc system plan Phase 04 should add them.

46. **`storytell_system.j2:12-13`** — Do thread_update and thread_add examples have `type` field? Arc system plan Phase 08 should validate.

47. **`storytell_system.j2:39`** — Does REQUIRED directive exist? Arc system plan Phase 08 should validate.

48. **`storytell_system.j2:66`** — Does "Emit **only** when:" language exist? Arc system plan Phase 07 should validate.

49. **`storytell_system.j2:72`** — Does contrasting example use `long_term_objective`? Arc system plan Phase 07 should validate.

50. **`generate_seed_system.j2:37,64`** — Does `goal_context` exist in seed prompt? Primitives plan Phase 01 should remove, Phase 02 should rename to `arc_origin`.

51. **`generate_seed_system.j2:63-64`** — Does `visible_goal` exist in seed prompt? Primitives plan Phase 02 should rename to `long_term_objective`.

52. **`_state_left.html:63,109`** — Does `visible_goal` exist in UI sidebar? Primitives plan Phase 02 should rename to `long_term_objective`.

53. **`_state_left.html:64,109`** — Does `goal_context` exist in UI sidebar? Primitives plan Phase 02 should rename to `arc_origin`.

54. **`_state_left.html:64`** — Does `arc_origin` rendering exist? Seed worldbuilding plan Phase 13 should add it.

55. **`_save_picker.html:29`** — Does `visible_goal` exist in save picker? Primitives plan Phase 02 should rename to `long_term_objective` (or render `arc_origin` per design doc).

56. **`_save_picker.html:29`** — Does `arc_origin` rendering exist? Seed worldbuilding plan Phase 13 should add it.

57. **`_world_state.j2:6`** — Does `fact.tier == "permanent"` check exist? Seed worldbuilding plan Phase 11 should replace with `fact.permanent`.

58. **`storytell_user.j2`** — Does tier/valence badge rendering exist? Seed worldbuilding plan Phase 11 should add it.

59. **`sanitize_thread.j2:15,86`** — Does `goal_context` exist in sanitizer prompt? Primitives plan Phase 01 should remove.

60. **`sanitize_thread.j2:48`** — Does abandonment criteria reference "4+ turns" or "5+ turns"? Primitives plan Phase 06 should align with TTL strategy.

61. **`sanitize_thread.j2:51`** — Does "4+ turns" dormant guidance exist? Primitives plan Phase 06 should change to "8+ turns".

62. **`turn_state.py:249`** — Does `goal_context` exist in resolved_arcs entry? Primitives plan Phase 01 should remove.

63. **`turn_state.py:266`** — Does `goal_context` exist in successor arc construction? Primitives plan Phase 01 should remove.

64. **`turn_state.py:534-541`** — Does `goal_context` exist in goal_update path? Primitives plan Phase 05 should update to use `long_term_objective`.

65. **`turn_state.py:235-243`** — Does `drop_threads` filtering exist? Primitives plan Phase 01 should remove.

66. **`turn_state.py:264-270`** — Does `new_threads` exist in successor arc construction? Primitives plan Phase 01 should remove.

67. **`turn_state.py:334-338`** — Does `world_state_candidate` collection exist? Arc system plan Phase 02 should add it.

68. **`thread_sanitizer.py:143,150`** — Does `goal_context` exist in template context? Primitives plan Phase 01 should remove.

69. **`thread_sanitizer.py:219-222`** — Does `_apply_goal_update` validate `goal_context`? Primitives plan Phase 05 should update to use `long_term_objective`.

70. **`thread_sanitizer.py:340-345`** — Does `_apply_goal_update` apply `goal_context` to `arc.goal_context`? Primitives plan Phase 05 should remove.

71. **`thread_sanitizer.py:238-240`** — Does "shift" coercion exist? Primitives plan should remove.

72. **`thread_sanitizer.py:146`** — Does `resolved_turn` pass to sanitizer's `completed_threads` context? Primitives plan Phase 04 should add it.

73. **`narrate.py:65`** — Does `visible_goal` exist in narrate context? Primitives plan Phase 02 should rename to `long_term_objective`.

74. **`narrate.py:80`** — Does TTL filtering exist in narrate path? Primitives plan Phase 07 should verify.

75. **`narrate.py:128-136`** — Does `_filter_completed_threads()` exist? Primitives plan Phase 07 should verify.

76. **`extraction/pipeline.py:227`** — Does `visible_goal` exist in extraction pipeline? Primitives plan Phase 02 should rename to `long_term_objective`.

77. **`engine/changes.py:285-286`** — Does `visible_goal` exist in change detection? Primitives plan Phase 02 should rename to `long_term_objective`.

78. **`state/delta_builder.py:53-55`** — Does `visible_goal` exist in delta builder? Primitives plan Phase 02 should rename to `long_term_objective`.

79. **`ev/prompt_context.py:217`** — Does `visible_goal` exist in prompt context? Primitives plan Phase 02 should rename to `long_term_objective`.

80. **`ev/state_tools.py:472,1029,1111`** — Does `visible_goal` or `CampaignArc` exist in state tools? Primitives plan Phase 02 should rename.

81. **`ev/play.py:503,525`** — Does `visible_goal` exist in turn context? Primitives plan Phase 02 should rename to `long_term_objective`.

82. **`server/tv.py:408`** — Does `visible_goal` exist in server TV? Primitives plan Phase 02 should rename to `long_term_objective`.

83. **`ev/audit.py:312,321,325`** — Does `goal_context` exist in audit? Primitives plan Phase 01 should remove, Phase 02 should rename.

84. **`ev/checkers/arc_resolution_validity.py:64-69`** — Does `goal_context` validation exist? Primitives plan Phase 01 should remove.

85. **`ev/checkers/goal_update_validity.py:56,58`** — Does `visible_goal` validation exist? Primitives plan Phase 02 should rename to `long_term_objective`.

86. **`ev/checkers/arc_goals.py:38,40`** — Does `visible_goal` validation exist? Primitives plan Phase 02 should rename to `long_term_objective`.

87. **`turn_state.py:140,153,595`** — Does `urgency_set_turn` exist? Primitives plan design doc says to keep it.

88. **`seed.py:371-384`** — Does `urgency_set_turn` exist? Primitives plan design doc says to keep it.

89. **`turn_state.py:341-349`** — Does `promote_to_world_state` handling exist? Primitives plan Phase 01 should remove.

90. **`turn_state.py:116`** — Does `dormant_threshold = 4` exist? Primitives plan Phase 06 should change to 8.

91. **`turn_state.py:229`** — Does `if turns_since < 5` exist? Design doc C13 says to change to 8. Primitives plan Phase 06 should update.

92. **`config.py:184`** — Does `thread_completion_threshold: int = 3` exist? Design doc C12 says to remove. Primitives plan should add phase.

93. **`packs/golden-piracy/scenario.yaml`** — Does it have `inspiration.pc`, `inspiration.npcs`, `inspiration.inventory`, `world_facts`, `forbid_cliches`, `pc_stat_range`, `pc_stat_total_range`? Primitives plan Phase 01 should remove, seed worldbuilding plan Phase 14 should remove.

94. **`packs/golden-piracy/scenario.yaml`** — Does it have `scene_detail_bundles`? Seed worldbuilding plan Phase 14 should expand.

95. **`packs/golden-piracy/scenario.yaml`** — Does it have archetype pools? Seed worldbuilding plan Phase 14 should audit.

96. **`packs/golden-piracy/scenario.yaml`** — Does it currently have `pc_situation_schema`? Seed worldbuilding plan Phase 14 should add.

97. **`docs/architecture/OVERVIEW.md`** — Does it document `world_state_candidates`? Arc system plan Phase 09 should add, seed worldbuilding plan Phase 15 should verify.

98. **`docs/architecture/step2c-storytell.md`** — Does it document `world_state_candidate` on ThreadResolution? Arc system plan Phase 09 should add, seed worldbuilding plan Phase 15 should verify.

99. **`docs/repomap.md`** — Does it document `state["world_state_candidates"]`? Arc system plan Phase 09 should add, seed worldbuilding plan Phase 15 should verify.

100. **`AGENTS.md`** — Does it need updates for arc plan completion? Arc system plan Phase 09 should add, seed worldbuilding plan Phase 15 should verify.

---

## 6. Questions Resolved (2026-06-23)

1. **Primitives plan has no documentation phase.** → **ADD.** Add Phase 12 to primitives plan covering state-models.md, cross-module-contracts.md, step2c-storytell.md, step2a-scene.md, OVERVIEW.md, repomap.md, AGENTS.md.

2. **Primitives plan Phase 02 has an unresolved [QUESTION] about _save_picker.html:29.** → **RENDER `long_term_objective`.** Primitives Phase 02 should rename `visible_goal` → `long_term_objective` in _save_picker.html. Seed worldbuilding Phase 13 renders `arc_origin` in save picker separately.

3. **Design doc C12 calls for removing thread_completion_threshold from config.py but no primitives phase implements it.** → **ADD PHASE.** Add a sub-step in primitives Phase 01 or a new phase to remove `thread_completion_threshold` from config.py.

4. **WorldStateFact replacement — should it be in primitives (model replacement) or seed worldbuilding (downstream effects)?** → **PRIMITIVES REPLACES MODEL, SEED EXTENDS.** Primitives Phase 03 should add `WorldStateFact` replacement (old→new schema). Seed worldbuilding Phase 05 handles downstream effects (code that branches on old values, rendering).
