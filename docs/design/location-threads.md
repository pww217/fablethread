# Location Threads Design

> **Status:** scoping
> **Related tickets:**
> - [F-33: Location threads](../../roadmap/features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival
> - [F-31: Location expansion](../../roadmap/features/F-31-location-expansion.md) — seed-declared location details as strings (prerequisite foundation)
> - [F-32: Scene inventory](../../roadmap/features/F-32-scene-inventory.md) — seed-declared location items as strings (independent)

## Problem

The `unify-threads` plan removed thread scope entirely — all threads are now global campaign threads that persist across location changes and arc boundaries. This was the right decision for campaign-level threads, but it eliminated the possibility of location-specific narrative threads that could make locations feel alive and worth visiting.

Currently, seed generates 1-2 active threads + up to 3 dormant threads (4-5 total). All threads are campaign-level. When the player arrives at a new location, there's no mechanism for that location to introduce new narrative pressure or context. The location's seed description and details provide exposition, but no thread-level narrative engagement.

This makes location changes feel like set changes — the narrator describes the new place, but no new narrative threads emerge from the location itself. The player has less incentive to explore because locations don't offer new story content beyond visual description.

## Design Principles

**Seed-declared only.** All location threads are seed-declared. No runtime thread generation at locations. No LLM-generated location threads at runtime. This keeps seed dimensionality manageable and avoids extraction complexity.

**Minimal scope re-introduction.** Re-introduce `scope` as a single Literal field with only two values: `"campaign"` and `"location"`. Don't over-engineer — location threads are a narrow use case.

**No pacing disruption.** Location threads should NOT directly affect ruling, convergence, or directive at background/normal urgency. They should only escalate if Record promotes them. This prevents location threads from disrupting pacing.

**Deferred until proven necessary.** This design should NOT be implemented until F-31 (location expansion via seed-declared details) is proven effective. The seed-declared details alone should make locations feel interesting and worth visiting. If location threads are still desired after F-31 proves the foundation works, this design can be picked up as a separate enhancement.

## Target State

### Model Changes

**ArcThread:** Re-introduce `scope` field:
```python
scope: Literal["campaign", "location"] = "campaign"
```

Only two values: campaign (existing behavior) and location (new). Location threads have different lifecycle rules:
- Location threads start dormant
- Location threads activate on location arrival (set `dormant: False`)
- Location threads do NOT affect ruling (ruling only sees urgent campaign threads)
- Location threads do NOT affect convergence (convergence only counts campaign threads)
- Location threads CAN be resolved by Record like any other thread
- Location threads should be dropped at arc boundary (cleaner, less state complexity)

**KeyLocation:** Add seed-declared location threads:
```python
class SeedThread(BaseModel):
    id: str
    summary: str
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    initial_urgency: Literal["background", "normal"] = "background"
    # Note: location threads should NOT start as urgent
```

Seed threads are simpler than full `ArcThread` — they don't need progress entries, resolution state, or turn tracking at seed time. These are populated by Record at runtime.

### Thread Activation Mechanism

**When:** End-of-turn async window (same window as World step). This keeps activation out of the main turn pipeline and avoids delaying the player's turn.

**How:** World step (or a new async sub-step) checks if the player's current location has seed-declared location threads that haven't been activated yet. If so, activates them:
- Set `dormant: False` on matching threads
- Set `urgency` to seed-declared initial_urgency (background or normal, never urgent)
- Set `added_turn` to current turn
- Set `last_updated_turn` to current turn
- Log activation for event recording

**Why async:** Activation should not block the turn. The player's turn completes normally, and location thread activation happens in the async window. The next turn's state will reflect the activated threads.

### Narrator Integration

When location threads activate, the narrator should introduce them as part of the location's atmosphere. This should be guided by:
- World step records which threads activated (in event data)
- Next turn's narrator prompt includes thread activation context
- Narrator guidance: introduce thread content as environmental details, not as mechanical events

Example: A location thread with type="revelation" and summary="decrypted radio signals point to survivor camp" should be narrated as "The radio crackles with fragmented transmissions — someone out there is moving, and the signal direction suggests a camp to the east."

### Collision Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Seed generation** | One new field on seed output | Seed already generates location data; additive |
| **ArcThread model** | Re-introduces `scope` field | One Literal field, two values only |
| **World step (async)** | Thread activation logic | End-of-turn async window, doesn't block turn |
| **Ruling** | Filters location threads out | Only shows urgent campaign threads |
| **Convergence** | Filters location threads out | Only counts campaign threads |
| **Directive** | No change | Only driven by campaign threads |
| **Arc resolution** | Drops location threads | Clean boundary; Record can promote if needed |
| **Thread cap** | Location threads don't count | Separate pool |

### Interaction with Pacing

**Convergence:** Location threads should NOT directly affect convergence score. Convergence should only count campaign threads (urgent_thread component, threat_thread component, threat_density component). This prevents location threads from forcing phase transitions the player didn't initiate.

**Directive:** Location threads should NOT affect narration directive. Directive should only be driven by campaign thread urgency and scene age.

**Thread urgency escalation:** Location threads that start as background/normal CAN escalate via Record's normal urgency decay/escalation mechanics. If Record promotes a location thread to urgent, it should then affect convergence and directive like any other urgent thread. This allows location threads to naturally grow into campaign-level pressure if the story warrants it.

**Scene age:** Location thread activation does NOT reset scene age. Scene age should only reset on location change (existing behavior). Thread activation is a state change within the location, not a location change itself.

### Thread Dedup and Lifecycle

**Dedup:** Location threads should be deduplicated against existing campaign threads. If a location thread's summary is ≥70% similar to an existing thread, don't activate it (Record should handle dedup via normal progress dedup if the thread is later promoted).

**Arc boundary:** When arc resolves, location threads should be dropped (not carried forward as campaign threads). This keeps location threads tied to their location's narrative context. If a location thread's content should survive arc boundary, Record should promote it to a campaign thread via thread_update before arc resolution.

**Cap:** Location threads don't count against the active thread cap (5 threads). They're a separate pool. This prevents location threads from displacing campaign threads.

### Seed Generation

Seed prompt should generate location threads for key locations:
- 0-2 location threads per location (not every location needs threads)
- Threads should be appropriate to the location's purpose and the world's theme
- Threads should NOT duplicate seed-declared campaign threads
- Threads should start as background or normal urgency (never urgent)
- Thread type should be varied (not all threats, not all opportunities)

### Implementation Phases

**Phase 1: Model changes**
- Add `scope` field back to `ArcThread` (Literal["campaign", "location"])
- Add `SeedThread` model
- Extend `KeyLocation` with `location_threads` field
- Update seed prompt to generate location threads for key locations

**Phase 2: Thread activation logic**
- Add async location thread activation to world step (or new async sub-step)
- Activation logic: find seed-declared location threads for current location that haven't been activated
- Set dormant=False, urgency=seed-declared, added_turn=turn
- Log activation for event recording

**Phase 3: Thread lifecycle integration**
- Update ruling: only show urgent campaign threads (filter out location threads)
- Update convergence: only count campaign threads (filter out location threads)
- Update directive: only driven by campaign threads
- Update arc resolution: drop location threads at arc boundary
- Update thread cap: location threads don't count against cap

**Phase 4: Narrator integration**
- World step records thread activations in event data
- Narrator prompt includes thread activation context
- Narrator guidance: introduce thread content as environmental details

**Phase 5: Validation + testing**
- Checker: seed locations have location_threads populated (where appropriate)
- Checker: location threads activate on first location arrival
- Checker: location threads don't affect ruling/convergence/directive at background/normal urgency
- Eval: thread activation feels organic, not mechanical
- Eval: location threads don't disrupt pacing

### Risks

1. **Scope re-introduction complexity:** Re-introducing thread scope undoes the unify-threads simplification. Mitigation: keep scope as a single Literal field with only two values. Don't over-engineer — location threads are a narrow use case.

2. **Pacing disruption:** Even if location threads don't directly affect convergence, if Record promotes them to urgent, they WILL affect pacing. Mitigation: seed-declared location threads should start as background urgency. Record should need multiple turns to escalate them. This gives the player time to engage before pacing shifts.

3. **Seed complexity:** Adding location threads to seed generation increases dimensionality further. Mitigation: 0-2 threads per location, simple schema (id/summary/type/initial_urgency), not full ArcThread complexity.

4. **Thread dedup edge cases:** Location threads might overlap with campaign threads if seed generation isn't careful. Mitigation: seed prompt should include explicit guidance to avoid duplicating campaign thread content. Runtime dedup via Record's normal progress dedup as fallback.

5. **Arc boundary handling:** Location threads dropped at arc boundary might feel like lost content. Mitigation: if a location thread's content should survive arc boundary, Record should promote it via thread_update before arc resolution. This puts the agency on Record (LLM-driven), not the engine.

6. **Async activation timing:** Thread activation in async window means the player won't see activated threads until the next turn. Mitigation: this is acceptable — the narrator should introduce the thread content in the next turn's narration, which feels natural (the thread activates as the player explores, and the narrator describes what they find).

### Deferred Until After F-31

This design should NOT be implemented until F-31 (location expansion via seed-declared details) is implemented and proven effective. The seed-declared details alone should make locations feel interesting and worth visiting. If location threads are still desired after F-31 proves the foundation works, this design can be picked up as a separate enhancement.

The main blocker for location threads is re-introducing thread scope, which undoes the unify-threads simplification. This should only be done if seed-declared details alone don't provide enough incentive for location exploration.

### Dependencies on Other Designs

- **Location Expansion Design** — seed-declared location details as strings, first-visit flag, narrator exposition (prerequisite; should be proven effective first)
- **Seed Two-Step Design** — seed generation pipeline that location_threads extends
- **Seed Worldbuilding Redesign** — funnel ordering, key locations seed generation
- **Unify Threads Plan** — removed thread scope, unified all threads (this design reverses scope removal for location threads only)
