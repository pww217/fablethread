# Deepen Seed Opening — Exposition, Pacing, NPC Compendium

## Status
`completed`

## Phases
2 phases covering: (1) prompt contract changes (system + user templates + pack.py docstring), (2) numeric constraint alignment (scenario.yaml ranges + seed.py stale rules).

## Issue

Seed-generated openings converge on a pattern: mid-crisis immersion with minimal orientation, 275–550 words, 2 in-scene NPCs with weak-to-nonexistent personal ties to the PC, and an empty compendium. This robs the opening of depth, stakes, and texture. The player is dropped into urgency without understanding their environment, their relationships, or what they could meaningfully interact with.

Three root causes:
1. The opening narration guidance prioritises "start mid-scene, feel like chapter two" over exposition and environmental detail
2. The prompt explicitly forbids compendium population at seed time ("LLM must NOT populate compendium.npcs — engine manages both") — so only the 2 in-scene NPCs exist
3. The `relation` field on present NPCs has weak prompting — the LLM often fills it with generic role descriptions ("is their squadmate", "works at the settlement") rather than specific personal history

## Solution

Restructure the seed prompt to produce richer, slower openings with meaningful NPC relationships and a populated world. Three changes:

1. **Opening narration**: Replace "start mid-scene, feel like chapter two" with a three-movement structure: sensory close-up (orientation to a specific object/texture/sound) → exposition paragraph (what's around to examine, loot, interact with) → crisis/gameplay moment (the tension arrives or is revealed). Raise word range to 400–700.

2. **Compendium at seed time**: Remove the prohibition on seed-time compendium population. Instruct the LLM to generate 4–5 total NPCs: 2 in `present_npcs`, 2–3 in `compendium.npcs`. The compendium NPCs have `name`, `title`, `bio` — they exist "out there in the world" for later discovery. This uses the existing `SeedCompendium` model which already handles compendium data correctly through the pipeline.

3. **NPC relation strengthening**: Sharpen the `relation` field prompting. Instead of "narrative role of this NPC relative to PC," require one in-scene NPC to have a specific personal connection: debt owed, shared history, emotional bond, or key story intersection. Their `bio` must reference the PC by name.

## Firm decisions

1. **No new fields, no new models, no new systems.** All changes are prompt text only + numeric range updates + removal of stale constraints. The existing `SeedCompendium` model, `SeedEnvelope` schema, and `present_npcs` field are sufficient.
2. **4–5 total NPCs:** exactly 2 in `present_npcs`, 2–3 in `compendium.npcs`. The LLM decides which NPCs are in-scene vs known-but-absent. No flags, no presence markers on compendium entries.
3. **Opening structure is guidance, not a schema.** The three-movement structure (close-up → exposition → crisis) lives in prose guidance, not as separate JSON fields. No new `environmental_details` or `exposition` fields.
4. **Personal tie is prompting only.** No `relationship` enum, no new data field. One present NPC must have a `relation` value that specifies shared history with the PC, and optionally a `bio` that references the PC by name. The other NPC carries external pressure (world/institution/conflict tension) — existing rule, just better enforced.
5. **Prose word range raised to 400–700** across all 6 dynamic packs.

## Non-goals

- No changes to the turn pipeline (narrate.py, extraction, storytell)
- No changes to the seed.py generation logic (only removing stale comments/constraints)
- No new Pydantic models, no new state fields
- No changes to generate_pack (custom pack generation)
- No changes to static packs (hand-authored seed_state.yaml packs)
- No tests (tests temporarily removed per AGENTS.md)

## Risks, Ambiguities, and Blockers

- **LLM compliance with compendium guidance:** The LLM will need to produce 2 fully-detailed present NPCs + 2–3 compendium NPCs in a single generation pass. This may strain output quality if the model doesn't distribute attention well. Monitor seed generation logs for thin compendium entries (single-sentence bios, missing titles).
- **Opening length tradeoff:** 400–700 words is substantially longer. Compaction and chronicle tail trimming may cut these openings sooner. The existing token budget cascade handles this (trim_messages drops oldest non-system turns first), but very long openings will be the first thing dropped when token pressure builds.
- **Three-movement structure is new prose guidance:** The LLM has been trained to "start mid-scene." The new guidance tells it to start with quiet sensory detail _before_ the crisis. This is a reversal — expect some seeds to produce hybrid structures (brief close-up → immediate crisis) before the model adapts.
- **SeedEnvelope field ordering in output:** The existing retry feedback in seed.py (lines 287, 311) is generic. If the LLM produces compendium NPCs with bad data naming, the current retry messages won't help diagnose the specific issue. Not in scope to fix, but worth noting.
- **No incompatible_with validation on compendium NPCs:** The in-scene NPCs already have the weak `relation` field. Compendium NPCs get `name`, `title`, `bio` only — no guarantee they're thematically aligned with the chosen pools. This is acceptable for seed-time worldbuilding; the scene extractor and narrator will filter for relevance during play.

## Implementation — Phase 1: Prompt contract changes

### Context files to load
- `ccya/prompts/generate_seed_system.j2` (full file, 199 lines)
- `ccya/prompts/generate_seed_user.j2` (full file, 87 lines)
- `ccya/pack.py` — SeedEnvelope docstring only (lines 76–87)
- `docs/repomap.md` — "Seed emotional context → narrator consumption" section (lines 115–119) to verify narrator consumption paths

### Detailed steps

#### Step 1.1 — Remove compendium prohibition, add compendium generation guidance

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Replace the "Absolute rules" line 11 (`meta.compendium_touch_order absent or []. Engine manages both.`) with new guidance:

```
- Generate 4–5 named NPCs total: exactly 2 in scene.present_npcs and the remaining 2–3 in compendium.npcs with {name, title, bio}. The compendium NPCs exist "out there in the world" — they are known to the PC but not present in the opening scene. Their bios should establish them as real people with roles in the world, not as future quest-givers. Do NOT include motivation, fear, or leverage fields on compendium entries — engine manages those. Do NOT set meta.compendium_touch_order — engine manages that.
```

**Why:** This is the single prompt-level change that enables compendium population at seed time. The existing pipeline already handles compendium data correctly (seed.py `_sanitize_envelope()` processes compendium entries at lines 52–59; `SeedState.compendium` serialises and persists correctly). The only thing blocking it is the prompt telling the LLM not to do it.

**Validation:** Template renders without Jinja errors.

#### Step 1.2 — Restructure opening narration guidance

**File:** `ccya/prompts/generate_seed_system.j2`, `opening_narrative` section (lines 156–157)

**What:** Replace the entire `opening_narrative` prose guidance paragraph with:

```
## opening_narrative
{{ c.prose_word_range[0] }}–{{ c.prose_word_range[1] }} words. Second person, present tense.

Structure the opening in three movements:

1. **Close-up** (~80 words): Start with a specific sensory detail — an object, texture, sound, smell, or weather. The PC's immediate physical reality before any crisis is declared. Orient the player through the character's senses. No summary, no biography, no "you are a..."

2. **Exposition** (~100 words): What is around the PC to see, examine, touch, or potentially interact with? Describe 2–4 specific environmental details: a locked footlocker, a cracked mirror, a discarded letter, a tool left behind, a stain on the wall, an open window. These are things the player could choose to engage with. Do NOT describe these as "things you could examine" — weave them into the scene as natural details.

3. **Crisis / gameplay moment** (remaining words): The tension arrives or is revealed. Present NPCs act. The moment the player must respond to. This is where the "mid-scene" feel belongs — earned after the orientation.

Movement guidance:
- The close-up and exposition together should feel like chapter one, building atmosphere and place before revealing danger.
- Bold NPC names on first introduction. Bold inventory item names on first use.
- Let the campaign arc tension surface through what the player observes rather than what the narrator announces.
- NPCs should appear in action, not be introduced.
- The opening should feel like chapter one, not a mid-chapter drop.
```

**Why:** The old guidance ("start mid-scene... feel like chapter two") actively discouraged the orienting exposition that seed openings need. The three-movement structure ensures the player understands where they are and what's around them before engaging with the crisis. The ~180 words of orientation (close-up + exposition) leave 220–520 words for the crisis, which is still substantial.

**Validation:** Template renders without Jinja errors.

#### Step 1.3 — Strengthen NPC relation guidance

**File:** `ccya/prompts/generate_seed_system.j2`, `present_npcs` section (lines 162–169)

**What:** Replace the `present_npcs` prose paragraph with:

```
## present_npcs
{% if npc_count_override and npc_count_override > 0 %}
Exactly {{ npc_count_override }} NPCs that appear in the opening scene — {id: snake_case, name, title, notes, bio, relation}. These are the characters the player meets immediately.
{% else %}
Exactly 2 NPCs that appear in the opening scene — {id: snake_case, name, title, notes, bio, relation}. These are the characters the player meets immediately.
{% endif %}

Of the 2 in-scene NPCs, at least 1 must have a specific personal connection to the PC: a debt owed, a shared history (served together, grew up together, survived something together), an emotional bond (family, old friend, former lover), or a key story intersection (they are the reason the PC is here, they hold something the PC needs). Their `relation` field must specify this tie — not a generic role description. Their `bio` should reference the PC by name where the shared history demands it.

The other in-scene NPC carries immediate external pressure from the world, institution, or conflict pressing on the scene — their `relation` describes this institutional or situational connection (e.g., "represents the faction that controls this checkpoint", "is the officer whose orders you're failing"). Together the two NPCs embody: personal stakes (one NPC) + external pressure (the other NPC).

## compendium.npcs
Generate exactly 2–3 additional NPCs in compendium.npcs (keyed by snake_case id, with {name, title, bio}). These are characters the PC knows of or has encountered before — they exist in the world but are not present in the opening scene. Their bios should tie them to the world's factions, locations, or pressures rather than to the immediate opening situation. They may become allies, antagonists, sources of information, or neutral parties as the story unfolds.

Do NOT add `relation`, `notes`, `motivation`, `fear`, or `leverage` to compendium entries. Those fields are engine-managed at runtime. Compendium entries get: `name`, `title`, `bio` (and optional `allegiance` if relevant). `allegiance` is a faction id from the world pack.
```

**Why:** The existing `relation` field already exists on present NPCs but the prompting is weak ("narrative role of this NPC relative to PC"). The new guidance makes the personal/external split explicit and gives concrete examples. The compendium section tells the LLM exactly what fields to generate and what to omit, preventing schema drift.

**Validation:** Template renders without Jinja errors.

#### Step 1.4 — Add compendium generation context to user prompt

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Add a new section after the existing `## npc_generation_context` block (after line 60):

```
## compendium_generation (for the 2–3 NPCs not in the opening scene)
Use the same faction context and world facts above to create NPCs that feel organic to this world. Compendium NPCs should fill roles that the world needs: faction members, civilians, power figures, or people caught between the forces described in world_state/recent_events. Their bios should establish what they want and why they matter — not as explicit agendas, but as subtext a player would infer from knowing them.

At least one compendium NPC should have a loose connection to a faction or world_state pressure — not as a plot hook, but as a person whose life is visibly shaped by that force.
```

**Why:** The user prompt provides the raw context material (factions, world facts, tone). The compendium section tells the LLM how to use that material for compendium NPCs rather than treating them as disconnected name+title+bio entries.

**Validation:** Template renders without Jinja errors.

#### Step 1.5 — Update SeedEnvelope docstring

**File:** `ccya/pack.py`, `SeedEnvelope` class docstring (lines 76–81)

**What:** Replace the docstring:

```python
class SeedEnvelope(BaseModel):
    """Output schema for the generate_seed LLM call.

    The LLM may populate compendium.npcs at seed time with 2–3 additional
    NPCs (name, title, bio). These are known-to-but-not-present in the
    opening scene. Do NOT set meta.compendium_touch_order — engine manages
    that field at runtime.
    """
```

**Why:** The old docstring said "MUST NOT populate compendium.npcs" which contradicted the new prompt guidance. The new docstring reflects the updated contract.

**Validation:** Import check passes.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required

- `ccya/pack.py` — update SeedEnvelope docstring
- `ccya/prompts/generate_seed_system.j2` — multiple section updates (compendium prohibition removed, opening narration restructured, NPC relation strengthened, present_npcs section expanded, compendium.npcs section added)
- `ccya/prompts/generate_seed_user.j2` — add compendium_generation section

## Implementation — Phase 2: Constraint alignment

### Context files to load
- All 6 scenario.yaml files (one per pack):
  - `packs/default/allied-ww2/scenario.yaml`
  - `packs/default/zombie-survival/scenario.yaml`
  - `packs/default/space-western/scenario.yaml`
  - `packs/default/sengoku-japan/scenario.yaml`
  - `packs/default/noir-1930s/scenario.yaml`
  - `packs/default/golden-piracy/scenario.yaml`
- `ccya/engine/seed.py` lines 186–206 (`_soft_validate_seed`) to check word range validation
- `docs/repomap.md` — "Key constants" section for any related caps

### Detailed steps

#### Step 2.1 — Update prose_word_range in all 6 packs

**Files:** All 6 `packs/default/*/scenario.yaml` files

**What:** In each scenario.yaml, change `prose_word_range: [275, 550]` to `prose_word_range: [400, 700]`. (Some packs may have slightly different values — update them all to [400, 700].)

Current values per pack:
- allied-ww2: `[275, 550]`
- zombie-survival: `[275, 550]`
- space-western: verify from source
- sengoku-japan: verify from source
- noir-1930s: `[275, 550]`
- golden-piracy: verify from source

**Why:** The old range (275–550) was tight for the old "start mid-scene" guidance. The new three-movement structure needs ~180 words for orientation alone, leaving 220–520 for the crisis. 400–700 provides sufficient room for both without ballooning the opening past what compaction can handle.

**Validation:** YAML parses correctly in each file; `python -c "from ccya.pack import load_pack; print(load_pack('zombie-survival').scenario.constraints.prose_word_range)"` returns `[400, 700]`.

#### Step 2.2 — Remove stale compendium constraint comments in seed.py

**File:** `ccya/engine/seed.py`

**What:** Two changes:

1. Remove the `# Preserve compendium NPCs generated by the seed LLM; clear touch order` comment and its surrounding code block at lines 339–341 — but only the `del` for `compendium_touch_order`. Wait — actually, the touch_order deletion at line 341 is fine: `if "compendium_touch_order" in envelope.seed_state.meta: del envelope.seed_state.meta["compendium_touch_order"]`. The comment says "clear touch order" which is correct. But the comment at line 339 says "Preserve compendium NPCs generated by the seed LLM" — this was written when compendium population was prohibited, so the comment was aspirational/misleading. Update the comment.

2. Check `_build_generate_seed_messages` at lines 158–177 for any comment or variable name that references "both" (compendium + touch_order being engine-managed). If found, update to reflect the new contract.

**Why:** Minor housekeeping — the code already handles compendium NPCs correctly (the sanitisation at lines 52–59 processes them, the model serialises them, the storage path persists them). Only stale comments need updating to match the new prompt contract.

**Validation:** `git diff` shows only comment/commented-code changes in seed.py.

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required

- `packs/default/*/scenario.yaml` — prose_word_range changed from [275, 550] to [400, 700] (6 files)
- `ccya/engine/seed.py` — update stale compendium-related comments
