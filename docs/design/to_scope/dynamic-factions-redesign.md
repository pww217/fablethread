# Dynamic Factions Redesign

> **Status:** scoping
> **Related designs:**
> - [Pack Validation](./pack-validation-design.md) — **depends on this.** Dynamic factions need to generate factions that conform to the same `Faction` schema as hardcoded factions. This design assumes pack-validation's single validation gate is already implemented — factions generated at seed time or pack time must pass the same `validate_pack()` gate as hardcoded factions.
> - [Pack Parity](./pack-parity-redesign.md) — **related.** Pack parity should ensure generated factions meet the same quality bar as default pack factions.
> - [World Creator Seed Pack](./world-creator-seed-pack.md) — **related.** User-authored packs should support both hardcoded and dynamically generated factions via the same schema.
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work. Write the plan only after [Pack Validation](./pack-validation-design.md) is implemented.

## Problem Statement

Factions are currently hardcoded in `scenario.yaml` (via `factions: list[Faction]`)
and injected into the narrate prompt, storytell prompt, and game state. This approach
is rigid and doesn't allow for dynamic faction generation.

Pack validation already enforces faction ID uniqueness and structural correctness via
`validate_pack()`. This design focuses on **how factions get generated** — seed-time LLM
call, pack authoring, or runtime — and how they flow into the prompt pipeline and game
state, while conforming to the same schema as hardcoded factions.

## Proposed Direction

Factions will be generated dynamically instead of hardcoded. Minimum ~4 factions:
1 friendly, 1 hostile, 2 neutral. Requires a more complete factions system.

Generated factions must conform to the same `Faction` schema as hardcoded factions and
pass the same `validate_pack()` gate. This is enforced by the single validation gate
from pack-validation — no separate validation path for dynamic factions.

## Open Questions

- How are factions generated (seed-time LLM call, pack authoring, or runtime)?
- How do factions flow into the narrate prompt (current behavior)?
- How do factions flow into the storytell prompt (current behavior)?
- How are factions stored in `state.world.factions` (current behavior)?
- What's the minimum viable factions system for this redesign?
- How do factions interact with the arc system (deferred, not yet written)?
- Should generated factions be baked into the pack at seed time, or generated fresh each game?

## Scope

This design assumes [Pack Validation](./pack-validation-design.md) is already implemented.
It needs contract alignment with seed worldbuilding redesign and world state lifecycle,
but should focus on generation mechanics and prompt integration rather than schema
validation (which pack-validation handles via the single validation gate).
