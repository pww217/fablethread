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

## System Prompts (from turn 1 — identical every turn)

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
Roll: 2 + 3 +1 (stat) = 6 → FAIL
Directive: The negotiate fails. The attempt fails outright — what you tried to do does not happen.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





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
FAIL on charisma — The negotiate fails. The attempt fails outright — what you tried to do does not happen.## pc
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
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor. Caron doesn't offer a greeting. He merely shifts his weight, his eyes tracking the movement of your hands as you settle in. He looks older than when you last saw him, the deep creases around his mouth framed by a graying beard that seems unkempt in the dim light of the Crossed Keys. He takes a slow, deliberate sip of his dark ale, letting the silence stretch until it feels thick enough to choke on.

"You think a few polite words and a seat at my table makes the ledger any lighter?" Caron asks, his voice a low rasp. He sets the tankard down with a heavy thud, a small splash of ale slopping over the rim onto the scarred wood. He leans forward, bringing the scent of stale grain and old sweat into your personal space. "I don't care about your excuses or your 'readiness.' The coin isn't in my hand, and until it is, you're still in the red."

He gestures vaguely toward the door, dismissing the conversation before it has even truly begun. He isn't interested in a negotiation or a compromise; he is simply waiting for the physical reality of your payment. He turns his gaze away from you, looking toward the hearth, effectively cutting you out of his world.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
scene

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## CURRENT TURN NARRATION
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor. Caron doesn't offer a greeting. He merely shifts his weight, his eyes tracking the movement of your hands as you settle in. He looks older than when you last saw him, the deep creases around his mouth framed by a graying beard that seems unkempt in the dim light of the Crossed Keys. He takes a slow, deliberate sip of his dark ale, letting the silence stretch until it feels thick enough to choke on.

"You think a few polite words and a seat at my table makes the ledger any lighter?" Caron asks, his voice a low rasp. He sets the tankard down with a heavy thud, a small splash of ale slopping over the rim onto the scarred wood. He leans forward, bringing the scent of stale grain and old sweat into your personal space. "I don't care about your excuses or your 'readiness.' The coin isn't in my hand, and until it is, you're still in the red."

He gestures vaguely toward the door, dismissing the conversation before it has even truly begun. He isn't interested in a negotiation or a compromise; he is simply waiting for the physical reality of your payment. He turns his gaze away from you, looking toward the hearth, effectively cutting you out of his world.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player intends to initiate a conversation with Caron regarding the repayment of a debt.",
  "rolled": true,
  "total_ms": 9625.5,
  "tokens_in": 955,
  "tokens_out": 1062,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    2,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 6,
  "band": "fail",
  "outcome_summary": "Your attempt to negotiate fails as Caron refuses to listen to excuses, demanding only the physical coin you owe."
}
```

**Raw LLM output:**
```
{
  "intent": "The player intends to initiate a conversation with Caron regarding the repayment of a debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "The player's relationship with Caron and the terms of their debt repayment.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor. Caron doesn't offer a greeting. He merely shifts his weight, his eyes tracking the movement of your hands as you settle in. He looks older than when you last saw him, the deep creases around his mouth framed by a graying beard that seems unkempt in the dim light of the Crossed Keys. He takes a slow, deliberate sip of his dark ale, letting the silence stretch until it feels thick enough to choke on.

"You think a few polite words and a seat at my table makes the ledger any lighter?" Caron asks, his voice a low rasp. He sets the tankard down with a heavy thud, a small splash of ale slopping over the rim onto the scarred wood. He leans forward, bringing the scent of stale grain and old sweat into your personal space. "I don't care about your excuses or your 'readiness.' The coin isn't in my hand, and until it is, you're still in the red."

He gestures vaguely toward the door, dismissing the conversation before it has even truly begun. He isn't interested in a negotiation or a compromise; he is simply waiting for the physical reality of your payment. He turns his gaze away from you, looking toward the hearth, effectively cutting you out of his world.

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "Debt Remains Unpaid",
  "location_change": null,
  "location_description": "The dim light of the Crossed Keys feels oppressive as the silence between you and Caron thickens.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Dismissive and impatient, leaning forward with a scent of stale grain and sweat while demanding physical coin.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "actions": [
    "Offer a partial payment to appease Caron's immediate anger",
    "Demand more time to secure the remaining coin for him",
    "Ask Caron if he has any work to earn it",
    "Search the tavern for any loose coin or valuables"
  ],
  "outcome_summary": "Your attempt to negotiate fails as Caron refuses to listen to excuses, demanding only the physical coin you owe."
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
      "title": "Merchant/Creditor",
      "bio": "A stern creditor at the Crossed Keys who is strictly focused on collecting a debt from Aren Voss.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": null
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The dim light of the Crossed Keys feels oppressive as the silence between you and Caron thickens.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "Debt Remains Unpaid",
  "compendium_npc_update": [
    {
      "id": "caron",
      "name": "Caron",
      "title": "Merchant/Creditor",
      "bio": "A stern creditor at the Crossed Keys who is strictly focused on collecting a debt from Aren Voss.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Dismissive and impatient, leaning forward with a scent of stale grain and sweat while demanding physical coin."
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

- Offer a partial payment to appease Caron's immediate anger

- Demand more time to secure the remaining coin for him

- Ask Caron if he has any work to earn it

- Search the tavern for any loose coin or valuables

### Context Telemetry

- rules: est=1104t trimmed=False
- narrate: est=2745t trimmed=False
- extract.scene: est=2318t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=2961t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A stern creditor at the Crossed Keys who is strictly focused on collecting a debt from Aren Voss.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 2
        },
        "name": "Caron",
        "title": "Merchant/Creditor"
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
    "description": "The dim light of the Crossed Keys feels oppressive as the silence between you and Caron thickens.",
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
    "pending_gm_beat": null,
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
        "notes": "Dismissive and impatient, leaning forward with a scent of stale grain and sweat while demanding physical coin.",
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
    "tagline": "Debt Remains Unpaid",
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
T2: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — … y of your payment. He turns his gaze away from you, looking toward the hearth, effectively cutting you out of his world.

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
The dim light of the Crossed Keys feels oppressive as the silence between you and Caron thickens.

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

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor. Caron doesn't offer a greeting. He merely shifts his weight, his eyes tracking the movement of your hands as you settle in. He looks older than when you last saw him, the deep creases around his mouth framed by a graying beard that seems unkempt in the dim light of the Crossed Keys. He takes a slow, deliberate sip of his dark ale, letting the silence stretch until it feels thick enough to choke on.

"You think a few polite words and a seat at my table makes the ledger any lighter?" Caron asks, his voice a low rasp. He sets the tankard down with a heavy thud, a small splash of ale slopping over the rim onto the scarred wood. He leans forward, bringing the scent of stale grain and old sweat into your personal space. "I don't care about your excuses or your 'readiness.' The coin isn't in my hand, and until it is, you're still in the red."

He gestures vaguely toward the door, dismissing the conversation before it has even truly begun. He isn't interested in a negotiation or a compromise; he is simply waiting for the physical reality of your payment. He turns his gaze away from you, looking toward the hearth, effectively cutting you out of his world.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 5 + 3 +1 (stat) = 9 → PARTIAL
Directive: The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.

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
- Caron (Old creditor) — Dismissive and impatient, leaning forward with a scent of stale grain and sweat while demanding physical coin.
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
quest_updates, recent_events

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








## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## CURRENT TURN NARRATION
You push the stack of **Credits** across the scarred wood, the metal clinking softly against the table. Caron watches the coins slide toward him, his eyes narrowing as he calculates the pile. He reaches out with a thick, calloused hand and sweeps the coins into a small leather pouch at his belt without a word of thanks. He pulls a small, battered ledger from beneath the table and flips through the yellowed pages, his finger pausing on a line of ink before he makes a sharp, aggressive stroke through your name.

"There," Caron grunts, slamming the book shut. "The debt is officially dead. Don't come looking for grace if you fall behind again." He leans back, the tension in his shoulders relaxing slightly, but his eyes remain hard. He isn't relieved; he looks like a man who just completed a chore he intends to repeat.

As you begin to stand, a shadow falls over the table. A man wearing a boiled leather jerkin and a heavy iron-studded belt approaches. He has a thick, unruly mane of red hair and a jagged scar running through his left eyebrow. He doesn't look like a merchant or a local; he carries the restless energy of a man looking for trouble. He taps a heavy finger on the table near your hands, glancing between you and Caron. "That's a lot of coin for a man without a carriage, traveler," he says, his voice a thick, mocking drawl. "Seems a shame to keep it all tucked away in a pouch."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to convince Caron to officially clear their debt using a partial payment.",
  "rolled": true,
  "total_ms": 2702.4,
  "tokens_in": 1026,
  "tokens_out": 1131,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    5,
    3
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
  "intent": "The player attempts to convince Caron to officially clear their debt using a partial payment.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "The debt remains active, potentially leading to further collection attempts or hostility.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You push the stack of **Credits** across the scarred wood, the metal clinking softly against the table. Caron watches the coins slide toward him, his eyes narrowing as he calculates the pile. He reaches out with a thick, calloused hand and sweeps the coins into a small leather pouch at his belt without a word of thanks. He pulls a small, battered ledger from beneath the table and flips through the yellowed pages, his finger pausing on a line of ink before he makes a sharp, aggressive stroke through your name.

"There," Caron grunts, slamming the book shut. "The debt is officially dead. Don't come looking for grace if you fall behind again." He leans back, the tension in his shoulders relaxing slightly, but his eyes remain hard. He isn't relieved; he looks like a man who just completed a chore he intends to repeat.

As you begin to stand, a shadow falls over the table. A man wearing a boiled leather jerkin and a heavy iron-studded belt approaches. He has a thick, unruly mane of red hair and a jagged scar running through his left eyebrow. He doesn't look like a merchant or a local; he carries the restless energy of a man looking for trouble. He taps a heavy finger on the table near your hands, glancing between you and Caron. "That's a lot of coin for a man without a carriage, traveler," he says, his voice a thick, mocking drawl. "Seems a shame to keep it all tucked away in a pouch."

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
          "index": 1,
          "description": null,
          "done": true,
          "failed": null
        },
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
      "id": "caron_debt_cleared",
      "text": "Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.",
      "turn": 0
    },
    {
      "id": "red_haired_stranger_confrontation",
      "text": "A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [
    "You found Caron in the tavern \u2014 he's been waiting for you."
  ],
  "compendium_npc_update": [
    {
      "id": "caron",
      "name": "Caron",
      "title": null,
      "bio": "A hard-eyed man who collects debts; he has officially cleared Aren Voss's debt but remains unsympathetic.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [
    {
      "id": "stranger_confrontation",
      "text": "A suspicious red-haired man is aggressively questioning Aren Voss about his coin.",
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
  "quest_updates": [
    {
      "id": "settle_the_debt",
      "title": "",
      "status": "completed",
      "objectives": [
        {
          "index": 1,
          "done": true
        },
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
  "compendium_npc_update": [
    {
      "id": "caron",
      "name": "Caron",
      "bio": "A hard-eyed man who collects debts; he has officially cleared Aren Voss's debt but remains unsympathetic.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "caron_debt_cleared",
      "text": "Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.",
      "turn": 0
    },
    {
      "id": "red_haired_stranger_confrontation",
      "text": "A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [
    "You found Caron in the tavern \u2014 he's been waiting for you."
  ],
  "scene_pressure_add": [
    {
      "id": "stranger_confrontation",
      "text": "A suspicious red-haired man is aggressively questioning Aren Voss about his coin.",
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

- rules: est=1184t trimmed=False
- narrate: est=3139t trimmed=False
- extract.scene: skipped
- extract.state: skipped
- extract.progress: est=3315t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": {
          "from": "A stern creditor at the Crossed Keys who is strictly focused on collecting a debt from Aren Voss.",
          "to": "A hard-eyed man who collects debts; he has officially cleared Aren Voss's debt but remains unsympathetic."
        },
        "last_seen": {
          "turn": {
            "from": 2,
            "to": 3
          }
        }
      }
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "",
        "surface_as": "npc_behavior",
        "type": "complication"
      }
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
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "caron_debt_cleared",
          "text": "Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.",
          "turn": 2
        },
        {
          "id": "red_haired_stranger_confrontation",
          "text": "A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.",
          "turn": 2
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "stranger_confrontation",
          "max_turns": null,
          "text": "A suspicious red-haired man is aggressively questioning Aren Voss about his coin.",
          "turn_added": 2,
          "urgency": "immediate"
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
T3: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — … a carriage, traveler," he says, his voice a thick, mocking drawl. "Seems a shame to keep it all tucked away in a pouch."

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
The dim light of the Crossed Keys feels oppressive as the silence between you and Caron thickens.

## Inventory
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
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] A suspicious red-haired man is aggressively questioning Aren Voss about his coin.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.
- A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair, the legs scraping harshly against the tavern floor. Caron doesn't offer a greeting. He merely shifts his weight, his eyes tracking the movement of your hands as you settle in. He looks older than when you last saw him, the deep creases around his mouth framed by a graying beard that seems unkempt in the dim light of the Crossed Keys. He takes a slow, deliberate sip of his dark ale, letting the silence stretch until it feels thick enough to choke on.

"You think a few polite words and a seat at my table makes the ledger any lighter?" Caron asks, his voice a low rasp. He sets the tankard down with a heavy thud, a small splash of ale slopping over the rim onto the scarred wood. He leans forward, bringing the scent of stale grain and old sweat into your personal space. "I don't care about your excuses or your 'readiness.' The coin isn't in my hand, and until it is, you're still in the red."

He gestures vaguely toward the door, dismissing the conversation before it has even truly begun. He isn't interested in a negotiation or a compromise; he is simply waiting for the physical reality of your payment. He turns his gaze away from you, looking toward the hearth, effectively cutting you out of his world.

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You push the stack of **Credits** across the scarred wood, the metal clinking softly against the table. Caron watches the coins slide toward him, his eyes narrowing as he calculates the pile. He reaches out with a thick, calloused hand and sweeps the coins into a small leather pouch at his belt without a word of thanks. He pulls a small, battered ledger from beneath the table and flips through the yellowed pages, his finger pausing on a line of ink before he makes a sharp, aggressive stroke through your name.

"There," Caron grunts, slamming the book shut. "The debt is officially dead. Don't come looking for grace if you fall behind again." He leans back, the tension in his shoulders relaxing slightly, but his eyes remain hard. He isn't relieved; he looks like a man who just completed a chore he intends to repeat.

As you begin to stand, a shadow falls over the table. A man wearing a boiled leather jerkin and a heavy iron-studded belt approaches. He has a thick, unruly mane of red hair and a jagged scar running through his left eyebrow. He doesn't look like a merchant or a local; he carries the restless energy of a man looking for trouble. He taps a heavy finger on the table near your hands, glancing between you and Caron. "That's a lot of coin for a man without a carriage, traveler," he says, his voice a thick, mocking drawl. "Seems a shame to keep it all tucked away in a pouch."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: easy
Roll: 5 + 3 +1 (stat) +1 (diff) = 10 → SUCCESS
Directive: The negotiate succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (COMPLICATION, surface as npc_behavior):

This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Dismissive and impatient, leaning forward with a scent of stale grain and sweat while demanding physical coin.
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
inventory, quest_updates

## rules_outcome
SUCCESS on charisma. The negotiate succeeds cleanly. Clean success — you do what you intended.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: success
directive: The negotiate succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrows_crossing`

## EXTRACT EXAMPLES (band: success)

### Quest objective done by index
Thinking: - Player handed Halden the ledger; first objective of deliver_the_ledger is done.
- Use index=1 to mark it; engine resolves index → objective.


JSON:
{
  "scene_tags": ["dialogue", "delivery"],
  "scene_tagline": "Ledger handed over",
  "present_npcs": [{"id": "halden", "notes": "Takes the ledger with both hands; thumbs the wax seal."}],
  "quest_updates": [{"id": "deliver_the_ledger", "objectives": [{"index": 1, "done": true}]}],
  "outcome_summary": "Halden took the ledger and pressed the seal home with his thumb."
}


## CURRENT TURN NARRATION
You push away from the table, ignoring the red-haired man's predatory stare and Caron's dismissive silence. You step out of the dim, stifling air of the Crossed Keys and into the bracing light of Marrow's Crossing. The town is alive with the sounds of commerce and the distant rushing of the rivers, a sharp contrast to the tension you left behind.

You find **Halden** standing near the town well, his brow furrowed as he studies a map spread across a stone ledge. He looks up as you approach, squinting against the daylight. You speak clearly, laying out the terms: you will transport the ledger to the Crossed Keys and confirm the contract in person for a fee of 200 credits. He pauses, tapping a finger against the wax seal on his documents, weighing your reliability against the risk of the road.

"Two hundred? You're a bold one, Aren Voss," Halden says, a small, approving nod cutting through his skepticism. He reaches into a small pouch at his side and pulls out two heavy coin purses, handing one to you. "The ledger is non-negotiable. It stays secure, and it reaches the merchant at the inn without a single page torn or a drop of water on the ink. Do this, and the coin is yours." He hands you the heavy, leather-bound book, its weight a physical reminder of the task ahead.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
inventory, quest_updates

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

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






## scene_pressure (time-sensitive threats — add/remove/update as fiction demands)
- `stranger_confrontation` [immediate] A suspicious red-haired man is aggressively questioning Aren Voss about his coin. (added turn 2)
## items_gained
leather-bound ledger, coin purse

## CURRENT TURN NARRATION
You push away from the table, ignoring the red-haired man's predatory stare and Caron's dismissive silence. You step out of the dim, stifling air of the Crossed Keys and into the bracing light of Marrow's Crossing. The town is alive with the sounds of commerce and the distant rushing of the rivers, a sharp contrast to the tension you left behind.

You find **Halden** standing near the town well, his brow furrowed as he studies a map spread across a stone ledge. He looks up as you approach, squinting against the daylight. You speak clearly, laying out the terms: you will transport the ledger to the Crossed Keys and confirm the contract in person for a fee of 200 credits. He pauses, tapping a finger against the wax seal on his documents, weighing your reliability against the risk of the road.

"Two hundred? You're a bold one, Aren Voss," Halden says, a small, approving nod cutting through his skepticism. He reaches into a small pouch at his side and pulls out two heavy coin purses, handing one to you. "The ledger is non-negotiable. It stays secure, and it reaches the merchant at the inn without a single page torn or a drop of water on the ink. Do this, and the coin is yours." He hands you the heavy, leather-bound book, its weight a physical reminder of the task ahead.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to negotiate a delivery job with Halden for 200 credits.",
  "rolled": true,
  "total_ms": 2747.8,
  "tokens_in": 1038,
  "tokens_out": 1145,
  "skill": "charisma",
  "difficulty": "easy",
  "dice": [
    5,
    3
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": ""
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to negotiate a delivery job with Halden for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "The player fails to secure the job and loses the opportunity for extra credits.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

You push away from the table, ignoring the red-haired man's predatory stare and Caron's dismissive silence. You step out of the dim, stifling air of the Crossed Keys and into the bracing light of Marrow's Crossing. The town is alive with the sounds of commerce and the distant rushing of the rivers, a sharp contrast to the tension you left behind.

You find **Halden** standing near the town well, his brow furrowed as he studies a map spread across a stone ledge. He looks up as you approach, squinting against the daylight. You speak clearly, laying out the terms: you will transport the ledger to the Crossed Keys and confirm the contract in person for a fee of 200 credits. He pauses, tapping a finger against the wax seal on his documents, weighing your reliability against the risk of the road.

"Two hundred? You're a bold one, Aren Voss," Halden says, a small, approving nod cutting through his skepticism. He reaches into a small pouch at his side and pulls out two heavy coin purses, handing one to you. "The ledger is non-negotiable. It stays secure, and it reaches the merchant at the inn without a single page torn or a drop of water on the ink. Do this, and the coin is yours." He hands you the heavy, leather-bound book, its weight a physical reminder of the task ahead.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "leather_bound_ledger",
      "name": "leather-bound ledger",
      "notes": "A heavy book containing important merchant documents; must be kept secure.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "coin_purse",
      "name": "coin purse",
      "notes": "A heavy pouch containing 200 credits.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "credits",
      "name": null,
      "notes": null
    }
  ],
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
        },
        {
          "index": 2,
          "description": null,
          "done": true,
          "failed": null
        },
        {
          "index": 3,
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
  "compendium_npc_update": [
    {
      "id": "halden",
      "name": "Halden",
      "title": "Merchant",
      "bio": "A merchant at Marrow's Crossing who hires couriers to transport sensitive ledgers.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "stranger_confrontation"
  ],
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
      "id": "leather_bound_ledger",
      "name": "leather-bound ledger",
      "notes": "A heavy book containing important merchant documents; must be kept secure.",
      "amount": 1,
      "aliases": []
    },
    {
      "id": "coin_purse",
      "name": "coin purse",
      "notes": "A heavy pouch containing 200 credits.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "credits"
    }
  ],
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": true
        },
        {
          "index": 2,
          "done": true
        },
        {
          "index": 3,
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
      "bio": "A merchant at Marrow's Crossing who hires couriers to transport sensitive ledgers.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "stranger_confrontation"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

- rules: est=1190t trimmed=False
- narrate: est=3704t trimmed=False
- extract.scene: skipped
- extract.state: est=2495t trimmed=False attempts=1
- extract.progress: est=3219t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A hard-eyed man who collects debts; he has officially cleared Aren Voss's debt but remains unsympathetic.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 3
        },
        "name": "Caron",
        "title": "Merchant/Creditor"
      },
      "halden": {
        "bio": "A merchant at Marrow's Crossing who hires couriers to transport sensitive ledgers.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 4
        },
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
    },
    {
      "amount": 1,
      "id": "leather_bound_ledger",
      "name": "leather-bound ledger",
      "notes": "A heavy book containing important merchant documents; must be kept secure."
    },
    {
      "amount": 1,
      "id": "coin_purse",
      "name": "coin purse",
      "notes": "A heavy pouch containing 200 credits."
    }
  ],
  "location": {
    "description": "The dim light of the Crossed Keys feels oppressive as the silence between you and Caron thickens.",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "compendium_touch_order": [
      "caron",
      "halden"
    ],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "",
      "surface_as": "ambient",
      "type": "revelation"
    },
    "prior_history": [],
    "setting_pack": "eval-pack",
    "turn": 4
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
      "last_advanced_turn": 3,
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
          "done": true,
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
    "present_npcs": [
      {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "id": "caron",
        "name": "Caron",
        "notes": "Dismissive and impatient, leaning forward with a scent of stale grain and sweat while demanding physical coin.",
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
      },
      {
        "id": "caron_debt_cleared",
        "text": "Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.",
        "turn": 2
      },
      {
        "id": "red_haired_stranger_confrontation",
        "text": "A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.",
        "turn": 2
      }
    ],
    "scene_pressure": [],
    "tagline": "Debt Remains Unpaid",
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
# Deterministic Signals

## Auto-Checker Failures
| Turn | Assertion | Detail |
|---|---|---|
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed Keys'] |
| 3 | `universal.recent_events_add.turn_stamped` | 2 entries had turn=0/null instead of 3: ['Aren Voss successfully paid off the debt to Caron, and the ledger has been marked.', 'A red-haired man in boiled leather has approached Aren Voss, eyeing his coin with predatory intent.'] |
| 3 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Seems', 'Credits', 'Don'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1104 | 2745 | 2318 | 0 | 2961 | 0 | 0 |
| 3 | 1184 | 3139 | 0 | 0 | 3315 | 0 | 0 |
| 4 | 1190 | 3704 | 0 | 2495 | 3219 | 0 | 0 |
