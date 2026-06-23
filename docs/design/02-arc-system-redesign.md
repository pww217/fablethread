# 02-Arc System Redesign

> **Status:** scoping
> **Related designs:**
> - [01-Primitives](./01-primitives.md) — Shared building blocks (field renames, TTL, pressure score, pc.situation)
> - [03-Seed Worldbuilding Redesign](./03-seed-worldbuilding-redesign.md)
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

4. **The LLM doesn't need to manage arcs directly.** Arc lifecycle management should
   be driven by engine heuristics, not LLM decisions. The LLM should provide
   narrative content; the engine should manage thread lifecycle.

5. **Schema fields should be independent.** No bundling thread cleanup, thread creation,
   and arc-ending into one JSON object. Each operation should be its own field.

6. **Naming matters.** LLMs are natural language models. Field names are prompts.
   Names should signal when to update (or not update) a field.
   See [Primitives](./01-primitives.md#field-renames-and-deletions) for all renames.

## Decisions

### Thread type stability

**Stable by default.** Type (threat/opportunity/complication/revelation) should rarely
change. The storyteller and sanitizer can change it, but they must provide a `reason`
field explaining why. Not every threat that's neutralized becomes an opportunity — it
needs a good narrative reason.

**Model change:** Add `reason: str | None` to `ThreadUpdate` in `state.py:170`.
When the storyteller or sanitizer changes a thread's type, the `reason` field must
explain the narrative justification. If no reason is needed, set to `null`.

### Thread → world state promotion

**Two-step: storyteller flags, sanitizer confirms.** When a thread resolves or an arc
resolves, the storyteller can flag it as a `world_state_candidate`. The sanitizer
(confirms every 5 turns) decides if it's still relevant and promotes it to world state.
This gives the resolved thread 0–5 turns for the sanitizer to evaluate. The resolved
thread needs a `resolved_turn` marker so the sanitizer knows how many turns it's been.

**`resolved_turn` marker specification:**
- Add `resolved_turn: int | None` to `ThreadResolution` in `state.py:161`
- Set `resolved_turn` in `turn_state.py:334-338` when a thread is resolved (already set on the ArcThread copy, but must also be on ThreadResolution)
- Pass `resolved_turn` to sanitizer's `completed_threads` context in `thread_sanitizer.py:146`
- Sanitizer uses `resolved_turn` to evaluate "0–5 turns after resolution" window

**`world_state_candidate` field specification:**
- Add `world_state_candidate: str | None` to `ThreadResolution` in `state.py:161`
- Set in storyteller extraction when the storyteller determines a resolved thread should
  feed into world state
- Collect candidates in a `world_state_candidates` list in state (new field)
- Pass to sanitizer for evaluation every 5 turns
- Sanitizer has full authority to promote, reject, consolidate, modify, or replace
- If rejected, the candidate is discarded (no partial promotion)
- If approved, the candidate text is used to create a new `WorldStateFact` with
  appropriate tier, valence, and expires_turn

**Sanitizer authority:** The sanitizer also has full authority to consolidate, remove,
update, or fold multiple world state facts into one. It is the ultimate authority on
world state.

### Auto-thread completion

**Remove if present.** Hard TTL on active threads (auto-resolve when progress entries
>= threshold) is a terrible idea. Threads should be resolved by the storyteller via
`thread_resolve`, not auto-completed by the engine. A TTL on resolved threads to move
them to archived is acceptable. See [Primitives](./01-primitives.md#ttl-strategy).

**Mechanical corrections:**
- Delete auto-completion block in `turn_state.py:161-182`
- Remove `thread_completion_threshold: int = 3` from `EngineConfig` in `config.py:184`

### arc_resolve — hard floor removed

The 8-turn minimum on `arc_resolve` frequency is removed as an enforcement mechanism.
It was derived from eval descriptive data (target cadence: 8–15 turns), not a design
constraint. A hard floor would delay legitimate arc resolutions (e.g., a goal achieved
on turn 5) and force either artificial narrative padding or premature goal changes. The
engine enforces no minimum. The 8–15 turn cadence remains a target, now achieved through
the tiered hint system rather than a hard gate. See [Primitives](./01-primitives.md#pressure-score-system).

**Mechanical corrections:**
- Update `turn_state.py:229` — change `if turns_since < 5` to `if turns_since < 8`
  (or remove the warning entirely, since pressure score hints replace hard gates)

### TTL filtering in prompts

Completed/abandoned threads surface in prompts for 3 turns after resolution, then are
removed from all prompt rendering. This applies to both `_arc.j2` and `narrate_user.j2`.

**Mechanical corrections:**
- `_arc.j2:21` — replace `current_arc.completed_threads[:15]` with TTL-filtered
  `completed_threads` from context builder (3-turn TTL)
- `_arc.j2:18-24` — remove `[:15]` hard cap, render all TTL-filtered threads
- `_arc.j2:12-16` — rename "Previously Resolved Arcs" to "Recently Resolved Arcs"
- Context builder in `prompts/context.py` — add TTL filtering for completed_threads
  (3-turn TTL), following the same pattern as `_get_resolved_arcs()` in narrate.py:139
- `narrate_user.j2:59-61` — remove "Past Resolutions" section entirely (it renders
  unfiltered completed threads, causing context bloat)

### Dead state

- **`urgency_set_turn`** — KEPT. Actively read and written in turn_state.py:140,153,595
  and seed.py:371-384. Used for urgency decay (stepwise demotion: urgent → normal →
  background). See [Primitives](./01-primitives.md#kept).
- **`promote_to_world_state`** — Replaced by two-step candidate system above. Delete.
  See [Primitives](./01-primitives.md#deletions).

## Open Questions

### Convergence Starvation (Pacing Engine — Out of Scope)

The pacing engine's convergence system has a critical gap: when all 5 convergence
components are 0, there's no mechanism to recover. Eval Cycle 2 showed T20-T22 in noir
with convergence score = 0 across all components (no urgent threads, no threat threads,
scene age = 0, no beat streak, no dice weight). The opportunist persona's stealth-heavy
play style starves convergence.

This is a **pacing engine problem**, not an arc system problem. The arc redesign doesn't
address it. Questions:
- Should convergence have a proactive injection mechanism (e.g., "if convergence has
  been <2 for N turns, inject a pressure beat")?
- Should the phase machine allow narrative-based transitions (e.g., "if the player has
  been in stealth for 5 turns, transition to a new phase based on narrative context,
  not just convergence score")?
- Should the ruling system be less generous with "routine" skips that starve dice_weight?

The convergence threshold was lowered from 3 to 2 in commit `eed5878` to help with
starvation, but it hasn't helped much. Previously, the problem may have been overly
passive NPCs (which are apparently doing better now) and NPCs not getting their
personalities correctly due to a misconfiguration. See bug ticket:
`roadmap/bugs/convergence-starvation.md`.

### Arc auto-resolve when all threads resolved/failed/abandoned

This case is unlikely in practice (arcs rarely reach zero threads). The pressure score
system handles the realistic cases. If it becomes a real failure mode in evals, revisit.
If it is implemented, it must require a minimum arc age guard (≥ 8 turns) to prevent
auto-resolve of a brand-new successor arc.

### Pack-level threshold tuning

Pressure score thresholds (both thread and arc tiers) are candidates for pack-level
configuration. Some genres naturally run shorter arcs (action, heist); others run longer
(political intrigue, survival). Deferred to a future pass after initial eval validation.
See [Primitives](./01-primitives.md#out-of-scope).

### Should thread urgency be graduated (more than 3 states)?

**Deferred.** Currently background/normal/urgent is too coarse. The pressure score
system's duration weight partially addresses this by making age matter, but the urgency
labels in prompts remain 3-state. Defer to a future design pass. See
[Primitives](./01-primitives.md#out-of-scope).

## Scope

This design coordinates with:
- **01-Primitives** — Shared building blocks that both arc system and seed worldbuilding
  redesigns depend on.
- **03-Seed Worldbuilding Redesign** — Contract alignment on `arc_origin`,
  `long_term_objective` rename, thread→world state promotion.
- **Dynamic Factions** (deferred) — Factions will feed into arc/thread generation.
- **Multiple arcs** (deferred) — Whether threads cleanly fit into multiple concurrent
  arcs.
