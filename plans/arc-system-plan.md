# Plan: Arc System Redesign

**Derived from:** [02-Arc System Redesign](../design/02-arc-system-redesign.md)
**Depends on:** [Primitives Plan](./primitives-plan.md)
**Date:** 2026-06-23

---

## Purpose

Implement arc lifecycle changes, thread→world state promotion, and storyteller prompt updates. This plan assumes primitives (field renames, deletions, TTL strategy, pressure score system) are already in place.

## Problem

Eval data shows threads accumulate without resolution, arc resolution fires too frequently with no-op goal updates, and the system never closes narrative arcs. The storyteller tries to resolve threads that no longer exist in the active thread list.

## Scope

Arc lifecycle, thread→world state promotion, storyteller prompt updates, and removing completed threads from storyteller's prompt.

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
- Documentation updates (seed worldbuilding plan)

## Firm Decisions

- **No auto-arc-resolve.** Arc resolution is entirely storyteller-driven. No auto-resolve logic.
- **No auto-thread-completion.** Hard TTL on active threads removed.
- **Thread type stability.** Stable by default. Changes require `reason` field.
- **Thread → world state promotion.** Two-step: storyteller flags `world_state_candidate`, sanitizer confirms every 5 turns with full array replacement authority.
- **Completed threads in storyteller's prompt.** Remove or TTL-filter to 3-turn window. Storyteller sees completed thread IDs and tries to resolve them, causing silent failures.
- **`arc_origin` on seed model only.** Never on LongTermObjective or ArcResolution. Never regenerated. Never injected into narrate, storytell, or ruling prompts.
- **`major_update_signal` values.** `advancement` / `setback` only. `shift` removed.

## Risks

- **Prompt structural changes.** Removing completed threads from storyteller's prompt changes what the LLM sees. This may affect LLM behavior in unexpected ways.
- **Two-step world state.** Adding `world_state_candidate` to ThreadResolution and collecting it in `world_state_candidates` list is a new data flow that the sanitizer must consume.

---

## Phase 01: Update `_apply_arc_resolve` to carry all threads forward

**Files:**
- `ccya/engine/turn_state.py:235-243` — remove `drop_threads` filtering logic; all threads carry forward
- `ccya/engine/turn_state.py:264-270` — remove `new_threads` from successor arc construction; set `started_turn` to current turn; reset `completed_threads` to `[]`

**What:** All threads carry forward to the successor arc automatically on `arc_resolve`. No special thread-creation moment tied to arc resolution.

**Why:** Arc and thread lifecycles are fully decoupled. The storyteller emits `thread_add` independently — there is no special thread-creation moment tied to arc resolution.

**Validation:** `_apply_arc_resolve()` carries all threads forward without filtering. Successor arc has `started_turn` set to current turn and `completed_threads` reset to `[]`.

## Phase 02: Implement two-step world state candidate system

**Files:**
- `ccya/engine/turn_state.py:334-338` — collect `world_state_candidate` from ThreadResolution into `world_state_candidates` list
- Pass `world_state_candidates` to sanitizer for evaluation every 5 turns
- Sanitizer has full authority to promote, reject, consolidate, modify, or replace

**What:** Collect `world_state_candidate` from ThreadResolution into `world_state_candidates` list. Pass to sanitizer for evaluation.

**Why:** Two-step system: storyteller flags, sanitizer confirms. Prevents trivial additions while allowing meaningful narrative consequences to persist.

**Validation:** `world_state_candidates` list populated from ThreadResolution. Sanitizer evaluates candidates every 5 turns.

## Phase 03: Update storyteller prompt — arc_resolve schema

**Files:**
- `ccya/prompts/storytell_system.j2:14` — update arc_resolve schema example to use final ArcResolution model (`resolution: str`, `long_term_objective: str`)
- Remove `drop_threads`, `new_threads`, `goal_context` from arc_resolve example

**What:** Update arc_resolve schema example in storyteller prompt.

**Why:** Consistent with final ArcResolution model.

**Validation:** arc_resolve example in storyteller prompt matches final ArcResolution model.

## Phase 04: Update storyteller prompt — thread_resolve schema

**Files:**
- `ccya/prompts/storytell_system.j2:11` — update thread_resolve schema example to use final ThreadResolution model (`id`, `resolution_state`, `outcome`, `resolved_turn`, `world_state_candidate`)
- Remove `promote_to_world_state` from thread_resolve example

**What:** Update thread_resolve schema example in storyteller prompt.

**Why:** Consistent with final ThreadResolution model.

**Validation:** thread_resolve example in storyteller prompt matches final ThreadResolution model.

## Phase 05: Update storyteller prompt — thread_update schema

**Files:**
- `ccya/prompts/storytell_system.j2` — update thread_update schema example to use `major_update_signal` instead of `progress_kind`
- Add `reason` field to thread_update example

**What:** Update thread_update schema example in storyteller prompt.

**Why:** Consistent with final ThreadUpdate model.

**Validation:** thread_update example in storyteller prompt matches final ThreadUpdate model.

## Phase 06: Remove completed threads from storyteller's prompt

**Files:**
- `ccya/prompts/sections/_arc.j2` — remove completed threads section from storyteller's user prompt (or TTL-filter to 3-turn window)

**What:** Remove completed threads from storyteller's prompt.

**Why:** Storyteller sees completed thread IDs in the prompt and tries to resolve them, even though they're no longer in the active list. This causes silent failures.

**Validation:** Storyteller's user prompt does not include completed threads (or only TTL-filtered ones within 3 turns).

## Phase 07: Update arc_resolve guidance in storyteller prompt

**Files:**
- `ccya/prompts/storytell_system.j2` — tighten arc resolution guidance: "Emit **only** when the narrative chapter genuinely ends — a decisive win, a fundamental shift, or 8+ turns on the same goal. Target cadence: 8–15 turns."
- Add contrasting example: "WRONG: `arc_resolve` with unchanged `long_term_objective` (no-op). RIGHT: `arc_resolve` introduces a new goal."

**What:** Tighten arc resolution guidance in storyteller prompt.

**Why:** Current language ("Emit when:") reads permissive. "Emit **only** when:" reads restrictive. The LLM fires `arc_resolve` with the same goal (no-op).

**Validation:** Arc resolution guidance in storyteller prompt uses "Emit **only** when:" language.

## Phase 08: Update thread type guidance in storyteller prompt

**Files:**
- `ccya/prompts/storytell_system.j2` — add guidance: "REQUIRED — every `thread_add` and `thread_update` must include exactly one type from the list above."
- Add `type` to Schema examples in `thread_update` and `thread_add`

**What:** Add required-type directive and type to Schema examples.

**Why:** Schema examples are the LLM's primary reference for required fields. Current examples omit `type`, so the LLM treats it as optional.

**Validation:** Schema examples show `type` on both `thread_add` and `thread_update`. Required-type directive exists in prompt.

---

## Verification

After all phases:
1. `make check` — lint + typecheck must pass
2. Render storytell prompt with `ev.py prompt-eval dump` — verify Schema has new field names
3. Verify `_apply_arc_resolve()` carries all threads forward without filtering
4. Verify `world_state_candidates` list is populated from ThreadResolution
5. Verify storyteller's user prompt does not include completed threads (or only TTL-filtered ones)
6. Verify arc resolution guidance uses "Emit **only** when:" language
7. Verify Schema examples include `type` on `thread_add` and `thread_update`
