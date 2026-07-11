---
title: "Location threads — dormant seed-declared threads that activate on location arrival"
status: idea
urgency: 4
size: large
created: 2026-07-06
ticket_id: F-33
design: docs/design/location-threads.md
labels:
  - engine
  - seed
  - threads
  - pacing
---

## Problem

The `unify-threads` plan removed thread scope entirely — all threads are now global campaign threads that persist across location changes and arc boundaries. This was the right decision for campaign-level threads, but it eliminated the possibility of location-specific narrative threads that could make locations feel alive and worth visiting.

Currently, seed generates 1-2 active threads + up to 3 dormant threads (4-5 total). All threads are campaign-level. When the player arrives at a new location, there's no mechanism for that location to introduce new narrative pressure or context. The location's seed description and details provide exposition, but no thread-level narrative engagement.

This makes location changes feel like set changes — the narrator describes the new place, but no new narrative threads emerge from the location itself. The player has less incentive to explore because locations don't offer new story content beyond visual description.

## Goals

1. **Seed-declared dormant location threads:** Each key location's seed data includes dormant threads that are specific to that location. These threads are seed-declared, not LLM-generated at runtime. They represent narrative hooks that should activate when the player arrives at the location.

2. **Thread activation on location arrival:** When the player arrives at a location for the first time, seed-declared dormant threads for that location should activate (become non-dormant). This should happen via the world step (async, end-of-turn), not during the turn's main pipeline.

3. **Narrator exposition for thread activation:** When threads activate on location arrival, the narrator should generate prose that introduces the thread's narrative content as environmental details or events. This should feel organic — not "a thread activated" but "the narrator describes the thread's content as part of the location's atmosphere."

4. **Thread lifecycle integration:** Activated location threads should follow the same lifecycle as other threads (urgency decay, dormancy, resolution). They should NOT affect ruling/dice/phase directly — they should start as background/normal urgency and only escalate if Record promotes them. This prevents location threads from disrupting pacing.

## Design

Full design doc: [docs/design/location-threads.md](../design/location-threads.md)

## Deferred Until After F-31

This ticket should NOT be started until F-31 (location expansion via seed-declared opportunities) is implemented and proven effective. The seed-declared opportunities alone should make locations feel interesting and worth visiting. If location threads are still desired after F-31 proves the foundation works, this ticket can be picked up as a separate enhancement.

The main blocker for location threads is re-introducing thread scope, which undoes the unify-threads simplification. This should only be done if seed-declared opportunities alone don't provide enough incentive for location exploration.

## Related Tickets

- [F-31: Location expansion](../features/F-31-location-expansion.md) — seed-declared location details as strings, first-visit flag, narrator exposition (prerequisite — location threads build on location foundation; should be proven effective first)
- [F-32: Scene inventory](../features/F-32-scene-inventory.md) — seed-declared location items as strings (independent, both build on location expansion foundation)
- [unify-threads plan](../../plans/completed/thread/unify-threads.md) — removed thread scope, unified all threads (this ticket reverses scope removal for location threads only)
