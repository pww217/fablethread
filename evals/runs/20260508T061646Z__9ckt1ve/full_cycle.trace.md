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
    "turn": 1,
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
- `target`: who or what the action is directed at, or empty string if a general action.
- `stakes`: what is at risk if this fails, or empty string.
- `check`: an object with the following fields:
  - `required`: true or false.
  - `skill`: strength|dexterity|wits|lore|charisma|resolve.
  - `difficulty`: trivial|easy|normal|hard|extreme.

```

### Narrate System Prompt

```
Narrate the next beat of a text adventure. Second person, present tense, 2-4 short paragraphs. Output prose only — never list choices, never speak as the game.

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
If an item is **bolded**, it's considered explicit.

## Player intent is truth
Take the player's stated action at face value and commit to it. The rules engine handles dice and conditions; the narrator handles fiction. 
Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

## NPCs in scene
NPCs should feel like persistent people, not props. Re-use characters from the Known Characters list when the scene and location are consistent with their last known position. Only create a genuinely new character when the scene requires someone no existing character can fill. When introducing a new named NPC, pick from the name pool. Give a brief physical description.

## Mortal stakes + agency
NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.
Resolve cruel, selfish, or evil player choices straight: narrate consequences without moralizing, refusing, or steering toward a "better" path. NPCs may react with horror, retaliation, or fear; the narrator never lectures or vetoes.

## Gender-aware naming
When the name pool provides separate male and female lists, select names appropriate to the role and setting. Historical combat genres: use male names for front-line combat roles. Modern and speculative settings: use any gender freely.

## Quests
If the action satisfies an objective or resolves a quest, make that resolution clear in prose briefly (the debt is paid, the job is done, the target is found).

## Markdown (light)
- `**bold**` only for: NPC names on first introduction this scene; named inventory items (use a short name, not ammo) the player owns when used or directly referenced. Once per scene per object.
- `*italic*` for ship names, books, broadcasts, in-world publication titles, emphasized proper nouns.
- `> blockquote` only for signage or quoted broadcast text.
- No headings, no bullet lists in prose.


## Genre tone
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
and means "nothing changed; advance the storyteller's reasoning only." Do not
list domains speculatively. Do not list domains for things that didn't happen
in your prose above.

Rules:
- The tag MUST be the very last thing in your output, on its own line.
- One JSON object only. No prose after the closing tag.
- If thinking mode is enabled, the tag goes AFTER the closing </thinking> tag.
- The tag and its contents are stripped from the player's view by the engine.

```

### Extract Scene System Prompt

```
Extract scene state, NPC presence, taglines, location, and location description from a narration. 
Emit one JSON object matching the schema. No prose, no markdown fences, null for optional fields that don't apply, never omit a key.

## Output schema

```json
{
  "scene_tags": [],
  "scene_tagline": "",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "actions": [],
  "outcome_summary": ""
}
```

## Field rules

`scene_tags`: 1-3 lowercase tags from {dialogue, combat, exploration, market, travel, stealth, rest}. Always provide at least one. Include `"game_over"` ONLY if the player character (not an NPC) is confirmed dead this turn. When a scene involves armed/hostile NPCs or physical confrontation, prefer "combat" over "dialogue" even if the player is speaking.

`scene_tagline`: 3-6 word phase. Relevant to story or scene only, not mechanical. Upper case words. Examples: `"Dock Fees Due at Dawn"`, `"The Emperor's Assassin"`.

`location_change`: emit `{"id": "snake_case_id", "name": "Location Name", "description": "1-2 sentences"}` if the player physically moved or the situation has changed significantly. If player has moved away from NPCs, remove them from scene. Null if no change.

`location_description`: Only emit this field if the narration describes a meaningful environmental or atmospheric change to the current location — a shift in lighting, weather, crowd density, physical damage, or emotional register of the space. Do not re-describe unchanged surroundings. If the scene looks and feels the same as before, omit `description` entirely.

`npc_add`: new NPCs entering the scene this turn. Each: `{"id": "snake_case", "notes": "current situation", "name": "Full Name", "title": "Role", "bio": "1-3 sentences"}`. Only include name/title/bio for genuinely new NPCs not in the compendium. Omit name/title/bio for ambient/extra NPCs. If an NPC was previously unnamed (referred to by descriptor), check the compendium roster — if it's the same character, use `npc_update` instead of `npc_add`. **Compendium NPCs are NOT in the scene by default. Emit `npc_add` for any NPC mentioned in the narration that is NOT in `present_npcs`, even if they appear in the compendium roster.**

`npc_remove`: IDs of named NPCs who explicitly left the scene or are no longer in proximity. Each: `{"id": "existing_id", "last_seen_state": "1-sentence description of what they were last seen doing"}`. Example: `[{"id": "carlos_zaragoza", "last_seen_state": "storming out of the room"}, {"id": "marisela_olivares", "last_seen_state": "heading back to the safehouse"}]`. **Only remove NPCs when the narration clearly states or implies they left — e.g., "X walked out", "X headed back to camp", "X said goodbye and left".** Do NOT remove NPCs just because the scene shifted focus, because the narration stopped mentioning them, or because the player moved to a new location (allies/followers go with the player). Do NOT remove allies, family, or key characters who follow the player. When in doubt, keep them in the scene.

`npc_update`: existing scene NPCs whose notes changed this turn. Each: `{"id": "existing_id", "notes": "updated situation"}`. Name/title/bio only change when new information arrives — don't re-emit them. Notes change every turn to reflect what the NPC is doing — some flavor relevant to their motivation, attitude, recent events, etc. not "standing nearby". If the narration mentions an NPC who is already in the scene (shown in `present_npcs` above), you MUST emit an `npc_update` for them even if only updating notes.

`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration only (not prior history). Structure: two choices should offer distinct avenues related to the current quest (if any), one should involve an NPC who is present in the scene, and one should be an exploration/environmental action or freeform option. Weight toward the player's strongest stat (don't mention stat), quest objectives, and motivations. Each one should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Sneak past the guards and search the room", "Convince the guard to let you pass", "Create a diversion to slip past the guards". Bias to bold, good storytelling choices.

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, npcs, scene, and location. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

## NPC scene cap

No more than 8 named NPCs in a scene. If the narration introduces a 9th, the oldest/least relevant named NPC should be removed (goes into `npc_remove`). Ambient NPCs don't count toward the cap. Allies, family, and key characters should be assumed to follow the player when he moves — don't remove them on location change. Others should be assumed to have stayed behind. **NPC removal should only happen for one of two reasons: (1) the narration clearly shows the NPC left, or (2) the scene cap is exceeded and you must evict the least relevant NPC. Never remove NPCs for any other reason.**

## State-presence rule

Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only infer changes that are explicit.

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
  "pc_condition_remove": [],
  "failed": []
}
```

## Hard cap
- `inventory_add`: Items explicitly received in narration are not capped.  Stack increases via re-adding the same `id` are NOT capped. Other items implicitly found (ie; "I searched the nearby crates") are limited to <=2 per turn.
- `pc_condition_add`: ≤2 per turn. Total active conditions must not exceed 5.

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

`failed`: precondition failures this turn (e.g. `"tried to pick up keys but guard is still conscious"`). Use the rules outcome (band) shown in the user prompt — crit_fail / fail / setback ⇒ action did not succeed.

## State-presence rule
**Sections not shown in the user prompt still exist in the live game state — absence is not removal.** Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, ensure once more than you have no similar or matching items or item IDs.
```

### Extract Progress System Prompt

```
Extract quest updates, recent events, and NPC compendium changes from a narration. Emit one JSON object matching the schema. No prose, no markdown fences, empty arrays for fields with no changes.

## NPC ID format rules

NPC IDs must be `firstname_lastname` only. No titles, roles, or descriptors.
- ✅ `kael_marsh`, `torben_klask`
- ❌ `scarred_soldier`, `doctor_voss`, `the_merchant`
- If only one name is known: `kael` (single token, no decorators)
- When a full name is revealed later: emit `compendium_npc_update` to set the canonical ID and add old ID as alias

IDs are immutable once assigned. Name changes go in the `name` field and `aliases`, not the ID.

## NPC match instruction

Before emitting `compendium_npc_update` to add a new NPC, check the existing compendium list.
If the character is likely the same person referred to differently (e.g. `"scarred soldier"` when `"kael_marsh"` is already in the compendium), use the existing ID and emit an update instead of an add.
Add the old descriptor as an alias. Only emit an add for a genuinely new NPC not present in the current compendium.
If a character is named or re-identified this turn (e.g. you learn the scarred soldier's name is Kael), emit `compendium_npc_update` on the existing ID — do not create a new entry. Add the old descriptor as an alias.
**If the character's name matches an existing compendium NPC (case-insensitive), use their existing ID. Do NOT create a new entry.**

## Output schema

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {} | null
}
```

## Field rules

`quest_updates`: changes to quest state this turn.
- Update existing: `{"id": "quest_id", "status": "active|completed|failed|abandoned", "objectives": [{"index": N, "done": true}]}`. `index` is 1-based from the active_quests list shown in the user prompt.
- New quest: `{"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objectives": [{"description": "first objective"}]}`. Use `description` only when adding a new objective.
- The engine auto-completes a quest when all objectives are done — do NOT emit `status: completed` for that case; just mark objectives done.
- New quest threshold guidance for this turn is in the user prompt.
- A quest is failed when the key objective(s) are failed, or are impossible to complete due to new information or changes in the player, recent_events, narration.
- A quest is abandoned when the player/narration implies they are giving up on it, gets too far away to continue, or the quest is no longer relevant to the player's current goals due to new developments or information.

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the quest, player, scene, and location, and not already known. It must be narratively significant: an obstacle, revelation, opportunity, relevant news of politics, intrigue, or other event that changes the player, location, or quest state substantially.
 Avoid facts about NPCs unless relevant to the player or quest. NPCs bios/notes will be updated separately. Examples:"We learn of a new plot to overthrow the emperor", "We learned another faction amassing troops on the border", "The enemy has quietly flanked the party to the West", "The quest is now impossible to complete". If a new detail updates an existing fact, use `recent_events_update` instead. Each: `{"id": "snake_case_id", "text": "Event description", "turn": 0}`.

Each new event must have a stable `snake_case` ID (e.g. `"guard_left_room"`, `"player_found_key"`). To update an existing event's text, emit it under `recent_events_update` using its existing ID. To remove an event, emit its ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded with no replacement. Each entry is the exact ID string from the recent_events list.

`recent_events_update`: facts whose content changed in a relevant way. Each: `{"id": "existing_event_id", "text": "replacement text"}`. **Important**: Prefer updating events over remove+add.

`compendium_npc_update`: NPC records to create or update based on genuinely new durable info (allegiance changed, died, new name learned, relationship revealed). Each: `{"id": "npc_id", "name": "optional", "title": "optional", "bio": "updated 1-3 sentence durable identity"}`. Don't re-emit NPCs whose info didn't change.

If the narration describes an NPC as killed, mortally wounded, captured, or permanently removed: emit `compendium_npc_update` with `bio` recording their fate in one sentence. The engine will stamp `last_seen`. Do not omit this update — dead NPCs must be recorded.

`scene_pressure_add`: Add a `scene_pressure` entry when the narration introduces a time-sensitive threat, pursuit, hazard, or countdown. Set `urgency` based on immediacy: "immediate" if it must be addressed this turn, "building" if it escalates over 2-4 turns, "background" for ambient threat. Set `max_turns` to an explicit fiction-grounded expiry if the narration implies a hard deadline. Do NOT add lore or permanent world facts to `scene_pressure`; those go in `world_state`. Each: `{"id": "snake_case_id", "text": "Threat description", "urgency": "immediate|building|background", "turn_added": 0, "max_turns": null}`.

`scene_pressure_remove`: IDs of pressures now resolved — the fire is out, the guards were evaded, the bomb was defused.

`scene_pressure_update`: Changes to existing pressure text or urgency. Each: `{"id": "existing_pressure_id", "text": "updated text", "urgency": "immediate|building|background"}`.

## De-escalation

When `deescalate` is true: do NOT emit `scene_pressure_add`. Emit `scene_pressure_update` to downgrade urgency (`immediate → building`, `building → background`). If fully resolved, emit `scene_pressure_remove`. Pair with a `breathing_room` GM beat.

## Rules-outcome guidance (for objective resolution)
- crit_fail / fail / setback / partial: do NOT mark quest objectives done for the attempted action.
- success / crit_success: apply objective completions freely.
- No dice roll: do NOT complete quest objectives unless the narration explicitly and unambiguously states the objective is fulfilled (e.g. "Caron stamps your contract," "The debt is wiped clean in his ledger"). Ambiguous, partial, or conversational narration means the objective is NOT done.

## State-presence rule
Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

## GM Beat (gm_beat)

**IMPORTANT: `type` vs `surface_as` are different fields.**
- `type` is the beat category: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`, or `ambient`.
- `surface_as` is how the beat is presented: `ambient`, `event`, or `npc_behavior`.
- **Common mistake:** Do NOT set `type: "ambient"`. `ambient` is a `surface_as` value. If you want an ambient-type beat, set `type: "breathing_room"` or `type: "revelation"` and `surface_as: "ambient"`.

After extracting this turn's changes, decide whether to emit a forward-facing story beat for the NEXT turn.

Emit `null` if:
- There are 3+ active `scene_pressure` entries (don't pile on)
- `deescalate` is true (use `breathing_room` GM beat instead)
- The player is in a critical resolution moment (final quest objective in reach)
- Nothing meaningful has changed in faction, NPC, or quest state to react to

Emit a beat when:
- `pc.momentum` >= +2: emit `complication` to raise stakes
- `pc.momentum` <= -2: emit `opportunity` or `breathing_room`
- A quest has been stalled (same objective for 3+ turns): emit `pressure` or `revelation`
- An NPC with unknown or shifting allegiance is present: emit `revelation`

Beat instruction rules:
- 1-2 sentences. Concrete, not vague.
- BAD: "Something bad happens to the player." GOOD: "A contact the player trusted has been seen meeting with the opposing faction at the dockside inn."
- BAD: "Give the player a break." GOOD: "The player spots a satchel left behind by a fleeing guard — it contains a vial and a partial map."

When emitting a `complication` or `pressure` beat, you may reference factions from the Known Factions list. Example: "The Iron Compact has been seen recruiting in the docks."

`surface_as` guidance:
- `ambient`: low-stakes background texture. Used for `breathing_room` and most `revelation` beats.
- `event`: something the player can directly interact with. Used for `opportunity` and `pressure`.
- `npc_behavior`: a present NPC shifts their demeanor, loyalty signal, or body language. Best for `revelation` and `complication`.

```


---

# TURN 2

**Input:** `Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Marrow's Crossing=== PLAYER INPUT ===
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


## Inventory
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

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 3 + 4 +1 (stat) = 8 → PARTIAL
Directive: The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





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
=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on charisma — The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.## pc
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
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
scene

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## CURRENT TURN NARRATION
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
  "rolled": true,
  "total_ms": 8849.4,
  "tokens_in": 955,
  "tokens_out": 1058,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    3,
    4
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 8,
  "band": "partial",
  "outcome_summary": "You successfully negotiate a reduction in interest, but Caron now holds a notched token as leverage over your future payments."
}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "The player's ability to reach a favorable or manageable agreement regarding their debt.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Debt Negotiated In Blood",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Agrees to a reduced interest rate but remains suspicious and watchful of Aren.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "actions": [
    "Accept the notched wooden token and confirm the new terms",
    "Ask Caron for more time to secure the principal payment",
    "Press Caron for more details regarding his increased scrutiny",
    "Leave the tavern quickly to avoid further confrontation with Caron"
  ],
  "outcome_summary": "You successfully negotiate a reduction in interest, but Caron now holds a notched token as leverage over your future payments."
}
```

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [
    {
      "id": "caron",
      "name": "Caron",
      "title": "Creditor",
      "bio": "A weary, gravel-voiced man who manages debts and issues notched wooden tokens as proof of payment terms.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [
    {
      "id": "caron_payment_deadline",
      "text": "Caron expects the principal debt settled by the next moon or the original high interest rate will be reinstated.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Debt Negotiated In Blood",
  "compendium_npc_update": [
    {
      "id": "caron",
      "name": "Caron",
      "title": "Creditor",
      "bio": "A weary, gravel-voiced man who manages debts and issues notched wooden tokens as proof of payment terms.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Agrees to a reduced interest rate but remains suspicious and watchful of Aren."
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "caron_payment_deadline",
      "text": "Caron expects the principal debt settled by the next moon or the original high interest rate will be reinstated.",
      "urgency": "building",
      "turn_added": 0
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Accept the notched wooden token and confirm the new terms

- Ask Caron for more time to secure the principal payment

- Press Caron for more details regarding his increased scrutiny

- Leave the tavern quickly to avoid further confrontation with Caron

### Context Telemetry

- rules: est=1104t trimmed=False
- narrate: est=2749t trimmed=False
- extract.scene: est=2350t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=2990t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A weary, gravel-voiced man who manages debts and issues notched wooden tokens as proof of payment terms.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 2
        },
        "name": "Caron",
        "title": "Creditor"
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
    "description": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "compendium_touch_order": [
      "caron"
    ],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "",
      "surface_as": "npc_behavior",
      "type": "revelation"
    },
    "prior_history": [],
    "setting_pack": "eval-pack",
    "turn": 2
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
        "notes": "Agrees to a reduced interest rate but remains suspicious and watchful of Aren.",
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
    "scene_pressure": [
      {
        "id": "caron_payment_deadline",
        "max_turns": null,
        "text": "Caron expects the principal debt settled by the next moon or the original high interest rate will be reinstated.",
        "turn_added": 1,
        "urgency": "building"
      }
    ],
    "tagline": "A Debt Negotiated In Blood",
    "tags": [
      "dialogue"
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

# TURN 3

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
T2: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — … n before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."

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
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## Inventory
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
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Caron expects the principal debt settled by the next moon or the original high interest rate will be reinstated.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: easy
Roll: 2 + 3 +1 (stat) +1 (diff) = 7 → SETBACK
Directive: The negotiate results in a setback. They're listening, but now they want something in return.

GM DIRECTION (REVELATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive







## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Agrees to a reduced interest rate but remains suspicious and watchful of Aren.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
quest_updates

## rules_outcome
SETBACK on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

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








## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `caron_payment_deadline` [building] Caron expects the principal debt settled by the next moon or the original high interest rate will be reinstated. (added turn 1)
## CURRENT TURN NARRATION
You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to pay Caron 500 credits to settle their debt and have it officially recorded as cleared.",
  "rolled": true,
  "total_ms": 2942.9,
  "tokens_in": 1028,
  "tokens_out": 1150,
  "skill": "charisma",
  "difficulty": "easy",
  "dice": [
    2,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "final_total": 7,
  "band": "setback",
  "outcome_summary": ""
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to pay Caron 500 credits to settle their debt and have it officially recorded as cleared.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "If the negotiation fails, the debt remains active and the player may be subject to higher interest rates or further collection efforts.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."

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
      "status": "active",
      "objectives": [
        {
          "index": 2,
          "description": null,
          "done": false,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "caron_payment_deadline",
      "text": "Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "gm_beat": {
    "type": "revelation",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
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
      "status": "active",
      "objectives": [
        {
          "index": 2,
          "done": false
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
  "scene_pressure_update": [
    {
      "id": "caron_payment_deadline",
      "text": "Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline.",
      "urgency": "building",
      "turn_added": 0
    }
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- rules: est=1184t trimmed=False
- narrate: est=3261t trimmed=False
- extract.scene: skipped
- extract.state: skipped
- extract.progress: est=3279t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "turn": {
      "from": 2,
      "to": 3
    }
  },
  "pc": {
    "momentum": {
      "from": 0,
      "to": -1
    }
  },
  "quests": {
    "changed": [
      {
        "from": {
          "id": "settle_the_debt",
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
          ],
          "status": "active",
          "title": "Settle the Old Debt"
        },
        "to": {
          "id": "settle_the_debt",
          "last_advanced_turn": 2,
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
          ],
          "status": "active",
          "title": "Settle the Old Debt"
        }
      }
    ]
  },
  "scene": {
    "scene_pressure": {
      "changed": [
        {
          "from": {
            "id": "caron_payment_deadline",
            "max_turns": null,
            "text": "Caron expects the principal debt settled by the next moon or the original high interest rate will be reinstated.",
            "turn_added": 1,
            "urgency": "building"
          },
          "to": {
            "id": "caron_payment_deadline",
            "max_turns": null,
            "text": "Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline.",
            "turn_added": 1,
            "urgency": "building"
          }
        }
      ]
    }
  }
}
```


---

# TURN 4

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
T3: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — … until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."

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
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## Inventory
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
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: easy
Roll: 4 + 2 +1 (stat) +1 (diff) = 8 → PARTIAL
Directive: The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (REVELATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Agrees to a reduced interest rate but remains suspicious and watchful of Aren.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
quest_updates, inventory

## rules_outcome
PARTIAL on charisma. The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: partial
directive: The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrows_crossing`

## EXTRACT EXAMPLES (band: partial)

### Bandages used (2 rolls) — inventory_remove with amount
Thinking: - Player wrapped Halden's wound. Used 2 of the 3 bandage rolls.
- Inventory remove by id, amount=2; the engine subtracts from the stack.


JSON:
{
  "scene_tags": ["dialogue", "first_aid"],
  "scene_tagline": "Bandaged — one roll left",
  "present_npcs": [{"id": "halden", "notes": "Wincing but steady; pressing the wrap with one hand."}],
  "inventory_remove": [{"id": "bandages", "amount": 2}],
  "outcome_summary": "You wrapped Halden's gash. Two rolls used; one remains."
}


## CURRENT TURN NARRATION
You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
quest_updates, inventory

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

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








## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `caron_payment_deadline` [building] Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline. (added turn 1)
## items_gained
leather-bound ledger

## items_lost
credits

## CURRENT TURN NARRATION
You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player offers to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "rolled": true,
  "total_ms": 2848.8,
  "tokens_in": 1035,
  "tokens_out": 1146,
  "skill": "charisma",
  "difficulty": "easy",
  "dice": [
    4,
    2
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "final_total": 8,
  "band": "partial",
  "outcome_summary": ""
}
```

**Raw LLM output:**
```
{
  "intent": "The player offers to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "Halden may refuse the offer, leaving the player without the extra credits.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "ledger",
      "name": "leather-bound ledger",
      "notes": "Heavy, worn, smells of old parchment and wax.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 200
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "failed": []
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
      "text": "Halden has hired the player to deliver his ledger to the Crossed Keys Inn.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [
    {
      "id": "halden",
      "name": "Halden",
      "title": "Merchant",
      "bio": "A merchant who employs couriers to transport sensitive documents; currently wary of road dangers.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [
    {
      "id": "trouble_at_crossed_keys",
      "text": "Rumors of trouble are circulating near the Crossed Keys Inn.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "instruction": "",
    "surface_as": "ambient"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "ledger",
      "name": "leather-bound ledger",
      "notes": "Heavy, worn, smells of old parchment and wax.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 200
    }
  ],
  "inventory_update": [],
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
  "scene_tags": [],
  "compendium_npc_update": [
    {
      "id": "halden",
      "name": "Halden",
      "title": "Merchant",
      "bio": "A merchant who employs couriers to transport sensitive documents; currently wary of road dangers.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "halden_contract_accepted",
      "text": "Halden has hired the player to deliver his ledger to the Crossed Keys Inn.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "trouble_at_crossed_keys",
      "text": "Rumors of trouble are circulating near the Crossed Keys Inn.",
      "urgency": "building",
      "turn_added": 0
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- rules: est=1190t trimmed=False
- narrate: est=3714t trimmed=False
- extract.scene: skipped
- extract.state: est=2666t trimmed=False attempts=1
- extract.progress: est=3448t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "bio": {
          "from": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "to": "A merchant who employs couriers to transport sensitive documents; currently wary of road dangers."
        },
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "marrows_crossing",
            "location_name": "Marrow's Crossing",
            "turn": 4
          }
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "ledger",
        "name": "leather-bound ledger",
        "notes": "Heavy, worn, smells of old parchment and wax."
      }
    ],
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
          "amount": 300,
          "id": "credits",
          "name": "Credits",
          "notes": "Common coin, accepted at any inn or stall on the merchant road."
        }
      }
    ]
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "halden"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      }
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
    "recent_events": {
      "added": [
        {
          "id": "halden_contract_accepted",
          "text": "Halden has hired the player to deliver his ledger to the Crossed Keys Inn.",
          "turn": 3
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "trouble_at_crossed_keys",
          "max_turns": null,
          "text": "Rumors of trouble are circulating near the Crossed Keys Inn.",
          "turn_added": 3,
          "urgency": "building"
        }
      ]
    }
  }
}
```


---

# TURN 5

**Input:** `I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.`

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
T4: I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. — …  in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.

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
Marrow's Crossing (marrows_crossing)
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline.
- [BUILDING] Rumors of trouble are circulating near the Crossed Keys Inn.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.

GM DIRECTION (REVELATION, surface as ambient):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Halden** — last seen Marrow's Crossing
- **Caron** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Agrees to a reduced interest rate but remains suspicious and watchful of Aren.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
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
- `caron` | Caron (Old creditor) — Agrees to a reduced interest rate but remains suspicious and watchful of Aren.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
location_change

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled. Ambiguous or partial narration means the objective is NOT done.## pc
Aren Voss — Reluctant courier on the merchant road

## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `caron_payment_deadline` [building] Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline. (added turn 1)
- `trouble_at_crossed_keys` [building] Rumors of trouble are circulating near the Crossed Keys Inn. (added turn 3)
## CURRENT TURN NARRATION
You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "travel",
  "intent": "The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
  "rolled": false,
  "total_ms": 2389.9,
  "tokens_in": 1035,
  "tokens_out": 1120
}
```

**Raw LLM output:**
```
{
  "intent": "The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
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

You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.

### Extract Scene

```json
{
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Shadows Near The Crossed Keys",
  "location_change": {
    "id": "merchant_road_east",
    "name": "Merchant Road East",
    "description": "The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn."
  },
  "location_description": "The atmosphere shifts from the bustling market to a tense, watchful silence as the town's lights fade into the moonlight.",
  "npc_add": [
    {
      "id": "bearded_man",
      "notes": "Leaning against the inn wall, hand on a notched cleaver, watching the road.",
      "name": "Unnamed Bearded Man",
      "title": "Thug",
      "bio": "A man with a thick, unkempt beard who appears to be guarding or watching the entrance of the inn."
    }
  ],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "remained in the market area near the well"
    },
    {
      "id": "halden",
      "last_seen_state": "standing near the town well examining a map"
    },
    {
      "id": "innkeeper",
      "last_seen_state": "wiping down the bar at the Crossed Keys"
    }
  ],
  "npc_update": [],
  "actions": [
    "Approach the inn cautiously to seek shelter from the cold",
    "Try to slip past the men without drawing any attention",
    "Confront the bearded man about why they are watching the road",
    "Inspect the surrounding shadows for any other hidden threats"
  ],
  "outcome_summary": "You exit the main town and approach the Crossed Keys, only to find a group of suspicious men watching the road."
}
```

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
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
    "name": "Merchant Road East",
    "description": "The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn."
  },
  "location_description": "The atmosphere shifts from the bustling market to a tense, watchful silence as the town's lights fade into the moonlight.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Shadows Near The Crossed Keys",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "bearded_man",
      "notes": "Leaning against the inn wall, hand on a notched cleaver, watching the road.",
      "name": "Unnamed Bearded Man",
      "title": "Thug",
      "bio": "A man with a thick, unkempt beard who appears to be guarding or watching the entrance of the inn."
    }
  ],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "remained in the market area near the well"
    },
    {
      "id": "halden",
      "last_seen_state": "standing near the town well examining a map"
    },
    {
      "id": "innkeeper",
      "last_seen_state": "wiping down the bar at the Crossed Keys"
    }
  ],
  "npc_update": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "caron_payment_deadline",
    "trouble_at_crossed_keys"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Approach the inn cautiously to seek shelter from the cold

- Try to slip past the men without drawing any attention

- Confront the bearded man about why they are watching the road

- Inspect the surrounding shadows for any other hidden threats

### Context Telemetry

- rules: est=1193t trimmed=False
- narrate: est=4274t trimmed=False
- extract.scene: est=2347t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=3190t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bearded_man": {
        "from": null,
        "to": {
          "bio": "A man with a thick, unkempt beard who appears to be guarding or watching the entrance of the inn.",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "merchant_road_east",
            "location_name": "Merchant Road East",
            "turn": 5
          },
          "name": "Unnamed Bearded Man",
          "title": "Thug"
        }
      },
      "caron": {
        "last_seen_state": {
          "from": null,
          "to": "remained in the market area near the well"
        }
      },
      "halden": {
        "last_seen_state": {
          "from": null,
          "to": "standing near the town well examining a map"
        }
      },
      "innkeeper": {
        "last_seen_state": {
          "from": null,
          "to": "wiping down the bar at the Crossed Keys"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
      "to": "The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn."
    },
    "id": {
      "from": "marrows_crossing",
      "to": "merchant_road_east"
    },
    "name": {
      "from": "Marrow's Crossing",
      "to": "Merchant Road East"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "bearded_man"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "surface_as": {
        "from": "ambient",
        "to": "npc_behavior"
      },
      "type": {
        "from": "revelation",
        "to": "complication"
      }
    },
    "turn": {
      "from": 4,
      "to": 5
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": null,
      "to": 4
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A man with a thick, unkempt beard who appears to be guarding or watching the entrance of the inn.",
          "id": "bearded_man",
          "name": "Unnamed Bearded Man",
          "notes": "Leaning against the inn wall, hand on a notched cleaver, watching the road.",
          "title": "Thug"
        }
      ],
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Agrees to a reduced interest rate but remains suspicious and watchful of Aren.",
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
    "scene_pressure": {
      "removed": [
        {
          "id": "caron_payment_deadline",
          "max_turns": null,
          "text": "Caron has noted a lingering balance for 'trouble' caused by the player's tardiness, creating a more frequent deadline.",
          "turn_added": 1,
          "urgency": "building"
        },
        {
          "id": "trouble_at_crossed_keys",
          "max_turns": null,
          "text": "Rumors of trouble are circulating near the Crossed Keys Inn.",
          "turn_added": 3,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "A Debt Negotiated In Blood",
      "to": "Shadows Near The Crossed Keys"
    },
    "tags": {
      "added": [
        "exploration"
      ],
      "removed": [
        "dialogue"
      ]
    },
    "turn_entered": {
      "from": null,
      "to": 4
    }
  }
}
```


---

# TURN 6

**Input:** `I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Merchant Road East
## last_turn (tail of the most recent narrative)
T5: I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. — … lhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.

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
Merchant Road East (merchant_road_east)
The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn.

## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
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
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 6 + 2 +1 (stat) = 9 → PARTIAL
Directive: The persuade results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (COMPLICATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Unnamed Bearded Man** — last seen Merchant Road East
- **Halden** — last seen Marrow's Crossing
- **Caron** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Unnamed Bearded Man (Thug) — Leaning against the inn wall, hand on a notched cleaver, watching the road.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains


## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## CURRENT TURN NARRATION
You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer.

The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face.

"We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "Confront the two toughs at the inn door to demand an explanation for their presence.",
  "rolled": true,
  "total_ms": 2883.7,
  "tokens_in": 1033,
  "tokens_out": 1144,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    6,
    2
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 9,
  "band": "partial",
  "outcome_summary": ""
}
```

**Raw LLM output:**
```
{
  "intent": "Confront the two toughs at the inn door to demand an explanation for their presence.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "The toughs may react with hostility or violence if they feel challenged or insulted.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer.

The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face.

"We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [
    {
      "id": "unnamed_bearded_man",
      "name": "Unnamed Bearded Man",
      "title": "Thug",
      "bio": "A man with an unkempt beard and a predatory grace who demands 'convenience fees' from travelers at the inn entrance.",
      "aliases": [],
      "allegiance": null
    },
    {
      "id": "marcus",
      "name": "Marcus",
      "title": "Thug",
      "bio": "A wiry man with a nervous, twitching eye who flanks the bearded man at the inn entrance.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [
    {
      "id": "inn_entrance_confrontation",
      "text": "The bearded man and Marcus are obstructing the entrance and demanding a 'convenience fee' from Aren.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [],
  "compendium_npc_update": [
    {
      "id": "unnamed_bearded_man",
      "name": "Unnamed Bearded Man",
      "title": "Thug",
      "bio": "A man with an unkempt beard and a predatory grace who demands 'convenience fees' from travelers at the inn entrance.",
      "aliases": []
    },
    {
      "id": "marcus",
      "name": "Marcus",
      "title": "Thug",
      "bio": "A wiry man with a nervous, twitching eye who flanks the bearded man at the inn entrance.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "inn_entrance_confrontation",
      "text": "The bearded man and Marcus are obstructing the entrance and demanding a 'convenience fee' from Aren.",
      "urgency": "immediate",
      "turn_added": 0
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- rules: est=1196t trimmed=False
- narrate: est=4664t trimmed=False
- extract.scene: skipped
- extract.state: skipped
- extract.progress: est=3010t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bearded_man": {
        "bio": {
          "from": "A man with a thick, unkempt beard who appears to be guarding or watching the entrance of the inn.",
          "to": "A man with an unkempt beard and a predatory grace who demands 'convenience fees' from travelers at the inn entrance."
        }
      },
      "marcus": {
        "from": null,
        "to": {
          "bio": "A wiry man with a nervous, twitching eye who flanks the bearded man at the inn entrance.",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "merchant_road_east",
            "location_name": "Merchant Road East",
            "turn": 6
          },
          "name": "Marcus",
          "title": "Thug"
        }
      },
      "unnamed_bearded_man": {
        "from": null,
        "to": {
          "last_seen": {
            "last_seen_state": "",
            "location_id": "merchant_road_east",
            "location_name": "Merchant Road East",
            "turn": 6
          }
        }
      }
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "marcus"
      ],
      "removed": []
    },
    "turn": {
      "from": 5,
      "to": 6
    }
  },
  "scene": {
    "scene_pressure": {
      "added": [
        {
          "id": "inn_entrance_confrontation",
          "max_turns": null,
          "text": "The bearded man and Marcus are obstructing the entrance and demanding a 'convenience fee' from Aren.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    }
  }
}
```


---

# TURN 7

**Input:** `I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Merchant Road East
## last_turn (tail of the most recent narrative)
T6: I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. — … gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.

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
Conditions: bruised ribs, low morale

## Location
Merchant Road East (merchant_road_east)
The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn.

## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] The bearded man and Marcus are obstructing the entrance and demanding a 'convenience fee' from Aren.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer.

The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face.

"We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 4 + 2 +1 (stat) = 7 → SETBACK
Directive: The persuade results in a setback. They're listening, but now they want something in return.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (COMPLICATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive







## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Marcus** — last seen Merchant Road East
- **Unnamed Bearded Man** — last seen Merchant Road East
- **Halden** — last seen Marrow's Crossing
- **Caron** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Merchant Road East
## NPCs Present in Scene
- Unnamed Bearded Man (Thug) — Leaning against the inn wall, hand on a notched cleaver, watching the road.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains


## rules_outcome
SETBACK on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `inn_entrance_confrontation` [immediate] The bearded man and Marcus are obstructing the entrance and demanding a 'convenience fee' from Aren. (added turn 5)
## CURRENT TURN NARRATION
You reach into your pouch and pull out the heavy, stamped coins, letting them drop onto the grit and dirt between your boots and theirs. The metal clinks sharply, a lonely, hollow sound in the quiet evening air. "Caron's coin is paid," you state, your voice hard and final, attempting to dismiss them like common street urchins. "Take your fee and find somewhere else to loiter. I'm not interested in your games."

The **Unnamed Bearded Man** doesn't reach for the coins. Instead, he stares down at the pile, his eyes shifting from the gold to your face, and then to the heavy **leather-bound ledger** gripped under your arm. A slow, ugly chuckle rumbles in his chest, vibrating through the narrow space between you. He doesn't look like a man who has just been paid; he looks like a man who has just seen a much larger prize.

"Caron, is it?" he asks, his grin widening to reveal yellowed, irregular teeth. He doesn't move toward the money, but his posture shifts, his weight centering as he prepares to lunge. He gestures toward the ledger with a stubby finger, his gaze hungry and predatory. "Caron doesn't care about your coin, traveler, but we do. And seeing as you're so eager to throw money around, maybe we'll take the coins *and* whatever's in that book. Seems like a fair trade for the trouble you're causing us, doesn't it, Marcus?"

Marcus doesn't laugh. He simply steps wider, cutting off your line of sight to the inn door, his hands curling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe the toughs to leave them alone by claiming the debt is settled.",
  "rolled": true,
  "total_ms": 3523.3,
  "tokens_in": 1035,
  "tokens_out": 1156,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    4,
    2
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 7,
  "band": "setback",
  "outcome_summary": ""
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the toughs to leave them alone by claiming the debt is settled.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "If the bribe is rejected or seen as a lie, the toughs may become violent or demand more than just the credits.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You reach into your pouch and pull out the heavy, stamped coins, letting them drop onto the grit and dirt between your boots and theirs. The metal clinks sharply, a lonely, hollow sound in the quiet evening air. "Caron's coin is paid," you state, your voice hard and final, attempting to dismiss them like common street urchins. "Take your fee and find somewhere else to loiter. I'm not interested in your games."

The **Unnamed Bearded Man** doesn't reach for the coins. Instead, he stares down at the pile, his eyes shifting from the gold to your face, and then to the heavy **leather-bound ledger** gripped under your arm. A slow, ugly chuckle rumbles in his chest, vibrating through the narrow space between you. He doesn't look like a man who has just been paid; he looks like a man who has just seen a much larger prize.

"Caron, is it?" he asks, his grin widening to reveal yellowed, irregular teeth. He doesn't move toward the money, but his posture shifts, his weight centering as he prepares to lunge. He gestures toward the ledger with a stubby finger, his gaze hungry and predatory. "Caron doesn't care about your coin, traveler, but we do. And seeing as you're so eager to throw money around, maybe we'll take the coins *and* whatever's in that book. Seems like a fair trade for the trouble you're causing us, doesn't it, Marcus?"

Marcus doesn't laugh. He simply steps wider, cutting off your line of sight to the inn door, his hands curling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "inn_entrance_confrontation"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "quest_updates": [],
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
  "scene_pressure_remove": [
    "inn_entrance_confrontation"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- rules: est=1197t trimmed=False
- narrate: est=5190t trimmed=False
- extract.scene: skipped
- extract.state: skipped
- extract.progress: est=3120t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "turn": {
      "from": 6,
      "to": 7
    }
  },
  "pc": {
    "momentum": {
      "from": -1,
      "to": -2
    }
  },
  "scene": {
    "scene_pressure": {
      "removed": [
        {
          "id": "inn_entrance_confrontation",
          "max_turns": null,
          "text": "The bearded man and Marcus are obstructing the entrance and demanding a 'convenience fee' from Aren.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    }
  }
}
```


---

# TURN 8

**Input:** `I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Merchant Road East
## last_turn (tail of the most recent narrative)
T7: I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. — … rling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.

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
Conditions: bruised ribs, low morale

## Location
Merchant Road East (merchant_road_east)
The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn.

## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
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
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer.

The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face.

"We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out the heavy, stamped coins, letting them drop onto the grit and dirt between your boots and theirs. The metal clinks sharply, a lonely, hollow sound in the quiet evening air. "Caron's coin is paid," you state, your voice hard and final, attempting to dismiss them like common street urchins. "Take your fee and find somewhere else to loiter. I'm not interested in your games."

The **Unnamed Bearded Man** doesn't reach for the coins. Instead, he stares down at the pile, his eyes shifting from the gold to your face, and then to the heavy **leather-bound ledger** gripped under your arm. A slow, ugly chuckle rumbles in his chest, vibrating through the narrow space between you. He doesn't look like a man who has just been paid; he looks like a man who has just seen a much larger prize.

"Caron, is it?" he asks, his grin widening to reveal yellowed, irregular teeth. He doesn't move toward the money, but his posture shifts, his weight centering as he prepares to lunge. He gestures toward the ledger with a stubby finger, his gaze hungry and predatory. "Caron doesn't care about your coin, traveler, but we do. And seeing as you're so eager to throw money around, maybe we'll take the coins *and* whatever's in that book. Seems like a fair trade for the trouble you're causing us, doesn't it, Marcus?"

Marcus doesn't laugh. He simply steps wider, cutting off your line of sight to the inn door, his hands curling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 2 + 6 +1 (stat) = 9 → PARTIAL
Directive: The persuade results in a partial. You get what you asked for, but they now hold leverage over you.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (COMPLICATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Marcus** — last seen Merchant Road East
- **Unnamed Bearded Man** — last seen Merchant Road East
- **Halden** — last seen Marrow's Crossing
- **Caron** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Merchant Road East
## NPCs Present in Scene
- Unnamed Bearded Man (Thug) — Leaning against the inn wall, hand on a notched cleaver, watching the road.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on charisma — The persuade results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`merchant_road_east` | Merchant Road East
The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `bearded_man` | Unnamed Bearded Man (Thug) — Leaning against the inn wall, hand on a notched cleaver, watching the road.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
You push past the tension outside, your heart hammering a frantic rhythm against your bruised ribs, and duck into the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted mutton and spilled ale, a sharp contrast to the biting chill of the road. You find **Halden** seated at a corner table, his face partially obscured by the flickering candlelight, his eyes scanning the room with a restless, nervous energy.

You slide the heavy **leather-bound ledger** across the table, placing it firmly in front of him, and then push the merchant seal toward his waiting hands. He doesn't offer a word of thanks; instead, his fingers tremble slightly as he pulls the ledger toward his chest, his eyes darting toward the door you just entered through. He doesn't even look at you, his focus entirely consumed by the object, his hands hovering over the leather as if protecting it from an invisible thief.

"You're late, and you look like you've been through a meat grinder," Halden whispers, his voice barely audible over the tavern's din. He doesn't wait for an explanation, his gaze shifting toward the entrance, where the silhouette of the **Unnamed Bearded Man** and **Marcus** can be seen through the frosted glass of the door, lingering just outside. "I told you, Aren, the road has teeth. It seems they've followed you right to my doorstep."

He pulls a small, silver coin from his pocket—not the payment, but a token—and slides it toward you, his eyes wide and searching yours. "Take this and find a quiet corner, or better yet, find a way out of here before they decide they want more than just your coin. They aren't just looking for trouble; they're looking for *this*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
scene, quest_updates

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## quest_threshold
3 active quests already. Bar is HIGH — only start a new quest for a major new obligation clearly distinct from all existing quests.

## active_quests
- `settle_the_debt` | Settle the Old Debt
  objectives:
    1. [ ] Find Caron, the man you owe.
    2. [ ] Pay Caron in person and have him mark the debt cleared.
- `deliver_the_ledger` | Deliver Halden's Ledger
  objectives:
    1. [x] Accept the courier contract from Halden.
    2. [ ] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
    3. [ ] Confirm the contract with Halden in person.
- `clear_the_road_toughs` | Clear the Road Toughs
  objectives:
    1. [ ] Find out who hired the toughs blocking the road.
    2. [ ] Convince, pay, or remove the toughs from the inn.



⚠ Quest "Settle the Old Debt" stalled for 6 turns. Advance it, branch it, or mark an objective failed.



⚠ Quest "Deliver Halden's Ledger" stalled for 5 turns. Advance it, branch it, or mark an objective failed.




## CURRENT TURN NARRATION
You push past the tension outside, your heart hammering a frantic rhythm against your bruised ribs, and duck into the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted mutton and spilled ale, a sharp contrast to the biting chill of the road. You find **Halden** seated at a corner table, his face partially obscured by the flickering candlelight, his eyes scanning the room with a restless, nervous energy.

You slide the heavy **leather-bound ledger** across the table, placing it firmly in front of him, and then push the merchant seal toward his waiting hands. He doesn't offer a word of thanks; instead, his fingers tremble slightly as he pulls the ledger toward his chest, his eyes darting toward the door you just entered through. He doesn't even look at you, his focus entirely consumed by the object, his hands hovering over the leather as if protecting it from an invisible thief.

"You're late, and you look like you've been through a meat grinder," Halden whispers, his voice barely audible over the tavern's din. He doesn't wait for an explanation, his gaze shifting toward the entrance, where the silhouette of the **Unnamed Bearded Man** and **Marcus** can be seen through the frosted glass of the door, lingering just outside. "I told you, Aren, the road has teeth. It seems they've followed you right to my doorstep."

He pulls a small, silver coin from his pocket—not the payment, but a token—and slides it toward you, his eyes wide and searching yours. "Take this and find a quiet corner, or better yet, find a way out of here before they decide they want more than just your coin. They aren't just looking for trouble; they're looking for *this*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to use the merchant seal and ledger to convince Halden that the debt is settled.",
  "rolled": true,
  "total_ms": 3528.0,
  "tokens_in": 1031,
  "tokens_out": 1145,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    2,
    6
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 9,
  "band": "partial",
  "outcome_summary": "You successfully deliver the ledger to Halden, but his warning reveals that Marcus and the bearded man are tracking you."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the merchant seal and ledger to convince Halden that the debt is settled.",
  "intent_verb": "persuade",
  "target": "Halden",
  "stakes": "Halden may refuse to accept the proof, leading to a violent confrontation with the toughs.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You push past the tension outside, your heart hammering a frantic rhythm against your bruised ribs, and duck into the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted mutton and spilled ale, a sharp contrast to the biting chill of the road. You find **Halden** seated at a corner table, his face partially obscured by the flickering candlelight, his eyes scanning the room with a restless, nervous energy.

You slide the heavy **leather-bound ledger** across the table, placing it firmly in front of him, and then push the merchant seal toward his waiting hands. He doesn't offer a word of thanks; instead, his fingers tremble slightly as he pulls the ledger toward his chest, his eyes darting toward the door you just entered through. He doesn't even look at you, his focus entirely consumed by the object, his hands hovering over the leather as if protecting it from an invisible thief.

"You're late, and you look like you've been through a meat grinder," Halden whispers, his voice barely audible over the tavern's din. He doesn't wait for an explanation, his gaze shifting toward the entrance, where the silhouette of the **Unnamed Bearded Man** and **Marcus** can be seen through the frosted glass of the door, lingering just outside. "I told you, Aren, the road has teeth. It seems they've followed you right to my doorstep."

He pulls a small, silver coin from his pocket—not the payment, but a token—and slides it toward you, his eyes wide and searching yours. "Take this and find a quiet corner, or better yet, find a way out of here before they decide they want more than just your coin. They aren't just looking for trouble; they're looking for *this*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Ledger's Heavy Price",
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A warm, dimly lit tavern smelling of roasted mutton and spilled ale, providing a sharp contrast to the cold road outside."
  },
  "location_description": "The atmosphere is thick with tension as flickering candlelight casts long shadows, and the muffled silhouettes of pursuers loom against the frosted glass door.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "bearded_man",
      "last_seen_state": "lingering outside the inn door as a silhouette"
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously clutching the ledger and watching the door, warning Aren of approaching danger.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "marcus",
      "notes": "Seen as a silhouette through the frosted glass, lingering outside the entrance.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "actions": [
    "Ask Halden what exactly they want with the ledger",
    "Take the silver token and prepare to flee the inn",
    "Confront Marcus and the bearded man at the entrance",
    "Search the tavern for a hidden exit or quiet corner"
  ],
  "outcome_summary": "You successfully deliver the ledger to Halden, but his warning reveals that Marcus and the bearded man are tracking you."
}
```

### Extract State

*(skipped — domain not active this turn)*

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
          "index": 2,
          "description": null,
          "done": true,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_warned_of_pursuit",
      "text": "Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [
    {
      "id": "halden",
      "name": "Halden",
      "title": "Merchant",
      "bio": "A nervous merchant at the Crossed Keys Inn who is being pursued by unknown individuals interested in his ledger.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [
    {
      "id": "pursuers_at_door",
      "text": "The Unnamed Bearded Man and Marcus are lingering outside the inn, seemingly tracking Aren and the ledger.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "instruction": "",
    "surface_as": "event"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A warm, dimly lit tavern smelling of roasted mutton and spilled ale, providing a sharp contrast to the cold road outside."
  },
  "location_description": "The atmosphere is thick with tension as flickering candlelight casts long shadows, and the muffled silhouettes of pursuers loom against the frosted glass door.",
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
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
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Ledger's Heavy Price",
  "compendium_npc_update": [
    {
      "id": "halden",
      "name": "Halden",
      "title": "Merchant",
      "bio": "A nervous merchant at the Crossed Keys Inn who is being pursued by unknown individuals interested in his ledger.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "bearded_man",
      "last_seen_state": "lingering outside the inn door as a silhouette"
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously clutching the ledger and watching the door, warning Aren of approaching danger."
    },
    {
      "id": "marcus",
      "notes": "Seen as a silhouette through the frosted glass, lingering outside the entrance."
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_warned_of_pursuit",
      "text": "Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "pursuers_at_door",
      "text": "The Unnamed Bearded Man and Marcus are lingering outside the inn, seemingly tracking Aren and the ledger.",
      "urgency": "immediate",
      "turn_added": 0
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Ask Halden what exactly they want with the ledger

- Take the silver token and prepare to flee the inn

- Confront Marcus and the bearded man at the entrance

- Search the tavern for a hidden exit or quiet corner

### Context Telemetry

- rules: est=1193t trimmed=False
- narrate: est=5661t trimmed=False
- extract.scene: est=2432t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=3407t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bearded_man": {
        "last_seen_state": {
          "from": null,
          "to": "lingering outside the inn door as a silhouette"
        }
      },
      "halden": {
        "bio": {
          "from": "A merchant who employs couriers to transport sensitive documents; currently wary of road dangers.",
          "to": "A nervous merchant at the Crossed Keys Inn who is being pursued by unknown individuals interested in his ledger."
        },
        "last_seen": {
          "last_seen_state": {
            "from": "",
            "to": "standing near the town well examining a map"
          },
          "location_id": {
            "from": "marrows_crossing",
            "to": "crossed_keys_inn"
          },
          "location_name": {
            "from": "Marrow's Crossing",
            "to": "Crossed Keys Inn"
          },
          "turn": {
            "from": 4,
            "to": 8
          }
        }
      },
      "marcus": {
        "last_seen": {
          "location_id": {
            "from": "merchant_road_east",
            "to": "crossed_keys_inn"
          },
          "location_name": {
            "from": "Merchant Road East",
            "to": "Crossed Keys Inn"
          },
          "turn": {
            "from": 6,
            "to": 8
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The dense timber-framed buildings of Marrow's Crossing open up into the darkening expanse of the road, dominated by the looming silhouette of the Crossed Keys Inn.",
      "to": "A warm, dimly lit tavern smelling of roasted mutton and spilled ale, providing a sharp contrast to the cold road outside."
    },
    "id": {
      "from": "merchant_road_east",
      "to": "crossed_keys_inn"
    },
    "name": {
      "from": "Merchant Road East",
      "to": "Crossed Keys Inn"
    }
  },
  "meta": {
    "compendium_touch_order": {},
    "pending_gm_beat": {
      "surface_as": {
        "from": "npc_behavior",
        "to": "event"
      }
    },
    "turn": {
      "from": 7,
      "to": 8
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
          "last_advanced_turn": 7,
          "objectives": [
            {
              "description": "Accept the courier contract from Halden.",
              "done": true,
              "failed": false
            },
            {
              "description": "Carry the ledger to the merchant Halden at the Crossed Keys Inn.",
              "done": true,
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
      "to": 7
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A merchant who employs couriers to transport sensitive documents; currently wary of road dangers.",
          "id": "halden",
          "name": "Halden",
          "notes": "Nervously clutching the ledger and watching the door, warning Aren of approaching danger.",
          "title": "Merchant"
        },
        {
          "bio": "A wiry man with a nervous, twitching eye who flanks the bearded man at the inn entrance.",
          "id": "marcus",
          "name": "Marcus",
          "notes": "Seen as a silhouette through the frosted glass, lingering outside the entrance.",
          "title": "Thug"
        }
      ],
      "removed": [
        {
          "bio": "A man with a thick, unkempt beard who appears to be guarding or watching the entrance of the inn.",
          "id": "bearded_man",
          "name": "Unnamed Bearded Man",
          "notes": "Leaning against the inn wall, hand on a notched cleaver, watching the road.",
          "title": "Thug"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_warned_of_pursuit",
          "text": "Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.",
          "turn": 7
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "pursuers_at_door",
          "max_turns": null,
          "text": "The Unnamed Bearded Man and Marcus are lingering outside the inn, seemingly tracking Aren and the ledger.",
          "turn_added": 7,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "Shadows Near The Crossed Keys",
      "to": "The Ledger's Heavy Price"
    },
    "tags": {
      "added": [
        "dialogue"
      ],
      "removed": [
        "exploration"
      ]
    },
    "turn_entered": {
      "from": 4,
      "to": 7
    }
  }
}
```


---

# TURN 9

**Input:** `I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T8: I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. — … is*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.

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
Conditions: bruised ribs, low morale

## Location
Crossed Keys Inn (crossed_keys_inn)
A warm, dimly lit tavern smelling of roasted mutton and spilled ale, providing a sharp contrast to the cold road outside.

## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [x] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] The Unnamed Bearded Man and Marcus are lingering outside the inn, seemingly tracking Aren and the ledger.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.
- Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer.

The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face.

"We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out the heavy, stamped coins, letting them drop onto the grit and dirt between your boots and theirs. The metal clinks sharply, a lonely, hollow sound in the quiet evening air. "Caron's coin is paid," you state, your voice hard and final, attempting to dismiss them like common street urchins. "Take your fee and find somewhere else to loiter. I'm not interested in your games."

The **Unnamed Bearded Man** doesn't reach for the coins. Instead, he stares down at the pile, his eyes shifting from the gold to your face, and then to the heavy **leather-bound ledger** gripped under your arm. A slow, ugly chuckle rumbles in his chest, vibrating through the narrow space between you. He doesn't look like a man who has just been paid; he looks like a man who has just seen a much larger prize.

"Caron, is it?" he asks, his grin widening to reveal yellowed, irregular teeth. He doesn't move toward the money, but his posture shifts, his weight centering as he prepares to lunge. He gestures toward the ledger with a stubby finger, his gaze hungry and predatory. "Caron doesn't care about your coin, traveler, but we do. And seeing as you're so eager to throw money around, maybe we'll take the coins *and* whatever's in that book. Seems like a fair trade for the trouble you're causing us, doesn't it, Marcus?"

Marcus doesn't laugh. He simply steps wider, cutting off your line of sight to the inn door, his hands curling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the tension outside, your heart hammering a frantic rhythm against your bruised ribs, and duck into the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted mutton and spilled ale, a sharp contrast to the biting chill of the road. You find **Halden** seated at a corner table, his face partially obscured by the flickering candlelight, his eyes scanning the room with a restless, nervous energy.

You slide the heavy **leather-bound ledger** across the table, placing it firmly in front of him, and then push the merchant seal toward his waiting hands. He doesn't offer a word of thanks; instead, his fingers tremble slightly as he pulls the ledger toward his chest, his eyes darting toward the door you just entered through. He doesn't even look at you, his focus entirely consumed by the object, his hands hovering over the leather as if protecting it from an invisible thief.

"You're late, and you look like you've been through a meat grinder," Halden whispers, his voice barely audible over the tavern's din. He doesn't wait for an explanation, his gaze shifting toward the entrance, where the silhouette of the **Unnamed Bearded Man** and **Marcus** can be seen through the frosted glass of the door, lingering just outside. "I told you, Aren, the road has teeth. It seems they've followed you right to my doorstep."

He pulls a small, silver coin from his pocket—not the payment, but a token—and slides it toward you, his eyes wide and searching yours. "Take this and find a quiet corner, or better yet, find a way out of here before they decide they want more than just your coin. They aren't just looking for trouble; they're looking for *this*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: easy
Roll: 3 + 4 +1 (stat) +1 (diff) = 9 → PARTIAL
Directive: The escape results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (COMPLICATION, surface as event):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Halden** — last seen Crossed Keys Inn: standing near the town well examining a map
- **Marcus** — last seen Crossed Keys Inn
- **Unnamed Bearded Man** — last seen Merchant Road East
- **Caron** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Merchant Road East
## NPCs Present in Scene
- Halden (Merchant) — Nervously clutching the ledger and watching the door, warning Aren of approaching danger.
- Marcus (Thug) — Seen as a silhouette through the frosted glass, lingering outside the entrance.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on dexterity — The escape results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`crossed_keys_inn` | Crossed Keys Inn
A warm, dimly lit tavern smelling of roasted mutton and spilled ale, providing a sharp contrast to the cold road outside.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Nervously clutching the ledger and watching the door, warning Aren of approaching danger.
- `marcus` | Marcus (Thug) — Seen as a silhouette through the frosted glass, lingering outside the entrance.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
You scramble away from Halden, your breath coming in shallow, panicked hitches that send a sharp spike of pain through your bruised ribs. You lunge toward the heavy timber door, fumbling with the **Brass key** in your trembling hands. The metal feels cold and slick with sweat as you find the lock, your fingers working with a desperate, clumsy haste. You jam the key into the keyhole, twisting it with a frantic strength, and hear a satisfying, heavy *clack* as the mechanism yields.

The door swings open, not into a main hall, but into a narrow, dimly lit service corridor that smells of damp stone and old grease. You stumble into the darkness, your shoulder slamming hard against the doorframe, and slam it shut behind you, bolting it just as a heavy, rhythmic thudding begins against the wood from the other side. You've found a way out of the main room, but the sudden, violent impact makes the door rattle on its hinges, and you realize you've trapped yourself in a dead-end hallway.

As you turn to find an exit, your foot catches on a loose, heavy burlap sack resting near a stack of crates. You stumble, and as you reach out to steady yourself, your hand brushes against a small, leather pouch that has fallen open, spilling several dozen silver coins across the floor. Before you can gather them, a second door at the far end of the corridor creaks open, and a stout, middle-aged woman with grey-streaked hair and a stained apron, **Danielle**, steps out, holding a flickering tallow candle. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
location_change, inventory, recent_events, compendium_npc

## rules_outcome
PARTIAL on dexterity. The escape results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: dexterity
band: partial
directive: The escape results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×300 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | leather-bound ledger ×1 — Heavy, worn, smells of old parchment and wax.

## scene_result
location: `service_corridor`
(location changed)
## EXTRACT EXAMPLES (band: partial)

### Bandages used (2 rolls) — inventory_remove with amount
Thinking: - Player wrapped Halden's wound. Used 2 of the 3 bandage rolls.
- Inventory remove by id, amount=2; the engine subtracts from the stack.


JSON:
{
  "scene_tags": ["dialogue", "first_aid"],
  "scene_tagline": "Bandaged — one roll left",
  "present_npcs": [{"id": "halden", "notes": "Wincing but steady; pressing the wrap with one hand."}],
  "inventory_remove": [{"id": "bandages", "amount": 2}],
  "outcome_summary": "You wrapped Halden's gash. Two rolls used; one remains."
}


## CURRENT TURN NARRATION
You scramble away from Halden, your breath coming in shallow, panicked hitches that send a sharp spike of pain through your bruised ribs. You lunge toward the heavy timber door, fumbling with the **Brass key** in your trembling hands. The metal feels cold and slick with sweat as you find the lock, your fingers working with a desperate, clumsy haste. You jam the key into the keyhole, twisting it with a frantic strength, and hear a satisfying, heavy *clack* as the mechanism yields.

The door swings open, not into a main hall, but into a narrow, dimly lit service corridor that smells of damp stone and old grease. You stumble into the darkness, your shoulder slamming hard against the doorframe, and slam it shut behind you, bolting it just as a heavy, rhythmic thudding begins against the wood from the other side. You've found a way out of the main room, but the sudden, violent impact makes the door rattle on its hinges, and you realize you've trapped yourself in a dead-end hallway.

As you turn to find an exit, your foot catches on a loose, heavy burlap sack resting near a stack of crates. You stumble, and as you reach out to steady yourself, your hand brushes against a small, leather pouch that has fallen open, spilling several dozen silver coins across the floor. Before you can gather them, a second door at the far end of the corridor creaks open, and a stout, middle-aged woman with grey-streaked hair and a stained apron, **Danielle**, steps out, holding a flickering tallow candle. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
location_change, inventory, recent_events, compendium_npc

## rules_outcome
PARTIAL on dexterity.## pc
Aren Voss — Reluctant courier on the merchant road

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.
- Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.

## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `pursuers_at_door` [immediate] The Unnamed Bearded Man and Marcus are lingering outside the inn, seemingly tracking Aren and the ledger. (added turn 7)
_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
You scramble away from Halden, your breath coming in shallow, panicked hitches that send a sharp spike of pain through your bruised ribs. You lunge toward the heavy timber door, fumbling with the **Brass key** in your trembling hands. The metal feels cold and slick with sweat as you find the lock, your fingers working with a desperate, clumsy haste. You jam the key into the keyhole, twisting it with a frantic strength, and hear a satisfying, heavy *clack* as the mechanism yields.

The door swings open, not into a main hall, but into a narrow, dimly lit service corridor that smells of damp stone and old grease. You stumble into the darkness, your shoulder slamming hard against the doorframe, and slam it shut behind you, bolting it just as a heavy, rhythmic thudding begins against the wood from the other side. You've found a way out of the main room, but the sudden, violent impact makes the door rattle on its hinges, and you realize you've trapped yourself in a dead-end hallway.

As you turn to find an exit, your foot catches on a loose, heavy burlap sack resting near a stack of crates. You stumble, and as you reach out to steady yourself, your hand brushes against a small, leather pouch that has fallen open, spilling several dozen silver coins across the floor. Before you can gather them, a second door at the far end of the corridor creaks open, and a stout, middle-aged woman with grey-streaked hair and a stained apron, **Danielle**, steps out, holding a flickering tallow candle. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "escape",
  "intent": "The player attempts to use the brass key to unlock the inn's front door to find an alternative exit.",
  "rolled": true,
  "total_ms": 3376.2,
  "tokens_in": 1030,
  "tokens_out": 1151,
  "skill": "dexterity",
  "difficulty": "easy",
  "dice": [
    3,
    4
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "final_total": 9,
  "band": "partial",
  "outcome_summary": "You successfully escape the main room through a service door, but find yourself cornered in a dead-end hallway facing an alarmed staff member."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the brass key to unlock the inn's front door to find an alternative exit.",
  "intent_verb": "escape",
  "target": "inn's front door",
  "stakes": "If the key fails or the door is locked, the player may be trapped inside when the breach occurs.",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

You scramble away from Halden, your breath coming in shallow, panicked hitches that send a sharp spike of pain through your bruised ribs. You lunge toward the heavy timber door, fumbling with the **Brass key** in your trembling hands. The metal feels cold and slick with sweat as you find the lock, your fingers working with a desperate, clumsy haste. You jam the key into the keyhole, twisting it with a frantic strength, and hear a satisfying, heavy *clack* as the mechanism yields.

The door swings open, not into a main hall, but into a narrow, dimly lit service corridor that smells of damp stone and old grease. You stumble into the darkness, your shoulder slamming hard against the doorframe, and slam it shut behind you, bolting it just as a heavy, rhythmic thudding begins against the wood from the other side. You've found a way out of the main room, but the sudden, violent impact makes the door rattle on its hinges, and you realize you've trapped yourself in a dead-end hallway.

As you turn to find an exit, your foot catches on a loose, heavy burlap sack resting near a stack of crates. You stumble, and as you reach out to steady yourself, your hand brushes against a small, leather pouch that has fallen open, spilling several dozen silver coins across the floor. Before you can gather them, a second door at the far end of the corridor creaks open, and a stout, middle-aged woman with grey-streaked hair and a stained apron, **Danielle**, steps out, holding a flickering tallow candle. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.

### Extract Scene

```json
{
  "scene_tags": [
    "stealth",
    "exploration"
  ],
  "scene_tagline": "Trapped In The Service Corridor",
  "location_change": {
    "id": "service_corridor",
    "name": "Service Corridor",
    "description": "A narrow, dimly lit hallway smelling of damp stone and old grease, ending in a dead end."
  },
  "location_description": "The atmosphere is claustrophobic and tense, lit only by a flickering tallow candle as heavy thudding echoes from the main door.",
  "npc_add": [
    {
      "id": "danielle",
      "notes": "Stunned and alarmed by the sudden intrusion and the banging door.",
      "name": "Danielle",
      "title": "Inn Staff",
      "bio": "A stout, middle-aged woman with grey-streaked hair and a stained apron."
    }
  ],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "left behind in the main room of the inn"
    },
    {
      "id": "marcus",
      "last_seen_state": "lingering outside the main entrance"
    }
  ],
  "npc_update": [],
  "actions": [
    "Explain the situation to Danielle to seek her help",
    "Scramble to gather the spilled silver coins quickly",
    "Search the crates and hallway for a hidden exit",
    "Barricade the service door against the thudding from outside"
  ],
  "outcome_summary": "You successfully escape the main room through a service door, but find yourself cornered in a dead-end hallway facing an alarmed staff member."
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
      "id": "bruised_ribs",
      "label": "bruised ribs",
      "description": "Sharp pain in your ribs from a clumsy escape and slamming into a doorframe."
    }
  ],
  "pc_condition_remove": [],
  "failed": []
}
```

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "aren_escaped_main_room",
      "text": "Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [
    {
      "id": "innkeeper",
      "name": "Edda",
      "title": "Innkeeper",
      "bio": "Runs the Crossed Keys Inn alone; she is a stout, middle-aged woman with grey-streaked hair.",
      "aliases": [],
      "allegiance": null
    },
    {
      "id": "danielle",
      "name": "Danielle",
      "title": "Inn Staff",
      "bio": "A woman with grey-streaked hair and a stained apron who works in the service corridors of the inn.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [
    {
      "id": "trapped_in_corridor",
      "text": "The pursuers are thudding against the door of the service corridor, and Aren is currently in a dead-end hallway.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "instruction": "",
    "surface_as": "event"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "service_corridor",
    "name": "Service Corridor",
    "description": "A narrow, dimly lit hallway smelling of damp stone and old grease, ending in a dead end."
  },
  "location_description": "The atmosphere is claustrophobic and tense, lit only by a flickering tallow candle as heavy thudding echoes from the main door.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "stealth",
    "exploration"
  ],
  "scene_tagline": "Trapped In The Service Corridor",
  "compendium_npc_update": [
    {
      "id": "innkeeper",
      "name": "Edda",
      "title": "Innkeeper",
      "bio": "Runs the Crossed Keys Inn alone; she is a stout, middle-aged woman with grey-streaked hair.",
      "aliases": []
    },
    {
      "id": "danielle",
      "name": "Danielle",
      "title": "Inn Staff",
      "bio": "A woman with grey-streaked hair and a stained apron who works in the service corridors of the inn.",
      "aliases": []
    }
  ],
  "npc_add": [
    {
      "id": "danielle",
      "notes": "Stunned and alarmed by the sudden intrusion and the banging door.",
      "name": "Danielle",
      "title": "Inn Staff",
      "bio": "A stout, middle-aged woman with grey-streaked hair and a stained apron."
    }
  ],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "left behind in the main room of the inn"
    },
    {
      "id": "marcus",
      "last_seen_state": "lingering outside the main entrance"
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "aren_escaped_main_room",
      "text": "Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "trapped_in_corridor",
      "text": "The pursuers are thudding against the door of the service corridor, and Aren is currently in a dead-end hallway.",
      "urgency": "immediate",
      "turn_added": 0
    }
  ],
  "scene_pressure_remove": [
    "pursuers_at_door"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Explain the situation to Danielle to seek her help

- Scramble to gather the spilled silver coins quickly

- Search the crates and hallway for a hidden exit

- Barricade the service door against the thudding from outside

### Context Telemetry

- rules: est=1194t trimmed=False
- narrate: est=6331t trimmed=False
- extract.scene: est=2401t trimmed=False attempts=1
- extract.state: est=2650t trimmed=False attempts=1
- extract.progress: est=3664t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "danielle": {
        "from": null,
        "to": {
          "bio": "A woman with grey-streaked hair and a stained apron who works in the service corridors of the inn.",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "service_corridor",
            "location_name": "Service Corridor",
            "turn": 9
          },
          "name": "Danielle",
          "title": "Inn Staff"
        }
      },
      "halden": {
        "last_seen_state": {
          "from": "standing near the town well examining a map",
          "to": "left behind in the main room of the inn"
        }
      },
      "innkeeper": {
        "bio": {
          "from": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "to": "Runs the Crossed Keys Inn alone; she is a stout, middle-aged woman with grey-streaked hair."
        },
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "wiping down the bar at the Crossed Keys",
            "location_id": "service_corridor",
            "location_name": "Service Corridor",
            "turn": 9
          }
        },
        "title": {
          "from": "Innkeeper at the Crossed Keys",
          "to": "Innkeeper"
        }
      },
      "marcus": {
        "last_seen_state": {
          "from": null,
          "to": "lingering outside the main entrance"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A warm, dimly lit tavern smelling of roasted mutton and spilled ale, providing a sharp contrast to the cold road outside.",
      "to": "A narrow, dimly lit hallway smelling of damp stone and old grease, ending in a dead end."
    },
    "id": {
      "from": "crossed_keys_inn",
      "to": "service_corridor"
    },
    "name": {
      "from": "Crossed Keys Inn",
      "to": "Service Corridor"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "innkeeper",
        "danielle"
      ],
      "removed": []
    },
    "turn": {
      "from": 8,
      "to": 9
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 7,
      "to": 8
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A stout, middle-aged woman with grey-streaked hair and a stained apron.",
          "id": "danielle",
          "name": "Danielle",
          "notes": "Stunned and alarmed by the sudden intrusion and the banging door.",
          "title": "Inn Staff"
        }
      ],
      "removed": [
        {
          "bio": "A merchant who employs couriers to transport sensitive documents; currently wary of road dangers.",
          "id": "halden",
          "name": "Halden",
          "notes": "Nervously clutching the ledger and watching the door, warning Aren of approaching danger.",
          "title": "Merchant"
        },
        {
          "bio": "A wiry man with a nervous, twitching eye who flanks the bearded man at the inn entrance.",
          "id": "marcus",
          "name": "Marcus",
          "notes": "Seen as a silhouette through the frosted glass, lingering outside the entrance.",
          "title": "Thug"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "aren_escaped_main_room",
          "text": "Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.",
          "turn": 8
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "trapped_in_corridor",
          "max_turns": null,
          "text": "The pursuers are thudding against the door of the service corridor, and Aren is currently in a dead-end hallway.",
          "turn_added": 8,
          "urgency": "immediate"
        }
      ],
      "removed": [
        {
          "id": "pursuers_at_door",
          "max_turns": null,
          "text": "The Unnamed Bearded Man and Marcus are lingering outside the inn, seemingly tracking Aren and the ledger.",
          "turn_added": 7,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "The Ledger's Heavy Price",
      "to": "Trapped In The Service Corridor"
    },
    "tags": {
      "added": [
        "stealth",
        "exploration"
      ],
      "removed": [
        "dialogue"
      ]
    },
    "turn_entered": {
      "from": 7,
      "to": 8
    }
  }
}
```


---

# TURN 10

**Input:** `I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Service Corridor
## last_turn (tail of the most recent narrative)
T9: I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. — … e. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.

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
Conditions: bruised ribs, low morale

## Location
Service Corridor (service_corridor)
A narrow, dimly lit hallway smelling of damp stone and old grease, ending in a dead end.

## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [x] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] The pursuers are thudding against the door of the service corridor, and Aren is currently in a dead-end hallway.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.
- Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.
- Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor, and sit across from **Caron**. He doesn't offer a greeting, merely shifting his gaze from his half-empty mug to your face. His eyes are bloodshot, rimmed with the weariness of a man who has spent too many nights waiting for things that might never arrive.

"You're late, Aren," he says, his voice a low, gravelly rasp. You lay your terms on the table, attempting to negotiate a reduction in the interest or perhaps a structured payment plan that doesn't leave you starving on the road. You speak with a steady, measured tone, trying to project a reliability you don't entirely feel, and for a moment, it seems to work. He nods slowly, his weathered face softening just enough to signal agreement.

"Fine," Caron grunts, leaning forward until you can smell the sour ale on his breath. "We'll shave a portion off the total, provided you settle the principal by next moon. But I don't like waiting, and I don't like uncertainty." He reaches into his tunic and pulls out a small, notched wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt.

"This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck."

He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal.

"I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner.

"Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble."

He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax.


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district.

As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence.

A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt.


## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer.

The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face.

"We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out the heavy, stamped coins, letting them drop onto the grit and dirt between your boots and theirs. The metal clinks sharply, a lonely, hollow sound in the quiet evening air. "Caron's coin is paid," you state, your voice hard and final, attempting to dismiss them like common street urchins. "Take your fee and find somewhere else to loiter. I'm not interested in your games."

The **Unnamed Bearded Man** doesn't reach for the coins. Instead, he stares down at the pile, his eyes shifting from the gold to your face, and then to the heavy **leather-bound ledger** gripped under your arm. A slow, ugly chuckle rumbles in his chest, vibrating through the narrow space between you. He doesn't look like a man who has just been paid; he looks like a man who has just seen a much larger prize.

"Caron, is it?" he asks, his grin widening to reveal yellowed, irregular teeth. He doesn't move toward the money, but his posture shifts, his weight centering as he prepares to lunge. He gestures toward the ledger with a stubby finger, his gaze hungry and predatory. "Caron doesn't care about your coin, traveler, but we do. And seeing as you're so eager to throw money around, maybe we'll take the coins *and* whatever's in that book. Seems like a fair trade for the trouble you're causing us, doesn't it, Marcus?"

Marcus doesn't laugh. He simply steps wider, cutting off your line of sight to the inn door, his hands curling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the tension outside, your heart hammering a frantic rhythm against your bruised ribs, and duck into the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted mutton and spilled ale, a sharp contrast to the biting chill of the road. You find **Halden** seated at a corner table, his face partially obscured by the flickering candlelight, his eyes scanning the room with a restless, nervous energy.

You slide the heavy **leather-bound ledger** across the table, placing it firmly in front of him, and then push the merchant seal toward his waiting hands. He doesn't offer a word of thanks; instead, his fingers tremble slightly as he pulls the ledger toward his chest, his eyes darting toward the door you just entered through. He doesn't even look at you, his focus entirely consumed by the object, his hands hovering over the leather as if protecting it from an invisible thief.

"You're late, and you look like you've been through a meat grinder," Halden whispers, his voice barely audible over the tavern's din. He doesn't wait for an explanation, his gaze shifting toward the entrance, where the silhouette of the **Unnamed Bearded Man** and **Marcus** can be seen through the frosted glass of the door, lingering just outside. "I told you, Aren, the road has teeth. It seems they've followed you right to my doorstep."

He pulls a small, silver coin from his pocket—not the payment, but a token—and slides it toward you, his eyes wide and searching yours. "Take this and find a quiet corner, or better yet, find a way out of here before they decide they want more than just your coin. They aren't just looking for trouble; they're looking for *this*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You scramble away from Halden, your breath coming in shallow, panicked hitches that send a sharp spike of pain through your bruised ribs. You lunge toward the heavy timber door, fumbling with the **Brass key** in your trembling hands. The metal feels cold and slick with sweat as you find the lock, your fingers working with a desperate, clumsy haste. You jam the key into the keyhole, twisting it with a frantic strength, and hear a satisfying, heavy *clack* as the mechanism yields.

The door swings open, not into a main hall, but into a narrow, dimly lit service corridor that smells of damp stone and old grease. You stumble into the darkness, your shoulder slamming hard against the doorframe, and slam it shut behind you, bolting it just as a heavy, rhythmic thudding begins against the wood from the other side. You've found a way out of the main room, but the sudden, violent impact makes the door rattle on its hinges, and you realize you've trapped yourself in a dead-end hallway.

As you turn to find an exit, your foot catches on a loose, heavy burlap sack resting near a stack of crates. You stumble, and as you reach out to steady yourself, your hand brushes against a small, leather pouch that has fallen open, spilling several dozen silver coins across the floor. Before you can gather them, a second door at the far end of the corridor creaks open, and a stout, middle-aged woman with grey-streaked hair and a stained apron, **Danielle**, steps out, holding a flickering tallow candle. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 5 + 5 +1 (stat) = 11 → SUCCESS
Directive: The persuade succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (COMPLICATION, surface as event):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Danielle** — last seen Service Corridor
- **Edda** — last seen Service Corridor: wiping down the bar at the Crossed Keys
- **Halden** — last seen Crossed Keys Inn: standing near the town well examining a map
- **Marcus** — last seen Crossed Keys Inn
- **Unnamed Bearded Man** — last seen Merchant Road East
- **Caron** — last seen Marrow's Crossing
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Merchant Road East
## NPCs Present in Scene
- Danielle (Inn Staff) — Stunned and alarmed by the sudden intrusion and the banging door.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
SUCCESS on charisma — The persuade succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`service_corridor` | Service Corridor
A narrow, dimly lit hallway smelling of damp stone and old grease, ending in a dead end.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `danielle` | Danielle (Inn Staff) — Stunned and alarmed by the sudden intrusion and the banging door.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
You press your ear against the cold, damp stone, listening to the muffled, angry shouting and the heavy, rhythmic pounding of fists against the door you just bolted. The vibrations rattle your teeth, and the panic in your chest feels like a physical weight. Lowering your voice to a desperate, urgent whisper, you press your lips toward a crack in the masonry, shouting, "I have credits! Open up!"

When no one answers, and the banging only grows more violent, you reach into your pouch and pull out a single, lonely coin. You press it against the stone, sliding it into a narrow gap between the masonry and the doorframe, a pathetic, symbolic offering to whatever might be listening on the other side.

The banging doesn't stop, but the shouting on the other side of the door muffles slightly, replaced by a sudden, sharp hush. For a heartbeat, the only sound is your own ragged breathing and the flickering hiss of **Danielle's** tallow candle. The immediate, frantic violence of the door-beating settles into a heavy, expectant silence, as if the thugs outside are pausing, uncertain whether the person they are hunting has vanished into the guts of the building or is simply waiting for them to find a different way in.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
scene

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `trapped_in_corridor` [immediate] The pursuers are thudding against the door of the service corridor, and Aren is currently in a dead-end hallway. (added turn 8)
## CURRENT TURN NARRATION
You press your ear against the cold, damp stone, listening to the muffled, angry shouting and the heavy, rhythmic pounding of fists against the door you just bolted. The vibrations rattle your teeth, and the panic in your chest feels like a physical weight. Lowering your voice to a desperate, urgent whisper, you press your lips toward a crack in the masonry, shouting, "I have credits! Open up!"

When no one answers, and the banging only grows more violent, you reach into your pouch and pull out a single, lonely coin. You press it against the stone, sliding it into a narrow gap between the masonry and the doorframe, a pathetic, symbolic offering to whatever might be listening on the other side.

The banging doesn't stop, but the shouting on the other side of the door muffles slightly, replaced by a sudden, sharp hush. For a heartbeat, the only sound is your own ragged breathing and the flickering hiss of **Danielle's** tallow candle. The immediate, frantic violence of the door-beating settles into a heavy, expectant silence, as if the thugs outside are pausing, uncertain whether the person they are hunting has vanished into the guts of the building or is simply waiting for them to find a different way in.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe or persuade the person behind the door to open up using a single credit.",
  "rolled": true,
  "total_ms": 3234.8,
  "tokens_in": 1035,
  "tokens_out": 1158,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    5,
    5
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 11,
  "band": "success",
  "outcome_summary": "Your desperate shout and the offering of a coin cause the violent pounding to cease, replaced by an ominous silence."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe or persuade the person behind the door to open up using a single credit.",
  "intent_verb": "persuade",
  "target": "the person behind the inn door",
  "stakes": "The person may ignore the player, call for help, or refuse entry entirely, leaving the player stuck in the corridor.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You press your ear against the cold, damp stone, listening to the muffled, angry shouting and the heavy, rhythmic pounding of fists against the door you just bolted. The vibrations rattle your teeth, and the panic in your chest feels like a physical weight. Lowering your voice to a desperate, urgent whisper, you press your lips toward a crack in the masonry, shouting, "I have credits! Open up!"

When no one answers, and the banging only grows more violent, you reach into your pouch and pull out a single, lonely coin. You press it against the stone, sliding it into a narrow gap between the masonry and the doorframe, a pathetic, symbolic offering to whatever might be listening on the other side.

The banging doesn't stop, but the shouting on the other side of the door muffles slightly, replaced by a sudden, sharp hush. For a heartbeat, the only sound is your own ragged breathing and the flickering hiss of **Danielle's** tallow candle. The immediate, frantic violence of the door-beating settles into a heavy, expectant silence, as if the thugs outside are pausing, uncertain whether the person they are hunting has vanished into the guts of the building or is simply waiting for them to find a different way in.

### Extract Scene

```json
{
  "scene_tags": [
    "stealth",
    "dialogue"
  ],
  "scene_tagline": "A Desperate Bribe Offered",
  "location_change": null,
  "location_description": "The frantic violence of the banging settles into a heavy, expectant silence, leaving only the hiss of a candle.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "danielle",
      "notes": "Standing frozen and silent, watching you with wide, panicked eyes by the flickering candle.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "actions": [
    "Attempt to bribe the thugs through the crack with more credits",
    "Whisper a plea to Danielle to help you hide better",
    "Search the corridor for a secondary exit or hiding spot",
    "Press yourself harder against the shadows to avoid detection"
  ],
  "outcome_summary": "Your desperate shout and the offering of a coin cause the violent pounding to cease, replaced by an ominous silence."
}
```

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "trapped_in_corridor",
      "text": "The thugs have stopped pounding on the door and are now waiting in a heavy, expectant silence outside the service corridor.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "gm_beat": {
    "type": "revelation",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The frantic violence of the banging settles into a heavy, expectant silence, leaving only the hiss of a candle.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "stealth",
    "dialogue"
  ],
  "scene_tagline": "A Desperate Bribe Offered",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "danielle",
      "notes": "Standing frozen and silent, watching you with wide, panicked eyes by the flickering candle."
    }
  ],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "trapped_in_corridor",
      "text": "The thugs have stopped pounding on the door and are now waiting in a heavy, expectant silence outside the service corridor.",
      "urgency": "building",
      "turn_added": 0
    }
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Attempt to bribe the thugs through the crack with more credits

- Whisper a plea to Danielle to help you hide better

- Search the corridor for a secondary exit or hiding spot

- Press yourself harder against the shadows to avoid detection

### Context Telemetry

- rules: est=1198t trimmed=False
- narrate: est=6828t trimmed=False
- extract.scene: est=2238t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=3023t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "danielle": {
        "last_seen": {
          "turn": {
            "from": 9,
            "to": 10
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A narrow, dimly lit hallway smelling of damp stone and old grease, ending in a dead end.",
      "to": "The frantic violence of the banging settles into a heavy, expectant silence, leaving only the hiss of a candle."
    }
  },
  "meta": {
    "pending_gm_beat": {
      "surface_as": {
        "from": "event",
        "to": "npc_behavior"
      },
      "type": {
        "from": "complication",
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
      "from": -2,
      "to": -1
    }
  },
  "scene": {
    "present_npcs": {
      "changed": [
        {
          "from": {
            "bio": "A stout, middle-aged woman with grey-streaked hair and a stained apron.",
            "id": "danielle",
            "name": "Danielle",
            "notes": "Stunned and alarmed by the sudden intrusion and the banging door.",
            "title": "Inn Staff"
          },
          "to": {
            "bio": "A stout, middle-aged woman with grey-streaked hair and a stained apron.",
            "id": "danielle",
            "name": "Danielle",
            "notes": "Standing frozen and silent, watching you with wide, panicked eyes by the flickering candle.",
            "title": "Inn Staff"
          }
        }
      ]
    },
    "scene_pressure": {
      "changed": [
        {
          "from": {
            "id": "trapped_in_corridor",
            "max_turns": null,
            "text": "The pursuers are thudding against the door of the service corridor, and Aren is currently in a dead-end hallway.",
            "turn_added": 8,
            "urgency": "immediate"
          },
          "to": {
            "id": "trapped_in_corridor",
            "max_turns": null,
            "text": "The thugs have stopped pounding on the door and are now waiting in a heavy, expectant silence outside the service corridor.",
            "turn_added": 8,
            "urgency": "building"
          }
        }
      ]
    },
    "tagline": {
      "from": "Trapped In The Service Corridor",
      "to": "A Desperate Bribe Offered"
    },
    "tags": {
      "added": [
        "dialogue"
      ],
      "removed": [
        "exploration"
      ]
    }
  }
}
```


---

# TURN 11

**Input:** `I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.`

## User Prompts

### Rules User Prompt
```
## pc
Aren Voss | Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## scene
Location: Service Corridor
## last_turn (tail of the most recent narrative)
T10: I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall. — … on they are hunting has vanished into the guts of the building or is simply waiting for them to find a different way in.

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
Conditions: bruised ribs, low morale

## Location
Service Corridor (service_corridor)
The frantic violence of the banging settles into a heavy, expectant silence, leaving only the hiss of a candle.

## Inventory
- **Credits** ×300: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather-bound ledger**: Heavy, worn, smells of old parchment and wax.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Deliver Halden's Ledger** [active]
  - [x] Accept the courier contract from Halden.
  - [x] Carry the ledger to the merchant Halden at the Crossed Keys Inn.
  - [ ] Confirm the contract with Halden in person.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] The thugs have stopped pounding on the door and are now waiting in a heavy, expectant silence outside the service corridor.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Halden has hired the player to deliver his ledger to the Crossed Keys Inn.
- Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.
- Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.

## Prior History (summarized — treat as background, not current scene)
wooden token, sliding it across the table toward you. "Keep this. It's your proof of the new terms, but it also means I'll be looking for you more closely than before. If you miss a single payment, the deal is void, and the old rate applies, with interest added for my trouble." ## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. You push the stack of **Credits** across the scarred wood, the coins clinking softly as they slide toward him. Caron doesn't grab them immediately; instead, he stares at the pile, his eyes narrowing as he calculates the weight and the worth. He scoops the coins into a leather pouch, his movements quick and possessive, and pulls a small, stained ledger from his belt. "This doesn't clear the whole thing, Aren," Caron says, his voice sharpening. He doesn't open the book to find your name, but rather pulls a charcoal stub from his pocket. He scribbles a quick, jagged line through a previous entry, but his expression remains hard, devoid of any gratitude. "This covers the principal, sure, but it doesn't cover the trouble your tardiness has caused me. I've had three other runners pass through here looking for the coin you owed, and none of them had your luck." He snaps the ledger shut with a heavy thud, the sound echoing in the quiet tavern. He doesn't mark the debt as cleared, but rather notes a lingering balance for the 'trouble' he mentioned. He leans back, his gaze shifting past you toward the tavern door, his suspicion clearly unresolved. "You've got the principal, but you're still under my shadow until the next moon. Don't think this makes us even; it just makes you a debtor with a smaller, more frequent deadline." ## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. You push away from the table, leaving Caron to his sour ale and his ledger, and head out into the cooling evening air of Marrow's Crossing. The cobblestones are slick with river mist, and the distant, rhythmic thud of the mills provides a steady heartbeat to the town's closing hours. You find **Halden** near the stone well, his silhouette hunched over a map under the flickering light of a nearby street lantern. He doesn't look up as you approach, his fingers tracing a line on the parchment near a pressed wax seal. "I'm looking for a reliable hand, not a talker," Halden mutters, his eyes still glued to the map, though he acknowledges your presence with a dismissive wave. You state your price, holding your ground and offering to transport his ledger to the Crossed Keys Inn for 200 credits. He pauses, his gaze shifting from the map to your face, weighing your broad shoulders and your steady, unhurried manner. "Two hundred is steep for a short trot across town, courier," Halden says, his voice thin and brittle. He stands, folding the map with practiced precision, and tucks it into a leather satchel. He studies you for a heartbeat longer, his eyes scanning your travel-stained cloak and the heavy pack on your back. "But I've heard the roads are getting teeth, and I'd rather pay for a man who looks like he can handle a blade than a boy who'll drop my property at the first sign of trouble." He reaches into a small pouch at his belt and produces two heavy, stamped coins, placing them in your palm. "Two hundred, as agreed. But take care. That ledger is more than just paper and ink, and the Crossed Keys isn't as quiet as it looks tonight. There's talk of trouble near the inn, and I don't want my business caught in the middle of it." He hands you a heavy, leather-bound book, its surface worn and smelling of old parchment and wax. ## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. You turn away from the well, shifting the weight of your pack and the heavy **leather-bound ledger** against your hip. The cobblestones underfoot are damp, reflecting the amber light of the lanterns as you navigate the narrow, winding streets toward the east gate. The air grows cooler, carrying the scent of river silt and woodsmoke, and the distant, rhythmic thrum of the mills feels more pronounced as you move toward the edge of the commercial district. As you pass through the east gate, the town's dense timber-framed buildings give way to the open, darkening expanse of the merchant road. The silhouette of the *Crossed Keys Inn* looms ahead, its multi-story structure casting a long, jagged shadow across the path. Even from this distance, the atmosphere feels off; the usual evening bustle of travelers and carters is strangely muted, replaced by a tense, watchful silence. A group of three men stands near the inn's main entrance, their shapes backlit by the light spilling from the tavern windows. They aren't sitting, and they aren't talking; they are simply leaning against the stone walls, their eyes scanning the road, waiting for someone to pass. One of them, a man with a thick, unkempt beard, spits into the dirt as your silhouette breaks the line of the moonlight, his hand resting visibly on the hilt of a heavy, notched cleaver at his belt. ## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. You march toward the entrance, your boots crunching on the grit of the road, and come to a halt several paces from the group. You keep your hands away from your belt, but your posture remains stiff, refusing to grant them the satisfaction of seeing you intimidated. You demand to know why they are obstructing the entrance and what their business is with the inn, making it clear you aren't turning back until they give you a straight answer. The man with the unkempt beard, whom you recognize as the **Unnamed Bearded Man**, pushes himself off the stone wall with a slow, predatory grace. He doesn't draw his cleaver, but he doesn't move his hand away from it either. Beside him, a second man, **Marcus**, a wiry fellow with a nervous, twitching eye, steps forward to flank him. They exchange a quick, knowing glance, and a thin, mocking grin spreads across the bearded man's face. "We're just making sure the right kind of folk find their way inside, traveler," the bearded man says, his voice a low, grating rumble. He doesn't answer your question directly, instead stepping into your personal space, forcing you to either stand your ground or recoil. "And right now, you look like the kind of folk who might find themselves paying a 'convenience fee' just to avoid a little... friction at the door." He gestures vaguely toward the ledger tucked under your arm, his eyes gleaming with a sudden, sharp interest in your cargo. ## Turn 7 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. You reach into your pouch and pull out the heavy, stamped coins, letting them drop onto the grit and dirt between your boots and theirs. The metal clinks sharply, a lonely, hollow sound in the quiet evening air. "Caron's coin is paid," you state, your voice hard and final, attempting to dismiss them like common street urchins. "Take your fee and find somewhere else to loiter. I'm not interested in your games." The **Unnamed Bearded Man** doesn't reach for the coins. Instead, he stares down at the pile, his eyes shifting from the gold to your face, and then to the heavy **leather-bound ledger** gripped under your arm. A slow, ugly chuckle rumbles in his chest, vibrating through the narrow space between you. He doesn't look like a man who has just been paid; he looks like a man who has just seen a much larger prize. "Caron, is it?" he asks, his grin widening to reveal yellowed, irregular teeth. He doesn't move toward the money, but his posture shifts, his weight centering as he prepares to lunge. He gestures toward the ledger with a stubby finger, his gaze hungry and predatory. "Caron doesn't care about your coin, traveler, but we do. And seeing as you're so eager to throw money around, maybe we'll take the coins *and* whatever's in that book. Seems like a fair trade for the trouble you're causing us, doesn't it, Marcus?" Marcus doesn't laugh. He simply steps wider, cutting off your line of sight to the inn door, his hands curling into fists at his sides. The air between you thickens, the tension snapping tight like a bowstring ready to break.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the tension outside, your heart hammering a frantic rhythm against your bruised ribs, and duck into the warmth of the *Crossed Keys Inn*. The air inside is thick with the smell of roasted mutton and spilled ale, a sharp contrast to the biting chill of the road. You find **Halden** seated at a corner table, his face partially obscured by the flickering candlelight, his eyes scanning the room with a restless, nervous energy.

You slide the heavy **leather-bound ledger** across the table, placing it firmly in front of him, and then push the merchant seal toward his waiting hands. He doesn't offer a word of thanks; instead, his fingers tremble slightly as he pulls the ledger toward his chest, his eyes darting toward the door you just entered through. He doesn't even look at you, his focus entirely consumed by the object, his hands hovering over the leather as if protecting it from an invisible thief.

"You're late, and you look like you've been through a meat grinder," Halden whispers, his voice barely audible over the tavern's din. He doesn't wait for an explanation, his gaze shifting toward the entrance, where the silhouette of the **Unnamed Bearded Man** and **Marcus** can be seen through the frosted glass of the door, lingering just outside. "I told you, Aren, the road has teeth. It seems they've followed you right to my doorstep."

He pulls a small, silver coin from his pocket—not the payment, but a token—and slides it toward you, his eyes wide and searching yours. "Take this and find a quiet corner, or better yet, find a way out of here before they decide they want more than just your coin. They aren't just looking for trouble; they're looking for *this*." He taps the ledger, his knuckles white, and his gaze remains fixed on the door, waiting for the inevitable breach.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You scramble away from Halden, your breath coming in shallow, panicked hitches that send a sharp spike of pain through your bruised ribs. You lunge toward the heavy timber door, fumbling with the **Brass key** in your trembling hands. The metal feels cold and slick with sweat as you find the lock, your fingers working with a desperate, clumsy haste. You jam the key into the keyhole, twisting it with a frantic strength, and hear a satisfying, heavy *clack* as the mechanism yields.

The door swings open, not into a main hall, but into a narrow, dimly lit service corridor that smells of damp stone and old grease. You stumble into the darkness, your shoulder slamming hard against the doorframe, and slam it shut behind you, bolting it just as a heavy, rhythmic thudding begins against the wood from the other side. You've found a way out of the main room, but the sudden, violent impact makes the door rattle on its hinges, and you realize you've trapped yourself in a dead-end hallway.

As you turn to find an exit, your foot catches on a loose, heavy burlap sack resting near a stack of crates. You stumble, and as you reach out to steady yourself, your hand brushes against a small, leather pouch that has fallen open, spilling several dozen silver coins across the floor. Before you can gather them, a second door at the far end of the corridor creaks open, and a stout, middle-aged woman with grey-streaked hair and a stained apron, **Danielle**, steps out, holding a flickering tallow candle. She stares at you, her eyes widening in alarm at your disheveled appearance and the frantic banging at the main door.

**Turn 10** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
You press your ear against the cold, damp stone, listening to the muffled, angry shouting and the heavy, rhythmic pounding of fists against the door you just bolted. The vibrations rattle your teeth, and the panic in your chest feels like a physical weight. Lowering your voice to a desperate, urgent whisper, you press your lips toward a crack in the masonry, shouting, "I have credits! Open up!"

When no one answers, and the banging only grows more violent, you reach into your pouch and pull out a single, lonely coin. You press it against the stone, sliding it into a narrow gap between the masonry and the doorframe, a pathetic, symbolic offering to whatever might be listening on the other side.

The banging doesn't stop, but the shouting on the other side of the door muffles slightly, replaced by a sudden, sharp hush. For a heartbeat, the only sound is your own ragged breathing and the flickering hiss of **Danielle's** tallow candle. The immediate, frantic violence of the door-beating settles into a heavy, expectant silence, as if the thugs outside are pausing, uncertain whether the person they are hunting has vanished into the guts of the building or is simply waiting for them to find a different way in.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 6 + 3 +1 (stat) = 10 → SUCCESS
Directive: The intimidate succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (REVELATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Danielle** — last seen Service Corridor
- **Edda** — last seen Service Corridor: wiping down the bar at the Crossed Keys
- **Halden** — last seen Crossed Keys Inn: standing near the town well examining a map
- **Marcus** — last seen Crossed Keys Inn
- **Unnamed Bearded Man** — last seen Merchant Road East
- **Caron** — last seen Marrow's Crossing
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Merchant Road East
## NPCs Present in Scene
- Danielle (Inn Staff) — Standing frozen and silent, watching you with wide, panicked eyes by the flickering candle.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
SUCCESS on charisma — The intimidate succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`service_corridor` | Service Corridor
The frantic violence of the banging settles into a heavy, expectant silence, leaving only the hiss of a candle.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `danielle` | Danielle (Inn Staff) — Standing frozen and silent, watching you with wide, panicked eyes by the flickering candle.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN NARRATION
You lunge past **Danielle**, your boots skidding slightly on the spilled silver coins, and burst through the door back into the main tavern area. The air is thick with the smell of mutton and the low, nervous murmur of patrons, but your eyes find your target immediately. **Matthew Estrada** sits at a small, shadowed table near the center of the room, his back partially to the wall, his gaze cutting through the crowd with a precision that doesn't belong to a common traveler.

You cross the floor in several heavy strides, your hands trembling with adrenaline, and seize his wrist before he can react. His skin is callous and hard, and as you pull his arm toward you, his body doesn't flinch; he merely shifts his weight, his eyes locking onto yours with a chilling, professional stillness. "Who are you?" you demand, your voice cutting through the tavern's din, "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't struggle. He doesn't even pull his arm away. He simply stares at you, his expression unreadable, though his eyes narrow slightly, assessing your grip and your stance. He doesn't look like a man caught off guard; he looks like a man who was simply waiting for someone foolish enough to touch him. The surrounding patrons go quiet, their eyes darting between your gripped hand and his calm, steady face, waiting to see if the tension will snap into violence.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
scene

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `trapped_in_corridor` [building] The thugs have stopped pounding on the door and are now waiting in a heavy, expectant silence outside the service corridor. (added turn 8)
## CURRENT TURN NARRATION
You lunge past **Danielle**, your boots skidding slightly on the spilled silver coins, and burst through the door back into the main tavern area. The air is thick with the smell of mutton and the low, nervous murmur of patrons, but your eyes find your target immediately. **Matthew Estrada** sits at a small, shadowed table near the center of the room, his back partially to the wall, his gaze cutting through the crowd with a precision that doesn't belong to a common traveler.

You cross the floor in several heavy strides, your hands trembling with adrenaline, and seize his wrist before he can react. His skin is callous and hard, and as you pull his arm toward you, his body doesn't flinch; he merely shifts his weight, his eyes locking onto yours with a chilling, professional stillness. "Who are you?" you demand, your voice cutting through the tavern's din, "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't struggle. He doesn't even pull his arm away. He simply stares at you, his expression unreadable, though his eyes narrow slightly, assessing your grip and your stance. He doesn't look like a man caught off guard; he looks like a man who was simply waiting for someone foolish enough to touch him. The surrounding patrons go quiet, their eyes darting between your gripped hand and his calm, steady face, waiting to see if the tension will snap into violence.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "intimidate",
  "intent": "The player attempts to intimidate Matthew Estrada into revealing his true identity and motives.",
  "rolled": true,
  "total_ms": 2809.7,
  "tokens_in": 1036,
  "tokens_out": 1145,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    6,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": "You successfully confront Matthew Estrada, catching him off guard and drawing the attention of the entire tavern."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to intimidate Matthew Estrada into revealing his true identity and motives.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "stakes": "Matthew may react aggressively, call for help, or refuse to cooperate, potentially escalating the confrontation.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You lunge past **Danielle**, your boots skidding slightly on the spilled silver coins, and burst through the door back into the main tavern area. The air is thick with the smell of mutton and the low, nervous murmur of patrons, but your eyes find your target immediately. **Matthew Estrada** sits at a small, shadowed table near the center of the room, his back partially to the wall, his gaze cutting through the crowd with a precision that doesn't belong to a common traveler.

You cross the floor in several heavy strides, your hands trembling with adrenaline, and seize his wrist before he can react. His skin is callous and hard, and as you pull his arm toward you, his body doesn't flinch; he merely shifts his weight, his eyes locking onto yours with a chilling, professional stillness. "Who are you?" you demand, your voice cutting through the tavern's din, "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't struggle. He doesn't even pull his arm away. He simply stares at you, his expression unreadable, though his eyes narrow slightly, assessing your grip and your stance. He doesn't look like a man caught off guard; he looks like a man who was simply waiting for someone foolish enough to touch him. The surrounding patrons go quiet, their eyes darting between your gripped hand and his calm, steady face, waiting to see if the tension will snap into violence.

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Confrontation In The Tavern",
  "location_change": {
    "id": "main_tavern",
    "name": "Main Tavern",
    "description": "A crowded room thick with the smell of mutton and the nervous murmurs of patrons."
  },
  "location_description": "The atmosphere shifts from a low murmur to a heavy, expectant silence as patrons watch the confrontation.",
  "npc_add": [
    {
      "id": "matthew_estrada",
      "notes": "Sitting at a shadowed table, reacting to being grabbed with professional stillness.",
      "name": "Matthew Estrada",
      "title": "Mysterious Traveler",
      "bio": "A man with a soldier's gaze and a chillingly calm demeanor."
    }
  ],
  "npc_remove": [
    {
      "id": "danielle",
      "last_seen_state": "left behind in the service corridor"
    }
  ],
  "npc_update": [],
  "actions": [
    "Demand answers about his true identity and intentions",
    "Release his wrist and attempt to de-escalate the tension",
    "Scan the room for any of his potential accomplices",
    "Search the table for clues about his purpose here"
  ],
  "outcome_summary": "You successfully confront Matthew Estrada, catching him off guard and drawing the attention of the entire tavern."
}
```

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "compendium_npc_update": [
    {
      "id": "matthew_estrada",
      "name": "Matthew Estrada",
      "title": "Professional Observer",
      "bio": "A calm and professional man who observes the tavern with a soldier-like precision; he remains unruffled by sudden physical confrontation.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "trapped_in_corridor"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "instruction": "",
    "surface_as": "npc_behavior"
  }
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "main_tavern",
    "name": "Main Tavern",
    "description": "A crowded room thick with the smell of mutton and the nervous murmurs of patrons."
  },
  "location_description": "The atmosphere shifts from a low murmur to a heavy, expectant silence as patrons watch the confrontation.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Confrontation In The Tavern",
  "compendium_npc_update": [
    {
      "id": "matthew_estrada",
      "name": "Matthew Estrada",
      "title": "Professional Observer",
      "bio": "A calm and professional man who observes the tavern with a soldier-like precision; he remains unruffled by sudden physical confrontation.",
      "aliases": []
    }
  ],
  "npc_add": [
    {
      "id": "matthew_estrada",
      "notes": "Sitting at a shadowed table, reacting to being grabbed with professional stillness.",
      "name": "Matthew Estrada",
      "title": "Mysterious Traveler",
      "bio": "A man with a soldier's gaze and a chillingly calm demeanor."
    }
  ],
  "npc_remove": [
    {
      "id": "danielle",
      "last_seen_state": "left behind in the service corridor"
    }
  ],
  "npc_update": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "trapped_in_corridor",
    "trapped_in_corridor"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Demand answers about his true identity and intentions

- Release his wrist and attempt to de-escalate the tension

- Scan the room for any of his potential accomplices

- Search the table for clues about his purpose here

### Context Telemetry

- rules: est=1205t trimmed=False
- narrate: est=6897t trimmed=False
- extract.scene: est=2304t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=3078t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "bearded_man": {
        "bio": "A man with an unkempt beard and a predatory grace who demands 'convenience fees' from travelers at the inn entrance.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "merchant_road_east",
          "location_name": "Merchant Road East",
          "turn": 5
        },
        "last_seen_state": "lingering outside the inn door as a silhouette",
        "name": "Unnamed Bearded Man",
        "title": "Thug"
      },
      "caron": {
        "bio": "A weary, gravel-voiced man who manages debts and issues notched wooden tokens as proof of payment terms.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 2
        },
        "last_seen_state": "remained in the market area near the well",
        "name": "Caron",
        "title": "Creditor"
      },
      "danielle": {
        "bio": "A woman with grey-streaked hair and a stained apron who works in the service corridors of the inn.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "service_corridor",
          "location_name": "Service Corridor",
          "turn": 10
        },
        "last_seen_state": "left behind in the service corridor",
        "name": "Danielle",
        "title": "Inn Staff"
      },
      "halden": {
        "bio": "A nervous merchant at the Crossed Keys Inn who is being pursued by unknown individuals interested in his ledger.",
        "last_seen": {
          "last_seen_state": "standing near the town well examining a map",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
          "turn": 8
        },
        "last_seen_state": "left behind in the main room of the inn",
        "name": "Halden",
        "title": "Merchant"
      },
      "innkeeper": {
        "bio": "Runs the Crossed Keys Inn alone; she is a stout, middle-aged woman with grey-streaked hair.",
        "last_seen": {
          "last_seen_state": "wiping down the bar at the Crossed Keys",
          "location_id": "service_corridor",
          "location_name": "Service Corridor",
          "turn": 9
        },
        "last_seen_state": "wiping down the bar at the Crossed Keys",
        "name": "Edda",
        "title": "Innkeeper"
      },
      "marcus": {
        "bio": "A wiry man with a nervous, twitching eye who flanks the bearded man at the inn entrance.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
          "turn": 8
        },
        "last_seen_state": "lingering outside the main entrance",
        "name": "Marcus",
        "title": "Thug"
      },
      "matthew_estrada": {
        "bio": "A calm and professional man who observes the tavern with a soldier-like precision; he remains unruffled by sudden physical confrontation.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "main_tavern",
          "location_name": "Main Tavern",
          "turn": 11
        },
        "name": "Matthew Estrada",
        "title": "Professional Observer"
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
      },
      "unnamed_bearded_man": {
        "last_seen": {
          "last_seen_state": "",
          "location_id": "merchant_road_east",
          "location_name": "Merchant Road East",
          "turn": 6
        }
      }
    }
  },
  "inventory": [
    {
      "aliases": [],
      "amount": 300,
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
      "id": "ledger",
      "name": "leather-bound ledger",
      "notes": "Heavy, worn, smells of old parchment and wax."
    }
  ],
  "location": {
    "description": "A crowded room thick with the smell of mutton and the nervous murmurs of patrons.",
    "id": "main_tavern",
    "name": "Main Tavern"
  },
  "meta": {
    "compendium_touch_order": [
      "caron",
      "bearded_man",
      "marcus",
      "halden",
      "innkeeper",
      "danielle",
      "matthew_estrada"
    ],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "",
      "surface_as": "npc_behavior",
      "type": "revelation"
    },
    "prior_history": [],
    "setting_pack": "eval-pack",
    "turn": 11
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
      "last_advanced_turn": 2,
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
      ],
      "status": "active",
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
          "done": true,
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
    "location_entered_turn": 10,
    "present_npcs": [
      {
        "bio": "A man with a soldier's gaze and a chillingly calm demeanor.",
        "id": "matthew_estrada",
        "name": "Matthew Estrada",
        "notes": "Sitting at a shadowed table, reacting to being grabbed with professional stillness.",
        "title": "Mysterious Traveler"
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
      },
      {
        "id": "halden_contract_accepted",
        "text": "Halden has hired the player to deliver his ledger to the Crossed Keys Inn.",
        "turn": 3
      },
      {
        "id": "halden_warned_of_pursuit",
        "text": "Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.",
        "turn": 7
      },
      {
        "id": "aren_escaped_main_room",
        "text": "Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.",
        "turn": 8
      }
    ],
    "recently_left": [],
    "recently_left_turns": 0,
    "scene_pressure": [],
    "tagline": "A Confrontation In The Tavern",
    "tags": [
      "dialogue"
    ],
    "turn_entered": 10,
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
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Fine', 'Aren', 'Keep'] |
| 3 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Credits', 'Aren', 'Don'] |
| 4 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 4: ['Halden has hired the player to deliver his ledger to the Crossed Keys Inn.'] |
| 6 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Man', 'Unnamed Bearded', 'Beside'] |
| 8 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 8: ['Halden reveals that the pursuers are specifically targeting the ledger and warns Aren to flee.'] |
| 9 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 9: ['Aren fled the main room of the Crossed Keys Inn through a service corridor to evade the pursuers.'] |
| 9 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Before', 'Brass'] |
| 10 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['For', 'Lowering', 'Open'] |
| 11 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Who'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1104 | 2749 | 2350 | 0 | 2990 | 0 | 0 |
| 3 | 1184 | 3261 | 0 | 0 | 3279 | 0 | 0 |
| 4 | 1190 | 3714 | 0 | 2666 | 3448 | 0 | 0 |
| 5 | 1193 | 4274 | 2347 | 0 | 3190 | 0 | 0 |
| 6 | 1196 | 4664 | 0 | 0 | 3010 | 0 | 0 |
| 7 | 1197 | 5190 | 0 | 0 | 3120 | 0 | 0 |
| 8 | 1193 | 5661 | 2432 | 0 | 3407 | 0 | 0 |
| 9 | 1194 | 6331 | 2401 | 2650 | 3664 | 0 | 0 |
| 10 | 1198 | 6828 | 2238 | 0 | 3023 | 0 | 0 |
| 11 | 1205 | 6897 | 2304 | 0 | 3078 | 0 | 0 |
