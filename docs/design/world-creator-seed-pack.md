# World Creator Seed Pack Redesign

> **Status:** scoping
> **Related designs:**
> - [Seed System Worldbuilding Redesign](./seed-worldbuilding-redesign.md) (deferred world creator)
> - [Pack Parity](./pack-parity-redesign.md) (deferred, placeholder)
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work.

## Problem Statement

The step before seed generation — for users who want to make their own packs — needs
significant design work. This is the "world creator seed pack" step.

## Open Questions

- What is the current flow for users who want to create their own packs?
- How does the world creator seed pack interact with the seed generation pipeline?
- What's the minimum viable world creator system?
- How does this interact with `pc_situation_schema` (seed worldbuilding redesign)?
- How does this interact with dynamic factions (deferred, separate design)?
- How does this interact with pack parity (deferred, placeholder)?

## Scope

This design is separate from the seed worldbuilding redesign (Workstream 1) and
world state lifecycle (Workstream 2), but needs contract alignment with both.
