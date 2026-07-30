---
title: "Location threads — merged into F-31"
status: canceled
urgency: 4
size: large
created: 2026-07-06
ticket_id: F-33
design: docs/design/location-expansion.md
labels:
  - engine
  - seed
  - threads
  - pacing
---

## Status: CANCELED — merged into F-31

Merged into [F-31: Location expansion](../features/F-31-location-expansion.md) during design review (2026-07-26). The canonical design is [docs/design/location-expansion.md](../design/location-expansion.md); the original draft survives as a merge record at `docs/design/to_scope/location-threads.md`.

### Decisions made at merge

1. **One hook mechanism.** Location threads are the single seed-declared per-location hook. F-31's earlier "opportunities" concept was a placeholder for threads and is retired.
2. **No `scope` field on ArcThread.** The unify-threads simplification stands — this ticket originally proposed reversing it, and review rejected that. Activated location threads are ordinary threads: normal convergence/ruling/directive treatment, normal lifecycle, no arc-boundary drop rule.
3. **Sync engine activation, not async.** This ticket proposed activation in the async World-step window. Review moved it to the delta builder at location change (same code path as `location_arrived`) — activation is a pure state mutation with no LLM call to defer.
4. **Never urgent at seed.** Location threads start background/normal; escalation happens via Record's normal mechanics. The `threat_thread` convergence component is not urgency-gated, so the opportunity-type bias is the arrival-shock guardrail.

## Original problem statement (preserved)

The `unify-threads` plan removed thread scope entirely — all threads became global campaign threads. That eliminated location-specific narrative pressure: arriving at a new location introduced no new threads, making location changes feel like set changes with no new story content. **This problem is now addressed by F-31.**

## Related Tickets

- [F-31: Location expansion](../features/F-31-location-expansion.md) — canonical ticket; implements everything here
- [F-32: Scene inventory](../features/F-32-scene-inventory.md) — seed-declared location items (independent, builds on F-31)
- [unify-threads plan](../../plans/completed/thread/unify-threads.md) — removed thread scope; preserved (this ticket's scope-revival proposal was rejected)
