---
title: "Arc, thread, and seed generation refactor"
status: done
urgency: 1
size: large
created: 2026-06-23
labels:
  - Feature
  - Refactor
  - World Building
---

## Detail

Comprehensive refactor of the arc system, thread lifecycle, and seed generation pipeline. Three design docs are ready:

- [01-Primitives](../design/01-primitives.md) — Shared building blocks: field renames, deletions, TTL strategy, pressure score system, age tracking, pc.situation primitive
- [02-Arc System Redesign](../design/02-arc-system-redesign.md) — Arc lifecycle, thread management, pressure score, hints, thread→world state promotion
- [03-Seed Worldbuilding Redesign](../design/03-seed-worldbuilding-redesign.md) — Seed funnel, pc.situation, world state lifecycle, NPC roster

## Motivation

Eval data shows threads accumulate without resolution, arc resolution fires too frequently with no-op goal updates, and the system never closes narrative arcs. The current model needs a fundamental redesign.

## Scope

This refactor covers all three design docs in a single worktree/branch (`arc-thread-seed-gen-refactor`). It supersedes these existing roadmap items:
- `arcs-need-firmer-goals.md` (scoping)
- `threads-as-fact-sheet-objectives-multiple-arcs.md` (idea)
- `world-state-shows-bloat-not-active-constraints.md` (scoping)
- `opening-arc-improvement.md` (scoping)
- `choices-tied-to-arcs-threads.md` (scoping)

## Out of Scope

- Convergence starvation (pacing engine — separate bug ticket)
- Beat driver always "motivation" (NPC roster data — separate bug ticket)
- Thread resolution events ≠ unique threads (resolved by TTL filtering in this refactor)
- Dynamic factions (deferred)
- Multiple concurrent arcs (deferred)
- Thread urgency graduated states (deferred)
- External inventory (deferred)
- Pack parity (generated vs custom packs — deferred)
- Location tracking system (deferred)

## Design Reference

- [01-Primitives](../design/01-primitives.md)
- [02-Arc System Redesign](../design/02-arc-system-redesign.md)
- [03-Seed Worldbuilding Redesign](../design/03-seed-worldbuilding-redesign.md)
