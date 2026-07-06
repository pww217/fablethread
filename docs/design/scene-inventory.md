# Scene Inventory Design

> **Status:** scoping
> **Related tickets:**
> - [F-32: Scene inventory](../../roadmap/features/F-32-scene-inventory.md) — seed-declared location items as strings
> - [F-31: Location expansion](../../roadmap/features/F-31-location-expansion.md) — seed-declared location details as strings (prerequisite foundation)
> - [F-33: Location threads](../../roadmap/features/F-33-location-threads.md) — dormant seed-declared threads that activate on location arrival (independent)

## Problem

Inventory in CCYA is strictly PC-owned. `state.inventory` contains items the PC carries. When the narrator writes "You see a rusted key on the table" or "The weapon lies abandoned on the floor," that item exists narratively but has no state representation. This creates several issues:

1. **Narrator inconsistency:** The narrator may describe items that ruling didn't know about, creating dissonance if the player tries to interact with them.
2. **No ruling awareness:** Ruling's impossibility check only sees PC inventory. If the narrator describes a weapon on the wall and the player tries to pick it up, ruling has no context that the weapon exists.
3. **No state fidelity:** Items that exist in the world but not on the PC's person are ephemeral — they exist only in prose, not in state.
4. **Seed waste:** Seed generates rich location descriptions but no structured data about what's actually at each location.

The canceled B-12 ticket proposed `nearby_interactable_items` as a scene extraction concept but was never implemented. This design revisits the idea with a seed-declared string approach instead of runtime extraction.

## Design Principles

**Seed-declared strings only.** No new model for location items. Location items ARE seed-declared strings via F-31's `scene_details` field. "rusted key on desk" is both a detail AND an item. No separate seed field needed.

**Soft consistency.** Location items exist as seed-declared facts shown every turn as context. If the narrator describes the player taking an item, the narrator should note it's gone on subsequent visits via prompt guidance — not state enforcement. Acceptable for small detail lists (3 items max).

**Minimal extraction changes.** No new extraction fields. No new delta builder logic. One extraction context addition (seed-declared location details as context). One extraction prompt instruction (guidance on extracting PC pickup as `inventory_add`).

## Target State

### Model Changes

**No model changes.** Location items should be seed-declared as strings via F-31's `scene_details` field on `KeyLocation`. Each string can represent either an environmental detail or an interactable item — the seed prompt should include at least one item-like detail per location (e.g., "rusted key on desk" implies an item the player could pick up).

### Seed Prompt Change

Seed prompt should generate scene_details that include location items:
- 2-4 seed-declared details per location
- At least one should be an item the player could interact with (weapon, key, document, resource)
- Items should be appropriate to the location's purpose and the world's theme
- Items should NOT duplicate PC inventory items (seed already generates PC inventory separately)

### Prompt Context Management

**Narrate prompt:** Same as F-31 — location context section shows seed-declared details (which include items). No separate section needed.

**Ruling prompt:** Same as F-31 — ruling instruction about location details/items not needing to be in PC inventory for impossibility check. No separate ruling change needed.

### Extraction Context Change

Pass seed-declared location details as context to step2b's extraction prompt. One lookup by location ID from `state.world.locations`, shown as a short list in the extraction user prompt. This lets the LLM match narration to seed-declared items and emit `inventory_add` for location item pickups.

When the player picks up a location item, step2b should extract it as a PC inventory change via existing `inventory_add` mechanism. The extraction prompt needs guidance:
- "If the narration describes the PC taking an item that was present at this location (seed-declared), treat it as inventory_add"
- "Use an appropriate canonical ID if the seed-declared detail implies a specific item type"

### Collision Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Seed generation** | No model change | seed_details already covers location items as strings |
| **Narrator prompt** | No change | Same as F-31 |
| **Ruling prompt** | No change | Same as F-31 |
| **Extraction context** | One lookup + context addition | No schema change. No new extraction fields |
| **Delta builder** | No change | No location_inventory fields |
| **Convergence/phase** | No change | No thread involvement |

### Interaction with Ruling's Impossibility Check

Same as F-31. Ruling should NOT mark location item interactions as impossible just because the item isn't in PC inventory. Physical constraints and character capabilities still apply — ruling should only be lenient on location items, not on all impossibility checks.

### Interaction with Seed Generation

Seed prompt should generate scene_details that include location items:
- 2-4 seed-declared details per location
- At least one should be an item the player could interact with (weapon, key, document, resource)
- Items should be appropriate to the location's purpose and the world's theme
- Items should NOT duplicate PC inventory items (seed already generates PC inventory separately)

### Token Efficiency

Same as F-31. Location context should be **current location only**. One section. ~90 tokens max per turn. No change to seed dimensionality beyond one field. No extraction changes beyond prompt guidance.

### Soft Consistency Model

Same as F-31. Location items exist as seed-declared facts shown every turn as context. If narrator describes player taking an item, narrator should note it's gone via prompt guidance — not state enforcement. Acceptable for small detail lists (3 items max).

### Implementation Phases

**Phase 1: No model changes (covered by F-31)**
- F-31's `scene_details` field on `KeyLocation` already covers location items as seed-declared strings
- No additional seed model changes needed

**Phase 2: Prompt integration (covered by F-31)**
- F-31's narrator prompt location context section already shows seed-declared details (including items)
- F-31's ruling prompt instruction already covers location item awareness
- No additional prompt changes needed

**Phase 3: Extraction guidance**
- Pass seed-declared location details to step2b's extraction prompt (lookup by location ID from `world.locations`)
- Update step2b extraction prompt: guidance on extracting PC pickup of location items as inventory_add
- Validate extraction correctly handles location item pickup

**Phase 4: Validation + testing**
- Checker: seed locations have scene_details populated (covered by F-31)
- Checker: narrate prompt includes location details context (covered by F-31)
- Eval: narrator exposition quality with location items
- Eval: ruling awareness of location items for impossibility (covered by F-31)
- Eval: extraction correctly handles location item pickup

### Risks

1. **Seed complexity:** seed_details should include at least one location item per location. Mitigation: seed prompt should give clear examples of item details vs environmental details. Max 3 details per location keeps seed dimensionality manageable.

2. **Soft consistency:** Location items exist as seed-declared facts. If narrator describes player taking an item, there's no state enforcement that the item is gone. Mitigation: prompt guidance should encourage narrator self-correction based on prior narration. Accept that this is a soft consistency model.

3. **Extraction ambiguity:** When player picks up a location item, step2b needs to know it's a location item pickup vs a new item discovery. Mitigation: extraction prompt should include location detail context and guidance on matching narration to seed-declared details.

4. **Prompt context bloat:** seed_details add tokens every turn. Mitigation: cap at 3 details per location, keep them concise. Measure token delta during implementation.

### Deferred Items

- **Seed-declared location items as a separate model:** seed-declared strings are enough for now; if runtime item interaction needs more structure (item IDs, amounts, durability), that's a separate ticket
- **Location-scoped threads:** seed-declared details alone should make locations feel alive; thread scope re-introduction should only be picked up if seed-declared details alone don't provide enough incentive for location exploration
- **Runtime location inventory extraction:** seed-declared only, no extraction of new location items at runtime via new fields
- **Item durability/degradation:** items don't change condition over time
- **Multiple copies of location items:** seed-declared items are single instances
- **UI changes:** turn viewer may need updates later but not in this design
- **Dynamic item generation:** all items seed-declared, no lazy generation

### Dependencies on Other Designs

- **Location Expansion Design** — seed-declared location details as strings, first-visit flag, narrator exposition (prerequisite; this design builds on F-31's seed_details field)
- **Seed Two-Step Design** — seed generation pipeline that seed_details extends
- **Seed Worldbuilding Redesign** — funnel ordering, key locations seed generation
