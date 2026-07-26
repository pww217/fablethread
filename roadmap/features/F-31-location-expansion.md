---
title: "Location expansion — seed-declared location threads, arrival flag, NPC location pinning"
status: up-next
urgency: 3
size: large
created: 2026-07-06
ticket_id: F-31
design: docs/design/location-expansion.md
labels:
  - engine
  - seed
  - narration
  - npc
  - threads
---

## Problem

Locations are an afterthought in seed generation. Each seed produces:
- One starting location as `state.location` (LocationRef: id/name/description)
- 4-5 key locations as `world.locations` (KeyLocation: id/name/description/status/tags)

The key locations exist as seed-declared world map data but are never shown to the narrator, never referenced by ruling, and serve no function beyond being seed-declared facts. Players have no incentive to visit them. Location changes only replace `state.location` — there's no memory of visited places, no exposition about what's interesting at a location, and no narrator guidance toward exploring.

Worse, arriving at a new location introduces no new narrative pressure — no threads emerge from the location itself. Location changes feel like set changes.

## Goals

1. **Seed-declared location threads:** Each key location gets `location_threads: list[SeedThread]` (0-2; id/summary/type/initial_urgency). Never urgent at seed. Type biased toward `opportunity` (other types allowed); locations tied to the long-term objective carry threads that flesh out, gate, or complicate it. This subsumes F-33 — opportunities and threads are one mechanism (threads were the intent; "opportunities" was a placeholder).

2. **Sync engine activation:** The delta builder activates a location's seed threads at location change — same code path as `turn_entered` (delta_builder.py:208-232). No LLM call, no async window. Activated threads are ordinary ArcThreads: no `scope` field, normal lifecycle, count toward `thread_max_active`. Eviction logic (currently inlined in turn_state.py's record `thread_add` path) is extracted to a shared helper and applied at activation.

3. **Arrival flag:** `location_arrived: bool` on `state.scene`, set on any location change (arrival detector, not first-visit — renamed from `first_visit_location` in design review). Signals the narrator to weave activated threads into narration naturally.

4. **Resolution-aware narrator context:** One "Location Context" section (~150 token aggregate cap, shared with F-32) showing the KeyLocation seed description (takes precedence over extractor-written LocationRef.description) + activated, unresolved threads. Resolved threads drop out — real state signal on revisit.

5. **NPC location pinning:** `last_seen_location` becomes the canonical anchor point after location changes — NPCs demoted to `nearby` with the pin when the PC moves; extractor overrides only when an NPC actually moves.

## Scope Decisions

- **Key locations = spatial boundary.** Sub-areas handled through description granularity, not separate location IDs.
- **No extraction schema changes.** Threads are ordinary ArcThreads after activation; Record handles them normally.
- **No convergence/ruling/directive filtering.** Activated threads behave like any thread. Note: the `threat_thread` convergence component is not urgency-gated — the opportunity-type bias is the arrival-shock guardrail.
- **No ruling prompt change** (F-32 owns the only ruling change).
- **No UI changes in this phase.**

## Design

Full design doc (status: reviewed): [docs/design/location-expansion.md](../design/location-expansion.md)

## Related Tickets

- [F-32: Scene inventory](../features/F-32-scene-inventory.md) — seed-declared location details/items (builds on this foundation; owns `scene_details` + ruling change)
- [F-33: Location threads](../features/F-33-location-threads.md) — **canceled: merged into this ticket** per design review
- [B-1: Location description overwritten by empty location_change delta](../bugs/B-1.md) — fixed, guard condition prevents empty deltas from overwriting seed data
