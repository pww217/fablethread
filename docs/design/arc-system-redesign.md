# Arc System Redesign

> **Status:** scoping
> **Related designs:**
> - [Seed System Worldbuilding Redesign](./seed-worldbuilding-redesign.md) (deferred arc redesign)
>
> **Note:** This is a placeholder. Not an implementation plan — just a signpost for
> follow-up work.

## Problem Statement

The arc system (CampaignArc, ArcThread, arc resolution, arc lifecycle) is being
redesigned separately. This document will coordinate with the seed worldbuilding
redesign for contract alignment.

## Open Questions

- What are the key changes to the arc system?
- How does `arc_origin` (seed worldbuilding redesign) fit into the new arc model?
- How does `visible_goal` (seed worldbuilding redesign) fit into the new arc model?
- How does arc resolution work in the new system?
- How do threads interact with arcs in the new system?
- How does the sanitizer interact with the new arc system?
- How does the new arc system interact with the seed worldbuilding redesign?
- How does the new arc system interact with the world state lifecycle (Workstream 2)?

## Scope

This design is separate from the seed worldbuilding redesign (Workstream 1) and
world state lifecycle (Workstream 2), but needs contract alignment with both.
