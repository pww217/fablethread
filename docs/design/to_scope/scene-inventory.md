# Scene Inventory Design

> **Status:** reviewed
> **Related tickets:**
> - [F-32: Scene inventory](../../../roadmap/features/F-32-scene-inventory.md) — seed-declared location details/items as strings
> - [F-31: Location expansion](../../../roadmap/features/F-31-location-expansion.md) — location threads, first-visit flag (prerequisite; ships first)
>
> **Design review decisions incorporated:**
> 1. This design **owns** the `scene_details` field on KeyLocation. Earlier drafts assumed F-31 provided it; F-31's field is `location_threads` (action hooks became threads), so details/items land here.
> 2. This design **owns** the ruling-context change (location items visible to ruling's impossibility check). F-31 makes no ruling change.
> 3. Taken items are **tracked, not soft-corrected**: `taken_location_items` on state, appended by the delta builder on matching `inventory_add`, filtered from narrate/extraction context. Seed facts stay intact for audit and turn viewer.

## Problem

Inventory in CCYA is strictly PC-owned. `state.inventory` contains items the PC carries. When the narrator writes "You see a rusted key on the table" or "The weapon lies abandoned on the floor," that item exists narratively but has no state representation. This creates several issues:

1. **Narrator inconsistency:** The narrator may describe items that ruling didn't know about, creating dissonance if the player tries to interact with them.
2. **No ruling awareness:** Ruling's impossibility check only sees PC inventory. If the narrator describes a weapon on the wall and the player tries to pick it up, ruling has no context that the weapon exists.
3. **No state fidelity:** Items that exist in the world but not on the PC's person are ephemeral — they exist only in prose, not in state.
4. **Seed waste:** Seed generates rich location descriptions but no structured data about what's actually at each location.

The canceled B-12 ticket proposed `nearby_interactable_items` as a scene extraction concept but was never implemented. This design revisits the idea with a seed-declared string approach instead of runtime extraction.

## Design Principles

**Seed-declared strings only.** No item model with IDs, amounts, or durability. Location items are seed-declared strings in `scene_details`. "rusted key on desk" is both a detail and an item.

**Tracked removal, not soft consistency.** When the PC takes a seed-declared item, the delta builder records it in `taken_location_items` and context renderers filter it out. The seed fact remains in state (audit, turn viewer), but the narrator and extractor no longer see it. This kills the "take the same key twice" failure mode that pure narrator self-correction invites.

**Minimal extraction changes.** No new extraction fields. One extraction context addition (location details as context to step2b). One extraction prompt instruction (match PC pickup to seed-declared item, emit `inventory_add`). Delta builder gains the taken-items append.

## Target State

### Model Changes

**Seed model:** One field on `KeyLocation` (part of the unified KeyLocation schema defined in F-31):
```python
scene_details: list[str] = Field(default_factory=list, max_length=3)
```
Mixed environmental details and interactable items as short strings. At least one entry per location should be item-like (weapon, key, document, resource).

**State model:** One field (exact placement TBD at plan time — `state.world` or `state.scene`):
```python
taken_location_items: list[str] = Field(default_factory=list)
```
Entries are the seed detail strings the PC has taken (e.g., "rusted key on desk").

### Seed Prompt Change

Seed prompt generates `scene_details` per key location:
- Up to 3 details per location
- At least one should be an item the player could interact with (weapon, key, document, resource)
- Details should be appropriate to the location's purpose and the world's theme
- Items should NOT duplicate PC inventory items (seed generates PC inventory separately)

### Prompt Context Management

**Narrate prompt:** Location details join F-31's "Location Context" section, within its **~150 token aggregate cap**. Rendered as the location's `scene_details` filtered against `taken_location_items`:
```
## This Location
{seed description}

- {detail 1}
- {detail 2}   (taken items omitted)

Threads here: ...   (via F-31)
```

**Ruling prompt:** One addition, owned by this design: pass the current location's (un-taken) `scene_details` as context, with guidance that interactions with these items are NOT impossible merely because the item isn't in PC inventory. Physical constraints and character capabilities still apply — leniency covers item presence only.

### Extraction Context Change

Pass the current location's un-taken `scene_details` to step2b's extraction prompt (one lookup by location ID from `state.world.locations`). This lets the LLM match narration to seed-declared items and emit `inventory_add` for pickups. Prompt guidance:
- "If the narration describes the PC taking an item that was present at this location (seed-declared), treat it as inventory_add"
- "Use an appropriate canonical ID if the seed-declared detail implies a specific item type"

### Delta Builder Change

When step2b emits `inventory_add` whose narration matches a seed-declared detail at the current location, append that detail string to `taken_location_items`. Matching reuses the same seed-detail context passed to the extractor — no fuzzy matching in the delta builder; the extraction prompt's matching is the authority, and the delta builder records the matched detail string emitted with the delta. (Exact delta shape — e.g., an optional `matched_location_detail` hint on `inventory_add` — is a plan-time decision.)

### Collision Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Seed generation** | One field on KeyLocation | Max 3 short strings |
| **Narrator prompt** | Details added to F-31's Location Context section | Within ~150 token aggregate cap; taken items filtered |
| **Ruling prompt** | One context addition + guidance, owned here | Current location only; leniency limited to item presence |
| **Extraction context** | One lookup + context addition to step2b | No schema change, no new extraction fields |
| **Delta builder** | One list append on matched pickup | Authority is the extractor's match; no fuzzy matching engine-side |
| **Convergence/phase** | None | No thread involvement |

### Interaction with Ruling's Impossibility Check

Ruling should NOT mark location item interactions as impossible just because the item isn't in PC inventory — but only for items currently shown (seed-declared and not taken). Physical constraints and character capabilities still apply. Ruling leniency covers item presence only, not all impossibility checks.

### Token Efficiency

Location details live inside F-31's Location Context section and its ~150 token aggregate cap: current location only, one section, taken items filtered. No seed dimensionality beyond one field.

### Taken-Items Consistency Model

Taking an item is enforced by state: the detail string enters `taken_location_items` and disappears from narrator, ruling, and extraction context. The seed fact itself is never deleted — it remains in `world.locations` for audit and turn viewer, and the mechanism is reversible if a future design wants items returned to a location.

Items the narrator invents (not seed-declared) remain soft-consistency: acceptable, since ruling only shows seed-declared items and the narrator self-corrects from prior narration for anything else.

### Implementation Phases

**Phase 1: Model + seed changes**
- Add `scene_details: list[str]` (max_length=3) to `KeyLocation`
- Add `taken_location_items: list[str]` to state
- Update seed prompt: up to 3 details per location, ≥1 item-like, no PC inventory duplication

**Phase 2: Prompt integration**
- Render filtered `scene_details` in F-31's Location Context section (narrate)
- Add ruling context + impossibility leniency guidance (owned here)

**Phase 3: Extraction + delta builder**
- Pass un-taken location details to step2b extraction prompt; add pickup-matching guidance
- Delta builder: append matched detail to `taken_location_items` on pickup
- Validate extraction correctly handles location item pickup

**Phase 4: Validation + testing**
- Checker: seed locations have scene_details populated, ≥1 item-like
- Checker: taken items filtered from narrate/ruling/extraction context
- Eval: narrator exposition quality with location items
- Eval: ruling awareness of location items for impossibility
- Eval: extraction correctly handles location item pickup; no double-take narration
- Docs: update `docs/architecture/state-models.md` (KeyLocation.scene_details, taken_location_items), `docs/repomap.md`

### Risks

1. **Seed complexity:** scene_details must include ≥1 item-like entry per location. Mitigation: seed prompt gives clear examples of item vs environmental details; max 3 strings keeps dimensionality manageable.

2. **Match failures:** If the extractor takes a seed item but doesn't match it to the detail string, the item stays visible (stale context) and the PC has a duplicate-adjacent item. Mitigation: extraction prompt includes the exact detail strings; eval covers the no-double-take case. Worst case degrades to F-32's original soft-consistency behavior.

3. **Extraction ambiguity:** Pickup of location item vs new item discovery. Mitigation: detail context + matching guidance in the extraction prompt.

4. **Prompt context bloat:** Details add tokens every turn. Mitigation: inside F-31's aggregate cap, taken items filtered; measure token delta during implementation.

### Deferred Items

- **Structured item model:** seed-declared strings are enough; item IDs/amounts/durability are a separate ticket if ever needed
- **Runtime location inventory extraction:** seed-declared only, no extraction of new location items at runtime
- **Item durability/degradation**
- **Multiple copies of location items:** single instances
- **Returning items to locations:** mechanism is reversible but drop-back is not designed
- **UI changes:** turn viewer may surface taken items later
- **Dynamic item generation:** all items seed-declared, no lazy generation

### Dependencies on Other Designs

- **Location Expansion Design (F-31)** — unified KeyLocation schema, Location Context section + aggregate token cap, first-visit flag (prerequisite; ships first)
- **Seed Two-Step Design** — seed generation pipeline that `scene_details` extends
- **Seed Worldbuilding Redesign** — funnel ordering, key locations seed generation
