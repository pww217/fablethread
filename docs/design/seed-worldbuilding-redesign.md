# Seed System Worldbuilding Redesign

> **Status:** scoping
> **Related designs:**
> - [Dynamic Factions](./dynamic-factions-redesign.md) (deferred, needs separate design)
> - [Pack Parity](./pack-parity-redesign.md) (deferred, placeholder)
> - [World Creator Seed Pack](./world-creator-seed-pack.md) (deferred, placeholder)
> - [Arc System Redesign](./arc-system-redesign.md) (deferred, not yet written)
>
> **Note on placeholders:** The four designs above are placeholders. They mark areas
> that need separate design work before implementation. They are not implementation
> plans — just signposts for follow-up work.

## Problem Statement

The current seed system reaches turn 0 with a populated `state.yaml`, but the world it
establishes is too shallow to feel real. World facts are injected as flat strings with no
proximity to the player. The PC's situational context — what they own, who they owe,
whether they have a ship — is either absent or buried in free-form bio prose. Arcs have
goals but no backstory. The result is a game that cannot answer basic questions before
the first turn begins, and a world state that grows without bound and degrades in quality
over time.

This document covers two interrelated workstreams:

- **Seed worldbuilding redesign** — producing a richer, more grounded turn 0
- **World state lifecycle** — making world state mutable, tiered, and self-maintaining

**Scope note:** These are two separate design documents (seed worldbuilding + world state
lifecycle), coordinated with the Arc System Redesign (deferred, not yet written).
Implementation will need contract alignment across all three.

***

## Design Principles

**The funnel.** Generation moves from most global to most specific. World facts are
established before regional context. Regional context is established before the PC's
situation. The PC's situation is established before bio and inventory are generated.
Every later stage is a distillation of every earlier stage — nothing at the individual
level should contradict what was set globally.

**Vagueness over prescription.** The seed system runs at high temperature. Its job is to
inject randomness with genre coherence, not to constrain the LLM into a predetermined
story. Fields that describe *what kinds of things to generate* are preferable to fields
that name specific content. The archetypes and pool system handle specificity; the schema
handles shape.

**Pack-specificity for situational facts.** Different genres have fundamentally different
axes of player concern. A pack author knows what a player would want on their character
sheet before sitting down. Those questions — not implementation details, not plot hooks —
are what `pc_situation_schema` defines.

> **Needs expansion:** The current design for `pc_situation_schema` needs more thought
> and better authoring guidance. Follow-up work includes pack parity (default packs vs
> generated packs) and the world creator seed pack (step before seed generation).

**No dead facts.** World state entries the player cannot conceivably encounter in a
session are noise. Everything established at seed time should be either (a) global and
always relevant, (b) local and near the player's current operating radius, or (c) a named
thing the player can seek out.

**Sanitizer as custodian.** World state currently only grows. The thread sanitizer is the
right system to maintain it — it already has full arc and thread context, runs on a
cadence, and reasons about narrative relevance. Extending it to world state is a natural
expansion of its existing role.

**Clean break.** This redesign does not maintain backward compatibility with existing
save files or pack schemas. Old saves are invalid under the new schema. No migration
shims, no coercion validators, no deprecation stubs. Dead fields are deleted everywhere —
schema, prompts, pack files, engine code. If it was replaced, it is gone.

***

## Workstream 1: Seed Worldbuilding

### Generation Order (The Funnel)

Each stage receives all outputs from prior stages as context. The prompt is structured to
enforce this ordering. The existing generation order block in `generate_seed_system.j2`
is rewritten to be unconditional and to cover the new fields below.

```
1. WORLD FACTS — global tier
   Immutable or slow-changing backdrop. True everywhere, affects everyone.
   Examples: ongoing war, economic conditions, a faction's collapse.
   Count: 1–2. Valence: mixed (not all threats).

2. WORLD FACTS — local tier
   True in the area the PC currently operates. More likely to decay.
   Examples: curfew in effect, patrols increased, market fair in town.
   Count: 1–2. Valence: mixed.

3. KEY LOCATIONS (→ world.locations)
   4–5 named places that exist in the world at game start.
   Ordered from most accessible to least known.
   Status: accessible | restricted | unknown_location | rumored
   Includes 1–2 breadcrumb locations that give the PC a reason to move.
   Geographic and institutional variety required — do not cluster around
   a single obvious theme.
   Note: Status values are metadata only (no gameplay effect).
   Defer to future location overhaul for narrator integration.

4. PC SITUATION (→ pc.situation)
   What the player would want to know before sitting down.
   Pack-specific schema defines which axes to populate.
   Generated after world context so it reflects that context.
   This is the "entry vector" — genre-specific context answering
   "who am I, what do I have, where am I, who are the people around me."
   **Important:** pc.situation is updatable during gameplay. If the PC's
    vessel is destroyed, home is burned down, or crew is lost, these facts
    should be reflected in state. See decisions below.
    Full pc.situation feeds seed prompt and early turns; stripped-down
    version (persist: true fields) surfaces in ongoing narrate prompts.

5. NPC BONDS + COMPENDIUM
   Drawn from npc_bonds pool. Grounded in pc_situation where applicable
   (crewmates if vessel exists; settlement contacts if home_base exists).

6. ARC
    `long_term_objective` (renamed from `visible_goal`, see Arc System Redesign), arc_origin (replaces goal_context).
    Threads generated after arc.
    Note: Arc system redesign is deferred (not yet written).
    arc_origin and long_term_objective are placeholders until arc redesign is complete.

7. PC BIO + INVENTORY
   Last step. Bio distills global context + situation + stats into a person.
   Stats inform bio: high strength → physical survival history; high charisma →
   negotiation or social leverage background. The link need not be direct
   occupation but some connection should exist.
   The opening narration generated at seed time must establish pc.situation
   in enough detail that both the player and the narrator can treat it as
   ground truth — vessel name and condition, home port, crew, whatever the
   pack's situation schema produced. This is the only place pc.situation is
   surfaced narratively; it does not feed into the narrate system prompt.
```

***

### New Field: `pc.situation`

> **Needs expansion:** This section needs more thought and better authoring guidance.
> Follow-up work includes pack parity (default packs vs generated packs) and the world
> creator seed pack (step before seed generation).

`pc.situation` is added to the PC block as `dict[str, Any]`, keyed by the pack's
`pc_situation_schema`. It is a peer of `bio`, `tagline`, and `stats` in `_default_state()`.

The schema is defined in `scenario.yaml` by the pack author. It declares which
situational axes matter for this genre. The LLM receives these as structured slots to
populate — not open-ended prose. The schema describes *what to ask*, not *what to answer*.

**Authoring constraint: 3–5 keys maximum.** Each key should answer a question the player
would reasonably ask before the game begins — not plot hooks, not obligations, not
backstory. Situational facts only: what do they have, where is it, what condition is it
in, who are they to the people around them. These establish the facts of the universe
as they pertain to the player, before anything is set in motion.

All keys are `required: false` — the LLM may determine the PC has no vessel, no home
port, no crew. It must state that explicitly rather than invent something false.

**Updatable during gameplay.** pc.situation should be updatable when circumstances change:
- Vessel destroyed or stolen → update vessel field
- Home port burned down → update home_port field
- Crew lost or gained → update crew field

This is important for continuity at turn 15 and turn 25. The narrator needs to know
where the PC's home is, whether they have a vehicle, what their situation looks like
now — not just what it was at turn 0.

**Relationship to external inventory.** pc.situation is related to the idea of "external
inventory" — things that belong to the PC but aren't on their person (ship, home, base
of operations). This needs more fleshing out and may warrant a separate field or
extension of pc.situation.

**Placement in prompts.** pc.situation is surfaced in prompts in a tiered fashion:

- **Seed prompt + first 2-3 turns:** Full pc.situation is fed to the seed prompt and
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

This tiered approach avoids context bloat while ensuring ongoing situational awareness.

Example — golden-piracy:

```yaml
pc_situation_schema:
  # Does the PC have a vessel, and what is its status?
  # Answer: name, condition (seaworthy/damaged/impounded), PC's role aboard
  # (captain/crew/passenger), and current location. If no vessel, state that
  # explicitly — do not invent one.
  - key: vessel
    label: Ship
    required: false

  # Does the PC have a port or settlement they consider home or safe harbor?
  # Answer: name and the PC's standing there (welcome/tolerated/wanted).
  - key: home_port
    label: Home Port
    required: false

  # Who else is in the PC's immediate crew or working group, if any?
  # Answer: 1–3 names and roles. These should align with npc_bonds pool selections.
  # Do not list more than 3. If the PC is a lone operator, state that.
  - key: crew
    label: Crew
    max_items: 3
    required: false
```

Example — zombie survival:

```yaml
pc_situation_schema:
  # What settlement, if any, does the PC call home?
  # Answer: name, rough size, and current resource status (stable/strained/critical).
  - key: home_settlement
    label: Home Settlement
    required: false

  # Who does the PC know is alive? Who do they know is dead or missing?
  # Answer: 2–4 names with status. These seed NPC bonds and may generate dormant threads.
  - key: known_survivors
    label: Known Survivors
    max_items: 4
    required: false

  # What is the PC's mode of transport, if any?
  # Answer: type, condition, fuel/resource status.
  - key: transport
    label: Transport
    required: false
```

***

### New Field: `arc.arc_origin`

> **Arc system redesign deferred.** The arc system is being redesigned separately
> (see [Arc System Redesign](./arc-system-redesign.md), not yet written).
> `arc_origin` and `long_term_objective` are placeholders until that redesign is complete.

`goal_context` is removed entirely — from `CampaignArc`, `_default_state()`,
`StorytellerResult`, the sanitizer schema, `turn_state.py`, `audit.py`, all eval
checkers, all Jinja2 templates, and the PC UI panel. No backward compatibility.

**`arc.arc_origin: str`** — 2–3 sentences, past tense. How did the PC end up here? What
happened that made this goal personal? This replaces `goal_context`.

**Placement:** `arc_origin` goes in the UI (sidebar tooltip, replacing goal_context's
current placement) and in the seed opening narration. It does NOT go into the narrate
system prompt or the storyteller prompt. It is UI-only.

**Lifecycle:** Each arc gets its own `arc_origin` at creation time (seed or successor
arc). When a new arc replaces the old one (arc resolution), the new arc gets a new
`arc_origin`. The old one is not carried forward.

**Design decisions (from Arc System Redesign):**
- UI only + seed opening narration. NOT in narrate/storytell prompts.
- If early-turn prompt context is needed, that's a future consideration (first N turns).
- The opening narration should establish arc_origin in a way the narrator can use for
  continuity.

***

### Key Locations → `world.locations`

> **Metadata only.** Status values are for the player's reference, not the narrator's
> guidance. Defer to future location overhaul for narrator integration.

`world.locations` already exists in `_default_state()` and is currently always empty.
The seed populates it with 4–5 entries at game start. No new top-level field needed —
the seed generator writes directly to `world.locations`.

```python
class KeyLocation(BaseModel):
    id: str
    name: str
    description: str
    # 1–2 sentences. What is this place and why does it matter?
    status: Literal["accessible", "restricted", "unknown_location", "rumored"]
    # accessible: PC can go here now
    # restricted: known but gated by faction, cost, or social access
    # unknown_location: known to exist, whereabouts unclear
    # rumored: existence itself is unconfirmed
    tags: list[str]
```

`unknown_location` and `rumored` entries give the PC a reason to investigate without
materializing the place fully. The narrator treats seed-established locations as
canonical. Runtime location growth is deferred to a future location overhaul.

***

### Fields Deleted from `scenario.yaml` and All Pack Files

Removed from schema definitions, all default pack YAML files, all prompt templates that
reference them, and all engine code that reads them. No stubs, no deprecation comments.

| Field | Reason |
|---|---|
| `inspiration.pc` | Replaced by archetype pools + funnel ordering |
| `inspiration.npcs` | Enumerates specific NPC types by name, overrides pool randomness |
| `inspiration.inventory` | Inventory is last-stage; prompt handles genre defaults |
| `world_facts` (static list) | Replaced by `permanent: true, tier: global` seed-generated facts |
| `forbid_cliches` | Active enforcement in seed.py; removed per design intent |
| `pc_stat_range` | Engine does not consume post-seed |
| `pc_stat_total_range` | Engine does not consume post-seed |
| `goal_context` (all locations) | Replaced by `arc_origin` |

### Fields Deferred (Needs Separate Design)

| Field | Reason |
|---|---|
| `factions` | Needs separate design for dynamic factions (see [Dynamic Factions](./dynamic-factions-redesign.md)). Factions will still plumb into narrate prompt, storytell, and game state, but generated dynamically (minimum ~4: 1 friendly, 1 hostile, 2 neutral). |

***

## Workstream 2: World State Lifecycle

> **Separate design document.** This workstream is a separate design document from
> seed worldbuilding (Workstream 1), coordinated with the Arc System Redesign (deferred).

### Current State (To Be Replaced)

`WorldStateFact` has three fields: `id`, `text`, `tier: Literal["permanent", "persistent"]`.
World state is append-only. `persistent` means only "not permanent." The sanitizer does
not touch world state. Nothing removes or consolidates facts.

The entire `WorldStateFact` model is replaced. All code that branches on `"permanent"`
or `"persistent"` is rewritten.

### New `WorldStateFact` Schema

```python
class WorldStateFact(BaseModel):
    id: str
    text: str
    tier: Literal["global", "local"]
    # global: affects the whole world or a large region; slow-changing
    #   Examples: faction at war, city burned by raiders, economic boom
    # local: near the PC's current operating area; more likely to decay
    #   Examples: curfew in effect, patrols increased, market fair in town
    permanent: bool = False
    # True signals to the sanitizer that this fact is foundational genre
    # canon established at seed time. The bar for removal is high — only
    # retire if something in the arc or recent events unambiguously supersedes
    # it. Permanent facts should not have expires_turn set.
    valence: Literal["threat", "complication", "neutral", "boon"] = "neutral"
    # threat: active danger or pressure on the PC or world
    # complication: friction without immediate danger
    # neutral: world texture with no clear charge
    # boon: an advantage, opportunity, or favorable condition
    expires_turn: int | None = None
    # Absolute turn number at which the engine hard-deletes this fact.
    # For time-bounded facts set at seed time or by the storyteller:
    # curfews, fairs, temporary events. Facts without expires_turn do not
    # expire via TTL — only the sanitizer can retire them.
    # Do not set on permanent facts.
```

**Seed-time valence requirement:** The seed prompt must produce at least one `neutral` or
`boon` fact across the combined global + local world state. Left without instruction the
LLM defaults to threats and complications.

**Rendering in prompts:** Both `_world_state.j2` and `storytell_user.j2` render tier and
valence as paired badges: `[global/threat]`, `[local/boon]`, etc. This gives the
storyteller the signal it needs to self-correct toward balance without additional
instruction.

### Thread/Arc → World State Promotion

When a thread resolves or an arc resolves, it should be able to feed into world state
as a persistent fact. Example: "the hospital was destroyed → medication shortage
settlement-wide." This is continuity — the narrator can reference it later when
relevant events occur.

**Two-step system (from Arc System Redesign decisions):**
1. **Storyteller flags** — When resolving a thread or arc, the storyteller can emit a
   `world_state_candidate` field with the proposed fact.
2. **Sanitizer confirms** — The sanitizer (every 5 turns) evaluates the candidate. It
   has 0–5 turns after resolution to decide if the fact is still relevant. The resolved
   thread needs a `resolved_turn` marker so the sanitizer knows the timing.

The sanitizer has full authority to:
- Promote the candidate to world state
- Reject the candidate
- Consolidate it with existing world state facts
- Modify the text

This two-step process prevents trivial additions (the same problem progress had) while
allowing meaningful narrative consequences to persist.

### TTL Expiry (Engine-Handled)

At the start of each turn, before any LLM call, the turn pipeline iterates `world_state`
and hard-deletes any fact where `current_turn >= expires_turn`. No LLM involved. No
archive. The fact remains visible in `events.jsonl` at the turn it was added, which is
sufficient for eval audit purposes.

### Sanitizer World State Authority

The sanitizer is extended to maintain world state on the same cadence as thread
sanitization (`config.sanitize_every`). It receives the full `world_state` list as
additional context and returns a complete replacement `world_state` array. The engine
swaps the old array for the new one atomically — no per-ID surgical operations.

This mirrors how the sanitizer already handles threads: the LLM rewrites the full
structure in one pass rather than emitting a diff. It is simpler to prompt, simpler to
apply, and eliminates ID mismatch bugs.

The sanitizer may update, consolidate, or remove facts in this rewrite. Facts with
`permanent: true` require a meaningfully higher bar for removal — the prompt instructs
the sanitizer to treat them as foundational and remove them only when something in the
arc or recent events unambiguously supersedes them.

All removals are hard deletes. No archive list in state. `events.jsonl` is the record.

**Extended sanitizer output schema (additions only):**

```json
{
  "world_state": [
    {
      "id": "fact_id",
      "text": "current or revised text",
      "tier": "global | local",
      "permanent": false,
      "valence": "threat | complication | neutral | boon",
      "expires_turn": null
    }
  ]
}
```

The returned array is the complete replacement. Any fact not present in the returned
array is considered removed.

***

## Implementation Order

1. **Clearing pass.** Delete all removed fields from schema, all default pack YAML files,
    all engine code, and all prompt templates that reference them.
2. **`WorldStateFact` replacement.** New schema, rewrite all code branching on old tier
    values. Update `_world_state.j2` and `storytell_user.j2` to render `[tier/valence]`
    badges.
3. **TTL expiry.** Add hard-delete pass to the turn pipeline start.
4. **Sanitizer extension.** Add `world_state` input and full replacement array output to
    the sanitizer schema and prompt. Add two-step world state candidate system
    (storyteller flags → sanitizer confirms).
5. **Seed prompt rewrite.** Funnel ordering, new field generation, deleted fields removed.
6. **`arc_origin`.** Add to `CampaignArc` and `_default_state()`. Remove `goal_context`
    from all callsites simultaneously.
    > **Note:** Arc system redesign is deferred (not yet written). `arc_origin` and
    > `long_term_objective` are placeholders until that redesign is complete.
7. **`pc.situation`.** Add to `_default_state()` and `SeedPC`. Add
    `pc_situation_schema` to `ScenarioBrief`. Update seed prompt.
    > **Note:** This section needs expansion and better authoring guidance.
    > pc.situation should be updatable during gameplay.
8. **Pack update.** Update golden-piracy: add `pc_situation_schema`, remove all deleted
    fields, expand `scene_detail_bundles`, audit archetype pools.
    > **Note:** Pack parity (default packs vs generated packs) is deferred (see
    > [Pack Parity](./pack-parity-redesign.md)).

### NPC Roster Limit

Current limit is 10 NPCs in `_build_npc_roster()` (prompt_context.py:25-53). Bumping to **12** (user preference). If context issues arise, can move to 15 later.

### Skeptical Items (Question These)

**Null beat rate 34-57%.** All beats have a two-turn TTL, and a 30-50% null rate gives the narration room to breathe. Less than 50% null is acceptable. No checker needed to enforce a threshold.

**NPC dialogue not tracked.** The NPC model has no dialogue or speech_history field. User preference: not needed. Personality fields (including speech) and previous turn outcomes should be sufficient to drive consistent NPC behavior.

### Dependencies on Arc System Redesign

The following items in this document depend on decisions from the [Arc System Redesign](./arc-system-redesign.md):

- **`arc_origin` placement** — UI-only + opening narration (decided in arc redesign)
- **`visible_goal` rename** — settled: renamed to `long_term_objective`
- **Thread → world state promotion** — two-step system (decided in arc redesign)
- **`pc.situation` updatable** — needs engine support for updating situational facts
  during gameplay (scoped to primitives document)
- **External inventory** — related to pc.situation, needs separate design (deferred)
- **Arc → world state** — out of scope for this redesign. When an arc resolves, its
  narrative weight does not directly feed into world state.

> **Execution order:** Primitives first, then arc system redesign, then seed worldbuilding
> redesign. The primitives document captures all shared building blocks that both designs
> depend on. Arc system runs before seed worldbuilding because `arc_origin` and
> `long_term_objective` are defined in the arc redesign, and thread→world state promotion
> is an arc system decision.

### Dependencies on Other Designs

- **Primitives Document** (deferred, to be written) — Shared building blocks that both
  arc system and seed worldbuilding redesigns depend on. Includes `pc.situation` primitive
  definition, TTL strategy, field renames/deletions.
- **Dynamic Factions** — factions will feed into arc/thread generation and world state
- **Pack Parity** — pc_situation_schema needs parity between generated and custom packs
- **World Creator Seed Pack** — authoring guidance for pc_situation_schema

***

## Non-Goals

- **Pack parity.** Generated and custom packs are deferred. This redesign targets default
  packs only. (See [Pack Parity](./pack-parity-redesign.md) for placeholder.)
- **Location tracking system.** `world.locations` is a worldbuilding reference list, not
  a movement or state-change system. No visit history, no unlocking mechanics, no map UI.
  Runtime location growth is a future overhaul.
- **Stat generation.** Stats remain outside seed generation. Bio may reference stats as
  context; the pipeline does not produce or validate stat values.
- **Phased `goal_context` removal.** It is removed in full as part of step 6. There is
  no transitional period where both `goal_context` and `arc_origin` coexist.
- **Dynamic factions.** Factions will be redesigned separately (see
  [Dynamic Factions](./dynamic-factions-redesign.md)). This redesign does not include
  factions in its scope.
- **World creator seed pack.** The step before seed generation (for users who want to
  make their own packs) needs separate design work (see
  [World Creator Seed Pack](./world-creator-seed-pack.md)).
- **Multiple arcs.** Whether threads cleanly fit into multiple concurrent arcs (1–3) is
  deferred. See [Arc System Redesign](./arc-system-redesign.md#decisions).

***

## Deferred Design Documents (Placeholders)

These are placeholders for follow-up work. They are not implementation plans — just
signposts for areas that need separate design before implementation.

### [Dynamic Factions](./dynamic-factions-redesign.md)
Factions will be generated dynamically (minimum ~4: 1 friendly, 1 hostile, 2 neutral)
instead of hardcoded in scenario.yaml. They will still plumb into the narrate prompt,
storytell, and game state. Requires a more complete factions system.

### [Pack Parity](./pack-parity-redesign.md)
Ensure generated packs and default packs have parity in their worldbuilding output.
Requires work on the world creator seed pack (step before seed generation).

### [World Creator Seed Pack](./world-creator-seed-pack.md)
The step before seed generation — for users who want to make their own packs. Needs
significant design work.

### [Arc System Redesign](./arc-system-redesign.md)
The arc system is being redesigned separately. `arc_origin` and `long_term_objective` in this
design are placeholders until that redesign is complete. This document coordinates with
the arc system redesign for contract alignment.

Key coordination points:
- `arc_origin` replaces `goal_context` (UI-only + opening narration)
- `long_term_objective` replaces `visible_goal` (see arc redesign decisions)
- Thread → world state promotion uses two-step system (storyteller flags, sanitizer confirms)
- `pc.situation` is updatable during gameplay (needs engine support, scoped to primitives)
- Multiple arcs deferred (see arc redesign decisions)
- Arc → world state: out of scope for this redesign

### [Primitives Document](../design/primitives.md) (deferred, to be written)
Shared building blocks that both arc system and seed worldbuilding redesigns depend on.
Includes `pc.situation` primitive definition, TTL strategy, field renames/deletions,
pressure score system, age tracking. This document should be written last, after all
design decisions in the other docs are settled, to capture the canonical definitions.
