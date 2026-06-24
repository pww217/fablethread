---
title: "Ruling Engine GM Beat Authority & Pre-Turn Pipeline"
status: scoping
urgency: 3
size: medium
created: 2026-06-24
labels:
  - architecture
  - engine
  - pacing
  - design-question
---
## Problem

Architecture questions about ruling engine authority and pipeline structure:

1. **Should ruling engine set `gm_beat`?** — Currently world tick pipeline handles GM beats. If ruling engine owns this, we could eliminate the world tick extra pipeline step.
2. **Two pre-turn pipelines?** — One async pipeline running between turns (for GM beats, NPC proactive actions, world simulation) vs. the current synchronous turn pipeline.

## Context

- Ruling engine currently outputs rulings but doesn't directly drive GM beat selection
- World tick runs as separate pipeline phase between turns
- Proactive NPC agency design (`proactive-npc-agency-gm-beats-redesign.md` in features) suggests GM beats should be more intentional

## Trade-offs

**Ruling engine owns gm_beat:**
- Pro: Single source of truth for "what happens next" (ruling + beat)
- Pro: Eliminates world tick pipeline duplication
- Con: Ruling engine gets more complex; mixes judgment + pacing

**Two pre-turn pipelines (async + sync):**
- Pro: Clear separation — async for world sim/NPC agency, sync for player turn resolution
- Pro: Async can run while player reads/thinks
- Con: More complex orchestration; state synchronization concerns

## Suggested Next Step

Design review needed. Spike: prototype ruling-engine-driven gm_beat in isolation to assess complexity. Compare against async pre-turn pipeline approach.