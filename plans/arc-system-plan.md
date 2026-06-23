# Plan: Arc System Redesign

**Derived from:** [02-Arc System Redesign](../docs/design/02-arc-system-redesign.md)
**Depends on:** [Primitives Plan](./primitives-plan.md)
**Date:** 2026-06-23

---

## Purpose

Implement arc lifecycle changes, thread→world state promotion, and storyteller prompt updates. This plan assumes primitives (field renames, deletions, TTL strategy, pressure score system) are already in place.

## Problem

Eval data shows threads accumulate without resolution, arc resolution fires too frequently with no-op goal updates, and the system never closes narrative arcs. The storyteller tries to resolve threads that no longer exist in the active thread list.

## Scope

Arc lifecycle, thread→world state promotion, storyteller prompt updates, and TTL-filtering completed threads from prompts.

## Out of Scope

- Field renames and deletions (primitives plan)
- TTL strategy (primitives plan)
- Pressure score system (primitives plan)
- pc.situation (primitives plan)
- Seed funnel ordering (seed worldbuilding plan)
- arc_origin on seed state model (seed worldbuilding plan)
- Key locations (seed worldbuilding plan)
- World state lifecycle (seed worldbuilding plan)
- Sanitizer extension (seed worldbuilding plan)
- Pack update (seed worldbuilding plan)

## Firm Decisions

- **No auto-arc-resolve.** Arc resolution is entirely storyteller-driven. No auto-resolve logic.
- **No auto-thread-completion.** Hard TTL on active threads removed.
- **Thread type stability.** Stable by default. Changes require `reason` field.
- **Thread → world state promotion.** Two-step: storyteller flags `world_state_candidate`, sanitizer confirms every 5 turns with full array replacement authority.
- **Completed threads in storyteller's prompt.** TTL-filtered to 3-turn window via context builder. Storyteller sees completed thread IDs and tries to resolve them, causing silent failures.
- **`arc_origin` on seed model only.** Never on LongTermObjective or ArcResolution. Never regenerated. Never injected into narrate, storytell, or ruling prompts.
- **`major_update_signal` values.** `advancement` / `setback` only. `shift` removed.

## Risks

- **Prompt structural changes.** TTL-filtering completed threads changes what the LLM sees. This may affect LLM behavior in unexpected ways.
- **Two-step world state.** Adding `world_state_candidate` to ThreadResolution and collecting it in `world_state_candidates` list is a new data flow. Collection is handled here; sanitizer evaluation is in the seed worldbuilding plan.

---

## Phase 01 [VALIDATION]: Verify `_apply_arc_resolve` carries all threads forward

**Files:**
- `ccya/engine/turn_state.py:192-275` — read `_apply_arc_resolve()` to confirm primitives cleanup

**What:** [VALIDATION] Confirm primitives correctly removed `drop_threads` filtering and `new_threads` from successor arc construction. All threads carry forward automatically.

**Why:** Primitive plan Phase 01 removes `drop_threads` filtering and `new_threads` from successor arc construction. Phase 04 sets `started_turn`. This phase validates those changes are applied correctly.

**Validation:** `grep -n "drop_threads\|new_threads\|goal_context" ccya/engine/turn_state.py` returns zero matches. `_apply_arc_resolve()` successor arc has `started_turn == turn_no` and `completed_threads == []`.

## Phase 02: Collect `world_state_candidate` from ThreadResolution into `world_state_candidates` list

**Files:**
- `ccya/engine/turn_state.py:334-338` — add `world_state_candidate` collection in `_apply_thread_resolutions()` for-loop body, after the `updates.append()` block at lines 334-338

**What:** In the `for res in storyteller_result.thread_resolve` loop, after the `updates.append()` call, check `res.world_state_candidate`. If present and non-empty, use `state.setdefault("world_state_candidates", []).append(...)` to append `{"thread_id": res.id, "text": res.world_state_candidate, "resolved_turn": turn_no}`.

**Why:** Two-step system: storyteller flags, sanitizer confirms (sanitizer evaluation handled by seed worldbuilding plan). This phase implements the first step — collecting candidates. Use `setdefault` so saves missing the key (pre-primitives) don't crash.

**Validation:** After a turn where storyteller emits `thread_resolve` with `world_state_candidate`, `state["world_state_candidates"]` contains one entry with `thread_id`, `text`, and `resolved_turn`.

## Phase 03 [VALIDATION]: Verify storyteller arc_resolve schema

**Files:**
- `ccya/prompts/storytell_system.j2:14` — read arc_resolve schema example

**What:** [VALIDATION] Confirm primitives updated the arc_resolve schema example to use final ArcResolution model.

**Why:** Primitive plan Phase 01 removes `goal_context`/`drop_threads`/`new_threads` from the arc_resolve example. Phase 02 renames `visible_goal` to `long_term_objective`. This phase validates both are applied.

**Validation:** arc_resolve example reads: `"arc_resolve": {"resolution": "...", "long_term_objective": "..."}`. No `drop_threads`, `new_threads`, `goal_context`, or `visible_goal` in the example.

## Phase 04: Update storyteller prompt — thread_resolve schema

**Files:**
- `ccya/prompts/storytell_system.j2:11` — update thread_resolve schema example to use final ThreadResolution model with `resolved_turn` and `world_state_candidate` (primitives already removed `promote_to_world_state`)

**What:** Replace thread_resolve schema example to match final ThreadResolution model: `id`, `resolution_state`, `outcome`, `resolved_turn`, `world_state_candidate`.

**Why:** Consistent with final ThreadResolution model. `resolved_turn` and `world_state_candidate` are new fields added by primitives Phase 03 that must be reflected in the schema example.

**Validation:** thread_resolve example reads: `"thread_resolve": [{"id": "...", "resolution_state": "resolved|failed|abandoned", "outcome": "...", "resolved_turn": 0, "world_state_candidate": "..."}]`.

## Phase 05: Update storyteller prompt — thread_update schema

**Files:**
- `ccya/prompts/storytell_system.j2` — update thread_update schema example to use `major_update_signal` instead of `progress_kind`
- Add `reason` field to thread_update example

**What:** Update thread_update schema example in storyteller prompt.

**Why:** Consistent with final ThreadUpdate model.

**Validation:** thread_update example reads: `"thread_update": [{"id": "...", "type": "threat", "progress": "...", "major_update_signal": "advancement|setback", "urgency": "background|normal|urgent", "dormant": true, "reason": "..."}]`.

## Phase 06 [VALIDATION]: Verify TTL filtering of completed threads

**Files:**
- `ccya/prompts/context.py` — verify context builder TTL-filters completed_threads (primitives Phase 07)
- `ccya/prompts/sections/_arc.j2:18-24` — verify template renders filtered list without `[:15]` cap

**What:** [VALIDATION] Confirm primitives implemented TTL filtering for completed threads (3-turn window) in the context builder. Completed threads outside the TTL window do not appear in storyteller or narrator prompts.

**Why:** Primitive plan Phase 07 adds TTL filtering in the context builder, not the template. This phase validates the filtering is working correctly.

**Validation:** Context builder's `completed_threads` list only includes threads resolved within the last 3 turns. `_arc.j2` renders no `[:15]` cap.

## Phase 07 [VALIDATION]: Verify arc_resolve guidance in storyteller prompt

**Files:**
- `ccya/prompts/storytell_system.j2:66` — read arc resolution guidance section
- `ccya/prompts/storytell_system.j2:68` — read stale `drop_threads` prohibition
- `ccya/prompts/storytell_system.j2:72` — read contrasting example

**What:** [VALIDATION] Confirm arc resolution guidance uses "Emit **only** when:" language, the contrasting example uses `long_term_objective` (not `visible_goal`), and the stale `drop_threads` prohibition at line 68 is removed or updated.

**Why:** "Emit **only** when:" language already exists at line 66. Primitives renames `visible_goal` → `long_term_objective` in the example and removes `chapter_end` reference. Line 68's "Using `arc_resolve` with `drop_threads`" warning references a field that no longer exists — must be removed or reworded to avoid confusing the LLM.

**Validation:** Line 66: "Emit **only** when the narrative chapter genuinely ends..." Line 72: "WRONG: `arc_resolve` with unchanged `long_term_objective` (no-op). RIGHT: `arc_resolve` introduces a new goal." Line 68: no reference to `drop_threads` or `visible_goal` in the prohibition text.

## Phase 08 [VALIDATION]: Verify thread type in schema examples

**Files:**
- `ccya/prompts/storytell_system.j2:12` — read thread_update example
- `ccya/prompts/storytell_system.j2:13` — read thread_add example
- `ccya/prompts/storytell_system.j2:39` — read REQUIRED directive

**What:** [VALIDATION] Confirm `type` is present in both `thread_update` and `thread_add` schema examples. Confirm REQUIRED directive exists.

**Why:** `type` is already present in both schema examples (lines 12-13) and the REQUIRED directive exists (line 39). No implementation needed.

**Validation:** `thread_update` example includes `"type": "threat"`. `thread_add` example includes `"type": "threat"`. Line 39: "REQUIRED — every `thread_add` and `thread_update` must include exactly one type."

## Phase 09: Documentation updates

**Files:**
- `docs/design/02-arc-system-redesign.md` — update YAML frontmatter status from `scoping` to `implemented`; add `arc-system-plan.md` to Related designs
- `docs/architecture/OVERVIEW.md` — add `world_state_candidates` to state data shapes; document collection flow in turn pipeline
- `docs/architecture/step2c-storytell.md` — update extraction fields to include `world_state_candidate` on ThreadResolution
- `docs/repomap.md` — note `state["world_state_candidates"]` key in state module section; update `_apply_thread_resolutions` signature note
- `AGENTS.md` — add signpost for arc plan completion if applicable

**What:** Update design doc status, architecture docs, repomap, and AGENTS.md to reflect the new `world_state_candidates` collection flow and the re-scoped phases.

**Why:** Mandatory per AGENTS.md — any code change touching a module, config key, model field, prompt, or public API requires corresponding documentation updates.

**Validation:** `grep -q "world_state_candidates" docs/architecture/OVERVIEW.md docs/architecture/step2c-storytell.md docs/repomap.md` and design doc status is `implemented`.

---

## Verification

### Required (must pass):
1. `make check` — lint + typecheck must pass
2. Render storytell prompt with `ev.py prompt-eval dump` — verify Schema has new field names
3. Verify `world_state_candidates` list is populated from ThreadResolution

### Validation phases (confirm primitives applied correctly):
4. Verify `_apply_arc_resolve()` carries all threads forward without filtering
5. Verify storyteller prompt's completed threads section shows only TTL-filtered entries within 3-turn window
6. Verify arc resolution guidance uses "Emit **only** when:" language and contrasting example uses `long_term_objective`
7. Verify Schema examples include `type` on `thread_add` and `thread_update`

### Documentation:
8. Verify `world_state_candidates` is documented in `docs/architecture/OVERVIEW.md`, `docs/architecture/step2c-storytell.md`, and `docs/repomap.md`
