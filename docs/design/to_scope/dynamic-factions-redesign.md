# Dynamic Factions Redesign

> **Status:** reviewed
> **Related designs:**
> - [Pack Validation](../complete/tooling-infra/pack-validation-design.md) — **implemented.** Generated factions conform to the same `Faction` schema as hardcoded factions and pass the same `validate_pack()` gate. Dependency satisfied.
> - [Pack Parity](../complete/tooling-infra/pack-parity-redesign.md) — generated factions should meet the same quality bar as default pack factions.
> - [World Creator Seed Pack](./world-creator-seed-pack.md) — user-authored packs support both hardcoded and dynamically generated factions via the same schema.
> - [Location Expansion](../location-expansion.md) — `faction_presence` is part of the unified KeyLocation schema defined there; faction names render in its Location Context section.
> - [Scene Inventory](./scene-inventory.md) — faction-owned items in `scene_details` (glue point, below).
>
> **Note:** No roadmap ticket exists for this work yet — create one when this design is picked up.
>
> **Design review decisions incorporated:**
> 1. Factions are generated **at seed time**, in the same seed pass as key locations, so faction IDs can cross-reference in both directions.
> 2. `faction_presence: list[str]` (0-2 faction IDs) on `KeyLocation`. The seed generator chooses wisely: a faction's home base → exactly 1 (the owner); a contested location → 2 (the rivals); minor/wilderness locations → 0-1.
> 3. Factions **persist across arcs** — they are world facts, not arc-scoped state. (Contrast: location threads follow normal thread lifecycle with no special arc handling.)
> 4. Faction opinion-of-PC, faction-vs-faction state, and record/world-step reasoning are **deferred**. Factions in this design are generated entities with presence, not simulated actors.

## Problem Statement

Factions are currently hardcoded in `scenario.yaml` (via `factions: list[Faction]`,
pack.py) and flow into the narrate context each turn (`world_factions` in narrate.py)
and `state.world.factions` (stored as `list[dict[str, str]]`, not Faction models).
This approach is rigid and doesn't allow for dynamic faction generation. Note: the
pack schema caps factions at 6 (`max_length=6`) — the ~4 minimum below is compatible,
but generated packs must respect the cap. `validate_pack()` already checks faction ID
uniqueness; the `faction_presence` cross-reference check below is new.

## Target State

### Generation

- **When:** Seed time, in the same seed pass that generates key locations. Faction generation must be ordered so that `faction_presence` IDs on KeyLocation resolve against the generated faction list (funnel ordering — see Seed Worldbuilding Redesign).
- **Composition:** Minimum ~4 factions: 1 friendly, 1 hostile, 2 neutral.
- **Schema:** Generated factions conform to the existing `Faction` schema — same as hardcoded factions. No separate dynamic-faction schema.
- **Validation:** Single gate: `validate_pack()` (pack-validation, implemented). No separate validation path. One new check: every `faction_presence` ID on every KeyLocation must exist in the faction list.

### Faction Presence on Locations

Part of the unified KeyLocation schema defined in the Location Expansion design:

```python
faction_presence: list[str] = Field(default_factory=list, max_length=2)  # faction IDs
```

Seed prompt guidance:
- A faction's home base → exactly 1 faction present (the owner)
- A contested location → 2 factions (the rivals)
- Minor/wilderness locations → 0-1
- Presence should be coherent with each faction's nature (a raider gang doesn't share a hospital with the settler council without a reason)

**Prompt rendering:** Faction names for the current location's presence render as one line in F-31's Location Context section, within its ~150 token aggregate cap. Current location only.

### Glue with the Location Expansion

- **NPC pinning (F-31):** Faction NPCs get a natural anchor — pinned via `last_seen_location` at their faction's locations when the PC moves away.
- **Scene inventory (F-32):** `scene_details` items may be faction-owned (per seed prompt phrasing, e.g., "raider supply cache"). The PC taking one is extracted as a normal `inventory_add` + taken-item tracking; Record can naturally escalate the theft into faction-relevant thread content. No new mechanics.
- **Location threads (F-31):** Seed prompt may generate location threads with faction stakes (e.g., an opportunity thread "mediator wanted between the two crews at the depot" at a contested location). Threads reference factions by name in summaries; no structural link required.

### Lifecycle

Factions persist across arc boundaries unchanged. They are world facts. If a future arc design wants faction shifts at arc resolution, that belongs to the arc design, not this one.

### Open Questions

Resolved by design review:
- ~~How are factions generated (seed-time, pack authoring, runtime)?~~ → Seed time, same pass as key locations.
- ~~Do generated factions conform to the Faction schema?~~ → Yes, validated by the single `validate_pack()` gate.
- ~~How do factions interact with locations?~~ → `faction_presence` (0-2 IDs), presence rules above.

Remaining:
- How deep should faction reasoning go (opinion of PC, faction-vs-faction state, record/world tracking)? **Deferred** — out of scope for this design.
- Storytell prompt flow: current behavior (factions injected) continues unchanged; revisit if faction reasoning is ever added.

### Deferred Items

- **Faction opinion/state mechanics:** reputation, faction-vs-faction relations, record/world-step reasoning about factions
- **Runtime faction generation:** all factions seed-declared in this design
- **Arc-system interaction:** factions persist across arcs; any arc-coupled faction shifts belong to a future arc design
- **Faction NPC rosters:** named faction members generated at seed time (currently NPCs emerge via extraction)

## Scope

This design covers generation mechanics (seed time), schema conformance (existing
`Faction` + single validation gate), and location integration (`faction_presence`).
It deliberately stops short of faction simulation. Write the implementation plan only
when this design is picked up; pack-validation, its former blocker, is already
implemented.
