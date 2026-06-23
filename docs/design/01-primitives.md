# Primitives Document

> **Status:** scoping
> **Related designs:**
> - [02-Arc System Redesign](./02-arc-system-redesign.md)
> - [03-Seed Worldbuilding Redesign](./03-seed-worldbuilding-redesign.md)
>
> **Discovery/evidence:** [Arc System — Discovery](../discovery/arc-system-problems.md)

This document captures all shared building blocks that both the arc system redesign
and the seed worldbuilding redesign depend on. It is the canonical reference for:
- Field renames and deletions
- TTL strategy
- Pressure score system
- Age tracking
- `pc.situation` primitive definition
- Execution order

Both other design docs reference this document, not each other, for shared concepts.
This eliminates circular dependencies and ensures a single source of truth.

## Execution Order

**Primitives → Arc System → Seed Worldbuilding.**

The primitives document defines shared building blocks. The arc system redesign defines
`arc_origin`, `long_term_objective`, and thread→world state promotion. The seed
worldbuilding redesign depends on those definitions.

This order ensures that when the arc system plan is written, all shared primitives are
already defined. When the seed worldbuilding plan is written, both primitives and arc
system are already defined.

## Field Renames and Deletions

### Renames

| Old Field | New Field | Scope | Rationale |
|-----------|-----------|-------|-----------|
| `progress` | `major_updates` | ArcThread model, prompts, packs | "Major" signals "only when something worth noting happens." Not a running play-by-play. |
| `visible_goal` | `long_term_objective` | CampaignArc model, prompts, packs | "Long-term" signals update frequency and duration. "Objective" avoids immediate-completion trigger. |
| `goal_context` | `arc_origin` | CampaignArc model, prompts, packs, UI | "How did the PC end up here?" Past tense, 2–3 sentences. UI-only + seed opening narration. |
| `progress_kind` | `major_update_signal` | ProgressEntry in ArcThread | "Signal" is more descriptive. Values: `advancement` / `setback` only. |

### Deletions

| Field | Scope | Reason |
|-------|-------|--------|
| `chapter_end` | CampaignArc, prompts, packs, engine | No behavioral effect. Added as patch for arc_resolve misuse. Adds cognitive load. |
| `urgency_set_turn` | ArcThread model | Dead state. Never read or written. |
| `promote_to_world_state` | ThreadResolution model | Dead state. Never read by engine. Replaced by two-step candidate system. |
| `goal_context` (all references) | CampaignArc, _default_state(), StorytellerResult, sanitizer schema, turn_state.py, audit.py, eval checkers, Jinja2 templates, PC UI panel | Replaced by `arc_origin`. No backward compatibility. |

### `major_update_signal` Values

Two values only: `advancement` and `setback`. `shift` is removed entirely.

Rationale: the only information the engine needs is whether the thread moved forward or
backward. `shift` described dimensional change, not directional progress, and had no
distinguishing value from a low-signal `advancement`. If nothing significant happened,
no `major_updates` entry should be emitted — the field name already enforces this.

## Age Tracking

### CampaignArc: `created_turn` and `started_turn`

Both fields are added to CampaignArc. They track different moments in the arc's lifecycle.

- **`created_turn`** — When the arc object is instantiated in the engine (usually during
  seed/worldbuilding phase, before the game starts narrating). This is the "birth" of
  the arc in the data model.
- **`started_turn`** — When the narrator first renders the arc in prompts (usually turn
  1, or later if the arc is seeded but not surfaced immediately). This is when the arc
  becomes "active" in gameplay.

Both are needed for the pressure score system's duration weight calculation. If they end
up the same value, that's fine — they diverge only if an arc is created but not
immediately surfaced.

## TTL Strategy

### Completed/Abandoned Threads

- **Data retention:** Kept in `state.yaml` forever for auditability. No TTL on data.
- **Prompt rendering:** Surfaces in prompts for 3 turns after resolution (as "Recently
  Resolved Threads"), then removed from all prompt rendering.
- **Hard cap:** Removed. The `[:15]` hard cap in `_arc.j2` is deleted. TTL filtering
  ensures bounded prompt load, so unbounded growth in data is acceptable.
- **Abandoned threads:** Included in the 3-turn TTL alongside resolved threads. If they
  turn out to distract the narrator by forcing recall of forgotten threads, they can be
  filtered to resolved-only in a future pass.
- **"Past Resolutions" in narrate_user.j2:** Removed. It renders unfiltered completed
  threads, causing context bloat. The TTL-filtered "Recently Resolved Threads" section
  in `_arc.j2` replaces it.

### Dormant Threads

- **Auto-dormant threshold:** 8 turns (configurable). Moved from 4 turns.
- **Archival TTL:** 13 turns (8 dormant + 5 more). When a thread has been dormant for
  5 more turns, the sanitizer marks it for archival.
- **Archival resurfacing:** No. Dormant threads approaching archival do NOT get a
  resurfacing hint. LLMs are bad at ignoring things. The TTL system handles cleanup
  without requiring proactive resurfacing.

### Resolved Arcs

- **Prompt rendering:** TTL-filtered in prompts (3 turns). Already implemented in
  `_get_resolved_arcs()` in narrate.py. No change needed.

### NPC Archival

Existing pattern, no change:
- **Nearby decay:** 2 turns before nearby → known auto-decay.
- **Departed archive:** 3 turns as "departed" before → archived.
- **Archived NPCs:** Excluded from roster, kept in compendium. No TTL on data.

## Pressure Score System

The engine computes a `pressure_score` per thread and per arc at render time. It is never
persisted to state and never visible in any LLM prompt until it crosses a hint threshold.
When it crosses a threshold, only the resulting hint tag is injected — not the score
itself.

### Two Inputs

**Duration weight** (same structure for threads and arcs):

| Age (turns active) | Cumulative duration weight added |
|---|---|
| 1–4 | 0 |
| 5–7 | +1 |
| 8–10 | +3 (cumulative: 4) |
| 11–13 | +6 (cumulative: 10) |
| 14+ | +10 (cumulative: 20) |

**Progress signal:**
- Threads: each `advancement` entry in `major_updates` → +1; each `setback` → −1
  (floor: 0). Turns with no update are neutral.
- Arcs: each thread resolved under this arc → +2. Threads abandoned or archived → +0.
  Turn count is covered by duration weight; resolved thread count is the only progress
  signal.

*Pressure score = duration weight + progress signal.*

### Hint Tiers

| Tier | Thread threshold | Arc threshold | Signal injected |
|---|---|---|---|
| None | < 4 | < 5 | Nothing |
| Soft hint | 4–6 | 5–8 | "Consider resolving" |
| Strong hint | 7–9 | 9–12 | "This should be reaching conclusion" |
| Imperative | ≥ 10 | ≥ 13 | "Wrap up — failure is a valid resolution" |

Thresholds are initial tuning values. They will be validated against eval data and may be
made configurable at the pack level in a future pass.

### Hint Delivery

When a thread crosses a tier threshold, the hint is injected into both the narrator
prompt and the storyteller prompt on the same turn. The narrator acts first (writes
toward the signaled conclusion); the storyteller receives the narrator's output plus
the same hint and is told to respond to what the narrator played out. This is a
coordinated nudge, not a hard resolve — the LLM retains narrative judgment about how
closure happens.

For arcs, the same tiers apply with the arc thresholds above. Hint language for arcs
should refer to the arc's `long_term_objective` and explicitly note that both success
and failure are valid resolutions.

### Implementation

The hint computation should live in a shared preprocessing helper (e.g.,
`engine/hints.py`) — pure functions, state in, hint context out, no side effects.
Both the narrator path (`narrate.py`) and the storyteller path (`extraction/storytell.py`)
currently build their arc context independently with no shared builder. The hints helper
is the right shared injection point for both thread and arc hints without adding a new
dependency between those two paths.

## `pc.situation` Primitive

### What It Is

`pc.situation` is a `dict[str, Any]` keyed by the pack's `pc_situation_schema`. It is a
peer of `bio`, `tagline`, and `stats` in `_default_state()`.

The schema is defined in `scenario.yaml` by the pack author. It declares which
situational axes matter for this genre. The LLM receives these as structured slots to
populate — not open-ended prose. The schema describes *what to ask*, not *what to answer*.

### Authoring Constraint

**3–5 keys maximum.** Each key should answer a question the player would reasonably ask
before the game begins — not plot hooks, not obligations, not backstory. Situational
facts only: what do they have, where is it, what condition is it in, who are they to
the people around them.

All keys are `required: false` — the LLM may determine the PC has no vessel, no home
port, no crew. It must state that explicitly rather than invent something false.

### Updatable During Gameplay

pc.situation should be updatable when circumstances change:
- Vessel destroyed or stolen → update vessel field
- Home port burned down → update home_port field
- Crew lost or gained → update crew field

This is important for continuity at turn 15 and turn 25. The narrator needs to know
where the PC's home is, whether they have a vehicle, what their situation looks like
now — not just what it was at turn 0.

### Tiered Surfacing in Prompts

- **Seed prompt + first 2–3 turns:** Full pc.situation is fed to the seed prompt and
  early narration. This establishes the PC's baseline canon (home settlement, family,
  vehicle, crew, etc.) and may generate NPCs, inventory items, or other persistent
  state.
- **Ongoing turns:** A stripped-down version surfaces in narrate prompts (and possibly
  storytell/ruling). Only fields marked with `persist: true` (or equivalent) are
  included. Items that generated their own persistent entities (NPCs, inventory)
  don't need ongoing surfacing — those entities carry their own context.

Example: "home settlement" persists (the PC still has a home). "Crew member X" doesn't
need surfacing — if that crew member matters, they exist as an NPC in the compendium.
But "vessel condition: damaged" might persist if the vessel itself is a persistent entity.

### Relationship to External Inventory

pc.situation is related to the idea of "external inventory" — things that belong to the
PC but aren't on their person (ship, home, base of operations). This needs more
fleshing out and may warrant a separate field or extension of pc.situation. Deferred.

## Out of Scope

These items are explicitly scoped to other designs or deferred to future passes. They
are not addressed in this primitives document.

- **Arc → world state** — When an arc resolves, its narrative weight does not directly
  feed into world state. Deferred to a future pass.
- **Multiple arcs** — Whether threads cleanly fit into multiple concurrent arcs (1–3)
  is deferred.
- **Thread urgency graduated states** — Currently background/normal/urgent is too coarse.
  Deferred to a future design pass.
- **External inventory** — Related to pc.situation, needs separate design. Deferred.
- **Convergence starvation** — Pacing engine problem, not arc system problem. Out of
  scope. See bug ticket: `roadmap/bugs/convergence-starvation.md`.
- **Pack-level threshold tuning** — Pressure score thresholds may be configurable at
  the pack level in a future pass. Deferred.
