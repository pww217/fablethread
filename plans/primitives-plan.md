# Plan: Primitives — Shared Building Blocks

**Derived from:** [01-Primitives](../design/01-primitives.md)
**Date:** 2026-06-23

---

## Purpose

Implement all shared building blocks that both the arc system redesign and the seed worldbuilding redesign depend on: field renames, deletions, TTL strategy, pressure score system, age tracking, and pc.situation primitive.

## Problem

The current field names (`visible_goal`, `progress`, `progress_kind`, `goal_context`) don't signal their purpose to the LLM. TTL strategy is missing. Pressure score system doesn't exist. pc.situation isn't in the codebase.

## Scope

All shared primitives from Phase 01-05 and pc.situation primitive from the master plan. This is the foundation that both other plans depend on.

## Out of Scope

- Arc lifecycle changes (arc system plan)
- Thread→world state promotion (arc system plan)
- Storyteller prompt schema updates (arc system plan)
- Seed funnel ordering (seed worldbuilding plan)
- arc_origin on seed state model (seed worldbuilding plan)
- Key locations (seed worldbuilding plan)
- World state lifecycle (seed worldbuilding plan)
- Sanitizer extension (seed worldbuilding plan)
- Pack update (seed worldbuilding plan)
- Documentation updates (seed worldbuilding plan)

## Firm Decisions

- **`arc_origin` on seed model only.** Never on LongTermObjective or ArcResolution. Never regenerated. Never injected into narrate, storytell, or ruling prompts.
- **`started_turn` only.** No `created_turn`. Set at arc construction time.
- **TTL strategy.** Completed/abandoned threads kept in data forever, TTL-filtered in prompts (3 turns). Dormant at 8 turns, archival at 13. No resurfacing hints.
- **Pressure score system.** Pure functions in `engine/hints.py`. Hint tiers: None/Soft/Strong/Imperative. No hard floors.
- **`goal_update` dict.** Just `long_term_objective` key. No `arc_origin`.
- **`major_update_signal` values.** `advancement` / `setback` only. `shift` removed.
- **`pc.situation` persist flag.** TBD at implementation time. Pack authors mark keys using a `persist: true` flag (or equivalent) on each `pc_situation_schema` entry.
- **Ruling context.** Extended to include `pc.situation` (persistent fields only). No arc fields added to ruling.
- **NPC roster limit.** 10 → 12.

## Risks

- **Cascade deletions.** `goal_context` exists in 28+ locations. All callsites must be deleted simultaneously. Partial deletion breaks the engine.
- **Model renames.** `CampaignArc` → `LongTermObjective` and `state["arc"]` → `state["long_term_objective"]` touch imports, engine code, prompts, templates, and UI.
- **Prompt structural changes.** TTL filtering in context builder and pressure score hint injection change prompt structure in ways that may affect LLM behavior.

---

## Phase 01: Delete all removed fields

**Files:**
- `ccya/models/state.py` — remove `goal_context` from CampaignArc, `goal_context`/`drop_threads`/`new_threads` from ArcResolution, `chapter_end` from CampaignArc (if present), `promote_to_world_state` from ThreadResolution
- `ccya/engine/turn_state.py` — remove `goal_context` from resolved_arcs entry, remove `goal_context` from successor arc construction, remove `drop_threads` filtering, remove `new_threads` from successor arc construction, delete `turns_since` warning guard, remove `promote_to_world_state` handling
- `ccya/engine/thread_sanitizer.py` — remove `goal_context` from template context, remove `goal_context` validation in `_apply_goal_update`, remove `goal_context` application to `arc.goal_context`
- `ccya/state/io.py` — remove `goal_context` from `_default_state()`
- `ccya/prompts/storytell_system.j2` — remove `goal_context` from arc_resolve example, remove `chapter_end` references, remove `promote_to_world_state` from thread_resolve example, update arc_resolve/thread_update examples to remove `drop_threads`/`new_threads`
- `ccya/prompts/sanitize_thread.j2` — remove `goal_context` from sanitizer prompt
- `ccya/prompts/narrate_user.j2` — remove "Past Resolutions" section
- `ccya/ev/checkers/arc_resolution_validity.py` — remove `goal_context` validation
- `ccya/ev/audit.py` — remove `goal_context` references
- All default pack YAML files — remove `goal_context`, `chapter_end`, `inspiration.pc`, `inspiration.npcs`, `inspiration.inventory`, `world_facts`, `forbid_cliches`, `pc_stat_range`, `pc_stat_total_range`

**What:** Delete all removed fields from models, engine, prompts, templates, ev tools, and packs.

**Why:** Clean break. No backward compatibility.

**Validation:** `grep -r "goal_context\|chapter_end\|drop_threads\|new_threads\|turns_since" ccya/` returns zero matches (except in design docs and comments).

## Phase 02: Rename fields throughout

**Files:**
- `ccya/models/state.py:79-85` — rename class `CampaignArc` to `LongTermObjective`
- `ccya/models/state.py:80` — rename `visible_goal` to `long_term_objective` in LongTermObjective
- `ccya/models/state.py:43` — rename `progress: list[ProgressEntry]` to `major_updates: list[MajorUpdateEntry]` in ArcThread
- `ccya/models/state.py:170` — rename `progress_kind` to `major_update_signal` in ThreadUpdate
- `ccya/models/state.py:22` — change `Literal["advancement", "setback", "shift"]` to `Literal["advancement", "setback"]` in ProgressEntry
- `ccya/models/extraction.py:231` — change `goal_update: str | None` to `goal_update: dict | None` in StorytellerResult
- All imports throughout codebase — update `from ccya.models import CampaignArc` → `from ccya.models import LongTermObjective`
- `ccya/state/io.py` — rename `state["arc"]` key to `state["long_term_objective"]` in `_default_state()`
- `ccya/engine/turn_state.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`, `progress`, `progress_kind`
- `ccya/engine/thread_sanitizer.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`, `progress`, `progress_kind`
- `ccya/engine/narrate.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`
- `ccya/engine/ruling.py` — update all references to `CampaignArc`, `state["arc"]`
- `ccya/state/delta_builder.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`
- `ccya/engine/changes.py` — update all references to `visible_goal`
- `ccya/engine/extraction/pipeline.py` — update all references to `visible_goal`
- `ccya/ev/state_tools.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`
- `ccya/ev/prompt_context.py` — update all references to `visible_goal`
- `ccya/ev/play.py` — update all references to `visible_goal`
- `ccya/ev/audit.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`
- `ccya/server/tv.py` — update all references to `CampaignArc`, `state["arc"]`, `visible_goal`
- `ccya/prompts/sections/_arc.j2` — rename `current_arc` to `current_objective`, rename `visible_goal` to `long_term_objective`
- `ccya/prompts/storytell_system.j2` — rename `visible_goal` to `long_term_objective`
- `ccya/prompts/generate_seed_system.j2` — rename `visible_goal` to `long_term_objective`, `goal_context` to `arc_origin`
- `ccya/templates/_state_left.html` — rename `goal_context` to `arc_origin`
- `ccya/templates/_save_picker.html` — rename `goal_context` to `arc_origin`
- `ccya/ev/checkers/goal_update_validity.py` — update to `long_term_objective`
- `ccya/ev/checkers/arc_goals.py` — update to `long_term_objective`

**What:** Rename all fields throughout the codebase.

**Why:** Consistent with LLM-naming principle. Field names are prompts.

**Validation:** `grep -r "CampaignArc\|visible_goal\|state\[.arc.\]\|\.progress[^_]" ccya/` returns zero matches (except in design docs, comments, and `progress_kind`/`progress_entry` which are handled separately).

## Phase 03: Add new fields to models

**Files:**
- `ccya/models/state.py:79-85` — add `started_turn: int | None = None` to LongTermObjective (no `created_turn`)
- `ccya/models/state.py:170` — add `reason: str | None` to ThreadUpdate
- `ccya/models/state.py:156-161` — add `resolved_turn: int | None` and `world_state_candidate: str | None` to ThreadResolution (remove `promote_to_world_state` in Phase 01)
- `ccya/models/state.py:183-188` — final ArcResolution model: `resolution: str`, `long_term_objective: str`
- `ccya/state/io.py:93` — add initialization in `_default_state()`
- `ccya/state/io.py` — add `world_state_candidates: []` to `_default_state()`

**What:** Add new fields to models.

**Why:** `started_turn` for arc age tracking. `reason` for thread type changes. `resolved_turn` and `world_state_candidate` for two-step world state promotion.

**Validation:** LongTermObjective has `started_turn`. ThreadUpdate has `reason`. ThreadResolution has `resolved_turn` and `world_state_candidate`. ArcResolution has exactly two fields: `resolution` and `long_term_objective`.

## Phase 04: Set `started_turn` at construction time

**Files:**
- `ccya/engine/seed.py` — set `started_turn` when arc is created in seed pipeline
- `ccya/engine/turn_state.py:264-270` — set `started_turn` in `_apply_arc_resolve()` when successor arc is constructed
- `ccya/engine/turn_state.py:334-338` — set `resolved_turn` when a thread is resolved (already set on the ArcThread copy, but must also be on ThreadResolution)
- Pass `resolved_turn` to sanitizer's `completed_threads` context in `thread_sanitizer.py:146`

**What:** Set `started_turn` at arc construction time. Set `resolved_turn` at thread resolution time.

**Why:** `started_turn` is the single source of truth for arc age. Used in pressure score duration weight calculation.

**Validation:** Seed pipeline sets `started_turn`. `_apply_arc_resolve()` sets `started_turn` for successor arcs. `_apply_thread_resolutions()` sets `resolved_turn`.

## Phase 05: Update `goal_update` format

**Files:**
- `ccya/models/extraction.py:231` — change `goal_update: str | None` to `goal_update: dict | None` in StorytellerResult
- `ccya/engine/thread_sanitizer.py:219-222` — update `_apply_goal_update` to use `long_term_objective` key only
- `ccya/engine/thread_sanitizer.py:340-345` — remove `goal_context` application (deleted in Phase 01)
- `ccya/engine/turn_state.py:534-536` — update to apply dict to `long_term_objective` field only

**What:** Change `goal_update` from `str | None` to `dict | None` with `long_term_objective` key.

**Why:** Structural decoupling. The storyteller should not be generating `arc_origin` mid-game.

**Validation:** `StorytellerResult.goal_update` is `dict | None` with `long_term_objective` key.

## Phase 06: Update dormant threshold

**Files:**
- `ccya/engine/turn_state.py:116` — change `dormant_threshold = 4` to `dormant_threshold = 8`
- `ccya/engine/turn_state.py:229` — change `if turns_since < 5` to `if turns_since < 8` (or remove entirely in Phase 01)
- `ccya/prompts/sanitize_thread.j2:51` — "If a thread has no activity in 4+ turns" → "If a thread has no activity in 8+ turns"
- `ccya/prompts/sanitize_thread.j2:48` — align abandonment criteria with TTL strategy (8 dormant + 5 archival = 13 turns total)

**What:** Update dormant threshold from 4 to 8 turns. Update sanitizer prompt.

**Why:** 8 turns gives threads more breathing room before auto-dormant.

**Validation:** Dormant threshold is 8 turns in turn_state.py. Sanitizer prompt references "8+ turns" for dormant guidance.

## Phase 07: Implement TTL filtering in context builder

**Files:**
- `ccya/prompts/context.py` — add TTL filtering for completed_threads (3-turn TTL), following the same pattern as `_get_resolved_arcs()` in narrate.py:139
- Pass pre-filtered `completed_threads` to templates
- `ccya/prompts/sections/_arc.j2:21` — replace `current_arc.completed_threads[:15]` with TTL-filtered `completed_threads` from context builder
- `ccya/prompts/sections/_arc.j2:18-24` — remove `[:15]` hard cap, render all TTL-filtered threads
- `ccya/prompts/sections/_arc.j2:12-16` — rename "Previously Resolved Arcs" to "Recently Resolved Arcs"

**What:** Add TTL filtering in the context builder, not the template. Pass pre-filtered `completed_threads` to the template.

**Why:** TTL filtering in the context builder ensures bounded prompt load. Following the same pattern as `_get_resolved_arcs()` ensures consistency.

**Validation:** Context builder filters completed_threads to only those resolved within 3 turns. `_arc.j2` renders TTL-filtered threads without `[:15]` cap.

## Phase 08: Create `engine/hints.py` — Pressure Score System

**Files:**
- `ccya/engine/hints.py` — new file with pure functions:
  - `compute_thread_pressure_score(thread: ArcThread, current_turn: int) -> tuple[int, str | None]`
  - `compute_arc_pressure_score(arc: LongTermObjective, current_turn: int) -> tuple[int, str | None]`
  - Duration weight calculation (same structure for threads and arcs)
  - Hint tier resolution (None/Soft/Strong/Imperative)
  - Hint language: Soft "Consider resolving", Strong "This should be reaching conclusion", Imperative "Wrap up — failure is a valid resolution"

**What:** Create `engine/hints.py` with pressure score computation functions.

**Why:** Pure functions, state in, hint context out, no side effects. Shared by both narrator and storyteller paths.

**Validation:** `engine/hints.py` exists with pressure score computation functions. No side effects.

## Phase 09: Wire hints into narrator and storyteller

**Files:**
- `ccya/engine/narrate.py` — call pressure score functions, inject hint tags into narrator context
- `ccya/engine/extraction/storytell.py` — call pressure score functions, inject hint tags into storyteller context
- `ccya/prompts/sections/_arc.j2` — render hint tags when present (same template as narrator)

**What:** Call pressure score functions in narrator and storyteller context builders, inject hint tags into prompts.

**Why:** Narrator acts first (writes toward the signaled conclusion). Storyteller receives the narrator's output plus the same hint and is told to respond to what the narrator played out.

**Validation:** Narrator and storyteller prompts include hint tags when pressure score crosses threshold.

## Phase 10: Add pc.situation to ruling context

**Files:**
- `ccya/engine/ruling.py` — add `pc_situation` (persistent fields only) to ruling context
- `ccya/prompts/ruling_user.j2` — add `pc.situation` section to ruling prompt

**What:** Add `pc.situation` (persistent fields only) to ruling context.

**Why:** Ruling needs situational facts about what the PC owns and can access. Without it, ruling may incorrectly deny actions that depend on established situational facts.

**Validation:** Ruling prompt includes `pc.situation` section.

## Phase 11: Bump NPC roster limit

**Files:**
- `ccya/prompts/context.py:25-53` (`_build_npc_roster()`) — bump NPC roster limit from 10 to 12

**What:** Bump NPC roster limit from 10 to 12.

**Why:** More NPCs in context improves narrative variety. If context issues arise, revisit at 15.

**Validation:** NPC roster limit is 12 in `_build_npc_roster()`.

---

## Verification

After all phases:
1. `make check` — lint + typecheck must pass
2. `grep -r "CampaignArc" ccya/` returns zero matches (except in design docs)
3. `grep -r "visible_goal" ccya/` returns zero matches (except in design docs)
4. `grep -r 'state\["arc"\]' ccya/` returns zero matches (except in design docs)
5. `grep -r "goal_context" ccya/` returns zero matches (except in design docs)
6. `grep -r "progress_kind" ccya/` returns zero matches (except in design docs)
7. Render storytell prompt with `ev.py prompt-eval dump` — verify Schema has new field names
8. Render narrate prompt with `ev.py prompt-eval dump` — verify TTL filtering and hint tags
9. Check LongTermObjective has `started_turn` field
10. Check ThreadUpdate has `reason` field
11. Check ThreadResolution has `resolved_turn` and `world_state_candidate` fields
12. Check ArcResolution has exactly two fields: `resolution` and `long_term_objective`
13. Check `engine/hints.py` exists with pressure score functions
14. Check ruling prompt includes `pc.situation` section
15. Check NPC roster limit is 12
