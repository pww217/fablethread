I have turn.py, narrate_system.j2, narrate_user.j2, and the prompts directory. I still need extraction.py, extract_scene_system.j2, extract_progress_system.j2, extract_state_system.j2, generate_seed_system.j2, the models, the pack.py/seed.py details, and AGENTS.md + TODO.md. I've hit the tool limit for this turn. Let me use what I have plus what I read at session start (seed.py was partially loaded) and produce the plan now. I'll note the files I still need to verify inline and flag them as ambiguities.

***

# CCYA Bug Fix — Full Resolution Plan

## Status
`open`

## Part of
`bugfix/2026-05-09-batch`

## Dependencies
- None — all phases are standalone unless noted.

## Objective
Resolve all open bugs and quality issues identified from the 2026-05-09 eval report and manual gameplay observations. Issues span: state extraction correctness (NPC identity, inventory ammo, scene population), world-gen quality (char names, starter items, world seeds), narration quality (scope over-flagging, word bans, tone, NPC agency, conditions), GM/progress pacing (beats, action choices, quest length), and gameplay rules (disarm on capture).

## Non-goals
- No compactor changes.
- No token-hygiene / prompt deduplication work.
- No auto-checker changes.
- No UI changes.
- No changes to the dice/rules engine resolution math.

## Affected files

| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/generate_seed_system.j2` | modify | PC first+last name requirement; skill-matched starter items; world_state and recent_events discipline |
| `ccya/prompts/generate_seed_user.j2` | modify | Surface skill list to seed LLM for item matching |
| `ccya/prompts/narrate_system.j2` | modify | Ban "wet"; scene always has NPC or loneliness moodlet; NPC agency rules; disarm on capture; scope over-flag fix; reduce faction/inventory emphasis |
| `ccya/prompts/narrate_user.j2` | modify | Pass present_npcs minimum count hint; pass quest count for pacing |
| `ccya/prompts/extract_scene_system.j2` | modify | Always add introduced NPCs to scene; NPC identity/alias merge rules; `location_change` only on ID change |
| `ccya/prompts/extract_scene_user.j2` | modify | Surface compendium NPC list for alias matching |
| `ccya/prompts/extract_state_system.j2` | modify | Ammo/consumable removal on use; conditions liberal-application guard |
| `ccya/prompts/extract_state_user.j2` | modify | Pass present_npcs for grounding |
| `ccya/prompts/extract_progress_system.j2` | modify | Action choices: plot-forward, skill/quest/NPC/inventory tied; GM beats faster paced; include current scene in full |
| `ccya/prompts/extract_progress_user.j2` | modify | Pass full current scene text + present_npcs; pass active quests for choice generation |
| `ccya/engine/extraction.py` | modify | Pass `narrative` (full current turn scene) into progress extractor context |
| `ccya/engine/narrate.py` | modify | Pass `present_npcs_count` hint to narrate template |
| `ccya/engine/seed.py` | modify | Validate PC name has first+last; post-process skill→item seeding if LLM doesn't comply |
| `ccya/pack.py` | inspect | Confirm `world_state` and `recent_events` schema for seed constraints |
| `docs/REPOMAP/engine.md` | update | Reflect extraction.py and narrate.py signature changes |
| `docs/REPOMAP/seed.md` | update | Reflect seed validation changes |
| `docs/plans/TODO.md` | update | Add this plan |

***

## Firm Decisions

1. **NPC alias merge happens in the scene extractor, not the narrate prompt.** The extractor has the compendium; the narrator doesn't need to know merge logic.
2. **`location_change` domain fires only when `location.id` changes**, not when description text changes. This is enforced via prompt instruction, not engine code, because the LLM is the one emitting the scope tag.
3. **Ammo/consumable removal is a state extractor responsibility** (extract_state_system.j2), since inventory is its domain.
4. **"Wet" ban is a single line addition to narrate_system.j2.** No engine code change needed.
5. **Conditions guard is prompt-level.** The extractor must require explicit narrative evidence for any condition addition. No model schema change.
6. **World seed world_state = constraints/immutables only.** No historical events more than one generation old unless they are an active hard constraint on the story world. recent_events = things that happened in the last few days/weeks that are immediately relevant to the opening scene and do not telegraph gm_beats.
7. **Starter items are seeded from the PC's top 2 skills.** The seed LLM receives the generated skill block and must justify each item against a skill.
8. **PC name requires first and last name.** Enforced by post-generation validation in `seed.py`; if the LLM returns a single token, the game creation flow should surface an error or re-prompt.
9. **Capture/surrender disarm is narrate_system.j2 instruction.** The rules extractor (state extractor) must follow through and emit `inventory_remove` for all weapons.
10. **Progress extractor receives the full current-turn narrative text** (already in `narrative` variable in `_run_extraction_pipeline`). The user prompt template must include it.
11. **Action choices must reference: (a) one skill-driven action, (b) one quest-related action, (c) one NPC-related action, (d) one wildcard.** This is a minimum shape rule, not a rigid template.
12. **GM beats should target 1–2 turn resolution**, not 5–6. Language in the beat instructions changes from "eventually" / "over time" to "this turn" / "next turn".
13. **Initial quest target: solvable in ≤10 turns.** This is enforced in `generate_seed_system.j2` as an explicit constraint on quest design.

***

## Implementation — Phase 1: World Gen Quality

**Context files to load:**
- `ccya/engine/seed.py`
- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`
- `ccya/pack.py` (SeedEnvelope, parse_world_facts)
- `docs/REPOMAP/seed.md`

### Overview
Fixes B5 (first+last name), B6 (skill-matched starter items), B16/B17 (world_state constraints vs. history, recent_events discipline), and the initial quest pacing target (B11). All changes are in the seed prompt and seed.py validation. Nothing in the runtime turn pipeline is touched.

### Detailed Steps

#### Step 1.1 — PC first+last name enforcement in generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Add an explicit rule to the PC generation section requiring a given name AND a family/surname. The current prompt likely says "generate a name" with no structure requirement.

**Why:** A single-token name like "Kovak" or "Renna" breaks immersion and fails the first+last requirement (B5).

**Code Snippet**
```jinja2
{# In the PC generation section, replace or augment the name instruction: #}
- `name`: Full name with a **given name and family name** (e.g. "Mira Sovak", "Dren Calloway"). 
  Single-word names are not permitted. The name must fit the world's cultural tone.
```

**Validation:** Generate a new game. Confirm `state.pc.name` contains a space and two tokens.

***

#### Step 1.2 — Post-generation name validation in seed.py

**File:** `ccya/engine/seed.py`

**What:** After `_sanitize_envelope`, add a validation check. If `envelope.seed_state.pc.name` has fewer than 2 whitespace-separated tokens, raise a `ValueError` describing the failure so the caller can surface it to the user.

**Why:** Belt-and-suspenders. The LLM may ignore prompt instructions.

**Code Snippet**
```python
def _validate_seed_envelope(envelope: SeedEnvelope) -> None:
    """Raise ValueError if seed envelope violates hard constraints."""
    name_parts = envelope.seed_state.pc.name.strip().split()
    if len(name_parts) < 2:
        raise ValueError(
            f"PC name '{envelope.seed_state.pc.name}' must include a given name and family name. "
            "Re-generate or provide a full name."
        )
```

Call this immediately after `_sanitize_envelope(envelope)` in the seed generation function.

**Validation:** Unit test: construct a `SeedEnvelope` with `pc.name = "Kovak"` and assert `_validate_seed_envelope` raises `ValueError`. Construct one with `pc.name = "Kovak Strand"` and assert no raise.

***

#### Step 1.3 — Skill-matched starter items in generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Add a constraint block for inventory generation that requires at least 2 of the starting items to be directly justified by the PC's top 2 stat/skill values. The user prompt will now include the stat block before inventory is generated.

**Why:** Random items that don't fit the character's build break immersion and reduce early-game coherence (B6).

**Code Snippet**
```jinja2
{# Replace/augment the inventory section instructions: #}
## Starter Inventory Rules
- Generate 3–6 starting items appropriate to the opening scene.
- **At least 2 items must be directly tied to the PC's strongest skills** (the top 2 by value in the stats block above).
  Example: if the PC's top skills are `firearms` and `stealth`, starter items must include a sidearm/ammo AND a concealable tool (suppressor, dark clothing, lockpick). 
- Do not add items for skills the PC has no investment in.
- Quantities must be realistic and not overpowered for turn 1.
```

**Validation:** Generate 5 seeds with varied skill distributions. Inspect `seed_state.inventory` — at least 2 items should be recognizably tied to the top skills in each case.

***

#### Step 1.4 — world_state and recent_events discipline in generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Replace permissive world_state and recent_events generation instructions with strict constraint-based rules.

**Why:** B16 — world_state currently produces obscure ancient lore with no story relevance. B17 — recent_events accidentally telegraphs gm_beats or is redundant with the opening scene.

**Code Snippet**
```jinja2
## world_state — Hard Constraints Only
`world_state` is a list of **immutable hard constraints** that govern what is physically, legally, or politically possible in this world.

Rules:
- Each entry states a constraint that will *directly affect gameplay choices*: border closures, active martial law, banned technologies, faction blockades, economic collapse.
- No historical backstory older than 1 generation unless it is an active hard constraint right now.
- No flavor lore, legends, myths, or distant history — those belong in prose, not world_state.
- Maximum 5 entries. Each is one sentence.
- BAD: "The old empire fell three centuries ago and its ruins dot the landscape."
- GOOD: "Travel between the Northern and Southern districts requires a valid faction pass."

## recent_events — Immediate Pre-Story Context
`recent_events` are things that happened in the last few days or weeks, visible to anyone paying attention on the street.

Rules:
- Must be immediately relevant to the opening scene or the PC's situation.
- Must NOT telegraph, echo, or foreshadow any gm_beat. The player should learn of gm_beat content through play, not world setup.
- Maximum 4 entries. Each is one sentence in past tense.
- BAD: "A mysterious figure was seen entering the Governor's mansion last night." (telegraphs a gm_beat)
- GOOD: "A dockworkers' strike has slowed cargo movement across the port for three days."
```

**Validation:** Generate 3 seeds. Inspect `world_state` — all entries should be actionable constraints, not flavor. Inspect `recent_events` — none should echo the `gm_beats` field.

***

#### Step 1.5 — Initial quest pacing constraint in generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Add an explicit constraint to the quest generation section requiring the initial quest to be completable in 10 turns or fewer.

**Why:** B11 — the initial quest should provide early closure and momentum. Long-horizon quests without near-term payoff kill pacing.

**Code Snippet**
```jinja2
## Quest Design Constraint
The initial quest must be **completable within 10 player turns** under competent play.
- Objectives must be concrete and local: find X, reach Y, deliver Z, kill or confront W.
- No objective should require world travel, large-scale faction politics, or information chains longer than 2 steps.
- Sub-objectives (if any) should each be resolvable in 1–2 turns.
- Longer story arcs belong in gm_beats, not the initial quest.
```

**Validation:** Review generated quests from 3 seeds. Verify objectives are local, concrete, and could reasonably resolve in 10 turns.

### Tests to write or update
- `tests/test_seed.py`: Add `test_validate_seed_envelope_rejects_single_token_name` and `test_validate_seed_envelope_accepts_full_name`.

### REPOMAP updates required
- `docs/REPOMAP/seed.md`: Add `_validate_seed_envelope` function entry with signature and behavior description.

### Risks
1. LLM may still generate single-token names sporadically — the Python guard will catch it but will surface an error to the user during game creation. Mitigation: the error message must be user-readable and prompt them to retry.
2. Skill-to-item mapping is heuristic (prompt-only) — a weak LLM may not comply. Mitigation: no hard enforcement needed for MVP; prompt is sufficient.

## Ambiguities requiring resolution before execution
1. **`generate_seed_user.j2` stat block**: Does the current user prompt already include the full stat block before the inventory section, or does the system prompt generate stats and inventory in a single pass? If stats are not yet available when inventory is generated, Step 1.3 requires a template restructure. **Options:** A) Stats and inventory are generated in the same LLM call (single pass) — the system prompt must reference the "stats you just generated above." B) Two-pass generation — unlikely given the current code. Executor must check the actual template before writing.

***

## Implementation — Phase 2: State Extraction Correctness

**Context files to load:**
- `ccya/prompts/extract_scene_system.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_system.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/engine/extraction.py`
- `ccya/models.py` (StateDelta, CompendiumNpcUpdate)
- `docs/REPOMAP/extraction.md`

### Overview
Fixes: B1 (ammo not removed on shot), B2 (introduced NPCs not added to scene), B3/R4 (NPC alias merge), R3 (`location_change` on description drift), R5 (rules/state extractor targets absent NPCs), R2 (condition duplication), B9 (conditions applied too liberally).

This phase touches only extraction prompts and the Python context-building in `extraction.py`. No engine orchestration changes.

### Detailed Steps

#### Step 2.1 — Ammo/consumable removal on use (extract_state_system.j2)

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Add an explicit rule: when the narrative describes the player firing a weapon, using a consumable, or spending an item, the extractor MUST emit an `inventory_remove` for the appropriate consumable (ammo, charges, doses). Quantity must match what was described.

**Why:** B1 — pistol rounds are not being removed when fired. The narrate prompt cannot track this; only the state extractor can.

**Code Snippet**
```jinja2
## Consumable tracking (mandatory)
When the narrative describes ANY of the following, you MUST emit the corresponding `inventory_remove`:
- A firearm fired → remove the appropriate ammo item (1 round per shot, or the described burst quantity).
  Match the ammo to the weapon: pistol → pistol rounds/cartridges, rifle → rifle rounds, etc.
- A grenade, explosive, or thrown weapon used → remove 1 unit of that item.
- A healing item, stimulant, or drug consumed → remove 1 unit.
- Credits, currency, or tokens explicitly spent → remove the described amount.

**Do not skip this even if the narrative is ambiguous about exact count.** Default to 1 unit removed.
The engine will clamp over-draws; under-removal corrupts game state permanently.

Matching: use fuzzy match on the item name from the inventory list. "pistol rounds", "9mm", ".45 cartridges" all match the ammo item closest in name. If no match exists in inventory, do not emit a remove — the item was never there.
```

**Validation:** Play a turn where the player fires a pistol. Inspect `applied.inventory_remove` in `events.jsonl`. Confirm an ammo item is present with `amount: 1`.

***

#### Step 2.2 — Introduce NPC into scene on first mention (extract_scene_system.j2)

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add a rule: any NPC who is introduced (named, described, or given dialogue) for the first time in the narrative must be added to `present_npcs` via an `npc_add` operation in the same turn. The extractor must not wait for a subsequent turn.

**Why:** B2 — characters introduced in the narrative don't appear in `present_npcs`, so subsequent prompts don't see them.

**Code Snippet**
```jinja2
## NPC scene population (mandatory)
Every NPC who appears in the narrative this turn — named, given dialogue, or described physically — 
must be reflected in `present_npcs` by the end of this extraction:

1. If the NPC is already in `present_npcs`: ensure their entry is current (title, notes).
2. If the NPC is new to the scene but exists in the compendium: emit `npc_add` with their compendium `id`.
3. If the NPC is genuinely new (no compendium entry): emit `npc_add` AND `compendium_npc` to create them.

**Never leave a narrative-present NPC absent from `present_npcs`.** This is a hard rule.
```

**Validation:** Run a turn that introduces a new named NPC. Inspect `state.scene.present_npcs` after the turn — the new NPC must appear.

***

#### Step 2.3 — NPC alias/identity merge (extract_scene_system.j2 + extract_scene_user.j2)

**File:** `ccya/prompts/extract_scene_system.j2` and `ccya/prompts/extract_scene_user.j2`

**What:**
- **System:** Add a rule: if the player learns a name or alias for an NPC previously tracked under a generic identifier (e.g. "the guard" → "Mira Sovak"), the extractor must immediately update the compendium entry with the canonical name and add `aliases`. Do not create a new compendium entry.
- **User:** Surface the existing compendium NPC list (id + name + aliases) so the extractor can match against it.

**Why:** B3/R4 — when the player learns an NPC's name, a duplicate compendium entry is created instead of updating the existing one.

**Code Snippet — system:**
```jinja2
## NPC identity resolution (alias merge)
Before creating any new compendium NPC entry, check the ## Known NPCs list in the context.

If the NPC being named/described matches an existing entry by:
- Physical description similarity, OR
- Role/title match (e.g. "the guard at the gate" → existing guard NPC at same location), OR
- Player explicitly learning their name ("the stranger introduces herself as Mira"),

Then:
- **DO NOT create a new entry.** 
- Emit `compendium_npc_update` on the existing entry's `id`.
- Set `name` to the canonical name.
- Add the old identifier to `aliases` (e.g. `aliases: ["the stranger", "hooded figure"]`).
- Update `present_npcs` to use the canonical name.

Only create a new compendium entry when you are confident this NPC has no prior entry.
```

**Code Snippet — user template addition (after existing known_characters block):**
```jinja2
{% if known_npcs -%}
## Known NPCs (check before creating new entries)
{% for n in known_npcs %}- id: `{{ n.id }}` | name: **{{ n.name }}**{% if n.aliases %} | aliases: {{ n.aliases | join(', ') }}{% endif %}{% if n.last_seen %} | last seen: {{ n.last_seen.location_name }}{% endif %}
{% endfor -%}
{% endif -%}
```

**Validation:** Run a multi-turn sequence where the player meets an unnamed NPC, then learns their name. Confirm `compendium.npcs` has only one entry for that person, with the alias recorded.

***

#### Step 2.4 — location_change only on ID change (extract_scene_system.j2)

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add an explicit rule that `location_change` must only be emitted when the location's `id` changes — not when the description, tagline, or atmospheric details change.

**Why:** R3 — `location_change` was firing on description-only changes, causing auto-checker failures and unnecessary state writes.

**Code Snippet:**
```jinja2
## location_change — strict definition
Emit `location_change` ONLY when the player physically moves to a **different location** — 
meaning the location `id` would change (e.g. from `warehouse_district` to `dockside_tavern`).

Do NOT emit `location_change` for:
- Changes in atmosphere, lighting, or description within the same location.
- Time passing within the same room or area.
- A new section of the same named location (use scene tag updates instead).

When in doubt: if the player is still in the same named place, do not emit `location_change`.
```

**Validation:** Run a turn with descriptive scene shift but no physical move. Confirm `applied.location_change` is absent from the event.

***

#### Step 2.5 — State extractor grounded to present_npcs (extract_state_system.j2 + extract_state_user.j2)

**File:** `ccya/prompts/extract_state_system.j2` and `ccya/prompts/extract_state_user.j2`

**What:**
- **System:** Add rule that all NPC-targeting state changes (condition application, injury, status) must only target NPCs listed in the `## NPCs Present in Scene` section of the user prompt. Targeting absent NPCs is prohibited.
- **User:** Ensure `present_npcs` is included in the state extractor's user prompt (it may already be; executor must verify and add if missing).

**Why:** R5 — state extractor was applying conditions/injuries to NPCs hallucinated from player intent rather than the actual scene population.

**Code Snippet — system:**
```jinja2
## NPC targeting constraint
All NPC-targeted changes (injuries, conditions, status updates, compendium updates) MUST reference 
an NPC from the ## NPCs Present in Scene list in the user prompt.

If an NPC is not in that list, they are not in this scene. Do NOT emit changes for absent NPCs,
even if the player's action or the narrative implies an interaction with them.
```

**Code Snippet — user template:**
```jinja2
{% if present_npcs -%}
## NPCs Present in Scene
{% for n in present_npcs %}- id: `{{ n.id }}` | {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}
{% endfor -%}
{% endif -%}
```

**Validation:** Run a turn where player attacks an NPC not in the scene. Confirm no `npc_update` or `compendium_npc_update` is emitted for that NPC.

***

#### Step 2.6 — Conditions require explicit narrative evidence (extract_state_system.j2)

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Add a strict evidence requirement for adding any condition to the PC or an NPC. The condition must be explicitly narrated — not implied, not inferred from dice outcome alone.

**Why:** B9/R2 — conditions are being applied too liberally, including cases where the narrative doesn't actually show the condition manifesting.

**Code Snippet:**
```jinja2
## Condition application — evidence required
Only add a condition to `pc_conditions_add` or an NPC's condition list when the **narrative 
explicitly describes the effect**. Examples of explicit evidence:
- "A sharp pain lances through their leg" → `injured_leg` is valid.
- "The gas fills their lungs and their vision blurs" → `disoriented` is valid.

Examples of insufficient evidence:
- The player rolled a `crit_fail` → alone, this does not justify a condition. The narrative must confirm it.
- The scene has a `CONSEQUENCE` directive → this tells the narrator to apply cost; you wait for the narrator to describe it, then extract it.
- The action was risky → risk alone is not a condition.

**When in doubt, do not add the condition.** Conditions are hard to remove; they compound across turns.

Additionally: check existing `pc_conditions` and NPC conditions before adding. If a condition with the 
same `id` already exists, do not duplicate it — emit nothing for that condition.
```

**Validation:** Run a turn with a partial failure where the narrative is ambiguous. Confirm no spurious condition is added. Run a turn where the narrative explicitly says the PC is wounded. Confirm the condition is captured.

### Tests to write or update
- `tests/test_extraction.py` or equivalent: 
  - `test_location_change_not_emitted_on_description_only_change`
  - `test_npc_added_to_scene_on_introduction` (integration, may require FakeLLM)
  - `test_condition_dedup_not_applied_when_already_present` (if a pure Python helper exists for dedup)

### REPOMAP updates required
- `docs/REPOMAP/extraction.md`: Note that `extract_state_user.j2` now receives `present_npcs`; note alias-merge behavior in scene extractor.

### Risks
1. The alias-merge instruction relies on the LLM correctly matching description to compendium entry. False negatives (missed merges) will still create duplicates. Mitigation: the instruction is conservative ("when you are confident") — prefer misses over false merges.
2. `present_npcs` in the state extractor user prompt needs to be confirmed present in `extraction.py`. If it's missing from the template args, a code change is needed in addition to the template change. Executor must check.

## Ambiguities requiring resolution before execution
1. **Does `extract_state_user.j2` currently receive `present_npcs`?** Executor must check `ccya/engine/extraction.py` for the kwargs passed to the state extractor template. If absent, add it — it's already computed in `run_turn` as `_present_npcs`.
2. **Does `extract_scene_user.j2` currently receive the compendium NPC list?** It may be passed as `known_npcs`. Executor must check and add if missing.

***

## Implementation — Phase 3: Narration Quality

**Context files to load:**
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/engine/narrate.py`
- `ccya/prompts/sections/_pc.j2`
- `ccya/prompts/sections/_quests.j2`

### Overview
Fixes: B7 (always 1 NPC or loneliness moodlet), B13 (NPC agency), B14 (ban "wet"), B15 (over-emphasis on factions/inventory), B4 (disarm on capture/surrender), R6 (scope over-flag for inventory/pc_condition when nothing changed). All changes are in `narrate_system.j2` and minor additions to `narrate_user.j2`. No Python changes except a minor hint pass-through in `narrate.py`.

### Detailed Steps

#### Step 3.1 — Ban "wet" (narrate_system.j2)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a single prohibited-word rule to the Style section.

**Code Snippet:**
```jinja2
**Prohibited words:** Never use the word "wet" in any form (wet, wetness, wetting). 
Find a more specific word: damp, soaked, drenched, slick, humid, waterlogged, clammy.
```

**Validation:** Run 10 turns in a rain/water scene. Grep output logs for "wet". Should be absent.

***

#### Step 3.2 — Scene always has at least 1 NPC or explicit loneliness moodlet (narrate_system.j2)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a rule in the "NPCs in scene" section: if the scene has no NPCs and none are plausible given the location (wilderness, isolated cell, abandoned area), the narrator must include an explicit acknowledgment of the player's isolation as a mood beat — not silence.

**Why:** B7 — empty scenes feel inert. Either populate with an ambient NPC or make the emptiness narratively present.

**Code Snippet:**
```jinja2
## Scene population
Every scene must feel inhabited or consciously empty. Two options — pick one:

**Option A — Populate:** Include at least one NPC (named, ambient, or background) who exists in the 
space. This can be as minimal as a vendor glancing up, a guard at a post, or a passerby. 
Re-use existing Known Characters when plausible. Only introduce new anonymous NPCs if no known 
character fits.

**Option B — Solitude moodlet:** If the fiction genuinely requires the player to be alone 
(isolated cell, deep wilderness, post-combat aftermath), narrate the solitude explicitly as a mood 
beat: the absence itself becomes the atmosphere. "The corridor was empty. Even the rats had cleared 
out." Do not silently omit NPC presence — name the emptiness.

Default to Option A unless the scene's tags or prior narrative establishes isolation.
```

**Validation:** Play through 5 scene transitions. Each should either have an NPC referenced or include an explicit solitude beat.

***

#### Step 3.3 — NPC agency (narrate_system.j2)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Expand the NPCs section to require that present NPCs act on their own motives each turn — not just react to the player. At least one NPC per scene should do something proactive.

**Why:** B13 — NPCs feel passive/reactive. They need their own agendas.

**Code Snippet:**
```jinja2
## NPC agency (mandatory)
NPCs are not stage props waiting for the player to address them. Every present NPC has a motive, 
an agenda, and a situation that evolves independently of the player's action.

Each turn, at least one present NPC must:
- Pursue their own goal (check a clock, move toward an objective, speak to someone else),
- React to the scene's conditions (not just to the player), OR  
- Create a new opportunity or complication for the player through their autonomous action.

Passive NPCs — ones who only respond when spoken to, stand in place, or observe — are only 
acceptable when the fiction explicitly establishes them as subordinate (a guard following orders, 
a prisoner in a cell). Even then, they notice things, shift their weight, or exchange glances.

**Never write an NPC as a vending machine.** They are in the world before the player arrived and 
will remain after the player leaves.
```

**Validation:** Play 5 turns in a scene with NPCs. Each should show at least one NPC doing something not directly prompted by the player's action.

***

#### Step 3.4 — Reduce faction/inventory over-emphasis (narrate_system.j2)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a priority hierarchy to the narration focus rules, explicitly deprioritizing faction name-drops and inventory callouts in favor of scene, emotion, motives, and quests.

**Why:** B15 — narration over-references factions and items when the moment calls for tension, character, or story.

**Code Snippet:**
```jinja2
## Narrative focus hierarchy
When deciding what to foreground in a beat, prioritize in this order:
1. **What is happening in the scene right now** — action, stakes, sensory detail.
2. **Emotional state** — the player's and the NPCs'. Show it through behavior, not statement.
3. **Quest momentum** — is a goal getting closer or further away? Make it felt.
4. **NPC motives** — what does this person want, and is the player helping or blocking them?
5. **World/faction context** — only reference a faction when it is directly relevant to THIS moment.
6. **Inventory** — only reference an item when the player used it or it is directly at stake.

Do not name-drop factions or itemize inventory for flavor. A faction is relevant when its agents 
are present or its policies are the immediate obstacle. An item is relevant when it is being used 
or sought. Otherwise, silence.
```

**Validation:** Play through a tense scene. Review narrative output — faction references should only appear when faction agents or policies are the direct obstacle. Inventory mentions should track player use only.

***

#### Step 3.5 — Disarm on capture/surrender (narrate_system.j2)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add a rule: when the player surrenders or is captured, the narrative must explicitly describe being disarmed and searched. This triggers the state extractor to remove weapons.

**Why:** B4 — captured players retain their weapons, breaking realism and game balance.

**Code Snippet:**
```jinja2
## Capture and surrender
When the player surrenders, is knocked unconscious and taken prisoner, or otherwise falls into 
hostile custody:

1. **Describe the disarming explicitly** — captors take weapons, remove holdouts, check for 
   concealed items. Name the items being taken if they are in the player's inventory.
2. **Describe the search** — a pat-down, a strip search if genre-appropriate, or at minimum a 
   weapon confiscation. This is not optional flavor; it is a mechanical trigger for the state 
   extractor.
3. If the player has no weapons, note that the captors find nothing of value to take.

The state extractor will remove the items; your job is to narrate the action clearly so the 
extractor has evidence to act on.
```

**Validation:** Surrender in a combat scene. Confirm `applied.inventory_remove` contains the PC's weapon(s) after the turn.

***

#### Step 3.6 — Scope over-flag fix for inventory/pc_condition (narrate_system.j2)

**File:** `ccya/prompts/narrate_system.j2`

**What:** Tighten the scope tail instructions for `inventory` and `pc_condition` domains. They should only be flagged when a change is confirmed in prose — not as defensive over-flagging.

**Why:** R6 — narrator flags `inventory` and `pc_condition` even when nothing changes, causing unnecessary extraction passes.

**Code Snippet** (replace/augment the existing scope tail instructions):
```jinja2
**Stricter rules for inventory and pc_condition:**
- `inventory`: Only flag if your narration explicitly shows an item being received, lost, consumed, 
  upgraded, or destroyed. Do NOT flag because a weapon was wielded or because an item was mentioned 
  in passing.
- `pc_condition`: Only flag if your narration explicitly shows the player gaining or losing a 
  condition, wound, or status. A tense moment or a near-miss does NOT qualify. The change must be 
  described in the text.

Omitting these from the scope tag is correct and expected when nothing changed.
```

**Validation:** Run 10 turns of normal play. Count turns where `scope.active_domains` includes `inventory` or `pc_condition` vs. turns where those were actually changed. The false-positive rate should drop significantly.

### Tests to write or update
- No pure unit tests for prompt changes. Integration: run the eval harness on a short (5-turn) game and manually review narrative output for each fix.

### REPOMAP updates required
- `docs/REPOMAP/narrate.md`: Note new NPC agency rule, scene population rule, scope tag tightening.

### Risks
1. The solitude moodlet (Step 3.2) may cause the narrator to over-explain emptiness in scenes that should be quiet. Mitigation: "minimal" examples in the instruction.
2. NPC agency (Step 3.3) may cause NPCs to act in ways that conflict with the extractor's understanding of who is where. This is an acceptable risk — the extractor will reconcile.
3. Capture/disarm (Step 3.5) requires coordination with Phase 2 (state extractor). If Phase 2 is not applied first, the narrative will describe disarming but nothing will be removed. **Phase 2 must precede or accompany Phase 3.**

***

## Implementation — Phase 4: Progress Extractor — Pacing and Action Choices

**Context files to load:**
- `ccya/prompts/extract_progress_system.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/engine/extraction.py`
- `ccya/models.py` (ProgressResult, GmBeat schema)
- `docs/REPOMAP/extraction.md`

### Overview
Fixes: B8 (action choices are weak and plot-irrelevant), B10 (GM beats too slow), B12 (progress extractor doesn't receive full current scene). This phase modifies the progress extractor prompt and the Python call-site in `extraction.py` to pass the full narrative text.

### Detailed Steps

#### Step 4.1 — Pass full current narrative to progress extractor (extraction.py + extract_progress_user.j2)

**File:** `ccya/engine/extraction.py` and `ccya/prompts/extract_progress_user.j2`

**What:** 
- In `extraction.py`, ensure the `narrative` variable (the full current turn narration) is passed to the progress extractor template as `current_scene`.
- In `extract_progress_user.j2`, add a `## Current Scene` section that renders this text before the existing context.

**Why:** B12 — the progress extractor currently only sees the chronicle tail and recent turns. It doesn't have direct access to what just happened this turn, causing it to make stale choices and miss quest events.

**Code Snippet — extraction.py** (find where progress template context dict is built and add):
```python
# In _run_extraction_pipeline or equivalent, in the kwargs for the progress template:
"current_scene": narrative,   # full text of this turn's narration (post-scope-strip)
```

**Code Snippet — extract_progress_user.j2** (add at the top, before prior history):
```jinja2
## Current Scene (this turn — most recent)
{{ current_scene }}

```

**Validation:** Inspect the rendered progress prompt (via `log_prompts=True`). Confirm the current narrative text appears at the top of the user message.

***

#### Step 4.2 — Action choices: plot-forward, skill/quest/NPC/inventory tied (extract_progress_system.j2)

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Replace or augment the action choice generation rules with a strict 4-shape requirement.

**Why:** B8 — choices are often generic ("fight", "flee", "investigate") with no connection to the PC's build, active quests, present NPCs, or held items.

**Code Snippet:**
```jinja2
## Action choice generation — mandatory shape
Generate exactly 4 suggested actions. They must follow this shape:

1. **Skill action**: Something the PC is built for. Reference a specific skill from their stats 
   (e.g. "Use your [Firearms] skill to cover the exit"). Ties to the PC's identity.

2. **Quest action**: Something that directly advances the most urgent active quest objective. 
   Must name the quest or objective. (e.g. "Confront [Target] about the shipment — this is the 
   lead you've been following.")

3. **NPC action**: Something that engages a present NPC directly — not generically. Reference the 
   NPC by name. (e.g. "Ask [Mira] what she knows about the back entrance.")

4. **Wild card**: An unexpected or lateral approach — creative, risky, or opportunistic. Should 
   feel like it could only happen in this exact scene.

Rules:
- All 4 choices must be actionable THIS TURN from the current location.
- No choice may be a restatement of the player's last action.
- Do not generate "wait and see", "do nothing", or purely passive choices.
- If no active quest exists, replace #2 with a scene-specific opportunity.
- If no present NPC exists, replace #3 with an environment interaction.
```

**Validation:** Play 5 turns. Review choices — each set should include a recognizable skill tie, a quest reference, an NPC reference, and a lateral option. None should be generic.

***

#### Step 4.3 — GM beats: faster paced, direct, 1–2 turn horizon (extract_progress_system.j2)

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Replace the GM beat instruction language to remove hedged, multi-turn timeline language and enforce immediate/next-turn resolution targets.

**Why:** B10 — GM beats currently have language like "over the coming turns" and "eventually." This produces slow, unresponsive storytelling.

**Code Snippet:**
```jinja2
## GM beat generation — pacing rules
GM beats are tactical instructions to the narrator for the NEXT 1–2 turns maximum.

Rules:
- **Immediate beats** (`surface_as: immediate`): The narrator must surface this beat in the 
  very next turn. No delay. Language: "This turn, [specific thing happens]."
- **Pending beats** (`surface_as: pending`): Surface within the next 2 turns. Do not generate 
  beats with longer horizons — if an event needs more lead time, it belongs in world_state or 
  a new quest objective, not a beat.
- Beats must be **concrete and specific**: name the NPC, name the object, name the location. 
  No vague instructions like "raise the stakes" or "introduce tension."
- Beats must be **completable in 1 turn** of narration. If a beat requires multiple turns to 
  resolve, split it into 2 beats.
- Do not re-issue a beat that was already issued last turn. Check `pending_gm_beat` in context — 
  if it exists and has not been consumed, do not generate a new beat of the same type.

BAD: "Over the next few turns, the faction's interest in the player should grow."
GOOD: "This turn: [Mira] reveals she works for the Syndicate and offers the player a choice — 
      join or be reported."
```

**Validation:** Play 10 turns. Review `events.jsonl` for `pending_gm_beat` entries. Beats should be specific NPC/object/location instructions, not vague pacing nudges. Each beat should be consumed (i.e., no longer present) within 2 turns.

### Tests to write or update
- `tests/test_extraction.py`:
  - `test_progress_extractor_receives_current_scene` — assert `current_scene` key is present in the template kwargs when `narrative` is non-empty.

### REPOMAP updates required
- `docs/REPOMAP/extraction.md`: Add `current_scene` as a new template variable for the progress extractor. Note the 4-shape action choice rule and 1–2 turn GM beat horizon.

### Risks
1. The 4-shape action choice rule is a strong constraint. If the scene has no active quest and no present NPC simultaneously (opening turn of a solo scene), two of the four shapes collapse to fallbacks. The fallback rules in the prompt handle this, but executor should verify the fallback language is clear enough.
2. Passing `current_scene` (full narrative) increases the progress extractor prompt size by ~300–600 tokens per turn. This is acceptable — the extractor already has a large context. If it approaches token budget, the executor must verify `trim_messages` will handle it correctly.

## Ambiguities requiring resolution before execution
1. **Where exactly in `_run_extraction_pipeline` is the progress template context dict built?** The executor must find the call and confirm `narrative` is accessible at that point. Based on `turn.py`, `narrative` is available before `_run_extraction_pipeline` is called, but the executor must confirm it's passed through the function signature into the template kwargs.
2. **Does `extract_progress_system.j2` currently have a GM beat section, or is beat generation a separate schema field?** Executor must read the current template fully before writing Step 4.3 to avoid duplicating existing instructions.

***

## TODO.md update

Add under **P1 — Active** section:

```markdown
- [ ] [bugfix/2026-05-09-batch](docs/plans/bugfix/2026-05-09-batch/) — World gen, extraction correctness, narration quality, progress/pacing
  - [ ] [Phase 1: World Gen Quality](docs/plans/bugfix/2026-05-09-batch/01-world-gen.md)
  - [ ] [Phase 2: State Extraction Correctness](docs/plans/bugfix/2026-05-09-batch/02-extraction.md)
  - [ ] [Phase 3: Narration Quality](docs/plans/bugfix/2026-05-09-batch/03-narration.md)
  - [ ] [Phase 4: Progress Extractor — Pacing and Action Choices](docs/plans/bugfix/2026-05-09-batch/04-progress.md)
```

***

## Cross-phase dependency note

- **Phase 3 Step 3.5** (disarm on capture) depends on **Phase 2 Step 2.1** (inventory removal rules in state extractor) being active. The narrative will describe disarming, but nothing is actually removed until the state extractor has the consumable tracking instruction. These two phases can be deployed in the same PR but Phase 2 changes must be committed first.
- All other phases are fully independent of each other.
