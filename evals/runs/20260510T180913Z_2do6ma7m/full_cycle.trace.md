# Static Context (immutable across all turns)

## World Pack Style

```
# Eval-pack style

This pack is a deterministic test fixture. The narrator should write in a plain,
clear, second-person past-tense register. Keep these in mind:

- Specific over abstract. Name the thing the player did, the object they touched, the
  NPC they spoke to. Avoid generic mood words ("an air of menace") in favor of
  concrete sensory detail.
- One scene per turn. Do not skip ahead in time unless the player explicitly does so.
- Honor the dice. If the rules outcome is `fail` or `setback`, the action did not
  succeed; describe the cost. If `partial`, the action succeeded with a complication.
- Honor the present_npcs. Every named NPC in the scene either acts, reacts, or is
  visibly present in the prose. Do not invent new NPCs unless the player's input
  introduces one.
- Plain language. No archaic phrasing, no fantasy-trope syntax ("Lo, the door...").
  This is a working road in a working world.
- 120-220 words per turn unless the action is large.

```

## Seed State

```json
{
  "meta": {
    "game_name": "eval",
    "turn": 0,
    "setting_pack": "eval-pack",
    "model": ""
  },
  "pc": {
    "name": "Aren Voss",
    "tagline": "Reluctant courier on the merchant road",
    "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
    "stats": {
      "strength": 3,
      "dexterity": 3,
      "wits": 2,
      "lore": 2,
      "charisma": 3,
      "resolve": 3
    },
    "conditions": [],
    "momentum": 0
  },
  "location": {
    "id": "marrows_crossing",
    "name": "Marrow's Crossing",
    "description": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n"
  },
  "inventory": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Common coin, accepted at any inn or stall on the merchant road.",
      "amount": 500,
      "aliases": []
    },
    {
      "id": "iron_dagger",
      "name": "Iron dagger",
      "notes": "Plain crossguard, edge worn from honing. Belt-carried.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "bandages",
      "name": "Linen bandages",
      "notes": "Three rolls. Field-grade \u2014 won't replace a healer.",
      "amount": 3,
      "aliases": []
    },
    {
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, hood deep enough to hide a face.",
      "amount": 1,
      "aliases": [
        "cloak",
        "travel cloak"
      ]
    },
    {
      "id": "brass_key",
      "name": "Brass key",
      "notes": "A small brass key Halden gave you with the ledger.",
      "amount": 1,
      "aliases": []
    }
  ],
  "quests": [
    {
      "id": "settle_the_debt",
      "title": "Settle the Old Debt",
      "status": "active",
      "objectives": [
        {
          "description": "Find Caron, the man you owe.",
          "done": false,
          "failed": false
        },
        {
          "description": "Pay Caron in person and have him mark the debt cleared.",
          "done": false,
          "failed": false
        }
      ]
    },
    {
      "id": "deliver_the_ledger",
      "title": "Deliver Halden's Ledger",
      "status": "active",
      "objectives": [
        {
          "description": "Accept the courier contract from Halden.",
          "done": false,
          "failed": false
        },
        {
          "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
          "done": false,
          "failed": false
        },
        {
          "description": "Confirm the contract with Halden in person.",
          "done": false,
          "failed": false
        }
      ]
    },
    {
      "id": "clear_the_road_toughs",
      "title": "Clear the Road Toughs",
      "status": "active",
      "objectives": [
        {
          "description": "Find out who hired the toughs blocking the road.",
          "done": false,
          "failed": false
        },
        {
          "description": "Convince, pay, or remove the toughs from the inn.",
          "done": false,
          "failed": false
        }
      ]
    }
  ],
  "scene": {
    "tagline": "Market town at dusk",
    "tags": [
      "peaceful",
      "start"
    ],
    "world_state": [
      "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
      "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
      "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
    ],
    "recent_events": [
      "You arrived in Marrow's Crossing after three days on the road.",
      "You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.",
      "You found Caron in the tavern \u2014 he's been waiting for you."
    ],
    "present_npcs": [
      {
        "id": "caron",
        "name": "Caron",
        "title": "Old creditor",
        "notes": "Sits at a corner table in the tavern, nursing a drink and watching the door.",
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago."
      },
      {
        "id": "halden",
        "name": "Halden",
        "title": "Merchant",
        "notes": "Stands near the town well, examining a map and a pressed wax seal.",
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money."
      },
      {
        "id": "innkeeper",
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys",
        "notes": "Wiping down the bar at the Crossed Keys, which is two streets over.",
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door."
      }
    ]
  },
  "compendium": {
    "npcs": {
      "caron": {
        "name": "Caron",
        "title": "Old creditor",
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago."
      },
      "halden": {
        "name": "Halden",
        "title": "Merchant",
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money."
      },
      "innkeeper": {
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys",
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door."
      },
      "tough_a": {
        "name": "Bald Tough",
        "title": "Road thug",
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad."
      },
      "tough_b": {
        "name": "Scarred Tough",
        "title": "Road thug",
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains."
      },
      "matthew_estrada": {
        "name": "Matthew Estrada",
        "title": "Traveler",
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision."
      }
    }
  }
}
```

## Engine Constants

```json
{
  "pressure_building_at": 6,
  "pressure_immediate_at": 10,
  "pressure_max_age": 15,
  "urgency_levels": [
    "background",
    "building",
    "immediate"
  ],
  "momentum_min": -3,
  "momentum_max": 3,
  "momentum_delta": {
    "crit_success": 2,
    "success": 1,
    "partial": 0,
    "setback": -1,
    "fail": -1,
    "crit_fail": -2
  }
}
```

## System Prompts (identical every turn)

### Rules System Prompt

```
You decide whether the player's action requires a skill check, and if so, classify it. Emit ONLY a JSON object — no prose, no markdown fences.

## Stats — pick exactly one for check.skill
- strength: Physical force, melee, lifting, breaking, soak, endure pain
- dexterity: Agility, stealth, ranged attacks, fine motor, dodge, pickpocket
- wits: Quick thinking, perception, deduction, hacking under pressure, spot a lie
- lore: Recalled knowledge, history, languages, protocols, identification, expertise
- charisma: Persuade, deceive, charm, negotiate, perform, seduce, intimidate by presence
- resolve: Willpower, courage, resist fear / torture / coercion / temptation

## Difficulty — pick exactly one for check.difficulty
- trivial (+2): Almost certain; only roll if failure would be interesting
- easy (+1): Routine for a competent person
- normal (0): A genuine challenge
- hard (-1): Requires skill, preparation, or favourable conditions
- extreme (-2): Near-impossible without exceptional ability or luck

## Decision rule — default NO
Set check.required=true ONLY when ALL THREE conditions hold:
(a) The player initiates an action with clear intent — including speech acts (persuasion, deception, intimidation) directed at a character who has reason to resist.
(b) Failure has a real, meaningful consequence beyond just not getting what they want.
(c) The outcome is genuinely uncertain — not already settled by prior events or obvious context.

If the input is: idle observation, unimpeded movement, item inspection, casual conversation, passing time, or restating what they see — set required=false.

If the player is paying a stated or clearly implied fixed price to a willing or commercially neutral NPC (buying goods at market price, paying a fee, tipping, settling a stated debt) — set check.required=false. No charisma roll is needed for routine commerce with a willing counterparty.

## Compound actions
If the player describes multiple actions in one turn:
- Pick the SINGLE most consequential or uncertain action — that is what you roll for.
- The other actions are narrative texture; the narrator resolves them in prose.
- If individually-trivial sub-actions compound into something risky ("sneak past three guards then lift the badge"), classify as ONE harder check rather than rolling for each step.
- `intent` should summarise the full sequence; `intent_verb` and `check` apply to the gating action only.
- If the gating action would fail, the chain does not continue — note this in `stakes`.

## Anti-declare-outcome rule
If the player's phrasing asserts the result ("I one-shot the guard", "I instantly convince her", "I hack through in seconds") — classify the underlying attempt at hard or extreme difficulty. Never let the player's prose dictate success.

## Output schema (emit this JSON object only)
{
  "intent": "", 
  "intent_verb": "",
  "target": "",
  "stakes": "",
  "check": {
    "required": boolean,
    "skill": "",
    "difficulty": "",
    "tags": []
  }
}

## Field rules

- `intent`: 1 sentence declaring player intent as related to the story, quests, world, or npcs. Never substitute, dismiss as impractical or extreme, or embellish. Default: player moves with allies. Only soften it in line with the anti-declare-outcome rule.
- `intent_verb`: attack|persuade|sneak|hack|deceive|intimidate|climb|repair|recall|escape|negotiate. If it fits none of these, you must choose an appropriate word not listed.
  - `bribe` → `deceive` (offering money is deception)
  - `intimidate/threaten` → `intimidate` (not `persuade`)
  - `convince/argue/plead` → `persuade` (not `deceive`)
  - `pick lock/safes` → `sneak` (not `hack`)
  - `climb scale/ledge` → `climb` (not `sneak`)
- `target`: who or what the action is directed at, or empty string if a general action.
- `stakes`: what is at risk if this fails. Use this template: `[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: what the antagonist/world does next]`. If nothing meaningful is at risk, emit empty string.
- `check`: an object with the following fields:
  - `required`: true or false.
  - `skill`: strength|dexterity|wits|lore|charisma|resolve.
  - `difficulty`: trivial|easy|normal|hard|extreme.

## Directive notes

The directive you produce feeds into the narrator's prose. When a `fail` directive includes a near-miss note, the narration should describe a setback or complication that changes the situation without completely blocking the player. The player still fails — but the story advances.

```

### Narrate System Prompt

```
Narrate the next beat of a text adventure. Second person. Follow the tense specified in the ## Genre tone section below; if no tense is specified, use past tense. 2-4 short paragraphs. Output prose only — never list choices, never speak as the game.

Each beat advances the fiction. Match the weight of your narration to the outcome and the scene's current state. The user prompt provides a Narration Directive for this specific turn — follow it.

- NPCs should frequently suffer positive and negative consequences, not just the player. In appropriate genres, death and mortal injury is common.
- Mention characters from recent turns sometimes when relevant and adds flavor.

**Pacing is critical.** Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes. The Narration Directive in the user prompt tells you how to pace this specific turn.

## Style
Spatial clarity: when positioning matters (combat, stealth, formations, who-is-where) make distance, direction, cover, and line of sight explicit.
Avoid tropes; invent fresh twists, weird details, even humor in dark stories. Don't repeat known facts or restate conditions already mentioned.
Use direct dialogue when player or NPC is speaking. 
NPCs and scene/location should interact with the player when appropriate.
Viseral, gory, and sexual details are allowed when appropriate to the story and genre.
Describe appearances of new characters briefly. 
Keep it tight — each turn is a scene beat, not a chapter.
Use colorful imagery, metaphores/similes, and genre-appropriate colloquialisms.

## Items and inventory
Items with multiples should be always quantified, even if vaguely: "I picked up a couple pistol clips." When relevant to quests or inventory, explicit quantity is preferred.
**Bold** named inventory items on first use or direct reference in a scene. **Bold** NPC names on first introduction in a scene. This applies on the very first turn the same as all subsequent turns.

**Inventory is a hard constraint.** Before narrating any item usage, spending, or consumption, verify the item appears in the `## inventory` list in the user prompt. If the player's action implies spending an item not in that list, narrate the *attempt* or *intent* without confirming a successful transfer. Never describe the player producing, spending, or losing an item that is not in their current inventory. If the inventory list shows `credits: 500`, the player has 500 credits — do not invent `iron_coin`, `silver`, or other substitute denominations.

## Player intent is truth
Take the player's stated action at face value and commit to it. The rules engine handles dice and conditions; the narrator handles fiction. 
Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

## Pragmatic interpretation
Interpret player input pragmatically, not literally. If the player says something absurd or physically impossible ("I offer a credit to the wall", "I punch the sky"), narrate the attempt as a reasonable interpretation of their intent — the wall doesn't accept coins, the sky can't be punched. The rules engine will resolve whether the action succeeds. Never refuse the action outright; narrate the attempt and let the dice decide.

## NPCs in scene
NPCs should feel like persistent people, not props. Re-use characters from the Known Characters list when the scene and location are consistent with their last known position. Only create a genuinely new character when the scene requires someone no existing character can fill. When introducing a new named NPC, pick from the name pool. Give a brief physical description.

## Mortal stakes + agency
NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.
Resolve cruel, selfish, or evil player choices straight: narrate consequences without moralizing, refusing, or steering toward a "better" path. NPCs may react with horror, retaliation, or fear; the narrator never lectures or vetoes.

## Gender-aware naming
When the name pool provides separate male and female lists, select names appropriate to the role and setting. Historical combat genres: use male names for front-line combat roles. Modern and speculative settings: use any gender freely.

## NPC naming
All NPC names must include a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Single-word names are not permitted. When introducing a new NPC, pick from the name pool provided in the user prompt. If the NPC is anonymous or unnamed in-scene, use a descriptive placeholder like "the guard" or "a stranger" — but once their true name is revealed, it must supersede the placeholder and the placeholder becomes an alias (handled by the scene extractor).

## Quests
If the action satisfies an objective or resolves a quest, make that resolution clear in prose briefly (the debt is paid, the job is done, the target is found).

## Markdown (light)
- `**bold**` only for: NPC names on first introduction this scene; named inventory items (use a short name, not ammo) the player owns when used or directly referenced. Once per scene per object.
- `*italic*` for ship names, books, broadcasts, in-world publication titles, emphasized proper nouns.
- `> blockquote` only for signage or quoted broadcast text.
- No headings, no bullet lists in prose.




## Active scope tail
After your prose is complete, on a new line, emit a single line:

<scope>{"active_domains":["..."]}</scope>

Valid domains:
- scene             — scene tags, NPC presence, scene tagline changes
- location_change   — player physically moved or scene shifted significantly
- inventory         — items received, used, dropped, upgraded
- pc_condition      — wounds, fatigue, mental conditions added or resolved
- quest_updates     — quest objective progress, new quest, quest resolved/failed
- recent_events     — narratively significant new fact (politics, intrigue, world)
- compendium_npc    — NPC named for the first time, durable identity change, death

List ONLY domains that genuinely changed THIS turn. Empty list `[]` is valid
and means "nothing changed; advance the storyteller's reasoning only."

**No speculation.** Only list a domain if a change is confirmed in your narration. Do not list domains for things that might happen, things you hint at, or things you foreshadow. If your narration does not explicitly show a change, do not flag the domain.

**Bias towards inclusion for scene-related domains.** If any of these happened,
flag the appropriate scope:
- A character enters or leaves the narration → `scene`
- The location changes or the player physically moves → `location_change`
- An NPC's situation, position, or state shifts → `scene`
- A character is named for the first time → `compendium_npc`

When in doubt, include the scope. It is better to over-flag than to skip
extraction streams that need to run.

Rules:
- The tag MUST be the very last thing in your output, on its own line.
- One JSON object only. No prose after the closing tag.
- If thinking mode is enabled, the tag goes AFTER the closing </thinking> tag.
- The tag and its contents are stripped from the player's view by the engine.

```

### Extract Scene System Prompt

```
## Objective

Read the turn narration and extract the scene-level state: which NPCs are present and how they stand toward the player, whether the player moved to a new location, what the scene feels like, and any new spatial details about the current space. Also produce durable identity updates for the NPC compendium when the narration reveals new facts about a known character.

## Output schema

```json
{
  "scene_tags": [],
  "scene_tagline": null,
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "compendium_npc_update": []
}
```

## Field rules

`scene_tags`: mood/genre descriptors for the scene. Up to 5. Use concise noun or adjective phrases. Examples: `"combat"`, `"tense_conversation"`, `"investigation"`, `"stealth"`, `"discovery"`.

`scene_tagline`: 3–6 words summarizing the scene for the UI header. Grounded in what just happened. Examples: `"A Toll Paid In Blood"`, `"Whispers in the Dark"`, `"The Guard Raises the Alarm"`.

`location_change`: emitted only when the player moves to a new location (the location ID differs from the current one). Each: `{"id": "snake_case_id", "name": "Display Name", "description": "one-sentence description of the new space"}`. Do NOT emit if the player is still in the same location with added spatial detail — use `location_description` instead.

`location_description`: new physical/spatial detail about the current space. Only emit when the narration introduces genuinely new details not already in the stored description. Do not restate or paraphrase existing description. One to two sentences.

`npc_add`: named characters who entered or are revealed in the scene. Each: `{"id": "snake_case_id", "notes": "current attitude or situation toward the player", "name": "Display Name", "title": "Optional title", "bio": "1-2 sentence identity"}`. Omit `name`, `title`, `bio` when the NPC is already known from the compendium — the engine will hydrate from the compendium. Always include `notes` describing how the NPC is behaving toward the player right now.

`npc_remove`: named characters who left the scene. Each: `{"id": "snake_case_id", "last_seen_state": "1-sentence description of what NPC was last seen doing"}`. The `id` must match an NPC currently in `present_npcs`. Omit `last_seen_state` if there is nothing meaningful to record.

`npc_update`: changes to how an existing present NPC is behaving toward the player (attitude, situation). Each: `{"id": "snake_case_id", "notes": "updated attitude or situation"}`. Only emit when the NPC's behavior or situation toward the player has changed meaningfully. Omit `name`, `title`, `bio` — those are compendium fields, not scene fields.

`compendium_npc_update`: durable identity updates for NPCs that should persist across turns in the global compendium. Each: `{"id": "snake_case_id", "name": "new_name", "title": "new_title", "bio": "updated bio", "aliases": ["alias1"], "allegiance": "faction_or_alignment"}`. Only emit when the narration reveals new durable identity information about a known NPC (new name, title, bio, allegiance, or aliases). Do NOT emit for temporary scene behavior — that goes in `npc_update` under `notes`.

## NPC ID rules

- Use existing IDs from the `## Present NPCs` list when referencing NPCs already in the scene.
- For new NPCs, generate a stable `snake_case` ID from their name/title. Examples: `"scarred_tough"`, `"guard_captain_renn"`.
- If an NPC is known from the compendium, use their existing compendium ID — do NOT create a new ID.
- When adding a new NPC, include `name`, `title`, and `bio` so the engine can populate the compendium.

## State-presence rule

Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, verify that you have no duplicate or near-duplicate entries:

- **NPCs:** Do not add an NPC whose ID already appears in the `## Present NPCs` list or whose name/title closely matches an existing compendium entry. If the narration refers to an already-present NPC, use `npc_update` instead of `npc_add`.
- **Locations:** Do not emit `location_change` if the location ID is the same as the current location. Do not emit `location_description` if the narration only restates or paraphrases details already in the stored description.
- **Scene tags:** Do not repeat tags already present in the previous turn's `scene_tags` unless the mood has genuinely shifted. Keep the list to at most 5.
- **Compendium updates:** Do not emit a `compendium_npc_update` for an NPC that has no new durable identity information (name, title, bio, allegiance, aliases).

## NPC Grounding Rule

All NPC `name`, `title`, and `bio` values must be grounded in the narration or the compendium. Do not invent character names, titles, or backstories that are not stated or strongly implied by the narration. If the narration only gives a description (e.g. "a scarred man"), use a descriptive ID like `"scarred_man"` and omit `name`/`title`/`bio` — the engine will hydrate from the compendium if the NPC is known.

## Constraints

- **Always emit at least one NPC entry.** If no specific named character is present, emit ambient presence (e.g., a crowd, onlookers, guards, townsfolk). Use a generic ID like `"crowd"`, `"bystanders"`, `"inn_patrons"`, or `"guards"` with appropriate `notes`.
- **Never invent location IDs.** Only use location IDs from the `## Current Location` section or well-known locations from the compendium.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit `npc_add` to at most 3 per turn.** Only add NPCs that are meaningfully present or interact with the player. Background extras go in ambient presence.

Output a single JSON object matching the SceneExtractResult schema.

```

### Extract State System Prompt

```
Extract inventory and condition deltas from a narration. Emit one JSON object matching the schema. 
No prose, no markdown fences, empty arrays for fields with no changes.
Always check against existing inventory before adding or removing an item. Duplication forbidden.
Only items that are explicitly received by the player character are to be extracted, not every item mentioned, observed, or items belonging to NPCS or the world.

## ID format rules

Inventory IDs must be `noun` or `adjective_noun`, lowercase, no articles.
- ✅ `worn_dagger`, `brass_key`, `short_sword`
- ❌ `the_dagger`, `a_key`, `soldiers_rifle`

IDs are immutable once assigned. If an item is renamed or upgraded, use `inventory_update` with the existing ID and put the old name in `aliases`.

## Match instruction

Before emitting `inventory_add`, check the existing inventory list provided in context.
If the item is likely the same object referred to differently (e.g. `"dagger"` when `"worn_dagger"` already exists), use the existing ID and emit an `inventory_update` instead of an `inventory_add`.
Only emit `inventory_add` for a genuinely new item not present in the current inventory.

Item descriptions should be relevant to story, player, and setting.

**Quantities are exact.** If narration says "used two morphine syrettes", emit `{"id": "<item_id>", "amount": 2}`. 
Read the current stack from the user prompt before emitting `amount`. 
Never emit `amount` greater than the current stack — if the player used the entire stack, omit `amount` (treated as full remove).
If an amount is not specified in narration, infer the amount: "used some bandages" ⇒ 2-3, "fired multiple rounds" ⇒ 3-6, "spent all your money" ⇒ full stack.

## Output schema

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

## Hard cap
- `inventory_add`: Items explicitly received in narration are not capped.  Stack increases via re-adding the same `id` are NOT capped. Other items implicitly found (ie; "I searched the nearby crates") are limited to <=2 per turn.
- `pc_condition_add`: ≤2 per turn. Total active conditions must not exceed 5. If it does, remove the least relevant or consequential.

## Field rules

`inventory_add`: items explicitly received in narration by the player character ONLY. NPC posessions do not count. Each: `{"id": "snake_case", "name": "Display Name", "notes": "optional", "amount": 1}`. Infer from narration only. Ranged weapons require a separate depletable ammo stack (`{"id": "9mm_rounds", "name": "9mm rounds", "amount": 12}`); if compatible ammo already in inventory, use `inventory_update` instead.

`inventory_remove`: items lost, used, destroyed, or spent. Each: `{"id": "exact_existing_id", "amount": N}` or omit `amount` to remove the entire stack. Use the exact id from the inventory list shown in the user prompt. Never emit add and remove for the same id in one turn. If the narration describes the player parting with an item (e.g. "dropped credits on the ground," "handed over the key"), emit the remove even if the narration later says the recipient rejected it or the action failed — the state should reflect what the player attempted, not just what succeeded.

`inventory_update`: amount/notes patches to existing items, or items are upgraded, changed, damaged, or otherwise modified. Each: `{"id": "exact_existing_id", "name": "optional", "notes": "optional"}`. Example (player upgrades their weapon): `{"id": "laser_rifle", "name": "laser rifle with scope", "notes": "just upgraded, 5x magnification"}`. Item name and description should reflect recent events, if applicable.

`pc_condition_add`: new conditions with a clear, substantial cause in narration. Default to not adding for minor effects. Each: `{"id": "snake_case", "label": "1-4 word lowercase tag", "description": "one-sentence cause and effect of condition"}`. Don't duplicate by id. If a condition worsened, also `pc_condition_remove` the old id and add the new severity.

## Condition guidance — use roll context

Positive conditions are only added for significant changes in player state that have practical application given the narrative.

The roll_context section above shows which skill was checked and the outcome band. Use this as the primary signal for condition decisions:

- Failed/setback `strength` or `dexterity` during combat verb → consider `wounded`, `bleeding`
- Failed/setback `resolve` → consider `shaken`
- Failed/setback `wits` under pressure → consider `frightened` or `drugged` (if substance involved)
- Failed/setback `strength`/`dexterity`/`resolve` with sustained effort → consider `exhausted`
- Do NOT add negative conditions on a clean success or crit_success

The narration text confirms the cause, but the roll context triggers the condition type.

`pc_condition_remove`: conditions that resolved this turn. Each: `{"id": "existing_condition_id"}`. Prefer removal over accumulation — if narration implies resolution or enough time has passed, remove even when not stated explicitly.

## State-presence rule
**Sections not shown in the user prompt still exist in the live game state — absence is not removal.** Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, ensure once more than you have no similar or matching items or item IDs.

## Generic item mapping (MANDATORY)

If the narration references a generic denomination or container term, you MUST map it to the
closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term.

Mapping examples:
  "coin", "silver", "iron coin", "gold piece", "copper" → map to existing currency ID (e.g., "credits")
  "roll of cash", "stack of credits", "pouch of money" → map to existing currency ID
  "a coin" → map to existing currency ID
  "some money" → map to existing currency ID

If no inventory item clearly matches the generic term, do NOT emit an inventory_remove or
inventory_add for that reference. The narrator's language is imprecise — the state should not
change. Omission is always safer than inventing a new ID.

**If you create an inventory ID that does not match any existing item and is not a genuinely
new item described in the narration, you have failed this rule.**
```

### Extract Progress System Prompt

```
Extract quest updates, recent events, suggested player actions, and outcome summary from a narration. Emit one JSON object matching the schema. No prose, no markdown fences, empty arrays for fields with no changes.

## Output schema

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

## Field rules

`quest_updates`: changes to quest state this turn.
- Update existing: `{"id": "quest_id", "status": "active|completed|failed|abandoned", "objectives": [{"index": N, "done": true}]}`. `index` is 1-based from the active_quests list shown in the user prompt.
- New quest: `{"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objectives": [{"description": "first objective"}]}`. Use `description` only when adding a new objective.
- The engine auto-completes a quest when all objectives are done — do NOT emit `status: completed` for that case; just mark objectives done.
- New quest threshold guidance for this turn is in the user prompt.
- **Quest deduplication (MANDATORY):** Before creating ANY new quest, you MUST compare its subject, target NPC, and object against every quest in the `## active_quests` list. If the new quest overlaps with an existing quest in subject, target NPC, or object, you MUST update the existing quest instead of creating a new one. Overlap means: same item being delivered/found, same NPC being sought/paid, same conflict being resolved, or same objective being advanced. New quest IDs that differ only in word choice from existing IDs (e.g., `deliver_stained_ledger` vs `deliver_the_ledger`, `caron_debt` vs `settle_the_debt`) are duplicates — use the EXISTING ID. Only create a genuinely new quest if the task, target, AND context are all distinct from every active quest. When in doubt, update the existing quest.
- **NEVER create a new quest ID when an existing active quest covers the same objective.** Examples of what NOT to do:
  - Do NOT create `deliver_ledger_to_inn` when `deliver_the_ledger` already exists — update `deliver_the_ledger` instead.
  - Do NOT create `caron_debt` when `settle_the_debt` already exists — update `settle_the_debt` instead.
  - Do NOT create `find_the_ledger` when `deliver_the_ledger` already exists — update `deliver_the_ledger` instead.
- A quest is failed when the key objective(s) are failed, or are impossible to complete due to new information.
- A quest is abandoned when the player/narration implies they are giving up on it, gets too far away to continue, or it is no longer relevant.

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the quest, player, scene, and location, and not already known. Must be narratively significant: an obstacle, revelation, opportunity, relevant news that changes the player, location, or quest state substantially. Examples: "We learn of a new plot to overthrow the emperor", "The enemy has quietly flanked the party to the West". Each: `{"id": "snake_case_id", "text": "Event description", "turn": <CURRENT_TURN>}`. The current turn number is shown at the top of the user prompt under `## turn`. Always use that value — never 0.

Each new event must have a stable `snake_case` ID. To update an existing event's text, emit under `recent_events_update` with its existing ID. To remove, emit ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded.

`recent_events_update`: facts whose content changed. Each: `{"id": "existing_event_id", "text": "replacement text"}`. Prefer updating over remove+add.

`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current quest state. Structure: two choices should offer distinct avenues related to the current quest (if any), one should involve an NPC who is present in the scene, and one should be an exploration/environmental or freeform option. Weight toward quest objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices.

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, NPCs, scene, and location. Ground this in the roll outcome (if any) and the player's intent. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

`gm_beat`: a single GM beat to shape the next turn, or `null` if none is needed. Use `deescalate` and `quest_ages` context to decide:
- `deescalate > 0.5` → prefer `breathing_room` or `null` (no beat)
- `deescalate == 0.0` with active pressure → `pressure` or `escalation`
- Quest staleness in `quest_ages` (age >= 3) → `setback` or `complication`
- Recent `twist` or `callback` beats should not repeat within 2 turns
- `type` values: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`, `twist`, `setback`, `escalation`, `callback`
- `surface_as` values: `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`
- Each beat must be narratively specific: name NPCs, reference locations, tie to active quests
- Emit as: `{"type": "pressure", "surface_as": "npc_behavior", "instruction": "The guard captain returns with reinforcements."}`
- If no beat is warranted, emit `null` (not an empty object)

`beat_disposition`: controls what happens to the pending_gm_beat from the previous turn. Values: `"consume"` (default) — beat is cleared after narration; `"carry"` — beat stays in meta.pending_gm_beat unchanged for the next turn; `"replace"` — the new gm_beat above supersedes the carried one. If you emit a new gm_beat, use `"replace"`. If you want to preserve an unsurfaced beat, emit `"carry"` and leave gm_beat null.

`scene_pressure_add`: new scene pressures generated from story causality this turn. Each: `{"id": "snake_case_id", "text": "Threat description", "urgency": "immediate|building|background", "turn_added": <CURRENT_TURN>}`. Add pressure when a named NPC/faction acts against the player off-screen, a quest deadline triggers, or a failed roll's consequence activates. Do NOT add pressure for resolved threats or vague ambient danger.

`scene_pressure_remove`: IDs of pressures now resolved. Emit the id string in the list.

`scene_pressure_update`: Change the text or urgency of an EXISTING pressure. Each: `{"id": "existing_pressure_id", "text": "updated text", "urgency": "immediate|building|background"}`.
**RULE: update-only.** Every `id` you emit MUST match an id in the `## Current Pressures` list provided in the user prompt. Do not invent new pressure ids here. If you need a new pressure, use `scene_pressure_add` instead.

## GM Beat Grounding Rule

`gm_beat.instruction` must reference a specific named entity already present in state:
an NPC id from the Present NPCs list, or a pressure id from the Current Pressures list.
Do not invent new characters or situations in `gm_beat`. A beat that references no existing
entity will be nullified by the engine.

## Rules-outcome guidance (for objective resolution)
- crit_fail / fail / setback / partial: do NOT mark quest objectives done for the attempted action.
- success / crit_success: apply objective completions freely.
- No dice roll: do NOT complete quest objectives unless the narration explicitly and unambiguously states the objective is fulfilled. **Exception: see Contact and meet objective rule below.** Ambiguous, partial, or conversational narration means the objective is NOT done.

## Contact and meet objective rule
**This rule overrides the general rules-outcome guidance above.** Contact and meet objectives resolve on narrative presence, not roll outcome, even when no dice were rolled.
If a quest objective's description contains any of: "find", "meet", "contact", "locate", "speak with", "reach", "talk to", "seek out" — the objective completes when ALL of:
- The named NPC or target is present in the current narration (they appear, respond, or speak).
- The player has established or attempted communication (spoken to them, signaled them, made contact).
- The narration does not explicitly show the contact failed or was refused.
This applies regardless of rules_outcome.band. Contact objectives are resolved by narrative presence, not roll outcome.

## State-presence rule
Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

```


---

# TURN 1

**Input:** `Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Marrow's Crossing## Current Turn: 1
=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [ ] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron**
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 1
=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 1

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`marrows_crossing` | Marrow's Crossing
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 1

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrows_crossing`

## CURRENT TURN NARRATION
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 1

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player approaches Caron to discuss the repayment or settlement of their debt.
## quest_threshold
3 active quests already. Bar is HIGH — only start a new quest for a major new obligation clearly distinct from all existing quests.

## active_quests
- `settle_the_debt` | Settle the Old Debt
  objectives:
    1. [ ] Find Caron, the man you owe.
    2. [ ] Pay Caron in person and have him mark the debt cleared.
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [ ] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `settle_the_debt`:  turns
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player approaches Caron to discuss the repayment or settlement of their debt.",
  "rolled": false,
  "total_ms": 9480.9,
  "tokens_in": 1231,
  "tokens_out": 1320
}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss the repayment or settlement of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "",
  "check": {
    "required": false,
    "skill": "charisma",
    "difficulty": "trivial",
    "tags": []
  }
}
```

### Narration

The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "dimly_lit",
    "quiet"
  ],
  "scene_tagline": "A Debt Awaits",
  "location_change": null,
  "location_description": "The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [
    {
      "id": "settle_the_debt",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Offer Caron the coin you have to settle the debt.",
    "Ask Caron if he knows anything about the road toughs.",
    "Try to charm Caron to buy more time for payment.",
    "Scan the tavern for any signs of trouble or eavesdroppers."
  ],
  "outcome_summary": "You have successfully located Caron in the tavern and confronted him about your debt.",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.",
  "quest_updates": [
    {
      "id": "settle_the_debt",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": true
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_conversation",
    "dimly_lit",
    "quiet"
  ],
  "scene_tagline": "A Debt Awaits",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation."
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Offer Caron the coin you have to settle the debt.

- Ask Caron if he knows anything about the road toughs.

- Try to charm Caron to buy more time for payment.

- Scan the tavern for any signs of trouble or eavesdroppers.

### Context Telemetry

- rules: est=1404t trimmed=False
- narrate: est=3086t trimmed=False
- extract.scene: est=2441t trimmed=False attempts=1
- extract.state: est=2540t trimmed=False attempts=1
- extract.progress: est=3715t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 1
        },
        "name": "Caron",
        "title": "Old creditor"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "name": "Halden",
        "title": "Merchant"
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys"
      },
      "matthew_estrada": {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "name": "Matthew Estrada",
        "title": "Traveler"
      },
      "tough_a": {
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "name": "Bald Tough",
        "title": "Road thug"
      },
      "tough_b": {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "name": "Scarred Tough",
        "title": "Road thug"
      }
    }
  },
  "inventory": [
    {
      "aliases": [],
      "amount": 500,
      "id": "credits",
      "name": "Credits",
      "notes": "Common coin, accepted at any inn or stall on the merchant road."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "iron_dagger",
      "name": "Iron dagger",
      "notes": "Plain crossguard, edge worn from honing. Belt-carried."
    },
    {
      "aliases": [],
      "amount": 3,
      "id": "bandages",
      "name": "Linen bandages",
      "notes": "Three rolls. Field-grade \u2014 won't replace a healer."
    },
    {
      "aliases": [
        "cloak",
        "travel cloak"
      ],
      "amount": 1,
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, hood deep enough to hide a face."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "brass_key",
      "name": "Brass key",
      "notes": "A small brass key Halden gave you with the ledger."
    }
  ],
  "location": {
    "description": "The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "compendium_touch_order": [],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": null,
    "prior_history": [],
    "setting_pack": "eval-pack",
    "turn": 1
  },
  "pc": {
    "allegiance": null,
    "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
    "conditions": [
      {
        "added_turn": 8,
        "description": "A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.",
        "id": "bruised_ribs",
        "label": "bruised ribs"
      },
      {
        "added_turn": 10,
        "description": "Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.",
        "id": "low_morale",
        "label": "low morale"
      }
    ],
    "momentum": 0,
    "name": "Aren Voss",
    "stats": {
      "charisma": 3,
      "dexterity": 3,
      "lore": 2,
      "resolve": 3,
      "strength": 3,
      "wits": 2
    },
    "tagline": "Reluctant courier on the merchant road"
  },
  "quests": [
    {
      "id": "settle_the_debt",
      "last_advanced_turn": 0,
      "objectives": [
        {
          "description": "Find Caron, the man you owe.",
          "done": true,
          "failed": false
        },
        {
          "description": "Pay Caron in person and have him mark the debt cleared.",
          "done": false,
          "failed": false
        }
      ],
      "status": "active",
      "title": "Settle the Old Debt"
    },
    {
      "id": "deliver_the_ledger",
      "objectives": [
        {
          "description": "Accept the courier contract from Halden.",
          "done": false,
          "failed": false
        },
        {
          "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
          "done": false,
          "failed": false
        },
        {
          "description": "Confirm the contract with Halden in person.",
          "done": false,
          "failed": false
        }
      ],
      "status": "active",
      "title": "Deliver Halden's Ledger"
    },
    {
      "id": "clear_the_road_toughs",
      "objectives": [
        {
          "description": "Find out who hired the toughs blocking the road.",
          "done": false,
          "failed": false
        },
        {
          "description": "Convince, pay, or remove the toughs from the inn.",
          "done": false,
          "failed": false
        }
      ],
      "status": "active",
      "title": "Clear the Road Toughs"
    }
  ],
  "scene": {
    "present_npcs": [
      {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "id": "caron",
        "name": "Caron",
        "notes": "Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation.",
        "title": "Old creditor"
      },
      {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "id": "halden",
        "name": "Halden",
        "notes": "Stands near the town well, examining a map and a pressed wax seal.",
        "title": "Merchant"
      },
      {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "id": "innkeeper",
        "name": "Edda",
        "notes": "Wiping down the bar at the Crossed Keys, which is two streets over.",
        "title": "Innkeeper at the Crossed Keys"
      }
    ],
    "recent_events": [
      {
        "id": "you_arrived_in_marrows_crossing_after",
        "text": "You arrived in Marrow's Crossing after three days on the road.",
        "turn": 0
      },
      {
        "id": "you_heard_rumors_of_roadtoughs_extorting",
        "text": "You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.",
        "turn": 0
      },
      {
        "id": "you_found_caron_in_the_tavern",
        "text": "You found Caron in the tavern \u2014 he's been waiting for you.",
        "turn": 0
      }
    ],
    "scene_pressure": [],
    "tagline": "A Debt Awaits",
    "tags": [
      "tense_conversation",
      "dimly_lit",
      "quiet"
    ],
    "world_state": [
      "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
      "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
      "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
    ]
  },
  "world": {
    "factions": [],
    "locations": []
  }
}
```


---

# TURN 2

**Input:** `I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Marrow's Crossing
## last_turn (tail of the most recent narrative)
T1: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.

## Current Turn: 2
=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Settle the Old Debt** [active]
  - [x] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [ ] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 1** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 2
=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## Current Turn: 2

## active_domains
quest_updates

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player offers 500 credits to Caron to settle their outstanding debt.
## quest_threshold
3 active quests already. Bar is HIGH — only start a new quest for a major new obligation clearly distinct from all existing quests.

## active_quests
- `settle_the_debt` | Settle the Old Debt
  objectives:
    1. [x] Find Caron, the man you owe.
    2. [ ] Pay Caron in person and have him mark the debt cleared.
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [ ] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## prior_turn_narration (T1 — for outcome_summary and actions context)
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.

## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `settle_the_debt`:  turns
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player offers 500 credits to Caron to settle their outstanding debt.",
  "rolled": false,
  "total_ms": 2637.8,
  "tokens_in": 1522,
  "tokens_out": 1609
}
```

**Raw LLM output:**
```
{
  "intent": "The player offers 500 credits to Caron to settle their outstanding debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "",
  "check": {
    "required": false,
    "skill": "",
    "difficulty": "",
    "tags": []
  }
}
```

### Narration

You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [
    {
      "id": "settle_the_debt",
      "title": "",
      "status": "completed",
      "objectives": [
        {
          "index": 2,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Ask Caron for any rumors regarding the road toughs.'}",
    "{'text': 'Leave the tavern immediately to seek out Halden.'}",
    "{'text': 'Try to charm Caron into giving you a lead.'}",
    "{'text': 'Scan the tavern for any suspicious characters watching you.'}"
  ],
  "outcome_summary": "You successfully pay Caron 500 credits, and he marks your debt as cleared in his ledger.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "Caron mentions the road is hungry, hinting at the danger ahead.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "quest_updates": [
    {
      "id": "settle_the_debt",
      "title": "",
      "status": "completed",
      "objectives": [
        {
          "index": 2,
          "done": true
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [],
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'text': 'Ask Caron for any rumors regarding the road toughs.'}

- {'text': 'Leave the tavern immediately to seek out Halden.'}

- {'text': 'Try to charm Caron into giving you a lead.'}

- {'text': 'Scan the tavern for any suspicious characters watching you.'}

### Context Telemetry

- rules: est=1788t trimmed=False
- narrate: est=3468t trimmed=False
- extract.scene: skipped
- extract.state: skipped
- extract.progress: est=4002t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "beat_expires_turn": 4,
        "instruction": "Caron mentions the road is hungry, hinting at the danger ahead.",
        "surface_as": "npc_behavior",
        "type": "revelation"
      }
    },
    "turn": {
      "from": 1,
      "to": 2
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "settle_the_debt",
          "last_advanced_turn": 0,
          "objectives": [
            {
              "description": "Find Caron, the man you owe.",
              "done": true,
              "failed": false
            },
            {
              "description": "Pay Caron in person and have him mark the debt cleared.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Settle the Old Debt"
        },
        "to": {
          "id": "settle_the_debt",
          "last_advanced_turn": 0,
          "objectives": [
            {
              "description": "Find Caron, the man you owe.",
              "done": true,
              "failed": false
            },
            {
              "description": "Pay Caron in person and have him mark the debt cleared.",
              "done": true,
              "failed": false
            }
          ],
          "status": "completed",
          "title": "Settle the Old Debt"
        }
      }
    ]
  }
}
```


---

# TURN 3

**Input:** `I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Marrow's Crossing
## last_turn (tail of the most recent narrative)
T2: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

## Current Turn: 3
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Deliver Halden's Ledger** [active]
  - [ ] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 1** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.

**Turn 2** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

GM DIRECTION (REVELATION, surface as npc_behavior):
Caron mentions the road is hungry, hinting at the danger ahead.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 3
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 3

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`marrows_crossing` | Marrow's Crossing
The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor) — Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T2 context)
You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

## CURRENT TURN NARRATION
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 3

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrows_crossing_streets`
(location changed)
## CURRENT TURN NARRATION
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 3

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [ ] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## prior_turn_narration (T2 — for outcome_summary and actions context)
You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

## items_gained
leather-bound ledger

## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "rolled": false,
  "total_ms": 2733.1,
  "tokens_in": 1585,
  "tokens_out": 1675
}
```

**Raw LLM output:**
```
{
  "intent": "Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "",
  "check": {
    "required": false,
    "skill": "",
    "difficulty": "",
    "tags": []
  }
}
```

### Narration

You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_negotiation",
    "nocturnal",
    "transactional"
  ],
  "scene_tagline": "A Dangerous Delivery Agreed",
  "location_change": {
    "id": "marrows_crossing_streets",
    "name": "Marrow's Crossing Streets",
    "description": "Slick cobblestone streets illuminated by moonlight and flickering street lamps, near the town well."
  },
  "location_description": "The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum.",
  "npc_add": [
    {
      "id": "bystanders",
      "notes": "Quietly moving through the dark streets in the distance.",
      "name": "Bystanders",
      "title": null,
      "bio": null
    }
  ],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Left alone at the tavern table with the player's coins."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Accepting the player's terms and handing over a valuable leather-bound ledger.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "leather_bound_ledger",
      "name": "leather-bound ledger",
      "notes": "A heavy, valuable-looking volume handed over by Halden.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_contract_accepted",
      "text": "Halden has entrusted you with his leather-bound ledger for delivery.",
      "turn": 3
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': \"Ask Halden for more details about the ledger's contents.\"}",
    "{'text': 'Confirm the delivery route and any specific dangers to avoid.'}",
    "{'text': 'Ask Halden if he knows anything about the road toughs.'}",
    "{'text': 'Head straight toward the Crossed Keys Inn with the ledger.'}"
  ],
  "outcome_summary": "You successfully negotiated a contract with Halden, securing the leather-bound ledger for delivery to the Crossed Keys Inn.",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "leather_bound_ledger",
      "name": "Leather-bound ledger",
      "notes": "A heavy, valuable-looking volume handed over by Halden.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "marrows_crossing_streets",
    "name": "Marrow's Crossing Streets",
    "description": "Slick cobblestone streets illuminated by moonlight and flickering street lamps, near the town well."
  },
  "location_description": "The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum.",
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": true
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_negotiation",
    "nocturnal",
    "transactional"
  ],
  "scene_tagline": "A Dangerous Delivery Agreed",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "bystanders",
      "notes": "Quietly moving through the dark streets in the distance.",
      "name": "Bystanders"
    }
  ],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Left alone at the tavern table with the player's coins."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Accepting the player's terms and handing over a valuable leather-bound ledger."
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_contract_accepted",
      "text": "Halden has entrusted you with his leather-bound ledger for delivery.",
      "turn": 3
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'text': "Ask Halden for more details about the ledger's contents."}

- {'text': 'Confirm the delivery route and any specific dangers to avoid.'}

- {'text': 'Ask Halden if he knows anything about the road toughs.'}

- {'text': 'Head straight toward the Crossed Keys Inn with the ledger.'}

### Context Telemetry

- rules: est=1830t trimmed=False
- narrate: est=3903t trimmed=False
- extract.scene: est=2898t trimmed=False attempts=2
- extract.state: est=2636t trimmed=False attempts=1
- extract.progress: est=4145t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bystanders": {
        "from": null,
        "to": {
          "bio": "",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "marrows_crossing_streets",
            "location_name": "Marrow's Crossing Streets",
            "turn": 3
          },
          "name": "Bystanders",
          "title": ""
        }
      },
      "caron": {
        "last_seen_state": {
          "from": null,
          "to": "Left alone at the tavern table with the player's coins."
        }
      },
      "halden": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "marrows_crossing_streets",
            "location_name": "Marrow's Crossing Streets",
            "turn": 3
          }
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "leather_bound_ledger",
        "name": "Leather-bound ledger",
        "notes": "A heavy, valuable-looking volume handed over by Halden."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The tavern is filled with the scent of stale ale and woodsmoke, lit by flickering candlelight that casts long shadows across the scarred wooden tables.",
      "to": "Slick cobblestone streets illuminated by moonlight and flickering street lamps, near the town well."
    },
    "id": {
      "from": "marrows_crossing",
      "to": "marrows_crossing_streets"
    },
    "name": {
      "from": "Marrow's Crossing",
      "to": "Marrow's Crossing Streets"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "bystanders"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "from": {
        "beat_expires_turn": 4,
        "instruction": "Caron mentions the road is hungry, hinting at the danger ahead.",
        "surface_as": "npc_behavior",
        "type": "revelation"
      },
      "to": null
    },
    "turn": {
      "from": 2,
      "to": 3
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "deliver_the_ledger",
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": false,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        },
        "to": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 2,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        }
      }
    ]
  },
  "scene": {
    "location_entered_turn": {
      "from": null,
      "to": 2
    },
    "present_npcs": {
      "added": [
        {
          "bio": "",
          "id": "bystanders",
          "name": "Bystanders",
          "notes": "Quietly moving through the dark streets in the distance.",
          "title": ""
        }
      ],
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Watching the player with predatory stillness and unreadable, sharp eyes; waiting expectantly for an explanation.",
          "title": "Old creditor"
        },
        {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "id": "innkeeper",
          "name": "Edda",
          "notes": "Wiping down the bar at the Crossed Keys, which is two streets over.",
          "title": "Innkeeper at the Crossed Keys"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Stands near the town well, examining a map and a pressed wax seal.",
            "title": "Merchant"
          },
          "to": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Accepting the player's terms and handing over a valuable leather-bound ledger.",
            "title": "Merchant"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_contract_accepted",
          "text": "Halden has entrusted you with his leather-bound ledger for delivery.",
          "turn": 3
        }
      ]
    },
    "recently_left": {
      "from": null,
      "to": []
    },
    "recently_left_turns": {
      "from": null,
      "to": 0
    },
    "tagline": {
      "from": "A Debt Awaits",
      "to": "A Dangerous Delivery Agreed"
    },
    "tags": {
      "added": [
        "tense_negotiation",
        "nocturnal",
        "transactional"
      ],
      "removed": [
        "dimly_lit",
        "quiet",
        "tense_conversation"
      ]
    },
    "turn_entered": {
      "from": null,
      "to": 2
    }
  }
}
```


---

# TURN 4

**Input:** `I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Marrow's Crossing Streets
## last_turn (tail of the most recent narrative)
T3: I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. — You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

## Current Turn: 4
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## Location
Marrow's Crossing Streets (marrows_crossing_streets)
Slick cobblestone streets illuminated by moonlight and flickering street lamps, near the town well.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: A heavy, valuable-looking volume handed over by Halden.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has entrusted you with his leather-bound ledger for delivery.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 1** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.

**Turn 2** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

**Turn 3** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing Streets
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Accepting the player's terms and handing over a valuable leather-bound ledger.
- Bystanders — Quietly moving through the dark streets in the distance.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 4
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 4

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`marrows_crossing_streets` | Marrow's Crossing Streets
Slick cobblestone streets illuminated by moonlight and flickering street lamps, near the town well.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Accepting the player's terms and handing over a valuable leather-bound ledger.
- `bystanders` | Bystanders — Quietly moving through the dark streets in the distance.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T3 context)
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

## CURRENT TURN NARRATION
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 4

## active_domains
location_change, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_bound_ledger` | Leather-bound ledger ×1 — A heavy, valuable-looking volume handed over by Halden.

## scene_result
location: `merchant_road_east`
(location changed)
## CURRENT TURN NARRATION
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 4

## active_domains
location_change, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
travel: Aren leaves Marrow's Crossing via the east gate to deliver the ledger to the Crossed Keys Inn along the merchant road.
## prior_turn_narration (T3 — for outcome_summary and actions context)
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "travel",
  "intent": "Aren leaves Marrow's Crossing via the east gate to deliver the ledger to the Crossed Keys Inn along the merchant road.",
  "rolled": false,
  "total_ms": 2772.7,
  "tokens_in": 1609,
  "tokens_out": 1700
}
```

**Raw LLM output:**
```
{
  "intent": "Aren leaves Marrow's Crossing via the east gate to deliver the ledger to the Crossed Keys Inn along the merchant road.",
  "intent_verb": "travel",
  "target": "",
  "stakes": "",
  "check": {
    "required": false,
    "skill": "",
    "difficulty": "",
    "tags": []
  }
}
```

### Narration

The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

### Extract Scene

```json
{
  "scene_tags": [
    "travel",
    "tense",
    "atmospheric"
  ],
  "scene_tagline": "Into the Shadowed Road",
  "location_change": {
    "id": "merchant_road_east",
    "name": "Merchant Road (East)",
    "description": "A winding dirt and stone path flanked by skeletal trees and thickening mist rolling off the river."
  },
  "location_description": "The path transitions from cobblestones to gravel and dirt, bordered by a looming stone archway and a treeline of skeletal silhouettes.",
  "npc_add": [
    {
      "id": "ambient_wildlife",
      "notes": "An owl cries in the distance, adding to the heavy silence of the road.",
      "name": "Wildlife",
      "title": "Nature's Echo",
      "bio": null
    }
  ],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Left behind near the town well after handing over the ledger."
    },
    {
      "id": "bystanders",
      "last_seen_state": "Fading into the distance as the player exits the town."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "journey_begins",
      "text": "Aren Voss has departed Marrow's Crossing to deliver the ledger.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Keep a vigilant watch for any movement in the treeline.",
    "Pick up the pace to reach the inn before dawn.",
    "Search the roadside for any signs of recent travelers.",
    "Check the ledger for any clues about its importance."
  ],
  "outcome_summary": "You successfully depart Marrow's Crossing with the ledger, beginning your trek along the dark and misty merchant road.",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": [
    {
      "id": "road_toughs_threat",
      "text": "Rumors of road toughs lurking in the shadows.",
      "urgency": "building",
      "turn_added": 4,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "merchant_road_east",
    "name": "Merchant Road (East)",
    "description": "A winding dirt and stone path flanked by skeletal trees and thickening mist rolling off the river."
  },
  "location_description": "The path transitions from cobblestones to gravel and dirt, bordered by a looming stone archway and a treeline of skeletal silhouettes.",
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": true
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "travel",
    "tense",
    "atmospheric"
  ],
  "scene_tagline": "Into the Shadowed Road",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "ambient_wildlife",
      "notes": "An owl cries in the distance, adding to the heavy silence of the road.",
      "name": "Wildlife",
      "title": "Nature's Echo"
    }
  ],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Left behind near the town well after handing over the ledger."
    },
    {
      "id": "bystanders",
      "last_seen_state": "Fading into the distance as the player exits the town."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "journey_begins",
      "text": "Aren Voss has departed Marrow's Crossing to deliver the ledger.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "road_toughs_threat",
      "text": "Rumors of road toughs lurking in the shadows.",
      "urgency": "building",
      "turn_added": 4
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Keep a vigilant watch for any movement in the treeline.

- Pick up the pace to reach the inn before dawn.

- Search the roadside for any signs of recent travelers.

- Check the ledger for any clues about its importance.

### Context Telemetry

- rules: est=1887t trimmed=False
- narrate: est=4319t trimmed=False
- extract.scene: est=2843t trimmed=False attempts=1
- extract.state: est=2509t trimmed=False attempts=1
- extract.progress: est=3872t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "ambient_wildlife": {
        "from": null,
        "to": {
          "bio": "",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "merchant_road_east",
            "location_name": "Merchant Road (East)",
            "turn": 4
          },
          "name": "Wildlife",
          "title": "Nature's Echo"
        }
      },
      "bystanders": {
        "last_seen_state": {
          "from": null,
          "to": "Fading into the distance as the player exits the town."
        }
      },
      "halden": {
        "last_seen_state": {
          "from": null,
          "to": "Left behind near the town well after handing over the ledger."
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "Slick cobblestone streets illuminated by moonlight and flickering street lamps, near the town well.",
      "to": "A winding dirt and stone path flanked by skeletal trees and thickening mist rolling off the river."
    },
    "id": {
      "from": "marrows_crossing_streets",
      "to": "merchant_road_east"
    },
    "name": {
      "from": "Marrow's Crossing Streets",
      "to": "Merchant Road (East)"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "ambient_wildlife"
      ],
      "removed": []
    },
    "turn": {
      "from": 3,
      "to": 4
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 2,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        },
        "to": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 3,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        }
      }
    ]
  },
  "scene": {
    "location_entered_turn": {
      "from": 2,
      "to": 3
    },
    "present_npcs": {
      "added": [
        {
          "bio": "",
          "id": "ambient_wildlife",
          "name": "Wildlife",
          "notes": "An owl cries in the distance, adding to the heavy silence of the road.",
          "title": "Nature's Echo"
        }
      ],
      "removed": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Accepting the player's terms and handing over a valuable leather-bound ledger.",
          "title": "Merchant"
        },
        {
          "bio": "",
          "id": "bystanders",
          "name": "Bystanders",
          "notes": "Quietly moving through the dark streets in the distance.",
          "title": ""
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "journey_begins",
          "text": "Aren Voss has departed Marrow's Crossing to deliver the ledger.",
          "turn": 4
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "road_toughs_threat",
          "max_turns": null,
          "text": "Rumors of road toughs lurking in the shadows.",
          "turn_added": 4,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "A Dangerous Delivery Agreed",
      "to": "Into the Shadowed Road"
    },
    "tags": {
      "added": [
        "travel",
        "tense",
        "atmospheric"
      ],
      "removed": [
        "tense_negotiation",
        "nocturnal",
        "transactional"
      ]
    },
    "turn_entered": {
      "from": 2,
      "to": 3
    }
  }
}
```


---

# TURN 5

**Input:** `I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Merchant Road (East)
## last_turn (tail of the most recent narrative)
T4: I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. — The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

## Current Turn: 5
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## Location
Merchant Road (East) (merchant_road_east)
A winding dirt and stone path flanked by skeletal trees and thickening mist rolling off the river.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: A heavy, valuable-looking volume handed over by Halden.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Rumors of road toughs lurking in the shadows.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has entrusted you with his leather-bound ledger for delivery.
- Aren Voss has departed Marrow's Crossing to deliver the ledger.

## Prior History (summarized — treat as background, not current scene)



## Turn 1 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."

**Turn 3** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

**Turn 4** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 3 + 3 +1 (stat) = 7 → SETBACK
Directive: The persuade results in a setback. They're listening, but now they want something in return.

## Narration Directive







## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing Streets
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Wildlife (Nature's Echo) — An owl cries in the distance, adding to the heavy silence of the road.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 5
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 5

## rules_outcome
SETBACK on charisma — The persuade results in a setback. They're listening, but now they want something in return.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`merchant_road_east` | Merchant Road (East)
A winding dirt and stone path flanked by skeletal trees and thickening mist rolling off the river.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `ambient_wildlife` | Wildlife (Nature's Echo) — An owl cries in the distance, adding to the heavy silence of the road.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T4 context)
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

## CURRENT TURN NARRATION
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 5

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
SETBACK on charisma. The persuade results in a setback. They're listening, but now they want something in return.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: setback
directive: The persuade results in a setback. They're listening, but now they want something in return.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_bound_ledger` | Leather-bound ledger ×1 — A heavy, valuable-looking volume handed over by Halden.

## scene_result
location: `crossed_keys_inn_exterior`
(location changed)
## rules_stakes_hint
Rules engine named this cost on failure: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: the toughs may become hostile or refuse to speak, leading to a confrontation or being barred from the inn]
If the narration is ambiguous, treat any condition name in the above as a strong signal to apply it.
## CURRENT TURN NARRATION
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 5

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
SETBACK on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: Confront the two toughs at the inn door to demand an explanation for their presence.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [x] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has entrusted you with his leather-bound ledger for delivery.
- Aren Voss has departed Marrow's Crossing to deliver the ledger.

## prior_turn_narration (T4 — for outcome_summary and actions context)
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

## rules_stakes
Band: SETBACK. At-risk cost named by rules engine: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: the toughs may become hostile or refuse to speak, leading to a confrontation or being barred from the inn]
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## Current Pressures
- [road_toughs_threat] (building) Rumors of road toughs lurking in the shadows.

## CURRENT TURN NARRATION
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "Confront the two toughs at the inn door to demand an explanation for their presence.",
  "rolled": true,
  "total_ms": 3414.5,
  "tokens_in": 1546,
  "tokens_out": 1679,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    3,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 7,
  "band": "setback",
  "outcome_summary": "Your attempt to persuade the toughs fails; instead of an explanation, they demand a toll for your safe passage."
}
```

**Raw LLM output:**
```
{
  "intent": "Confront the two toughs at the inn door to demand an explanation for their presence.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: the toughs may become hostile or refuse to speak, leading to a confrontation or being barred from the inn]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "tense_conversation",
    "extortion"
  ],
  "scene_tagline": "A Toll for Safe Passage",
  "location_change": {
    "id": "crossed_keys_inn_exterior",
    "name": "Crossed Keys Inn",
    "description": "A heavy, timber-framed building with glowing amber windows, standing as a beacon of warmth against the misty road."
  },
  "location_description": "The entrance is guarded by a heavy oak door, set against the backdrop of a dim, amber-lit tavern.",
  "npc_add": [
    {
      "id": "tough_a",
      "notes": "Amused and unimpressed by the player's boldness; crossing his arms defiantly.",
      "name": "Bald Tough",
      "title": null,
      "bio": null
    },
    {
      "id": "tough_b",
      "notes": "Hostile and predatory; demanding a toll and eyeing the player's pack with intent.",
      "name": "Scarred Tough",
      "title": null,
      "bio": null
    }
  ],
  "npc_remove": [],
  "npc_update": [],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "shaken",
      "label": "shaken",
      "description": "The intimidating presence and demand for a toll from the toughs has rattled your composure."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "confrontation_at_crossed_keys",
      "text": "Aren Voss confronted the toughs guarding the Crossed Keys Inn.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Offer them a portion of your coin to let you pass.",
    "Threaten them with your iron dagger to demand their true purpose.",
    "Try to intimidate the Scarred Tough into revealing their employer.",
    "Attempt to slip past them into the inn unnoticed."
  ],
  "outcome_summary": "Your attempt to persuade the toughs fails; instead of an explanation, they demand a toll for your safe passage.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior",
    "instruction": "The Bald Tough and Scarred Tough begin to close the distance, blocking the entrance to the inn.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "inn_entrance_blockade",
      "text": "The toughs are actively extorting travelers at the inn entrance.",
      "urgency": "immediate",
      "turn_added": 5,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_exterior",
    "name": "Crossed Keys Inn",
    "description": "A heavy, timber-framed building with glowing amber windows, standing as a beacon of warmth against the misty road."
  },
  "location_description": "The entrance is guarded by a heavy oak door, set against the backdrop of a dim, amber-lit tavern.",
  "quest_updates": [],
  "pc_condition_add": [
    {
      "id": "shaken",
      "label": "shaken",
      "description": "The intimidating presence and demand for a toll from the toughs has rattled your composure."
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "confrontation",
    "tense_conversation",
    "extortion"
  ],
  "scene_tagline": "A Toll for Safe Passage",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Amused and unimpressed by the player's boldness; crossing his arms defiantly."
    },
    {
      "id": "tough_b",
      "notes": "Hostile and predatory; demanding a toll and eyeing the player's pack with intent."
    }
  ],
  "recent_events_add": [
    {
      "id": "confrontation_at_crossed_keys",
      "text": "Aren Voss confronted the toughs guarding the Crossed Keys Inn.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "inn_entrance_blockade",
      "text": "The toughs are actively extorting travelers at the inn entrance.",
      "urgency": "immediate",
      "turn_added": 5
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Offer them a portion of your coin to let you pass.

- Threaten them with your iron dagger to demand their true purpose.

- Try to intimidate the Scarred Tough into revealing their employer.

- Attempt to slip past them into the inn unnoticed.

### Context Telemetry

- rules: est=1828t trimmed=False
- narrate: est=4834t trimmed=False
- extract.scene: est=2908t trimmed=False attempts=1
- extract.state: est=2924t trimmed=False attempts=1
- extract.progress: est=4274t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "tough_a": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_exterior",
            "location_name": "Crossed Keys Inn",
            "turn": 5
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_exterior",
            "location_name": "Crossed Keys Inn",
            "turn": 5
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A winding dirt and stone path flanked by skeletal trees and thickening mist rolling off the river.",
      "to": "A heavy, timber-framed building with glowing amber windows, standing as a beacon of warmth against the misty road."
    },
    "id": {
      "from": "merchant_road_east",
      "to": "crossed_keys_inn_exterior"
    },
    "name": {
      "from": "Merchant Road (East)",
      "to": "Crossed Keys Inn"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "beat_expires_turn": 7,
        "instruction": "The Bald Tough and Scarred Tough begin to close the distance, blocking the entrance to the inn.",
        "surface_as": "npc_behavior",
        "type": "pressure"
      }
    },
    "turn": {
      "from": 4,
      "to": 5
    }
  },
  "pc": {
    "conditions": {
      "added": [
        {
          "added_turn": 4,
          "description": "The intimidating presence and demand for a toll from the toughs has rattled your composure.",
          "id": "shaken",
          "label": "shaken"
        }
      ]
    },
    "momentum": {
      "from": 0,
      "to": -1
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 3,
      "to": 4
    },
    "present_npcs": {
      "added": [
        {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Amused and unimpressed by the player's boldness; crossing his arms defiantly.",
          "title": "Road thug"
        },
        {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Hostile and predatory; demanding a toll and eyeing the player's pack with intent.",
          "title": "Road thug"
        }
      ],
      "removed": [
        {
          "bio": "",
          "id": "ambient_wildlife",
          "name": "Wildlife",
          "notes": "An owl cries in the distance, adding to the heavy silence of the road.",
          "title": "Nature's Echo"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "confrontation_at_crossed_keys",
          "text": "Aren Voss confronted the toughs guarding the Crossed Keys Inn.",
          "turn": 5
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "inn_entrance_blockade",
          "max_turns": null,
          "text": "The toughs are actively extorting travelers at the inn entrance.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "Into the Shadowed Road",
      "to": "A Toll for Safe Passage"
    },
    "tags": {
      "added": [
        "extortion",
        "confrontation",
        "tense_conversation"
      ],
      "removed": [
        "travel",
        "tense",
        "atmospheric"
      ]
    },
    "turn_entered": {
      "from": 3,
      "to": 4
    }
  }
}
```


---

# TURN 6

**Input:** `I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## scene
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T5: I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. — The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

## Current Turn: 6
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## Location
Crossed Keys Inn (crossed_keys_inn_exterior)
A heavy, timber-framed building with glowing amber windows, standing as a beacon of warmth against the misty road.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: A heavy, valuable-looking volume handed over by Halden.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Rumors of road toughs lurking in the shadows.
- [IMMEDIATE] The toughs are actively extorting travelers at the inn entrance.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has entrusted you with his leather-bound ledger for delivery.
- Aren Voss has departed Marrow's Crossing to deliver the ledger.
- Aren Voss confronted the toughs guarding the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## Turn 1 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

The heavy scent of stale ale and woodsmoke hangs thick in the air of the tavern as you navigate the narrow space between tables. **Caron** doesn't look up immediately when you approach; he remains focused on the amber liquid in his cup, his weathered hands steady despite the dim, flickering candlelight. The tavern is quiet, the evening lull settling over the room like a heavy shroud, leaving only the distant murmur of the river outside to fill the silence.

As you pull out the heavy wooden chair and settle your weight against your bruised ribs, the chair screeches against the floorboards. Caron finally lifts his gaze. His eyes are sharp, unreadable, and possess a predatory stillness that suggests he has been counting every second of your absence. He sets his cup down with a deliberate click and leans forward, his shadow stretching long across the scarred tabletop toward you.

"You took your time, Voss," he says, his voice a low rasp that barely carries past the edge of the table. He doesn't offer a greeting or a smile. Instead, he simply taps a thick, calloused finger against the wood, waiting for you to prove you haven't brought more excuses along with your heavy pack.


## Turn 2 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You reach into your pouch and pull out the heavy clink of **Credits**, sliding the pile of coin across the scarred wood toward him. The metal rings softly against the table, a sharp, transactional sound that cuts through the tavern's low hum. You meet his gaze, your voice steady despite the ache in your ribs, and tell him clearly that you want the debt marked as cleared.

**Caron** doesn't reach for the coin immediately. Instead, he stares at the pile as if weighing the worth of your soul against the metal. A slow, humorless smirk tugs at the corner of his mouth, though his eyes remain as cold as the river outside. He reaches out, his thick fingers grazing the coins as he pulls them toward his chest, tucking them out of sight with a practiced, greedy motion.

"A heavy price for a heavy name, Voss," he mutters, reaching into a leather pouch at his belt. He produces a small, battered ledger and flips through the parchment pages with a rhythmic *thwip-thwip-thwip*. He finds a page, pulls a charcoal stub from his vest, and makes a sharp, decisive mark next to your name. He slams the book shut and leans back, the predatory tension in his shoulders relaxing only slightly. "Consider it done. But don't think this makes us friends. The road is a hungry thing, and it doesn't care if you're free or not."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 3** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push away from the table, leaving **Caron** alone with his stolen coins and his grim warnings. The tavern air feels stifling compared to the biting chill of the night as you step out into the streets of Marrow's Crossing. The cobblestones are slick with moisture, and the distant sound of the river provides a constant, low-frequency thrum beneath the quiet footsteps of the town.

You find **Halden** near the stone lip of the town well, his silhouette hunched under the moonlight. He is squinting at a parchment map, his thumb tracing a pressed wax seal with obsessive focus. The flickering light from a nearby street lamp catches the gray in his beard and the weary lines etched into his forehead.

"I have a proposal, Halden," you say, approaching him through the gloom. You state your terms clearly: you will take his ledger and deliver it safely to the Crossed Keys Inn for a fee of 200 credits.

**Halden** looks up, his eyes blinking against the sudden intrusion of your voice. He studies your face, his gaze lingering on the heavy pack on your shoulders and the guarded expression you wear. He sighs, a sound of pure exhaustion, and tucks the map into a leather satchel. "The road has been unkind lately, Voss. If you can get it there without it falling into the wrong hands, the coin is yours." He reaches into his heavy tunic and produces a thick, leather-bound volume, handing it to you with a reverence that suggests the contents are worth far more than the gold you've requested.

**Turn 4** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

**Turn 5** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 3 + 3 +1 (stat) = 7 → SETBACK
Directive: The deceive results in a setback. They're listening, but now they want something in return.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (PRESSURE, surface as npc_behavior):
The Bald Tough and Scarred Tough begin to close the distance, blocking the entrance to the inn.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive







## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing Streets
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Inn
- **Scarred Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Bald Tough (Road thug) — Amused and unimpressed by the player's boldness; crossing his arms defiantly.
- Scarred Tough (Road thug) — Hostile and predatory; demanding a toll and eyeing the player's pack with intent.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 6
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 6

## rules_outcome
SETBACK on charisma — The deceive results in a setback. They're listening, but now they want something in return.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_exterior` | Crossed Keys Inn
A heavy, timber-framed building with glowing amber windows, standing as a beacon of warmth against the misty road.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | Bald Tough (Road thug) — Amused and unimpressed by the player's boldness; crossing his arms defiantly.
- `tough_b` | Scarred Tough (Road thug) — Hostile and predatory; demanding a toll and eyeing the player's pack with intent.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T5 context)
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

## CURRENT TURN NARRATION
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 6

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
SETBACK on charisma. The deceive results in a setback. They're listening, but now they want something in return.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: setback
directive: The deceive results in a setback. They're listening, but now they want something in return.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.
- `shaken` | shaken — The intimidating presence and demand for a toll from the toughs has rattled your composure.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_bound_ledger` | Leather-bound ledger ×1 — A heavy, valuable-looking volume handed over by Halden.

## scene_result
location: `crossed_keys_inn_exterior`

## rules_stakes_hint
Rules engine named this cost on failure: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The toughs reject the bribe and turn violent or demand more.]
If the narration is ambiguous, treat any condition name in the above as a strong signal to apply it.
## CURRENT TURN NARRATION
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 6

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
SETBACK on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
deceive: The player offers 200 credits as a bribe to the toughs to avoid conflict and leave them alone.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [x] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has entrusted you with his leather-bound ledger for delivery.
- Aren Voss has departed Marrow's Crossing to deliver the ledger.
- Aren Voss confronted the toughs guarding the Crossed Keys Inn.

## prior_turn_narration (T5 — for outcome_summary and actions context)
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

## items_lost
credits

## rules_stakes
Band: SETBACK. At-risk cost named by rules engine: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The toughs reject the bribe and turn violent or demand more.]
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## Current Pressures
- [road_toughs_threat] (building) Rumors of road toughs lurking in the shadows.
- [inn_entrance_blockade] (immediate) The toughs are actively extorting travelers at the inn entrance.

## CURRENT TURN NARRATION
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "deceive",
  "intent": "The player offers 200 credits as a bribe to the toughs to avoid conflict and leave them alone.",
  "rolled": true,
  "total_ms": 3477.2,
  "tokens_in": 1686,
  "tokens_out": 1818,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    3,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 7,
  "band": "setback",
  "outcome_summary": "The bribe is rejected; the Bald Tough and Scarred Tough flank you, turning the extortion attempt into a direct physical confrontation."
}
```

**Raw LLM output:**
```
{
  "intent": "The player offers 200 credits as a bribe to the toughs to avoid conflict and leave them alone.",
  "intent_verb": "deceive",
  "target": "Bald Tough and Scarred Tough",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The toughs reject the bribe and turn violent or demand more.]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "tense",
    "imminent_combat"
  ],
  "scene_tagline": "A Toll Too Low",
  "location_change": null,
  "location_description": "The damp cobblestones and gravel of the inn's entrance are now littered with scattered credits.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "No longer amused; has uncrossed his arms and is curling his fists, moving to flank the player to block the inn entrance.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "tough_b",
      "notes": "Hostile and predatory; has dropped his false politeness and is closing the distance to box the player in.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 50
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Draw your weapon and prepare for a fight.",
    "Try to reason with them further despite the setback.",
    "Attempt to bolt past them toward the inn entrance.",
    "Call out for help from the tavern patrons."
  ],
  "outcome_summary": "The bribe is rejected; the Bald Tough and Scarred Tough flank you, turning the extortion attempt into a direct physical confrontation.",
  "gm_beat": {
    "type": "escalation",
    "surface_as": "npc_behavior",
    "instruction": "The Bald Tough and Scarred Tough initiate a coordinated strike to box Aren Voss against the wall.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "imminent_combat",
      "text": "The toughs are closing in for a violent confrontation.",
      "urgency": "immediate",
      "turn_added": 6,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [
    "inn_entrance_blockade"
  ],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 50
    }
  ],
  "inventory_update": [],
  "location_description": "The damp cobblestones and gravel of the inn's entrance are now littered with scattered credits.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "confrontation",
    "tense",
    "imminent_combat"
  ],
  "scene_tagline": "A Toll Too Low",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "No longer amused; has uncrossed his arms and is curling his fists, moving to flank the player to block the inn entrance."
    },
    {
      "id": "tough_b",
      "notes": "Hostile and predatory; has dropped his false politeness and is closing the distance to box the player in."
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "imminent_combat",
      "text": "The toughs are closing in for a violent confrontation.",
      "urgency": "immediate",
      "turn_added": 6
    }
  ],
  "scene_pressure_remove": [
    "inn_entrance_blockade"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Draw your weapon and prepare for a fight.

- Try to reason with them further despite the setback.

- Attempt to bolt past them toward the inn entrance.

- Call out for help from the tavern patrons.

### Context Telemetry

- rules: est=1964t trimmed=False
- narrate: est=5579t trimmed=False
- extract.scene: est=3020t trimmed=False attempts=1
- extract.state: est=2875t trimmed=False attempts=1
- extract.progress: est=4388t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 5,
            "to": 6
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "turn": {
            "from": 5,
            "to": 6
          }
        }
      }
    }
  },
  "inventory": {
    "changed": [
      {
        "from": {
          "aliases": [],
          "amount": 500,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        },
        "to": {
          "aliases": [],
          "amount": 450,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        }
      }
    ]
  },
  "location": {
    "description": {
      "from": "A heavy, timber-framed building with glowing amber windows, standing as a beacon of warmth against the misty road.",
      "to": "The damp cobblestones and gravel of the inn's entrance are now littered with scattered credits."
    }
  },
  "meta": {
    "last_compacted_turn": {
      "from": 0,
      "to": 3
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 7,
        "to": 8
      },
      "instruction": {
        "from": "The Bald Tough and Scarred Tough begin to close the distance, blocking the entrance to the inn.",
        "to": "The Bald Tough and Scarred Tough initiate a coordinated strike to box Aren Voss against the wall."
      },
      "type": {
        "from": "pressure",
        "to": "escalation"
      }
    },
    "prior_history": {
      "added": [
        "- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.",
        "- [T1] Voss met with Caron at the tavern to address the outstanding debt.",
        "- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger."
      ],
      "removed": []
    },
    "turn": {
      "from": 5,
      "to": 6
    }
  },
  "pc": {
    "momentum": {
      "from": -1,
      "to": -2
    }
  },
  "scene": {
    "present_npcs": {
      "changed": [
        {
          "from": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Amused and unimpressed by the player's boldness; crossing his arms defiantly.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "No longer amused; has uncrossed his arms and is curling his fists, moving to flank the player to block the inn entrance.",
            "title": "Road thug"
          }
        },
        {
          "from": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Hostile and predatory; demanding a toll and eyeing the player's pack with intent.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Hostile and predatory; has dropped his false politeness and is closing the distance to box the player in.",
            "title": "Road thug"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "debt_cleared",
          "text": "Your debt to Caron has been settled in full.",
          "turn": 2
        },
        {
          "id": "halden_ledger_contract",
          "text": "Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.",
          "turn": 3
        },
        {
          "id": "road_toughs_rumors",
          "text": "Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.",
          "turn": 6
        }
      ],
      "removed": [
        {
          "id": "you_arrived_in_marrows_crossing_after",
          "text": "You arrived in Marrow's Crossing after three days on the road.",
          "turn": 0
        },
        {
          "id": "you_heard_rumors_of_roadtoughs_extorting",
          "text": "You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.",
          "turn": 0
        },
        {
          "id": "you_found_caron_in_the_tavern",
          "text": "You found Caron in the tavern \u2014 he's been waiting for you.",
          "turn": 0
        },
        {
          "id": "halden_contract_accepted",
          "text": "Halden has entrusted you with his leather-bound ledger for delivery.",
          "turn": 3
        },
        {
          "id": "journey_begins",
          "text": "Aren Voss has departed Marrow's Crossing to deliver the ledger.",
          "turn": 4
        },
        {
          "id": "confrontation_at_crossed_keys",
          "text": "Aren Voss confronted the toughs guarding the Crossed Keys Inn.",
          "turn": 5
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "imminent_combat",
          "max_turns": null,
          "text": "The toughs are closing in for a violent confrontation.",
          "turn_added": 6,
          "urgency": "immediate"
        }
      ],
      "removed": [
        {
          "id": "inn_entrance_blockade",
          "max_turns": null,
          "text": "The toughs are actively extorting travelers at the inn entrance.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Toll for Safe Passage",
      "to": "A Toll Too Low"
    },
    "tags": {
      "added": [
        "imminent_combat",
        "tense"
      ],
      "removed": [
        "extortion",
        "tense_conversation"
      ]
    }
  }
}
```


---

# TURN 7

**Input:** `I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## scene
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T6: I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. — You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

## Current Turn: 7
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## Location
Crossed Keys Inn (crossed_keys_inn_exterior)
The damp cobblestones and gravel of the inn's entrance are now littered with scattered credits.

## inventory (cross-reference before describing item use)
- **Credits** ×450: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: A heavy, valuable-looking volume handed over by Halden.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Rumors of road toughs lurking in the shadows.
- [IMMEDIATE] The toughs are closing in for a violent confrontation.
## Recent Events
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Voss met with Caron at the tavern to address the outstanding debt.
- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.



## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 4** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.

**Turn 5** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

**Turn 6** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 4 + 6 +1 (stat) = 11 → SUCCESS
Directive: The persuade succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (ESCALATION, surface as npc_behavior):
The Bald Tough and Scarred Tough initiate a coordinated strike to box Aren Voss against the wall.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing Streets
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Inn
- **Scarred Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Bald Tough (Road thug) — No longer amused; has uncrossed his arms and is curling his fists, moving to flank the player to block the inn entrance.
- Scarred Tough (Road thug) — Hostile and predatory; has dropped his false politeness and is closing the distance to box the player in.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 7
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 7

## rules_outcome
SUCCESS on charisma — The persuade succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_exterior` | Crossed Keys Inn
The damp cobblestones and gravel of the inn's entrance are now littered with scattered credits.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | Bald Tough (Road thug) — No longer amused; has uncrossed his arms and is curling his fists, moving to flank the player to block the inn entrance.
- `tough_b` | Scarred Tough (Road thug) — Hostile and predatory; has dropped his false politeness and is closing the distance to box the player in.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T6 context)
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

## CURRENT TURN NARRATION
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 7

## active_domains
scene, inventory

## rules_outcome
SUCCESS on charisma. The persuade succeeds cleanly. Clean success — you do what you intended.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: success
directive: The persuade succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×450 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_bound_ledger` | Leather-bound ledger ×1 — A heavy, valuable-looking volume handed over by Halden.

## scene_result
location: `crossed_keys_inn_interior`
(location changed)
## CURRENT TURN NARRATION
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 7

## active_domains
scene, inventory

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to use the merchant seal and ledger to convince Halden to allow them to pass or provide assistance.
## prior_turn_narration (T6 — for outcome_summary and actions context)
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

## items_lost
leather_bound_ledger

## rules_stakes
Band: SUCCESS. At-risk cost named by rules engine: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: Halden rejects the bribe/documents, leaving the player vulnerable to the toughs without protection or an ally.]
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## deescalate
A pressure resolved this turn (magnitude: 0.6).
Partial deescalation. Prefer low-urgency beat or no beat.
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## Current Pressures
- [road_toughs_threat] (building) Rumors of road toughs lurking in the shadows.
- [imminent_combat] (immediate) The toughs are closing in for a violent confrontation.

## CURRENT TURN NARRATION
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to use the merchant seal and ledger to convince Halden to allow them to pass or provide assistance.",
  "rolled": true,
  "total_ms": 3558.0,
  "tokens_in": 1642,
  "tokens_out": 1779,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    4,
    6
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 11,
  "band": "success",
  "outcome_summary": "You successfully use the bribe and your authority to bypass the toughs and deliver the ledger to Halden, who is visibly relieved."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the merchant seal and ledger to convince Halden to allow them to pass or provide assistance.",
  "intent_verb": "persuade",
  "target": "Halden",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: Halden rejects the bribe/documents, leaving the player vulnerable to the toughs without protection or an ally.]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_standoff",
    "relief",
    "negotiation"
  ],
  "scene_tagline": "A Costly Peace",
  "location_change": {
    "id": "crossed_keys_inn_interior",
    "name": "Crossed Keys Inn",
    "description": "A warm common room filled with the scent of roasted meat and stale ale, providing a sharp contrast to the misty exterior."
  },
  "location_description": null,
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Standing in a defensive, watchful stance outside the inn entrance."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Watching the player with narrowed, hateful eyes from the doorway."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Visibly relieved and trembling as he inspects the ledger and merchant seal.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "leather_bound_ledger",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_receives_ledger",
      "text": "Halden has received the leather-bound ledger and merchant seal.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Ask Halden for more information regarding Caron's business.",
    "Request protection or a safe room from Halden for the night.",
    "Inquire if the road toughs are part of a larger gang.",
    "Order a drink and try to blend into the inn's crowd."
  ],
  "outcome_summary": "You successfully use the bribe and your authority to bypass the toughs and deliver the ledger to Halden, who is visibly relieved.",
  "gm_beat": {
    "type": "opportunity",
    "surface_as": "npc_behavior",
    "instruction": "Halden leans in closer, whispering a warning about the growing influence of the road toughs.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "imminent_combat"
  ],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "leather_bound_ledger",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_interior",
    "name": "Crossed Keys Inn",
    "description": "A warm common room filled with the scent of roasted meat and stale ale, providing a sharp contrast to the misty exterior."
  },
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": true
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_standoff",
    "relief",
    "negotiation"
  ],
  "scene_tagline": "A Costly Peace",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Standing in a defensive, watchful stance outside the inn entrance."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Watching the player with narrowed, hateful eyes from the doorway."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Visibly relieved and trembling as he inspects the ledger and merchant seal."
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_receives_ledger",
      "text": "Halden has received the leather-bound ledger and merchant seal.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "imminent_combat"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Ask Halden for more information regarding Caron's business.

- Request protection or a safe room from Halden for the night.

- Inquire if the road toughs are part of a larger gang.

- Order a drink and try to blend into the inn's crowd.

### Context Telemetry

- rules: est=1897t trimmed=False
- narrate: est=4879t trimmed=False
- extract.scene: est=3094t trimmed=False attempts=1
- extract.state: est=2779t trimmed=False attempts=1
- extract.progress: est=4182t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "last_seen_state": {
            "from": "",
            "to": "Left behind near the town well after handing over the ledger."
          },
          "location_id": {
            "from": "marrows_crossing_streets",
            "to": "crossed_keys_inn_interior"
          },
          "location_name": {
            "from": "Marrow's Crossing Streets",
            "to": "Crossed Keys Inn"
          },
          "turn": {
            "from": 3,
            "to": 7
          }
        }
      },
      "tough_a": {
        "last_seen_state": {
          "from": null,
          "to": "Standing in a defensive, watchful stance outside the inn entrance."
        }
      },
      "tough_b": {
        "last_seen_state": {
          "from": null,
          "to": "Watching the player with narrowed, hateful eyes from the doorway."
        }
      }
    }
  },
  "inventory": {
    "removed": [
      {
        "amount": 1,
        "id": "leather_bound_ledger",
        "name": "Leather-bound ledger",
        "notes": "A heavy, valuable-looking volume handed over by Halden."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The damp cobblestones and gravel of the inn's entrance are now littered with scattered credits.",
      "to": "A warm common room filled with the scent of roasted meat and stale ale, providing a sharp contrast to the misty exterior."
    },
    "id": {
      "from": "crossed_keys_inn_exterior",
      "to": "crossed_keys_inn_interior"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 8,
        "to": 9
      },
      "instruction": {
        "from": "The Bald Tough and Scarred Tough initiate a coordinated strike to box Aren Voss against the wall.",
        "to": "Halden leans in closer, whispering a warning about the growing influence of the road toughs."
      },
      "type": {
        "from": "escalation",
        "to": "opportunity"
      }
    },
    "turn": {
      "from": 6,
      "to": 7
    }
  },
  "pc": {
    "momentum": {
      "from": -2,
      "to": -1
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 3,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        },
        "to": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 6,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        }
      }
    ]
  },
  "scene": {
    "location_entered_turn": {
      "from": 4,
      "to": 6
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Visibly relieved and trembling as he inspects the ledger and merchant seal.",
          "title": "Merchant"
        }
      ],
      "removed": [
        {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "No longer amused; has uncrossed his arms and is curling his fists, moving to flank the player to block the inn entrance.",
          "title": "Road thug"
        },
        {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Hostile and predatory; has dropped his false politeness and is closing the distance to box the player in.",
          "title": "Road thug"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_receives_ledger",
          "text": "Halden has received the leather-bound ledger and merchant seal.",
          "turn": 7
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "imminent_combat",
          "max_turns": null,
          "text": "The toughs are closing in for a violent confrontation.",
          "turn_added": 6,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Toll Too Low",
      "to": "A Costly Peace"
    },
    "tags": {
      "added": [
        "tense_standoff",
        "negotiation",
        "relief"
      ],
      "removed": [
        "imminent_combat",
        "confrontation",
        "tense"
      ]
    },
    "turn_entered": {
      "from": 4,
      "to": 6
    }
  }
}
```


---

# TURN 8

**Input:** `I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## scene
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T7: I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. — The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

## Current Turn: 8
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## Location
Crossed Keys Inn (crossed_keys_inn_interior)
A warm common room filled with the scent of roasted meat and stale ale, providing a sharp contrast to the misty exterior.

## inventory (cross-reference before describing item use)
- **Credits** ×450: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Rumors of road toughs lurking in the shadows.
## Recent Events
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Voss met with Caron at the tavern to address the outstanding debt.
- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"

**Turn 6** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

**Turn 7** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: normal
Roll: 3 + 6 +1 (stat) = 10 → SUCCESS
Directive: The sneak succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (OPPORTUNITY, surface as npc_behavior):
Halden leans in closer, whispering a warning about the growing influence of the road toughs.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Crossed Keys Inn: Left behind near the town well after handing over the ledger.
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Inn
- **Scarred Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Halden (Merchant) — Visibly relieved and trembling as he inspects the ledger and merchant seal.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 8
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 8

## rules_outcome
SUCCESS on dexterity — The sneak succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_interior` | Crossed Keys Inn
A warm common room filled with the scent of roasted meat and stale ale, providing a sharp contrast to the misty exterior.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Visibly relieved and trembling as he inspects the ledger and merchant seal.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T7 context)
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

## CURRENT TURN NARRATION
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 8

## active_domains
scene, inventory

## rules_outcome
SUCCESS on dexterity. The sneak succeeds cleanly. Clean success — you do what you intended.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: dexterity
band: success
directive: The sneak succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×450 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_back_passage`
(location changed)
## CURRENT TURN NARRATION
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 8

## active_domains
scene, inventory

## rules_outcome
SUCCESS on dexterity.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
sneak: The player attempts to use the brass key to find a back room or exit within the inn.
## prior_turn_narration (T7 — for outcome_summary and actions context)
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

## rules_stakes
Band: SUCCESS. At-risk cost named by rules engine: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The innkeeper or guards notice the suspicious activity and confront the player.]
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## deescalate
A pressure resolved this turn (magnitude: 0.6).
Partial deescalation. Prefer low-urgency beat or no beat.
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## Current Pressures
- [road_toughs_threat] (building) Rumors of road toughs lurking in the shadows.

## CURRENT TURN NARRATION
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "sneak",
  "intent": "The player attempts to use the brass key to find a back room or exit within the inn.",
  "rolled": true,
  "total_ms": 3466.4,
  "tokens_in": 1706,
  "tokens_out": 1835,
  "skill": "dexterity",
  "difficulty": "normal",
  "dice": [
    3,
    6
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": "You successfully use the brass key to unlock a hidden passage, bypassing the main common room."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the brass key to find a back room or exit within the inn.",
  "intent_verb": "sneak",
  "target": "inn's back room door",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The innkeeper or guards notice the suspicious activity and confront the player.]",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "discovery"
  ],
  "scene_tagline": "A Shadow Over the Road",
  "location_change": {
    "id": "crossed_keys_inn_back_passage",
    "name": "Back Passage",
    "description": "A dim, narrow passage tucked behind a velvet curtain near the entryway."
  },
  "location_description": "A secondary, dark-wood door near the entryway leads into a narrow, dimly lit passage.",
  "npc_add": [
    {
      "id": "inn_patrons",
      "notes": "Glancing up at the player's sudden movement as they head toward the back door.",
      "name": "Inn Patrons",
      "title": null,
      "bio": null
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Anxious and paranoid, clutching the ledger to his chest and warning the player about the thugs outside.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_warning",
      "text": "Halden reveals the road toughs have wider connections near the river banks.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Explore the narrow passage behind the secondary door.'}",
    "{'text': 'Ask Halden more about the shadow growing over the road.'}",
    "{'text': 'Keep a watchful eye on the toughs through the window.'}",
    "{'text': 'Search the back rooms for a more discreet exit.'}"
  ],
  "outcome_summary": "You successfully use the brass key to unlock a hidden passage, bypassing the main common room.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "Halden's nervous glances suggest he knows more about the river bank connections than he is letting on.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "road_toughs_threat"
  ],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_back_passage",
    "name": "Back Passage",
    "description": "A dim, narrow passage tucked behind a velvet curtain near the entryway."
  },
  "location_description": "A secondary, dark-wood door near the entryway leads into a narrow, dimly lit passage.",
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": true
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_conversation",
    "discovery"
  ],
  "scene_tagline": "A Shadow Over the Road",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "inn_patrons",
      "notes": "Glancing up at the player's sudden movement as they head toward the back door.",
      "name": "Inn Patrons"
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Anxious and paranoid, clutching the ledger to his chest and warning the player about the thugs outside."
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_warning",
      "text": "Halden reveals the road toughs have wider connections near the river banks.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "road_toughs_threat"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'text': 'Explore the narrow passage behind the secondary door.'}

- {'text': 'Ask Halden more about the shadow growing over the road.'}

- {'text': 'Keep a watchful eye on the toughs through the window.'}

- {'text': 'Search the back rooms for a more discreet exit.'}

### Context Telemetry

- rules: est=2027t trimmed=False
- narrate: est=5426t trimmed=False
- extract.scene: est=3054t trimmed=False attempts=1
- extract.state: est=2629t trimmed=False attempts=1
- extract.progress: est=4137t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "location_id": {
            "from": "crossed_keys_inn_interior",
            "to": "crossed_keys_inn_back_passage"
          },
          "location_name": {
            "from": "Crossed Keys Inn",
            "to": "Back Passage"
          },
          "turn": {
            "from": 7,
            "to": 8
          }
        }
      },
      "inn_patrons": {
        "from": null,
        "to": {
          "bio": "",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_back_passage",
            "location_name": "Back Passage",
            "turn": 8
          },
          "name": "Inn Patrons",
          "title": ""
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A warm common room filled with the scent of roasted meat and stale ale, providing a sharp contrast to the misty exterior.",
      "to": "A dim, narrow passage tucked behind a velvet curtain near the entryway."
    },
    "id": {
      "from": "crossed_keys_inn_interior",
      "to": "crossed_keys_inn_back_passage"
    },
    "name": {
      "from": "Crossed Keys Inn",
      "to": "Back Passage"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "inn_patrons"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 9,
        "to": 10
      },
      "instruction": {
        "from": "Halden leans in closer, whispering a warning about the growing influence of the road toughs.",
        "to": "Halden's nervous glances suggest he knows more about the river bank connections than he is letting on."
      },
      "type": {
        "from": "opportunity",
        "to": "revelation"
      }
    },
    "turn": {
      "from": 7,
      "to": 8
    }
  },
  "pc": {
    "momentum": {
      "from": -1,
      "to": 0
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 6,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        },
        "to": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 7,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        }
      }
    ]
  },
  "scene": {
    "location_entered_turn": {
      "from": 6,
      "to": 7
    },
    "present_npcs": {
      "added": [
        {
          "bio": "",
          "id": "inn_patrons",
          "name": "Inn Patrons",
          "notes": "Glancing up at the player's sudden movement as they head toward the back door.",
          "title": ""
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Visibly relieved and trembling as he inspects the ledger and merchant seal.",
            "title": "Merchant"
          },
          "to": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Anxious and paranoid, clutching the ledger to his chest and warning the player about the thugs outside.",
            "title": "Merchant"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_warning",
          "text": "Halden reveals the road toughs have wider connections near the river banks.",
          "turn": 8
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "road_toughs_threat",
          "max_turns": null,
          "text": "Rumors of road toughs lurking in the shadows.",
          "turn_added": 4,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "A Costly Peace",
      "to": "A Shadow Over the Road"
    },
    "tags": {
      "added": [
        "discovery",
        "tense_conversation"
      ],
      "removed": [
        "tense_standoff",
        "negotiation",
        "relief"
      ]
    },
    "turn_entered": {
      "from": 6,
      "to": 7
    }
  }
}
```


---

# TURN 9

**Input:** `I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## scene
Location: Back Passage
## last_turn (tail of the most recent narrative)
T8: I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. — The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

## Current Turn: 9
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## Location
Back Passage (crossed_keys_inn_back_passage)
A dim, narrow passage tucked behind a velvet curtain near the entryway.

## inventory (cross-reference before describing item use)
- **Credits** ×450: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Voss met with Caron at the tavern to address the outstanding debt.
- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.


## Turn 5 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 6** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."

**Turn 7** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

**Turn 8** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 1 + 3 +1 (stat) = 5 → FAIL
Directive: The deceive fails. The attempt fails outright — what you tried to do does not happen.

GM DIRECTION (REVELATION, surface as npc_behavior):
Halden's nervous glances suggest he knows more about the river bank connections than he is letting on.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Inn Patrons** — last seen Back Passage
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Back Passage: Left behind near the town well after handing over the ledger.
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Inn
- **Scarred Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Halden (Merchant) — Anxious and paranoid, clutching the ledger to his chest and warning the player about the thugs outside.
- Inn Patrons — Glancing up at the player's sudden movement as they head toward the back door.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 9
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 9

## rules_outcome
FAIL on charisma — The deceive fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_back_passage` | Back Passage
A dim, narrow passage tucked behind a velvet curtain near the entryway.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Anxious and paranoid, clutching the ledger to his chest and warning the player about the thugs outside.
- `inn_patrons` | Inn Patrons — Glancing up at the player's sudden movement as they head toward the back door.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T8 context)
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

## CURRENT TURN NARRATION
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 9

## active_domains
scene, inventory

## rules_outcome
FAIL on charisma. The deceive fails. The attempt fails outright — what you tried to do does not happen.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: fail
directive: The deceive fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×450 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_back_passage`

## rules_stakes_hint
Rules engine named this cost on failure: [Mechanical cost: none] + [Narrative consequence: The player's presence is discovered by someone behind the wall, potentially alerting the thugs or inn staff]
If the narration is ambiguous, treat any condition name in the above as a strong signal to apply it.
## CURRENT TURN NARRATION
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 9

## active_domains
scene, inventory

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
deceive: The player attempts to bribe the wall or an unseen entity behind it with a single credit.
## prior_turn_narration (T8 — for outcome_summary and actions context)
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

## items_lost
credits

## rules_stakes
Band: FAIL. At-risk cost named by rules engine: [Mechanical cost: none] + [Narrative consequence: The player's presence is discovered by someone behind the wall, potentially alerting the thugs or inn staff]
If a narrative consequence is named above (e.g. an NPC acting, alarm raised, escape cut off), emit it as a scene_pressure_add entry at `immediate` urgency.
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "deceive",
  "intent": "The player attempts to bribe the wall or an unseen entity behind it with a single credit.",
  "rolled": true,
  "total_ms": 3391.3,
  "tokens_in": 1625,
  "tokens_out": 1754,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    1,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 5,
  "band": "fail",
  "outcome_summary": "Your attempt to bribe the wall fails fruitlessly, but the silence is broken by a sudden, unsettling scrape of leather from the darkness ahead."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the wall or an unseen entity behind it with a single credit.",
  "intent_verb": "deceive",
  "target": "the unseen entity behind the wall",
  "stakes": "[Mechanical cost: none] + [Narrative consequence: The player's presence is discovered by someone behind the wall, potentially alerting the thugs or inn staff]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

### Extract Scene

```json
{
  "scene_tags": [
    "stealth",
    "tense",
    "suspense"
  ],
  "scene_tagline": "A Scrape in the Dark",
  "location_change": null,
  "location_description": "The air is stagnant, smelling of damp stone and old grease, with uneven masonry walls.",
  "npc_add": [
    {
      "id": "unknown_presence",
      "notes": "An unidentified presence making a sharp scraping sound further down the passage.",
      "name": "Unknown Presence",
      "title": "Shadowy Figure",
      "bio": "A mysterious entity moving through the darkness of the back passage."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Left behind in the common room; no longer present in the back passage.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "inn_patrons",
      "notes": "Muffled sounds of patrons can be heard from the main room, but they are no longer directly interacting with the player.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "scraping_sound_in_passage",
      "text": "A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Draw your weapon and prepare to confront the source of the noise.",
    "Call out into the darkness to demand identification from the intruder.",
    "Quietly retreat back through the velvet curtain into the common room.",
    "Search the narrow passage for any hidden doors or exits."
  ],
  "outcome_summary": "Your attempt to bribe the wall fails fruitlessly, but the silence is broken by a sudden, unsettling scrape of leather from the darkness ahead.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "environmental",
    "instruction": "The source of the scraping sound emerges from the shadows of the Back Passage.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "intruder_in_passage",
      "text": "An unknown presence is moving through the narrow Back Passage.",
      "urgency": "immediate",
      "turn_added": 9,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_description": "The air is stagnant, smelling of damp stone and old grease, with uneven masonry walls.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "stealth",
    "tense",
    "suspense"
  ],
  "scene_tagline": "A Scrape in the Dark",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "unknown_presence",
      "notes": "An unidentified presence making a sharp scraping sound further down the passage.",
      "name": "Unknown Presence",
      "title": "Shadowy Figure",
      "bio": "A mysterious entity moving through the darkness of the back passage."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Left behind in the common room; no longer present in the back passage."
    },
    {
      "id": "inn_patrons",
      "notes": "Muffled sounds of patrons can be heard from the main room, but they are no longer directly interacting with the player."
    }
  ],
  "recent_events_add": [
    {
      "id": "scraping_sound_in_passage",
      "text": "A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "intruder_in_passage",
      "text": "An unknown presence is moving through the narrow Back Passage.",
      "urgency": "immediate",
      "turn_added": 9
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Draw your weapon and prepare to confront the source of the noise.

- Call out into the darkness to demand identification from the intruder.

- Quietly retreat back through the velvet curtain into the common room.

- Search the narrow passage for any hidden doors or exits.

### Context Telemetry

- rules: est=1912t trimmed=False
- narrate: est=5908t trimmed=False
- extract.scene: est=2854t trimmed=False attempts=1
- extract.state: est=2600t trimmed=False attempts=1
- extract.progress: est=3882t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "turn": {
            "from": 8,
            "to": 9
          }
        }
      },
      "inn_patrons": {
        "last_seen": {
          "turn": {
            "from": 8,
            "to": 9
          }
        }
      },
      "unknown_presence": {
        "from": null,
        "to": {
          "bio": "A mysterious entity moving through the darkness of the back passage.",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_back_passage",
            "location_name": "Back Passage",
            "turn": 9
          },
          "name": "Unknown Presence",
          "title": "Shadowy Figure"
        }
      }
    }
  },
  "inventory": {
    "changed": [
      {
        "from": {
          "aliases": [],
          "amount": 450,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        },
        "to": {
          "aliases": [],
          "amount": 449,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        }
      }
    ]
  },
  "location": {
    "description": {
      "from": "A dim, narrow passage tucked behind a velvet curtain near the entryway.",
      "to": "The air is stagnant, smelling of damp stone and old grease, with uneven masonry walls."
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "unknown_presence"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 10,
        "to": 11
      },
      "instruction": {
        "from": "Halden's nervous glances suggest he knows more about the river bank connections than he is letting on.",
        "to": "The source of the scraping sound emerges from the shadows of the Back Passage."
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "environmental"
      },
      "type": {
        "from": "revelation",
        "to": "pressure"
      }
    },
    "turn": {
      "from": 8,
      "to": 9
    }
  },
  "pc": {
    "momentum": {
      "from": 0,
      "to": -1
    }
  },
  "scene": {
    "present_npcs": {
      "added": [
        {
          "bio": "A mysterious entity moving through the darkness of the back passage.",
          "id": "unknown_presence",
          "name": "Unknown Presence",
          "notes": "An unidentified presence making a sharp scraping sound further down the passage.",
          "title": "Shadowy Figure"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Anxious and paranoid, clutching the ledger to his chest and warning the player about the thugs outside.",
            "title": "Merchant"
          },
          "to": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Left behind in the common room; no longer present in the back passage.",
            "title": "Merchant"
          }
        },
        {
          "from": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "Glancing up at the player's sudden movement as they head toward the back door.",
            "title": ""
          },
          "to": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "Muffled sounds of patrons can be heard from the main room, but they are no longer directly interacting with the player.",
            "title": ""
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "scraping_sound_in_passage",
          "text": "A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.",
          "turn": 9
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "intruder_in_passage",
          "max_turns": null,
          "text": "An unknown presence is moving through the narrow Back Passage.",
          "turn_added": 9,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Shadow Over the Road",
      "to": "A Scrape in the Dark"
    },
    "tags": {
      "added": [
        "stealth",
        "suspense",
        "tense"
      ],
      "removed": [
        "discovery",
        "tense_conversation"
      ]
    }
  }
}
```


---

# TURN 10

**Input:** `I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## scene
Location: Back Passage
## last_turn (tail of the most recent narrative)
T9: I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall. — The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

## Current Turn: 10
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## Location
Back Passage (crossed_keys_inn_back_passage)
The air is stagnant, smelling of damp stone and old grease, with uneven masonry walls.

## inventory (cross-reference before describing item use)
- **Credits** ×449: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] An unknown presence is moving through the narrow Back Passage.
## Recent Events
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.
- A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Voss met with Caron at the tavern to address the outstanding debt.
- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.


## Turn 5 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"


## Turn 6 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.

You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 7** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.

**Turn 8** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

**Turn 9** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 4 + 5 +1 (stat) = 10 → SUCCESS
Directive: The intimidate succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (PRESSURE, surface as environmental):
The source of the scraping sound emerges from the shadows of the Back Passage.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Unknown Presence** — last seen Back Passage
- **Inn Patrons** — last seen Back Passage
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Back Passage: Left behind near the town well after handing over the ledger.
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Inn
- **Scarred Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Halden (Merchant) — Left behind in the common room; no longer present in the back passage.
- Inn Patrons — Muffled sounds of patrons can be heard from the main room, but they are no longer directly interacting with the player.
- Unknown Presence (Shadowy Figure) — An unidentified presence making a sharp scraping sound further down the passage.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 10
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 10

## rules_outcome
SUCCESS on charisma — The intimidate succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_back_passage` | Back Passage
The air is stagnant, smelling of damp stone and old grease, with uneven masonry walls.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Left behind in the common room; no longer present in the back passage.
- `inn_patrons` | Inn Patrons — Muffled sounds of patrons can be heard from the main room, but they are no longer directly interacting with the player.
- `unknown_presence` | Unknown Presence (Shadowy Figure) — An unidentified presence making a sharp scraping sound further down the passage.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T9 context)
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

## CURRENT TURN NARRATION
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 10

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
SUCCESS on charisma. The intimidate succeeds cleanly. Clean success — you do what you intended.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: success
directive: The intimidate succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.
- `shaken` | shaken — The intimidating presence and demand for a toll from the toughs has rattled your composure.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×449 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_common_room`
(location changed)
## CURRENT TURN NARRATION
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 10

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
intimidate: Aren confronts Matthew Estrada at the bar to demand his true identity and purpose.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [x] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.
- A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.

## prior_turn_narration (T9 — for outcome_summary and actions context)
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

## rules_stakes
Band: SUCCESS. At-risk cost named by rules engine: [Mechanical cost: charisma check] + [Narrative consequence: Matthew reacts defensively or alerts others to Aren's aggression]
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## deescalate
A pressure resolved this turn (magnitude: 0.6).
Partial deescalation. Prefer low-urgency beat or no beat.
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## Current Pressures
- [intruder_in_passage] (immediate) An unknown presence is moving through the narrow Back Passage.

## CURRENT TURN NARRATION
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "intimidate",
  "intent": "Aren confronts Matthew Estrada at the bar to demand his true identity and purpose.",
  "rolled": true,
  "total_ms": 3096.9,
  "tokens_in": 1525,
  "tokens_out": 1639,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    4,
    5
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": "Your intimidation attempt fails to rattle Matthew, who meets your aggression with unsettling, disciplined calm."
}
```

**Raw LLM output:**
```
{
  "intent": "Aren confronts Matthew Estrada at the bar to demand his true identity and purpose.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "stakes": "[Mechanical cost: charisma check] + [Narrative consequence: Matthew reacts defensively or alerts others to Aren's aggression]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "social_interaction"
  ],
  "scene_tagline": "A Soldier's Calm Gaze",
  "location_change": {
    "id": "crossed_keys_inn_common_room",
    "name": "Common Room",
    "description": "A boisterous, warm space thick with the scent of roasted meat and the din of rowdy patrons."
  },
  "location_description": null,
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Left behind in the back passage."
    },
    {
      "id": "unknown_presence",
      "last_seen_state": "Making a scraping sound in the darkness of the back passage."
    }
  ],
  "npc_update": [
    {
      "id": "inn_patrons",
      "notes": "The patrons are boisterous and rowdy, largely oblivious to the player's confrontation.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "matthew_estrada",
      "notes": "Sitting rigidly near the bar; remains calm and unreadable despite the player's aggressive physical contact.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Demand Matthew reveal his true identity and military background.",
    "Offer Matthew a bribe to gain information on the toughs.",
    "Scan the room to see if Matthew's reaction alerted anyone.",
    "Release Matthew and attempt to strike up a casual conversation."
  ],
  "outcome_summary": "Your intimidation attempt fails to rattle Matthew, who meets your aggression with unsettling, disciplined calm.",
  "gm_beat": {
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "Matthew Estrada leans in closer, whispering a cryptic warning about the person watching from the shadows.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "intruder_in_passage"
  ],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_common_room",
    "name": "Common Room",
    "description": "A boisterous, warm space thick with the scent of roasted meat and the din of rowdy patrons."
  },
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_confrontation",
    "social_interaction"
  ],
  "scene_tagline": "A Soldier's Calm Gaze",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Left behind in the back passage."
    },
    {
      "id": "unknown_presence",
      "last_seen_state": "Making a scraping sound in the darkness of the back passage."
    }
  ],
  "npc_update": [
    {
      "id": "inn_patrons",
      "notes": "The patrons are boisterous and rowdy, largely oblivious to the player's confrontation."
    },
    {
      "id": "matthew_estrada",
      "notes": "Sitting rigidly near the bar; remains calm and unreadable despite the player's aggressive physical contact."
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "intruder_in_passage"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Demand Matthew reveal his true identity and military background.

- Offer Matthew a bribe to gain information on the toughs.

- Scan the room to see if Matthew's reaction alerted anyone.

- Release Matthew and attempt to strike up a casual conversation.

### Context Telemetry

- rules: est=1795t trimmed=False
- narrate: est=6420t trimmed=False
- extract.scene: est=2879t trimmed=False attempts=1
- extract.state: est=2729t trimmed=False attempts=1
- extract.progress: est=4200t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen_state": {
          "from": "Left behind near the town well after handing over the ledger.",
          "to": "Left behind in the back passage."
        }
      },
      "inn_patrons": {
        "last_seen": {
          "location_id": {
            "from": "crossed_keys_inn_back_passage",
            "to": "crossed_keys_inn_common_room"
          },
          "location_name": {
            "from": "Back Passage",
            "to": "Common Room"
          },
          "turn": {
            "from": 9,
            "to": 10
          }
        }
      },
      "matthew_estrada": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_common_room",
            "location_name": "Common Room",
            "turn": 10
          }
        }
      },
      "unknown_presence": {
        "last_seen_state": {
          "from": null,
          "to": "Making a scraping sound in the darkness of the back passage."
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The air is stagnant, smelling of damp stone and old grease, with uneven masonry walls.",
      "to": "A boisterous, warm space thick with the scent of roasted meat and the din of rowdy patrons."
    },
    "id": {
      "from": "crossed_keys_inn_back_passage",
      "to": "crossed_keys_inn_common_room"
    },
    "name": {
      "from": "Back Passage",
      "to": "Common Room"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 11,
        "to": 12
      },
      "instruction": {
        "from": "The source of the scraping sound emerges from the shadows of the Back Passage.",
        "to": "Matthew Estrada leans in closer, whispering a cryptic warning about the person watching from the shadows."
      },
      "surface_as": {
        "from": "environmental",
        "to": "npc_behavior"
      },
      "type": {
        "from": "pressure",
        "to": "revelation"
      }
    },
    "turn": {
      "from": 9,
      "to": 10
    }
  },
  "pc": {
    "momentum": {
      "from": -1,
      "to": 0
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 7,
      "to": 9
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
          "id": "matthew_estrada",
          "name": "Matthew Estrada",
          "notes": "Sitting rigidly near the bar; remains calm and unreadable despite the player's aggressive physical contact.",
          "title": "Traveler"
        }
      ],
      "removed": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Left behind in the common room; no longer present in the back passage.",
          "title": "Merchant"
        },
        {
          "bio": "A mysterious entity moving through the darkness of the back passage.",
          "id": "unknown_presence",
          "name": "Unknown Presence",
          "notes": "An unidentified presence making a sharp scraping sound further down the passage.",
          "title": "Shadowy Figure"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "Muffled sounds of patrons can be heard from the main room, but they are no longer directly interacting with the player.",
            "title": ""
          },
          "to": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "The patrons are boisterous and rowdy, largely oblivious to the player's confrontation.",
            "title": ""
          }
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "intruder_in_passage",
          "max_turns": null,
          "text": "An unknown presence is moving through the narrow Back Passage.",
          "turn_added": 9,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Scrape in the Dark",
      "to": "A Soldier's Calm Gaze"
    },
    "tags": {
      "added": [
        "social_interaction",
        "tense_confrontation"
      ],
      "removed": [
        "stealth",
        "suspense",
        "tense"
      ]
    },
    "turn_entered": {
      "from": 7,
      "to": 9
    }
  }
}
```


---

# TURN 11

**Input:** `Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## scene
Location: Common Room
## last_turn (tail of the most recent narrative)
T10: I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier. — You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

## Current Turn: 11
=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## Location
Common Room (crossed_keys_inn_common_room)
A boisterous, warm space thick with the scent of roasted meat and the din of rowdy patrons.

## inventory (cross-reference before describing item use)
- **Credits** ×449: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.
- A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Voss met with Caron at the tavern to address the outstanding debt.
- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the **Leather-bound ledger** settles against your hip, a heavy and significant presence that makes your journey feel less like a walk and more like a mission. You turn away from the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road.

The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately.

Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**.


## Turn 5 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw.

As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story.

The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances."

The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?"


## Turn 6 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.

You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now."

The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger.

"Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?"

The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins."


## Turn 7 — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.

The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth.

The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass.

You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table.

The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 8** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist.

"You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs."

Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

**Turn 9** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

**Turn 10** — I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Strength (3) | Difficulty: hard
Roll: 2 + 6 +1 (stat) -1 (diff) = 8 → PARTIAL
Directive: The strength results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.

GM DIRECTION (REVELATION, surface as npc_behavior):
Matthew Estrada leans in closer, whispering a cryptic warning about the person watching from the shadows.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Unknown Presence** — last seen Back Passage
- **Inn Patrons** — last seen Common Room
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Back Passage: Left behind near the town well after handing over the ledger.
- **Edda**
- **Matthew Estrada** — last seen Common Room
- **Bald Tough** — last seen Crossed Keys Inn
- **Scarred Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Inn Patrons — The patrons are boisterous and rowdy, largely oblivious to the player's confrontation.
- Matthew Estrada (Traveler) — Sitting rigidly near the bar; remains calm and unreadable despite the player's aggressive physical contact.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 11
=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 11

## rules_outcome
PARTIAL on strength — The strength results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_common_room` | Common Room
A boisterous, warm space thick with the scent of roasted meat and the din of rowdy patrons.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `inn_patrons` | Inn Patrons — The patrons are boisterous and rowdy, largely oblivious to the player's confrontation.
- `matthew_estrada` | Matthew Estrada (Traveler) — Sitting rigidly near the bar; remains calm and unreadable despite the player's aggressive physical contact.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T10 context)
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

## CURRENT TURN NARRATION
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 11

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
PARTIAL on strength. The strength results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: strength
band: partial
directive: The strength results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.
- `shaken` | shaken — The intimidating presence and demand for a toll from the toughs has rattled your composure.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×449 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_common_room`

## CURRENT TURN NARRATION
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 11

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
PARTIAL on strength.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
strength: Tackle the bodyguard into the bar shelves and search his coat while he is dazed.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [x] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.
- A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.

## prior_turn_narration (T10 — for outcome_summary and actions context)
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

## items_gained
leather pouch, folded parchment

## rules_stakes
Band: PARTIAL. At-risk cost named by rules engine: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The bodyguard recovers quickly to retaliate or Matthew intervenes to defend his guard.]
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "strength",
  "intent": "Tackle the bodyguard into the bar shelves and search his coat while he is dazed.",
  "rolled": true,
  "total_ms": 3551.4,
  "tokens_in": 1591,
  "tokens_out": 1730,
  "skill": "strength",
  "difficulty": "hard",
  "dice": [
    2,
    6
  ],
  "stat_mod": 1,
  "diff_mod": -1,
  "cond_mod": 0,
  "final_total": 8,
  "band": "partial",
  "outcome_summary": "You successfully tackle the bodyguard into the shelves and loot a leather pouch and parchment from his coat, though your actions have caused a scene and drawn unwanted attention."
}
```

**Raw LLM output:**
```
{
  "intent": "Tackle the bodyguard into the bar shelves and search his coat while he is dazed.",
  "intent_verb": "strength",
  "target": "Matthew's bodyguard",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The bodyguard recovers quickly to retaliate or Matthew intervenes to defend his guard.]",
  "check": {
    "required": true,
    "skill": "strength",
    "difficulty": "hard",
    "tags": [
      "combat",
      "physical"
    ]
  }
}
```

### Narration

The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "tension",
    "stealth_interrupted",
    "chaos"
  ],
  "scene_tagline": "A Violent Scramble for Clues",
  "location_change": null,
  "location_description": "The area behind the bar is now a mess of shattered glass, spilled ale, and expensive oils following the collision.",
  "npc_add": [
    {
      "id": "bodyguard_youth",
      "notes": "Dazed and gasping for air after being tackled into the shelving.",
      "name": "Wiry Youth",
      "title": "Bodyguard",
      "bio": "A nervous, wiry man who serves as Matthew Estrada's protector."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "inn_patrons",
      "notes": "Startled into a sudden silence by the sound of breaking glass and the violent collision.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "matthew_estrada",
      "notes": "Watching the player with profound, weary disappointment; remains calm and warns the player about a hidden observer.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "leather_pouch",
      "name": "leather pouch",
      "notes": "A small, heavy pouch found on the bodyguard's person.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "folded_parchment",
      "name": "folded parchment",
      "notes": "A piece of parchment found tucked in the bodyguard's inner pocket.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "glass_cuts",
      "label": "glass cuts",
      "description": "Stinging shards of glass from the shattered bottles have grazed your arm."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "tavern_brawl_start",
      "text": "A violent struggle between Voss and Matthew's guard has drawn the attention of the entire tavern.",
      "turn": 11
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Quickly hide the stolen pouch and parchment before anyone notices.",
    "Demand to know who is watching from the shadows.",
    "Attempt to apologize to Matthew to de-escalate the tavern's tension.",
    "Scan the darkened corners of the room for the hidden observer."
  ],
  "outcome_summary": "You successfully tackle the bodyguard into the shelves and loot a leather pouch and parchment from his coat, though your actions have caused a scene and drawn unwanted attention.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "environmental",
    "instruction": "The tavern patrons begin to murmur and stand up, some reaching for weapons as the tension rises.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "tavern_attention",
      "text": "The tavern patrons are alerted to the brawl and may intervene.",
      "urgency": "immediate",
      "turn_added": 11,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "leather_pouch",
      "name": "Leather pouch",
      "notes": "A small, heavy pouch found on the bodyguard's person.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "folded_parchment",
      "name": "Folded parchment",
      "notes": "A piece of parchment found tucked in the bodyguard's inner pocket.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The area behind the bar is now a mess of shattered glass, spilled ale, and expensive oils following the collision.",
  "quest_updates": [],
  "pc_condition_add": [
    {
      "id": "glass_cuts",
      "label": "glass cuts",
      "description": "Stinging shards of glass from the shattered bottles have grazed your arm."
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "combat",
    "tension",
    "stealth_interrupted",
    "chaos"
  ],
  "scene_tagline": "A Violent Scramble for Clues",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "bodyguard_youth",
      "notes": "Dazed and gasping for air after being tackled into the shelving.",
      "name": "Wiry Youth",
      "title": "Bodyguard",
      "bio": "A nervous, wiry man who serves as Matthew Estrada's protector."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "inn_patrons",
      "notes": "Startled into a sudden silence by the sound of breaking glass and the violent collision."
    },
    {
      "id": "matthew_estrada",
      "notes": "Watching the player with profound, weary disappointment; remains calm and warns the player about a hidden observer."
    }
  ],
  "recent_events_add": [
    {
      "id": "tavern_brawl_start",
      "text": "A violent struggle between Voss and Matthew's guard has drawn the attention of the entire tavern.",
      "turn": 11
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "tavern_attention",
      "text": "The tavern patrons are alerted to the brawl and may intervene.",
      "urgency": "immediate",
      "turn_added": 11
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Quickly hide the stolen pouch and parchment before anyone notices.

- Demand to know who is watching from the shadows.

- Attempt to apologize to Matthew to de-escalate the tavern's tension.

- Scan the darkened corners of the room for the hidden observer.

### Context Telemetry

- rules: est=1879t trimmed=False
- narrate: est=6796t trimmed=False
- extract.scene: est=3033t trimmed=False attempts=1
- extract.state: est=2835t trimmed=False attempts=1
- extract.progress: est=4329t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bodyguard_youth": {
        "from": null,
        "to": {
          "bio": "A nervous, wiry man who serves as Matthew Estrada's protector.",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_common_room",
            "location_name": "Common Room",
            "turn": 11
          },
          "name": "Wiry Youth",
          "title": "Bodyguard"
        }
      },
      "inn_patrons": {
        "last_seen": {
          "turn": {
            "from": 10,
            "to": 11
          }
        }
      },
      "matthew_estrada": {
        "last_seen": {
          "turn": {
            "from": 10,
            "to": 11
          }
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "leather_pouch",
        "name": "Leather pouch",
        "notes": "A small, heavy pouch found on the bodyguard's person."
      },
      {
        "amount": 1,
        "id": "folded_parchment",
        "name": "Folded parchment",
        "notes": "A piece of parchment found tucked in the bodyguard's inner pocket."
      }
    ]
  },
  "location": {
    "description": {
      "from": "A boisterous, warm space thick with the scent of roasted meat and the din of rowdy patrons.",
      "to": "The area behind the bar is now a mess of shattered glass, spilled ale, and expensive oils following the collision."
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "bodyguard_youth"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 12,
        "to": 13
      },
      "instruction": {
        "from": "Matthew Estrada leans in closer, whispering a cryptic warning about the person watching from the shadows.",
        "to": "The tavern patrons begin to murmur and stand up, some reaching for weapons as the tension rises."
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "environmental"
      },
      "type": {
        "from": "revelation",
        "to": "pressure"
      }
    },
    "turn": {
      "from": 10,
      "to": 11
    }
  },
  "pc": {
    "conditions": {
      "added": [
        {
          "added_turn": 10,
          "description": "Stinging shards of glass from the shattered bottles have grazed your arm.",
          "id": "glass_cuts",
          "label": "glass cuts"
        }
      ]
    }
  },
  "scene": {
    "present_npcs": {
      "added": [
        {
          "bio": "A nervous, wiry man who serves as Matthew Estrada's protector.",
          "id": "bodyguard_youth",
          "name": "Wiry Youth",
          "notes": "Dazed and gasping for air after being tackled into the shelving.",
          "title": "Bodyguard"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "The patrons are boisterous and rowdy, largely oblivious to the player's confrontation.",
            "title": ""
          },
          "to": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "Startled into a sudden silence by the sound of breaking glass and the violent collision.",
            "title": ""
          }
        },
        {
          "from": {
            "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
            "id": "matthew_estrada",
            "name": "Matthew Estrada",
            "notes": "Sitting rigidly near the bar; remains calm and unreadable despite the player's aggressive physical contact.",
            "title": "Traveler"
          },
          "to": {
            "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
            "id": "matthew_estrada",
            "name": "Matthew Estrada",
            "notes": "Watching the player with profound, weary disappointment; remains calm and warns the player about a hidden observer.",
            "title": "Traveler"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "tavern_brawl_start",
          "text": "A violent struggle between Voss and Matthew's guard has drawn the attention of the entire tavern.",
          "turn": 11
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "tavern_attention",
          "max_turns": null,
          "text": "The tavern patrons are alerted to the brawl and may intervene.",
          "turn_added": 11,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Soldier's Calm Gaze",
      "to": "A Violent Scramble for Clues"
    },
    "tags": {
      "added": [
        "chaos",
        "tension",
        "stealth_interrupted",
        "combat"
      ],
      "removed": [
        "social_interaction",
        "tense_confrontation"
      ]
    }
  }
}
```


---

# TURN 12

**Input:** `I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken, glass cuts

## scene
Location: Common Room
## last_turn (tail of the most recent narrative)
T11: Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed. — The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."

## Current Turn: 12
=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken, glass cuts

## Location
Common Room (crossed_keys_inn_common_room)
The area behind the bar is now a mess of shattered glass, spilled ale, and expensive oils following the collision.

## inventory (cross-reference before describing item use)
- **Credits** ×449: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather pouch**: A small, heavy pouch found on the bodyguard's person.
- **Folded parchment**: A piece of parchment found tucked in the bodyguard's inner pocket.

## Quests
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] The tavern patrons are alerted to the brawl and may intervene.
## Recent Events
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.
- A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.
- A violent struggle between Voss and Matthew's guard has drawn the attention of the entire tavern.

## Prior History (summarized — treat as background, not current scene)
the stone well, leaving **Halden** to his maps and his quiet anxieties, and head toward the eastern edge of Marrow's Crossing. The town's lights fade behind you, replaced by the rhythmic crunch of gravel and the thickening shadows of the merchant road. The air grows colder as you pass through the east gate, the stone archway looming like a silent sentry against the moonlight. The road ahead stretches out into the darkness, a ribbon of dirt and stone winding between the silhouettes of skeletal trees. You keep a steady pace, your eyes scanning the treeline and the dips in the road, acutely aware of the rumors regarding the toughs who have been making life difficult for travelers lately. Progress is slow as the moonlight struggles to pierce the thickening mist rolling off the nearby river. The silence of the road is heavy, broken only by the occasional rustle of wind through the brush or the distant, lonely cry of an owl. Every shadow seems to stretch a little too far, and every snap of a twig underfoot makes your hand drift instinctively toward the hilt of your **Iron dagger**. ## Turn 5 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. The *Crossed Keys Inn* looms out of the mist like a heavy, timber-framed beast, its windows glowing with a dim, amber light that does little to pierce the gloom of the merchant road. Standing directly in front of the heavy oak entrance are two men, their silhouettes broad and imposing against the tavern's warmth. One is a massive, thick-necked man with a shaved head, and the other is leaner, with a jagged, prominent scar running from temple to jaw. As you approach, your footsteps heavy on the stone, the **Bald Tough** shifts his weight, crossing his massive arms over a leather jerkin. The **Scarred Tough** spits a glob of dark phlegm onto the road, his eyes narrowing as he tracks your movement toward them. You stop a few paces away, your voice cutting through the damp air as you demand to know what they are doing here and insist on hearing their side of the story. The **Bald Tough** lets out a low, rumbling chuckle that sounds like stones grinding together. He doesn't look intimidated; if anything, he looks amused by your sudden boldness. "Listen to this one," he says, glancing at his companion. "Thinks he's a magistrate coming to hear our grievances." The **Scarred Tough** steps forward, moving out of the shadow of the doorway to stand level with his partner. He doesn't look amused. He reaches out, resting a hand on the hilt of a heavy club hanging at his belt, his gaze fixed on the heavy pack at your hip. "We're just making sure the road stays... orderly, traveler," he says, his voice dripping with a false, oily politeness. "And 'order' usually comes with a toll. You look like a man who can afford to contribute to our services. Why don't you reach into that pouch and show us just how much you value your safe passage?" ## Turn 6 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. You reach into your pouch and pull out a heavy handful of **Credits**, letting them spill from your fingers. The coins clatter and scatter across the damp cobblestones between you and the two men, a bright, metallic sound that seems too loud in the heavy mist. "Caron's coin is paid," you state, your voice hard and final. "You can go home now." The **Bald Tough** looks down at the scattered wealth, his amusement vanishing as his gaze shifts from the coins back to your face. The silence that follows is thick and suffocating. The **Scarred Tough** doesn't reach for the money; instead, he takes a heavy, deliberate step toward you, his boots crunching loudly on the gravel. The false politeness has completely drained from his expression, replaced by a cold, predatory hunger. "Caron's coin?" the **Scarred Tough** repeats, his voice dropping an octave into a dangerous snarl. He doesn't look like a man who is about to walk away. "You think we're some street urchins looking for scraps from a merchant's table?" The **Bald Tough** uncrosses his massive arms, his hands curling into thick, heavy fists at his sides. He steps out from the doorway, moving to flank you and cutting off your path toward the inn's entrance. The two of them begin to close the distance, boxing you in against the stone wall of the building. "You've got a lot of nerve, Voss," the **Bald Tough** rumbles, his shadow looming over you. "But we don't take orders from couriers. If you want to pass, you're going to pay a lot more than just a few coins." ## Turn 7 — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. The tension of the confrontation at the door breaks not with a blow, but with the heavy, undeniable weight of your words and the undeniable sight of the coin. The **Scarred Tough** hesitates, his gaze darting between your steady eyes and the glinting **Credits** on the ground. The mention of Caron seems to strike a chord of recognition or perhaps a warning of a name they'd rather not tangle with; the predatory hunger in his eyes flickers and dies, replaced by a begrudging, sullen realization that you are more trouble than the immediate payout is worth. The **Bald Tough** grunts, a sound of pure irritation, and holds up a hand to signal his partner to stand down. They don't apologize—men like this don't have the temperament for it—but the immediate threat of violence recedes as they settle into a defensive, watchful stance, watching you with narrowed, hateful eyes as if waiting for you to slip up. The heavy pressure of the standoff lifts, leaving only the damp chill of the night and the quiet, rhythmic breathing of the two men as they watch you pass. You push past them, your boots clicking softly on the stone as you enter the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted meat and stale ale, a sharp contrast to the misty gloom outside. You navigate the crowded common room toward a quiet corner where **Halden** sits hunched over a small, candlelit table. The merchant looks up, his face etched with a visible relief that seems to drain the tension from his shoulders as you approach. Without a word, you reach into your coat and produce the **Leather-bound ledger**, sliding it across the scarred wood of the table toward him. You follow this by sliding the merchant seal toward him as well, the heavy objects coming to rest near his trembling hands. **Halden** stares at the ledger for a long moment, his fingers grazing the leather as if confirming it is indeed real, and he lets out a long, shaky exhale of pure relief. ## Turn 8 — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. The heavy tension of the standoff at the entrance has dissipated, replaced by the low hum of tavern chatter and the crackle of the hearth. You take a seat near **Halden**, the warmth of the common room seeping into your bruised ribs and soothing the chill of the road. The merchant doesn't reach for his coin pouch immediately; instead, he holds the ledger to his chest like a shield, his eyes darting toward the window where the silhouettes of the two toughs can still be seen lurking in the mist. "You did well to get inside, Voss," **Halden** whispers, leaning across the table so his voice barely carries over the clinking of tankards. He glances toward the door, his voice dropping to a gravelly murmur. "Those men out there... they aren't just idle bullies. They've been seen whispering with travelers near the river banks. There's a shadow growing over this road, and it has more reach than a few men with clubs." Ignoring the merchant's warning for a moment, you reach into your pocket and retrieve the **Brass key**. You stand and navigate toward the heavy oak door you just passed through, moving past a few patrons who glance up at your sudden movement. You find a smaller, secondary door tucked into the corner of the entryway, partially obscured by a heavy velvet curtain. The wood here is darker, less polished than the main entrance. You fit the key into the tarnished lock and turn it; with a heavy, satisfying *thunk*, the mechanism gives way, and the door creaks open just enough to reveal a dim, narrow passage leading toward the back of the inn.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 9** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
The heavy velvet curtain muffles the rowdy laughter of the common room as you slip into the narrow confines of the **Back Passage**. The air here is stagnant, smelling of damp stone and old grease. You lean your head against the cold, uneven surface of the wall, pressing your ear against the masonry to catch any sound of movement or conversation from the other side.

"I have credits. Open up," you whisper toward the stone, your voice barely a breath. You reach into your pouch and pull out a single **Credit**, pressing the cold coin against the rough surface of the wall as if it were a sentient thing capable of commerce.

The stone remains indifferent. There is no click of a latch, no voice from the other side, only the oppressive silence of the passage and the distant, muffled thud of a tankard hitting a table in the main room. The attempt to bribe the very architecture of the *Crossed Keys Inn* yields nothing but a hollow ache in your ears and the realization that the wall has no interest in your coin.

A sudden, sharp scrape of leather against stone echoes from further down the passage, coming from the darkness ahead.

**Turn 10** — I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

**Turn 11** — Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: normal
Roll: 3 + 1 +1 (stat) = 5 → FAIL
Directive: The escape fails. The attempt fails outright — what you tried to do does not happen.

GM DIRECTION (PRESSURE, surface as environmental):
The tavern patrons begin to murmur and stand up, some reaching for weapons as the tension rises.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Wiry Youth** — last seen Common Room
- **Unknown Presence** — last seen Back Passage
- **Inn Patrons** — last seen Common Room
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Back Passage: Left behind near the town well after handing over the ledger.
- **Edda**
- **Matthew Estrada** — last seen Common Room
- **Bald Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Inn Patrons — Startled into a sudden silence by the sound of breaking glass and the violent collision.
- Matthew Estrada (Traveler) — Watching the player with profound, weary disappointment; remains calm and warns the player about a hidden observer.
- Wiry Youth (Bodyguard) — Dazed and gasping for air after being tackled into the shelving.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 12
=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 12

## rules_outcome
FAIL on dexterity — The escape fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken, glass cuts

## location
`crossed_keys_inn_common_room` | Common Room
The area behind the bar is now a mess of shattered glass, spilled ale, and expensive oils following the collision.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `inn_patrons` | Inn Patrons — Startled into a sudden silence by the sound of breaking glass and the violent collision.
- `matthew_estrada` | Matthew Estrada (Traveler) — Watching the player with profound, weary disappointment; remains calm and warns the player about a hidden observer.
- `bodyguard_youth` | Wiry Youth (Bodyguard) — Dazed and gasping for air after being tackled into the shelving.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T11 context)
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."

## CURRENT TURN NARRATION
Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 12

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
FAIL on dexterity. The escape fails. The attempt fails outright — what you tried to do does not happen.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: dexterity
band: fail
directive: The escape fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.
- `shaken` | shaken — The intimidating presence and demand for a toll from the toughs has rattled your composure.
- `glass_cuts` | glass cuts — Stinging shards of glass from the shattered bottles have grazed your arm.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×449 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_pouch` | Leather pouch ×1 — A small, heavy pouch found on the bodyguard's person.
- `folded_parchment` | Folded parchment ×1 — A piece of parchment found tucked in the bodyguard's inner pocket.

## scene_result
location: `crossed_keys_inn_common_room`

## rules_stakes_hint
Rules engine named this cost on failure: [Mechanical cost: dexterity check] + [Narrative consequence: being intercepted by the person Matthew warned about or being cornered in the alley]
If the narration is ambiguous, treat any condition name in the above as a strong signal to apply it.
## CURRENT TURN NARRATION
Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 12

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
FAIL on dexterity.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
escape: Aren attempts to flee the tavern through the back exit toward the river docks while calling out to Halden.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [x] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron has been settled in full.
- Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has received the leather-bound ledger and merchant seal.
- Halden reveals the road toughs have wider connections near the river banks.
- A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.
- A violent struggle between Voss and Matthew's guard has drawn the attention of the entire tavern.

## prior_turn_narration (T11 — for outcome_summary and actions context)
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."

## items_gained
Leather-bound ledger

## rules_stakes
Band: FAIL. At-risk cost named by rules engine: [Mechanical cost: dexterity check] + [Narrative consequence: being intercepted by the person Matthew warned about or being cornered in the alley]
If a narrative consequence is named above (e.g. an NPC acting, alarm raised, escape cut off), emit it as a scene_pressure_add entry at `immediate` urgency.
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `deliver_the_ledger`:  turns
- `clear_the_road_toughs`:  turns

## Current Pressures
- [tavern_attention] (immediate) The tavern patrons are alerted to the brawl and may intervene.

## CURRENT TURN NARRATION
Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "escape",
  "intent": "Aren attempts to flee the tavern through the back exit toward the river docks while calling out to Halden.",
  "rolled": true,
  "total_ms": 3285.8,
  "tokens_in": 1652,
  "tokens_out": 1773,
  "skill": "dexterity",
  "difficulty": "normal",
  "dice": [
    3,
    1
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 5,
  "band": "fail",
  "outcome_summary": "Your attempt to flee through the back exit fails as you slip on spilled oil, slamming into the doorframe and leaving you trapped between the locked door and an angry crowd."
}
```

**Raw LLM output:**
```
{
  "intent": "Aren attempts to flee the tavern through the back exit toward the river docks while calling out to Halden.",
  "intent_verb": "escape",
  "target": "",
  "stakes": "[Mechanical cost: dexterity check] + [Narrative consequence: being intercepted by the person Matthew warned about or being cornered in the alley]",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.

### Extract Scene

```json
{
  "scene_tags": [
    "chaos",
    "tension",
    "hostility"
  ],
  "scene_tagline": "A Failed Escape",
  "location_change": null,
  "location_description": "The floor is now a treacherous hazard of spilled oil and shattered glass, making movement difficult and dangerous.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "inn_patrons",
      "notes": "Rising from their benches with weapons drawn, transitioning from startled silence to predatory hostility.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "bodyguard_youth",
      "notes": "Stirring amidst the broken glass and groaning in pain, preparing to rise.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "matthew_estrada",
      "notes": "Watching the escalating chaos unfold.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "leather_bound_ledger",
      "name": "Leather-bound ledger",
      "notes": "A heavy volume clutched tightly to your chest.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "bruised_ribs_worsened",
      "label": "worsened bruised ribs",
      "description": "A heavy impact against the doorframe has severely aggravated your existing rib injury."
    }
  ],
  "pc_condition_remove": [
    {
      "id": "bruised_ribs"
    }
  ]
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "tavern_uprising",
      "text": "The tavern patrons have turned hostile following the brawl and Voss's panicked shouting.",
      "turn": 12
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Attempt to bash through the locked back door to escape.",
    "Draw a weapon and fight your way through the patrons.",
    "Call out to Halden again for help or a distraction.",
    "Dive back toward the bar to use the wreckage as cover."
  ],
  "outcome_summary": "Your attempt to flee through the back exit fails as you slip on spilled oil, slamming into the doorframe and leaving you trapped between the locked door and an angry crowd.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior",
    "instruction": "The Inn Patrons begin closing in on Voss, brandishing heavy tankards and cudgels.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "trapped_in_tavern",
      "text": "Voss is cornered between a locked door and a hostile crowd.",
      "urgency": "immediate",
      "turn_added": 12,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "leather_bound_ledger",
      "name": "Leather-bound ledger",
      "notes": "A heavy volume clutched tightly to your chest.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The floor is now a treacherous hazard of spilled oil and shattered glass, making movement difficult and dangerous.",
  "quest_updates": [],
  "pc_condition_add": [
    {
      "id": "bruised_ribs_worsened",
      "label": "worsened bruised ribs",
      "description": "A heavy impact against the doorframe has severely aggravated your existing rib injury."
    }
  ],
  "pc_condition_remove": [
    {
      "id": "bruised_ribs"
    }
  ],
  "scene_tags": [
    "chaos",
    "tension",
    "hostility"
  ],
  "scene_tagline": "A Failed Escape",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "inn_patrons",
      "notes": "Rising from their benches with weapons drawn, transitioning from startled silence to predatory hostility."
    },
    {
      "id": "bodyguard_youth",
      "notes": "Stirring amidst the broken glass and groaning in pain, preparing to rise."
    },
    {
      "id": "matthew_estrada",
      "notes": "Watching the escalating chaos unfold."
    }
  ],
  "recent_events_add": [
    {
      "id": "tavern_uprising",
      "text": "The tavern patrons have turned hostile following the brawl and Voss's panicked shouting.",
      "turn": 12
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "trapped_in_tavern",
      "text": "Voss is cornered between a locked door and a hostile crowd.",
      "urgency": "immediate",
      "turn_added": 12
    }
  ],
  "scene_pressure_remove": [
    "tavern_attention"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Attempt to bash through the locked back door to escape.

- Draw a weapon and fight your way through the patrons.

- Call out to Halden again for help or a distraction.

- Dive back toward the bar to use the wreckage as cover.

### Context Telemetry

- rules: est=1960t trimmed=False
- narrate: est=7275t trimmed=False
- extract.scene: est=3135t trimmed=False attempts=1
- extract.state: est=2972t trimmed=False attempts=1
- extract.progress: est=4498t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bodyguard_youth": {
        "last_seen": {
          "turn": {
            "from": 11,
            "to": 12
          }
        }
      },
      "inn_patrons": {
        "last_seen": {
          "turn": {
            "from": 11,
            "to": 12
          }
        }
      },
      "matthew_estrada": {
        "last_seen": {
          "turn": {
            "from": 11,
            "to": 12
          }
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "leather_bound_ledger",
        "name": "Leather-bound ledger",
        "notes": "A heavy volume clutched tightly to your chest."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The area behind the bar is now a mess of shattered glass, spilled ale, and expensive oils following the collision.",
      "to": "The floor is now a treacherous hazard of spilled oil and shattered glass, making movement difficult and dangerous."
    }
  },
  "meta": {
    "last_compacted_turn": {
      "from": 3,
      "to": 9
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 13,
        "to": 14
      },
      "instruction": {
        "from": "The tavern patrons begin to murmur and stand up, some reaching for weapons as the tension rises.",
        "to": "The Inn Patrons begin closing in on Voss, brandishing heavy tankards and cudgels."
      },
      "surface_as": {
        "from": "environmental",
        "to": "npc_behavior"
      }
    },
    "prior_history": {
      "added": [
        "- [T5] Encountered the Bald Tough and Scarred Tough at the Crossed Keys Inn; they demanded a toll for passage.",
        "- [T9] Investigated the back passage, hearing a mysterious scraping sound in the darkness.",
        "- [T7] Delivered the leather-bound ledger and merchant seal to Halden at the Crossed Keys Inn.",
        "- [T4] Uneventful \u2014 no mechanical changes.",
        "- [T6] Paid the toughs 200 credits to avoid conflict, though they remained hostile.",
        "- [T8] Used the brass key to unlock a secondary door leading to a narrow back passage."
      ],
      "removed": []
    },
    "turn": {
      "from": 11,
      "to": 12
    }
  },
  "pc": {
    "conditions": {
      "added": [
        {
          "added_turn": 11,
          "description": "A heavy impact against the doorframe has severely aggravated your existing rib injury.",
          "id": "bruised_ribs_worsened",
          "label": "worsened bruised ribs"
        }
      ],
      "removed": [
        {
          "added_turn": 8,
          "description": "A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.",
          "id": "bruised_ribs",
          "label": "bruised ribs"
        }
      ]
    },
    "momentum": {
      "from": 0,
      "to": -1
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 7,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "active",
          "title": "Deliver Halden's Ledger"
        },
        "to": {
          "id": "deliver_the_ledger",
          "last_advanced_turn": 7,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": false,
              "failed": false
            },
            {
              "description": "Confirm the contract with Halden in person.",
              "done": false,
              "failed": false
            }
          ],
          "status": "completed",
          "title": "Deliver Halden's Ledger"
        }
      }
    ]
  },
  "scene": {
    "present_npcs": {
      "changed": [
        {
          "from": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "Startled into a sudden silence by the sound of breaking glass and the violent collision.",
            "title": ""
          },
          "to": {
            "bio": "",
            "id": "inn_patrons",
            "name": "Inn Patrons",
            "notes": "Rising from their benches with weapons drawn, transitioning from startled silence to predatory hostility.",
            "title": ""
          }
        },
        {
          "from": {
            "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
            "id": "matthew_estrada",
            "name": "Matthew Estrada",
            "notes": "Watching the player with profound, weary disappointment; remains calm and warns the player about a hidden observer.",
            "title": "Traveler"
          },
          "to": {
            "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
            "id": "matthew_estrada",
            "name": "Matthew Estrada",
            "notes": "Watching the escalating chaos unfold.",
            "title": "Traveler"
          }
        },
        {
          "from": {
            "bio": "A nervous, wiry man who serves as Matthew Estrada's protector.",
            "id": "bodyguard_youth",
            "name": "Wiry Youth",
            "notes": "Dazed and gasping for air after being tackled into the shelving.",
            "title": "Bodyguard"
          },
          "to": {
            "bio": "A nervous, wiry man who serves as Matthew Estrada's protector.",
            "id": "bodyguard_youth",
            "name": "Wiry Youth",
            "notes": "Stirring amidst the broken glass and groaning in pain, preparing to rise.",
            "title": "Bodyguard"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_ledger_delivered",
          "text": "Halden has safely received the leather-bound ledger and merchant seal.",
          "turn": 7
        },
        {
          "id": "halden_warning_toughs",
          "text": "Halden warns that the road toughs may have deeper connections near the river banks.",
          "turn": 8
        },
        {
          "id": "mystery_in_passage",
          "text": "A sharp scraping sound of leather against stone echoes from the darkness of the back passage.",
          "turn": 9
        }
      ],
      "removed": [
        {
          "id": "debt_cleared",
          "text": "Your debt to Caron has been settled in full.",
          "turn": 2
        },
        {
          "id": "halden_ledger_contract",
          "text": "Halden has entrusted you with his leather-bound ledger to be delivered to the Crossed Keys Inn.",
          "turn": 3
        },
        {
          "id": "road_toughs_rumors",
          "text": "Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.",
          "turn": 6
        },
        {
          "id": "halden_receives_ledger",
          "text": "Halden has received the leather-bound ledger and merchant seal.",
          "turn": 7
        },
        {
          "id": "halden_warning",
          "text": "Halden reveals the road toughs have wider connections near the river banks.",
          "turn": 8
        },
        {
          "id": "scraping_sound_in_passage",
          "text": "A sharp scraping sound of leather on stone echoes from the darkness of the Back Passage.",
          "turn": 9
        },
        {
          "id": "tavern_brawl_start",
          "text": "A violent struggle between Voss and Matthew's guard has drawn the attention of the entire tavern.",
          "turn": 11
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "tavern_attention",
          "max_turns": null,
          "text": "The tavern patrons are alerted to the brawl and may intervene.",
          "turn_added": 11,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Violent Scramble for Clues",
      "to": "A Failed Escape"
    },
    "tags": {
      "added": [
        "hostility"
      ],
      "removed": [
        "stealth_interrupted",
        "combat"
      ]
    }
  }
}
```


---

# TURN 13

**Input:** `I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: low morale, shaken, glass cuts, worsened bruised ribs

## scene
Location: Common Room
## last_turn (tail of the most recent narrative)
T12: I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on. — Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.

## Current Turn: 13
=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.

```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road
**Bio:** Mid-thirties, broad shoulders, careful with words. Took on a courier contract
to clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and
a heavier obligation.

Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: low morale, shaken, glass cuts, worsened bruised ribs

## Location
Common Room (crossed_keys_inn_common_room)
The floor is now a treacherous hazard of spilled oil and shattered glass, making movement difficult and dangerous.

## inventory (cross-reference before describing item use)
- **Credits** ×449: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather pouch**: A small, heavy pouch found on the bodyguard's person.
- **Folded parchment**: A piece of parchment found tucked in the bodyguard's inner pocket.
- **Leather-bound ledger**: A heavy volume clutched tightly to your chest.

## Quests
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- Halden has safely received the leather-bound ledger and merchant seal.
- Halden warns that the road toughs may have deeper connections near the river banks.
- A sharp scraping sound of leather against stone echoes from the darkness of the back passage.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Voss met with Caron at the tavern to address the outstanding debt.
- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.


- [T4] Uneventful — no mechanical changes.
- [T5] Encountered the Bald Tough and Scarred Tough at the Crossed Keys Inn; they demanded a toll for passage.
- [T6] Paid the toughs 200 credits to avoid conflict, though they remained hostile.
- [T7] Delivered the leather-bound ledger and merchant seal to Halden at the Crossed Keys Inn.
- [T8] Used the brass key to unlock a secondary door leading to a narrow back passage.
- [T9] Investigated the back passage, hearing a mysterious scraping sound in the darkness.


## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 10** — I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
You turn your back on the unsettling silence of the **Back Passage**, moving with a sudden, aggressive purpose toward the main common room. The warmth of the tavern hits you like a physical weight, thick with the scent of roasted meat and the boisterous noise of drunk patrons. You navigate the crowded floor, your gaze locking onto a man sitting alone near the edge of the bar.

**Matthew Estrada** sits with a rigid, disciplined posture that stands out among the slumped shoulders of the local drinkers. He holds a tankard with a steady hand, but his eyes are not on his drink; they are constantly shifting, scanning the room with a cold, tactical precision that speaks of training rather than paranoia. You reach out and seize his wrist in a sudden, forceful grip, pulling his arm toward you as you lean in close.

"Who are you really?" you demand, your voice low and dangerous, cutting through the tavern's din. "And why are you watching this room like a soldier?"

The man doesn't flinch. Even with your fingers digging into his skin, his expression remains as flat and unreadable as a stone slab. He doesn't reach for a weapon, nor does he attempt to shake you off; he simply turns his head to look you directly in the eye, his gaze heavy and unsettlingly calm. The immediate tension of your outburst seems to dissipate as he holds your gaze, the rowdy laughter of the nearby patrons continuing as if nothing out of the ordinary had occurred.

**Turn 11** — Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
The sudden flash of steel catches the dim tavern light as a man standing just behind **Matthew Estrada** reacts with startling speed. The newcomer, a wiry youth with a nervous twitch in his eye, draws a long, thin knife from a sheath at his hip. Before the blade can find its mark, you lunge forward, putting your entire weight behind a heavy, driving tackle.

The collision is violent and messy. You slam into the bodyguard, and the two of you crash into the heavy wooden shelving behind the bar. Bottles of cheap ale and expensive oils shatter upon impact, raining glass and liquid down upon you both. The sound of breaking glass and the sudden heavy thud of bodies hitting wood draws immediate, startled silence from the nearby patrons. The bodyguard groans, his head snapping back against a shelf as he slumps into a tangle of broken glass and spilled spirits, dazed and gasping for air.

Ignoring the stinging shards of glass grazing your arm, you scramble over his heavy limbs, your hands moving with frantic precision. You reach into the pockets of his leather coat, your fingers brushing past coarse fabric and cold metal. You manage to find a small, heavy leather pouch and a folded piece of parchment tucked into an inner pocket.

As you pull the items free, **Matthew Estrada** doesn't reach for a weapon or cry out for help. Instead, he remains seated, his gaze fixed on you with an expression of profound, weary disappointment. He doesn't move to stop you, but his voice cuts through the sudden quiet of the tavern like a cold wind. "You're making a scene, Voss," he says softly, his eyes darting toward the darkened corners of the room. "And while you're busy playing thief, you're missing the person who's actually watching us."

**Turn 12** — I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.

GM DIRECTION (PRESSURE, surface as npc_behavior):
The Inn Patrons begin closing in on Voss, brandishing heavy tankards and cudgels.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Wiry Youth** — last seen Common Room
- **Unknown Presence** — last seen Back Passage
- **Inn Patrons** — last seen Common Room
- **Wildlife** — last seen Merchant Road (East)
- **Bystanders** — last seen Marrow's Crossing Streets
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Back Passage: Left behind near the town well after handing over the ledger.
- **Edda**
- **Matthew Estrada** — last seen Common Room
- **Bald Tough** — last seen Crossed Keys Inn
## NPCs Present in Scene
- Inn Patrons — Rising from their benches with weapons drawn, transitioning from startled silence to predatory hostility.
- Matthew Estrada (Traveler) — Watching the escalating chaos unfold.
- Wiry Youth (Bodyguard) — Stirring amidst the broken glass and groaning in pain, preparing to rise.
_(immutable section omitted — see Static Context > Seed State)_
## Current Turn: 13
=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## Current Turn: 13

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: low morale, shaken, glass cuts, worsened bruised ribs

## location
`crossed_keys_inn_common_room` | Common Room
The floor is now a treacherous hazard of spilled oil and shattered glass, making movement difficult and dangerous.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `inn_patrons` | Inn Patrons — Rising from their benches with weapons drawn, transitioning from startled silence to predatory hostility.
- `matthew_estrada` | Matthew Estrada (Traveler) — Watching the escalating chaos unfold.
- `bodyguard_youth` | Wiry Youth (Bodyguard) — Stirring amidst the broken glass and groaning in pain, preparing to rise.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T12 context)
Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.

## CURRENT TURN NARRATION
The heavy door slams shut, sealing you inside a nightmare of rising tempers and clattering wood. You don't wait to see if the **Inn Patrons** reach you; instead, you throw your shoulder against the latch of the secondary door, praying the mechanism holds long enough for you to slip out. You burst through into the night air, lungs burning, and scramble toward the river docks, your boots slapping rhythmically against the damp, uneven stones of the waterfront.

You find a narrow, salt-crusted alcove between two stacked crates near the edge of the pier, shielded from the moonlight by a sagging canvas awning. Your breath comes in ragged, shallow gasps that send spikes of agony through your bruised ribs. With trembling hands, you reach for your **Linen bandages**, but find your fingers too clumsy and slick with sweat and oil. Frustrated and pressed for time, you tear a strip of fabric from your own shirt, pressing the rough cloth against the stinging glass cuts on your arm to stem the bleeding.

The river laps hungrily against the pilings below, a rhythmic, indifferent sound against the frantic beating of your heart. You reach into your pocket and pull out the **Folded parchment** and the **Leather pouch**, your mind racing with the implications of what you stole. Digging through the items, you find a scrap of clean parchment and a charcoal nub. With frantic, messy strokes, you scrawl a desperate message to **Caron**: *Intercepted a courier near the Crossed Keys. High-value cargo. The man watching the room is more than a traveler. Meet me.*

A small, soot-stained boy with a heavy wool cap—a local dock boy—scurries past your hiding spot, hauling a crate of salted fish. You reach out, snagging his sleeve and pressing a few **Credits** into his palm. "Get this to **Caron** at the tavern," you hiss, thrusting the folded note toward him. The boy eyes the coin with wide, greedy eyes, snatches the message, and vanishes into the mist of the river banks without a word.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## Current Turn: 13

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.
- `shaken` | shaken — The intimidating presence and demand for a toll from the toughs has rattled your composure.
- `glass_cuts` | glass cuts — Stinging shards of glass from the shattered bottles have grazed your arm.
- `bruised_ribs_worsened` | worsened bruised ribs — A heavy impact against the doorframe has severely aggravated your existing rib injury.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×449 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_pouch` | Leather pouch ×1 — A small, heavy pouch found on the bodyguard's person.
- `folded_parchment` | Folded parchment ×1 — A piece of parchment found tucked in the bodyguard's inner pocket.
- `leather_bound_ledger` | Leather-bound ledger ×1 — A heavy volume clutched tightly to your chest.

## scene_result
location: `river_docks_alcove`
(location changed)
## CURRENT TURN NARRATION
The heavy door slams shut, sealing you inside a nightmare of rising tempers and clattering wood. You don't wait to see if the **Inn Patrons** reach you; instead, you throw your shoulder against the latch of the secondary door, praying the mechanism holds long enough for you to slip out. You burst through into the night air, lungs burning, and scramble toward the river docks, your boots slapping rhythmically against the damp, uneven stones of the waterfront.

You find a narrow, salt-crusted alcove between two stacked crates near the edge of the pier, shielded from the moonlight by a sagging canvas awning. Your breath comes in ragged, shallow gasps that send spikes of agony through your bruised ribs. With trembling hands, you reach for your **Linen bandages**, but find your fingers too clumsy and slick with sweat and oil. Frustrated and pressed for time, you tear a strip of fabric from your own shirt, pressing the rough cloth against the stinging glass cuts on your arm to stem the bleeding.

The river laps hungrily against the pilings below, a rhythmic, indifferent sound against the frantic beating of your heart. You reach into your pocket and pull out the **Folded parchment** and the **Leather pouch**, your mind racing with the implications of what you stole. Digging through the items, you find a scrap of clean parchment and a charcoal nub. With frantic, messy strokes, you scrawl a desperate message to **Caron**: *Intercepted a courier near the Crossed Keys. High-value cargo. The man watching the room is more than a traveler. Meet me.*

A small, soot-stained boy with a heavy wool cap—a local dock boy—scurries past your hiding spot, hauling a crate of salted fish. You reach out, snagging his sleeve and pressing a few **Credits** into his palm. "Get this to **Caron** at the tavern," you hiss, thrusting the folded note toward him. The boy eyes the coin with wide, greedy eyes, snatches the message, and vanishes into the mist of the river banks without a word.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## Current Turn: 13

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
repair: The player attempts to tend to their injuries and send a message to Caron via a dock boy.
## quest_threshold
Start a new quest only if the narration introduces a clear multi-turn goal distinct from existing quests.

## active_quests
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Halden has safely received the leather-bound ledger and merchant seal.
- Halden warns that the road toughs may have deeper connections near the river banks.
- A sharp scraping sound of leather against stone echoes from the darkness of the back passage.

## prior_turn_narration (T12 — for outcome_summary and actions context)
Adrenaline surges through your veins, sharp and bitter, as you realize the trap is closing. You snatch the **Leather-bound ledger** from your coat with a frantic jerk, the heavy volume pressing hard against your ribs as you scramble upward from the wreckage of the bar. The **Wiry Youth** groans beneath you, a pathetic, wet sound, but you don't give him a second glance.

"Halden! Hold on!" you bellow, your voice cracking as it tears through the stunned silence of the common room. You lunge toward the small, secondary door you had unlocked earlier, your boots skidding on a slick patch of spilled oil. You reach for the heavy wood, your fingers clawing at the handle to push through to the **Back Passage**, but your footing betrays you. Your foot slips on the treacherous surface, and instead of a clean exit, you stumble heavily against the doorframe. The impact sends a jarring shock through your bruised ribs, and the heavy door slams shut with a resonant, mocking *boom* before you can slip through.

The tavern erupts. The sudden movement and your panicked shouting turn the startled silence into a low, predatory roar of confusion and hostility. **Inn Patrons** rise from their benches, chairs scraping harshly against the floorboards like sharpening knives. Some reach for heavy tankards or cudgels, their faces twisted in a mix of fear and anger at the sudden violence you've brought to their hearth.

You find yourself trapped between the heavy, locked door and the advancing crowd, the ledger clutched to your chest like a lifeline. Behind you, the **Wiry Youth** begins to stir among the shards of glass, a low hiss of pain escaping his lips as he prepares to rise.

## items_gained
charcoal nub, scrap of parchment

## items_lost
credits

## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `clear_the_road_toughs`:  turns

## CURRENT TURN NARRATION
The heavy door slams shut, sealing you inside a nightmare of rising tempers and clattering wood. You don't wait to see if the **Inn Patrons** reach you; instead, you throw your shoulder against the latch of the secondary door, praying the mechanism holds long enough for you to slip out. You burst through into the night air, lungs burning, and scramble toward the river docks, your boots slapping rhythmically against the damp, uneven stones of the waterfront.

You find a narrow, salt-crusted alcove between two stacked crates near the edge of the pier, shielded from the moonlight by a sagging canvas awning. Your breath comes in ragged, shallow gasps that send spikes of agony through your bruised ribs. With trembling hands, you reach for your **Linen bandages**, but find your fingers too clumsy and slick with sweat and oil. Frustrated and pressed for time, you tear a strip of fabric from your own shirt, pressing the rough cloth against the stinging glass cuts on your arm to stem the bleeding.

The river laps hungrily against the pilings below, a rhythmic, indifferent sound against the frantic beating of your heart. You reach into your pocket and pull out the **Folded parchment** and the **Leather pouch**, your mind racing with the implications of what you stole. Digging through the items, you find a scrap of clean parchment and a charcoal nub. With frantic, messy strokes, you scrawl a desperate message to **Caron**: *Intercepted a courier near the Crossed Keys. High-value cargo. The man watching the room is more than a traveler. Meet me.*

A small, soot-stained boy with a heavy wool cap—a local dock boy—scurries past your hiding spot, hauling a crate of salted fish. You reach out, snagging his sleeve and pressing a few **Credits** into his palm. "Get this to **Caron** at the tavern," you hiss, thrusting the folded note toward him. The boy eyes the coin with wide, greedy eyes, snatches the message, and vanishes into the mist of the river banks without a word.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "repair",
  "intent": "The player attempts to tend to their injuries and send a message to Caron via a dock boy.",
  "rolled": false,
  "total_ms": 2755.4,
  "tokens_in": 1653,
  "tokens_out": 1741
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to tend to their injuries and send a message to Caron via a dock boy.",
  "intent_verb": "repair",
  "target": "self",
  "stakes": "",
  "check": {
    "required": false,
    "skill": "",
    "difficulty": "",
    "tags": []
  }
}
```

### Narration

The heavy door slams shut, sealing you inside a nightmare of rising tempers and clattering wood. You don't wait to see if the **Inn Patrons** reach you; instead, you throw your shoulder against the latch of the secondary door, praying the mechanism holds long enough for you to slip out. You burst through into the night air, lungs burning, and scramble toward the river docks, your boots slapping rhythmically against the damp, uneven stones of the waterfront.

You find a narrow, salt-crusted alcove between two stacked crates near the edge of the pier, shielded from the moonlight by a sagging canvas awning. Your breath comes in ragged, shallow gasps that send spikes of agony through your bruised ribs. With trembling hands, you reach for your **Linen bandages**, but find your fingers too clumsy and slick with sweat and oil. Frustrated and pressed for time, you tear a strip of fabric from your own shirt, pressing the rough cloth against the stinging glass cuts on your arm to stem the bleeding.

The river laps hungrily against the pilings below, a rhythmic, indifferent sound against the frantic beating of your heart. You reach into your pocket and pull out the **Folded parchment** and the **Leather pouch**, your mind racing with the implications of what you stole. Digging through the items, you find a scrap of clean parchment and a charcoal nub. With frantic, messy strokes, you scrawl a desperate message to **Caron**: *Intercepted a courier near the Crossed Keys. High-value cargo. The man watching the room is more than a traveler. Meet me.*

A small, soot-stained boy with a heavy wool cap—a local dock boy—scurries past your hiding spot, hauling a crate of salted fish. You reach out, snagging his sleeve and pressing a few **Credits** into his palm. "Get this to **Caron** at the tavern," you hiss, thrusting the folded note toward him. The boy eyes the coin with wide, greedy eyes, snatches the message, and vanishes into the mist of the river banks without a word.

### Extract Scene

```json
{
  "scene_tags": [
    "escape",
    "stealth",
    "tense",
    "desperation"
  ],
  "scene_tagline": "A Desperate Message Sent",
  "location_change": {
    "id": "river_docks_alcove",
    "name": "River Docks Alcove",
    "description": "A narrow, salt-crusted alcove between stacked crates near the pier, sheltered by a sagging canvas awning."
  },
  "location_description": "The river laps hungrily against the pilings below, and the waterfront is composed of damp, uneven stones shrouded in mist.",
  "npc_add": [
    {
      "id": "dock_boy",
      "notes": "Greedily takes credits and a message before scurrying away into the mist.",
      "name": "Dock Boy",
      "title": "Local laborer",
      "bio": "A small, soot-stained boy wearing a heavy wool cap who works the waterfront."
    }
  ],
  "npc_remove": [
    {
      "id": "inn_patrons",
      "last_seen_state": "Rising from benches with weapons drawn in the common room."
    },
    {
      "id": "matthew_estrada",
      "last_seen_state": "Watching the chaos unfold inside the tavern."
    },
    {
      "id": "bodyguard_youth",
      "last_seen_state": "Stirring amidst broken glass inside the tavern."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": []
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "charcoal_nub",
      "name": "charcoal nub",
      "notes": "A small piece of charcoal used for writing.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "scrap_of_parchment",
      "name": "scrap of parchment",
      "notes": "A small piece of clean parchment.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "message_to_caron_sent",
      "text": "Aren has sent a desperate message to Caron via a dock boy regarding the intercepted cargo.",
      "turn": 13
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Wait in the alcove for Caron to arrive.",
    "Scout the docks to see if the patrons follow.",
    "Attempt to further stabilize your injuries using more cloth.",
    "Hide the ledger more securely before moving from the pier."
  ],
  "outcome_summary": "You narrowly escape the tavern's hostility and find refuge in a dockside alcove, where you tend your wounds and dispatch a message to Caron.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "environmental",
    "instruction": "The sound of heavy boots and shouting patrons begins to echo from the tavern's back exit towards the docks.",
    "beat_expires_turn": null
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "pursuit_from_crossed_keys",
      "text": "Angry patrons from the Crossed Keys are searching the waterfront.",
      "urgency": "building",
      "turn_added": 13,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "charcoal_nub",
      "name": "Charcoal nub",
      "notes": "A small piece of charcoal used for writing.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "scrap_of_parchment",
      "name": "Scrap of parchment",
      "notes": "A small piece of clean parchment.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_change": {
    "id": "river_docks_alcove",
    "name": "River Docks Alcove",
    "description": "A narrow, salt-crusted alcove between stacked crates near the pier, sheltered by a sagging canvas awning."
  },
  "location_description": "The river laps hungrily against the pilings below, and the waterfront is composed of damp, uneven stones shrouded in mist.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "escape",
    "stealth",
    "tense",
    "desperation"
  ],
  "scene_tagline": "A Desperate Message Sent",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "dock_boy",
      "notes": "Greedily takes credits and a message before scurrying away into the mist.",
      "name": "Dock Boy",
      "title": "Local laborer",
      "bio": "A small, soot-stained boy wearing a heavy wool cap who works the waterfront."
    }
  ],
  "npc_remove": [
    {
      "id": "inn_patrons",
      "last_seen_state": "Rising from benches with weapons drawn in the common room."
    },
    {
      "id": "matthew_estrada",
      "last_seen_state": "Watching the chaos unfold inside the tavern."
    },
    {
      "id": "bodyguard_youth",
      "last_seen_state": "Stirring amidst broken glass inside the tavern."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "message_to_caron_sent",
      "text": "Aren has sent a desperate message to Caron via a dock boy regarding the intercepted cargo.",
      "turn": 13
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "pursuit_from_crossed_keys",
      "text": "Angry patrons from the Crossed Keys are searching the waterfront.",
      "urgency": "building",
      "turn_added": 13
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Wait in the alcove for Caron to arrive.

- Scout the docks to see if the patrons follow.

- Attempt to further stabilize your injuries using more cloth.

- Hide the ledger more securely before moving from the pier.

### Context Telemetry

- rules: est=1961t trimmed=False
- narrate: est=5020t trimmed=False
- extract.scene: est=3190t trimmed=False attempts=1
- extract.state: est=2928t trimmed=False attempts=1
- extract.progress: est=4340t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "ambient_wildlife": {
        "bio": "",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "merchant_road_east",
          "location_name": "Merchant Road (East)",
          "turn": 4
        },
        "name": "Wildlife",
        "title": "Nature's Echo"
      },
      "bodyguard_youth": {
        "bio": "A nervous, wiry man who serves as Matthew Estrada's protector.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_common_room",
          "location_name": "Common Room",
          "turn": 12
        },
        "last_seen_state": "Stirring amidst broken glass inside the tavern.",
        "name": "Wiry Youth",
        "title": "Bodyguard"
      },
      "bystanders": {
        "bio": "",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing_streets",
          "location_name": "Marrow's Crossing Streets",
          "turn": 3
        },
        "last_seen_state": "Fading into the distance as the player exits the town.",
        "name": "Bystanders",
        "title": ""
      },
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 1
        },
        "last_seen_state": "Left alone at the tavern table with the player's coins.",
        "name": "Caron",
        "title": "Old creditor"
      },
      "dock_boy": {
        "bio": "A small, soot-stained boy wearing a heavy wool cap who works the waterfront.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "river_docks_alcove",
          "location_name": "River Docks Alcove",
          "turn": 13
        },
        "name": "Dock Boy",
        "title": "Local laborer"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "last_seen": {
          "last_seen_state": "Left behind near the town well after handing over the ledger.",
          "location_id": "crossed_keys_inn_back_passage",
          "location_name": "Back Passage",
          "turn": 9
        },
        "last_seen_state": "Left behind in the back passage.",
        "name": "Halden",
        "title": "Merchant"
      },
      "inn_patrons": {
        "bio": "",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_common_room",
          "location_name": "Common Room",
          "turn": 12
        },
        "last_seen_state": "Rising from benches with weapons drawn in the common room.",
        "name": "Inn Patrons",
        "title": ""
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys"
      },
      "matthew_estrada": {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_common_room",
          "location_name": "Common Room",
          "turn": 12
        },
        "last_seen_state": "Watching the chaos unfold inside the tavern.",
        "name": "Matthew Estrada",
        "title": "Traveler"
      },
      "tough_a": {
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_exterior",
          "location_name": "Crossed Keys Inn",
          "turn": 6
        },
        "last_seen_state": "Standing in a defensive, watchful stance outside the inn entrance.",
        "name": "Bald Tough",
        "title": "Road thug"
      },
      "tough_b": {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_exterior",
          "location_name": "Crossed Keys Inn",
          "turn": 6
        },
        "last_seen_state": "Watching the player with narrowed, hateful eyes from the doorway.",
        "name": "Scarred Tough",
        "title": "Road thug"
      },
      "unknown_presence": {
        "bio": "A mysterious entity moving through the darkness of the back passage.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_back_passage",
          "location_name": "Back Passage",
          "turn": 9
        },
        "last_seen_state": "Making a scraping sound in the darkness of the back passage.",
        "name": "Unknown Presence",
        "title": "Shadowy Figure"
      }
    }
  },
  "inventory": [
    {
      "aliases": [],
      "amount": 448,
      "id": "credits",
      "name": "Credits",
      "notes": "Common coin, accepted at any inn or stall on the merchant road."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "iron_dagger",
      "name": "Iron dagger",
      "notes": "Plain crossguard, edge worn from honing. Belt-carried."
    },
    {
      "aliases": [],
      "amount": 3,
      "id": "bandages",
      "name": "Linen bandages",
      "notes": "Three rolls. Field-grade \u2014 won't replace a healer."
    },
    {
      "aliases": [
        "cloak",
        "travel cloak"
      ],
      "amount": 1,
      "id": "traveler_cloak",
      "name": "Traveler's cloak",
      "notes": "Oiled wool, road-stained, hood deep enough to hide a face."
    },
    {
      "aliases": [],
      "amount": 1,
      "id": "brass_key",
      "name": "Brass key",
      "notes": "A small brass key Halden gave you with the ledger."
    },
    {
      "amount": 1,
      "id": "leather_pouch",
      "name": "Leather pouch",
      "notes": "A small, heavy pouch found on the bodyguard's person."
    },
    {
      "amount": 1,
      "id": "folded_parchment",
      "name": "Folded parchment",
      "notes": "A piece of parchment found tucked in the bodyguard's inner pocket."
    },
    {
      "amount": 1,
      "id": "leather_bound_ledger",
      "name": "Leather-bound ledger",
      "notes": "A heavy volume clutched tightly to your chest."
    },
    {
      "amount": 1,
      "id": "charcoal_nub",
      "name": "Charcoal nub",
      "notes": "A small piece of charcoal used for writing."
    },
    {
      "amount": 1,
      "id": "scrap_of_parchment",
      "name": "Scrap of parchment",
      "notes": "A small piece of clean parchment."
    }
  ],
  "location": {
    "description": "A narrow, salt-crusted alcove between stacked crates near the pier, sheltered by a sagging canvas awning.",
    "id": "river_docks_alcove",
    "name": "River Docks Alcove"
  },
  "meta": {
    "compendium_touch_order": [
      "bystanders",
      "ambient_wildlife",
      "inn_patrons",
      "unknown_presence",
      "bodyguard_youth",
      "dock_boy"
    ],
    "game_name": "eval",
    "last_compacted_turn": 9,
    "model": "",
    "pending_gm_beat": {
      "beat_expires_turn": 15,
      "instruction": "The sound of heavy boots and shouting patrons begins to echo from the tavern's back exit towards the docks.",
      "surface_as": "environmental",
      "type": "pressure"
    },
    "prior_history": [
      "- [T1] Voss met with Caron at the tavern to address the outstanding debt.",
      "- [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.",
      "- [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.",
      "- [T4] Uneventful \u2014 no mechanical changes.",
      "- [T5] Encountered the Bald Tough and Scarred Tough at the Crossed Keys Inn; they demanded a toll for passage.",
      "- [T6] Paid the toughs 200 credits to avoid conflict, though they remained hostile.",
      "- [T7] Delivered the leather-bound ledger and merchant seal to Halden at the Crossed Keys Inn.",
      "- [T8] Used the brass key to unlock a secondary door leading to a narrow back passage.",
      "- [T9] Investigated the back passage, hearing a mysterious scraping sound in the darkness."
    ],
    "setting_pack": "eval-pack",
    "turn": 13
  },
  "pc": {
    "allegiance": null,
    "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
    "conditions": [
      {
        "added_turn": 10,
        "description": "Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.",
        "id": "low_morale",
        "label": "low morale"
      },
      {
        "added_turn": 4,
        "description": "The intimidating presence and demand for a toll from the toughs has rattled your composure.",
        "id": "shaken",
        "label": "shaken"
      },
      {
        "added_turn": 10,
        "description": "Stinging shards of glass from the shattered bottles have grazed your arm.",
        "id": "glass_cuts",
        "label": "glass cuts"
      },
      {
        "added_turn": 11,
        "description": "A heavy impact against the doorframe has severely aggravated your existing rib injury.",
        "id": "bruised_ribs_worsened",
        "label": "worsened bruised ribs"
      }
    ],
    "momentum": -1,
    "name": "Aren Voss",
    "stats": {
      "charisma": 3,
      "dexterity": 3,
      "lore": 2,
      "resolve": 3,
      "strength": 3,
      "wits": 2
    },
    "tagline": "Reluctant courier on the merchant road"
  },
  "quests": [
    {
      "id": "settle_the_debt",
      "last_advanced_turn": 0,
      "objectives": [
        {
          "description": "Find Caron, the man you owe.",
          "done": true,
          "failed": false
        },
        {
          "description": "Pay Caron in person and have him mark the debt cleared.",
          "done": true,
          "failed": false
        }
      ],
      "status": "completed",
      "title": "Settle the Old Debt"
    },
    {
      "id": "deliver_the_ledger",
      "last_advanced_turn": 7,
      "objectives": [
        {
          "description": "Accept the courier contract from Halden.",
          "done": true,
          "failed": false
        },
        {
          "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
          "done": false,
          "failed": false
        },
        {
          "description": "Confirm the contract with Halden in person.",
          "done": false,
          "failed": false
        }
      ],
      "status": "completed",
      "title": "Deliver Halden's Ledger"
    },
    {
      "id": "clear_the_road_toughs",
      "objectives": [
        {
          "description": "Find out who hired the toughs blocking the road.",
          "done": false,
          "failed": false
        },
        {
          "description": "Convince, pay, or remove the toughs from the inn.",
          "done": false,
          "failed": false
        }
      ],
      "status": "active",
      "title": "Clear the Road Toughs"
    }
  ],
  "scene": {
    "location_entered_turn": 12,
    "present_npcs": [
      {
        "bio": "A small, soot-stained boy wearing a heavy wool cap who works the waterfront.",
        "id": "dock_boy",
        "name": "Dock Boy",
        "notes": "Greedily takes credits and a message before scurrying away into the mist.",
        "title": "Local laborer"
      }
    ],
    "recent_events": [
      {
        "id": "halden_ledger_delivered",
        "text": "Halden has safely received the leather-bound ledger and merchant seal.",
        "turn": 7
      },
      {
        "id": "halden_warning_toughs",
        "text": "Halden warns that the road toughs may have deeper connections near the river banks.",
        "turn": 8
      },
      {
        "id": "mystery_in_passage",
        "text": "A sharp scraping sound of leather against stone echoes from the darkness of the back passage.",
        "turn": 9
      },
      {
        "id": "message_to_caron_sent",
        "text": "Aren has sent a desperate message to Caron via a dock boy regarding the intercepted cargo.",
        "turn": 13
      }
    ],
    "recently_left": [],
    "recently_left_turns": 0,
    "scene_pressure": [
      {
        "id": "pursuit_from_crossed_keys",
        "max_turns": null,
        "text": "Angry patrons from the Crossed Keys are searching the waterfront.",
        "turn_added": 13,
        "urgency": "building"
      }
    ],
    "tagline": "A Desperate Message Sent",
    "tags": [
      "escape",
      "stealth",
      "tense",
      "desperation"
    ],
    "turn_entered": 12,
    "world_state": [
      "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
      "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
      "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
    ]
  },
  "world": {
    "factions": [],
    "locations": []
  }
}
```


---
# Deterministic Signals

## Auto-Checker Failures
| Turn | Assertion | Detail |
|---|---|---|
| 1 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Instead'] |
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Instead'] |
| 3 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed', 'Crossing', 'Marrow'] |
| 4 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossing', 'Leather', 'Marrow'] |
| 5 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 7 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Leather', 'Crossed'] |
| 8 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Ignoring'] |
| 9 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed', 'Credit', 'Passage'] |
| 10 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew', 'Passage'] |
| 11 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew', 'Instead'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1404 | 3086 | 2441 | 2540 | 3715 | 0 | 0 |
| 2 | 1788 | 3468 | 0 | 0 | 4002 | 0 | 0 |
| 3 | 1830 | 3903 | 2898 | 2636 | 4145 | 1 | 1 |
| 4 | 1887 | 4319 | 2843 | 2509 | 3872 | 0 | 0 |
| 5 | 1828 | 4834 | 2908 | 2924 | 4274 | 0 | 0 |
| 6 | 1964 | 5579 | 3020 | 2875 | 4388 | 0 | 0 |
| 7 | 1897 | 4879 | 3094 | 2779 | 4182 | 0 | 0 |
| 8 | 2027 | 5426 | 3054 | 2629 | 4137 | 0 | 0 |
| 9 | 1912 | 5908 | 2854 | 2600 | 3882 | 0 | 0 |
| 10 | 1795 | 6420 | 2879 | 2729 | 4200 | 0 | 0 |
| 11 | 1879 | 6796 | 3033 | 2835 | 4329 | 0 | 0 |
| 12 | 1960 | 7275 | 3135 | 2972 | 4498 | 0 | 0 |
| 13 | 1961 | 5020 | 3190 | 2928 | 4340 | 0 | 0 |

### Parse Error Details
**Turn 3** (1 error(s)):
- `1 validation error for SceneExtractResult
npc_add.0
  Input should be a valid dictionary or instance of NpcAdd [type=model_type, input_value='bystanders', input_type=str]
    For further information visit https://errors.pydantic.dev/2.13/v/model_type`

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + progress | 20 | `- You arrived in Marrow's Crossing after three days on the r / - You heard rumors of road-toughs extorting travelers near t / - You found Caron in the tavern — he's been waiting for you.` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |

## Compaction Features
**8 compaction event(s) observed.** For each event below, the judge must evaluate every capability and write `[OK] / [FAIL] / [NA]` with a one-line justification per capability. The 14 capabilities the compactor system prompt promises:

- `bullet_named_npcs` — Preserve named NPCs (first mention, role, title)
- `bullet_location` — Preserve location of the turn
- `bullet_quest_outcomes` — Preserve quest outcomes (resolved/failed/leads)
- `bullet_key_items` — Preserve key items (gained/lost/consumed)
- `bullet_conditions` — Preserve condition changes
- `bullet_irreversible` — Preserve irreversible player choices
- `bullet_deaths` — Preserve deaths/departures of named characters
- `bullet_mech_consequences` — Preserve mechanical consequences (alliances, enmities, oaths)
- `bullet_culling` — Cull atmospherics, dialogue without consequence, blow-by-blow combat, uneventful travel
- `sanitize_npc_merge` — Sanitize: npc_merge for duplicate compendium NPCs
- `sanitize_inventory` — Sanitize: inventory_remove for duplicate items
- `sanitize_quest_close` — Sanitize: quest_close for quests with all objectives done
- `sanitize_pressure` — Sanitize: pressure_remove for resolved scene pressures
- `sanitize_condition` — Sanitize: condition_remove for cured conditions

### Compaction at turn 6

- prior_history: 0 → 3 bullets (3 added)
- recent_events: 6 → 3 entries

**Bullets added:**

  > - [T1] Voss met with Caron at the tavern to address the outstanding debt.
  > - [T2] Voss paid 500 credits to Caron, successfully clearing the debt in his ledger.
  > - [T3] Voss met Halden near the town well and accepted a contract to deliver his leather-bound ledger to the Crossed Keys Inn for 200 credits.

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 7

- prior_history: 3 → 3 bullets (0 added)
- recent_events: 3 → 4 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 8

- prior_history: 3 → 3 bullets (0 added)
- recent_events: 4 → 5 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 9

- prior_history: 3 → 3 bullets (0 added)
- recent_events: 5 → 6 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 10

- prior_history: 3 → 3 bullets (0 added)
- recent_events: 6 → 6 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 11

- prior_history: 3 → 3 bullets (0 added)
- recent_events: 6 → 7 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 12

- prior_history: 3 → 9 bullets (6 added)
- recent_events: 7 → 3 entries

**Bullets added:**

  > - [T4] Uneventful — no mechanical changes.
  > - [T5] Encountered the Bald Tough and Scarred Tough at the Crossed Keys Inn; they demanded a toll for passage.
  > - [T6] Paid the toughs 200 credits to avoid conflict, though they remained hostile.
  > - [T7] Delivered the leather-bound ledger and merchant seal to Halden at the Crossed Keys Inn.
  > - [T8] Used the brass key to unlock a secondary door leading to a narrow back passage.
  > - [T9] Investigated the back passage, hearing a mysterious scraping sound in the darkness.

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 13

- prior_history: 9 → 9 bullets (0 added)
- recent_events: 3 → 4 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

