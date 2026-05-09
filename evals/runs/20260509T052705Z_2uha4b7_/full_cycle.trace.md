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

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs

## CURRENT TURN NARRATION
You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.
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
negotiate: The player approaches Caron to discuss and potentially negotiate the settlement of their debt.
## CURRENT TURN NARRATION
You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player approaches Caron to discuss and potentially negotiate the settlement of their debt.",
  "rolled": true,
  "total_ms": 9505.9,
  "tokens_in": 1015,
  "tokens_out": 1124,
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
  "outcome_summary": "Your attempt to negotiate fails as Caron dismisses you with a cold ultimatum, demanding full payment by sunrise."
}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss and potentially negotiate the settlement of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "Failure to reach an agreement could lead to immediate debt collection, hostility, or loss of reputation.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "No Room For Negotiation",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "caron_debt_deadline",
      "text": "Caron demands the full debt amount by sunrise or consequences will follow.",
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
    "instruction": "As Caron reaches the top of the stairs, he pauses and glances back over his shoulder, his eyes scanning the tavern for any of the other toughs who might be lurking in the shadows to enforce his ultimatum."
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
      "id": "caron_ultimatum",
      "text": "Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Try to reason with Caron one last time before he leaves.'}",
    "{'text': 'Offer a partial payment now to buy more time.'}",
    "{'text': 'Follow Caron upstairs to demand a more private conversation.'}",
    "{'text': 'Scan the tavern for anyone who might help you find the coin.'}"
  ],
  "outcome_summary": "Your attempt to negotiate fails as Caron dismisses you with a cold ultimatum, demanding full payment by sunrise."
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
  "scene_tagline": "No Room For Negotiation",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs."
    }
  ],
  "recent_events_add": [
    {
      "id": "caron_ultimatum",
      "text": "Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "caron_debt_deadline",
      "text": "Caron demands the full debt amount by sunrise or consequences will follow.",
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

- {'text': 'Try to reason with Caron one last time before he leaves.'}

- {'text': 'Offer a partial payment now to buy more time.'}

- {'text': 'Follow Caron upstairs to demand a more private conversation.'}

- {'text': 'Scan the tavern for anyone who might help you find the coin.'}

### Context Telemetry

- rules: est=1187t trimmed=False
- narrate: est=2787t trimmed=False
- extract.scene: est=3678t trimmed=False attempts=1
- extract.state: skipped
- extract.progress: est=1716t trimmed=False attempts=1

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
      "instruction": "As Caron reaches the top of the stairs, he pauses and glances back over his shoulder, his eyes scanning the tavern for any of the other toughs who might be lurking in the shadows to enforce his ultimatum.",
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
        "notes": "Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs.",
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
        "id": "caron_ultimatum",
        "text": "Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.",
        "turn": 1
      }
    ],
    "scene_pressure": [
      {
        "id": "caron_debt_deadline",
        "max_turns": null,
        "text": "Caron demands the full debt amount by sunrise or consequences will follow.",
        "turn_added": 1,
        "urgency": "building"
      }
    ],
    "tagline": "No Room For Negotiation",
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
T2: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — … le." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.

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
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As Caron reaches the top of the stairs, he pauses and glances back over his shoulder, his eyes scanning the tavern for any of the other toughs who might be lurking in the shadows to enforce his ultimatum.
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
- Caron (Old creditor) — Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs.
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
recent_events, quest_updates, inventory

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
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
recent_events, quest_updates, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player attempts to settle their debt by paying 500 credits and requesting a ledger update.
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
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.

## items_gained
stained ledger

## items_lost
credits

## CURRENT TURN NARRATION
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to settle their debt by paying 500 credits and requesting a ledger update.",
  "rolled": false,
  "total_ms": 2441.0,
  "tokens_in": 1087,
  "tokens_out": 1177
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to settle their debt by paying 500 credits and requesting a ledger update.",
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

You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "stained_ledger",
      "name": "stained ledger",
      "notes": "A small, stained book used to track debts; Caron used it to record interest.",
      "amount": 1,
      "aliases": []
    }
  ],
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
  "recent_events_add": [
    {
      "id": "caron_partial_payment_refusal",
      "text": "Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Demand Caron show you the ledger to confirm the payment.'}",
    "{'description': 'Try to negotiate a more favorable payment plan for the principal.'}",
    "{'description': 'Confront the shadows near the hearth to see if they are threats.'}",
    "{'description': 'Leave the tavern quickly to find a way to earn more credits.'}"
  ],
  "outcome_summary": "Caron rejects the payment as full settlement, claiming it only covers the interest and leaving the principal debt unpaid."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "stained_ledger",
      "name": "stained ledger",
      "notes": "A small, stained book used to track debts; Caron used it to record interest.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 500
    }
  ],
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
  "recent_events_add": [
    {
      "id": "caron_partial_payment_refusal",
      "text": "Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.",
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

- {'description': 'Demand Caron show you the ledger to confirm the payment.'}

- {'description': 'Try to negotiate a more favorable payment plan for the principal.'}

- {'description': 'Confront the shadows near the hearth to see if they are threats.'}

- {'description': 'Leave the tavern quickly to find a way to earn more credits.'}

### Context Telemetry

- rules: est=1266t trimmed=False
- narrate: est=3276t trimmed=False
- extract.scene: skipped
- extract.state: est=2166t trimmed=False attempts=1
- extract.progress: est=2160t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "stained_ledger",
        "name": "stained ledger",
        "notes": "A small, stained book used to track debts; Caron used it to record interest."
      }
    ],
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
        "instruction": "As Caron reaches the top of the stairs, he pauses and glances back over his shoulder, his eyes scanning the tavern for any of the other toughs who might be lurking in the shadows to enforce his ultimatum.",
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
    "recent_events": {
      "added": [
        {
          "id": "caron_partial_payment_refusal",
          "text": "Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.",
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
T3: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — … al is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

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
- **stained ledger**: A small, stained book used to track debts; Caron used it to record interest.

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
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

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
- Caron (Old creditor) — Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs.
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
- `caron` | Caron (Old creditor) — Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `caron_debt_deadline` [building] Caron demands the full debt amount by sunrise or consequences will follow. (added turn 1)


## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T3 context)
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

## CURRENT TURN NARRATION
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | stained ledger ×1 — A small, stained book used to track debts; Caron used it to record interest.

## scene_result
location: `marrows_crossing`

## CURRENT TURN NARRATION
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: Voss offers to perform a delivery service for Halden in exchange for 200 credits.
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
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.

## prior_turn_narration (T2 — for outcome_summary and actions context)
You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.

## items_gained
credits

## CURRENT TURN NARRATION
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "Voss offers to perform a delivery service for Halden in exchange for 200 credits.",
  "rolled": false,
  "total_ms": 2721.1,
  "tokens_in": 1095,
  "tokens_out": 1202
}
```

**Raw LLM output:**
```
{
  "intent": "Voss offers to perform a delivery service for Halden in exchange for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "Halden may refuse the offer, leaving Voss without additional funds.",
  "check": {
    "required": false,
    "skill": "charisma",
    "difficulty": "trivial",
    "tags": []
  }
}
```

### Narration

You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue",
    "exploration"
  ],
  "scene_tagline": "A Steep Price For Delivery",
  "location_change": null,
  "location_description": "The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Descended two steps of the tavern stairs to sneer at the player before heading upstairs."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "opportunity",
    "surface_as": "event",
    "instruction": "As you turn toward the Crossed Keys Inn, you notice a pair of shadows detached from the tavern doorway\u2014the muscle Caron mentioned\u2014watching your exchange with Halden from the edge of the square."
  }
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "credits",
      "notes": "Payment from Halden for the ledger delivery",
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
      "text": "Halden has paid 200 credits to Voss for the ledger delivery.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Head straight to the Crossed Keys Inn with the ledger.'}",
    "{'text': \"Ask Halden for more information about the ledger's contents.\"}",
    "{'text': 'Try to charm Halden into increasing the delivery fee.'}",
    "{'text': 'Search the town square for any signs of the road-toughs.'}"
  ],
  "outcome_summary": "You successfully negotiated a 200 credit fee from Halden and accepted the contract to deliver his ledger."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "credits",
      "name": "credits",
      "notes": "Payment from Halden for the ledger delivery",
      "amount": 200,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square.",
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
    "dialogue",
    "exploration"
  ],
  "scene_tagline": "A Steep Price For Delivery",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Descended two steps of the tavern stairs to sneer at the player before heading upstairs."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn."
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_contract_accepted",
      "text": "Halden has paid 200 credits to Voss for the ledger delivery.",
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

- {'text': 'Head straight to the Crossed Keys Inn with the ledger.'}

- {'text': "Ask Halden for more information about the ledger's contents."}

- {'text': 'Try to charm Halden into increasing the delivery fee.'}

- {'text': 'Search the town square for any signs of the road-toughs.'}

### Context Telemetry

- rules: est=1273t trimmed=False
- narrate: est=3588t trimmed=False
- extract.scene: est=4131t trimmed=False attempts=1
- extract.state: est=2276t trimmed=False attempts=1
- extract.progress: est=2546t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "last_seen_state": {
          "from": null,
          "to": "Descended two steps of the tavern stairs to sneer at the player before heading upstairs."
        }
      },
      "halden": {
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
        "amount": 200,
        "id": "credits",
        "name": "credits",
        "notes": "Payment from Halden for the ledger delivery"
      }
    ]
  },
  "location": {
    "description": {
      "from": "A market town built around the confluence of two rivers. Cobblestone streets,\ntimber-framed buildings, and the constant sound of water from the mills. The\ntown square has a stone well and a statue of the founder. Most shops are closing\nfor the evening.\n",
      "to": "The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square."
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As you turn toward the Crossed Keys Inn, you notice a pair of shadows detached from the tavern doorway\u2014the muscle Caron mentioned\u2014watching your exchange with Halden from the edge of the square.",
        "surface_as": "event",
        "type": "opportunity"
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
    "present_npcs": {
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Hostile and dismissive; has issued a hard deadline for the debt by sunrise and is heading upstairs.",
          "title": "Old creditor"
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
            "notes": "Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn.",
            "title": "Merchant"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_contract_accepted",
          "text": "Halden has paid 200 credits to Voss for the ledger delivery.",
          "turn": 3
        }
      ]
    },
    "recently_left": {
      "from": null,
      "to": [
        {
          "id": "caron",
          "name": "Caron",
          "title": "Old creditor"
        }
      ]
    },
    "recently_left_turns": {
      "from": null,
      "to": 1
    },
    "tagline": {
      "from": "No Room For Negotiation",
      "to": "A Steep Price For Delivery"
    },
    "tags": {
      "added": [
        "exploration"
      ],
      "removed": []
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
T4: I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. — … ke it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."

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
The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square.

## Recently Left (do NOT write dialogue or action for these — may briefly acknowledge their departure)
- Caron (Old creditor)
## Inventory
- **credits** ×200: Payment from Halden for the ledger delivery
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **stained ledger**: A small, stained book used to track debts; Caron used it to record interest.

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
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."

GM DIRECTION (OPPORTUNITY, surface as event):
As you turn toward the Crossed Keys Inn, you notice a pair of shadows detached from the tavern doorway—the muscle Caron mentioned—watching your exchange with Halden from the edge of the square.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
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
- `credits` | credits ×200 — Payment from Halden for the ledger delivery
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | stained ledger ×1 — A small, stained book used to track debts; Caron used it to record interest.

## scene_result
location: `marrows_crossing`

## CURRENT TURN NARRATION
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.
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
travel: The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.

## prior_turn_narration (T3 — for outcome_summary and actions context)
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

## CURRENT TURN NARRATION
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.
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
  "total_ms": 2360.4,
  "tokens_in": 1092,
  "tokens_out": 1177
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

You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "credits",
      "name": null,
      "notes": null
    }
  ],
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
      "id": "caron_enforcers_spotted",
      "text": "Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Speed up your pace toward the Crossed Keys Inn.', 'type': 'exploration'}",
    "{'description': 'Try to find a shortcut to avoid the main road.', 'type': 'exploration'}",
    "{'description': 'Look back to see if the men are following you.', 'type': 'exploration'}",
    "{'description': \"Search for more information about Caron's men in the town.\", 'type': 'quest'}"
  ],
  "outcome_summary": "You leave Marrow's Crossing under the watchful, unsettling eyes of Caron's enforcers as you head toward the inn."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "credits"
    }
  ],
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
      "id": "caron_enforcers_spotted",
      "text": "Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.",
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

- {'description': 'Speed up your pace toward the Crossed Keys Inn.', 'type': 'exploration'}

- {'description': 'Try to find a shortcut to avoid the main road.', 'type': 'exploration'}

- {'description': 'Look back to see if the men are following you.', 'type': 'exploration'}

- {'description': "Search for more information about Caron's men in the town.", 'type': 'quest'}

### Context Telemetry

- rules: est=1276t trimmed=False
- narrate: est=4107t trimmed=False
- extract.scene: skipped
- extract.state: est=2204t trimmed=False attempts=1
- extract.progress: est=2346t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As you turn toward the Crossed Keys Inn, you notice a pair of shadows detached from the tavern doorway\u2014the muscle Caron mentioned\u2014watching your exchange with Halden from the edge of the square.",
        "surface_as": "event",
        "type": "opportunity"
      },
      "to": null
    },
    "turn": {
      "from": 4,
      "to": 5
    }
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "caron_enforcers_spotted",
          "text": "Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.",
          "turn": 4
        }
      ]
    },
    "recently_left": {
      "removed": [
        {
          "id": "caron",
          "name": "Caron",
          "title": "Old creditor"
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
Location: Marrow's Crossing
## last_turn (tail of the most recent narrative)
T5: I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. — … f the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

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
Marrow's Crossing (marrows_crossing)
The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square.

## Inventory
- **credits** ×200: Payment from Halden for the ledger delivery
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **stained ledger**: A small, stained book used to track debts; Caron used it to record interest.

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
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.
- Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 5 + 1 +1 (stat) = 7 → SETBACK
Directive: The persuade results in a setback. They're listening, but now they want something in return.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

## Narration Directive







## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
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
`marrows_crossing` | Marrow's Crossing
The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `caron_debt_deadline` [building] Caron demands the full debt amount by sunrise or consequences will follow. (added turn 1)


⚠ Quest "Settle the Old Debt" stalled for 4 turns.

⚠ Quest "Deliver Halden's Ledger" stalled for 3 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T5 context)
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

## CURRENT TURN NARRATION
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."
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
- `credits` | credits ×200 — Payment from Halden for the ledger delivery
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | stained ledger ×1 — A small, stained book used to track debts; Caron used it to record interest.

## scene_result
location: `tavern_entrance`
(location changed)
## CURRENT TURN NARRATION
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."
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
persuade: Confront the two men at the inn door to demand an explanation for their presence.
## prior_turn_narration (T4 — for outcome_summary and actions context)
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."

## CURRENT TURN NARRATION
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "Confront the two men at the inn door to demand an explanation for their presence.",
  "rolled": true,
  "total_ms": 2673.8,
  "tokens_in": 1092,
  "tokens_out": 1196,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    5,
    1
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 7,
  "band": "setback",
  "outcome_summary": "Your attempt to demand an explanation fails as the thugs turn the conversation into a blatant extortion attempt, flanking you to cut off your escape."
}
```

**Raw LLM output:**
```
{
  "intent": "Confront the two men at the inn door to demand an explanation for their presence.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "Physical altercation or being denied entry to the inn.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."

### Extract Scene

```json
{
  "scene_tags": [
    "combat"
  ],
  "scene_tagline": "A Toll For The Road",
  "location_change": {
    "id": "tavern_entrance",
    "name": "Crossed Keys Entrance",
    "description": "The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile."
  },
  "location_description": null,
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Standing by the stone well in the town square."
    },
    {
      "id": "innkeeper",
      "last_seen_state": "Wiping down the bar inside the Crossed Keys."
    }
  ],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Flanking the player to cut off their retreat toward the town center.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "tough_b",
      "notes": "Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "tough_extortion",
      "text": "The Bald Tough and Scarred Tough are demanding a toll and eyeing the ledger.",
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
    "instruction": "As the Bald Tough begins his flanking maneuver, the Scarred Tough reaches into his tunic, his hand hovering near a concealed weapon to signal that the 'toll' conversation is rapidly transitioning into a physical confrontation."
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
  "quest_updates": [
    {
      "id": "deliver_stained_ledger",
      "title": "Deliver the Stained Ledger",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "description": null,
          "done": false,
          "failed": null
        }
      ]
    }
  ],
  "recent_events_add": [
    {
      "id": "toll_extortion_attempt",
      "text": "Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Offer them a portion of your credits to let you pass.'}",
    "{'description': 'Draw your iron dagger and prepare for a physical confrontation.'}",
    "{'description': 'Try to intimidate them into revealing their true intentions for the ledger.'}",
    "{'description': 'Attempt to slip past the Bald Tough toward the town center.'}"
  ],
  "outcome_summary": "Your attempt to demand an explanation fails as the thugs turn the conversation into a blatant extortion attempt, flanking you to cut off your escape."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "tavern_entrance",
    "name": "Crossed Keys Entrance",
    "description": "The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile."
  },
  "quest_updates": [
    {
      "id": "deliver_stained_ledger",
      "title": "Deliver the Stained Ledger",
      "status": "active",
      "objectives": [
        {
          "index": 1,
          "done": false
        }
      ]
    }
  ],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "combat"
  ],
  "scene_tagline": "A Toll For The Road",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Standing by the stone well in the town square."
    },
    {
      "id": "innkeeper",
      "last_seen_state": "Wiping down the bar inside the Crossed Keys."
    }
  ],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Flanking the player to cut off their retreat toward the town center."
    },
    {
      "id": "tough_b",
      "notes": "Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger."
    }
  ],
  "recent_events_add": [
    {
      "id": "toll_extortion_attempt",
      "text": "Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "tough_extortion",
      "text": "The Bald Tough and Scarred Tough are demanding a toll and eyeing the ledger.",
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

- {'description': 'Offer them a portion of your credits to let you pass.'}

- {'description': 'Draw your iron dagger and prepare for a physical confrontation.'}

- {'description': 'Try to intimidate them into revealing their true intentions for the ledger.'}

- {'description': 'Attempt to slip past the Bald Tough toward the town center.'}

### Context Telemetry

- rules: est=1278t trimmed=False
- narrate: est=4518t trimmed=False
- extract.scene: est=4252t trimmed=False attempts=1
- extract.state: est=2411t trimmed=False attempts=1
- extract.progress: est=2251t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen_state": {
          "from": null,
          "to": "Standing by the stone well in the town square."
        }
      },
      "innkeeper": {
        "last_seen_state": {
          "from": null,
          "to": "Wiping down the bar inside the Crossed Keys."
        }
      },
      "tough_a": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "tavern_entrance",
            "location_name": "Crossed Keys Entrance",
            "turn": 6
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "tavern_entrance",
            "location_name": "Crossed Keys Entrance",
            "turn": 6
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The evening air has cooled, and the rhythmic thud of the mill wheel and the rush of the river provide a steady backdrop to the quiet town square.",
      "to": "The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile."
    },
    "id": {
      "from": "marrows_crossing",
      "to": "tavern_entrance"
    },
    "name": {
      "from": "Marrow's Crossing",
      "to": "Crossed Keys Entrance"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As the Bald Tough begins his flanking maneuver, the Scarred Tough reaches into his tunic, his hand hovering near a concealed weapon to signal that the 'toll' conversation is rapidly transitioning into a physical confrontation.",
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
  "quests": {
    "added": [
      {
        "id": "deliver_stained_ledger",
        "last_advanced_turn": 5,
        "objectives": [],
        "status": "active",
        "title": "Deliver the Stained Ledger"
      }
    ]
  },
  "scene": {
    "location_entered_turn": {
      "from": null,
      "to": 5
    },
    "present_npcs": {
      "added": [
        {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Flanking the player to cut off their retreat toward the town center.",
          "title": "Road thug"
        },
        {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.",
          "title": "Road thug"
        }
      ],
      "removed": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Standing by the stone well, has just paid the player 200 credits to deliver a stained ledger to the Crossed Keys Inn.",
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
    "recent_events": {
      "added": [
        {
          "id": "toll_extortion_attempt",
          "text": "Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.",
          "turn": 5
        }
      ]
    },
    "recently_left_turns": {
      "from": 1,
      "to": 0
    },
    "scene_pressure": {
      "added": [
        {
          "id": "tough_extortion",
          "max_turns": null,
          "text": "The Bald Tough and Scarred Tough are demanding a toll and eyeing the ledger.",
          "turn_added": 5,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "A Steep Price For Delivery",
      "to": "A Toll For The Road"
    },
    "tags": {
      "added": [
        "combat"
      ],
      "removed": [
        "dialogue",
        "exploration"
      ]
    },
    "turn_entered": {
      "from": null,
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
Location: Crossed Keys Entrance
## last_turn (tail of the most recent narrative)
T6: I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. — … s his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."

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
Crossed Keys Entrance (tavern_entrance)
The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile.

## Inventory
- **credits** ×200: Payment from Halden for the ledger delivery
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **stained ledger**: A small, stained book used to track debts; Caron used it to record interest.

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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
- [IMMEDIATE] The Bald Tough and Scarred Tough are demanding a toll and eyeing the ledger.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.
- Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.
- Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 6 + 1 +1 (stat) = 8 → PARTIAL
Directive: The persuade results in a partial. You get what you asked for, but they now hold leverage over you.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As the Bald Tough begins his flanking maneuver, the Scarred Tough reaches into his tunic, his hand hovering near a concealed weapon to signal that the 'toll' conversation is rapidly transitioning into a physical confrontation.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Entrance
- **Scarred Tough** — last seen Crossed Keys Entrance
## NPCs Present in Scene
- Bald Tough (Road thug) — Flanking the player to cut off their retreat toward the town center.
- Scarred Tough (Road thug) — Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.
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

## rules_outcome
PARTIAL on charisma. The persuade results in a partial. You get what you asked for, but they now hold leverage over you.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: partial
directive: The persuade results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | credits ×200 — Payment from Halden for the ledger delivery
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | stained ledger ×1 — A small, stained book used to track debts; Caron used it to record interest.

## scene_result
location: `tavern_entrance`

## CURRENT TURN NARRATION
You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
inventory

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to bribe the toughs with 200 credits to convince them to leave.
## prior_turn_narration (T5 — for outcome_summary and actions context)
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

## items_lost
credits

## CURRENT TURN NARRATION
You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe the toughs with 200 credits to convince them to leave.",
  "rolled": true,
  "total_ms": 2794.3,
  "tokens_in": 1099,
  "tokens_out": 1211,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    6,
    1
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 8,
  "band": "partial",
  "outcome_summary": "Your attempt to bribe the thugs fails as they realize you are carrying more than just the initial payment, escalating the confrontation into a direct extortion attempt."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the toughs with 200 credits to convince them to leave.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "The toughs may refuse the bribe and turn violent or demand more money.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

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
  "pc_condition_add": [
    {
      "id": "compromised",
      "label": "compromised",
      "description": "The thugs now know you possess the ledger and have more wealth, giving them leverage over you."
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
      "id": "tough_extortion_attempt",
      "text": "Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.",
      "turn": 1
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Try to intimidate them into backing down without more coin.'}",
    "{'description': 'Offer more credits to de-escalate the situation immediately.'}",
    "{'description': 'Draw a weapon and prepare for a physical confrontation.'}",
    "{'description': 'Attempt to flee toward the safety of the town gate.'}"
  ],
  "outcome_summary": "Your attempt to bribe the thugs fails as they realize you are carrying more than just the initial payment, escalating the confrontation into a direct extortion attempt."
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
  "pc_condition_add": [
    {
      "id": "compromised",
      "label": "compromised",
      "description": "The thugs now know you possess the ledger and have more wealth, giving them leverage over you."
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [],
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "tough_extortion_attempt",
      "text": "Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.",
      "turn": 1
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "tough_extortion"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'description': 'Try to intimidate them into backing down without more coin.'}

- {'description': 'Offer more credits to de-escalate the situation immediately.'}

- {'description': 'Draw a weapon and prepare for a physical confrontation.'}

- {'description': 'Attempt to flee toward the safety of the town gate.'}

### Context Telemetry

- rules: est=1280t trimmed=False
- narrate: est=5259t trimmed=False
- extract.scene: skipped
- extract.state: est=2329t trimmed=False attempts=1
- extract.progress: est=2182t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "removed": [
      {
        "amount": 200,
        "id": "credits",
        "name": "credits",
        "notes": "Payment from Halden for the ledger delivery"
      }
    ]
  },
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As the Bald Tough begins his flanking maneuver, the Scarred Tough reaches into his tunic, his hand hovering near a concealed weapon to signal that the 'toll' conversation is rapidly transitioning into a physical confrontation.",
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
  "pc": {
    "conditions": {
      "added": [
        {
          "added_turn": 6,
          "description": "The thugs now know you possess the ledger and have more wealth, giving them leverage over you.",
          "id": "compromised",
          "label": "compromised"
        }
      ]
    }
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "tough_extortion_attempt",
          "text": "Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.",
          "turn": 1
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "tough_extortion",
          "max_turns": null,
          "text": "The Bald Tough and Scarred Tough are demanding a toll and eyeing the ledger.",
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
Conditions: bruised ribs, low morale, compromised

## scene
Location: Crossed Keys Entrance
## last_turn (tail of the most recent narrative)
T7: I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. — … de. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

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
Conditions: bruised ribs, low morale, compromised

## Location
Crossed Keys Entrance (tavern_entrance)
The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **stained ledger**: A small, stained book used to track debts; Caron used it to record interest.

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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.
- Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.
- Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 4 + 6 +1 (stat) = 11 → SUCCESS
Directive: The persuade succeeds cleanly. Clean success — you do what you intended.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Entrance
- **Scarred Tough** — last seen Crossed Keys Entrance
## NPCs Present in Scene
- Bald Tough (Road thug) — Flanking the player to cut off their retreat toward the town center.
- Scarred Tough (Road thug) — Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.
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
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | stained ledger ×1 — A small, stained book used to track debts; Caron used it to record interest.

## scene_result
location: `tavern_entrance`

## CURRENT TURN NARRATION
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
inventory, quest_updates

## rules_outcome
SUCCESS on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to use the merchant seal and ledger to prove their legitimacy and settle the dispute with Halden.
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
- `deliver_stained_ledger` | Deliver the Stained Ledger
  objectives:

## prior_turn_narration (T6 — for outcome_summary and actions context)
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."

## items_gained
leather pouch

## items_lost
stained_ledger

## CURRENT TURN NARRATION
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to use the merchant seal and ledger to prove their legitimacy and settle the dispute with Halden.",
  "rolled": true,
  "total_ms": 2911.6,
  "tokens_in": 1098,
  "tokens_out": 1216,
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
  "outcome_summary": "You successfully present the ledger and seal to Halden, earning his trust and receiving your promised payment pouch."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the merchant seal and ledger to prove their legitimacy and settle the dispute with Halden.",
  "intent_verb": "persuade",
  "target": "Halden",
  "stakes": "If the persuasion fails, the toughs may refuse the payment and demand more credits or escalate the confrontation.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "leather_pouch",
      "name": "leather pouch",
      "notes": "Halden's promised payment",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "stained_ledger",
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
      "id": "ledger_delivered_successfully",
      "text": "You successfully delivered the stained ledger and merchant seal to Halden.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Ask Halden for more information regarding the road toughs.', 'type': 'quest_related'}",
    "{'description': \"Request Halden's help in dealing with the thugs outside.\", 'type': 'npc_interaction'}",
    "{'description': 'Collect your payment and head back out into the night.', 'type': 'freeform'}",
    "{'description': 'Search the inn for rumors about who hired the toughs.', 'type': 'exploration'}"
  ],
  "outcome_summary": "You successfully present the ledger and seal to Halden, earning his trust and receiving your promised payment pouch."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "leather_pouch",
      "name": "leather pouch",
      "notes": "Halden's promised payment",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "stained_ledger",
      "amount": 1
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
  "recent_events_add": [
    {
      "id": "ledger_delivered_successfully",
      "text": "You successfully delivered the stained ledger and merchant seal to Halden.",
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

- {'description': 'Ask Halden for more information regarding the road toughs.', 'type': 'quest_related'}

- {'description': "Request Halden's help in dealing with the thugs outside.", 'type': 'npc_interaction'}

- {'description': 'Collect your payment and head back out into the night.', 'type': 'freeform'}

- {'description': 'Search the inn for rumors about who hired the toughs.', 'type': 'exploration'}

### Context Telemetry

- rules: est=1280t trimmed=False
- narrate: est=5565t trimmed=False
- extract.scene: skipped
- extract.state: est=2271t trimmed=False attempts=1
- extract.progress: est=2539t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "leather_pouch",
        "name": "leather pouch",
        "notes": "Halden's promised payment"
      }
    ],
    "removed": [
      {
        "amount": 1,
        "id": "stained_ledger",
        "name": "stained ledger",
        "notes": "A small, stained book used to track debts; Caron used it to record interest."
      }
    ]
  },
  "meta": {
    "turn": {
      "from": 7,
      "to": 8
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
    "recent_events": {
      "added": [
        {
          "id": "ledger_delivered_successfully",
          "text": "You successfully delivered the stained ledger and merchant seal to Halden.",
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
Conditions: bruised ribs, low morale, compromised

## scene
Location: Crossed Keys Entrance
## last_turn (tail of the most recent narrative)
T8: I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. — … ressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

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
Conditions: bruised ribs, low morale, compromised

## Location
Crossed Keys Entrance (tavern_entrance)
The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather pouch**: Halden's promised payment

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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Caron demands the full debt amount by sunrise or consequences will follow.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.
- Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.
- Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.
- You successfully delivered the stained ledger and merchant seal to Halden.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: easy
Roll: 5 + 3 +1 (stat) +1 (diff) = 10 → SUCCESS
Directive: The hack succeeds cleanly. Clean success — you do what you intended.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Marrow's Crossing
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Entrance
- **Scarred Tough** — last seen Crossed Keys Entrance
## NPCs Present in Scene
- Bald Tough (Road thug) — Flanking the player to cut off their retreat toward the town center.
- Scarred Tough (Road thug) — Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.
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
Conditions: bruised ribs, low morale, compromised

## location
`tavern_entrance` | Crossed Keys Entrance
The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | Bald Tough (Road thug) — Flanking the player to cut off their retreat toward the town center.
- `tough_b` | Scarred Tough (Road thug) — Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `caron_debt_deadline` [building] Caron demands the full debt amount by sunrise or consequences will follow. (added turn 1)

## deescalate
true — player succeeded on a check against active pressure. Do NOT add new pressures. Downgrade or remove existing ones.

⚠ Quest "Settle the Old Debt" stalled for 7 turns.

⚠ Quest "Deliver the Stained Ledger" stalled for 4 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_stained_ledger` | Deliver the Stained Ledger



## previous_turn_narration (T8 context)
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

## CURRENT TURN NARRATION
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.
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
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_pouch` | leather pouch ×1 — Halden's promised payment

## scene_result
location: `inn_service_corridor`
(location changed)
## CURRENT TURN NARRATION
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.
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
hack: The player attempts to use a brass key to unlock the inn's front door or find a back room.
## prior_turn_narration (T7 — for outcome_summary and actions context)
You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

## CURRENT TURN NARRATION
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "hack",
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find a back room.",
  "rolled": true,
  "total_ms": 2930.4,
  "tokens_in": 1087,
  "tokens_out": 1206,
  "skill": "dexterity",
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
  "outcome_summary": "You successfully used the brass key to unlock the side door and slip into the quiet service corridor, leaving the thugs behind."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find a back room.",
  "intent_verb": "hack",
  "target": "inn's front door/back room",
  "stakes": "Getting locked out of the inn or triggering an alarm/noise that alerts others.",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.

### Extract Scene

```json
{
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Quiet Corridor Escape",
  "location_change": {
    "id": "inn_service_corridor",
    "name": "Inn Service Corridor",
    "description": "A narrow, dimly lit passage smelling of dried herbs and floor wax, providing a quiet refuge from the tavern's main room."
  },
  "location_description": "The atmosphere shifts from the loud, ale-scented chaos of the taproom to a cool, quiet, and functional service corridor.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Loitering near the front entrance of the tavern."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Loitering near the front entrance of the tavern."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Sitting at a corner table, preoccupied with verifying the stained ledger and accounts.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "caron_debt_deadline"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "surface_as": "ambient",
    "instruction": "As you move deeper into the service corridor, you notice a discarded scrap of parchment wedged between the floorboards, bearing a partial seal that matches the one on the ledger you just delivered."
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
      "id": "entered_service_corridor",
      "text": "You successfully unlocked and entered the inn's side service corridor, escaping the thugs outside.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Search the service corridor for a more private room.'}",
    "{'description': 'Head toward the main taproom to find Halden again.'}",
    "{'description': 'Call out to Halden to warn him about the thugs.'}",
    "{'description': 'Check the corridor for any hidden exits or supplies.'}"
  ],
  "outcome_summary": "You successfully used the brass key to unlock the side door and slip into the quiet service corridor, leaving the thugs behind."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "inn_service_corridor",
    "name": "Inn Service Corridor",
    "description": "A narrow, dimly lit passage smelling of dried herbs and floor wax, providing a quiet refuge from the tavern's main room."
  },
  "location_description": "The atmosphere shifts from the loud, ale-scented chaos of the taproom to a cool, quiet, and functional service corridor.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Quiet Corridor Escape",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Loitering near the front entrance of the tavern."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Loitering near the front entrance of the tavern."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Sitting at a corner table, preoccupied with verifying the stained ledger and accounts."
    }
  ],
  "recent_events_add": [
    {
      "id": "entered_service_corridor",
      "text": "You successfully unlocked and entered the inn's side service corridor, escaping the thugs outside.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "caron_debt_deadline"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- {'description': 'Search the service corridor for a more private room.'}

- {'description': 'Head toward the main taproom to find Halden again.'}

- {'description': 'Call out to Halden to warn him about the thugs.'}

- {'description': 'Check the corridor for any hidden exits or supplies.'}

### Context Telemetry

- rules: est=1282t trimmed=False
- narrate: est=5991t trimmed=False
- extract.scene: est=4196t trimmed=False attempts=1
- extract.state: est=2252t trimmed=False attempts=1
- extract.progress: est=2187t trimmed=False attempts=1

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
            "to": "Standing by the stone well in the town square."
          },
          "location_id": {
            "from": "marrows_crossing",
            "to": "inn_service_corridor"
          },
          "location_name": {
            "from": "Marrow's Crossing",
            "to": "Inn Service Corridor"
          },
          "turn": {
            "from": 4,
            "to": 9
          }
        }
      },
      "tough_a": {
        "last_seen_state": {
          "from": null,
          "to": "Loitering near the front entrance of the tavern."
        }
      },
      "tough_b": {
        "last_seen_state": {
          "from": null,
          "to": "Loitering near the front entrance of the tavern."
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The flickering amber glow of the tavern doorway casts long, dancing shadows against the cobblestones as the atmosphere turns hostile.",
      "to": "A narrow, dimly lit passage smelling of dried herbs and floor wax, providing a quiet refuge from the tavern's main room."
    },
    "id": {
      "from": "tavern_entrance",
      "to": "inn_service_corridor"
    },
    "name": {
      "from": "Crossed Keys Entrance",
      "to": "Inn Service Corridor"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As you move deeper into the service corridor, you notice a discarded scrap of parchment wedged between the floorboards, bearing a partial seal that matches the one on the ledger you just delivered.",
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
      "from": -1,
      "to": 0
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 5,
      "to": 8
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Sitting at a corner table, preoccupied with verifying the stained ledger and accounts.",
          "title": "Merchant"
        }
      ],
      "removed": [
        {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Flanking the player to cut off their retreat toward the town center.",
          "title": "Road thug"
        },
        {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Leaning against the doorframe, encroaching on the player's personal space and eyeing their dagger.",
          "title": "Road thug"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "entered_service_corridor",
          "text": "You successfully unlocked and entered the inn's side service corridor, escaping the thugs outside.",
          "turn": 8
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "caron_debt_deadline",
          "max_turns": null,
          "text": "Caron demands the full debt amount by sunrise or consequences will follow.",
          "turn_added": 1,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "A Toll For The Road",
      "to": "Quiet Corridor Escape"
    },
    "tags": {
      "added": [
        "exploration"
      ],
      "removed": [
        "combat"
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
Conditions: bruised ribs, low morale, compromised

## scene
Location: Inn Service Corridor
## last_turn (tail of the most recent narrative)
T9: I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. — … sure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.

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
Conditions: bruised ribs, low morale, compromised

## Location
Inn Service Corridor (inn_service_corridor)
A narrow, dimly lit passage smelling of dried herbs and floor wax, providing a quiet refuge from the tavern's main room.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **leather pouch**: Halden's promised payment

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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.
- Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.
- Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.
- You successfully delivered the stained ledger and merchant seal to Halden.
- You successfully unlocked and entered the inn's side service corridor, escaping the thugs outside.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair across from **Caron**, the screech of legs against the floorboards drawing a few eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time.

"You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms.

He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms.


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe.

**Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger.

"You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity.

"The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal.

"Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens."


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center.

As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity.

You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you.


## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous.

"What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things."

The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**.

"Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger."

The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home."

The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape.

The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one."

The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 3 + 2 +1 (stat) = 6 → FAIL
Directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.

GM DIRECTION (REVELATION, surface as ambient):
As you move deeper into the service corridor, you notice a discarded scrap of parchment wedged between the floorboards, bearing a partial seal that matches the one on the ledger you just delivered.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Inn Service Corridor: Standing by the stone well in the town square.
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Entrance
- **Scarred Tough** — last seen Crossed Keys Entrance
## NPCs Present in Scene
- Halden (Merchant) — Sitting at a corner table, preoccupied with verifying the stained ledger and accounts.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
FAIL on charisma — The persuade fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, compromised

## location
`inn_service_corridor` | Inn Service Corridor
A narrow, dimly lit passage smelling of dried herbs and floor wax, providing a quiet refuge from the tavern's main room.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Sitting at a corner table, preoccupied with verifying the stained ledger and accounts.

_(immutable section omitted — see Static Context > Seed State)_

⚠ Quest "Settle the Old Debt" stalled for 8 turns.

⚠ Quest "Deliver Halden's Ledger" stalled for 3 turns.

⚠ Quest "Deliver the Stained Ledger" stalled for 5 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_stained_ledger` | Deliver the Stained Ledger



## previous_turn_narration (T9 context)
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.

## CURRENT TURN NARRATION
You press your ear against the cold, damp stone of the service corridor wall, straining to hear anything beyond the muffled roar of the tavern on the other side. Your voice comes out as a frantic, low whisper. "I have credits. Open up." To drive the point home, you pull a single coin from your pouch and press it against the masonry, the metal clinking hollowly against the stone.

The response is not a voice or a door opening, but a heavy, rhythmic thud from the other side of the wall—the sound of a boot striking wood or stone. A moment later, a harsh, mocking laugh echoes through the corridor, muffled by the thick building materials. There is no one coming to assist you; the wall offers no warmth and no greeting.

As you pull away from the stone, your eyes catch a sliver of something wedged deep between two uneven floorboards near the base of the wall. You kneel, your fingers brushing against a discarded scrap of parchment. It is crumpled and stained, but as you smooth it out, you recognize a partial, faded wax seal. It is a near-perfect match for the merchant seal you just handed to **Halden**, suggesting a connection between the ledger's contents and something hidden here in the shadows of the service passage.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
scene, inventory

## rules_outcome
FAIL on charisma. The persuade fails. The attempt fails outright — what you tried to do does not happen.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: fail
directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `leather_pouch` | leather pouch ×1 — Halden's promised payment

## scene_result
location: `inn_service_corridor`

## CURRENT TURN NARRATION
You press your ear against the cold, damp stone of the service corridor wall, straining to hear anything beyond the muffled roar of the tavern on the other side. Your voice comes out as a frantic, low whisper. "I have credits. Open up." To drive the point home, you pull a single coin from your pouch and press it against the masonry, the metal clinking hollowly against the stone.

The response is not a voice or a door opening, but a heavy, rhythmic thud from the other side of the wall—the sound of a boot striking wood or stone. A moment later, a harsh, mocking laugh echoes through the corridor, muffled by the thick building materials. There is no one coming to assist you; the wall offers no warmth and no greeting.

As you pull away from the stone, your eyes catch a sliver of something wedged deep between two uneven floorboards near the base of the wall. You kneel, your fingers brushing against a discarded scrap of parchment. It is crumpled and stained, but as you smooth it out, you recognize a partial, faded wax seal. It is a near-perfect match for the merchant seal you just handed to **Halden**, suggesting a connection between the ledger's contents and something hidden here in the shadows of the service passage.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
scene, inventory

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to bribe or persuade someone on the other side of the wall using a single credit.
## prior_turn_narration (T8 — for outcome_summary and actions context)
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

## items_gained
stained parchment

## items_lost
leather_pouch

## CURRENT TURN NARRATION
You press your ear against the cold, damp stone of the service corridor wall, straining to hear anything beyond the muffled roar of the tavern on the other side. Your voice comes out as a frantic, low whisper. "I have credits. Open up." To drive the point home, you pull a single coin from your pouch and press it against the masonry, the metal clinking hollowly against the stone.

The response is not a voice or a door opening, but a heavy, rhythmic thud from the other side of the wall—the sound of a boot striking wood or stone. A moment later, a harsh, mocking laugh echoes through the corridor, muffled by the thick building materials. There is no one coming to assist you; the wall offers no warmth and no greeting.

As you pull away from the stone, your eyes catch a sliver of something wedged deep between two uneven floorboards near the base of the wall. You kneel, your fingers brushing against a discarded scrap of parchment. It is crumpled and stained, but as you smooth it out, you recognize a partial, faded wax seal. It is a near-perfect match for the merchant seal you just handed to **Halden**, suggesting a connection between the ledger's contents and something hidden here in the shadows of the service passage.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe or persuade someone on the other side of the wall using a single credit.",
  "rolled": true,
  "total_ms": 2892.5,
  "tokens_in": 1094,
  "tokens_out": 1211,
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
  "outcome_summary": "Your attempt to bribe your way through the wall fails, met only by mocking laughter, but you discover a scrap of parchment bearing a familiar merchant seal."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe or persuade someone on the other side of the wall using a single credit.",
  "intent_verb": "persuade",
  "target": "unknown person behind the wall",
  "stakes": "The player may be discovered or ignored, potentially alerting staff to their presence in a restricted corridor.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You press your ear against the cold, damp stone of the service corridor wall, straining to hear anything beyond the muffled roar of the tavern on the other side. Your voice comes out as a frantic, low whisper. "I have credits. Open up." To drive the point home, you pull a single coin from your pouch and press it against the masonry, the metal clinking hollowly against the stone.

The response is not a voice or a door opening, but a heavy, rhythmic thud from the other side of the wall—the sound of a boot striking wood or stone. A moment later, a harsh, mocking laugh echoes through the corridor, muffled by the thick building materials. There is no one coming to assist you; the wall offers no warmth and no greeting.

As you pull away from the stone, your eyes catch a sliver of something wedged deep between two uneven floorboards near the base of the wall. You kneel, your fingers brushing against a discarded scrap of parchment. It is crumpled and stained, but as you smooth it out, you recognize a partial, faded wax seal. It is a near-perfect match for the merchant seal you just handed to **Halden**, suggesting a connection between the ledger's contents and something hidden here in the shadows of the service passage.

### Extract Scene

```json
{
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "A Secret in the Shadows",
  "location_change": null,
  "location_description": "The service corridor feels more oppressive now, the silence broken only by mocking laughter from the other side of the wall.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Sitting at a corner table in the tavern, preoccupied with his ledger."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "surface_as": "ambient",
    "instruction": "The crumpled parchment found near the floorboards contains a ledger entry fragment that explicitly mentions a secret payment intended for the very thugs loitering outside the inn."
  }
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "stained_parchment",
      "name": "stained parchment",
      "notes": "A crumpled scrap of parchment with a faded wax seal matching Halden's ledger.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "leather_pouch",
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
      "id": "merchant_seal_connection",
      "text": "A scrap of parchment with a seal matching Halden's merchant seal was found in the service corridor.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Investigate the service corridor further for more hidden scraps.'}",
    "{'description': 'Return to the tavern to confront Halden about the seal.'}",
    "{'description': 'Try to find another way into the tavern through the corridor.'}",
    "{'description': 'Search the shadows near the floorboards for more clues.'}"
  ],
  "outcome_summary": "Your attempt to bribe your way through the wall fails, met only by mocking laughter, but you discover a scrap of parchment bearing a familiar merchant seal."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "stained_parchment",
      "name": "stained parchment",
      "notes": "A crumpled scrap of parchment with a faded wax seal matching Halden's ledger.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "leather_pouch",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_description": "The service corridor feels more oppressive now, the silence broken only by mocking laughter from the other side of the wall.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "A Secret in the Shadows",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden",
      "last_seen_state": "Sitting at a corner table in the tavern, preoccupied with his ledger."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "merchant_seal_connection",
      "text": "A scrap of parchment with a seal matching Halden's merchant seal was found in the service corridor.",
      "turn": 9
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

- {'description': 'Investigate the service corridor further for more hidden scraps.'}

- {'description': 'Return to the tavern to confront Halden about the seal.'}

- {'description': 'Try to find another way into the tavern through the corridor.'}

- {'description': 'Search the shadows near the floorboards for more clues.'}

### Context Telemetry

- rules: est=1286t trimmed=False
- narrate: est=6424t trimmed=False
- extract.scene: est=4055t trimmed=False attempts=1
- extract.state: est=2236t trimmed=False attempts=1
- extract.progress: est=2163t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen_state": {
          "from": "Standing by the stone well in the town square.",
          "to": "Sitting at a corner table in the tavern, preoccupied with his ledger."
        }
      }
    }
  },
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "stained_parchment",
        "name": "stained parchment",
        "notes": "A crumpled scrap of parchment with a faded wax seal matching Halden's ledger."
      }
    ],
    "removed": [
      {
        "amount": 1,
        "id": "leather_pouch",
        "name": "leather pouch",
        "notes": "Halden's promised payment"
      }
    ]
  },
  "location": {
    "description": {
      "from": "A narrow, dimly lit passage smelling of dried herbs and floor wax, providing a quiet refuge from the tavern's main room.",
      "to": "The service corridor feels more oppressive now, the silence broken only by mocking laughter from the other side of the wall."
    }
  },
  "meta": {
    "pending_gm_beat": {
      "instruction": {
        "from": "As you move deeper into the service corridor, you notice a discarded scrap of parchment wedged between the floorboards, bearing a partial seal that matches the one on the ledger you just delivered.",
        "to": "The crumpled parchment found near the floorboards contains a ledger entry fragment that explicitly mentions a secret payment intended for the very thugs loitering outside the inn."
      }
    },
    "turn": {
      "from": 9,
      "to": 10
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
      "removed": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Sitting at a corner table, preoccupied with verifying the stained ledger and accounts.",
          "title": "Merchant"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "merchant_seal_connection",
          "text": "A scrap of parchment with a seal matching Halden's merchant seal was found in the service corridor.",
          "turn": 9
        }
      ]
    },
    "recently_left": {
      "added": [
        {
          "id": "halden",
          "name": "Halden",
          "title": "Merchant"
        }
      ]
    },
    "tagline": {
      "from": "Quiet Corridor Escape",
      "to": "A Secret in the Shadows"
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
Conditions: bruised ribs, low morale, compromised

## scene
Location: Inn Service Corridor
## last_turn (tail of the most recent narrative)
T10: I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall. — … , suggesting a connection between the ledger's contents and something hidden here in the shadows of the service passage.

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
Conditions: bruised ribs, low morale, compromised

## Location
Inn Service Corridor (inn_service_corridor)
The service corridor feels more oppressive now, the silence broken only by mocking laughter from the other side of the wall.

## Recently Left (do NOT write dialogue or action for these — may briefly acknowledge their departure)
- Halden (Merchant)
## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **stained parchment**: A crumpled scrap of parchment with a faded wax seal matching Halden's ledger.

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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.
- Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.
- Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.
- Halden has paid 200 credits to Voss for the ledger delivery.
- Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.
- Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.
- You successfully delivered the stained ledger and merchant seal to Halden.
- You successfully unlocked and entered the inn's side service corridor, escaping the thugs outside.
- A scrap of parchment with a seal matching Halden's merchant seal was found in the service corridor.

## Prior History (summarized — treat as background, not current scene)
eyes from the nearby tables. The man doesn't look up immediately. He keeps his eyes fixed on the amber liquid in his mug, his weathered face etched with a permanent scowl. When he finally lifts his gaze, his eyes are cold, showing no warmth for your arrival after all this time. "You think a polite seat and a steady voice fixes what you broke?" **Caron** asks, his voice a low rasp that cuts through the tavern's ambient noise. He doesn't lean in to listen; instead, he pushes his mug away with a dismissive flick of his finger. There is no room for negotiation here, no softening of his stance or willingness to hear your terms. He stands up abruptly, his chair clattering against the floor. "I didn't bring you here to talk about feelings or intentions, Voss. I brought you here because the coin is what matters. If you don't have the full amount by sunrise, don't bother coming back to this table." He turns his back on you, leaving his drink half-finished as he moves toward the stairs leading to the upper rooms. ## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. You slide your pouch of **Credits** across the scarred wood of the table. The heavy clink of the coins against the timber is loud in the sudden lull of the tavern's chatter. You watch as the pile of metal sits between you and his empty chair, a meager offering against the weight of what you owe. **Caron** stops halfway up the stairs. He turns his head, his eyes darting momentarily toward the dark corners of the room where a couple of shadows linger near the hearth—likely his muscle waiting for a signal. He looks back at the coins, his lip curling in a sneer of pure contempt. He doesn't descend the stairs to claim the money; instead, he reaches into his heavy coat and pulls out a small, stained ledger. "You think a handful of coin fixes a broken promise?" **Caron** spits, his voice carrying across the room. He descends two steps, his eyes never leaving yours. He scribbles something jagged and violent into the book with a charcoal nub. He doesn't offer a receipt or a smile. He simply snaps the ledger shut with a sound like a bone breaking. "This covers the interest. The principal is still breathing down your neck, Voss. You've got until the sun hits the river before I come looking for the rest." ## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. You step out of the warmth of the tavern and into the cooling evening air of Marrow's Crossing. The sound of the rushing river and the distant rhythmic thud of a mill wheel fill the silence as you navigate the cobblestones toward the town square. You find **Halden** standing by the stone well, his eyes narrowed as he studies a map spread across a wooden crate. He looks up as your heavy boots approach, his expression shifting from concentration to mild curiosity. "The ledger?" **Halden** asks, his voice steady as he glances at the **stained ledger** tucked against your side. He doesn't seem surprised by your arrival, only relieved that the task has a face attached to it. When you propose the price of 200 credits for the delivery to the *Crossed Keys Inn*, he pauses, his thumb rubbing against a pressed wax seal. "Two hundred is steep for a walk across town, Voss, but I've no time to haggle with the evening tide," **Halden** says, reaching into a small leather pouch at his belt. He pulls out a handful of metal and counts out the coins with practiced efficiency, pressing the weight of the payment into your hand. "Take it. Get that book to the inn before the lamps go out. I need those accounts settled before the morning market opens." ## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. You turn away from the well, the weight of the newly received **credits** heavy in your palm. As you begin the trek toward the *Crossed Keys Inn*, you navigate the winding cobblestone streets of Marrow's Crossing. The evening chill bites through your **traveler's cloak**, and the distant rush of the river seems louder as you move away from the town center. As you pass the darkened doorway of the tavern where you just left **Caron**, two silhouettes detach themselves from the gloom. They do not speak or move toward you, but they step into the periphery of the streetlamp's amber glow. One is a broad-shouldered man with a shaved head, his eyes tracking your movement with a predatory stillness. The other, a thinner man with a jagged scar running through his eyebrow, crosses his arms and spits into the gutter as you pass. They linger by the tavern entrance, watching your progress toward the east gate with a silent, unsettling intensity. You continue past the gate, leaving the immediate warmth of the town behind as you follow the merchant road toward the inn. The path ahead is shadowed by the encroaching night, and the silhouettes of the two men remain visible against the tavern's light for a few moments before they fade into the darkness behind you. ## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. You stop your advance toward the east gate and pivot on your heel, marching back toward the flickering amber glow of the tavern entrance. The two men—the broad-shouldered one and the man with the jagged scar—don't flinch as you approach. They stand like pillars of salt against the wood of the building, watching you with a patience that feels practiced and dangerous. "What are you two doing here?" you demand, your voice steady despite the ache in your bruised ribs. "I'm not leaving until I hear your side of things." The broad-shouldered man, whom you recognize as the **Bald Tough**, lets out a short, dry chuckle that doesn't reach his eyes. He uncrosses his arms, his massive hands hanging loosely at his sides, thumbs hooked into a thick leather belt. The **Scarred Tough** beside him merely leans his weight against the doorframe, his eyes narrowing as he studies the way your hand rests near your **Iron dagger**. "Our side?" the **Scarred Tough** asks, his voice a thin, oily rasp. He takes a step forward, encroaching on your personal space just enough to be a threat. "We're just enjoying the evening air, traveler. But since you're so eager to talk, maybe we should talk about a toll. The road's getting expensive, and we've got a particular interest in anyone carrying something as important as a ledger." The **Bald Tough** moves slightly to your left, his heavy footsteps silent on the cobblestones as he begins a slow, flanking maneuver to cut off your path back toward the town center. "A man with your attitude should be careful where he points his questions," he adds, his voice a low rumble. "Questions cost coin. And we're feeling particularly hungry tonight." ## Turn 7 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. You pull the heavy pouch from your belt and let the **credits** spill onto the uneven cobblestones. The metal clinks and dances against the stone, a bright, ringing sound that momentarily cuts through the tension. "Caron's coin is paid," you say, your voice hard as you stare them down. "Take it and go home." The **Scarred Tough** looks down at the pile of coin, his eyes momentarily widening as his gaze flickers from the metal to your face. He doesn't reach for it immediately. Instead, his hand slides downward, his fingers curling around a heavy, blunt object hidden beneath his tunic. The tension doesn't break; it merely shifts shape. The **Bald Tough** stops his flanking maneuver, his massive frame looming just a few feet away. He doesn't pick up the money. Instead, he lets out a low, predatory whistle that draws a few curious glances from the tavern's interior. "Caron's coin?" he repeats, his voice thick with amusement. "We aren't Caron's men, traveler. We're just men who recognize a heavy purse when we see one." The **Scarred Tough** takes a half-step closer, his shoulder almost brushing yours as his hand firmly grips his concealed weapon. "You've got a lot of nerve tossing coin like it's birdseed," he hisses, his eyes darting toward the **stained ledger** at your side. "Now we know exactly what you're carrying, and we know you've got more where that came from. The toll just went up."

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You push past the two men, ignoring the predatory weight of their stares as you step into the warmth of the *Crossed Keys Inn*. The tension of the street momentarily evaporates, replaced by the smell of stale ale and roasting meat. You navigate the crowded floor until you find **Halden**, who sits alone at a corner table, his eyes momentarily lifting from his paperwork as you approach.

Without a word, you slide the **stained ledger** across the wood toward him. You follow it by sliding the merchant seal—the heavy piece of wax and metal that verified his instructions—along the tabletop. The two objects land with a soft thud next to his inkwell. **Halden** picks up the ledger, his fingers tracing the worn edges of the cover as he checks the seal against his own records.

"You're a reliable man, Voss," **Halden** says, his voice quiet but carrying a note of genuine relief. He pulls a small leather pouch from his sleeve and sets it on the table, the weight of his promised payment momentarily settling the tension in your shoulders. He begins flipping through the pages of the ledger, his eyes darting across the scribbled accounts as he confirms the delivery is complete. The immediate pressure of the delivery and the confrontation outside momentarily recedes into the background as he focuses on his work.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.

**Turn 10** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
You press your ear against the cold, damp stone of the service corridor wall, straining to hear anything beyond the muffled roar of the tavern on the other side. Your voice comes out as a frantic, low whisper. "I have credits. Open up." To drive the point home, you pull a single coin from your pouch and press it against the masonry, the metal clinking hollowly against the stone.

The response is not a voice or a door opening, but a heavy, rhythmic thud from the other side of the wall—the sound of a boot striking wood or stone. A moment later, a harsh, mocking laugh echoes through the corridor, muffled by the thick building materials. There is no one coming to assist you; the wall offers no warmth and no greeting.

As you pull away from the stone, your eyes catch a sliver of something wedged deep between two uneven floorboards near the base of the wall. You kneel, your fingers brushing against a discarded scrap of parchment. It is crumpled and stained, but as you smooth it out, you recognize a partial, faded wax seal. It is a near-perfect match for the merchant seal you just handed to **Halden**, suggesting a connection between the ledger's contents and something hidden here in the shadows of the service passage.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 4 + 5 +1 (stat) = 10 → SUCCESS
Directive: The intimidate succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (REVELATION, surface as ambient):
The crumpled parchment found near the floorboards contains a ledger entry fragment that explicitly mentions a secret payment intended for the very thugs loitering outside the inn.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Inn Service Corridor: Standing by the stone well in the town square.
- **Edda**
- **Matthew Estrada**
- **Bald Tough** — last seen Crossed Keys Entrance
- **Scarred Tough** — last seen Crossed Keys Entrance
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
compendium_npc, inventory

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
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_parchment` | stained parchment ×1 — A crumpled scrap of parchment with a faded wax seal matching Halden's ledger.

## scene_result
location: `inn_service_corridor`

## CURRENT TURN NARRATION
You step out of the dim service corridor and push through the swinging doors back into the main taproom. The warmth of the fire and the thick smell of roasted meat hit you, but your eyes immediately lock onto a man sitting alone near the center of the room. **Matthew Estrada**, a man with a military posture and eyes that never stop scanning the exits, sits with a half-empty mug of ale. He doesn't look like a traveler or a merchant; his eyes move with a disciplined, predatory rhythm, cataloging every patron as they enter or leave.

You stride across the uneven floorboards, your boots thudding against the wood as you close the distance. Before he can react, you reach out and seize his wrist in a tight, commanding grip. The muscle underneath his sleeve is hard as corded rope. "Who are you really?" you demand, your voice cutting through the ambient murmur of the tavern. "And why are you watching this room like a soldier on duty?"

**Matthew Estrada** doesn't flinch or pull away. Instead, his eyes snap to yours, cold and unsettlingly calm. He doesn't reach for a weapon, but his entire body tenses, a coiled spring of readiness. "You're a bold one, traveler," he says, his voice a low, steady baritone that carries no hint of fear. He doesn't attempt to break your grip, instead staring you down with a gaze that suggests he has faced far more dangerous men than a courier with a grudge. "A man should mind his own business if he wants to keep his hands."
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
intimidate: Confront Matthew Estrada to uncover his true identity and motives for his suspicious behavior.
## prior_turn_narration (T9 — for outcome_summary and actions context)
You step away from the corner table where **Halden** sits, his eyes still buried in the ledger as he verifies the accounts. Ignoring the lingering tension from the street, you move toward the heavy timber of the inn's side entrance, away from the main crowd and the watchful eyes of the two thugs still loitering near the front. You reach into your pocket and pull out the small **Brass key**, its metal surface smooth against your thumb.

The lock on the side door is old, a heavy iron mechanism caked with layers of dried grease and dust. You fit the tip of the key into the keyhole and give it a steady, practiced twist. There is a momentary screech of metal against metal as the tumblers resist, but with a firm shove, the mechanism yields with a satisfying, heavy *clunk*. The bolt slides back smoothly, clearing the way.

The door swings inward on well-oiled hinges, revealing a narrow, dimly lit service corridor. The air here is cooler and smells of dried herbs and floor wax rather than the stale ale of the main taproom. It is a quiet, functional space, momentarily shielded from the noise of the tavern and the predatory stares of the men outside. The pressure of the delivery finally lifts as the door clicks shut behind you, momentarily sealing the chaos of the street away.

## CURRENT TURN NARRATION
You step out of the dim service corridor and push through the swinging doors back into the main taproom. The warmth of the fire and the thick smell of roasted meat hit you, but your eyes immediately lock onto a man sitting alone near the center of the room. **Matthew Estrada**, a man with a military posture and eyes that never stop scanning the exits, sits with a half-empty mug of ale. He doesn't look like a traveler or a merchant; his eyes move with a disciplined, predatory rhythm, cataloging every patron as they enter or leave.

You stride across the uneven floorboards, your boots thudding against the wood as you close the distance. Before he can react, you reach out and seize his wrist in a tight, commanding grip. The muscle underneath his sleeve is hard as corded rope. "Who are you really?" you demand, your voice cutting through the ambient murmur of the tavern. "And why are you watching this room like a soldier on duty?"

**Matthew Estrada** doesn't flinch or pull away. Instead, his eyes snap to yours, cold and unsettlingly calm. He doesn't reach for a weapon, but his entire body tenses, a coiled spring of readiness. "You're a bold one, traveler," he says, his voice a low, steady baritone that carries no hint of fear. He doesn't attempt to break your grip, instead staring you down with a gaze that suggests he has faced far more dangerous men than a courier with a grudge. "A man should mind his own business if he wants to keep his hands."
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
  "total_ms": 2764.9,
  "tokens_in": 1096,
  "tokens_out": 1205,
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
  "outcome_summary": "You successfully cornered Matthew Estrada, but his calm, military-like composure suggests he is far more than a simple traveler."
}
```

**Raw LLM output:**
```
{
  "intent": "Confront Matthew Estrada to uncover his true identity and motives for his suspicious behavior.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "stakes": "Matthew may react violently or refuse to cooperate, potentially escalating the confrontation in a public setting.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You step out of the dim service corridor and push through the swinging doors back into the main taproom. The warmth of the fire and the thick smell of roasted meat hit you, but your eyes immediately lock onto a man sitting alone near the center of the room. **Matthew Estrada**, a man with a military posture and eyes that never stop scanning the exits, sits with a half-empty mug of ale. He doesn't look like a traveler or a merchant; his eyes move with a disciplined, predatory rhythm, cataloging every patron as they enter or leave.

You stride across the uneven floorboards, your boots thudding against the wood as you close the distance. Before he can react, you reach out and seize his wrist in a tight, commanding grip. The muscle underneath his sleeve is hard as corded rope. "Who are you really?" you demand, your voice cutting through the ambient murmur of the tavern. "And why are you watching this room like a soldier on duty?"

**Matthew Estrada** doesn't flinch or pull away. Instead, his eyes snap to yours, cold and unsettlingly calm. He doesn't reach for a weapon, but his entire body tenses, a coiled spring of readiness. "You're a bold one, traveler," he says, his voice a low, steady baritone that carries no hint of fear. He doesn't attempt to break your grip, instead staring you down with a gaze that suggests he has faced far more dangerous men than a courier with a grudge. "A man should mind his own business if he wants to keep his hands."

### Extract Scene

*(skipped — domain not active this turn)*

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
      "id": "matthew_estrada_confrontation",
      "text": "Aren Voss confronted Matthew Estrada, revealing the man's disciplined and predatory demeanor.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Press Matthew harder to force a confession about his identity.'}",
    "{'description': 'Try to charm him into revealing his true purpose more calmly.'}",
    "{'description': 'Scan the room to see if his allies are approaching.'}",
    "{'description': 'Release his wrist and observe his reaction from a distance.'}"
  ],
  "outcome_summary": "You successfully cornered Matthew Estrada, but his calm, military-like composure suggests he is far more than a simple traveler."
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
  "recent_events_add": [
    {
      "id": "matthew_estrada_confrontation",
      "text": "Aren Voss confronted Matthew Estrada, revealing the man's disciplined and predatory demeanor.",
      "turn": 10
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

- {'description': 'Press Matthew harder to force a confession about his identity.'}

- {'description': 'Try to charm him into revealing his true purpose more calmly.'}

- {'description': 'Scan the room to see if his allies are approaching.'}

- {'description': 'Release his wrist and observe his reaction from a distance.'}

### Context Telemetry

- rules: est=1292t trimmed=False
- narrate: est=6779t trimmed=False
- extract.scene: skipped
- extract.state: est=2318t trimmed=False attempts=1
- extract.progress: est=2205t trimmed=False attempts=1

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
        "last_seen_state": "Descended two steps of the tavern stairs to sneer at the player before heading upstairs.",
        "name": "Caron",
        "title": "Old creditor"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "last_seen": {
          "last_seen_state": "Standing by the stone well in the town square.",
          "location_id": "inn_service_corridor",
          "location_name": "Inn Service Corridor",
          "turn": 9
        },
        "last_seen_state": "Sitting at a corner table in the tavern, preoccupied with his ledger.",
        "name": "Halden",
        "title": "Merchant"
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "last_seen_state": "Wiping down the bar inside the Crossed Keys.",
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
        "last_seen": {
          "last_seen_state": "",
          "location_id": "tavern_entrance",
          "location_name": "Crossed Keys Entrance",
          "turn": 6
        },
        "last_seen_state": "Loitering near the front entrance of the tavern.",
        "name": "Bald Tough",
        "title": "Road thug"
      },
      "tough_b": {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "tavern_entrance",
          "location_name": "Crossed Keys Entrance",
          "turn": 6
        },
        "last_seen_state": "Loitering near the front entrance of the tavern.",
        "name": "Scarred Tough",
        "title": "Road thug"
      }
    }
  },
  "inventory": [
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
      "id": "stained_parchment",
      "name": "stained parchment",
      "notes": "A crumpled scrap of parchment with a faded wax seal matching Halden's ledger."
    }
  ],
  "location": {
    "description": "The service corridor feels more oppressive now, the silence broken only by mocking laughter from the other side of the wall.",
    "id": "inn_service_corridor",
    "name": "Inn Service Corridor"
  },
  "meta": {
    "compendium_touch_order": [],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": null,
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
      },
      {
        "added_turn": 6,
        "description": "The thugs now know you possess the ledger and have more wealth, giving them leverage over you.",
        "id": "compromised",
        "label": "compromised"
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
    },
    {
      "id": "deliver_stained_ledger",
      "last_advanced_turn": 5,
      "objectives": [],
      "status": "active",
      "title": "Deliver the Stained Ledger"
    }
  ],
  "scene": {
    "location_entered_turn": 8,
    "present_npcs": [
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
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "id": "tough_a",
        "name": "Bald Tough",
        "notes": "",
        "title": "Road thug"
      },
      {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "id": "tough_b",
        "name": "Scarred Tough",
        "notes": "",
        "title": "Road thug"
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
        "id": "caron_ultimatum",
        "text": "Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.",
        "turn": 1
      },
      {
        "id": "tough_extortion_attempt",
        "text": "Two thugs have intercepted Aren, rejecting his bribe and demanding more than just the initial coin.",
        "turn": 1
      },
      {
        "id": "caron_partial_payment_refusal",
        "text": "Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.",
        "turn": 2
      },
      {
        "id": "halden_contract_accepted",
        "text": "Halden has paid 200 credits to Voss for the ledger delivery.",
        "turn": 3
      },
      {
        "id": "caron_enforcers_spotted",
        "text": "Two of Caron's men, a broad-shouldered man and a scarred man, watched you leave the tavern with predatory intent.",
        "turn": 4
      },
      {
        "id": "toll_extortion_attempt",
        "text": "Two thugs, the Bald Tough and the Scarred Tough, are attempting to extort a toll from Voss near the tavern entrance.",
        "turn": 5
      },
      {
        "id": "ledger_delivered_successfully",
        "text": "You successfully delivered the stained ledger and merchant seal to Halden.",
        "turn": 7
      },
      {
        "id": "entered_service_corridor",
        "text": "You successfully unlocked and entered the inn's side service corridor, escaping the thugs outside.",
        "turn": 8
      },
      {
        "id": "merchant_seal_connection",
        "text": "A scrap of parchment with a seal matching Halden's merchant seal was found in the service corridor.",
        "turn": 9
      },
      {
        "id": "matthew_estrada_confrontation",
        "text": "Aren Voss confronted Matthew Estrada, revealing the man's disciplined and predatory demeanor.",
        "turn": 10
      }
    ],
    "recently_left": [
      {
        "id": "halden",
        "name": "Halden",
        "title": "Merchant"
      }
    ],
    "recently_left_turns": 0,
    "scene_pressure": [],
    "tagline": "A Secret in the Shadows",
    "tags": [
      "exploration"
    ],
    "turn_entered": 8,
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
| 2 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 2: ['Caron issues a harsh ultimatum: pay the full debt by sunrise or face consequences.'] |
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Voss'] |
| 3 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 3: ['Caron accepted the 500 credits as interest only, leaving the principal debt outstanding.'] |
| 3 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Voss', 'Credits'] |
| 4 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 4: ['Halden has paid 200 credits to Voss for the ledger delivery.'] |
| 7 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Take', 'Instead'] |
| 9 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Ignoring', 'Brass'] |
| 10 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Your', 'Open'] |
| 11 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Who', 'Instead', 'Before'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1187 | 2787 | 3678 | 0 | 1716 | 0 | 0 |
| 3 | 1266 | 3276 | 0 | 2166 | 2160 | 0 | 0 |
| 4 | 1273 | 3588 | 4131 | 2276 | 2546 | 0 | 0 |
| 5 | 1276 | 4107 | 0 | 2204 | 2346 | 0 | 0 |
| 6 | 1278 | 4518 | 4252 | 2411 | 2251 | 0 | 0 |
| 7 | 1280 | 5259 | 0 | 2329 | 2182 | 0 | 0 |
| 8 | 1280 | 5565 | 0 | 2271 | 2539 | 0 | 0 |
| 9 | 1282 | 5991 | 4196 | 2252 | 2187 | 0 | 0 |
| 10 | 1286 | 6424 | 4055 | 2236 | 2163 | 0 | 0 |
| 11 | 1292 | 6779 | 0 | 2318 | 2205 | 0 | 0 |

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + progress | 9 | `- You arrived in Marrow's Crossing after three days on the r / - You heard rumors of road-toughs extorting travelers near t / - You found Caron in the tavern — he's been waiting for you.` |
| narrate + scene | 2 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |

## Compaction Features
*(compaction did not fire during this run — likely because the run was shorter than `compact_every`. Judge: do not score compaction capabilities for this run; note this in your verdict.)*
