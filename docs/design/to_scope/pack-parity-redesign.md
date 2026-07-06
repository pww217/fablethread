# Pack Parity Redesign

> **Status:** scoping
> **Related designs:**
> - [Pack Validation](./pack-validation-design.md) — **depends on this.** Pack parity requires a single validation gate that both YAML authoring and LLM generation paths must pass. This design assumes pack-validation is already implemented.
> - [Dynamic Factions](./dynamic-factions-redesign.md) — **related.** Dynamic factions need to generate factions that conform to the same schema as hardcoded factions. Pack parity should ensure generated factions meet the same quality bar as default pack factions.
> - [World Creator Seed Pack](./world-creator-seed-pack.md) — **related.** User-authored packs need the same parity as auto-generated ones. Both should pass the same validation gate.
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work. Write the plan only after [Pack Validation](./pack-validation-design.md) is implemented.

## Problem Statement

Generated packs and default packs should play identically at runtime. Both paths must
pass the same `validate_pack()` gate (from pack-validation), but parity goes further:
content quality should be equivalent — generated pools should be as rich as hand-authored
ones, factions should be as well-defined, and the overall seed should feel as crafted.

Pack validation enforces structural correctness by construction. Pack parity enforces
content quality — ensuring the LLM produces packs that don't just conform to the schema
but actually play as well as default packs.

## Open Questions

- What content quality gaps exist between default pack and generated pack output?
- How should we measure "parity" — via eval rubric, via manual comparison, or both?
- What's the minimum viable parity for this redesign?
- How does `pc_situation_schema` vary between packs, and should generated packs match default pack schemas?
- How do dynamic factions interact with generated packs — should they generate factions at seed time or pack time?

## Scope

This design assumes [Pack Validation](./pack-validation-design.md) is already implemented.
It needs contract alignment with seed worldbuilding redesign and world state lifecycle,
but should focus on content quality rather than structural correctness (which validation
handles).
