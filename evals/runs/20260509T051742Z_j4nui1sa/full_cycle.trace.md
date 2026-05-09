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
**Bold** named inventory items on first use or direct reference in a scene. **Bold** NPC names on first introduction in a scene. This applies on the very first turn the same as all subsequent turns.

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
Extract scene state, NPC presence, location, compendium NPC updates, scene pressure, and the GM beat from a narration.
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
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": null
}
```

## Field rules

`scene_tags`: 1-3 lowercase tags from {dialogue, combat, exploration, market, travel, stealth, rest}. Always provide at least one. Include `"game_over"` ONLY if the player character (not an NPC) is confirmed dead this turn. When a scene involves armed/hostile NPCs or physical confrontation, prefer "combat" over "dialogue" even if the player is speaking.

`scene_tagline`: 3-6 word phase. Relevant to story or scene only, not mechanical. Upper case words. Examples: `"Dock Fees Due at Dawn"`, `"The Emperor's Assassin"`.

`location_change`: emit `{"id": "snake_case_id", "name": "Location Name", "description": "1-2 sentences"}` if the player physically moved or the situation has changed significantly. If player has moved away from NPCs, remove them from scene. Null if no change.

`location_description`: Only emit this field if the narration describes a meaningful environmental or atmospheric change to the current location — a shift in lighting, weather, crowd density, physical damage, or emotional register of the space. Do not re-describe unchanged surroundings. If the scene looks and feels the same as before, omit `description` entirely.

`npc_add`: new NPCs entering the scene this turn. Each: `{"id": "snake_case", "notes": "current situation", "name": "Full Name", "title": "Role", "bio": "1-3 sentences"}`. Only include name/title/bio for genuinely new NPCs not in the compendium. Omit name/title/bio for ambient/extra NPCs. If an NPC was previously unnamed (referred to by descriptor), check the compendium roster — if it's the same character, use `npc_update` instead of `npc_add`. **Compendium NPCs are NOT in the scene by default. Emit `npc_add` for any NPC mentioned in the narration that is NOT in `present_npcs`, even if they appear in the compendium roster.**

`npc_remove`: IDs of named NPCs who explicitly left the scene or are no longer in proximity. Each: `{"id": "existing_id", "last_seen_state": "1-sentence description of what they were last seen doing"}`. **Only remove NPCs when the narration clearly states or implies they left.** Do NOT remove NPCs just because the scene shifted focus, or because the player moved (allies follow). When in doubt, keep them.

`npc_update`: existing scene NPCs whose notes changed this turn. Each: `{"id": "existing_id", "notes": "updated situation"}`. Name/title/bio only change when new information arrives. Notes change every turn. If the narration mentions an NPC already in the scene, you MUST emit an `npc_update` for them.

## NPC ID format rules

NPC IDs must be `firstname_lastname` only. No titles, roles, or descriptors.
- ✅ `kael_marsh`, `torben_klask`
- ❌ `scarred_soldier`, `doctor_voss`, `the_merchant`
- If only one name is known: `kael` (single token, no decorators)
- When a full name is revealed later: emit `compendium_npc_update` to set the canonical ID and add old ID as alias

IDs are immutable once assigned. Name changes go in the `name` field and `aliases`, not the ID.

## NPC match instruction

Before emitting `compendium_npc_update` with a new id, run this checklist:
- Is the character's name (or any name they've been called) present in the known_characters list above? If yes — use the existing ID. Do NOT create a new entry.
- Does the character's description match an existing NPC's bio or role (same faction, same job, same physical descriptor)? If yes — use the existing ID with an alias update.
- Are they referred to by a descriptor used in a previous turn (e.g., "the scarred soldier", "the dockmaster's man")? If a compendium NPC has that descriptor in their bio or aliases — use the existing ID.
Only emit a new id if you have confirmed the character is not any existing compendium NPC by name, descriptor, or role.
When using an existing ID after a descriptor match: add the old descriptor as an alias in the update. This prevents future mismatches.

`compendium_npc_update`: NPC records to create or update based on genuinely new durable info (allegiance changed, died, new name learned, relationship revealed). Each: `{"id": "npc_id", "name": "optional", "title": "optional", "bio": "updated 1-3 sentence durable identity"}`. Don't re-emit NPCs whose info didn't change.

If the narration describes an NPC as killed, mortally wounded, captured, or permanently removed: emit `compendium_npc_update` with `bio` recording their fate. Do not omit this update — dead NPCs must be recorded.

`scene_pressure_add`: Add a `scene_pressure` entry when the narration introduces a time-sensitive threat, pursuit, hazard, or countdown. Set `urgency` based on immediacy: "immediate" if it must be addressed this turn, "building" if it escalates over 2-4 turns, "background" for ambient threat. Set `max_turns` to an explicit fiction-grounded expiry if the narration implies a hard deadline. Do NOT add lore or permanent world facts to `scene_pressure`. Each: `{"id": "snake_case_id", "text": "Threat description", "urgency": "immediate|building|background", "turn_added": 0, "max_turns": null}`.

`scene_pressure_remove`: IDs of pressures now resolved. Before emitting a removal, ask: did the narration show the underlying threat itself was eliminated? Examples of valid removal evidence: "the fire was extinguished", "the guards were evaded and the gates sealed behind you", "the bomb was defused". Examples of invalid removal evidence: "the player moved to a new location", "the player succeeded on a roll", "the threat is no longer mentioned". A location change alone NEVER justifies removing an immediate or building pressure — those can follow the player. A background pressure may be removed on location change only if the narration explicitly implies the source of the threat is in the now-left location.

`scene_pressure_update`: Changes to existing pressure text or urgency. Each: `{"id": "existing_pressure_id", "text": "updated text", "urgency": "immediate|building|background"}`.

## De-escalation

When `deescalate` is true in the user prompt: do NOT emit `scene_pressure_add`. Emit `scene_pressure_update` to downgrade urgency (`immediate → building`, `building → background`). If fully resolved, emit `scene_pressure_remove`. Pair with a `breathing_room` GM beat.

## NPC scene cap

No more than 8 named NPCs in a scene. If the narration introduces a 9th, the oldest/least relevant named NPC should be removed. Ambient NPCs don't count toward the cap. Allies, family, and key characters should be assumed to follow the player when they move. **NPC removal should only happen for: (1) the narration clearly shows the NPC left, or (2) the scene cap is exceeded. Never remove NPCs for any other reason.**

## GM Beat (gm_beat)

**IMPORTANT: `type` vs `surface_as` are different fields.**
- `type` is the beat category: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`.
- `surface_as` is how the beat is presented: `ambient`, `event`, or `npc_behavior`.
- **Do NOT set `type: "ambient"`.** `ambient` is a `surface_as` value only.

After extracting this turn's changes, decide whether to emit a forward-facing story beat for the NEXT turn.

Emit `null` if:
- There are 3+ active `scene_pressure` entries (don't pile on)
- `deescalate` is true (use `breathing_room` GM beat instead — see De-escalation)
- The player is in a critical resolution moment (final quest objective in reach)
- Nothing meaningful has changed in faction, NPC, or quest state to react to

Emit a beat when:
- `pc.momentum` >= +2: emit `complication` to raise stakes
- `pc.momentum` <= -2: emit `opportunity` or `breathing_room`
- A quest has been stalled (same objective for 3+ turns, shown as ⚠ in user prompt): emit `pressure` or `revelation`
- An NPC with unknown or shifting allegiance is present: emit `revelation`

Beat instruction rules:

    Before writing instruction, confirm you can name at least one specific entity from the current scene: an NPC by name, a faction, an object, or a named location. If you cannot, emit null for the entire beat.

    instruction: 1–2 sentences. Concrete and story-specific — name the entity. Minimum ~25 words. Must not be empty, must not be a generic category description.

    BAD (too short): "Something happens." "Guards arrive." "Tension rises."

    BAD (generic category): "Introduce a complication involving the guards." "Give the player an opportunity." "Add pressure to the scene."

    BAD (no entity): "A rival faction acts against the player's interests." ← no names, no scene anchor

    GOOD: "Marten Voss, the dockmaster's enforcer the player spoke with earlier, has quietly signaled two armed men near the exit — they are waiting for the player to leave."

    GOOD: "The satchel the fleeing guard dropped contains a partial map with a location marked in red ink — the same symbol the player saw on the warehouse door."

    GOOD: "Councilor Drae has just entered the far end of the hall. She has not seen the player yet, but one of the staff has noticed both of them."

`surface_as` guidance:
- `ambient`: low-stakes background texture. Used for `breathing_room` and most `revelation` beats.
- `event`: something the player can directly interact with. Used for `opportunity` and `pressure`.
- `npc_behavior`: a present NPC shifts their demeanor, loyalty signal, or body language. Best for `revelation` and `complication`.

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
  "pc_condition_remove": []
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

## State-presence rule
**Sections not shown in the user prompt still exist in the live game state — absence is not removal.** Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, ensure once more than you have no similar or matching items or item IDs.
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
  "outcome_summary": ""
}
```

## Field rules

`quest_updates`: changes to quest state this turn.
- Update existing: `{"id": "quest_id", "status": "active|completed|failed|abandoned", "objectives": [{"index": N, "done": true}]}`. `index` is 1-based from the active_quests list shown in the user prompt.
- New quest: `{"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objectives": [{"description": "first objective"}]}`. Use `description` only when adding a new objective.
- The engine auto-completes a quest when all objectives are done — do NOT emit `status: completed` for that case; just mark objectives done.
- New quest threshold guidance for this turn is in the user prompt.
- A quest is failed when the key objective(s) are failed, or are impossible to complete due to new information.
- A quest is abandoned when the player/narration implies they are giving up on it, gets too far away to continue, or it is no longer relevant.

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the quest, player, scene, and location, and not already known. Must be narratively significant: an obstacle, revelation, opportunity, relevant news that changes the player, location, or quest state substantially. Examples: "We learn of a new plot to overthrow the emperor", "The enemy has quietly flanked the party to the West". Each: `{"id": "snake_case_id", "text": "Event description", "turn": 0}`.

Each new event must have a stable `snake_case` ID. To update an existing event's text, emit under `recent_events_update` with its existing ID. To remove, emit ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded.

`recent_events_update`: facts whose content changed. Each: `{"id": "existing_event_id", "text": "replacement text"}`. Prefer updating over remove+add.

`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current quest state. Structure: two choices should offer distinct avenues related to the current quest (if any), one should involve an NPC who is present in the scene, and one should be an exploration/environmental or freeform option. Weight toward quest objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices.

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, NPCs, scene, and location. Ground this in the roll outcome (if any) and the player's intent. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

## Rules-outcome guidance (for objective resolution)
- crit_fail / fail / setback / partial: do NOT mark quest objectives done for the attempted action.
- success / crit_success: apply objective completions freely.
- No dice roll: do NOT complete quest objectives unless the narration explicitly and unambiguously states the objective is fulfilled. Ambiguous, partial, or conversational narration means the objective is NOT done.

## Contact and meet objective rule
If a quest objective's description contains any of: "find", "meet", "contact", "locate", "speak with", "reach", "talk to", "seek out" — the objective completes when ALL of:
- The named NPC or target is present in the current narration (they appear, respond, or speak).
- The player has established or attempted communication (spoken to them, signaled them, made contact).
- The narration does not explicitly show the contact failed or was refused.
This applies regardless of rules_outcome.band. Contact objectives are resolved by narrative presence, not roll outcome.

## State-presence rule
Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

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
Roll: 3 + 2 +1 (stat) = 6 → FAIL
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

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs

## CURRENT TURN NARRATION
You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."
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

## player_intent
negotiate: The player approaches Caron to discuss the repayment or terms of their debt.
## CURRENT TURN NARRATION
You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player approaches Caron to discuss the repayment or terms of their debt.",
  "rolled": true,
  "total_ms": 3768.0,
  "tokens_in": 1015,
  "tokens_out": 1117,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    3,
    2
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 6,
  "band": "fail",
  "outcome_summary": "Your attempt to negotiate fails as Caron coldly rejects your manners, demanding labor instead of coin due to your late payment."
}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss the repayment or terms of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "The terms of the debt and potential repercussions for non-payment.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Debt Has Grown Teeth",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "caron_collection_demand",
      "text": "Caron is demanding immediate payment of the debt or your labor.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "As Caron taps the tally stick, a heavy-set man in a stained leather jerkin\u2014one of the local enforcers Caron is known to employ\u2014steps into the tavern doorway and begins scanning the room, his eyes lingering on Aren Voss."
  }
}
```

### Extract State

*(skipped — domain not active this turn)*

### Extract Progress

```json
{
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "caron_debt_demand",
      "text": "Caron refuses to negotiate and demands labor in lieu of coin.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Offer to perform a dangerous courier task for Caron.'}",
    "{'description': 'Try to plead for more time to gather the coin.'}",
    "{'description': 'Demand to see the tally stick and the exact debt amount.'}",
    "{'description': 'Quietly leave the tavern to find a way to earn money.'}"
  ],
  "outcome_summary": "Your attempt to negotiate fails as Caron coldly rejects your manners, demanding labor instead of coin due to your late payment."
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
  "scene_tagline": "The Debt Has Grown Teeth",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor."
    }
  ],
  "recent_events_add": [
    {
      "id": "caron_debt_demand",
      "text": "Caron refuses to negotiate and demands labor in lieu of coin.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "caron_collection_demand",
      "text": "Caron is demanding immediate payment of the debt or your labor.",
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

- {'description': 'Offer to perform a dangerous courier task for Caron.'}

- {'description': 'Try to plead for more time to gather the coin.'}

- {'description': 'Demand to see the tally stick and the exact debt amount.'}

- {'description': 'Quietly leave the tavern to find a way to earn money.'}

### Context Telemetry

- rules: est=1187t trimmed=False
- narrate: est=2787t trimmed=False
- extract.scene: est=3705t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=1737t trimmed=False attempts=1

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
          "turn": 2
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
    "description": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "compendium_touch_order": [],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "As Caron taps the tally stick, a heavy-set man in a stained leather jerkin\u2014one of the local enforcers Caron is known to employ\u2014steps into the tavern doorway and begins scanning the room, his eyes lingering on Aren Voss.",
      "surface_as": "npc_behavior",
      "type": "complication"
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
        "notes": "Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor.",
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
        "id": "caron_debt_demand",
        "text": "Caron refuses to negotiate and demands labor in lieu of coin.",
        "turn": 1
      }
    ],
    "scene_pressure": [
      {
        "id": "caron_collection_demand",
        "max_turns": null,
        "text": "Caron is demanding immediate payment of the debt or your labor.",
        "turn_added": 1,
        "urgency": "building"
      }
    ],
    "tagline": "The Debt Has Grown Teeth",
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
T2: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — … coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."

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
- [BUILDING] Caron is demanding immediate payment of the debt or your labor.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As Caron taps the tally stick, a heavy-set man in a stained leather jerkin—one of the local enforcers Caron is known to employ—steps into the tavern doorway and begins scanning the room, his eyes lingering on Aren Voss.
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
- Caron (Old creditor) — Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor.
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
```
## active_domains
recent_events, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrows_crossing`

## CURRENT TURN NARRATION
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
recent_events, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player pays a stated amount to settle their debt with Caron.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.

## items_lost
credits

## CURRENT TURN NARRATION
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player pays a stated amount to settle their debt with Caron.",
  "rolled": false,
  "total_ms": 2347.6,
  "tokens_in": 1093,
  "tokens_out": 1177
}
```

**Raw LLM output:**
```
{
  "intent": "The player pays a stated amount to settle their debt with Caron.",
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

You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 500
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
      "id": "tyler_appears",
      "text": "Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.",
      "turn": 0
    }
  ],
  "recent_events_update": [
    {
      "id": "caron_refuses_negotiation",
      "text": "Caron considers your offer of five hundred credits to settle the debt."
    }
  ],
  "recent_events_remove": [
    "caron_refuses_negotiation"
  ],
  "actions": [
    "{'description': 'Push the credits closer and demand Caron sign the ledger.'}",
    "{'description': 'Quickly pocket the credits and prepare to leave the inn.'}",
    "{'description': 'Address Tyler directly to see if he is with Caron.'}",
    "{'description': 'Scan the tavern for a quick exit or a distraction.'}"
  ],
  "outcome_summary": "You offer Caron five hundred credits to settle your debt, but his attention is diverted by the sudden arrival of the menacing Tyler."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 500
    }
  ],
  "inventory_update": [],
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [],
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "tyler_appears",
      "text": "Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.",
      "turn": 0
    }
  ],
  "recent_events_update": [
    {
      "id": "caron_refuses_negotiation",
      "text": "Caron considers your offer of five hundred credits to settle the debt."
    }
  ],
  "recent_events_remove": [
    "caron_refuses_negotiation"
  ],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'description': 'Push the credits closer and demand Caron sign the ledger.'}

- {'description': 'Quickly pocket the credits and prepare to leave the inn.'}

- {'description': 'Address Tyler directly to see if he is with Caron.'}

- {'description': 'Scan the tavern for a quick exit or a distraction.'}

### Context Telemetry

- rules: est=1266t trimmed=False
- narrate: est=3301t trimmed=False
- extract.scene: skipped
- extract.state: est=2182t trimmed=False attempts=1
- extract.progress: est=1934t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "removed": [
      {
        "aliases": [],
        "amount": 500,
        "id": "credits",
        "name": "Credits",
        "notes": "Common coin, accepted at any inn or stall on the merchant road."
      }
    ]
  },
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As Caron taps the tally stick, a heavy-set man in a stained leather jerkin\u2014one of the local enforcers Caron is known to employ\u2014steps into the tavern doorway and begins scanning the room, his eyes lingering on Aren Voss.",
        "surface_as": "npc_behavior",
        "type": "complication"
      },
      "to": null
    },
    "turn": {
      "from": 2,
      "to": 3
    }
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "tyler_appears",
          "text": "Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.",
          "turn": 2
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
T3: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — … e. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

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
- [BUILDING] Caron is demanding immediate payment of the debt or your labor.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

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
- Caron (Old creditor) — Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
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
- `caron` | Caron (Old creditor) — Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `caron_collection_demand` [building] Caron is demanding immediate payment of the debt or your labor. (added turn 1)


## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T3 context)
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

## CURRENT TURN NARRATION
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
location_change, inventory, quest_updates

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `town_square`
(location changed)
## CURRENT TURN NARRATION
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
location_change, inventory, quest_updates

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.
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

## prior_turn_narration (T2 — for outcome_summary and actions context)
You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."

## items_gained
Credits, Ledger

## CURRENT TURN NARRATION
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "rolled": false,
  "total_ms": 2757.9,
  "tokens_in": 1095,
  "tokens_out": 1204
}
```

**Raw LLM output:**
```
{
  "intent": "Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "Halden may refuse the deal, leaving the player without the extra credits.",
  "check": {
    "required": false,
    "skill": "charisma",
    "difficulty": "trivial",
    "tags": []
  }
}
```

### Narration

You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue",
    "exploration"
  ],
  "scene_tagline": "A Fair Price For Danger",
  "location_change": {
    "id": "town_square",
    "name": "Town Square",
    "description": "The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light."
  },
  "location_description": "The evening air is cooling and the town square has grown quiet as shops close for the night.",
  "npc_add": [
    {
      "id": "tyler",
      "notes": "Looming in the doorway of the Crossed Keys, watching the coin on the table.",
      "name": "Tyler",
      "title": "Enforcer",
      "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip."
    }
  ],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Sitting at a table in the Crossed Keys Inn, staring at a bag of coin with a predatory grin."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "caron_collection_demand"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "As Voss departs the square with the ledger, Tyler emerges from the Crossed Keys Inn and begins following at a distance, keeping a watchful eye on the courier's movements."
  }
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Payment from Halden for the ledger delivery.",
      "amount": 200,
      "aliases": []
    },
    {
      "id": "ledger",
      "name": "Ledger",
      "notes": "A merchant's ledger provided by Halden for delivery.",
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
        },
        {
          "index": 2,
          "description": null,
          "done": false,
          "failed": null
        },
        {
          "index": 3,
          "description": null,
          "done": false,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "contract_accepted_halden",
      "text": "Halden has hired Voss to deliver the ledger for 200 credits.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Head back to the Crossed Keys Inn to deliver the ledger.'}",
    "{'description': 'Search the town square for more information about the restless roads.'}",
    "{'description': 'Ask Halden if he knows anything about the road toughs.'}",
    "{'description': 'Keep a close eye on the shadows for any potential ambushes.'}"
  ],
  "outcome_summary": "You successfully negotiated a contract with Halden, securing 200 credits to deliver the ledger to the Crossed Keys Inn."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Payment from Halden for the ledger delivery.",
      "amount": 200,
      "aliases": []
    },
    {
      "id": "ledger",
      "name": "Ledger",
      "notes": "A merchant's ledger provided by Halden for delivery.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "town_square",
    "name": "Town Square",
    "description": "The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light."
  },
  "location_description": "The evening air is cooling and the town square has grown quiet as shops close for the night.",
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
          "done": false
        },
        {
          "index": 3,
          "done": false
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue",
    "exploration"
  ],
  "scene_tagline": "A Fair Price For Danger",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "tyler",
      "notes": "Looming in the doorway of the Crossed Keys, watching the coin on the table.",
      "name": "Tyler",
      "title": "Enforcer",
      "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip."
    }
  ],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Sitting at a table in the Crossed Keys Inn, staring at a bag of coin with a predatory grin."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger."
    }
  ],
  "recent_events_add": [
    {
      "id": "contract_accepted_halden",
      "text": "Halden has hired Voss to deliver the ledger for 200 credits.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "caron_collection_demand"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'description': 'Head back to the Crossed Keys Inn to deliver the ledger.'}

- {'description': 'Search the town square for more information about the restless roads.'}

- {'description': 'Ask Halden if he knows anything about the road toughs.'}

- {'description': 'Keep a close eye on the shadows for any potential ambushes.'}

### Context Telemetry

- rules: est=1273t trimmed=False
- narrate: est=3598t trimmed=False
- extract.scene: est=4213t trimmed=False attempts=1
- extract.state: est=2213t trimmed=False attempts=1
- extract.progress: est=2482t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "last_seen_state": {
          "from": null,
          "to": "Sitting at a table in the Crossed Keys Inn, staring at a bag of coin with a predatory grin."
        }
      },
      "halden": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "town_square",
            "location_name": "Town Square",
            "turn": 4
          }
        }
      },
      "tyler": {
        "from": null,
        "to": {
          "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "town_square",
            "location_name": "Town Square",
            "turn": 4
          },
          "name": "Tyler",
          "title": "Enforcer"
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 200,
        "id": "credits",
        "name": "Credits",
        "notes": "Payment from Halden for the ledger delivery."
      },
      {
        "amount": 1,
        "id": "ledger",
        "name": "Ledger",
        "notes": "A merchant's ledger provided by Halden for delivery."
      }
    ]
  },
  "location": {
    "description": {
      "from": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
      "to": "The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light."
    },
    "id": {
      "from": "marrows_crossing",
      "to": "town_square"
    },
    "name": {
      "from": "Marrow's Crossing",
      "to": "Town Square"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "tyler"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As Voss departs the square with the ledger, Tyler emerges from the Crossed Keys Inn and begins following at a distance, keeping a watchful eye on the courier's movements.",
        "surface_as": "npc_behavior",
        "type": "complication"
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
    "location_entered_turn": {
      "from": null,
      "to": 3
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
          "id": "tyler",
          "name": "Tyler",
          "notes": "Looming in the doorway of the Crossed Keys, watching the coin on the table.",
          "title": "Enforcer"
        }
      ],
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Hostile and unyielding; tapping a notched tally stick rhythmically on the table while demanding payment or labor.",
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
            "notes": "Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger.",
            "title": "Merchant"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "contract_accepted_halden",
          "text": "Halden has hired Voss to deliver the ledger for 200 credits.",
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
    "scene_pressure": {
      "removed": [
        {
          "id": "caron_collection_demand",
          "max_turns": null,
          "text": "Caron is demanding immediate payment of the debt or your labor.",
          "turn_added": 1,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "The Debt Has Grown Teeth",
      "to": "A Fair Price For Danger"
    },
    "tags": {
      "added": [
        "exploration"
      ],
      "removed": []
    },
    "turn_entered": {
      "from": null,
      "to": 3
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
Location: Town Square
## last_turn (tail of the most recent narrative)
T4: I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. — …  man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."

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
Town Square (town_square)
The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light.

## Inventory
- **Credits** ×200: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A merchant's ledger provided by Halden for delivery.

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
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As Voss departs the square with the ledger, Tyler emerges from the Crossed Keys Inn and begins following at a distance, keeping a watchful eye on the courier's movements.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Tyler** — last seen Town Square
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger.
- Tyler (Enforcer) — Looming in the doorway of the Crossed Keys, watching the coin on the table.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
recent_events, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A merchant's ledger provided by Halden for delivery.

## scene_result
location: `town_square`

## CURRENT TURN NARRATION
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
recent_events, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
travel: The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.

## prior_turn_narration (T3 — for outcome_summary and actions context)
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

## items_gained
Credits

## CURRENT TURN NARRATION
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "travel",
  "intent": "The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.",
  "rolled": false,
  "total_ms": 2434.6,
  "tokens_in": 1090,
  "tokens_out": 1175
}
```

**Raw LLM output:**
```
{
  "intent": "The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.",
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

You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "",
      "amount": 200,
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
      "id": "deliver_ledger",
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
      "id": "tyler_stalking_voss",
      "text": "Tyler has begun following Voss from a distance, lurking in the roadside ditches.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Quickly double back to confront Tyler before he gets closer.'}",
    "{'description': 'Pick up your pace to reach the inn more quickly.'}",
    "{'description': 'Search the roadside ditches for any sign of his presence.'}",
    "{'description': 'Try to signal Caron for help from a distance.'}"
  ],
  "outcome_summary": "You secure the ledger and begin your trek toward the inn, unaware that Tyler is stalking you from the shadows."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "",
      "amount": 200,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "quest_updates": [
    {
      "id": "deliver_ledger",
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
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "tyler_stalking_voss",
      "text": "Tyler has begun following Voss from a distance, lurking in the roadside ditches.",
      "turn": 4
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

- {'description': 'Quickly double back to confront Tyler before he gets closer.'}

- {'description': 'Pick up your pace to reach the inn more quickly.'}

- {'description': 'Search the roadside ditches for any sign of his presence.'}

- {'description': 'Try to signal Caron for help from a distance.'}

### Context Telemetry

- rules: est=1274t trimmed=False
- narrate: est=4104t trimmed=False
- extract.scene: skipped
- extract.state: est=2181t trimmed=False attempts=1
- extract.progress: est=2355t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "changed": [
      {
        "from": {
          "amount": 200,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        },
        "to": {
          "amount": 400,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        }
      }
    ]
  },
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As Voss departs the square with the ledger, Tyler emerges from the Crossed Keys Inn and begins following at a distance, keeping a watchful eye on the courier's movements.",
        "surface_as": "npc_behavior",
        "type": "complication"
      },
      "to": null
    },
    "turn": {
      "from": 4,
      "to": 5
    }
  },
  "quests": {
    "added": [
      {
        "id": "deliver_ledger",
        "last_advanced_turn": 4,
        "objectives": [],
        "status": "active",
        "title": ""
      }
    ]
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "tyler_stalking_voss",
          "text": "Tyler has begun following Voss from a distance, lurking in the roadside ditches.",
          "turn": 4
        }
      ]
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
Location: Town Square
## last_turn (tail of the most recent narrative)
T5: I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. — … distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

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
Town Square (town_square)
The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light.

## Inventory
- **Credits** ×400: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A merchant's ledger provided by Halden for delivery.

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
- **** [active]

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.
- Tyler has begun following Voss from a distance, lurking in the roadside ditches.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 4 + 2 +1 (stat) = 7 → SETBACK
Directive: The persuade results in a setback. They're listening, but now they want something in return.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

## Narration Directive







## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Tyler** — last seen Town Square
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger.
- Tyler (Enforcer) — Looming in the doorway of the Crossed Keys, watching the coin on the table.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
SETBACK on charisma — The persuade results in a setback. They're listening, but now they want something in return.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`town_square` | Town Square
The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger.
- `tyler` | Tyler (Enforcer) — Looming in the doorway of the Crossed Keys, watching the coin on the table.

_(immutable section omitted — see Static Context > Seed State)_

⚠ Quest "Deliver Halden's Ledger" stalled for 3 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_ledger` | 



## previous_turn_narration (T5 context)
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

## CURRENT TURN NARRATION
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
scene, inventory

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

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×400 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A merchant's ledger provided by Halden for delivery.

## scene_result
location: `crossed_keys_inn_entrance`
(location changed)
## CURRENT TURN NARRATION
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
scene, inventory

## rules_outcome
SETBACK on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: Confront the two toughs at the inn door to demand an explanation for their presence.
## prior_turn_narration (T4 — for outcome_summary and actions context)
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."

## CURRENT TURN NARRATION
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."
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
  "total_ms": 2840.9,
  "tokens_in": 1086,
  "tokens_out": 1197,
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
  "outcome_summary": "Your attempt to demand an explanation fails as the thugs mock your boldness and demand a toll for passage."
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

You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Toll At The Threshold",
  "location_change": {
    "id": "crossed_keys_inn_entrance",
    "name": "Crossed Keys Inn Entrance",
    "description": "The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men."
  },
  "location_description": null,
  "npc_add": [
    {
      "id": "bald_tough",
      "notes": "Blocking the inn entrance, demanding a toll with a mocking attitude.",
      "name": "Bald Tough",
      "title": "Road Tough",
      "bio": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn."
    },
    {
      "id": "scarred_tough",
      "notes": "Blocking the inn entrance, nervous and twitchy, eyeing the ditches.",
      "name": "Scarred Tough",
      "title": "Road Tough",
      "bio": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll."
    }
  ],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Standing near the town well in the town square."
    }
  ],
  "npc_update": [
    {
      "id": "tyler",
      "notes": "Lurking in the roadside ditches nearby, watching the confrontation from the shadows.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "road_toll_confrontation",
      "text": "Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "As the argument escalates, Scarred Tough's hand moves more decisively toward his blackjack, while Tyler's silhouette shifts closer from the ditches, suggesting the two groups are working in tandem to squeeze the player for more than just coin."
  }
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
  "recent_events_add": [
    {
      "id": "inn_toll_confrontation",
      "text": "Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Offer them a portion of your credits to pass peacefully.'}",
    "{'description': \"Intimidate the thugs to prove you aren't an easy target.\"}",
    "{'description': 'Demand that Bald Tough explain who they are working for.'}",
    "{'description': \"Search the nearby ditches for any sign of Tyler's movement.\"}"
  ],
  "outcome_summary": "Your attempt to demand an explanation fails as the thugs mock your boldness and demand a toll for passage."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_entrance",
    "name": "Crossed Keys Inn Entrance",
    "description": "The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men."
  },
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Toll At The Threshold",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "bald_tough",
      "notes": "Blocking the inn entrance, demanding a toll with a mocking attitude.",
      "name": "Bald Tough",
      "title": "Road Tough",
      "bio": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn."
    },
    {
      "id": "scarred_tough",
      "notes": "Blocking the inn entrance, nervous and twitchy, eyeing the ditches.",
      "name": "Scarred Tough",
      "title": "Road Tough",
      "bio": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll."
    }
  ],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Standing near the town well in the town square."
    }
  ],
  "npc_update": [
    {
      "id": "tyler",
      "notes": "Lurking in the roadside ditches nearby, watching the confrontation from the shadows."
    }
  ],
  "recent_events_add": [
    {
      "id": "inn_toll_confrontation",
      "text": "Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "road_toll_confrontation",
      "text": "Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.",
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

- {'description': 'Offer them a portion of your credits to pass peacefully.'}

- {'description': "Intimidate the thugs to prove you aren't an easy target."}

- {'description': 'Demand that Bald Tough explain who they are working for.'}

- {'description': "Search the nearby ditches for any sign of Tyler's movement."}

### Context Telemetry

- rules: est=1276t trimmed=False
- narrate: est=4540t trimmed=False
- extract.scene: est=4086t trimmed=False attempts=1
- extract.state: est=2325t trimmed=False attempts=1
- extract.progress: est=2234t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bald_tough": {
        "from": null,
        "to": {
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 6
          }
        }
      },
      "halden": {
        "last_seen_state": {
          "from": null,
          "to": "Standing near the town well in the town square."
        }
      },
      "scarred_tough": {
        "from": null,
        "to": {
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 6
          }
        }
      },
      "tough_a": {
        "bio": {
          "from": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "to": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn."
        },
        "title": {
          "from": "Road thug",
          "to": "Road Tough"
        }
      },
      "tough_b": {
        "bio": {
          "from": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "to": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll."
        },
        "title": {
          "from": "Road thug",
          "to": "Road Tough"
        }
      },
      "tyler": {
        "last_seen": {
          "location_id": {
            "from": "town_square",
            "to": "crossed_keys_inn_entrance"
          },
          "location_name": {
            "from": "Town Square",
            "to": "Crossed Keys Inn Entrance"
          },
          "turn": {
            "from": 4,
            "to": 6
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The central hub of Marrow's Crossing, featuring a stone well and a founder's statue under the dimming evening light.",
      "to": "The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men."
    },
    "id": {
      "from": "town_square",
      "to": "crossed_keys_inn_entrance"
    },
    "name": {
      "from": "Town Square",
      "to": "Crossed Keys Inn Entrance"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "tough_b",
        "tough_a"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As the argument escalates, Scarred Tough's hand moves more decisively toward his blackjack, while Tyler's silhouette shifts closer from the ditches, suggesting the two groups are working in tandem to squeeze the player for more than just coin.",
        "surface_as": "npc_behavior",
        "type": "complication"
      }
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
    "location_entered_turn": {
      "from": 3,
      "to": 5
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Blocking the inn entrance, demanding a toll with a mocking attitude.",
          "title": "Road Tough"
        },
        {
          "bio": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Blocking the inn entrance, nervous and twitchy, eyeing the ditches.",
          "title": "Road Tough"
        }
      ],
      "removed": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Standing near the town well, weary from trade, and has just commissioned Voss to deliver the ledger.",
          "title": "Merchant"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
            "id": "tyler",
            "name": "Tyler",
            "notes": "Looming in the doorway of the Crossed Keys, watching the coin on the table.",
            "title": "Enforcer"
          },
          "to": {
            "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
            "id": "tyler",
            "name": "Tyler",
            "notes": "Lurking in the roadside ditches nearby, watching the confrontation from the shadows.",
            "title": "Enforcer"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "inn_toll_confrontation",
          "text": "Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.",
          "turn": 5
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "road_toll_confrontation",
          "max_turns": null,
          "text": "Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Fair Price For Danger",
      "to": "The Toll At The Threshold"
    },
    "tags": {
      "added": [],
      "removed": [
        "exploration"
      ]
    },
    "turn_entered": {
      "from": 3,
      "to": 5
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T6: I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. — … ple pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men.

## Inventory
- **Credits** ×400: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A merchant's ledger provided by Halden for delivery.

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
- **** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.
- Tyler has begun following Voss from a distance, lurking in the roadside ditches.
- Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As the argument escalates, Scarred Tough's hand moves more decisively toward his blackjack, while Tyler's silhouette shifts closer from the ditches, suggesting the two groups are working in tandem to squeeze the player for more than just coin.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Scarred Tough**
- **Bald Tough**
- **Tyler** — last seen Crossed Keys Inn Entrance
- **** — last seen Crossed Keys Inn Entrance
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **** — last seen Crossed Keys Inn Entrance
## NPCs Present in Scene
- Tyler (Enforcer) — Lurking in the roadside ditches nearby, watching the confrontation from the shadows.
- Bald Tough (Road Tough) — Blocking the inn entrance, demanding a toll with a mocking attitude.
- Scarred Tough (Road Tough) — Blocking the inn entrance, nervous and twitchy, eyeing the ditches.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×400 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A merchant's ledger provided by Halden for delivery.

## scene_result
location: `crossed_keys_inn_entrance`

## CURRENT TURN NARRATION
You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player attempts to bribe the toughs with 200 credits to allow passage and end the confrontation.
## prior_turn_narration (T5 — for outcome_summary and actions context)
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

## items_lost
credits

## CURRENT TURN NARRATION
You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to bribe the toughs with 200 credits to allow passage and end the confrontation.",
  "rolled": false,
  "total_ms": 2975.1,
  "tokens_in": 1103,
  "tokens_out": 1220
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the toughs with 200 credits to allow passage and end the confrontation.",
  "intent_verb": "negotiate",
  "target": "the two toughs",
  "stakes": "If the bribe is rejected, the player may be denied entry or forced into a physical confrontation.",
  "check": {
    "required": false,
    "skill": "charisma",
    "difficulty": "trivial",
    "tags": []
  }
}
```

### Narration

You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 200
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
      "id": "bribe_attempt_tension",
      "text": "The attempted bribe of the thugs has increased the tension on the inn steps.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Offer more credits if they continue to demand a toll.'}",
    "{'description': 'Draw a weapon and prepare for a physical confrontation.'}",
    "{'description': 'Call out to Tyler to see if he will intervene.'}",
    "{'description': 'Attempt to push past the thugs into the inn.'}"
  ],
  "outcome_summary": "You offer 200 credits to the thugs, causing one to hesitate while the other remains defensive and wary of Tyler's approach."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 200
    }
  ],
  "inventory_update": [],
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [],
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "bribe_attempt_tension",
      "text": "The attempted bribe of the thugs has increased the tension on the inn steps.",
      "turn": 0
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

- {'description': 'Offer more credits if they continue to demand a toll.'}

- {'description': 'Draw a weapon and prepare for a physical confrontation.'}

- {'description': 'Call out to Tyler to see if he will intervene.'}

- {'description': 'Attempt to push past the thugs into the inn.'}

### Context Telemetry

- rules: est=1282t trimmed=False
- narrate: est=5180t trimmed=False
- extract.scene: skipped
- extract.state: est=2223t trimmed=False attempts=1
- extract.progress: est=2236t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "changed": [
      {
        "from": {
          "amount": 400,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        },
        "to": {
          "amount": 200,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        }
      }
    ]
  },
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As the argument escalates, Scarred Tough's hand moves more decisively toward his blackjack, while Tyler's silhouette shifts closer from the ditches, suggesting the two groups are working in tandem to squeeze the player for more than just coin.",
        "surface_as": "npc_behavior",
        "type": "complication"
      },
      "to": null
    },
    "turn": {
      "from": 6,
      "to": 7
    }
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "bribe_attempt_tension",
          "text": "The attempted bribe of the thugs has increased the tension on the inn steps.",
          "turn": 6
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T7: I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. — … of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men.

## Inventory
- **Credits** ×200: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Ledger**: A merchant's ledger provided by Halden for delivery.

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
- **** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.
- Tyler has begun following Voss from a distance, lurking in the roadside ditches.
- Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.
- The attempted bribe of the thugs has increased the tension on the inn steps.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 6 + 2 +1 (stat) = 9 → PARTIAL
Directive: The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Scarred Tough**
- **Bald Tough**
- **Tyler** — last seen Crossed Keys Inn Entrance
- **** — last seen Crossed Keys Inn Entrance
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **** — last seen Crossed Keys Inn Entrance
## NPCs Present in Scene
- Tyler (Enforcer) — Lurking in the roadside ditches nearby, watching the confrontation from the shadows.
- Bald Tough (Road Tough) — Blocking the inn entrance, demanding a toll with a mocking attitude.
- Scarred Tough (Road Tough) — Blocking the inn entrance, nervous and twitchy, eyeing the ditches.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
inventory, quest_updates

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
- `credits` | Credits ×200 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Ledger ×1 — A merchant's ledger provided by Halden for delivery.

## scene_result
location: `crossed_keys_inn_entrance`

## CURRENT TURN NARRATION
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
inventory, quest_updates

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player presents the merchant seal and ledger to Halden to verify their authenticity or complete a transaction.
## quest_threshold
4 active quests already. Bar is HIGH — only start a new quest for a major new obligation clearly distinct from all existing quests.

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
- `deliver_ledger` | 
  objectives:

## prior_turn_narration (T6 — for outcome_summary and actions context)
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."

## items_gained
Credits

## items_lost
ledger

## CURRENT TURN NARRATION
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player presents the merchant seal and ledger to Halden to verify their authenticity or complete a transaction.",
  "rolled": true,
  "total_ms": 3258.4,
  "tokens_in": 1087,
  "tokens_out": 1203,
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
  "outcome_summary": "You successfully deliver the ledger and merchant seal to Halden, securing your payment, but his warning about a mysterious watcher leaves you on edge."
}
```

**Raw LLM output:**
```
{
  "intent": "The player presents the merchant seal and ledger to Halden to verify their authenticity or complete a transaction.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "Halden may refuse to accept the documents or suspect a forgery, potentially leading to conflict or loss of reputation.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "",
      "amount": 50,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "ledger",
      "amount": null
    }
  ],
  "inventory_update": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Payment from Halden for the ledger delivery."
    }
  ],
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
  "recent_events_add": [
    {
      "id": "mysterious_watcher_in_ditches",
      "text": "Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Ask Halden for more details about the man in the jerkin.'}",
    "{'text': 'Search the inn for any sign of the suspicious watcher.'}",
    "{'text': 'Inquire if Halden knows who is responsible for the road thugs.'}",
    "{'text': 'Order a drink and keep a watchful eye on the door.'}"
  ],
  "outcome_summary": "You successfully deliver the ledger and merchant seal to Halden, securing your payment, but his warning about a mysterious watcher leaves you on edge."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "",
      "amount": 50,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "ledger"
    }
  ],
  "inventory_update": [
    {
      "id": "credits",
      "name": "Credits",
      "notes": "Payment from Halden for the ledger delivery."
    }
  ],
  "quest_updates": [
    {
      "id": "deliver_the_ledger",
      "title": "",
      "status": "active",
      "objectives": [
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
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "mysterious_watcher_in_ditches",
      "text": "Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.",
      "turn": 7
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

- {'text': 'Ask Halden for more details about the man in the jerkin.'}

- {'text': 'Search the inn for any sign of the suspicious watcher.'}

- {'text': 'Inquire if Halden knows who is responsible for the road thugs.'}

- {'text': 'Order a drink and keep a watchful eye on the door.'}

### Context Telemetry

- rules: est=1278t trimmed=False
- narrate: est=5597t trimmed=False
- extract.scene: skipped
- extract.state: est=2335t trimmed=False attempts=1
- extract.progress: est=2482t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "removed": [
      {
        "amount": 1,
        "id": "ledger",
        "name": "Ledger",
        "notes": "A merchant's ledger provided by Halden for delivery."
      }
    ],
    "changed": [
      {
        "from": {
          "amount": 200,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        },
        "to": {
          "amount": 250,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        }
      }
    ]
  },
  "meta": {
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
              "done": true,
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
    "recent_events": {
      "added": [
        {
          "id": "mysterious_watcher_in_ditches",
          "text": "Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.",
          "turn": 7
        }
      ]
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T8: I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. — …  man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men.

## Inventory
- **Credits** ×250: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.
- **** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.
- Tyler has begun following Voss from a distance, lurking in the roadside ditches.
- Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.
- The attempted bribe of the thugs has increased the tension on the inn steps.
- Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: easy
Roll: 5 + 4 +1 (stat) +1 (diff) = 11 → SUCCESS
Directive: The hack succeeds cleanly. Clean success — you do what you intended.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Scarred Tough**
- **Bald Tough**
- **Tyler** — last seen Crossed Keys Inn Entrance
- **** — last seen Crossed Keys Inn Entrance
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **** — last seen Crossed Keys Inn Entrance
## NPCs Present in Scene
- Tyler (Enforcer) — Lurking in the roadside ditches nearby, watching the confrontation from the shadows.
- Bald Tough (Road Tough) — Blocking the inn entrance, demanding a toll with a mocking attitude.
- Scarred Tough (Road Tough) — Blocking the inn entrance, nervous and twitchy, eyeing the ditches.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
SUCCESS on dexterity — The hack succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`crossed_keys_inn_entrance` | Crossed Keys Inn Entrance
The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tyler` | Tyler (Enforcer) — Lurking in the roadside ditches nearby, watching the confrontation from the shadows.
- `tough_a` | Bald Tough (Road Tough) — Blocking the inn entrance, demanding a toll with a mocking attitude.
- `tough_b` | Scarred Tough (Road Tough) — Blocking the inn entrance, nervous and twitchy, eyeing the ditches.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `road_toll_confrontation` [immediate] Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance. (added turn 5)

## deescalate
true — player succeeded on a check against active pressure. Do NOT add new pressures. Downgrade or remove existing ones.

⚠ Quest "" stalled for 5 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_ledger` | 



## previous_turn_narration (T8 context)
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

## CURRENT TURN NARRATION
You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
location_change, inventory

## rules_outcome
SUCCESS on dexterity. The hack succeeds cleanly. Clean success — you do what you intended.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: dexterity
band: success
directive: The hack succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×250 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_service_corridor`
(location changed)
## CURRENT TURN NARRATION
You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
location_change, inventory

## rules_outcome
SUCCESS on dexterity.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
hack: The player attempts to use a brass key to unlock the inn's front door to see if it provides access to a back room.
## prior_turn_narration (T7 — for outcome_summary and actions context)
You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

## CURRENT TURN NARRATION
You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "hack",
  "intent": "The player attempts to use a brass key to unlock the inn's front door to see if it provides access to a back room.",
  "rolled": true,
  "total_ms": 3692.9,
  "tokens_in": 1090,
  "tokens_out": 1221,
  "skill": "dexterity",
  "difficulty": "easy",
  "dice": [
    5,
    4
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "final_total": 11,
  "band": "success",
  "outcome_summary": "You successfully use the brass key to unlock a side door, gaining access to a quiet service corridor and escaping the immediate confrontation on the porch."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use a brass key to unlock the inn's front door to see if it provides access to a back room.",
  "intent_verb": "hack",
  "target": "inn's front door",
  "stakes": "The player might fail to unlock the door, potentially alerting staff or finding the key doesn't fit, leaving them stuck outside.",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.

### Extract Scene

```json
{
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "The Service Corridor Silence",
  "location_change": {
    "id": "crossed_keys_inn_service_corridor",
    "name": "Crossed Keys Inn Service Corridor",
    "description": "A narrow, dimly lit passage smelling of floor wax and stale grease, offering a quiet refuge from the tavern's noise."
  },
  "location_description": "The atmosphere shifts from the tense, crowded entrance to a stagnant, hollow stillness within the narrow corridor.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Standing on the porch demanding a toll."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Standing on the porch eyeing the ditches."
    },
    {
      "id": "tyler",
      "last_seen_state": "Lurking in the roadside ditches outside the inn."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "road_toll_confrontation"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "surface_as": "ambient",
    "instruction": "As the heavy door thuds shut, a faint, rhythmic scraping sound echoes from further down the service corridor, suggesting someone or something is moving toward the player from the kitchen area."
  }
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
  "recent_events_add": [
    {
      "id": "entered_crossed_keys_service_corridor",
      "text": "You successfully unlocked and entered a side service corridor of the Crossed Keys Inn.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Search the service corridor for a way into the main tavern.'}",
    "{'description': 'Quietly slip back out to confront the thugs before they notice.'}",
    "{'description': 'Call out to the thugs to see if they followed you.'}",
    "{'description': 'Investigate the source of the stale cooking grease smell.'}"
  ],
  "outcome_summary": "You successfully use the brass key to unlock a side door, gaining access to a quiet service corridor and escaping the immediate confrontation on the porch."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_service_corridor",
    "name": "Crossed Keys Inn Service Corridor",
    "description": "A narrow, dimly lit passage smelling of floor wax and stale grease, offering a quiet refuge from the tavern's noise."
  },
  "location_description": "The atmosphere shifts from the tense, crowded entrance to a stagnant, hollow stillness within the narrow corridor.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "The Service Corridor Silence",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Standing on the porch demanding a toll."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Standing on the porch eyeing the ditches."
    },
    {
      "id": "tyler",
      "last_seen_state": "Lurking in the roadside ditches outside the inn."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "entered_crossed_keys_service_corridor",
      "text": "You successfully unlocked and entered a side service corridor of the Crossed Keys Inn.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "road_toll_confrontation"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'description': 'Search the service corridor for a way into the main tavern.'}

- {'description': 'Quietly slip back out to confront the thugs before they notice.'}

- {'description': 'Call out to the thugs to see if they followed you.'}

- {'description': 'Investigate the source of the stale cooking grease smell.'}

### Context Telemetry

- rules: est=1279t trimmed=False
- narrate: est=5982t trimmed=False
- extract.scene: est=4215t trimmed=False attempts=1
- extract.state: est=2234t trimmed=False attempts=1
- extract.progress: est=2159t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "tough_a": {
        "last_seen_state": {
          "from": null,
          "to": "Standing on the porch demanding a toll."
        }
      },
      "tough_b": {
        "last_seen_state": {
          "from": null,
          "to": "Standing on the porch eyeing the ditches."
        }
      },
      "tyler": {
        "last_seen_state": {
          "from": null,
          "to": "Lurking in the roadside ditches outside the inn."
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The wooden steps of the inn, where the evening shadows gather and the entrance is physically blocked by two intimidating men.",
      "to": "A narrow, dimly lit passage smelling of floor wax and stale grease, offering a quiet refuge from the tavern's noise."
    },
    "id": {
      "from": "crossed_keys_inn_entrance",
      "to": "crossed_keys_inn_service_corridor"
    },
    "name": {
      "from": "Crossed Keys Inn Entrance",
      "to": "Crossed Keys Inn Service Corridor"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As the heavy door thuds shut, a faint, rhythmic scraping sound echoes from further down the service corridor, suggesting someone or something is moving toward the player from the kitchen area.",
        "surface_as": "ambient",
        "type": "revelation"
      }
    },
    "turn": {
      "from": 8,
      "to": 9
    }
  },
  "pc": {
    "momentum": {
      "from": -2,
      "to": -1
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 5,
      "to": 8
    },
    "present_npcs": {
      "removed": [
        {
          "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
          "id": "tyler",
          "name": "Tyler",
          "notes": "Lurking in the roadside ditches nearby, watching the confrontation from the shadows.",
          "title": "Enforcer"
        },
        {
          "bio": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Blocking the inn entrance, demanding a toll with a mocking attitude.",
          "title": "Road Tough"
        },
        {
          "bio": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Blocking the inn entrance, nervous and twitchy, eyeing the ditches.",
          "title": "Road Tough"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "entered_crossed_keys_service_corridor",
          "text": "You successfully unlocked and entered a side service corridor of the Crossed Keys Inn.",
          "turn": 8
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "road_toll_confrontation",
          "max_turns": null,
          "text": "Bald Tough and Scarred Tough are demanding a toll to pass through the inn entrance.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "The Toll At The Threshold",
      "to": "The Service Corridor Silence"
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
      "from": 5,
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
Location: Crossed Keys Inn Service Corridor
## last_turn (tail of the most recent narrative)
T9: I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. — … Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.

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
Crossed Keys Inn Service Corridor (crossed_keys_inn_service_corridor)
A narrow, dimly lit passage smelling of floor wax and stale grease, offering a quiet refuge from the tavern's noise.

## Inventory
- **Credits** ×250: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.
- **** [active]

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.
- Tyler has begun following Voss from a distance, lurking in the roadside ditches.
- Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.
- The attempted bribe of the thugs has increased the tension on the inn steps.
- Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.
- You successfully unlocked and entered a side service corridor of the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and settle into it. The chair legs scrape harshly against the floorboards, drawing a few brief glances from the other patrons. The man doesn't look up immediately; he merely stares into the amber liquid of his glass, his thumb tracing the rim. His face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table.

When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today."

**Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name.

The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table.


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing.

The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes.

"I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip."

**Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high."


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles.

You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road.

A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn.


## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance.

"What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things."

**Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him.

**Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home."

**Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado.

**Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door."

The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 5 + 4 +1 (stat) = 10 → SUCCESS
Directive: The persuade succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (REVELATION, surface as ambient):
As the heavy door thuds shut, a faint, rhythmic scraping sound echoes from further down the service corridor, suggesting someone or something is moving toward the player from the kitchen area.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Scarred Tough**
- **Bald Tough**
- **Tyler** — last seen Crossed Keys Inn Entrance
- **** — last seen Crossed Keys Inn Entrance
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **** — last seen Crossed Keys Inn Entrance
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
compendium_npc, inventory

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
- `credits` | Credits ×250 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_service_corridor`

## CURRENT TURN NARRATION
You lean your weight against the cold, damp stone of the service corridor wall, pressing your ear against the masonry to catch any movement from the other side. The stone is unyielding and chilled, vibrating faintly with the muffled roar of the tavern and the distant shouts from the street. "I have credits. Open up," you whisper into the dark, the words barely a breath against the stone. To drive the point home, you reach into your pouch and press a single **Credit** against the wall, letting the metal clink softly against the rock.

The response is not a voice, but a sound. From deeper within the service passage, beyond the reach of the dim light, comes a rhythmic, unmistakable scraping. It is the sound of something heavy being dragged across the floorboards—or perhaps a blade being sharpened against a stone. The noise is slow and deliberate, echoing up the narrow hallway and through the very wall you are leaning against.

A shadow flickers at the far end of the corridor, near the threshold of the kitchen. A figure emerges from the gloom, moving with a quiet, practiced gait that suggests they were waiting for someone to arrive. It is a woman with sharp, avian features and hair pulled back so tightly it seems to stretch the skin of her forehead. She wears a grease-stained apron over a dark tunic, and her eyes catch the sliver of light from the door with a predatory glint.

**Kathryn** stops several paces away, her gaze dropping to the single coin you pressed against the wall. She doesn't reach for it. Instead, she rests a heavy iron ladle against her shoulder like a club. "The wall doesn't take bribes, traveler," she says, her voice a low, dry rasp that cuts through the stagnant air. "And the kitchen is closed to those who come through the service door without an invitation."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
compendium_npc, inventory

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to bribe or persuade someone behind the wall to open the door.
## prior_turn_narration (T8 — for outcome_summary and actions context)
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

## items_lost
credits

## CURRENT TURN NARRATION
You lean your weight against the cold, damp stone of the service corridor wall, pressing your ear against the masonry to catch any movement from the other side. The stone is unyielding and chilled, vibrating faintly with the muffled roar of the tavern and the distant shouts from the street. "I have credits. Open up," you whisper into the dark, the words barely a breath against the stone. To drive the point home, you reach into your pouch and press a single **Credit** against the wall, letting the metal clink softly against the rock.

The response is not a voice, but a sound. From deeper within the service passage, beyond the reach of the dim light, comes a rhythmic, unmistakable scraping. It is the sound of something heavy being dragged across the floorboards—or perhaps a blade being sharpened against a stone. The noise is slow and deliberate, echoing up the narrow hallway and through the very wall you are leaning against.

A shadow flickers at the far end of the corridor, near the threshold of the kitchen. A figure emerges from the gloom, moving with a quiet, practiced gait that suggests they were waiting for someone to arrive. It is a woman with sharp, avian features and hair pulled back so tightly it seems to stretch the skin of her forehead. She wears a grease-stained apron over a dark tunic, and her eyes catch the sliver of light from the door with a predatory glint.

**Kathryn** stops several paces away, her gaze dropping to the single coin you pressed against the wall. She doesn't reach for it. Instead, she rests a heavy iron ladle against her shoulder like a club. "The wall doesn't take bribes, traveler," she says, her voice a low, dry rasp that cuts through the stagnant air. "And the kitchen is closed to those who come through the service door without an invitation."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe or persuade someone behind the wall to open the door.",
  "rolled": true,
  "total_ms": 3384.1,
  "tokens_in": 1097,
  "tokens_out": 1211,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    5,
    4
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": "Your attempt to bribe the door fails as Kathryn emerges from the shadows, brandishing a ladle and refusing your coin."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe or persuade someone behind the wall to open the door.",
  "intent_verb": "persuade",
  "target": "unseen person behind the wall",
  "stakes": "The player may be discovered or ignored, potentially alerting guards or losing the opportunity to enter quietly.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You lean your weight against the cold, damp stone of the service corridor wall, pressing your ear against the masonry to catch any movement from the other side. The stone is unyielding and chilled, vibrating faintly with the muffled roar of the tavern and the distant shouts from the street. "I have credits. Open up," you whisper into the dark, the words barely a breath against the stone. To drive the point home, you reach into your pouch and press a single **Credit** against the wall, letting the metal clink softly against the rock.

The response is not a voice, but a sound. From deeper within the service passage, beyond the reach of the dim light, comes a rhythmic, unmistakable scraping. It is the sound of something heavy being dragged across the floorboards—or perhaps a blade being sharpened against a stone. The noise is slow and deliberate, echoing up the narrow hallway and through the very wall you are leaning against.

A shadow flickers at the far end of the corridor, near the threshold of the kitchen. A figure emerges from the gloom, moving with a quiet, practiced gait that suggests they were waiting for someone to arrive. It is a woman with sharp, avian features and hair pulled back so tightly it seems to stretch the skin of her forehead. She wears a grease-stained apron over a dark tunic, and her eyes catch the sliver of light from the door with a predatory glint.

**Kathryn** stops several paces away, her gaze dropping to the single coin you pressed against the wall. She doesn't reach for it. Instead, she rests a heavy iron ladle against her shoulder like a club. "The wall doesn't take bribes, traveler," she says, her voice a low, dry rasp that cuts through the stagnant air. "And the kitchen is closed to those who come through the service door without an invitation."

### Extract Scene

*(skipped — domain not active this turn)*

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
      "id": "kathryn_confrontation",
      "text": "Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Try to bribe Kathryn more convincingly to gain entry.'}",
    "{'description': 'Ask Kathryn about the scraping sound heard in the corridor.'}",
    "{'description': 'Attempt to intimidate Kathryn with the merchant seal or authority.'}",
    "{'description': 'Search the dark corridor for the source of the scraping noise.'}"
  ],
  "outcome_summary": "Your attempt to bribe the door fails as Kathryn emerges from the shadows, brandishing a ladle and refusing your coin."
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
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [],
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "kathryn_confrontation",
      "text": "Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.",
      "turn": 0
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

- {'description': 'Try to bribe Kathryn more convincingly to gain entry.'}

- {'description': 'Ask Kathryn about the scraping sound heard in the corridor.'}

- {'description': 'Attempt to intimidate Kathryn with the merchant seal or authority.'}

- {'description': 'Search the dark corridor for the source of the scraping noise.'}

### Context Telemetry

- rules: est=1286t trimmed=False
- narrate: est=6304t trimmed=False
- extract.scene: skipped
- extract.state: est=2403t trimmed=False attempts=1
- extract.progress: est=2349t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "changed": [
      {
        "from": {
          "amount": 250,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        },
        "to": {
          "amount": 249,
          "id": "credits",
          "name": "Credits",
          "notes": "Payment from Halden for the ledger delivery."
        }
      }
    ]
  },
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As the heavy door thuds shut, a faint, rhythmic scraping sound echoes from further down the service corridor, suggesting someone or something is moving toward the player from the kitchen area.",
        "surface_as": "ambient",
        "type": "revelation"
      },
      "to": null
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
    "present_npcs": {
      "added": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "",
          "title": "Old creditor"
        },
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "",
          "title": "Merchant"
        },
        {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "id": "innkeeper",
          "name": "Edda",
          "notes": "",
          "title": "Innkeeper at the Crossed Keys"
        },
        {
          "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
          "id": "matthew_estrada",
          "name": "Matthew Estrada",
          "notes": "",
          "title": "Traveler"
        },
        {
          "bio": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "",
          "title": "Road Tough"
        },
        {
          "bio": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "",
          "title": "Road Tough"
        },
        {
          "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
          "id": "tyler",
          "name": "Tyler",
          "notes": "",
          "title": "Enforcer"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "kathryn_confrontation",
          "text": "Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.",
          "turn": 9
        }
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
Location: Crossed Keys Inn Service Corridor
## last_turn (tail of the most recent narrative)
T10: I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall. — …  through the stagnant air. "And the kitchen is closed to those who come through the service door without an invitation."

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
Crossed Keys Inn Service Corridor (crossed_keys_inn_service_corridor)
A narrow, dimly lit passage smelling of floor wax and stale grease, offering a quiet refuge from the tavern's noise.

## Inventory
- **Credits** ×249: Payment from Halden for the ledger delivery.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.

## Quests
- **Settle the Old Debt** [active]
  - [ ] Find Caron, the man you owe.
  - [ ] Pay Caron in person and have him mark the debt cleared.
- **Clear the Road Toughs** [active]
  - [ ] Find out who hired the toughs blocking the road.
  - [ ] Convince, pay, or remove the toughs from the inn.
- **** [active]

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron refuses to negotiate and demands labor in lieu of coin.
- Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.
- Halden has hired Voss to deliver the ledger for 200 credits.
- Tyler has begun following Voss from a distance, lurking in the roadside ditches.
- Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.
- The attempted bribe of the thugs has increased the tension on the inn steps.
- Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.
- You successfully unlocked and entered a side service corridor of the Crossed Keys Inn.
- Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.

## Prior History (summarized — treat as background, not current scene)
face is a map of deep lines and broken capillaries, illuminated by the flickering tallow candle on the table. When he finally meets your eyes, there is no warmth and no hint of the leniency you were hoping for. He sets the glass down with a dull thud and leans forward, the scent of stale ale and unwashed wool wafting from him. "You think a few words and a polite seat can make the numbers change, Voss?" he asks, his voice a low, rasping growl. "The interest doesn't care about your manners. You're late, and the debt has grown teeth." He reaches into a heavy leather pouch at his belt and pulls out a small, notched piece of wood—a tally stick. He taps it rhythmically against the table, the sound echoing like a slow heartbeat. "I'm not here to negotiate. I'm here to collect. If you can't bring the coin, then you've got nothing left to trade but your labor, and I've no use for a courier who can't keep his head down." ## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. You reach into your pack and pull out the heavy pouch of **Credits**. The metal clinks with a dull, satisfying weight as you slide the bag across the scarred wood of the table. It stops just short of **Caron**'s glass. "Five hundred," you say, your voice steady despite the ache in your ribs. "Take it and mark the debt cleared. I want the ledger closed today." **Caron** stares at the bag, his eyes narrowing. He doesn't reach for the coin immediately. Instead, the rhythmic tapping of the notched tally stick stops abruptly. He looks up at you, a slow, predatory grin spreading across his weathered face. "A man who pays when he's cornered is a man who can be trusted to pay when the stakes are higher," he murmurs. He pulls a small, leather-bound ledger from his coat and flips through the yellowed pages, searching for your name. The heavy thud of boots on the floorboards interrupts the moment. A large man in a stained leather jerkin, **Tyler**, looms in the doorway of the *Crossed Keys Inn*. He doesn't say a word, but his gaze sweeps the room with a practiced, menacing efficiency. His eyes lock onto yours, then drift down to the bag of coin on the table. He shifts his weight, his hand resting near the heavy club hanging at his hip, and waits for a signal from the table. ## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. You push back from the table, ignoring the heavy gaze of **Tyler** and the predatory grin still etched on **Caron**'s face. The bag of coin remains on the scarred wood between you, a target left too exposed. You navigate the dim, smoky interior of the *Crossed Keys Inn*, your boots echoing on the floorboards as you push through the heavy oak door and step back out into the cooling evening air of Marrow's Crossing. The town square is quiet, the stone well standing like a silent sentinel under the dimming light. You find **Halden** near the well, his silhouette hunched over a map. He looks up as you approach, the light from a nearby street lamp glinting off the pressed wax seal he holds. He looks tired, the weight of trade etched into the corners of his eyes. "I can take the ledger to the *Crossed Keys Inn*," you say, keeping your voice low and professional. "I'll deliver it safely and confirm the contract in person. Two hundred credits for the trip." **Halden** rubs a hand over his weary face, studying you. He looks at the ledger, then back at your determined expression. "The road is getting restless, Voss. People are losing more than just their coin these days," he says, his voice a weary murmur. He reaches into a small pouch at his belt and pulls out a handful of **Credits**. "Two hundred. It's a fair price for a man who looks like he can handle himself. Take the ledger and get moving. I want this settled before the moon is high." ## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. You take the **Ledger** from **Halden** and tuck it securely into your pack, the weight of the task settling alongside the new **Credits** in your pouch. You turn away from the stone well and navigate the darkening streets of Marrow's Crossing. The town square is thinning out as the evening chill sets in, and the shadows cast by the stone buildings stretch long and distorted across the cobbles. You head toward the east gate, the path leading you back toward the merchant road that connects the town to the surrounding trade routes. The heavy oak gates of the town stand partially ajar, allowing the scent of river silt and woodsmoke to drift in. As you pass through the threshold and begin the trek back toward the *Crossed Keys Inn*, the rhythmic thud of your own boots is the only sound on the road. A few dozen paces behind you, the heavy door of the inn creaks on its hinges. **Tyler** steps out into the twilight, his leather jerkin creaking softly. He doesn't call out or attempt to intercept you; instead, he slips into the deepening gloom of the roadside ditches. He keeps a steady, predatory distance, his silhouette a dark shape moving rhythmically through the shadows as he tracks your progress toward the inn. ## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. You march up the steps of the *Crossed Keys Inn*, your boots striking the wood with a heavy, rhythmic thud. The two men blocking the threshold don't move as you approach. One is a thick-set man with a broken nose, known to the locals as **Bald Tough**, and the other is a wiry, nervous-looking man with a jagged scar running through his eyebrow, the **Scarred Tough**. They stand shoulder-to-shoulder, a physical wall of muscle and leather blocking the entrance. "What are you doing here?" you demand, stopping just a few feet from them. "I'm not leaving until I hear your side of things." **Bald Tough** lets out a short, barking laugh that lacks any genuine mirth. He crosses his massive arms over his chest, his eyes scanning you up and down with blatant disrespect. "Our side? Our side is the road, traveler. And the road has a toll." He doesn't look intimidated by your proximity; if anything, your confrontation seems to amuse him. **Scarred Tough** shifts uncomfortably, his hand twitching near a heavy blackjack tucked into his belt. He glances nervously toward the ditches where **Tyler** was lurking, then back to you. "You've got a loud mouth for someone walking a lonely road," he spits, his voice thin and grating. "We aren't 'doing' anything. We're just making sure the right people pay for the privilege of passing through. If you want a story, go find a bard. If you want to pass, find your coin." ## Turn 7 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. You reach into your pouch and pull out a handful of **Credits**, letting the heavy metal coins spill from your palm. They hit the wooden steps with a series of sharp, ringing clatters, settling in the dust between the two men. "There's two hundred," you say, your voice flat and unyielding. "Caron's coin is paid. Now get out of my way and go home." **Bald Tough** stares down at the glinting coins, his eyes widening slightly. He looks up at you, the mocking grin faltering as he realizes you aren't just a traveler to be shaken down, but someone who has already dealt with the town's most dangerous moneylender. He glances at the coins, then at his partner, his posture losing some of its aggressive bravado. **Scarred Tough** doesn't look at the money. Instead, his eyes dart nervously toward the ditches where the dark shape of **Tyler** has begun to move closer. He reaches down, his fingers curling around the handle of the heavy blackjack at his belt, his knuckles white. "Caron's business is his own," he spits, though the tremor in his voice betrays him. "We don't care who pays who. We care about the toll for *this* door." The tension on the steps thickens. Behind them, the heavy door of the *Crossed Keys Inn* remains shut, and the silence of the evening is broken only by the rhythmic, approaching crunch of footsteps from the shadows of the roadside ditches.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the tension on the steps, ignoring the glint of the **Credits** left on the wood and the wary stares of the two men. You shoulder your way through the heavy oak doors of the *Crossed Keys Inn*, the sudden warmth and smell of roasted meat hitting you like a physical weight. The thugs let you pass, though **Bald Tough** spits on the floor near your heels as you cross the threshold.

Inside, the din of the tavern is a dull roar of voices and clinking glass. You navigate the crowded floor and find **Halden** seated at a corner table, his silhouette framed by the dim light of a guttering candle. He looks up as you approach, his eyes scanning your face for signs of the struggle you just left on the porch.

You sit and reach into your coat, pulling out the **Ledger** and the heavy merchant seal. You slide the **Ledger** across the table and place the seal beside it. "The delivery is complete," you say. **Halden** reaches out, his fingers trembling slightly as he pulls the book toward him. He inspects the wax seal, ensuring it remains unbroken.

"You've done well, Voss," he murmurs, though his eyes remain darting and anxious. He leans closer, his voice dropping to a whisper. "But be careful. I saw a man watching you from the ditches on your way up. A man in a leather jerkin. He didn't look like a man interested in trade." He pushes a small bundle of **Credits** toward you, the payment for the task finally secured.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.

**Turn 10** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
You lean your weight against the cold, damp stone of the service corridor wall, pressing your ear against the masonry to catch any movement from the other side. The stone is unyielding and chilled, vibrating faintly with the muffled roar of the tavern and the distant shouts from the street. "I have credits. Open up," you whisper into the dark, the words barely a breath against the stone. To drive the point home, you reach into your pouch and press a single **Credit** against the wall, letting the metal clink softly against the rock.

The response is not a voice, but a sound. From deeper within the service passage, beyond the reach of the dim light, comes a rhythmic, unmistakable scraping. It is the sound of something heavy being dragged across the floorboards—or perhaps a blade being sharpened against a stone. The noise is slow and deliberate, echoing up the narrow hallway and through the very wall you are leaning against.

A shadow flickers at the far end of the corridor, near the threshold of the kitchen. A figure emerges from the gloom, moving with a quiet, practiced gait that suggests they were waiting for someone to arrive. It is a woman with sharp, avian features and hair pulled back so tightly it seems to stretch the skin of her forehead. She wears a grease-stained apron over a dark tunic, and her eyes catch the sliver of light from the door with a predatory glint.

**Kathryn** stops several paces away, her gaze dropping to the single coin you pressed against the wall. She doesn't reach for it. Instead, she rests a heavy iron ladle against her shoulder like a club. "The wall doesn't take bribes, traveler," she says, her voice a low, dry rasp that cuts through the stagnant air. "And the kitchen is closed to those who come through the service door without an invitation."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 5 + 4 +1 (stat) = 10 → SUCCESS
Directive: The intimidate succeeds cleanly. Clean success — you do what you intended.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Scarred Tough**
- **Bald Tough**
- **Tyler** — last seen Crossed Keys Inn Entrance
- **** — last seen Crossed Keys Inn Entrance
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Town Square
- **Edda**
- **Matthew Estrada**
- **** — last seen Crossed Keys Inn Entrance
## NPCs Present in Scene
- Caron (Old creditor)
- Halden (Merchant)
- Edda (Innkeeper at the Crossed Keys)
- Matthew Estrada (Traveler)
- Bald Tough (Road Tough)
- Scarred Tough (Road Tough)
- Tyler (Enforcer)
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
`crossed_keys_inn_service_corridor` | Crossed Keys Inn Service Corridor
A narrow, dimly lit passage smelling of floor wax and stale grease, offering a quiet refuge from the tavern's noise.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor)
- `halden` | Halden (Merchant)
- `innkeeper` | Edda (Innkeeper at the Crossed Keys)
- `matthew_estrada` | Matthew Estrada (Traveler)
- `tough_a` | Bald Tough (Road Tough)
- `tough_b` | Scarred Tough (Road Tough)
- `tyler` | Tyler (Enforcer)

_(immutable section omitted — see Static Context > Seed State)_

⚠ Quest "" stalled for 7 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_ledger` | 



## previous_turn_narration (T10 context)
You lean your weight against the cold, damp stone of the service corridor wall, pressing your ear against the masonry to catch any movement from the other side. The stone is unyielding and chilled, vibrating faintly with the muffled roar of the tavern and the distant shouts from the street. "I have credits. Open up," you whisper into the dark, the words barely a breath against the stone. To drive the point home, you reach into your pouch and press a single **Credit** against the wall, letting the metal clink softly against the rock.

The response is not a voice, but a sound. From deeper within the service passage, beyond the reach of the dim light, comes a rhythmic, unmistakable scraping. It is the sound of something heavy being dragged across the floorboards—or perhaps a blade being sharpened against a stone. The noise is slow and deliberate, echoing up the narrow hallway and through the very wall you are leaning against.

A shadow flickers at the far end of the corridor, near the threshold of the kitchen. A figure emerges from the gloom, moving with a quiet, practiced gait that suggests they were waiting for someone to arrive. It is a woman with sharp, avian features and hair pulled back so tightly it seems to stretch the skin of her forehead. She wears a grease-stained apron over a dark tunic, and her eyes catch the sliver of light from the door with a predatory glint.

**Kathryn** stops several paces away, her gaze dropping to the single coin you pressed against the wall. She doesn't reach for it. Instead, she rests a heavy iron ladle against her shoulder like a club. "The wall doesn't take bribes, traveler," she says, her voice a low, dry rasp that cuts through the stagnant air. "And the kitchen is closed to those who come through the service door without an invitation."

## CURRENT TURN NARRATION
You push through the heavy service door and re-enter the main tavern, the sudden wall of noise and heat hitting you like a physical blow. You navigate the crowded floor, dodging a serving girl carrying a tray of frothing ale, and fix your eyes on a man sitting alone at the far end of the bar. **Matthew Estrada** sits with a rigid, upright posture that stands in stark contrast to the slumped, drunken patrons surrounding him. His eyes don't wander aimlessly; they cut through the room in precise, rhythmic sweeps, tracking the door and the patrons with the mechanical intensity of a trained sentry.

You bridge the gap between the tables and reach out, your fingers clamping firmly around his wrist. The skin is calloused and lean. "Who are you really?" you demand, leaning into his space and tightening your grip. "And why are you watching this room like a soldier on watch?"

**Matthew Estrada** doesn't flinch. He doesn't even attempt to pull his arm away. Instead, he turns his head slowly to meet your gaze, his eyes cold and entirely unblinking. He looks less like a startled traveler and more like a predator deciding whether a nuisance is worth the effort of a kill. "A man can watch a room without being a soldier, traveler," he says, his voice a calm, low baritone that carries an unmistakable edge of authority. "But a man who grabs strangers by the wrist is usually looking for a fight he can't finish. Walk away while you still have the hands to do it."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
scene, inventory

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

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×249 — Payment from Halden for the ledger delivery.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_tavern`
(location changed)
## CURRENT TURN NARRATION
You push through the heavy service door and re-enter the main tavern, the sudden wall of noise and heat hitting you like a physical blow. You navigate the crowded floor, dodging a serving girl carrying a tray of frothing ale, and fix your eyes on a man sitting alone at the far end of the bar. **Matthew Estrada** sits with a rigid, upright posture that stands in stark contrast to the slumped, drunken patrons surrounding him. His eyes don't wander aimlessly; they cut through the room in precise, rhythmic sweeps, tracking the door and the patrons with the mechanical intensity of a trained sentry.

You bridge the gap between the tables and reach out, your fingers clamping firmly around his wrist. The skin is calloused and lean. "Who are you really?" you demand, leaning into his space and tightening your grip. "And why are you watching this room like a soldier on watch?"

**Matthew Estrada** doesn't flinch. He doesn't even attempt to pull his arm away. Instead, he turns his head slowly to meet your gaze, his eyes cold and entirely unblinking. He looks less like a startled traveler and more like a predator deciding whether a nuisance is worth the effort of a kill. "A man can watch a room without being a soldier, traveler," he says, his voice a calm, low baritone that carries an unmistakable edge of authority. "But a man who grabs strangers by the wrist is usually looking for a fight he can't finish. Walk away while you still have the hands to do it."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
scene, inventory

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
intimidate: Confront Matthew Estrada to uncover his true identity and motives for his suspicious behavior.
## prior_turn_narration (T9 — for outcome_summary and actions context)
You reach into your pocket and retrieve the **Brass key**, the metal cool and solid against your palm. You ignore the lingering stares of the men on the porch and step up to the heavy oak door of the *Crossed Keys Inn*. Instead of pushing through the main entrance where the thugs stand guard, you move toward the side of the building, searching the frame for a secondary latch.

The lock is an old, recessed mechanism tucked into the weather-beaten wood of the side panel. You fit the **Brass key** into the keyhole and turn. There is a heavy, mechanical *click* that resonates through the wood, a sound of gears finally finding their teeth. The door yields with a slow, unceremonious groan, swinging inward to reveal a narrow, dimly lit service corridor.

The air inside the passage is stagnant, smelling of floor wax and stale cooking grease. It is a quiet, hollow space, far removed from the tension of the street and the low murmur of the tavern. The heavy door swings shut behind you with a soft thud, cutting off the sight of the men on the steps and the looming shape of **Tyler** in the ditches. For a moment, the only sound is the steady rhythm of your own breathing in the sudden stillness.

## CURRENT TURN NARRATION
You push through the heavy service door and re-enter the main tavern, the sudden wall of noise and heat hitting you like a physical blow. You navigate the crowded floor, dodging a serving girl carrying a tray of frothing ale, and fix your eyes on a man sitting alone at the far end of the bar. **Matthew Estrada** sits with a rigid, upright posture that stands in stark contrast to the slumped, drunken patrons surrounding him. His eyes don't wander aimlessly; they cut through the room in precise, rhythmic sweeps, tracking the door and the patrons with the mechanical intensity of a trained sentry.

You bridge the gap between the tables and reach out, your fingers clamping firmly around his wrist. The skin is calloused and lean. "Who are you really?" you demand, leaning into his space and tightening your grip. "And why are you watching this room like a soldier on watch?"

**Matthew Estrada** doesn't flinch. He doesn't even attempt to pull his arm away. Instead, he turns his head slowly to meet your gaze, his eyes cold and entirely unblinking. He looks less like a startled traveler and more like a predator deciding whether a nuisance is worth the effort of a kill. "A man can watch a room without being a soldier, traveler," he says, his voice a calm, low baritone that carries an unmistakable edge of authority. "But a man who grabs strangers by the wrist is usually looking for a fight he can't finish. Walk away while you still have the hands to do it."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "intimidate",
  "intent": "Confront Matthew Estrada to uncover his true identity and motives for his suspicious behavior.",
  "rolled": true,
  "total_ms": 3154.2,
  "tokens_in": 1098,
  "tokens_out": 1208,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    5,
    4
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": "Your attempt to intimidate Matthew Estrada fails to rattle him; he remains calm and issues a chilling warning."
}
```

**Raw LLM output:**
```
{
  "intent": "Confront Matthew Estrada to uncover his true identity and motives for his suspicious behavior.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "stakes": "Matthew may become hostile, refuse to answer, or alert others to the player's aggression.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You push through the heavy service door and re-enter the main tavern, the sudden wall of noise and heat hitting you like a physical blow. You navigate the crowded floor, dodging a serving girl carrying a tray of frothing ale, and fix your eyes on a man sitting alone at the far end of the bar. **Matthew Estrada** sits with a rigid, upright posture that stands in stark contrast to the slumped, drunken patrons surrounding him. His eyes don't wander aimlessly; they cut through the room in precise, rhythmic sweeps, tracking the door and the patrons with the mechanical intensity of a trained sentry.

You bridge the gap between the tables and reach out, your fingers clamping firmly around his wrist. The skin is calloused and lean. "Who are you really?" you demand, leaning into his space and tightening your grip. "And why are you watching this room like a soldier on watch?"

**Matthew Estrada** doesn't flinch. He doesn't even attempt to pull his arm away. Instead, he turns his head slowly to meet your gaze, his eyes cold and entirely unblinking. He looks less like a startled traveler and more like a predator deciding whether a nuisance is worth the effort of a kill. "A man can watch a room without being a soldier, traveler," he says, his voice a calm, low baritone that carries an unmistakable edge of authority. "But a man who grabs strangers by the wrist is usually looking for a fight he can't finish. Walk away while you still have the hands to do it."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Predator At The Bar",
  "location_change": {
    "id": "crossed_keys_inn_tavern",
    "name": "Crossed Keys Inn Tavern",
    "description": "A loud, crowded, and heat-filled room filled with drunken patrons and the smell of frothing ale."
  },
  "location_description": null,
  "npc_add": [
    {
      "id": "kathryn",
      "notes": "Currently in the service corridor, likely watching the service door.",
      "name": "Kathryn",
      "title": "Kitchen Worker",
      "bio": "A woman with sharp, avian features and a predatory glint in her eyes who carries a heavy iron ladle like a club."
    }
  ],
  "npc_remove": [
    {
      "id": "kathryn",
      "last_seen_state": "Standing in the service corridor with an iron ladle."
    }
  ],
  "npc_update": [
    {
      "id": "matthew_estrada",
      "notes": "Sitting at the bar, acting with mechanical intensity and a soldier-like vigilance; currently being confronted by Aren.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [
    {
      "id": "kathryn",
      "name": "Kathryn",
      "title": "Kitchen Worker",
      "bio": "A sharp-featured woman working in the kitchen of the Crossed Keys with a predatory demeanor.",
      "aliases": [],
      "allegiance": null
    }
  ],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "As Matthew Estrada stares you down, his hand subtly shifts beneath the table toward a concealed object, suggesting he is far more prepared for a confrontation than a mere traveler should be."
  }
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
  "recent_events_add": [
    {
      "id": "matthew_estrada_suspicion",
      "text": "Matthew Estrada displays the disciplined, watchful behavior of a trained soldier.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Press Matthew further to reveal his true identity and motives.'}",
    "{'description': 'Back down and observe Matthew from a distance for clues.'}",
    "{'description': \"Search the tavern for more information about Matthew's reputation.\"}",
    "{'description': \"Scan the room for any of Matthew's potential allies or contacts.\"}"
  ],
  "outcome_summary": "Your attempt to intimidate Matthew Estrada fails to rattle him; he remains calm and issues a chilling warning."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn_tavern",
    "name": "Crossed Keys Inn Tavern",
    "description": "A loud, crowded, and heat-filled room filled with drunken patrons and the smell of frothing ale."
  },
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Predator At The Bar",
  "compendium_npc_update": [
    {
      "id": "kathryn",
      "name": "Kathryn",
      "title": "Kitchen Worker",
      "bio": "A sharp-featured woman working in the kitchen of the Crossed Keys with a predatory demeanor.",
      "aliases": []
    }
  ],
  "npc_add": [
    {
      "id": "kathryn",
      "notes": "Currently in the service corridor, likely watching the service door.",
      "name": "Kathryn",
      "title": "Kitchen Worker",
      "bio": "A woman with sharp, avian features and a predatory glint in her eyes who carries a heavy iron ladle like a club."
    }
  ],
  "npc_remove": [
    {
      "id": "kathryn",
      "last_seen_state": "Standing in the service corridor with an iron ladle."
    }
  ],
  "npc_update": [
    {
      "id": "matthew_estrada",
      "notes": "Sitting at the bar, acting with mechanical intensity and a soldier-like vigilance; currently being confronted by Aren."
    }
  ],
  "recent_events_add": [
    {
      "id": "matthew_estrada_suspicion",
      "text": "Matthew Estrada displays the disciplined, watchful behavior of a trained soldier.",
      "turn": 0
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

- {'description': 'Press Matthew further to reveal his true identity and motives.'}

- {'description': 'Back down and observe Matthew from a distance for clues.'}

- {'description': "Search the tavern for more information about Matthew's reputation."}

- {'description': "Scan the room for any of Matthew's potential allies or contacts."}

### Context Telemetry

- rules: est=1292t trimmed=False
- narrate: est=6729t trimmed=False
- extract.scene: est=4281t trimmed=False attempts=1
- extract.state: est=2307t trimmed=False attempts=1
- extract.progress: est=2178t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "bald_tough": {
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 6
        }
      },
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrows_crossing",
          "location_name": "Marrow's Crossing",
          "turn": 2
        },
        "last_seen_state": "Sitting at a table in the Crossed Keys Inn, staring at a bag of coin with a predatory grin.",
        "name": "Caron",
        "title": "Old creditor"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "town_square",
          "location_name": "Town Square",
          "turn": 4
        },
        "last_seen_state": "Standing near the town well in the town square.",
        "name": "Halden",
        "title": "Merchant"
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys"
      },
      "kathryn": {
        "bio": "A sharp-featured woman working in the kitchen of the Crossed Keys with a predatory demeanor.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_tavern",
          "location_name": "Crossed Keys Inn Tavern",
          "turn": 11
        },
        "name": "Kathryn",
        "title": "Kitchen Worker"
      },
      "matthew_estrada": {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_tavern",
          "location_name": "Crossed Keys Inn Tavern",
          "turn": 11
        },
        "name": "Matthew Estrada",
        "title": "Traveler"
      },
      "scarred_tough": {
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 6
        }
      },
      "tough_a": {
        "bio": "A thick-set man with a broken nose who acts as a physical barrier for those entering the inn.",
        "last_seen_state": "Standing on the porch demanding a toll.",
        "name": "Bald Tough",
        "title": "Road Tough"
      },
      "tough_b": {
        "bio": "A wiry man with a jagged scar through his eyebrow, carrying a blackjack and acting as an enforcer for the road toll.",
        "last_seen_state": "Standing on the porch eyeing the ditches.",
        "name": "Scarred Tough",
        "title": "Road Tough"
      },
      "tyler": {
        "bio": "A large man in a stained leather jerkin with a menacing gaze and a heavy club at his hip.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 6
        },
        "last_seen_state": "Lurking in the roadside ditches outside the inn.",
        "name": "Tyler",
        "title": "Enforcer"
      }
    }
  },
  "inventory": [
    {
      "amount": 249,
      "id": "credits",
      "name": "Credits",
      "notes": "Payment from Halden for the ledger delivery."
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
    "description": "A loud, crowded, and heat-filled room filled with drunken patrons and the smell of frothing ale.",
    "id": "crossed_keys_inn_tavern",
    "name": "Crossed Keys Inn Tavern"
  },
  "meta": {
    "compendium_touch_order": [
      "tyler",
      "tough_a",
      "tough_b",
      "kathryn"
    ],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "As Matthew Estrada stares you down, his hand subtly shifts beneath the table toward a concealed object, suggesting he is far more prepared for a confrontation than a mere traveler should be.",
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
    "momentum": 1,
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
    },
    {
      "id": "deliver_ledger",
      "last_advanced_turn": 4,
      "objectives": [],
      "status": "active",
      "title": ""
    }
  ],
  "scene": {
    "location_entered_turn": 10,
    "present_npcs": [
      {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "id": "matthew_estrada",
        "name": "Matthew Estrada",
        "notes": "Sitting at the bar, acting with mechanical intensity and a soldier-like vigilance; currently being confronted by Aren.",
        "title": "Traveler"
      },
      {
        "bio": "A woman with sharp, avian features and a predatory glint in her eyes who carries a heavy iron ladle like a club.",
        "id": "kathryn",
        "name": "Kathryn",
        "notes": "Currently in the service corridor, likely watching the service door.",
        "title": "Kitchen Worker"
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
        "id": "caron_debt_demand",
        "text": "Caron refuses to negotiate and demands labor in lieu of coin.",
        "turn": 1
      },
      {
        "id": "tyler_appears",
        "text": "Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.",
        "turn": 2
      },
      {
        "id": "contract_accepted_halden",
        "text": "Halden has hired Voss to deliver the ledger for 200 credits.",
        "turn": 3
      },
      {
        "id": "tyler_stalking_voss",
        "text": "Tyler has begun following Voss from a distance, lurking in the roadside ditches.",
        "turn": 4
      },
      {
        "id": "inn_toll_confrontation",
        "text": "Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.",
        "turn": 5
      },
      {
        "id": "bribe_attempt_tension",
        "text": "The attempted bribe of the thugs has increased the tension on the inn steps.",
        "turn": 6
      },
      {
        "id": "mysterious_watcher_in_ditches",
        "text": "Halden warns that a suspicious man in a leather jerkin was watching Voss from the ditches.",
        "turn": 7
      },
      {
        "id": "entered_crossed_keys_service_corridor",
        "text": "You successfully unlocked and entered a side service corridor of the Crossed Keys Inn.",
        "turn": 8
      },
      {
        "id": "kathryn_confrontation",
        "text": "Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.",
        "turn": 9
      },
      {
        "id": "matthew_estrada_suspicion",
        "text": "Matthew Estrada displays the disciplined, watchful behavior of a trained soldier.",
        "turn": 10
      }
    ],
    "recently_left": [],
    "recently_left_turns": 0,
    "scene_pressure": [],
    "tagline": "A Predator At The Bar",
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
| 2 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 2: ['Caron refuses to negotiate and demands labor in lieu of coin.'] |
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Voss'] |
| 3 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 3: ['Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.'] |
| 4 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 4: ['Halden has hired Voss to deliver the ledger for 200 credits.'] |
| 6 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 6: ['Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.'] |
| 7 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 7: ['The attempted bribe of the thugs has increased the tension on the inn steps.'] |
| 10 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 10: ['Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.'] |
| 11 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 11: ['Matthew Estrada displays the disciplined, watchful behavior of a trained soldier.'] |
| 11 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Who', 'Instead', 'Walk'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1187 | 2787 | 3705 | 0 | 1737 | 0 | 0 |
| 3 | 1266 | 3301 | 0 | 2182 | 1934 | 0 | 0 |
| 4 | 1273 | 3598 | 4213 | 2213 | 2482 | 0 | 0 |
| 5 | 1274 | 4104 | 0 | 2181 | 2355 | 0 | 0 |
| 6 | 1276 | 4540 | 4086 | 2325 | 2234 | 0 | 0 |
| 7 | 1282 | 5180 | 0 | 2223 | 2236 | 0 | 0 |
| 8 | 1278 | 5597 | 0 | 2335 | 2482 | 0 | 0 |
| 9 | 1279 | 5982 | 4215 | 2234 | 2159 | 0 | 0 |
| 10 | 1286 | 6304 | 0 | 2403 | 2349 | 0 | 0 |
| 11 | 1292 | 6729 | 4281 | 2307 | 2178 | 0 | 0 |

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + progress | 6 | `- You arrived in Marrow's Crossing after three days on the r / - You heard rumors of road-toughs extorting travelers near t / - You found Caron in the tavern — he's been waiting for you.` |
| narrate + scene | 2 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |

## Compaction Features
*(compaction did not fire during this run — likely because the run was shorter than `compact_every`. Judge: do not score compaction capabilities for this run; note this in your verdict.)*
