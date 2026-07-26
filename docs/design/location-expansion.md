# Location Expansion Design

> **Status:** reviewed
> **Related tickets:**
> - [F-31: Location expansion](../../roadmap/features/F-31-location-expansion.md) — seed-declared location threads, first-visit flag, NPC location pinning
> - [F-32: Scene inventory](../../roadmap/features/F-32-scene-inventory.md) — seed-declared location details/items (separate concern; builds on this design)
> - [F-33: Location threads](../../roadmap/features/F-33-location-threads.md) — **merged into this design** per design review (see `to_scope/location-threads.md` for history)
>
> **Design review decisions incorporated:**
> 1. One hook mechanism: seed-declared location threads. The earlier `location_opportunities` concept (actions as plain strings) is retired — opportunities were a placeholder for threads.
> 2. No `scope` field on ArcThread. Threads are threads. Activated location threads affect convergence, ruling, and directive exactly like any other thread.
> 3. Activation is engine-driven and synchronous, in the delta builder at location arrival. No LLM call, no async window.
> 4. Seed-declared urgency is background or normal only — never urgent. Escalation happens via Record's normal mechanics.
> 5. Resolved threads drop out of narrator context — real state signal for revisits, replacing the earlier "opportunities may have changed" soft-consistency model.
> 6. Location threads bias toward `type=opportunity` (locations primarily offer things to pursue); other types allowed for variety. Locations mentioned in or required for the long-term objective carry threads that flesh out, gate, or complicate that objective.
> 7. Thread cap semantics confirmed against source: the cap (`thread_max_active`, default 5) counts active/non-dormant threads only. Eviction (demote stalest active) is currently inlined in turn_state.py's record `thread_add` path and must be extracted into a shared helper so activation can apply it. Freshly activated threads are never the eviction victim — evictions always hit older campaign threads, and the dormant-pool cull can cascade an evicted thread to "abandoned."

## Problem

Locations are an afterthought in seed generation. Each seed produces:
- One starting location as `state.location` (LocationRef: id/name/description)
- 4-5 key locations as `world.locations` (KeyLocation: id/name/description/status/tags)

The key locations exist as seed-declared world map data but are never shown to the narrator, never referenced by ruling, and serve no function beyond being seed-declared facts. Players have no incentive to visit them. Location changes only replace `state.location` — there's no memory of visited places, no exposition about what's interesting at a location, and no narrator guidance toward exploring.

Worse, when the player arrives at a new location, no new narrative pressure or context emerges from the location itself. Location changes feel like set changes — the narrator describes the new place, but no threads emerge from it.

## Design Principles

**Seed-declared only.** All location thread data is seed-declared. No runtime thread generation at locations. This keeps seed dimensionality manageable and avoids extraction complexity.

**One hook mechanism.** Location threads are the single seed-declared per-location narrative hook. There is no separate "opportunities" concept — anything a location offers the player is a thread.

**Engine-activated, not LLM-activated.** Thread activation is deterministic delta-builder logic triggered by location arrival. The LLM generates threads at seed time and manages them after activation (Record escalates/resolves; narrator weaves them in), but the activation decision belongs to the engine.

**No scope field.** `ArcThread` does not regain a `scope` field (the unify-threads simplification stands). Activated location threads are ordinary threads: they count toward the thread cap, affect convergence/ruling/directive per normal rules, and follow the normal lifecycle including arc boundaries.

**Never urgent at seed.** Seed-declared location threads start at background or normal urgency. Arriving at a location never instantly spikes convergence; escalation to urgent takes turns via Record. This is the pacing guardrail.

**Current location only.** Never show all key locations in every turn's prompt. Only the current location's seed data is shown.

**Resolution-aware context.** Narrator context shows the location's activated, unresolved threads. Resolved threads drop out of the section — the world's state, not narrator self-correction, signals what has changed on revisit.

**Minimal model changes.** One seed model (SeedThread), one field on KeyLocation, one state flag. No extraction schema changes. No convergence/ruling/directive filtering.

## Target State

### Model Changes

**Seed model:** New model + one field on `KeyLocation`:
```python
class SeedThread(BaseModel):
    id: str
    summary: str
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    initial_urgency: Literal["background", "normal"] = "background"
    # Never urgent at seed — pacing guardrail
    activated: bool = False  # set by engine on location arrival
```

Seed threads are simpler than full `ArcThread` — no progress entries, resolution state, or turn tracking at seed time. Those populate at activation.

```python
class KeyLocation(BaseModel):
    # ... existing fields ...
    location_threads: list[SeedThread] = Field(default_factory=list, max_length=2)
```

0-2 threads per location (not every location needs threads). Type biased toward `opportunity`, other types allowed for variety (see Seed Prompt Change). Seed prompt must avoid duplicating seed-declared campaign thread content, and thread IDs must be unique against campaign thread IDs.

**State model:** One field on `state.scene`:
```python
location_arrived: bool = False
```
Set to `True` on any location change, in the same delta-builder block that sets `turn_entered`/`location_entered_turn` (delta_builder.py:208-232). **Note:** the delta builder applies `location_change` only when the ID differs from the current location — this fires on *every* move, including revisits. This is an **arrival detector, not a first-visit detector**. True first-visit tracking requires a visited-ID list, which remains deferred; the flag's original name (`first_visit_location`) was retired because it stated semantics the spec couldn't deliver.

**Unified KeyLocation target schema.** This design owns `location_threads`. Two further fields land via follow-up designs and are recorded here so the seed schema evolves once, not three times:
- `scene_details: list[str]` — location details/items, via [F-32 Scene Inventory](to_scope/scene-inventory.md)
- `faction_presence: list[str]` — faction IDs (0-2), via [Dynamic Factions](to_scope/dynamic-factions-redesign.md)

### Thread Activation

**When:** In the delta builder, at location change — the same code path that sets `location_arrived` and `turn_entered`. Location changes are detected by step2b extraction; activation lands in the same apply phase as the location change itself. The narrator sees the new location and its activated threads together on the first turn at the new location — single-turn choreography, no async window, no event plumbing.

**How:** For each SeedThread on the new location where `activated=False`:
- Create an `ArcThread`: same id, summary, type; `dormant=False`; `urgency=initial_urgency`; `added_turn=current turn`; `last_updated_turn=current turn`
- Set `activated=True` on the SeedThread (prevents re-activation on revisit)
- Log activation for event recording

**Why sync:** Activation is a pure state mutation keyed off a location change the delta builder already detects. There is no LLM call to defer, so the async World-step window buys nothing and costs a one-turn delay.

**After activation:** The thread is an ordinary thread. Record escalates or resolves it via normal mechanics (`ThreadUpdate.urgency` exists; the sanitizer can also change urgency/dormancy). If Record promotes it to urgent, it affects convergence and directive like any urgent thread — this is intended. No special arc-boundary handling.

**Sanitizer interaction (verified against `sanitize_thread.j2`):** The sanitizer targets 3-4 threads and consolidates aggressively, but explicitly *never* abandons, dormants, or culls "threads that have never been updated (no turns-ago suffix)." Freshly activated location threads have no progress entries, so they are protected by that existing rule until they see narrative activity.

**Thread cap interaction:** The cap (`thread_max_active`, default 5) counts **active (non-dormant) threads only**; dormant threads are culled when their count reaches 3 (oldest dormant moved to completed as "abandoned" — effective dormant max 2). **Verified against source:** the eviction logic is currently **inlined in turn_state.py's record `thread_add` path only** (turn_state.py:603-615) — it does not fire for engine-side thread creation. Activation must extract that logic into a shared helper and apply it. Eviction demotes the stalest active thread by `last_updated_turn`; freshly activated threads are stamped with the current turn, so they are **never** the eviction victim — the victim is always an older campaign thread. Cascade to note: an arrival eviction grows the dormant pool, and the engine cull (>=3 dormant, runs every turn) can then permanently move a dormant campaign thread to completed/"abandoned" as a side effect of walking into a location. Accepted behavior under "threads are threads," covered by eval.

**Decided (review):** Activation applies eviction **immediately** — the inlined eviction logic in turn_state.py is extracted into a shared helper that both the record `thread_add` path and delta-builder activation call. The cap is never violated, and arrival-triggered demotions are deterministic and logged at the moment they happen.

**Dedup:** Seed prompt avoids duplicating campaign threads. Runtime overlap is handled by Record's normal progress dedup.

### Seed Prompt Change

Add instruction to seed generation covering three rules:

1. **Baseline:** "For each key location, optionally declare 0-2 narrative threads tied to this place (id, summary, type, initial urgency of background or normal — never urgent). Threads must be grounded in the location's purpose and the world's theme, must not duplicate the campaign threads, and thread IDs must be unique."
2. **Type bias:** "Bias location threads toward type=opportunity — locations primarily offer things to pursue. Complication, threat, and revelation are allowed for variety, but most location threads should be opportunities."
3. **Objective linkage:** "If a key location is mentioned in or required for the long-term objective, it should carry at least one thread that fleshes out, gates, or complicates that objective — any type as appropriate. Example: for objective 'reach the radio tower and broadcast a signal,' the tower might get a complication 'the broadcast array is damaged' plus an opportunity 'scavenged amplifier parts could boost signal range.' Objective-critical locations should feel central, not decorative."

Example of a baseline thread: a revelation thread "decrypted radio signals point to a survivor camp" at a radio station.

**Separate pool, explicitly:** Location threads live in a per-location field and do **not** count toward the seed's arc-thread constraints (exactly 2 non-dormant, ≥2 dormant, 4-5 total, ≥1 threat). The seed prompt must say so — otherwise the LLM will try to satisfy both constraint sets in one pool.

### Prompt Context Management

**Narrate prompt:** One "Location Context" section (after existing `_location.j2`), **aggregate cap ~150 tokens**, shared by this design and F-32:
```
## This Location
{seed description}

{scene_details — via F-32, filtered against taken_location_items}
{faction_presence — via Dynamic Factions: names of factions present here}

Threads here:
- {activated, unresolved thread summary}
- ...

{if location_arrived: "Weave 1-2 of these into narration naturally — not a list."}
```

Rendering rules:
- Current location only. Never all key locations.
- **Description precedence:** when the current location ID matches a KeyLocation, render that KeyLocation's seed description **instead of** `_location.j2`'s LocationRef description for that turn. Seed is ground truth; `LocationRef.description` is extractor-written on moves (extract_state_system.j2) and can diverge — the existing `location_description_consistency` checker already watches this property. Fall back to `_location.j2` when no KeyLocation matches.
- Threads shown = the location's SeedThreads where `activated=True`, minus any whose ArcThread is resolved (join by thread id).
- On revisit, resolved threads are simply absent — state, not narrator memory, reflects what changed.

**Ruling prompt:** No change in this design. (F-32 adds location-item awareness for the impossibility check.)

### Extraction Context

No change in this design. Record naturally recognizes activated thread content during narration — threads are real ArcThreads, so Record's normal thread handling applies with no emergent-integration gap.

### Collision Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Seed generation** | SeedThread model + one field on KeyLocation | 0-2 threads per location, simple schema |
| **Narrator prompt** | One section, ~150 token aggregate cap shared with F-32 | Current location only; resolved threads filtered |
| **Ruling prompt** | None | F-32 owns the only ruling change |
| **Extraction schema** | None | Threads are ordinary ArcThreads after activation |
| **Delta builder** | One boolean flag + activation logic | Same code path as `turn_entered` |
| **Convergence/ruling/directive** | None — deliberately | No filtering; activated threads behave normally by design |
| **Thread cap** | Activated threads count toward the active-only cap (`thread_max_active`, default 5) | Eviction rule is inlined in turn_state.py's record path — extract to shared helper and apply at activation; cull cascade documented (see Thread cap interaction) |
| **Arc resolution** | None | Normal thread lifecycle, no drop rule |
| **Event recording** | Activation logged | Same pattern as `post_turn_location_id` |

### Interaction with Pacing

**Convergence:** Activated location threads affect convergence exactly like campaign threads — with one component asymmetry verified against source (`_pacing.py:75-126`). Only the `urgent_thread` component is urgency-gated. The `threat_thread` component (+1) counts **any** non-dormant threat-type thread regardless of urgency, so a threat-type location thread adds +1 immediately on activation (convergence threshold default 2). `threat_density` (+1) requires 3 active threat threads (`threat_density_threshold` default 3), so location threads alone are unlikely to trip it. This makes the seed-time **opportunity-type bias load-bearing for pacing**, not just flavor: opportunity/complication/revelation threads contribute nothing until Record escalates them to urgent, while threat threads apply immediate arrival pressure. "Never urgent at seed" is the escalation guardrail; the type bias is the arrival-shock guardrail. Eval covers: arriving at a location never causes an immediate phase transition.

**Scene age:** Location changes reset scene age (existing behavior), which can keep scenes in lighter directive territory. Thread activation itself does NOT reset scene age — it's a state change within the location, not a location change.

**Directive:** Driven by campaign thread urgency and scene age; location threads participate only through their normal urgency.

### NPC Location Pinning

This design includes location pinning — `last_seen_location` on NPCEntry becomes the canonical anchor point after location changes. When `state.location` changes, NPCs at the old location are demoted to `nearby` with their `last_seen_location` pinned. When the extractor detects narration indicating an NPC moved to a new location, it overrides the pin.

This is a behavior change, not a model change: NPCEntry already has `last_seen_location`. The pinning tightens the semantic meaning: `last_seen_location` is not just "where they were last mentioned" but "where they actually are, unless the extractor explicitly moves them." Extractor guidance: `last_seen_location` should only change when an NPC actually moves, not every time they're mentioned.

(Faction-owned NPCs get a natural anchor once `faction_presence` lands — see Dynamic Factions design.)

### Implementation Phases

**Phase 1: Model + seed changes**
- Add `SeedThread` model; add `location_threads` to `KeyLocation` (max_length=2)
- Update seed prompt to generate location threads (0-2, background/normal only, varied types, no campaign duplication, unique IDs)
- Add `location_arrived: bool` to `state.scene`
- Delta builder: set `location_arrived` on location change; activate seed threads on arrival (same code path)

**Phase 2: Prompt integration**
- Add Location Context section to narrate prompt (description + activated unresolved threads + first_visit guidance), ~150 token aggregate cap
- Narrator guidance: weave threads naturally into narration on first visit, not a list

**Phase 3: NPC location pinning**
- Tighten `last_seen_location` semantics: canonical anchor point, authoritative but overrideable
- Delta builder pin behavior for NPC demotion on location change
- Extractor guidance: pin only changes when an NPC actually moves

**Phase 4: Validation + testing**
- Checker: seed locations have location_threads populated (where appropriate), background/normal only, unique IDs
- Checker: threads activate exactly once on first arrival, not on revisit
- Checker: location_arrived set correctly on location change (fires on every arrival, including revisits)
- Checker: activated location threads counted in thread cap
- Eval: narrator exposition quality at new locations; threads woven naturally, not listed
- Eval: arriving at a location never causes an immediate phase transition
- Eval: activation overflow evicts the oldest active thread per the existing eviction path (including the edge case of a just-activated thread being evicted)
- Eval: objective-linked locations carry objective-relevant threads; type bias toward opportunity holds
- Eval: NPC location pinning across location changes
- Docs: update `docs/architecture/state-models.md` (SeedThread, KeyLocation.location_threads, Scene.location_arrived), `docs/architecture/pacing-systems.md` (threat-component asymmetry), `docs/repomap.md`

**State mutator note (per AGENTS.md):** Activation mutates `world.locations` (SeedThread.activated) — a new runtime mutation site; nothing mutates `world.locations` today. All mutations go through typed mutator methods returning a new `WorldState`, never dict assignment.

### Risks

1. **Thread cap pressure.** Activated location threads count toward the active-thread cap (default 5, non-dormant only). Mitigation: activation only on visit (most playthroughs visit few locations); overflow is handled by the existing eviction path (oldest active demoted to dormant), not new machinery; `thread_cap_eviction` checker plus an overflow eval monitor it.

2. **Seed complexity.** Location threads add seed dimensionality. Mitigation: 0-2 per location, simple schema (id/summary/type/urgency), clear examples in seed prompt.

3. **Prompt context bloat.** One section, ~150 token aggregate cap shared with F-32. Mitigation: current location only, resolved threads filtered, measure token delta during implementation.

4. **Convergence surprise.** Two paths: threat-type location threads add +1 immediately via the `threat_thread` component regardless of urgency, and Record may escalate any thread to urgent over turns. Mitigation: opportunity-type bias is the arrival-shock guardrail (non-threat types contribute nothing until urgent); `threat_density` needs 3 active threats (default) so location threads alone can't trip it; eval checks no immediate phase transition on arrival.

5. **Seed thread dedup edge cases.** Location threads might overlap campaign threads. Mitigation: explicit seed prompt guidance + unique IDs; Record's normal progress dedup as fallback.

### Deferred Items

- **Scene inventory** (F-32): seed-declared location details/items as physical objects — separate design building on this one
- **Faction presence**: `faction_presence` on KeyLocation — see Dynamic Factions design
- **List of visited location IDs:** `location_arrived` (arrival detector) is sufficient; add as a separate ticket if true first-visit semantics are ever needed
- **UI changes:** turn viewer sidebar location panel may need updates later
- **Dynamic location generation:** all locations seed-declared, no lazy generation
- **Player steering via narration:** threads encourage exploration through content, not explicit direction

### Dependencies on Other Designs

- **Seed Two-Step Design:** seed generation pipeline that `location_threads` extends
- **Seed Worldbuilding Redesign:** funnel ordering, key locations seed generation
- **Unify Threads Plan:** removed thread scope; this design deliberately preserves that removal — location threads are ordinary threads
