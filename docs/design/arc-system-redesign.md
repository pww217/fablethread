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
- **`visible_goal` → `long_term_objective`** — "Long-term" signals update frequency and
  duration to the LLM. "Objective" is less likely to trigger immediate-completion behavior
  than "goal." This follows the same principle as `progress → major_updates`: field names
  are prompts, and the name must signal when *not* to update.
- **`goal_context` → `arc_origin`** — `goal_context` is UI-only noise. `arc_origin`
  (2–3 sentences, past tense, "how did the PC end up here?") replaces it. Placement:
  UI (sidebar tooltip) and seed opening narration only. NOT in narrate/storytell prompts.
  Each arc gets its own `arc_origin` at creation time (seed or successor arc).

### chapter_end

**Firm decision: removed.** It was added as a patch for arc_resolve misuse (Jun 18). It has no
behavioral effect — just stamps `last_chapter_end_turn` in meta. It adds cognitive load
by existing in the same JSON object as `arc_resolve`, making it feel like an option
rather than a signal. If arc_resolve is decoupled (see below), chapter_end has no
purpose.

### Thread type stability

**Stable by default.** Type (threat/opportunity/complication/revelation) should rarely
change. The storyteller and sanitizer can change it, but they must provide a `reason`
field explaining why. Not every threat that's neutralized becomes an opportunity — it
needs a good narrative reason.

### Dormant thread TTL and archival

**Dormancy at 8 turns, archival at 13 turns.** Auto-dormant threshold moves from 4 to
8 turns (configurable). When a thread has been dormant for 5 more turns (13 total),
the sanitizer marks it for archival. Once archived, it's permanently archived.

**Completed/abandoned thread archival.** Completed and abandoned threads are kept in
`state.yaml` forever for auditability. They are surfaced in prompts for 3 turns after
resolution (as "Recently Resolved Threads"), then removed from all prompt rendering.
No hard cap on the number in data — TTL filtering ensures bounded prompt load. The
`[:15]` hard cap in `_arc.j2` is removed.

"Past Resolutions" in `narrate_user.j2` is removed — it renders unfiltered completed
threads, causing context bloat. The TTL-filtered "Recently Resolved Threads" section
in `_arc.j2` replaces it.

Abandoned threads are included in the 3-turn TTL alongside resolved threads. If they
turn out to distract the narrator by forcing recall of forgotten threads, they can be
filtered to resolved-only in a future pass.

**Thread archival resurfacing.** Dormant threads approaching archival do NOT get a
resurfacing hint. LLMs are bad at ignoring things. The TTL system handles cleanup
without requiring proactive resurfacing.

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

### major_update_signal (was progress_kind)

The `major_updates` field on each thread entry includes a `major_update_signal` field.
Values are reduced to two: `advancement` and `setback`. `shift` is removed entirely.
Rationale: the only information the engine needs is whether the thread moved forward or
backward. `shift` described dimensional change, not directional progress, and had no
distinguishing value from a low-signal `advancement`. If nothing significant happened,
no `major_updates` entry should be emitted — the field name already enforces this.

### arc_resolve — hard floor removed

The 8-turn minimum on `arc_resolve` frequency is removed as an enforcement mechanism.
It was derived from eval descriptive data (target cadence: 8–15 turns), not a design
constraint. A hard floor would delay legitimate arc resolutions (e.g., a goal achieved
on turn 5) and force either artificial narrative padding or premature goal changes. The
engine enforces no minimum. The 8–15 turn cadence remains a target, now achieved through
the tiered hint system rather than a hard gate.

### Pressure Score System

The engine computes a `pressure_score` per thread and per arc at render time. It is never
persisted to state and never visible in any LLM prompt until it crosses a hint threshold.
When it crosses a threshold, only the resulting hint tag is injected — not the score itself.

**Two inputs:**

**Duration weight** (same structure for threads and arcs):

| Age (turns active) | Cumulative duration weight added |
|---|---|
| 1–4 | 0 |
| 5–7 | +1 |
| 8–10 | +3 (cumulative: 4) |
| 11–13 | +6 (cumulative: 10) |
| 14+ | +10 (cumulative: 20) |

**Progress signal:**
- Threads: each `advancement` entry in `major_updates` → +1; each `setback` → −1 (floor: 0). Turns with no update are neutral.
- Arcs: each thread resolved under this arc → +2. Threads abandoned or archived → +0. Turn count is covered by duration weight; resolved thread count is the only progress signal.

*Pressure score = duration weight + progress signal.*

*Hint tiers:*

| Tier | Thread threshold | Arc threshold | Signal injected |
|---|---|---|---|
| None | < 4 | < 5 | Nothing |
| Soft hint | 4–6 | 5–8 | "Consider resolving" |
| Strong hint | 7–9 | 9–12 | "This should be reaching conclusion" |
| Imperative | ≥ 10 | ≥ 13 | "Wrap up — failure is a valid resolution" |

Thresholds are initial tuning values. They will be validated against eval data and may be
made configurable at the pack level in a future pass.

*Hint delivery:* When a thread crosses a tier threshold, the hint is injected into both
the narrator prompt and the storyteller prompt on the same turn. The narrator acts first
(writes toward the signaled conclusion); the storyteller receives the narrator's output
plus the same hint and is told to respond to what the narrator played out. This is a
coordinated nudge, not a hard resolve — the LLM retains narrative judgment about how
closure happens.

For arcs, the same tiers apply with the arc thresholds above. Hint language for arcs
should refer to the arc's `long_term_objective` and explicitly note that both success and
failure are valid resolutions.

*Implementation note:* The hint computation should live in a shared preprocessing helper
(e.g., `engine/hints.py`) — pure functions, state in, hint context out, no side effects.
Both the narrator path (`narrate.py`) and the storyteller path (`extraction/storytell.py`)
currently build their arc context independently with no shared builder. The hints helper
is the right shared injection point for both thread and arc hints without adding a new
dependency between those two paths.

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

**Settled.** `major_update_signal` has two values: `advancement` and `setback`. `shift`
is removed. See [Discovery](../discovery/arc-system-problems.md#12-thread-progress-kinds-vague-classifications).

### `visible_goal` rename

**Settled.** Renamed to `long_term_objective`. See Decisions above.

### Arc auto-resolve when all threads resolved/failed/abandoned

This case is unlikely in practice (arcs rarely reach zero threads). The pressure score
system handles the realistic cases. If it becomes a real failure mode in evals, revisit.
If it is implemented, it must require a minimum arc age guard (≥ 8 turns) to prevent
auto-resolve of a brand-new successor arc.

### Pack-level threshold tuning

Pressure score thresholds (both thread and arc tiers) are candidates for pack-level
configuration. Some genres naturally run shorter arcs (action, heist); others run longer
(political intrigue, survival). Deferred to a future pass after initial eval validation.

### Arc age tracking

**Settled.** Add both `created_turn` and `started_turn` to CampaignArc. `created_turn`
is when the arc object is instantiated in the engine (usually during seed/worldbuilding
phase). `started_turn` is when the narrator first renders the arc in prompts (usually
turn 1, or later if the arc is seeded but not surfaced immediately). Both are needed
for the pressure score system's duration weight calculation. If they end up the same
value, that's fine — they diverge only if an arc is created but not immediately surfaced.

### Completed threads TTL

**Settled.** Completed and abandoned threads are kept in `state.yaml` forever for
auditability. They are surfaced in prompts for 3 turns after resolution (as "Recently
Resolved Threads"), then removed from all prompt rendering. No hard cap on the number
in data — TTL filtering ensures bounded prompt load. The `[:15]` hard cap in `_arc.j2`
is removed. "Past Resolutions" in `narrate_user.j2` is removed (unfiltered, causes bloat).

### Thread archival resurfacing

**Settled.** No. Dormant threads approaching archival do NOT get a resurfacing hint.
LLMs are bad at ignoring things. The TTL system handles cleanup without requiring
proactive resurfacing.

### How does `pc.situation` (seed worldbuilding redesign) interact with arcs?

Deferred to primitives document. `pc.situation` is a primitive that arcs depend on,
but the specific interaction design is scoped to the primitives document.

### How does `arc_origin` interact with the new arc model?

**Settled.** UI-only + seed opening narration. Does NOT feed into narrate/storytell
prompts. If early-turn prompt context is needed, that's a future consideration (first
N turns).

### How does the new arc system interact with the world state lifecycle (Workstream 2)?

Thread → world state: two-step system (storyteller flags, sanitizer confirms). See
Decisions above.

Arc → world state: **out of scope for this redesign.** When an arc resolves, its
narrative weight does not directly feed into world state. This may be designed in a
future pass.

### Should thread urgency be graduated (more than 3 states)?

**Deferred.** Currently background/normal/urgent is too coarse. The pressure score
system's duration weight partially addresses this by making age matter, but the urgency
labels in prompts remain 3-state. Defer to a future design pass.

## Scope

This design coordinates with:
- **Primitives Document** (deferred, to be written) — Shared building blocks that both
  arc system and seed worldbuilding redesigns depend on.
- **Seed System Worldbuilding Redesign** (Workstream 1: seed worldbuilding, Workstream 2:
  world state lifecycle) — contract alignment on `arc_origin`, `long_term_objective` rename,
  thread→world state promotion.
- **Dynamic Factions** (deferred) — factions will feed into arc/thread generation.
- **Multiple arcs** (deferred) — whether threads cleanly fit into multiple concurrent
  arcs.
