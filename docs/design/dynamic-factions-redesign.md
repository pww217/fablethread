# Dynamic Factions Redesign

> **Status:** scoping
> **Related designs:**
> - [Seed System Worldbuilding Redesign](./seed-worldbuilding-redesign.md) (deferred factions)
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work.

## Problem Statement

Factions are currently hardcoded in `scenario.yaml` (via `factions: list[Faction]`)
and injected into the narrate prompt, storytell prompt, and game state. This approach
is rigid and doesn't allow for dynamic faction generation.

## Proposed Direction

Factions will be generated dynamically instead of hardcoded. Minimum ~4 factions:
1 friendly, 1 hostile, 2 neutral. Requires a more complete factions system.

## Open Questions

- How are factions generated (seed-time LLM call, pack authoring, or runtime)?
- How do factions flow into the narrate prompt (current behavior)?
- How do factions flow into the storytell prompt (current behavior)?
- How are factions stored in `state.world.factions` (current behavior)?
- What's the minimum viable factions system for this redesign?
- How do factions interact with the arc system (deferred, not yet written)?

## Scope

This design is separate from the seed worldbuilding redesign (Workstream 1) and
world state lifecycle (Workstream 2), but needs contract alignment with both.
