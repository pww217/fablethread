# Location Expansion Design

> **Status:** scoping
> **Related tickets:**
> - [F-31: Location expansion](../../roadmap/features/F-31-location-expansion.md) — seed-declared details, narrator exposition, first-visit flag
> - [F-32: Scene inventory](../../roadmap/features/F-32-scene-inventory.md) — seed-declared location items as strings (builds on this foundation)
> - [F-33: Location threads](../../roadmap/features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival (deferred)

## Problem

Locations are an afterthought in seed generation. Each seed produces:
- One starting location as `state.location` (LocationRef: id/name/description)
- 4-5 key locations as `world.locations` (KeyLocation: id/name/description/status/tags)

The key locations exist as seed-declared world map data but are never shown to the narrator, never referenced by ruling, and serve no function beyond being seed-declared facts. Players have no incentive to visit them. Location changes only replace `state.location` — there's no memory of visited places, no exposition about what's interesting at a location, and no narrator guidance toward exploring.

Currently the narrator only describes the current location's seed description string. There's no structured seed data about what makes a location interesting or worth visiting.

## Design Principles

**Seed-declared only.** All location data is seed-declared. No runtime extraction. No LLM-generated location details at runtime. This keeps extraction pipeline unchanged and seed dimensionality manageable.

**Current location only.** Never show all key locations in every turn's prompt. Only the current location's seed data is shown. This prevents linear context bloat as more locations are visited.

**Soft consistency.** Location details exist as seed-declared facts shown every turn as context. If the narrator describes the player taking an item, the narrator should note it's gone on subsequent visits via prompt guidance — not state enforcement. Acceptable for small detail lists (3 items max).

**Minimal model changes.** One seed model field. One state flag. No extraction schema changes. No delta builder changes beyond one boolean flag. No ruling logic changes.

## Target State

### Model Changes

**Seed model:** One field on `KeyLocation`:
```python
scene_details: list[str] = Field(default_factory=list, max_length=3)
```
Just strings. Not a model. Not items with IDs. Three short phrases seed-declared at seed time (e.g., "rusted key on desk", "fresh boot prints in mud", "radio crackling with static"). Each ~20-30 chars. Total ~90 tokens max.

**State model:** One field on `state.scene`:
```python
first_visit_location: bool = False
```
Set to `True` on location change if location ID differs from previous location's ID. Set to `False` otherwise (same location revisited). One boolean flag, set in delta builder where `turn_entered` and `location_entered_turn` are already set.

### Seed Prompt Change

Add one instruction to seed generation: "For each key location, list up to 3 concrete details a player might notice when arriving (short phrases, 20-30 chars each). These should be specific and grounded in the location's purpose and the world's theme."

### Prompt Context Management

**Narrate prompt:** One new section (after existing `_location.j2`):
```
## This Location
{seed description}
Notable details:
- detail 1
- detail 2
- detail 3
{if first_visit_location: "Describe these as environmental details you notice."}
{if not first_visit_location: "These details may have changed if the player interacted with them."}
```

~90 tokens max (3 details × ~30 tokens each). Current location only. Never show all key locations.

**Ruling prompt:** One instruction added to ruling system prompt: "Player may interact with location details described in narration (items, objects, environmental features). These don't need to be in PC inventory for the action to be possible — ruling should only mark actions as impossible if they violate physical constraints or character capabilities, not if the required item isn't in PC inventory."

### Extraction Context Change (F-32 integration)

Pass seed-declared location details as context to step2b's extraction prompt. One lookup by location ID from `state.world.locations`, shown as a short list in the extraction user prompt. This lets the LLM match narration to seed-declared items and emit `inventory_add` for location item pickups.

### Collision Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Seed generation** | One new field on seed output | Seed already generates location data; additive, not structural |
| **Narrator prompt** | One new section, ~90 tokens | Current location only. No change to existing sections |
| **Ruling prompt** | One instruction | No model change. No ruling logic change |
| **Extraction context** | One lookup + context addition | No schema change. No new extraction fields |
| **Delta builder** | One boolean flag | Same place where `turn_entered` is already set |
| **Convergence/phase** | None | No thread involvement |
| **Event recording** | One boolean in event dict | Same as `post_turn_location_id` |

### Interaction with Pacing

**Risk:** If location details trigger more location changes, scene age resets more often (location change resets `turn_entered` and `location_entered_turn`). This could prevent the directive from reaching "Scene Imperative" threshold (5 turns), keeping the scene in lighter directive territory.

**Mitigation:** Location details should encourage exploration through interesting content, not explicit direction. No explicit "you should go to X" — only natural exposition that might suggest interesting places ("The radio crackles with a distant transmission from the eastern line..."). This is narrator guidance, not engine enforcement.

**Convergence:** Location expansion does NOT directly affect convergence score. Convergence is driven by thread urgency, beat streaks, roll starvation, and threat density. Location changes reset scene age but don't modify convergence directly. If location changes cause more frequent scene age resets, the directive computation may stay at lighter levels longer, which could indirectly affect beat type selection in World step. This is acceptable — lighter directive territory is fine for exploratory scenes.

### Location Change Detection

No change needed. Step2b already detects location changes via movement verbs and destination language. The extractor emits `location_change` as it does now. The delta builder's existing NPC presence management and timestamp resets apply as they do now. `first_visit_location` flag is set in the same delta builder code path.

### Soft Consistency Model

Seed-declared details are the ground truth shown every turn as context. On first visit, narrator describes them as environmental details the player notices. On revisits, narrator should note details may have changed if the player interacted with them via prompt guidance.

The seed data is shown every turn as context — if the narrator previously described taking an item, the narrator should note it's gone. If context got truncated and the narrator forgets, seed data might contradict prior narration — that's the soft part. Acceptable for small detail lists (3 items max).

### Implementation Phases

**Phase 1: Model + seed changes**
- Add `scene_details: list[str]` field to `KeyLocation` (max_length=3)
- Update seed prompt (`prepare_seed_system.j2`) to generate scene_details for each key location
- Add `first_visit_location: bool` to `state.scene`
- Delta builder sets `first_visit_location` on location change (same place as `turn_entered`)

**Phase 2: Prompt integration**
- Add location context section to narrate prompt (seed-declared details + first_visit flag)
- Narrator guidance: describe details as environmental details on first visit
- Narrator guidance: note details may have changed on revisit
- Add ruling prompt instruction: location details don't need to be in PC inventory for ruling impossibility check

**Phase 3: Extraction context (F-32)**
- Pass seed-declared location details to step2b's extraction prompt (lookup by location ID from `world.locations`)
- Update step2b extraction prompt: guidance on extracting PC pickup of location items as inventory_add

**Phase 4: Validation + testing**
- Checker: seed locations have scene_details populated (where appropriate)
- Checker: first_visit_location flag set correctly on location change
- Eval: narrator exposition quality at new locations
- Eval: ruling handles location detail interactions correctly
- Eval: extraction correctly handles location item pickup

### Risks

1. **Seed complexity:** Adding scene_details to seed generation increases seed dimensionality. Mitigation: max 3 short strings per location, seed prompt should give clear examples.

2. **Prompt context bloat:** One section, ~90 tokens max per turn. Mitigation: cap at 3 details, keep them concise. Measure token delta during implementation.

3. **Revisit handling:** On revisit, seed details are still shown (they're seed-declared). Mitigation: narrator prompt should note "these details may have changed if the player interacted with them" — narrator should self-correct based on prior narration. Soft consistency model.

4. **Ruling leniency:** If ruling is too lenient on location details, it might mark clearly impossible actions as possible. Mitigation: ruling instruction should say location details don't need to be in PC inventory — not that ruling should ignore impossibility entirely. Physical constraints and character capabilities still apply.

### Deferred Items

- **Scene inventory as structured model** (F-32): seed-declared strings are enough for now; if runtime item interaction needs more structure (item IDs, amounts, durability), that's a separate ticket
- **Location-scoped threads** (F-33): seed-declared details alone should make locations feel alive; thread scope re-introduction should only be picked up if seed-declared details alone don't provide enough incentive for location exploration
- **List of visited location IDs:** boolean flag is sufficient; if visited location history is needed later, add as separate ticket
- **UI changes:** turn viewer sidebar location panel may need updates later but not in this design
- **Dynamic location generation:** all locations seed-declared, no lazy generation on first visit
- **Player steering via narration:** location details should encourage exploration through interesting content, not explicit direction; if explicit steering is desired later, add as separate ticket

### Dependencies on Other Designs

- **Seed Two-Step Design** — seed generation pipeline that seed_details extends
- **Seed Worldbuilding Redesign** — funnel ordering, key locations seed generation
