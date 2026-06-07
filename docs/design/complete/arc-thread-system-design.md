# Arc / Thread System Design

## Purpose

Design authority for plans that overhaul the campaign arc and thread lifecycle. Covers: visible_goal progression, arc_resolve emission, thread scope classification, thread progress accumulation, urgency decay, and the thread_add gate feedback loop.

## Problem Statement

The arc and thread systems exist but produce zero useful output across both games analyzed (51 combined turns). The arc's visible_goal is set at seed time and never updated regardless of narrative direction. Thread scope is consistently misclassified (scene events classified as arc-scoped, polluting the thread list permanently). Thread progress is a single-string overwrite that loses the investigative trail. Thread urgency never decays. Arc-scoped threads never resolve while scene-scoped threads resolve cleanly, creating a growing dead-weight tail of permanent active threads. The thread_add gate silently drops threads with no feedback to the storyteller. The entire arc/thread apparatus is a net-negative on token budget — it consumes prompt context and compute time while producing stale, misleading state.

## Constraints

- Pipeline order is fixed: narrator runs first, then extraction, then arc director. The 1-turn lag between extraction and arc director is acceptable — it predates this design and reordering is too expensive.
- The basic thread lifecycle (create → update → resolve → completed_threads) is sound and unchanged.
- `_merge_arc_update` conditional replace behavior (only overwrite visible_goal when non-empty) is correct and unchanged for the arc_resolve path. The new `goal_update` field applies via direct dict assignment, NOT through `_merge_arc_update` (which always replaces `threads[]` unconditionally — passing a bare CampaignArc would wipe the thread list).
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

- **Seed time:** `CampaignArc` is created with `visible_goal`, `goal_context` (UI-only — not rendered in prompts), empty `threads[]` and `completed_threads[]`.
- **Per turn:** The arc director runs at `turn.py:1119-1174` after `apply_delta`. It processes:
  1. `_apply_thread_updates` (line 1121) — merges storyteller's `thread_update[]` into active threads. Progress is a single-string overwrite (`model_copy(update={"progress": new_value})` at line 194).
  2. `_apply_arc_resolve` (line 1132) — checks for `storyteller_result.arc_resolve`. If present, archives current arc to `resolved_arcs[]`, auto-resolves all arc-scoped threads (moves to `completed_threads[]` with state `"superseded"`), creates a successor arc with empty `threads[]`. Scene-scoped threads are unaffected.
  3. `_apply_thread_resolutions` (line 1143) — moves resolved/failed/abandoned threads from `threads[]` to `completed_threads[]`.
  4. Thread_add gate (line 1153) — checks `PacingContext.gate == "allow"`. If blocked, silenty discards the new thread with a debug log message.
- `visible_goal` is only updated by `_merge_arc_update` when `arc_resolve` fires (the `ArcResolution` model carries new `visible_goal`, `goal_context`). Without `arc_resolve`, `visible_goal` is only changeable via `goal_update`. `goal_context` is also updated on arc_resolve but is UI-only — never rendered in prompts or used in pipeline logic.

### Thread lifecycle

- **Add:** Storyteller emits `thread_add` with id, summary, scope, urgency. Pacing gate may silently drop it.
- **Update:** Storyteller emits `thread_update[]` with id + optional fields. `_apply_thread_updates` finds the thread by id, calls `model_copy(update=...)` which **replaces** progress, summary, urgency entirely.
- **Resolve:** Storyteller emits `thread_resolve[]` with id + resolution_state + outcome. Thread moves to `completed_threads[]`. Resolution states (as typed in `ThreadResolution` model): `"resolved"`, `"failed"`, `"abandoned"`. The prompt guidance only lists these three; `"superseded"` is not a recognized output value.
- **Purge:** On location change, `delta_builder.py` removes threads with `scope="scene"` from state before the arc director re-derives.

### Models

`ArcThread` (pre-change): id, summary, scope (scene|arc), active (bool), urgency (background|normal|urgent), progress (str — single string, overwritten on every update), resolution_state, outcome, resolved_turn.

`CampaignArc`: visible_goal (str), goal_context (str — UI-only, never rendered in prompts), threads (list[ArcThread]), completed_threads (list[ArcThread]), resolution, last_thread_created_turn.

`ThreadUpdate`: id, active (optional), urgency (optional), progress (optional).

`ArcResolution`: resolution, visible_goal, goal_context, drop_threads, new_threads.

### Pacing gate interaction

The `PacingContext.gate` is `"block_escalate"` when `deescalate >= 0.5` (high de-escalation from ruling phase). When blocked, `thread_add` at line 1158 logs a debug message and skips the add. No feedback reaches the storyteller.

## Problems with Current State

1. **Arc never progresses.** `arc_resolve` was never emitted across 51 turns in two games. Without it, `visible_goal` is frozen at seed-time values. In the zombie save, the visible goal ("Secure the medical archives") was obsolete for 30 turns but never updated.

2. **Thread scope misclassification is persistent and damaging.** Both games classified single-location events as "arc" scope (8 of 8 cross-game misclassifications in CONSOLIDATED-EV-FINDINGS.md). Arc-scoped threads survive location-change purge and accumulate permanently. In the zombie save's final state, 6 of 8 active threads should be scene-scoped but are classified as arc.

3. **Thread progress is lost on every update.** `_apply_thread_updates` replaces `thread.progress` entirely. The storyteller cannot see past progress values — only the latest string. In the noir save, T4's finding ("no blade among debris") was overwritten by T5's update ("transcribed details"). In the zombie save, `black_market_contact` received 8 updates with near-identical summaries because the storyteller couldn't see what was already recorded.

4. **Thread urgency never decays.** The storyteller only increases urgency or leaves it static. No thread in either game ever transitioned urgent → normal → background. `quarantine_spread` was urgent for 34 turns with no updates. `david_betrayal` has been urgent since T5 with David absent since T6.

5. **Thread_add gate has no feedback loop.** When the pacing gate blocks a thread_add, the thread is silently dropped. The storyteller has no way to know the add failed. At zombie T12, `santana_collusion_risk` was emitted by the storyteller but silently discarded because the gate was `"block_escalate"` from a Breathe directive.

6. **No-op thread_updates waste context.** Storyteller emits `thread_update` calls where all fields are None or empty — no meaningful change. The LLM receives no guidance to avoid this.

7. **Arc-scoped threads cannot resolve.** Scene-scoped threads resolve within 1-3 turns (confirmed in zombie T23-T34). Arc-scoped threads persist indefinitely with no resolution path. The thread list stabilizes at ~8 active threads because every add is balanced by a resolve — but only scene-scoped threads resolve.

## Proposed Solution

### Core Changes

#### 1. Make visible_goal updateable without arc_resolve

- Add `goal_update: str | None = None` to `StorytellerResult`. Bare string, no new model class — the value is the new `visible_goal`.
- In the arc director sequence (between thread updates and arc resolve), extract `goal_update` and apply it directly to the arc dict: `if storyteller_result.goal_update: state["arc"]["visible_goal"] = storyteller_result.goal_update`.
- Does NOT go through `_merge_arc_update` — that function replaces `threads[]` unconditionally, so passing a bare campaign arc would wipe the thread list. A direct dict-level assignment is simpler and correct.
- **Ordering:** goal_update applies before arc_resolve. If both fire on the same turn, arc_resolve wins (ending the arc supersedes a mid-arc update).
- **Rationale:** The storyteller demonstrably drives narrative direction but has no way to formally acknowledge that the goal has shifted. A dedicated goal_update field decouples goal progression from the arc resolution lifecycle.

#### 2. Add prompt guidance for visible_goal updates

- In `storytell_system.j2`, add guidance: "When the player makes significant progress toward or permanently changes the current visible_goal, update it to reflect the new state of the arc."
- Include concrete examples: "If the goal was 'Find the stolen ledger' and the player finds it, update to 'Deliver the ledger to a safe contact' or 'Decipher the ledger's contents'."

#### 3. Make thread_progress append-only (no boolean)

- Change `ArcThread.progress` type from `str` to `list[str]`. No backward compat needed — constraint #16.
- Always append. No boolean, no kind enum, no prefix parsing. Every `progress` value in a `thread_update` is appended to the list. The full log is rendered for the storyteller.
- When prior progress is invalidated, the storyteller appends a natural-language entry acknowledging the shift (e.g., "Correction: the dock lead was a dead end — the ledger is in the mayor's safe."). The renderer shows all entries in order; the LLM reading the log on subsequent turns sees the full trail.
- The `_thread_list.j2` section renders the full progress log for the storyteller.
- **Rationale:** The storyteller needs to see past progress to avoid repeating itself. The 8 near-identical updates to `black_market_contact` are direct evidence that single-string progress is insufficient. A boolean flag adds complexity the LLM won't reliably use; natural-language corrections are simpler and preserve the investigative trail.

**Same-turn resolve+update conflict detection:** Finding 2.7 (CONSOLIDATED-EV-FINDINGS.md) confirmed that at v2 T18 the storyteller emitted both `thread_resolve` (abandon) and `thread_update` (set `active=true`, new summary) for the same thread id in a single output, leaving the thread in contradictory state. The arc director's processing order (updates at line 1121, resolutions at line 1143) means resolution takes precedence over a same-turn update for the same thread id — the update fires, then the resolution fires, which is the correct precedence (resolution wins). The executor must verify this ordering is preserved and should add a debug log warning when both a `thread_update` and `thread_resolve` are present for the same `id` in a single turn's output — this is always an LLM error and should be surfaced for monitoring.

#### 4. Add urgency decay guidance

- Add prompt language: "Thread urgency should decay over time. If a thread has been updated once without the player addressing it, consider lowering urgency. If it's been inactive for 3+ turns, lower urgency to background or mark it inactive."
- Add `last_updated_turn: int | None = None` to `ArcThread`. Set to current turn on every `_apply_thread_updates` mutation. Rendered as `turns_since_last_update` in the prompt context for the storyteller to see.
- **Rationale:** `ArcThread` has no timestamp field in source. "Derivable from state without a new field" was inaccurate — there's no update-turn tracking. The field is one integer, zero ongoing cost.

#### 5. Add silent-drop feedback for thread_add gate

- In the `_thread_list.j2` section (or a new `_pacing_context.j2` section), explicitly state the current gate status.
- When `gate == "block_escalate"`, prefix or append: "**Gate: blocked** — new threads will not be added this turn due to de-escalation pacing."
- No code change needed for this — the PacingContext gate value is already available to the prompt renderer.

#### 6. Discourage no-op thread_updates

- Add prompt guidance: "Only emit `thread_update` when you are changing a thread's state. Do not emit updates with all-null fields."
- This is purely a prompt change. The code already handles `updates` being empty (returns None when `mutated` is False).

#### 7. Strengthen thread scope guidance + thread ecology

- Add explicit rules to `storytell_system.j2`:
  - "Use `scope: scene` for threads that will resolve within the current location or within 1-3 turns. These are automatically cleaned up on location change."
  - "Use `scope: arc` only for threads that span multiple locations and are central to the arc's visible_goal. Arc-scoped threads auto-close when the arc resolves. Mid-arc, they persist across location changes — resolve them explicitly if they become irrelevant before the arc ends."
  - "When in doubt, prefer `scope: scene`. Over-classifying as arc creates permanent dead threads."
  - "Before adding a new thread, check whether an existing thread already covers this domain. If an existing thread is related, update it with new progress rather than creating a new thread. New threads should represent genuinely new narrative concerns, not sub-events of an existing one. This directly addresses Finding 2.9 (CONSOLIDATED-EV-FINDINGS.md), where three separate threads were created for different facets of the same entity threat event."
  - "Keep thread summaries short (3-7 words) and generic — broad enough for 3-4+ substantive progress updates over the thread's lifetime. A thread titled 'The FEDRA conspiracy' can absorb every new discovery about FEDRA's secret projects; don't split it into 'entity_in_the_truck', 'sludge_outbreak', 'containment_hub_collapse'."
  - "Arc-scoped thread summaries should be especially stable. Prefer updating the progress log over changing the summary. A summary change should happen at most 1-2 times per arc (when the thread's nature fundamentally shifts)."
- Add soft cap guidance (rendered in prompt, not code-enforced):
  - Aim for **2-3 arc-scoped** and **1-2 scene-scoped** threads active at any time — **~5 total max**.
  - Keep each thread's domain broad; use the appendable progress log to record specific, grounded developments within that domain.
  - Aim for thread summaries short enough (3-7 words) that a single thread can encompass 3-4+ distinct updates before its summary needs changing.
  - If you need to add a thread near the cap, downgrade or resolve an existing one first.
- **Rationale:** The soft cap serves two purposes. First, the 100% misclassification rate (8/8 across two games) is structural — the LLM lacks distinguishing signal, not better instructions. The soft cap renders the constraint visibly so the storyteller self-regulates. Combined with the progress log, the storyteller has room to evolve existing threads without creating new ones. Second, it is a token budget decision: Finding 2.8 (CONSOLIDATED-EV-FINDINGS.md) quantified thread section growth from 781 chars at T1 to 2408 chars at T26 (~1000 tokens of overhead), growing O(n) in turns played. Dead arc threads that are never resolved or pruned are the primary driver of this unbounded growth. The soft cap and arc-scoped thread guidance together are the only mechanism in this design that limits unbounded prompt growth.

#### 8. Add arc resolution guidance

- When `arc_resolve` fires, the system auto-resolves all active arc-scoped threads (moves to `completed_threads[]` with state `"superseded"`). The successor arc starts with an empty `threads[]`. Scene-scoped threads are unaffected — they have their own resolution lifecycle. The storyteller should re-create arc-scoped threads if they remain relevant in the new arc. Add guidance to `storytell_system.j2`:
  - **All threads resolved or irrelevant.** Every arc-scoped thread is completed, failed, abandoned, or narratively moot. The arc has run its course — resolve it.
  - **Narrative shifted fundamentally.** The story's center of gravity has moved. Even if threads remain unresolved, the arc's premise no longer fits. Example: arc was "Survive the quarantine zone collapse" but the player has escaped and the story is now about cross-wasteland politics. A new arc is warranted. Multiple `goal_update` corrections in quick succession is a diagnostic signal — if you've needed 3+ `goal_update` changes, the arc no longer fits.
  - **Core conflict resolved.** The player decisively achieved or failed the central conflict. Remaining threads are clean-up, not arc-driving content. Create a successor arc with narrower scope.
  - **Arc has been coasting 8+ turns.** The `visible_goal` is unchanged, no `goal_update` has fired, and threads receive updates but nothing feels fresh. The arc is momentum-only — resolve it and start a focused successor.
- **Anti-guidance:** "Do NOT resolve an arc just because threads are getting long or because you want to clean up. Arc-scoped threads auto-close when the arc resolves, but that's a side effect, not a reason to end the arc. Use `goal_update`, thread progress updates, and thread resolutions for mid-arc maintenance. `arc_resolve` should feel climactic — it ends a narrative chapter."
- **Pacing awareness:** Arc resolution is climactic. Avoid resolving during `Breathe` turns (low tension = wrong energy for a chapter ending). Prefer `Scene Imperative` or neutral pacing. This is prompt guidance, not code-enforced — if the story demands resolution on a Breathe turn, the storyteller can override.
- **Target cadence:** Zero `arc_resolve` events across 77 analyzed turns means the system is broken, not that arcs should fire every turn. Target roughly one arc per 8-15 turns (2-3 play sessions). A resolved arc should feel like a season finale, not a commercial break.

### Alternatives Considered and Rejected

- **Auto-detect thread scope from location change:** Rejected. The pipeline cannot retroactively reclassify threads. The location-change purge is based on declared scope, not heuristics. Teaching the LLM better scope judgment is simpler and more reliable.
- **Auto-decay urgency in code:** Rejected. The storyteller controls narrative salience. Code-decay would silently change urgency in ways that contradict narrative intent. Prompt guidance is the right tool.
- ~~**Replace thread_update with append-only always:** Previously rejected out of concern that the storyteller needs to correct invalidated progress. Now accepted — the boolean flag added complexity without reliability gain, and natural-language correction entries in the log handle invalidation better.~~
- **Prevent arc-scoped thread creation in code:** Rejected. Arc-scoped threads are valid for multi-location plots. The problem is misclassification, not the existence of arc-scoped threads.
- **Auto-reclassify arc-scoped threads based on location change:** Rejected. The pipeline cannot retroactively reclassify threads — scope is declared at creation time. A soft cap with visible feedback is more practical.

## Decision Table

| Decision | What | Why |
| --- | --- | --- |
| visible_goal updateable without arc_resolve | `StorytellerResult.goal_update: str | None` — bare string, direct dict assignment, before arc_resolve in director sequence | Decouples goal progression from arc resolution; arc_resolve is too heavyweight for incremental goal shifts |
| thread_progress is always append | `ArcThread.progress` becomes `list[str]`; no boolean, no kind enum — every update appends | Preserves investigative trail; natural-language corrections in appended entries handle invalidation better than a boolean the LLM won't set reliably |
| urgency decay is prompt + `last_updated_turn` field | New `ArcThread.last_updated_turn: int | None` set on every update; prompt guidance to decay urgency over time | Code tracks update timing; storyteller decides urgency level |
| thread_add gate feedback is prompt-only | Render gate status in thread section | No code change needed; gives storyteller the awareness to avoid wasted emissions |
| scope guidance + soft cap in prompt | Explicit rules + target: 2-3 arc-scoped, 1-2 scene-scoped, ~5 total max; broad thread domains; progress log for granularity | 100% misclassification rate is structural; soft cap renders constraint visibly for self-regulation |
| no-op thread_updates discouraged via prompt | Guidance: only emit when changing state | Fixes excessive null-field updates with zero code change |
| ThreadUpdate.summary removed | `ThreadUpdate` no longer has a `summary` field. Threads are statically summarized after creation. Replace via resolve+add, not update. | Enforces static-summary contract at the model level; old saves with summary in JSON are silently ignored |

## Failure Modes and Risks

- **Storyteller ignores new prompt guidance.** Prompt guidance is advisory. If the LLM continues to misclassify scope or never emits goal_updates, the system state will not improve. Mitigation: add alert logging when scope misclassification exceeds thresholds (e.g., >50% of arc-scoped threads are resolved within 3 turns — suggesting misclassification).
- **progress_log grows unbounded.** A thread updated 20+ times will have a long progress log. Mitigation: cap rendering to the last N entries (e.g., last 5) in `_thread_list.j2`, or summarize older entries.
- **goal_update competes with arc_resolve.** The storyteller might use goal_update when it should use arc_resolve (to end the arc) or vice versa. Mitigation: prompt must clearly distinguish: "Use goal_update for mid-arc goal shifts. Use arc_resolve to end the current arc and start a new one." If both fire on the same turn, arc_resolve wins (order: goal_update → arc_resolve).
- **Urgency decay guidance makes threads too passive.** If the storyteller drops urgency too aggressively, nothing feels urgent. Mitigation: monitor urgency distribution in the thread list. At least 1-2 urgent threads per active arc is healthy.
- **Soft cap ignored by LLM.** The cap is rendered but not enforced. The LLM may still accumulate 8+ threads. Mitigation: monitor active thread count; if it exceeds 6 for 5+ consecutive turns, escalate to a code-enforced cap or automatic reclassification.
- **goal_update applied directly to dict bypasses _merge_arc_update's conditional replace.** The direct assignment is unconditional — it always overwrites `visible_goal`. This is intentional: if the storyteller emitted a goal_update, they meant to change the goal. The conditional-replace safety net of `_merge_arc_update` only applies to arc_resolve path.

## Open Questions (Resolved)

These questions from the original design have been resolved during review:

- **progress type change** → `list[str]` replacement. Backwards compatibility not required (constraint #16). Two-source-of-truth problem outweighs migration cost.
- **arc-scoped thread cap** → Soft cap of 2-3 arc-scoped, 1-2 scene-scoped, ~5 total max. Rendered in prompt context, not code-enforced. Broad thread domains + appendable progress log reduce need for new threads.
- **goal_update field shape** → Bare `str | None = None`. No model class, no `id`, no `goal_context`. If the arc needs `goal_context` changes, those go through arc_resolve.

## What Is Removed

- `ArcThread.progress` single-string field — replaced with `list[str]`. Always append, no replace mechanism.
- `_merge_arc_update` as the sole mechanism for `visible_goal` updates — `goal_update` now applies via direct dict assignment.
- `thematic_question` field — removed from `CampaignArc` and `ArcResolution`. No behavioral value evidenced across 77 turns.
- `progress_replace` boolean — removed. Always append with natural-language corrections.

## What Is Changed

- `CampaignArc` — `thematic_question` removed. `goal_context` now UI-only (not rendered in prompts).
- `_apply_arc_resolve` — arc-scoped threads auto-resolve to `completed_threads[]` (state `"superseded"`) instead of carrying forward. Successor arc starts with empty `threads[]`.
- `_apply_thread_updates` — progress is always appended (`list[str]`). No boolean, no replace mechanism.
- `ThreadUpdate.summary` removed — threads are static after creation. Use resolve+add instead of updating summary.

## What Is Unchanged

- Pipeline order (narrate before extraction before arc director).
- Pacing gate mechanism (gate value computation and enforcement).
- `_merge_arc_update` conditional replace logic (non-empty fields only) — still used by arc_resolve and thread_resolutions paths.
- `_apply_thread_resolutions` logic for moving threads to completed_threads.
- `ArcThread` basic lifecycle (create → update → resolve → completed).
- `StorytellerResult` structure aside from the new `goal_update: str | None` field.

## New Model Shapes

### StorytellerResult.goal_update (new field)

```
goal_update: str | None = None
```

Bare string — the value is the new `visible_goal`. No new model class. Applied directly to the arc dict outside of `_merge_arc_update`.

### ThreadUpdate (changed — `progress_replace` removed)

```
class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: str | None = None
    progress: str | None = None
    progress_kind: Literal["advancement", "setback", "shift"] | None = None
```

`progress` is always appended to `ArcThread.progress`. No boolean, no replace — natural-language corrections in the appended text handle invalidation. Migration: old saves with `progress_replace` in JSON are silently ignored (extra keys don't break Pydantic).

### ArcThread (changed)

```
class ArcThread(BaseModel):
    id: str
    summary: str
    scope: str  # scene | arc
    active: bool = True
    urgency: str = "normal"  # background | normal | urgent
    progress: list[str] = []  # CHANGED from str to list[str]
    last_updated_turn: int | None = None  # NEW
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
```

**Migration:** Existing saves have `progress: "some string"` (a single str). A Pydantic `field_validator("progress", mode="wrap")` is needed to coerce old string values: if the loaded value is a `str`, wrap it in a list `[value]`. Without this, loading a pre-change save will fail Pydantic validation.

### CampaignArc (changed)

```
class CampaignArc(BaseModel):
    visible_goal: str
    goal_context: str  # UI-only — never rendered in prompts or pipeline
    threads: list[ArcThread] = []
    completed_threads: list[ArcThread] = []
    resolution: str | None = None
    last_thread_created_turn: int | None = None
```

`thematic_question` removed. `goal_context` is present but only surfaced in the player UI (tooltip/description text). The pipeline and prompts never read it.

## Context for Implementing LLMs

- `ccya/models.py` lines 29-48 — `ArcThread` and `CampaignArc` model shapes. Understand existing fields before adding new ones.
- `ccya/engine/turn.py` lines 139-206 — `_apply_thread_updates`. This is where progress replacement happens and where append logic will be added.
- `ccya/engine/turn.py` lines 209-286 — `_apply_arc_resolve`. Understand how arc resolution currently works and where goal_update fits alongside it.
- `ccya/engine/turn.py` lines 1119-1174 — Arc director entry point. The new sequence: 1) thread updates (1121), 2) **goal_update apply** (new — between 1129 and 1131), 3) arc resolve (1132), 4) thread resolutions (1143), 5) thread_add gate (1153).
- `ccya/prompts/storytell_system.j2` — Primary prompt template. Lines 120-187 contain thread and beat guidance. Lines 1-120 contain visible_goal and thread_list rendering context. All prompt changes go here.
- `ccya/prompts/sections/_thread_list.j2` — Thread rendering for prompt context. Must be updated to render progress log (`list[str]`) as a human-readable list, plus `turns_since_last_update` from `last_updated_turn`. Also render the soft-cap guidance: current arc-scoped count vs target, gate status.
- `ccya/prompts/sections/_arc.j2` — Arc rendering. Renders `visible_goal`. `thematic_question` removed. `goal_context` removed from prompts (UI-only). Must be checked for `goal_update` awareness.
- `plans/findings/CONSOLIDATED-EV-FINDINGS.md` — Empirical evidence for every problem this design addresses. Category 2 (thread system) and Category 4 (arc system) are most relevant.
