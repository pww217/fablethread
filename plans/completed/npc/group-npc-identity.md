# Group NPC Identity: Distinguishing Descriptors

## Purpose

Make group NPCs (e.g., "Two sailors") feel like specific, distinguishable individuals in the narrative while preserving exact quantity tracking for state management.

## Problem Statement

Group NPCs are identified by quantity-stripped base type (e.g., "sailors_watch" for "Two sailors"). The narrator sees this in the roster and reuses the same ID whenever any sailors appear, even if the narration describes different sailors. This creates ambiguity: the player can't tell if "Two sailors" in turn 5 are the same sailors from turn 3 or new ones. The quantity rule works too well — it collapses all sailors into one generic slot with no distinguishing identity.

## Constraints

- Quantity must remain in `name` field (e.g., "Two sailors") — this is the state-tracking contract.
- The `name` field appears in UI (sidebar, compendium), so it must stay short.
- Distinguishing details go in `bio` — the roster template already renders bio in the NPC section visible to the narrator.
- No new fields or models — this is purely prompt-level guidance changes.
- Existing saves must continue to work (backward compatible).
- No quantity field in the NPC model — quantity is embedded in name only.

## Non-goals

- Adding a quantity field to the NPC model.
- Changing the group NPC ID dedup logic in `npcs.py` or `extraction.py`.
- Changing the roster template structure.
- Adding distinguishing fields to the Pydantic models.
- Fixing named NPC identity issues (out of scope).

## Solution

Three coordinated prompt changes:

1. **Seed system prompt:** Group NPC bios must include distinguishing features for each individual in the group (not generic filler). The name stays short with quantity + type.
2. **Scene extractor system prompt:** When extracting group NPCs, the bio should capture distinguishing descriptors from narration. The name stays short. The extractor should also guide the narrator to write distinguishing features when introducing new groups.
3. **Narrator system prompt:** When introducing a new group, describe distinguishing features in the narration (which the extractor captures into bio). When reintroducing an existing group NPC, reference the bio's distinguishing details by name rather than collapsing to the generic type.

Expected outcome: Each group NPC entry in the compendium has a short name ("Two sailors") and a bio that describes the individuals ("A tall man with a scarred brow and a short one with nervous hands, both crewmen on watch duty."). The narrator sees these in the roster and can reference them ("the scarred sailor and his nervous companion"), making reuse feel like the same people rather than any two sailors.

## Firm decisions

1. Name stays short: quantity + type only (e.g., "Two sailors"). No descriptors in name.
2. Distinguishing details go in bio. Bio is the identity layer for group NPCs.
3. The roster template (`_npc_roster.j2`) already renders bio — no template changes needed.
4. No code changes to `npcs.py`, `extraction.py`, or models.
5. Pattern for group bio: "Individual 1 description + Individual 2 description + [group role/context]."
6. The narrator sees the full roster with bios — it already has all the data it needs, just doesn't use it.

## Risks, Ambiguities, and Blockers

- **Bio length:** Group bios with multiple individuals could get long. Need to cap at 1-2 sentences per the existing bio rule.
- **Extractor accuracy:** The extractor must reliably pull distinguishing details from narration into the bio. If the narrator writes "Two sailors" without descriptors, the bio will be generic and the fix doesn't work.
- **Narrator compliance:** The narrator must actually reference bio details when reintroducing groups. The existing "reuse before creating new" guidance could still cause it to collapse to generic type.
- **Existing saves:** Old saves won't have distinguishing bios for group NPCs. The fix works forward — old saves will gradually get better bios as the extractor runs.

## Status

`completed`

## Phases

3 phases: (1) Seed system prompt — group NPC bio guidance, (2) Scene extractor system prompt — group NPC extraction guidance, (3) Narrator system prompt — group NPC reuse and introduction guidance.

## Implementation — Phase 1: Seed system prompt — group NPC bio guidance

### Context files to load
- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`

### Detailed steps

#### Step 1.1 — Add group NPC bio guidance to seed system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** In the "NPC field requirements" section (around line 92), add guidance for group NPC bios. The current guidance (lines 92-94) covers name format and ID rules but says nothing about bio content for groups.

Add after the existing group NPC guidance (after line 94):

```
- **Group NPC bio:** Must describe the individuals in the group — at least one distinguishing feature per person (appearance, demeanor, or visible trait). Generic filler like "crewmen on duty" is insufficient. Example: `"A tall man with a scarred brow and a short one with nervous hands, both crewmen on watch duty."` The name field states the count; the bio gives them identity.
```

**Why:** The seed is the first place group NPCs get their identity. Without distinguishing bios in the seed, the first turn starts with generic groups that the narrator has nothing to reference.

**Validation:** Read the file and verify the new guidance is placed in the correct section, after the existing group NPC rules and before the personality archetype table.

### Tests to write or update

None — tests are temporarily removed during refactor.

## Implementation — Phase 2: Scene extractor system prompt — group NPC extraction guidance

### Context files to load
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`

### Detailed steps

#### Step 2.1 — Add group NPC bio extraction guidance

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** In the "NPC field requirements" section (around line 84), add guidance for group NPC bio extraction. The current guidance (line 84) covers name format but not bio content for groups.

Add after the existing group NPC guidance (after line 85):

```
- **Group NPC bio:** When the narration describes distinguishing features of individuals in a group (appearance, demeanor, visible traits), capture them in the bio. Format: "Individual 1 description + Individual 2 description + [group role/context]." If the narration provides no distinguishing details, write a minimal bio that at least establishes the group's visible presence (e.g., "Crewmen on watch duty, standing near the hatch"). Never leave a group NPC bio as generic filler like "is a sailor" or "present in the scene."
```

**Why:** The extractor is responsible for populating the compendium from narration. If it doesn't pull distinguishing details into the bio, the narrator has nothing to reference on future turns.

**Validation:** Read the file and verify the new guidance is placed in the correct section, after the existing group NPC rules.

### Tests to write or update

None — tests are temporarily removed during refactor.

## Implementation — Phase 3: Narrator system prompt — group NPC reuse and introduction guidance

### Context files to load
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/sections/_npc_roster.j2`

### Detailed steps

#### Step 3.1 — Add group NPC introduction guidance

**File:** `ccya/prompts/narrate_system.j2`

**What:** In the "NPCs" section (around line 59), add guidance for introducing new group NPCs. The current "NPC RE-USE" guidance (line 59) tells the narrator to reuse known NPCs before creating new ones, but doesn't tell it to give new groups distinguishing features.

Add after the "NPC RE-USE" paragraph (after line 59), as a new paragraph:

```
**NEW GROUPS:** When introducing a new group of unnamed NPCs, describe at least one distinguishing feature per individual in the narration — appearance, demeanor, visible trait, or mannerism. The scene extractor will capture these into the group's compendium bio. Example: "Two sailors — a tall man with a scarred brow and a short one with nervous hands — stand near the hatch." This makes future reuse feel like the same people, not any two sailors.
```

**Why:** The narrator is the source of narration. If it doesn't write distinguishing details, the extractor has nothing to pull into the bio, and the group remains generic.

**Validation:** Read the file and verify the new guidance is placed in the correct section, after the NPC RE-USE paragraph and before the NPC BEHAVIOR DRIVERS section.

#### Step 3.2 — Add group NPC reuse guidance

**File:** `ccya/prompts/narrate_system.j2`

**What:** In the "NPCs" section, add guidance for reintroducing existing group NPCs. The current guidance tells the narrator to reuse known NPCs but doesn't tell it to reference their distinguishing features.

Add after the NEW GROUPS paragraph (or as a separate paragraph):

```
**REINTRODUCING GROUPS:** When an existing group NPC reappears, reference their distinguishing features from the compendium bio rather than collapsing to the generic type. If the roster shows "Two sailors — A tall man with a scarred brow and a short one with nervous hands," say "the scarred sailor and his nervous companion" or "the two watchmen you met earlier" — not just "two sailors." This makes reuse feel like the same people, not new generic characters.
```

**Why:** The narrator sees the full roster with bios in `_npc_roster.j2`. Currently it ignores the bio details and just sees "Two sailors." This guidance tells it to use the bio to ground reuse in actual identity.

**Validation:** Read the file and verify the new guidance is placed in the correct section, after the NEW GROUPS paragraph.

### Tests to write or update

None — tests are temporarily removed during refactor.
