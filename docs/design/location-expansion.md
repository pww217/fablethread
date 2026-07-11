# Location Expansion Design

> **Status:** scoping
> **Related tickets:**
> - [F-31: Location expansion](../../roadmap/features/F-31-location-expansion.md) — seed-declared location opportunities (actions/narrative nodes), first-visit flag, NPC location pinning
> - [F-32: Scene inventory](../../roadmap/features/F-32-scene-inventory.md) — seed-declared location items as physical objects (separate concern; F-32 is about objects that can be picked up, not action opportunities)
> - [F-33: Location threads](../../roadmap/features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival (deferred)

## Problem

Locations are an afterthought in seed generation. Each seed produces:
- One starting location as `state.location` (LocationRef: id/name/description)
- 4-5 key locations as `world.locations` (KeyLocation: id/name/description/status/tags)

The key locations exist as seed-declared world map data but are never shown to the narrator, never referenced by ruling, and serve no function beyond being seed-declared facts. Players have no incentive to visit them. Location changes only replace `state.location` — there's no memory of visited places, no exposition about what's interesting at a location, and no narrator guidance toward exploring.

Currently the narrator only describes the current location's seed description string. There's no structured seed data about what makes a location interesting or worth visiting.

## Design Principles

**Seed-declared only.** All location data is seed-declared. No runtime extraction. No LLM-generated location opportunities at runtime. This keeps extraction pipeline unchanged and seed dimensionality manageable.

**Current location only.** Never show all key locations in every turn's prompt. Only the current location's seed data is shown. This prevents linear context bloat as more locations are visited.

**Permanent context.** Location opportunities are always shown as context when at a key location. They don't expire or fade. Opportunities are a permanent piece of the world's narrative fabric at that location.

**Minimal model changes.** One seed model field. One state flag. No extraction schema changes. No delta builder changes beyond one boolean flag. No ruling logic changes.

**Thread-path, not thread-yet.** Opportunities preview the thread system without integrating with it directly. Record extractor should naturally recognize opportunities as potential thread content during narration. Explicit thread integration happens later if needed.

## Target State

### Model Changes

**Seed model:** One field on `KeyLocation`:
```python
location_opportunities: list[str] = Field(default_factory=list, max_length=3)
```
Just strings. Not a model. Not items with IDs. Three short phrases seed-declared at seed time (e.g., "scout from watchtower to survey terrain", "talk to the town alderman about rumors", "visit the local tavern for gossip"). Each ~20-30 chars. Total ~90 tokens max.

**State model:** One field on `state.scene`:
```python
first_visit_location: bool = False
```
Set to `True` on location change if location ID differs from previous location's ID. Same place where `turn_entered` and `location_entered_turn` are already set. Used as a signal to the narrator to introduce opportunities into narration.

### Seed Prompt Change

Add one instruction to seed generation: "For each key location, list up to 3 narrative opportunities a player might pursue (short phrases, 20-30 chars each). These should be concrete actions or events available at the location, grounded in the location's purpose and the world's theme. Examples: 'scout from watchtower to survey terrain', 'talk to town alderman about rumors', 'listen to tavern gossip about nearby events.'"

### Prompt Context Management

**Narrate prompt:** One new section (after existing `_location.j2`):
```
## This Location
{seed description}

Opportunities:
- {opportunity 1}
- {opportunity 2}

{if first_visit_location: "Weave some opportunities into narration when relevant — not a list."}
{if not first_visit_location: "These opportunities may have changed since your arrival."}
```

~90 tokens max (2 opportunities × ~30 chars). Current location only. Never show all key locations.

**Ruling prompt:** No change. Location opportunities are context for exposition. Ruling already handles NPC impossibility via existing rules ("Punch X NPC — NPC is not in scene/location").

### Extraction Context

No change. Location opportunities feed the seed → narrate pipeline; no runtime extraction is required. If Record naturally recognizes opportunity-related content as thread-worthy during narration, that's emergent integration handled by Record's normal behavior. Explicit extraction changes for opportunities are scoped out.

### Collision Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Seed generation** | One new field on seed output | Seed already generates location data; additive, not structural |
| **Narrator prompt** | One new section, ~90 tokens | Current location only. No change to existing sections |
| **Ruling prompt** | None | No ruling prompt change in this design |
| ****Extraction schema** | None | No new extraction fields for opportunities. Record behavior is unchanged |
| **Delta builder** | One boolean flag | Same place where `turn_entered` is already set |
| **Convergence/phase** | None | No thread involvement in this phase |
| **Event recording** | One boolean in event dict | Same as `post_turn_location_id` |

### Interaction with Pacing

**Risk:** Location opportunities may trigger more location changes as players follow interesting content. This resets scene age more often (location change resets `turn_entered` and `location_entered_turn`), potentially preventing the directive from reaching "Scene Imperative" threshold (5 turns), keeping the scene in lighter directive territory.

**Mitigation:** Opportunities should encourage exploration through interesting content, not explicit direction. No explicit "you should go to X" — only natural exposition that might suggest interesting places ("The radio crackles with a distant transmission from the eastern line..."). This is narrator guidance, not engine enforcement.

**Convergence:** Location expansion does NOT directly affect convergence score. Convergence is driven by thread urgency, beat streaks, roll starvation, and threat density. Location changes reset scene age but don't modify convergence directly. If location changes cause more frequent scene age resets, the directive computation may stay at lighter levels longer, which could indirectly affect beat type selection in World step. This is acceptable — lighter directive territory is fine for exploratory scenes.

### Location Change Detection

No change needed. Step2b already detects location changes via movement verbs and destination language. The extractor emits `location_change` as it does now. The delta builder's existing NPC presence management and timestamp resets apply as they do now. `first_visit_location` flag is set in the same delta builder code path.

### NPC Location Pinning

This design includes location pinning — `last_seen_location` on NPCEntry becomes the canonical anchor point after location changes. When `state.location` changes, NPCs at the old location are demoted to `nearby` with their `last_seen_location` pinned. When the extractor detects narration indicating an NPC moved to a new location, it overrides the pin.

This is a behavior change, not a model change: NPCEntry already has `last_seen_location` for tracking. The pinning is just tightening the semantic meaning: `last_seen_location` is not just "where they were last mentioned" but "where they actually are, unless the extractor explicitly moves them."

### Soft Consistency Model

Seed-declared opportunities are the ground truth shown every turn as context. On first visit, narrator introduces them into narration. On revisits, narrator should note opportunities may have changed if the player interacted with them via prompt guidance.

The seed data is shown every turn as context — if the narrator previously described the player walking into the alderman's office and getting new intelligence, the oppo "talk to alderman for rumors" might be different next time. The narrator should self-correct based on prior narration. Seed data is always shown as context — it won't disappear or change, but the narrator should adapt.

### Implementation Phases

**Phase 1: Model + seed changes**
- Add `location_opportunities: list[str]` field to `KeyLocation` (max_length=2)
- Update seed prompt (`prepare_seed_system.j2`) to generate location_opportunities for each key location
- Add `first_visit_location: bool` to `state.scene`
- Delta builder sets `first_visit_location` on location change (same place as `turn_entered`)

**Phase 2: Prompt integration**
- Add location context section to narrate prompt (seed-declared opportunities + first_visit flag)
- Narrator guidance: weave some opportunities naturally into narration when relevant, not a list
- Narrator guidance: note opportunities may have changed on revisit

**Phase 3: NPC location pinning**
- Tighten `last_seen_location` semantics: canonical anchor point, authoritative but overrideable
- Delta builder pin behavior for NPC demotion on location change
- Extractor guidance: `last_seen_location` should only change when an NPC actually moves (not every time they're mentioned)

**Phase 4: Validation + testing**
- Checker: seed locations have location_opportunities populated (where appropriate)
- Checker: first_visit_location flag set correctly on location change
- Eval: narrator exposition quality at new locations
- Eval: opportunities woven naturally into narration, not presented as a list
- Eval: NPC location pinning works correctly across location changes

### Risks

1. **Seed complexity:** Adding `location_opportunities` to seed generation increases seed dimensionality. Mitigation: max 2 short strings per location, seed prompt should give clear examples.

2. **Prompt context bloat:** One section, ~90 tokens max per turn. Mitigation: cap at 2 opportunities, keep them concise. Measure token delta during implementation.

3. **Revisit handling:** On revisit, seed opportunities are still shown (they're seed-declared). Mitigation: narrator prompt should note "these opportunities may have changed if the player interacted with them" — narrator should self-correct based on prior narration. Soft consistency model.

4. **Record awareness of opportunities:** If Record doesn't naturally recognize opportunity-related narration as thread-worthy, the opportunities don't contribute to campaign narrative. Mitigation: this is an emergent integration, not enforced. The opportunities do help the narrator generate richer narration, which Record picks up without explicit thread handling. If Record misses the signal after testing, explicit integration can be added later (F-33).

### Deferred Items

- **Scene inventory as structured model** (F-32): seed-declared physical items at locations (objects that can be picked up via extraction). This is a separate concern — F-31 is actions/opportunities, not objects.
- **Location-scoped threads** (F-33): seed-declared dormant threads that activate on location arrival. Opportunities may naturally become thread content through Record extraction, but explicit thread integration should only happen if opportunities alone don't provide enough incentive for location exploration.
- **List of visited location IDs:** boolean flag is sufficient; if visited location history is needed later, add as separate ticket
- **UI changes:** turn viewer sidebar location panel may need updates later but not in this design
- **Dynamic location generation:** all locations seed-declared, no lazy generation on first visit
- **Player steering via narration:** opportunities should encourage exploration through interesting content, not explicit direction; if explicit steering is desired later, add as separate ticket

### Dependencies on Other Designs

- **Seed Two-Step Design:** seed generation pipeline that `location_opportunities` extends
- **Seed Worldbuilding Redesign:** funnel ordering, key locations seed generation
