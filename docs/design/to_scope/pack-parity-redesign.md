# Pack Parity Redesign

> **Status:** scoping
> **Related designs:**
> - [Seed System Worldbuilding Redesign](./seed-worldbuilding-redesign.md) (deferred pack parity)
> - [World Creator Seed Pack](./world-creator-seed-pack.md) (deferred, placeholder)
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work.

## Problem Statement

Generated packs and default packs currently differ in their worldbuilding output.
This redesign aims to achieve parity between them.

## Open Questions

- What are the key differences between default pack and generated pack output?
- How does the world creator seed pack (step before seed generation) fit in?
- What's the minimum viable parity for this redesign?
- How does `pc_situation_schema` (seed worldbuilding redesign) interact with generated packs?
- How do dynamic factions (deferred, separate design) interact with generated packs?

## Scope

This design is separate from the seed worldbuilding redesign (Workstream 1) and
world state lifecycle (Workstream 2), but needs contract alignment with both.
