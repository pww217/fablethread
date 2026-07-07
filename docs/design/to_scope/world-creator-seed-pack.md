# World Creator Seed Pack Redesign

> **Status:** scoping
> **Related designs:**
> - [Pack Validation](./pack-validation-design.md) — **depends on this.** User-authored packs need the same validation as auto-generated ones via the single `validate_pack()` gate. This design assumes pack-validation's validation gate is already implemented — user-authored packs should pass the same structural checks as default and generated packs.
> - [Pack Parity](./pack-parity-redesign.md) — **depends on this.** User-authored packs should play identically to default and generated packs. Pack parity should treat user-authored packs as first-class citizens, not edge cases.
> - [Dynamic Factions](./dynamic-factions-redesign.md) — **related.** User-authored packs should support both hardcoded and dynamically generated factions via the same schema.
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work. Write the plan only after [Pack Validation](./pack-validation-design.md) is implemented.

## Problem Statement

The step before seed generation — for users who want to make their own packs — needs
significant design work. This is the "world creator seed pack" step.

Pack validation already enforces that all packs (default, generated, user-authored) pass
the same `validate_pack()` gate. This design focuses on **how users create packs** — the
authoring UX, the scaffolding, the guidance — while ensuring user-authored packs conform
to the same schema as default and generated packs via the single validation gate.

## Open Questions

- What is the current flow for users who want to create their own packs?
- How does the world creator seed pack interact with the seed generation pipeline?
- What's the minimum viable world creator system?
- How does this interact with `pc_situation_schema` (seed worldbuilding redesign)?
- How does this interact with dynamic factions (deferred, separate design)?
- How does this interact with pack parity (deferred, placeholder)?
- Should user-authored packs be validated at authoring time or at load time?

## Scope

This design assumes [Pack Validation](./pack-validation-design.md) is already implemented.
It needs contract alignment with seed worldbuilding redesign and world state lifecycle,
but should focus on the authoring UX and scaffolding rather than schema validation
(which pack-validation handles via the single validation gate).
