# Plan: Arc, Thread, and Seed Generation Refactor

**Derived from:**
- [01-Primitives](../design/01-primitives.md)
- [02-Arc System Redesign](../design/02-arc-system-redesign.md)
- [03-Seed Worldbuilding Redesign](../design/03-seed-worldbuilding-redesign.md)
- [Discovery](../discovery/arc-system-problems.md)

**Branch:** `arc-thread-seed-gen-refactor`
**Date:** 2026-06-23

---

## Purpose

Comprehensive refactor of the arc system, thread lifecycle, and seed generation pipeline. Three design docs are ready. This plan executes all three in a single worktree/branch.

## Problem

Eval data shows threads accumulate without resolution, arc resolution fires too frequently with no-op goal updates, and the system never closes narrative arcs. The current model needs a fundamental redesign.

## Scope

All three design docs in a single worktree/branch (`arc-thread-seed-gen-refactor`).

## Out of Scope

- Convergence starvation (pacing engine — separate bug ticket)
- Beat driver always "motivation" (NPC roster data — separate bug ticket)
- Dynamic factions (deferred)
- Multiple concurrent arcs (deferred)
- Thread urgency graduated states (deferred)
- External inventory (deferred)
- Pack parity (generated vs custom packs — deferred)
- Location tracking system (deferred)

## Design Reference

- [01-Primitives](../design/01-primitives.md)
- [02-Arc System Redesign](../design/02-arc-system-redesign.md)
- [03-Seed Worldbuilding Redesign](../design/03-seed-worldbuilding-redesign.md)

## Execution Order

**Primitives → Arc System → Seed Worldbuilding.**

The primitives document defines shared building blocks. The arc system redesign defines `arc_origin`/`long_term_objective`/thread→world state. The seed worldbuilding redesign depends on those definitions.

This order ensures that when the arc system phase is executed, all shared primitives are already defined. When the seed worldbuilding phase is executed, both primitives and arc system are already defined.

## Firm Decisions

- **Clean break.** No backward compatibility with existing saves or pack schemas. Old saves are invalid under the new schema. No migration shims, no coercion validators, no deprecation stubs.
- **`arc_origin` on seed model only.** Never on LongTermObjective or ArcResolution. Never regenerated. Never injected into narrate, storytell, or ruling prompts.
- **`started_turn` only.** No `created_turn`. Set at arc construction time.
- **TTL strategy.** Completed/abandoned threads kept in data forever, TTL-filtered in prompts (3 turns). Dormant at 8 turns, archival at 13. No resurfacing hints.
- **Pressure score system.** Pure functions in `engine/hints.py`. Hint tiers: None/Soft/Strong/Imperative. No hard floors.
- **Two-step world state.** Storyteller flags `world_state_candidate`, sanitizer confirms every 5 turns with full array replacement authority.
- **NPC roster limit.** 10 → 12.
- **`goal_update` dict.** Just `long_term_objective` key. No `arc_origin`.
- **Thread type stability.** Stable by default. Changes require `reason` field.
- **No auto-arc-resolve.** Arc resolution is entirely storyteller-driven.
- **No auto-thread-completion.** Hard TTL on active threads removed.
- **`turns_since` warning guard.** Deleted entirely.
- **`major_update_signal` values.** `advancement` / `setback` only. `shift` removed.
- **`pc.situation` persist flag.** TBD at implementation time. Pack authors mark keys using a `persist: true` flag (or equivalent) on each `pc_situation_schema` entry.
- **Ruling context.** Extended to include `pc.situation` (persistent fields only). No arc fields added to ruling.

## Risks

- **Cascade deletions.** `goal_context` exists in 28+ locations. All callsites must be deleted simultaneously. Partial deletion breaks the engine.
- **Model renames.** `CampaignArc` → `LongTermObjective` and `state["arc"]` → `state["long_term_objective"]` touch imports, engine code, prompts, templates, and UI.
- **Prompt structural changes.** Removing completed threads from storyteller's prompt, TTL filtering in context builder, and pressure score hint injection all change prompt structure in ways that may affect LLM behavior.
- **Sanitizer extension.** Adding world state authority to the sanitizer is a significant behavior change. The sanitizer already handles threads; adding world state maintenance doubles its scope.
- **Pack update.** The golden-piracy pack needs `pc_situation_schema`, deleted fields removed, and `scene_detail_bundles` expanded. If pack update is delayed, the game runs without pc.situation but should not break.

---

## Phase 01: Primitives Clearing Pass

**Goal:** Delete all removed fields from schema, engine, prompts, packs, and ev tools.

**Scope:** This is the foundation. Everything else depends on this. All deletions must happen in a single phase — partial deletion breaks the engine.

### 1.1 Delete `goal_context` from all callsites

**Files:**
- `ccya/models/state.py:81` — remove `goal_context: str = ""` from CampaignArc
- `ccya/models/state.py:186` — remove `goal_context: str` from ArcResolution
- `ccya/engine/turn_state.py:249` — remove `goal_context` from resolved_arcs entry
- `ccya/engine/turn_state.py:266` — remove `goal_context` from successor arc construction
- `ccya/engine/turn_state.py:534-541` — update goal_update path (renamed in Phase 02)
- `ccya/engine/thread_sanitizer.py:143,150` — remove `goal_context` from template context
- `ccya/engine/thread_sanitizer.py:219-222` — remove `goal_context` validation in `_apply_goal_update`
- `ccya/engine/thread_sanitizer.py:340-345` — remove `goal_context` application to `arc.goal_context`
- `ccya/state/io.py:93` — remove `goal_context` from `_default_state()`
- `ccya/prompts/storytell_system.j2:14` — remove `goal_context` from arc_resolve example
- `ccya/prompts/sanitize_thread.j2:15,86` — remove `goal_context` from sanitizer prompt
- `ccya/prompts/generate_seed_system.j2:37,64` — update to `arc_origin` (renamed in Phase 02)
- `ccya/templates/_state_left.html:64,109` — update to `arc_origin` (renamed in Phase 02)
- `ccya/ev/checkers/arc_resolution_validity.py:64-69` — remove `goal_context` validation
- `ccya/ev/audit.py:312,321,325` — remove `goal_context` references
- `ccya/templates/_save_picker.html:29` — update to `arc_origin` (renamed in Phase 02)

**What:** Remove all references to `goal_context` from models, engine, prompts, templates, and ev tools.

**Why:** Replaced by `arc_origin` on the seed state model only. No backward compatibility.

**Validation:** `grep -r "goal_context" ccya/` returns zero matches (except in design docs).

### 1.2 Delete `chapter_end` from all callsites

**Files:**
- `ccya/models/state.py` — remove `chapter_end` from CampaignArc (if present)
- `ccya/prompts/storytell_system.j2:16,72,74` — remove `chapter_end` references
- `ccya/engine/turn_state.py` — remove `chapter_end` handling (if present)
- `ccya/pack.py` — remove `chapter_end` from pack schema (if present)
- All default pack YAML files — remove `chapter_end` references

**What:** Remove all references to `chapter_end`.

**Why:** No behavioral effect. Added as a patch for arc_resolve misuse. Adds cognitive load.

**Validation:** `grep -r "chapter_end" ccya/` returns zero matches.

### 1.3 Delete `ArcResolution.drop_threads` and `ArcResolution.new_threads`

**Files:**
- `ccya/models/state.py:185-186` — remove `drop_threads` and `new_threads` from ArcResolution
- `ccya/engine/turn_state.py:235-243` — remove `drop_threads` filtering logic; all threads carry forward
- `ccya/engine/turn_state.py:264-270` — remove `new_threads` from successor arc construction
- `ccya/prompts/storytell_system.j2:14` — update arc_resolve schema example to remove `drop_threads` and `new_threads`

**What:** Remove `drop_threads` and `new_threads` from ArcResolution model and all engine logic.

**Why:** Arc and thread lifecycles are fully decoupled. All threads carry forward automatically on arc resolution.

**Validation:** ArcResolution model has no `drop_threads` or `new_threads` fields. `_apply_arc_resolve()` carries all threads forward without filtering.

### 1.4 Delete `ArcResolution.new_threads`

**Files:**
- `ccya/models/state.py:186` — remove `new_threads: list[ArcThread]` from ArcResolution
- `ccya/engine/turn_state.py:264-270` — remove `new_threads` from successor arc construction
- `ccya/prompts/storytell_system.j2:14` — remove `new_threads` from arc_resolve example

**What:** Remove `new_threads` from ArcResolution model and all engine logic.

**Why:** Thread creation is decoupled from arc resolution. Storyteller emits `thread_add` independently on any turn.

**Validation:** ArcResolution model has no `new_threads` field.

### 1.5 Delete `turns_since` warning guard

**Files:**
- `ccya/engine/turn_state.py:225-233` — delete the warning block entirely

**What:** Delete the `turns_since` warning guard.

**Why:** Consistent with no-hard-floors principle. Hint tiers handle arc resolution frequency.

**Validation:** No `turns_since` warning guard in turn_state.py.

### 1.6 Delete `ThreadResolution.promote_to_world_state`

**Files:**
- `ccya/models/state.py:161` — remove `promote_to_world_state: bool = False` from ThreadResolution
- `ccya/prompts/storytell_system.j2:11` — remove `promote_to_world_state` from thread_resolve example
- `ccya/engine/turn_state.py:341,343` — remove `promote_to_world_state` handling

**What:** Remove `promote_to_world_state` from ThreadResolution model and all engine logic.

**Why:** Replaced by two-step candidate system (storyteller flags `world_state_candidate`, sanitizer confirms).

**Validation:** ThreadResolution model has no `promote_to_world_state` field.

### 1.7 Update ev checkers

**Files:**
- `ccya/ev/checkers/goal_update_validity.py:56,58` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/ev/checkers/arc_goals.py:38,40` — update to `long_term_objective` (renamed in Phase 02)

**What:** Update checker references to use new field names.

**Why:** Field renames in Phase 02.

**Validation:** Checkers reference `long_term_objective` instead of `visible_goal`.

### 1.8 Update ev tools

**Files:**
- `ccya/ev/state_tools.py:472,1029,1111` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/ev/prompt_context.py:217` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/ev/play.py:503,525` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/ev/audit.py:312,321,325` — update to `long_term_objective` (renamed in Phase 02)

**What:** Update ev tool references to use new field names.

**Why:** Field renames in Phase 02.

**Validation:** Ev tools reference `long_term_objective` instead of `visible_goal` and `state["arc"]` instead of `state["arc"]`.

### 1.9 Update server and other references

**Files:**
- `ccya/server/tv.py:408` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/engine/changes.py:285-286` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/state/delta_builder.py:53-55` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/engine/narrate.py:65` — update to `long_term_objective` (renamed in Phase 02)
- `ccya/engine/extraction/pipeline.py:227` — update to `long_term_objective` (renamed in Phase 02)

**What:** Update remaining references to use new field names.

**Why:** Field renames in Phase 02.

**Validation:** All references use `long_term_objective` instead of `visible_goal` and `state["long_term_objective"]` instead of `state["arc"]`.

### 1.10 Update Jinja2 templates

**Files:**
- `ccya/prompts/sections/_arc.j2:3,6,9` — rename `visible_goal` → `long_term_objective`
- `ccya/prompts/sections/_arc.j2:18-24` — remove `[:15]` hard cap, add TTL filtering (Phase 04)
- `ccya/prompts/sections/_arc.j2:12-16` — rename "Previously Resolved Arcs" to "Recently Resolved Arcs"
- `ccya/prompts/sections/_arc.j2:21` — replace `current_arc.completed_threads[:15]` with TTL-filtered `completed_threads` (Phase 04)
- `ccya/prompts/storytell_system.j2:72,76` — rename `visible_goal` → `long_term_objective`
- `ccya/prompts/generate_seed_system.j2:63-64` — rename `visible_goal` → `long_term_objective`, `goal_context` → `arc_origin`
- `ccya/prompts/narrate_user.j2:59-61` — remove "Past Resolutions" section
- `ccya/templates/_state_left.html:63,109` — update to `arc_origin`
- `ccya/templates/_save_picker.html:29` — update to `arc_origin`

**What:** Update all template references to use new field names and remove deleted sections.

**Why:** Field renames and deletions in Phase 01 and 02.

**Validation:** All templates reference new field names. "Past Resolutions" section removed from narrate_user.j2.

### 1.11 Update pack files

**Files:**
- All default pack YAML files — remove `goal_context`, `chapter_end`, `inspiration.pc`, `inspiration.npcs`, `inspiration.inventory`, `world_facts`, `forbid_cliches`, `pc_stat_range`, `pc_stat_total_range`
- `golden-piracy` pack — add `pc_situation_schema` (Phase 07)

**What:** Remove deleted fields from all pack files.

**Why:** Clean break. No backward compatibility.

**Validation:** `grep -r "goal_context\|chapter_end\|inspiration\.pc\|inspiration\.npcs\|inspiration\.inventory\|world_facts\|forbid_cliches\|pc_stat_range\|pc_stat_total_range" packs/` returns zero matches.

---

## Phase 02: Primitives Field Renames

**Goal:** Rename all fields throughout the codebase.

**Scope:** This phase touches many files. Each rename must be consistent across models, engine, prompts, templates, and ev tools.

### 2.1 Rename `CampaignArc` → `LongTermObjective`

**Files:**
- `ccya/models/state.py:79-85` — rename class `CampaignArc` to `LongTermObjective`
- All imports throughout codebase — update `from ccya.models import CampaignArc` → `from ccya.models import LongTermObjective`
- `ccya/engine/turn_state.py` — update all references to `CampaignArc`
- `ccya/engine/thread_sanitizer.py` — update all references to `CampaignArc`
- `ccya/engine/seed.py` — update all references to `CampaignArc`
- `ccya/engine/narrate.py` — update all references to `CampaignArc`
- `ccya/engine/ruling.py` — update all references to `CampaignArc`
- `ccya/state/delta_builder.py` — update all references to `CampaignArc`
- `ccya/ev/state_tools.py` — update all references to `CampaignArc`
- `ccya/ev/audit.py` — update all references to `CampaignArc`
- `ccya/server/tv.py` — update all references to `CampaignArc`

**What:** Rename the `CampaignArc` class to `LongTermObjective` throughout.

**Why:** Consistent with LLM-naming principle; the model name should signal duration and scope to the LLM.

**Validation:** `grep -r "CampaignArc" ccya/` returns zero matches (except in design docs).

### 2.2 Rename `state["arc"]` → `state["long_term_objective"]`

**Files:**
- `ccya/state/io.py` — rename `state["arc"]` key to `state["long_term_objective"]` in `_default_state()`
- `ccya/engine/turn_state.py` — update all references to `state["arc"]`
- `ccya/engine/thread_sanitizer.py` — update all references to `state["arc"]`
- `ccya/engine/narrate.py` — update all references to `state["arc"]`
- `ccya/engine/ruling.py` — update all references to `state["arc"]`
- `ccya/state/delta_builder.py` — update all references to `state["arc"]`
- `ccya/ev/state_tools.py` — update all references to `state["arc"]`
- `ccya/ev/audit.py` — update all references to `state["arc"]`
- `ccya/server/tv.py` — update all references to `state["arc"]`

**What:** Rename the state key from `state["arc"]` to `state["long_term_objective"]`.

**Why:** Consistent with the model rename. The state key should match the model name.

**Validation:** `grep -r 'state\["arc"\]' ccya/` returns zero matches (except in design docs).

### 2.3 Rename `visible_goal` → `long_term_objective`

**Files:**
- `ccya/models/state.py:80` — rename `visible_goal` to `long_term_objective` in LongTermObjective
- `ccya/engine/turn_state.py:247,265,534` — update all references
- `ccya/engine/thread_sanitizer.py:142,149` — update all references
- `ccya/prompts/context.py:110,149` — update all references
- `ccya/engine/narrate.py:65` — update all references
- `ccya/engine/extraction/pipeline.py:227` — update all references
- `ccya/ev/prompt_context.py:217` — update all references
- `ccya/ev/state_tools.py:472,1029,1111` — update all references
- `ccya/ev/play.py:503,525` — update all references
- `ccya/server/tv.py:408` — update all references
- `ccya/engine/changes.py:285-286` — update all references
- `ccya/state/delta_builder.py:53-55` — update all references
- `ccya/prompts/sections/_arc.j2:3,6,9` — update all references
- `ccya/prompts/storytell_system.j2:72,76` — update all references
- `ccya/prompts/generate_seed_system.j2:63-64` — update all references

**What:** Rename `visible_goal` to `long_term_objective` throughout.

**Why:** "Long-term" signals update frequency and duration. "Objective" avoids immediate-completion trigger.

**Validation:** `grep -r "visible_goal" ccya/` returns zero matches (except in design docs).

### 2.4 Rename `progress` → `major_updates`

**Files:**
- `ccya/models/state.py:43` — rename `progress: list[ProgressEntry]` to `major_updates: list[MajorUpdateEntry]` in ArcThread
- All code references (100+ matches in grep) — update to `major_updates`

**What:** Rename `progress` to `major_updates` in ArcThread model and all references.

**Why:** "Major" signals "only when something worth noting happens." Not a running play-by-play.

**Validation:** `grep -r "\.progress" ccya/ | grep -i "thread\|arc" | grep -v "major_updates" | grep -v "progress_kind" | grep -v "progress_entry" | grep -v "design" | grep -v "check" | grep -v "ev/"` returns zero matches.

### 2.5 Rename `progress_kind` → `major_update_signal`

**Files:**
- `ccya/models/state.py:170` — rename `progress_kind` to `major_update_signal` in ThreadUpdate
- All code references — update to `major_update_signal`

**What:** Rename `progress_kind` to `major_update_signal` in ThreadUpdate model and all references.

**Why:** "Signal" is more descriptive.

**Validation:** `grep -r "progress_kind" ccya/` returns zero matches (except in design docs).

### 2.6 Rename `goal_context` → `arc_origin` in prompts

**Files:**
- `ccya/prompts/generate_seed_system.j2:37,64` — rename `goal_context` to `arc_origin`
- `ccya/templates/_state_left.html:64,109` — rename `goal_context` to `arc_origin`
- `ccya/templates/_save_picker.html:29` — rename `goal_context` to `arc_origin`

**What:** Rename `goal_context` to `arc_origin` in prompts and templates.

**Why:** "How did the PC end up here?" Past tense, 2–3 sentences. Seed-time field only, never regenerated.

**Validation:** `grep -r "goal_context" ccya/prompts/ ccya/templates/` returns zero matches.

### 2.7 Update `goal_update` format

**Files:**
- `ccya/models/extraction.py:231` — change `goal_update: str | None` to `goal_update: dict | None` in StorytellerResult
- `ccya/engine/thread_sanitizer.py:219-222` — update `_apply_goal_update` to use `long_term_objective` key only
- `ccya/engine/thread_sanitizer.py:340-345` — remove `goal_context` application (deleted in Phase 01)
- `ccya/engine/turn_state.py:534-536` — update to apply dict to `long_term_objective` field only

**What:** Change `goal_update` from `str | None` to `dict | None` with `long_term_objective` key.

**Why:** Structural decoupling. The storyteller should not be generating `arc_origin` mid-game.

**Validation:** `StorytellerResult.goal_update` is `dict | None` with `long_term_objective` key.

### 2.8 Update Jinja2 template variable names

**Files:**
- `ccya/prompts/sections/_arc.j2` — rename `current_arc` to `current_objective` (or equivalent consistent name)
- All templates using `current_arc` — rename variable to `current_objective`

**What:** Rename template variable from `current_arc` to `current_objective`.

**Why:** Consistent with the model rename.

**Validation:** No template references `current_arc`.

---

## Phase 03: Primitives Model Updates

**Goal:** Add new fields, update models.

### 3.1 Add `started_turn` to LongTermObjective

**Files:**
- `ccya/models/state.py:79-85` — add `started_turn: int | None = None` to LongTermObjective (no `created_turn`)
- `ccya/state/io.py:93` — add initialization in `_default_state()`
- `ccya/engine/seed.py` — set `started_turn` when arc is created in seed pipeline
- `ccya/engine/turn_state.py:264-270` — set `started_turn` in `_apply_arc_resolve()` when successor arc is constructed

**What:** Add `started_turn: int | None = None` to LongTermObjective model.

**Why:** Single source of truth for arc age. Used in pressure score duration weight calculation.

**Validation:** LongTermObjective has `started_turn` field. Seed pipeline sets it. `_apply_arc_resolve()` sets it for successor arcs.

### 3.2 Add `reason` to ThreadUpdate

**Files:**
- `ccya/models/state.py:170` — add `reason: str | None` to ThreadUpdate model
- `ccya/prompts/storytell_system.j2` — instruct storyteller to provide reason when changing thread type
- `ccya/prompts/sanitize_thread.j2` — instruct sanitizer to provide reason when changing thread type

**What:** Add `reason: str | None` to ThreadUpdate model.

**Why:** Thread type changes require a narrative justification. Stable by default.

**Validation:** ThreadUpdate has `reason` field. Storyteller and sanitizer prompts instruct to provide reason.

### 3.3 Update `ProgressEntry.kind` literal

**Files:**
- `ccya/models/state.py:22` — change `Literal["advancement", "setback", "shift"]` to `Literal["advancement", "setback"]`

**What:** Remove `shift` from ProgressEntry.kind literal.

**Why:** Two values only: advancement and setback. Shift described dimensional change, not directional progress, and had no distinguishing value from a low-signal advancement.

**Validation:** `ProgressEntry.kind` accepts only "advancement" and "setback".

### 3.4 Update `ThreadUpdate.major_update_signal` literal

**Files:**
- `ccya/models/state.py:170` — rename `progress_kind` to `major_update_signal` with `Literal["advancement", "setback"]`

**What:** Rename `progress_kind` to `major_update_signal` and update literal.

**Why:** Consistent with ProgressEntry.kind rename.

**Validation:** `ThreadUpdate.major_update_signal` accepts only "advancement" and "setback".

### 3.5 Add `world_state_candidates` to `_default_state()`

**Files:**
- `ccya/state/io.py` — add `world_state_candidates: []` to `_default_state()`

**What:** Add `world_state_candidates` list to default state.

**Why:** Collects `world_state_candidate` from ThreadResolution for sanitizer evaluation.

**Validation:** `_default_state()` includes `world_state_candidates: []`.

### 3.6 Update `ThreadResolution` model

**Files:**
- `ccya/models/state.py:156-161` — add `resolved_turn: int | None` and `world_state_candidate: str | None` to ThreadResolution (remove `promote_to_world_state` in Phase 01)

**What:** Add `resolved_turn` and `world_state_candidate` to ThreadResolution.

**Why:** `resolved_turn` for TTL evaluation. `world_state_candidate` for two-step world state promotion.

**Validation:** ThreadResolution has `resolved_turn` and `world_state_candidate` fields.

### 3.7 Update `ArcResolution` model

**Files:**
- `ccya/models/state.py:183-188` — final model: `resolution: str`, `long_term_objective: str` (remove `goal_context`, `drop_threads`, `new_threads`, `visible_goal` in Phase 01 and 02)

**What:** Final ArcResolution model: `resolution: str`, `long_term_objective: str`.

**Why:** Arc resolution is scoped to arc lifecycle only. No thread operations.

**Validation:** ArcResolution has exactly two fields: `resolution` and `long_term_objective`.

---

## Phase 04: Primitives TTL Strategy

**Goal:** Implement TTL filtering, remove hard caps, update dormant thresholds.

### 4.1 Update dormant threshold

**Files:**
- `ccya/engine/turn_state.py:116` — change `dormant_threshold = 4` to `dormant_threshold = 8`
- `ccya/engine/turn_state.py:229` — change `if turns_since < 5` to `if turns_since < 8` (or remove entirely in Phase 01)

**What:** Update dormant threshold from 4 to 8 turns.

**Why:** 8 turns gives threads more breathing room before auto-dormant.

**Validation:** Dormant threshold is 8 turns in turn_state.py.

### 4.2 Update sanitizer dormant guidance

**Files:**
- `ccya/prompts/sanitize_thread.j2:51` — "If a thread has no activity in 4+ turns" → "If a thread has no activity in 8+ turns"
- `ccya/prompts/sanitize_thread.j2:48` — align abandonment criteria with TTL strategy (8 dormant + 5 archival = 13 turns total)

**What:** Update sanitizer prompt to reference 8-turn dormant threshold.

**Why:** Consistent with engine dormant threshold.

**Validation:** Sanitizer prompt references "8+ turns" for dormant guidance.

### 4.3 Implement TTL filtering in context builder

**Files:**
- `ccya/prompts/context.py` — add TTL filtering for completed_threads (3-turn TTL), following the same pattern as `_get_resolved_arcs()` in narrate.py:139
- Pass pre-filtered `completed_threads` to templates

**What:** Add TTL filtering in the context builder, not the template. Pass pre-filtered `completed_threads` to the template.

**Why:** TTL filtering in the context builder ensures bounded prompt load. Following the same pattern as `_get_resolved_arcs()` ensures consistency.

**Validation:** Context builder filters completed_threads to only those resolved within 3 turns.

### 4.4 Update `_arc.j2` for TTL filtering

**Files:**
- `ccya/prompts/sections/_arc.j2:21` — replace `current_arc.completed_threads[:15]` with TTL-filtered `completed_threads` from context builder
- `ccya/prompts/sections/_arc.j2:18-24` — remove `[:15]` hard cap, render all TTL-filtered threads
- `ccya/prompts/sections/_arc.j2:12-16` — rename "Previously Resolved Arcs" to "Recently Resolved Arcs"

**What:** Update `_arc.j2` to render TTL-filtered threads without hard cap.

**Why:** TTL filtering ensures bounded prompt load, so unbounded growth in data is acceptable.

**Validation:** `_arc.j2` renders TTL-filtered threads without `[:15]` cap.

### 4.5 Remove "Past Resolutions" from narrate_user.j2

**Files:**
- `ccya/prompts/narrate_user.j2:59-61` — remove "Past Resolutions" section

**What:** Remove "Past Resolutions" section from narrate_user.j2.

**Why:** It renders unfiltered completed threads, causing context bloat. The TTL-filtered "Recently Resolved Threads" section in `_arc.j2` replaces it.

**Validation:** "Past Resolutions" section removed from narrate_user.j2.

### 4.6 Update `_apply_thread_resolutions` to set `resolved_turn`

**Files:**
- `ccya/engine/turn_state.py:334-338` — set `resolved_turn` when a thread is resolved (already set on the ArcThread copy, but must also be on ThreadResolution)
- Pass `resolved_turn` to sanitizer's `completed_threads` context in `thread_sanitizer.py:146`

**What:** Set `resolved_turn` on ThreadResolution when a thread is resolved.

**Why:** Sanitizer uses `resolved_turn` to evaluate "0–5 turns after resolution" window for world state candidate promotion.

**Validation:** ThreadResolution has `resolved_turn` set when a thread is resolved.

---

## Phase 05: Primitives Pressure Score System

**Goal:** Implement pressure score system in `engine/hints.py`, wire into narrator and storyteller.

### 5.1 Create `engine/hints.py`

**Files:**
- `ccya/engine/hints.py` — new file with pure functions for pressure score computation and hint tier resolution

**What:** Create `engine/hints.py` with:
- `compute_thread_pressure_score(thread: ArcThread, current_turn: int) -> tuple[int, str | None]`
- `compute_arc_pressure_score(arc: LongTermObjective, current_turn: int) -> tuple[int, str | None]`
- Duration weight calculation (same structure for threads and arcs)
- Hint tier resolution (None/Soft/Strong/Imperative)

**Why:** Pure functions, state in, hint context out, no side effects. Shared by both narrator and storyteller paths.

**Validation:** `engine/hints.py` exists with pressure score computation functions. No side effects.

### 5.2 Wire hints into narrator context builder

**Files:**
- `ccya/engine/narrate.py` — call pressure score functions, inject hint tags into narrator context
- `ccya/prompts/sections/_arc.j2` — render hint tags when present

**What:** Call pressure score functions in narrator context builder, inject hint tags into narrator prompt.

**Why:** Narrator acts first (writes toward the signaled conclusion).

**Validation:** Narrator prompt includes hint tags when pressure score crosses threshold.

### 5.3 Wire hints into storyteller context builder

**Files:**
- `ccya/engine/extraction/storytell.py` — call pressure score functions, inject hint tags into storyteller context
- `ccya/prompts/sections/_arc.j2` — render hint tags when present (same template as narrator)

**What:** Call pressure score functions in storyteller context builder, inject hint tags into storyteller prompt.

**Why:** Storyteller receives the narrator's output plus the same hint and is told to respond to what the narrator played out.

**Validation:** Storyteller prompt includes hint tags when pressure score crosses threshold.

### 5.4 Define hint language

**Files:**
- `ccya/engine/hints.py` — define hint language for each tier
- Soft hint: "Consider resolving"
- Strong hint: "This should be reaching conclusion"
- Imperative: "Wrap up — failure is a valid resolution"

**What:** Define hint language for each tier.

**Why:** Consistent language across narrator and storyteller prompts.

**Validation:** Hint language matches design spec.

---

## Phase 06: Arc System

**Goal:** Implement arc lifecycle changes, thread→world state promotion, two-step candidate system.

### 6.1 Update `_apply_arc_resolve` to carry all threads forward

**Files:**
- `ccya/engine/turn_state.py:235-243` — remove `drop_threads` filtering logic; all threads carry forward
- `ccya/engine/turn_state.py:264-270` — remove `new_threads` from successor arc construction; set `started_turn` to current turn; reset `completed_threads` to `[]`

**What:** All threads carry forward to the successor arc automatically on `arc_resolve`. No special thread-creation moment tied to arc resolution.

**Why:** Arc and thread lifecycles are fully decoupled.

**Validation:** `_apply_arc_resolve()` carries all threads forward without filtering. Successor arc has `started_turn` set to current turn and `completed_threads` reset to `[]`.

### 6.2 Implement two-step world state candidate system

**Files:**
- `ccya/engine/turn_state.py:334-338` — collect `world_state_candidate` from ThreadResolution into `world_state_candidates` list
- Pass `world_state_candidates` to sanitizer for evaluation every 5 turns
- Sanitizer has full authority to promote, reject, consolidate, modify, or replace

**What:** Collect `world_state_candidate` from ThreadResolution into `world_state_candidates` list. Pass to sanitizer for evaluation.

**Why:** Two-step system: storyteller flags, sanitizer confirms. Prevents trivial additions while allowing meaningful narrative consequences to persist.

**Validation:** `world_state_candidates` list populated from ThreadResolution. Sanitizer evaluates candidates every 5 turns.

### 6.3 Update storyteller prompt for arc_resolve

**Files:**
- `ccya/prompts/storytell_system.j2:14` — update arc_resolve schema example to use final ArcResolution model (`resolution: str`, `long_term_objective: str`)
- Remove `drop_threads`, `new_threads`, `goal_context` from arc_resolve example

**What:** Update arc_resolve schema example in storyteller prompt.

**Why:** Consistent with final ArcResolution model.

**Validation:** arc_resolve example in storyteller prompt matches final ArcResolution model.

### 6.4 Update storyteller prompt for thread_resolve

**Files:**
- `ccya/prompts/storytell_system.j2:11` — update thread_resolve example to use final ThreadResolution model (`id`, `resolution_state`, `outcome`, `resolved_turn`, `world_state_candidate`)
- Remove `promote_to_world_state` from thread_resolve example

**What:** Update thread_resolve schema example in storyteller prompt.

**Why:** Consistent with final ThreadResolution model.

**Validation:** thread_resolve example in storyteller prompt matches final ThreadResolution model.

### 6.5 Update storyteller prompt for thread_update

**Files:**
- `ccya/prompts/storytell_system.j2` — update thread_update example to use `major_update_signal` instead of `progress_kind`
- Add `reason` field to thread_update example

**What:** Update thread_update schema example in storyteller prompt.

**Why:** Consistent with final ThreadUpdate model.

**Validation:** thread_update example in storyteller prompt matches final ThreadUpdate model.

### 6.6 Remove completed threads from storyteller's prompt

**Files:**
- `ccya/prompts/sections/_arc.j2` — remove completed threads section from storyteller's user prompt (or TTL-filter to 3-turn window)

**What:** Remove completed threads from storyteller's prompt.

**Why:** Storyteller sees completed thread IDs in the prompt and tries to resolve them, even though they're no longer in the active list. This causes silent failures.

**Validation:** Storyteller's user prompt does not include completed threads (or only TTL-filtered ones within 3 turns).

---

## Phase 07: Seed Worldbuilding

**Goal:** Implement funnel ordering, pc.situation, arc_origin, key locations.

### 7.1 Add `arc_origin` to seed state model

**Files:**
- `ccya/models/state.py` — add `arc_origin: str` field to seed state model
- `ccya/prompts/generate_seed_system.j2` — instruct seed LLM to generate `arc_origin` (2–3 sentences, past tense, "how did the PC end up here?")

**What:** Add `arc_origin` to seed state model.

**Why:** "How did the PC end up here?" Past tense, 2–3 sentences. Seed-time field only, never regenerated.

**Validation:** Seed state model has `arc_origin` field. Seed prompt instructs LLM to generate it.

### 7.2 Add `pc.situation` to `_default_state()` and `SeedPC`

**Files:**
- `ccya/state/io.py` — add `pc.situation` to `_default_state()`
- `ccya/models/state.py` — add `pc.situation` to SeedPC model
- `ccya/pack.py` — add `pc_situation_schema` to ScenarioBrief

**What:** Add `pc.situation` to default state and SeedPC model. Add `pc_situation_schema` to ScenarioBrief.

**Why:** Pack-specific situational facts. 3–5 keys maximum, all `required: false`.

**Validation:** `_default_state()` includes `pc.situation`. SeedPC has `pc.situation` field. ScenarioBrief has `pc_situation_schema`.

### 7.3 Rewrite seed prompt with funnel ordering

**Files:**
- `ccya/prompts/generate_seed_system.j2` — rewrite generation order to enforce funnel:
  1. World facts (global tier)
  2. World facts (local tier)
  3. Key locations → `world.locations`
  4. PC situation → `pc.situation`
  5. NPC bonds + compendium
  6. Arc (long_term_objective + arc_origin)
  7. PC bio + inventory

**What:** Rewrite seed prompt to enforce funnel ordering.

**Why:** Each stage receives all outputs from prior stages as context. The prompt is structured to enforce this ordering.

**Validation:** Seed prompt enforces funnel ordering.

### 7.4 Add `KeyLocation` model

**Files:**
- `ccya/models/state.py` — add `KeyLocation` model with `id`, `name`, `description`, `status`, `tags`
- `ccya/state/io.py` — add `world.locations` to `_default_state()`

**What:** Add `KeyLocation` model and `world.locations` to default state.

**Why:** 4–5 named places that exist in the world at game start. Ordered from most accessible to least known.

**Validation:** `KeyLocation` model exists. `world.locations` in `_default_state()`.

### 7.5 Update seed prompt for arc_origin and long_term_objective

**Files:**
- `ccya/prompts/generate_seed_system.j2:63-64` — rename `visible_goal` to `long_term_objective`, `goal_context` to `arc_origin`

**What:** Update seed prompt to use new field names.

**Why:** Consistent with field renames in Phase 02.

**Validation:** Seed prompt references `long_term_objective` and `arc_origin`.

### 7.6 Add `pc.situation` to ruling context

**Files:**
- `ccya/engine/ruling.py` — add `pc_situation` (persistent fields only) to ruling context
- `ccya/prompts/ruling_user.j2` — add `pc.situation` section to ruling prompt

**What:** Add `pc.situation` (persistent fields only) to ruling context.

**Why:** Ruling needs situational facts about what the PC owns and can access. Without it, ruling may incorrectly deny actions that depend on established situational facts.

**Validation:** Ruling prompt includes `pc.situation` section.

### 7.7 Update UI to render `arc_origin`

**Files:**
- `ccya/templates/_state_left.html:64,109` — render `arc_origin` in UI sidebar for initial arc display
- `ccya/templates/_save_picker.html:29` — render `arc_origin` in save picker UI

**What:** Render `arc_origin` in UI sidebar and save picker.

**Why:** `arc_origin` surfaces in the opening narration and the UI sidebar for the initial arc only.

**Validation:** UI renders `arc_origin` in sidebar and save picker.

---

## Phase 08: World State Lifecycle

**Goal:** Implement new WorldStateFact, TTL expiry, sanitizer extension.

### 8.1 Replace `WorldStateFact` model

**Files:**
- `ccya/models/state.py:150-154` — replace `WorldStateFact` with new schema:
  ```python
  class WorldStateFact(BaseModel):
      id: str
      text: str
      tier: Literal["global", "local"]
      permanent: bool = False
      valence: Literal["threat", "complication", "neutral", "boon"] = "neutral"
      expires_turn: int | None = None
  ```

**What:** Replace `WorldStateFact` model with new schema.

**Why:** Old schema (`tier: Literal["permanent", "persistent"]`) is too coarse. New schema adds tier, permanence, valence, and TTL.

**Validation:** `WorldStateFact` has new schema with `tier`, `permanent`, `valence`, `expires_turn`.

### 8.2 Update code that branches on old tier values

**Files:**
- `ccya/engine/turn_state.py:346,348` — `tier: "persistent"` → `tier: "local"` (or `"global"`)
- All code that branches on `"permanent"` or `"persistent"` in world state context — rewrite

**What:** Rewrite all code that branches on old tier values.

**Why:** Old tier values (`"permanent"`, `"persistent"`) are replaced by new schema.

**Validation:** No code branches on `"permanent"` or `"persistent"` in world state context.

### 8.3 Add TTL expiry pass to turn pipeline

**Files:**
- `ccya/engine/turn.py` — add TTL expiry pass at start of each turn (before narrate and storyteller calls)
- Iterate `state["scene"]["world_state"]` and filter out facts where `fact.expires_turn` is not None and `current_turn >= fact.expires_turn`
- Hard-delete filtered facts from state (no archive list)
- Record removals in `events.jsonl` for audit purposes

**What:** Add TTL expiry pass to turn pipeline start.

**Why:** At the start of each turn, before any LLM call, hard-delete facts where `current_turn >= expires_turn`. No LLM involved. No archive.

**Validation:** TTL expiry pass runs at start of each turn. Facts with `expires_turn` are hard-deleted when TTL expires.

### 8.4 Add `SanitizedWorldStateFact` model

**Files:**
- `ccya/models/state.py` or `ccya/engine/thread_sanitizer.py` — add `SanitizedWorldStateFact` model

**What:** Add `SanitizedWorldStateFact` model for sanitizer output.

**Why:** Sanitizer returns a complete replacement array. The model defines the output schema.

**Validation:** `SanitizedWorldStateFact` model exists with same fields as `WorldStateFact`.

### 8.5 Extend sanitizer to maintain world state

**Files:**
- `ccya/engine/thread_sanitizer.py` — add `world_state` to input context and output schema
- `ccya/prompts/sanitize_thread.j2` — add world state to prompt context
- Engine applies atomic swap: `state["scene"]["world_state"] = sanitizer_output.world_state`
- Add `world_state_candidates` to sanitizer input context
- Pass `world_state_candidates` to sanitizer for evaluation

**What:** Extend sanitizer to maintain world state on the same cadence as thread sanitization.

**Why:** The sanitizer is the right system to maintain world state — it already has full arc and thread context, runs on a cadence, and reasons about narrative relevance.

**Validation:** Sanitizer receives `world_state` and `world_state_candidates` as input. Returns complete replacement array. Engine applies atomic swap.

### 8.6 Update sanitizer prompt for world state

**Files:**
- `ccya/prompts/sanitize_thread.j2` — add world state instructions:
  - Evaluate `world_state_candidates` within 0–5 turns of resolution
  - Promote, reject, consolidate, modify, or replace world state
  - Treat `permanent: true` facts with higher removal bar
  - Return complete replacement array (not diff)

**What:** Update sanitizer prompt to include world state instructions.

**Why:** Sanitizer needs clear instructions for world state maintenance.

**Validation:** Sanitizer prompt includes world state instructions.

### 8.7 Update `_world_state.j2` and `storytell_user.j2` to render tier/valence badges

**Files:**
- `ccya/prompts/sections/_world_state.j2:6` — replace `fact.tier == "permanent"` check with `fact.permanent` boolean field (new schema)
- Render tier and valence as paired badges: `[global/threat]`, `[local/boon]`, etc.
- `ccya/prompts/storytell_user.j2` — render tier and valence as paired badges

**What:** Update world state rendering to use new schema and render tier/valence badges.

**Why:** Gives the storyteller the signal it needs to self-correct toward balance without additional instruction.

**Validation:** World state renders `[tier/valence]` badges in both narrator and storyteller prompts.

### 8.8 Add seed-time valence requirement

**Files:**
- `ccya/prompts/generate_seed_system.j2` — add valence requirement to seed prompt instructions: "The seed prompt must produce at least one `neutral` or `boon` fact across the combined global + local world state."

**What:** Add seed-time valence requirement to seed prompt.

**Why:** Left without instruction the LLM defaults to threats and complications.

**Validation:** Seed prompt instructs LLM to produce at least one neutral or boon fact.

---

## Phase 09: Pack Update

**Goal:** Update golden-piracy pack.

### 9.1 Add `pc_situation_schema` to golden-piracy

**Files:**
- `packs/golden-piracy/scenario.yaml` — add `pc_situation_schema` with 3–5 keys (vessel, home_port, crew)

**What:** Add `pc_situation_schema` to golden-piracy pack.

**Why:** Pack-specific situational facts. 3–5 keys maximum, all `required: false`.

**Validation:** golden-piracy pack has `pc_situation_schema` with 3–5 keys.

### 9.2 Remove deleted fields from golden-piracy

**Files:**
- `packs/golden-piracy/scenario.yaml` — remove `goal_context`, `chapter_end`, `inspiration.pc`, `inspiration.npcs`, `inspiration.inventory`, `world_facts`, `forbid_cliches`, `pc_stat_range`, `pc_stat_total_range`

**What:** Remove deleted fields from golden-piracy pack.

**Why:** Clean break. No backward compatibility.

**Validation:** golden-piracy pack has no deleted fields.

### 9.3 Expand `scene_detail_bundles` in golden-piracy

**Files:**
- `packs/golden-piracy/scenario.yaml` — expand `scene_detail_bundles` to cover new world state fields

**What:** Expand `scene_detail_bundles` to cover new world state fields.

**Why:** Scene detail bundles should cover all world state tiers and valences.

**Validation:** `scene_detail_bundles` covers all world state tiers and valences.

### 9.4 Audit archetype pools in golden-piracy

**Files:**
- `packs/golden-piracy/scenario.yaml` — audit archetype pools for consistency with new field names

**What:** Audit archetype pools for consistency with new field names.

**Why:** Archetype pools should reference new field names.

**Validation:** Archetype pools reference new field names.

---

## Phase 10: Documentation Updates

**Goal:** Update docs/architecture/, docs/repomap.md, AGENTS.md.

### 10.1 Update state-models.md

**Files:**
- `docs/architecture/state-models.md` — update state model definitions to reflect all renames, deletions, and additions

**What:** Update state model definitions in docs.

**Why:** AGENTS.md mandates doc updates when models change.

**Validation:** State model docs match current models.

### 10.2 Update cross-module-contracts.md

**Files:**
- `docs/architecture/cross-module-contracts.md` — update thread lifecycle, extraction routing, and state model references

**What:** Update cross-module contracts in docs.

**Why:** Thread lifecycle and extraction routing have changed.

**Validation:** Cross-module contracts docs match current behavior.

### 10.3 Update step2c-storytell.md

**Files:**
- `docs/architecture/step2c-storytell.md` — update storytell prompt Schema section to reflect new field names and structures

**What:** Update storytell prompt docs.

**Why:** Storytell prompt Schema has changed.

**Validation:** Storytell prompt docs match current prompt.

### 10.4 Update step2a-scene.md

**Files:**
- `docs/architecture/step2a-scene.md` — update scene extractor docs to reflect new thread_update fields

**What:** Update scene extractor docs.

**Why:** Scene extractor thread_update fields have changed.

**Validation:** Scene extractor docs match current behavior.

### 10.5 Update repomap.md

**Files:**
- `docs/repomap.md` — update module boundaries, signatures, and public APIs

**What:** Update repomap to reflect new modules and signatures.

**Why:** New `engine/hints.py` module, renamed models, and updated signatures.

**Validation:** Repomap matches current codebase.

### 10.6 Update OVERVIEW.md

**Files:**
- `docs/architecture/OVERVIEW.md` — update pipeline overview to reflect TTL strategy, pressure score system, and two-step world state promotion

**What:** Update pipeline overview in docs.

**Why:** Pipeline has new stages (TTL filtering, pressure score computation, two-step world state promotion).

**Validation:** Pipeline overview matches current behavior.

### 10.7 Update AGENTS.md

**Files:**
- `AGENTS.md` — update build commands, signposts, and conventions if needed

**What:** Update AGENTS.md if build commands, signposts, or conventions have changed.

**Why:** AGENTS.md should reflect current state.

**Validation:** AGENTS.md matches current state.

---

## Verification

After all phases:
1. `make check` — lint + typecheck must pass
2. Render storytell prompt with `ev.py prompt-eval dump` — verify Schema includes new field names
3. Render narrate prompt with `ev.py prompt-eval dump` — verify TTL filtering and hint tags
4. Seed a game with `ev.py play --seed` — verify funnel ordering, pc.situation, arc_origin
5. Run 5 turns — verify TTL filtering, pressure score hints, thread lifecycle
6. Resolve a thread — verify two-step world state candidate system
7. Resolve an arc — verify successor arc carries all threads forward, no drop_threads/new_threads
