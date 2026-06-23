# Arc System Redesign

> **Status:** scoping
> **Related designs:**
> - [Seed System Worldbuilding Redesign](./seed-worldbuilding-redesign.md)
>
> **Data sources:**
> - [Eval Cycle 1 Report (2026-06-22)](../../evals/runs/2026-06-22_0.28.0-72-gdabe3b81_dabe3b8/REPORT.md)
> - [Outer Rim Full Eval (2026-06-21)](../../evals/findings/outer-rim-eval-2026-06-21.md)
> - [2026-06-21 Report](../../evals/runs/2026-06-21_0.28.0-56-g47ff6261_47ff626/REPORT.md)

## Problem Statement

The arc system (CampaignArc, ArcThread, arc resolution, arc lifecycle) is broken in
practice. Eval data shows threads accumulate without resolution, arc resolution fires
too frequently with no-op goal updates, and the system never closes narrative arcs.
The current model needs a fundamental redesign.

## Observed Failures (from eval data)

### 1. Zero arc resolutions across all packs

105 threads created across 5 packs (25 turns each). **Zero** arc resolutions occurred.
The game never closes its narrative arcs. Threads are only updated or left pending.

### 2. Thread resolution rate is abysmal

| Pack | Created | Resolved | Rate |
|------|---------|----------|------|
| noir | 17 | 1 | 5.9% |
| space-western | 15 | 4 | 26.7% |
| golden-piracy | 24 | 3 | 12.5% |
| zombie | 16 | 3 | 18.8% |
| ww2 | 18 | 3 | 16.7% |

Threads accumulate. Auto-dormant (4 turns) and auto-completion (progress threshold)
mechanisms exist but don't produce narrative satisfaction — dormant threads are just
forgotten, not resolved.

### 3. Arc resolution fires too fast and too often

Outer Rim (34 turns): arc_resolve fired at T4, T6, T15, T31 — all with the same
visible goal "Establish a reliable smuggling route through the Millerport blockade."

Root cause: the LLM can't update visible_goal without closing/reopening the arc, so
it uses arc_resolve to signal "this mini-arc is done." The prompt says target 8-15
turns per arc but the LLM ignores both.

### 4. Arc resolution no-ops

Same visible_goal across arc resolutions means the "new arc" after resolution is
functionally identical to the old one. This is a no-op wrapped in arc resolution
overhead.

### 5. Empty arc_resolve crashes validation

LLM emits `arc_resolve: {}` (empty dict). Pydantic `ArcResolution` requires
`resolution`, `visible_goal`, `goal_context` so `{}` fails validation. Fix was to
nullify before Pydantic sees it, but this masks the underlying prompt problem.

### 6. chapter_end has no behavioral effect

The `chapter_end` field on `StorytellerResult` is logged and recorded as
`last_chapter_end_turn` in meta, but the engine does NOT reset arc state on
chapter_end. It's a signal for future use — but the storyteller emits it expecting
it to do something.

### 7. Thread types not assigned

Storyteller output missing `type` on `thread_add`/`thread_update`. The prompt says
"set type to match the thread's semantic role" but the LLM treats it as optional.

### 8. No TTL on completed_threads

Completed threads accumulate forever. No cleanup mechanism.

### 9. chapter_end vs arc_resolve confusion

The storyteller doesn't understand when to use `chapter_end` vs `arc_resolve`.
`chapter_end` should mark a narrative beat without closing the arc. `arc_resolve`
should only fire for major chapter endings. The prompt guidance is insufficient.

## Design Principles

1. **Arcs must close.** The system should naturally produce arc resolutions over
   time, not let threads accumulate indefinitely.
2. **Thread lifecycle is first-class.** Threads should have a clear lifecycle:
   born → developed → resolved/failed/abandoned. Not just "added → dormant → forgotten."
3. **Arc resolution is rare and meaningful.** Not every beat change warrants a new
   arc. Arc resolution should signal a major narrative shift.
4. **chapter_end is a narrative marker, not a state reset.** It marks a turning point
   in the story without closing the arc.
5. **The LLM doesn't need to manage arcs directly.** Arc lifecycle management should
   be driven by engine heuristics, not LLM decisions. The LLM should provide
   narrative content; the engine should manage thread lifecycle.

## Open Questions

- Should arcs be auto-resolved when all threads are resolved/failed/abandoned?
- Should thread lifecycle be fully engine-driven (auto-dormant, auto-complete, auto-cull)
  with the LLM only providing narrative content?
- How does `arc_origin` (seed worldbuilding redesign) fit into the new arc model?
- How does `visible_goal` (seed worldbuilding redesign) fit into the new arc model?
- Should visible_goal change without arc resolution? (Currently it doesn't — goal
  changes require arc_resolve which closes the arc.)
- How does arc resolution work in the new system?
- How do threads interact with arcs in the new system?
- How does the sanitizer interact with the new arc system?
- How does the new arc system interact with the seed worldbuilding redesign?
- How does the new arc system interact with the world state lifecycle (Workstream 2)?
- What TTL should completed_threads use?
- Should thread types be required or optional?

## Scope

This design is separate from the seed worldbuilding redesign (Workstream 1) and
world state lifecycle (Workstream 2), but needs contract alignment with both.
