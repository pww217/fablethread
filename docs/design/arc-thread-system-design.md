# Arc / Thread System Design

## Purpose

Design authority for plans that overhaul the campaign arc and thread lifecycle. Covers: visible_goal progression, thematic_question engagement, arc_resolve emission, thread scope classification, thread progress accumulation, urgency decay, and the thread_add gate feedback loop.

## Problem Statement

The arc and thread systems exist but produce zero useful output across both games analyzed (51 combined turns). The arc's visible_goal and thematic_question are set at seed time and never updated regardless of narrative direction. Thread scope is consistently misclassified (scene events classified as arc-scoped, polluting the thread list permanently). Thread progress is a single-string overwrite that loses the investigative trail. Thread urgency never decays. Arc-scoped threads never resolve while scene-scoped threads resolve cleanly, creating a growing dead-weight tail of permanent active threads. The thread_add gate silently drops threads with no feedback to the storyteller. The entire arc/thread apparatus is a net-negative on token budget — it consumes prompt context and compute time while producing stale, misleading state.

## Constraints

- Pipeline order is fixed: narrator runs first, then extraction, then arc director. The 1-turn lag between extraction and arc director is acceptable — it predates this design and reordering is too expensive.
- The basic thread lifecycle (create → update → resolve → completed_threads) is sound and unchanged.
- `_merge_arc_update` conditional replace behavior (only overwrite visible_goal/thematic_question when non-empty) is correct and unchanged.
- Backwards compatibility is not required. Any state format change is acceptable.
- The prompt templates are the primary interface to the storyteller. Code changes enforce constraints; prompt changes guide behavior.

## Non-goals

- Conditions/status effect system — dead code, to be removed via a separate change.
- NPC continuity / last_seen enhancements — separate concern.
- World state usage improvements — separate concern.
- Inventory system changes — not involved in arc/thread problems.
- `_merge_arc_update` fragility (applies thread list replacement unconditionally) — acceptable as-is; the arc director correctly re-derives after apply_delta runs.

## Current State — What Exists

### Arc lifecycle

- **Seed time:** `CampaignArc` is created with `visible_goal`, `thematic_question`, `goal_context`, empty `threads[]` and `completed_threads[]`.
- **Per turn:** The arc director runs at `turn.py:1119-1174` after `apply_delta`. It processes:
  1. `_apply_thread_updates` (line 1121) — merges storyteller's `thread_update[]` into active threads. Progress is a single-string overwrite (`model_copy(update={"progress": new_value})` at line 194).
  2. `_apply_arc_resolve` (line 1132) — checks for `storyteller_result.arc_resolve`. If present, archives current arc to `resolved_arcs[]`, creates a successor arc, carries forward surviving threads.
  3. `_apply_thread_resolutions` (line 1143) — moves resolved/failed/abandoned threads from `threads[]` to `completed_threads[]`.
  4. Thread_add gate (line 1153) — checks `PacingContext.gate == "allow"`. If blocked, silenty discards the new thread with a debug log message.
- `visible_goal` and `thematic_question` are only updated by `_merge_arc_update` when `arc_resolve` fires (the ArcResolution model carries new `visible_goal`, `goal_context`, `thematic_question`). Without `arc_resolve`, they are immutable.

### Thread lifecycle

- **Add:** Storyteller emits `thread_add` with id, summary, scope, urgency. Pacing gate may silently drop it.
- **Update:** Storyteller emits `thread_update[]` with id + optional fields. `_apply_thread_updates` finds the thread by id, calls `model_copy(update=...)` which **replaces** progress, summary, urgency entirely.
- **Resolve:** Storyteller emits `thread_resolve[]` with id + resolution_state + outcome. Thread moves to `completed_threads[]`. Resolution states (as typed in `ThreadResolution` model): `"resolved"`, `"failed"`, `"abandoned"`. The prompt guidance only lists these three; `"superseded"` is not a recognized output value.
- **Purge:** On location change, `delta_builder.py` removes threads with `scope="scene"` from state before the arc director re-derives.

### Models

`ArcThread`: id, summary, scope (scene|arc), active (bool), urgency (background|normal|urgent), progress (str — single string), resolution_state, outcome, resolved_turn.

`CampaignArc`: visible_goal (str), thematic_question (str), goal_context (str), threads (list[ArcThread]), completed_threads (list[ArcThread]), resolution, last_thread_created_turn.

`ThreadUpdate`: id, active (optional), urgency (optional), summary (optional), progress (optional).

`ArcResolution`: resolution, visible_goal, goal_context, thematic_question (optional), drop_threads, new_threads.

### Pacing gate interaction

The `PacingContext.gate` is `"block_escalate"` when `deescalate >= 0.5` (high de-escalation from ruling phase). When blocked, `thread_add` at line 1158 logs a debug message and skips the add. No feedback reaches the storyteller.

## Problems with Current State

1. **Arc never progresses.** `arc_resolve` was never emitted across 51 turns in two games. Without it, `visible_goal` and `thematic_question` are frozen at seed-time values. In the zombie save, the visible goal ("Secure the medical archives") was obsolete for 30 turns but never updated.

2. **Thematic question is a dead field.** Set at seed time, rendered every turn via `_arc.j2` but never given behavioral weight. The storyteller has no mechanism or incentive to engage it meaningfully. The zombie save's question ("Do you save the knowledge of the old world or the people of the new one?") was ignored as the narrative evolved into black market politics.

3. **Thread scope misclassification is persistent and damaging.** Both games classified single-location events as "arc" scope (8 of 8 cross-game misclassifications in CONSOLIDATED-EV-FINDINGS.md). Arc-scoped threads survive location-change purge and accumulate permanently. In the zombie save's final state, 6 of 8 active threads should be scene-scoped but are classified as arc.

4. **Thread progress is lost on every update.** `_apply_thread_updates` replaces `thread.progress` entirely. The storyteller cannot see past progress values — only the latest string. In the noir save, T4's finding ("no blade among debris") was overwritten by T5's update ("transcribed details"). In the zombie save, `black_market_contact` received 8 updates with near-identical summaries because the storyteller couldn't see what was already recorded.

5. **Thread urgency never decays.** The storyteller only increases urgency or leaves it static. No thread in either game ever transitioned urgent → normal → background. `quarantine_spread` was urgent for 34 turns with no updates. `david_betrayal` has been urgent since T5 with David absent since T6.

6. **Thread_add gate has no feedback loop.** When the pacing gate blocks a thread_add, the thread is silently dropped. The storyteller has no way to know the add failed. At zombie T12, `santana_collusion_risk` was emitted by the storyteller but silently discarded because the gate was `"block_escalate"` from a Breathe directive.

7. **No-op thread_updates waste context.** Storyteller emits `thread_update` calls where all fields are None or empty — no meaningful change. The LLM receives no guidance to avoid this.

8. **Arc-scoped threads cannot resolve.** Scene-scoped threads resolve within 1-3 turns (confirmed in zombie T23-T34). Arc-scoped threads persist indefinitely with no resolution path. The thread list stabilizes at ~8 active threads because every add is balanced by a resolve — but only scene-scoped threads resolve.

## Proposed Solution

### Core Changes

#### 1. Make visible_goal updateable without arc_resolve

- Add a `visible_goal` field to `StorytellerResult` (or reuse existing signals) that the storyteller can update independently of arc resolution.
- `_merge_arc_update` already handles this correctly (conditional replace when non-empty). The missing piece is a prompt-level mechanism for the storyteller to emit goal updates.
- **Rationale:** The storyteller demonstrably drives narrative direction but has no way to formally acknowledge that the goal has shifted. A dedicated goal_update field decouples goal progression from the arc resolution lifecycle.

#### 2. Add prompt guidance for visible_goal updates

- In `storytell_system.j2`, add guidance: "When the player makes significant progress toward or permanently changes the current visible_goal, update it to reflect the new state of the arc."
- Include concrete examples: "If the goal was 'Find the stolen ledger' and the player finds it, update to 'Deliver the ledger to a safe contact' or 'Decipher the ledger's contents'."

#### 3. Engage thematic_question in prompt

- The `_arc.j2` section already renders the thematic question to the storyteller. Add explicit prompt language: "Your arc's thematic_question frames the moral tension of this story. Surface it through choices — force the player to confront it at least once per arc phase."
- Do NOT change code. The pipeline already renders it; the prompt just needs to assign behavioral weight.

#### 4. Make thread_progress an append-only list

- Change `ArcThread.progress` type from `str` to `list[str]` (or add a new field `progress_log: list[str]` while keeping `progress` as the latest entry for backward compatibility).
- `_apply_thread_updates` appends new progress strings instead of replacing.
- The `_thread_list.j2` section renders the full progress log for the storyteller.
- **Rationale:** The storyteller needs to see past progress to avoid repeating itself. The 8 near-identical updates to `black_market_contact` are direct evidence that single-string progress is insufficient.

#### 5. Add urgency decay guidance

- Add prompt language: "Thread urgency should decay over time. If a thread has been updated once without the player addressing it, consider lowering urgency. If it's been inactive for 3+ turns, lower urgency to background or mark it inactive."
- Code addition: a per-thread counter `turns_since_last_update` (derivable from state, not a new field — compare `thread_resolved_turn` or last update turn against current turn).
- `_thread_list.j2` can render `turns_since_last_update` in the thread display.

#### 6. Add silent-drop feedback for thread_add gate

- In the `_thread_list.j2` section (or a new `_pacing_context.j2` section), explicitly state the current gate status.
- When `gate == "block_escalate"`, prefix or append: "**Gate: blocked** — new threads will not be added this turn due to de-escalation pacing."
- No code change needed for this — the PacingContext gate value is already available to the prompt renderer.

#### 7. Discourage no-op thread_updates

- Add prompt guidance: "Only emit `thread_update` when you are changing a thread's state. Do not emit updates with all-null fields."
- This is purely a prompt change. The code already handles `updates` being empty (returns None when `mutated` is False).

#### 8. Strengthen thread scope guidance

- Add explicit rules to `storytell_system.j2`:
  - "Use `scope: scene` for threads that will resolve within the current location or within 1-3 turns. These are automatically cleaned up on location change."
  - "Use `scope: arc` only for threads that span multiple locations and are central to the arc's visible_goal. Arc-scoped threads must be explicitly resolved — they will not be cleaned up."
  - "When in doubt, prefer `scope: scene`. Over-classifying as arc creates permanent dead threads."
- Optionally: add a cap on arc-scoped threads (e.g., at most 3 active arc-scoped threads).

### Alternatives Considered and Rejected

- **Auto-detect thread scope from location change:** Rejected. The pipeline cannot retroactively reclassify threads. The location-change purge is based on declared scope, not heuristics. Teaching the LLM better scope judgment is simpler and more reliable.
- **Auto-decay urgency in code:** Rejected. The storyteller controls narrative salience. Code-decay would silently change urgency in ways that contradict narrative intent. Prompt guidance is the right tool.
- **Replace thread_update with append-only always:** Rejected. Sometimes the storyteller needs to correct or replace progress (e.g., when new information invalidates old progress). The append model should dominate, but the storyteller should be able to signal "replace" vs "append" explicitly.
- **Prevent arc-scoped thread creation in code:** Rejected. Arc-scoped threads are valid for multi-location plots. The problem is misclassification, not the existence of arc-scoped threads.

## Decision Table

| Decision | What | Why |
|---|---|---|
| visible_goal updateable without arc_resolve | New StorytellerResult.goal_update field | Decouples goal progression from arc resolution; arc_resolve is too heavyweight for incremental goal shifts |
| thread_progress changes to append-by-default | ArcThread.progress becomes list[str] or new progress_log: list[str] added | Stops investigative trail loss; storyteller can see past progress and avoid repetition |
| urgency decay is prompt-only | No code enforcement | Code cannot judge narrative salience; storyteller must own decay decisions |
| thread_add gate feedback is prompt-only | Render gate status in thread section | No code change needed; gives storyteller the awareness to avoid wasted emissions |
| scope guidance strengthened in prompt | Explicit rules and preference for scene | Misclassification is a prompt quality problem, not a code enforcement problem |
| thematic_question engagement is prompt-only | Add behavioral guidance in story context | The pipeline already renders it; only missing behavioral weight |
| no-op thread_updates discouraged via prompt | Guidance: only emit when changing state | Fixes excessive null-field updates with zero code change |

## Failure Modes and Risks

- **Storyteller ignores new prompt guidance.** Prompt guidance is advisory. If the LLM continues to misclassify scope or never emits goal_updates, the system state will not improve. Mitigation: add alert logging when scope misclassification exceeds thresholds (e.g., >50% of arc-scoped threads are resolved within 3 turns — suggesting misclassification).
- **progress_log grows unbounded.** A thread updated 20+ times will have a long progress log. Mitigation: cap rendering to the last N entries (e.g., last 5) in `_thread_list.j2`, or summarize older entries.
- **goal_update competes with arc_resolve.** The storyteller might use goal_update when it should use arc_resolve (to end the arc) or vice versa. Mitigation: prompt must clearly distinguish: "Use goal_update for mid-arc goal shifts. Use arc_resolve to end the current arc and start a new one."
- **Urgency decay guidance makes threads too passive.** If the storyteller drops urgency too aggressively, nothing feels urgent. Mitigation: monitor urgency distribution in the thread list. At least 1-2 urgent threads per active arc is healthy.
- **Scoped-thread cap creates silent drops.** If a cap on arc-scoped threads is enforced in code, threads beyond the cap would be silently dropped (same failure mode as the pacing gate). Mitigation: any cap must be explicit in the prompt, not enforced in code, with the storyteller deciding which threads to downgrade or resolve to stay under cap.

## Open Questions

- `[OPEN: progress type change — new field or replace?]` Should `ArcThread.progress` change type from `str` to `list[str]`, or should a new `progress_log: list[str]` be added alongside the existing `progress` field as the latest entry? The `list[str]` replacement is cleaner but requires a migration. The dual-field approach maintains backward compatibility but creates two sources of truth.
- `[OPEN: arc-scoped thread cap value?]` If a cap on arc-scoped threads is added, what value? 3 seems reasonable (enough for one main plot + two subplots). But any cap is arbitrary — the storyteller may legitimately need 5+ arc-scoped threads for a complex political arc.
- `[OPEN: goal_update field shape?]` Should `goal_update` be a simple `str` (new visible_goal) or a structured type with `visible_goal` + optional `goal_context`? The current code already merges `goal_context` from `ArcResolution` — a structured type aligns better with existing patterns.

## What Is Removed

Nothing. This design adds prompt guidance and one optional new field. No existing functionality is removed.

## What Is Unchanged

- `_merge_arc_update` conditional replace logic (non-empty fields only)
- `_apply_thread_updates` function signature and flow (only changes field behavior)
- `_apply_thread_resolutions` logic for moving threads to completed_threads
- `_apply_arc_resolve` logic for arc resolution + successor creation
- Pipeline order (narrate before extraction before arc director)
- Pacing gate mechanism (gate value computation and enforcement)
- `CampaignArc` structure aside from optional new goal_update field
- `ArcThread` basic lifecycle (create → update → resolve → completed)

## New Model Shapes

### GoalUpdate (new)

```
class GoalUpdate(BaseModel):
    id: str  # arc id, for multi-arc support
    visible_goal: str
    goal_context: str | None = None
```

### ThreadUpdate.progress semantics (changed)

`progress` field behavior changes from "replace" to "append-default". The storyteller can optionally prefix with `REPLACE:` to force a replacement instead of append.

No new field — same field, changed semantics. The `_apply_thread_updates` function appends new progress to existing progress (with newline or bullet separator) unless the value starts with `REPLACE:`.

## Context for Implementing LLMs

- `ccya/models.py` lines 29-48 — `ArcThread` and `CampaignArc` model shapes. Understand existing fields before adding new ones.
- `ccya/engine/turn.py` lines 139-206 — `_apply_thread_updates`. This is where progress replacement happens and where append logic will be added.
- `ccya/engine/turn.py` lines 209-286 — `_apply_arc_resolve`. Understand how arc resolution currently works and where goal_update fits alongside it.
- `ccya/engine/turn.py` lines 1119-1174 — Arc director entry point. Understand the order of operations (updates → resolve → resolutions → thread_add gate).
- `ccya/prompts/storytell_system.j2` — Primary prompt template. Lines 120-187 contain thread and beat guidance. Lines 1-120 contain visible_goal and thread_list rendering context. All prompt changes go here.
- `ccya/prompts/sections/_thread_list.j2` — Thread rendering for prompt context. Must be updated to render progress_log and turns_since_last_update.
- `ccya/prompts/sections/_arc.j2` — Arc rendering. Currently renders visible_goal and thematic_question. Must be checked for goal_update awareness.
- `plans/findings/CONSOLIDATED-EV-FINDINGS.md` — Empirical evidence for every problem this design addresses. Category 2 (thread system) and Category 4 (arc system) are most relevant.
