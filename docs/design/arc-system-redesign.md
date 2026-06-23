# Arc System Redesign

> **Status:** scoping
> **Related designs:**
> - [Seed System Worldbuilding Redesign](./seed-worldbuilding-redesign.md)
>
> **Discovery/evidence:** [Arc System — Discovery](../discovery/arc-system-problems.md)
>   Comprehensive evidence file: eval data, prompt evolution trace, code-based findings, checker gaps, state model issues.

## Problem Statement

The arc system (CampaignArc, ArcThread, arc resolution, arc lifecycle) is broken in
practice. Eval data shows threads accumulate without resolution, arc resolution fires
too frequently with no-op goal updates, and the system never closes narrative arcs.
The current model needs a fundamental redesign.

See [Discovery](../discovery/arc-system-problems.md) for the full evidence base:
- 7 eval cycles (June 17–22, 2026) showing thread resolution rate regression
- Zero arc resolutions across 5 packs in Eval Cycle 1 (105 threads, 0 closes)
- Prompt evolution trace showing changes between each eval period
- 15 structural, naming, engine, validation, and prompt integration problems
- State model issues, checker gaps, sanitizer integration problems

## Design Principles

1. **Arcs must close.** The system should naturally produce arc resolutions over
   time, not let threads accumulate indefinitely.

2. **Thread lifecycle is first-class.** Threads should have a clear lifecycle:
   born → developed → resolved/failed/abandoned. Not just "added → dormant → forgotten."

3. **Arc resolution is rare and meaningful.** Not every beat change warrants a new
   arc. Arc resolution should signal a major narrative shift. Target cadence: 8–15
   turns between resolutions.

4. **chapter_end is removed.** It was a patch for arc_resolve misuse. It has no
   behavioral effect and adds cognitive load. See decisions below.

5. **The LLM doesn't need to manage arcs directly.** Arc lifecycle management should
   be driven by engine heuristics, not LLM decisions. The LLM should provide
   narrative content; the engine should manage thread lifecycle.

6. **Schema fields should be independent.** No bundling thread cleanup, thread creation,
   and arc-ending into one JSON object. Each operation should be its own field.

7. **Required fields must have mechanical purpose.** If a field is required by schema
   but UI-only (like `goal_context`), it should be removed from the schema.

8. **Naming matters.** LLMs are natural language models. Field names are prompts.
   Names should signal when to update (or not update) a field.

## Decisions

### Naming

- **`progress` → `major_updates`** — Signals "only when something worth noting happens."
  The word "major" does the heavy lifting. Not a running play-by-play; a journal of
  important developments.
- **`visible_goal` → rename needed** — Needs a shorter name that denotes "not a one-turn
  objective." Candidates: `long_term_objective`, `active_objective`, `objective`.
  The name should signal it's a medium-to-long-term pursuit (5–15 turns), not something
  resolved in a single turn.
- **`goal_context` → `arc_origin`** — `goal_context` is UI-only noise. `arc_origin`
  (2–3 sentences, past tense, "how did the PC end up here?") replaces it. Placement:
  UI (sidebar tooltip) and seed opening narration only. NOT in narrate/storytell prompts.
  Each arc gets its own `arc_origin` at creation time (seed or successor arc).

### chapter_end

**Removed.** It was added as a patch for arc_resolve misuse (Jun 18). It has no
behavioral effect — just stamps `last_chapter_end_turn` in meta. It adds cognitive load
by existing in the same JSON object as `arc_resolve`, making it feel like an option
rather than a signal. If arc_resolve is decoupled (see below), chapter_end has no
purpose.

### Thread type stability

**Stable by default.** Type (threat/opportunity/complication/revelation) should rarely
change. The storyteller and sanitizer can change it, but they must provide a `reason`
field explaining why. Not every threat that's neutralized becomes an opportunity — it
needs a good narrative reason.

### Dormant thread TTL

**Dormancy at 8 turns, archival at 13 turns.** Auto-dormant threshold moves from 4 to
8 turns (configurable). When a thread has been dormant for 5 more turns (13 total),
the sanitizer marks it for archival. Once archived, it's permanently archived.

Future consideration (out of scope): when a thread is approaching archival (e.g., at
turn 10 of being dormant), hint to the narrator to resurface it if there's relevance.
This is risky because LLMs are bad at ignoring things. May need a pre-validation step
(sanitizer decides if resurfacing is warranted).

### Thread → world state promotion

**Two-step: storyteller flags, sanitizer confirms.** When a thread resolves or an arc
resolves, the storyteller can flag it as a `world_state_candidate`. The sanitizer
(confirms every 5 turns) decides if it's still relevant and promotes it to world state.
This gives the resolved thread 0–5 turns for the sanitizer to evaluate. The resolved
thread needs a `resolved_turn` marker so the sanitizer knows how many turns it's been.

The sanitizer also has full authority to consolidate, remove, update, or fold multiple
world state facts into one. It is the ultimate authority on world state.

### Multiple arcs

**Deferred.** Whether threads cleanly fit into multiple arcs (1–3 concurrent, each with
its own objective) deserves more discussion. Deferred to a future design.

### Auto-thread completion

**Remove if present.** Hard TTL on active threads (auto-resolve when progress entries
>= threshold) is a terrible idea. Threads should be resolved by the storyteller via
`thread_resolve`, not auto-completed by the engine. A TTL on resolved threads to move
them to archived is acceptable.

### Dead state

- **`urgency_set_turn`** — Deprecated. Never read or written. Delete.
- **`promote_to_world_state`** — Replaced by two-step candidate system above. Delete.

## Open Questions

### Convergence Starvation (Pacing Engine — Out of Scope)

The pacing engine's convergence system has a critical gap: when all 5 convergence components are 0, there's no mechanism to recover. Eval Cycle 2 showed T20-T22 in noir with convergence score = 0 across all components (no urgent threads, no threat threads, scene age = 0, no beat streak, no dice weight). The opportunist persona's stealth-heavy play style starves convergence.

This is a **pacing engine problem**, not an arc system problem. The arc redesign doesn't address it. Questions:
- Should convergence have a proactive injection mechanism (e.g., "if convergence has been <2 for N turns, inject a pressure beat")?
- Should the phase machine allow narrative-based transitions (e.g., "if the player has been in stealth for 5 turns, transition to a new phase based on narrative context, not just convergence score")?
- Should the ruling system be less generous with "routine" skips that starve dice_weight?

The convergence threshold was lowered from 3 to 2 in commit `eed5878` to help with starvation, but it hasn't helped much. Previously, the problem may have been overly passive NPCs (which are apparently doing better now) and NPCs not getting their personalities correctly due to a misconfiguration.

### Progress kind categories

- **Progress kind categories** — `advancement`/`setback`/`shift` are useless. Options:
  (a) Drop entirely, (b) Tie to mechanics (numeric ticker: advancement ticks up,
  setback ticks down, threshold triggers hints), (c) Replace with signal categories
  (e.g., "near_resolution", "stalled", "escalating"). Needs more thought. See
  [Discovery](../discovery/arc-system-problems.md#12-thread-progress-kinds-vague-classifications).
- **`visible_goal` rename** — Needs a short name denoting "not a one-turn objective."
  Candidates: `long_term_objective`, `active_objective`, `objective`.
- **Arc age tracking** — No `created_turn` or `started_turn` on CampaignArc. Should
  add for measuring arc age and enforcing resolution cadence.
- **Completed threads TTL** — Should completed_threads have a TTL? Currently they
  accumulate forever within an arc.
- **Thread archival resurfacing** — Should dormant threads approaching archival get a
  resurfacing hint? (See dormant thread TTL above.)
- **How does `pc.situation` (seed worldbuilding redesign) interact with arcs?**
  Player situation (vessel, home port, crew, etc.) is updatable and important at
  turn 15 and 25. How does it feed into arc context?
- **How does `arc_origin` interact with the new arc model?** It's UI-only + opening
  narration. Does it need to feed into prompts for early turns?
- **How does the new arc system interact with the world state lifecycle (Workstream 2)?**
  Thread/arc resolution should feed into world state (see decisions above).
- **Should arcs be auto-resolved when all threads are resolved/failed/abandoned?**
- **Should thread urgency be graduated (more than 3 states)?** Currently
  background/normal/urgent is too coarse.

## Scope

This design coordinates with:
- **Seed System Worldbuilding Redesign** (Workstream 1: seed worldbuilding, Workstream 2:
  world state lifecycle) — contract alignment on `arc_origin`, `visible_goal` rename,
  thread→world state promotion, `pc.situation` interaction.
- **Dynamic Factions** (deferred) — factions will feed into arc/thread generation.
- **Multiple arcs** (deferred) — whether threads cleanly fit into multiple concurrent
  arcs.

Implementation order (cross-cutting):
1. Clear dead state (`goal_context` → `arc_origin`, `urgency_set_turn`, `promote_to_world_state`)
2. Decouple `arc_resolve` from thread operations (structural fix)
3. Rename fields (`progress` → `major_updates`, `visible_goal` → rename, remove `chapter_end`)
4. Adjust engine thresholds (auto-dormant 4→8, archival at 13)
5. Add two-step world state candidate system
6. Remove auto-thread completion if present
7. Progress kind categories — decide and implement (or drop)

> **Note on execution order:** It's unclear whether the arc system redesign or the seed
> worldbuilding redesign should run first. They have interdependencies (arc_origin,
> visible_goal rename, thread→world state promotion). Options:
> (a) Arc system first, seed worldbuilding second (arc_origin is defined first),
> (b) Seed worldbuilding first, arc system second (pc.situation foundation first),
> (c) Split into multiple plans with shared foundation steps.
> This needs to be decided before planning begins.
