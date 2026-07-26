# Location Threads Design

> **Status:** merged — superseded by [Location Expansion Design](../location-expansion.md)
> **Related tickets:**
> - [F-33: Location threads](../../../roadmap/features/F-33-location-threads.md) — work now tracked under F-31
> - [F-31: Location expansion](../../../roadmap/features/F-31-location-expansion.md) — canonical design

This document is retained for history. Location threads were merged into the Location
Expansion design during design review. The canonical design lives in
[`docs/design/location-expansion.md`](../location-expansion.md).

## Decisions made at merge (design review)

The original draft proposed re-introducing a `scope` field on ArcThread and activating
threads in the async World-step window. Review reversed both:

1. **No `scope` field.** The unify-threads simplification stands. Activated location
   threads are ordinary ArcThreads: they affect convergence, ruling, and directive
   exactly like campaign threads, count toward the active thread cap (5), and follow
   the normal lifecycle with no special arc-boundary handling. If Record escalates one
   to urgent, it pushes pacing — intended behavior. The pacing guardrail is that seed
   never declares urgent location threads (background/normal only), so escalation
   always takes turns.
2. **Sync, engine-driven activation.** Activation is a pure state mutation keyed off a
   location change the delta builder already detects — there is no LLM call to defer.
   It    happens in the delta builder at location change, in the same code path as
   `location_arrived` (formerly named `first_visit_location` — renamed in review
   because it detects every arrival, not first visits). The async World-step window was rejected: it bought nothing
   and cost a one-turn delay plus event plumbing.
3. **One hook mechanism.** The earlier `location_opportunities` concept (F-31) was a
   placeholder for location threads; opportunities are retired and threads are the
   single seed-declared per-location narrative hook. As a side benefit, resolved
   threads drop out of narrator context, giving real state signal on revisit instead
   of narrator self-correction.
4. **Arrival sequencing.** Because activation is sync in the apply phase, the
   narrator sees the new location and its activated threads together on the first turn
   at the location — no two-turn rollout.

## Original problem statement (preserved)

The `unify-threads` plan removed thread scope entirely — all threads became global
campaign threads. That eliminated location-specific narrative pressure: arriving at a
new location introduced no new threads, making location changes feel like set changes
with no new story content. This problem is now addressed by the merged design.
