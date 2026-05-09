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
Roll: 6 + 3 +1 (stat) = 10 → SUCCESS
Directive: The negotiate succeeds cleanly. Clean success — you do what you intended.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.






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
SUCCESS on charisma — The negotiate succeeds cleanly. Clean success — you do what you intended.## pc
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
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
scene, inventory

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

## CURRENT TURN NARRATION
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."
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
negotiate: The player approaches Caron to discuss and potentially negotiate the settlement of their debt.
## CURRENT TURN NARRATION
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."
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
  "total_ms": 9504.4,
  "tokens_in": 1015,
  "tokens_out": 1122,
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
  "outcome_summary": "You sit across from Caron, facing his scrutiny as he presents the tally stick to demand a resolution to your debt."
}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss and potentially negotiate the settlement of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "stakes": "Failure to reach an agreement could lead to immediate collection of the debt or hostile confrontation.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "Facing The Old Creditor",
  "location_change": null,
  "location_description": "The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.",
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
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "As Caron taps the notched tally stick, he leans closer and whispers that the 'vultures' on the road have been seen wearing a specific crimson sigil, suggesting they are more organized than simple bandits."
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
      "id": "meeting_with_caron",
      "text": "Aren Voss meets with Caron at the tavern to discuss debt settlement.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Propose a restructured payment plan to settle the debt gradually.'}",
    "{'description': 'Offer a specific item or service in lieu of coin.'}",
    "{'description': \"Ask Caron about the 'vultures' currently controlling the road.\"}",
    "{'description': 'Scan the tavern for any potential threats or eavesdroppers.'}"
  ],
  "outcome_summary": "You sit across from Caron, facing his scrutiny as he presents the tally stick to demand a resolution to your debt."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "Facing The Old Creditor",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt."
    }
  ],
  "recent_events_add": [
    {
      "id": "meeting_with_caron",
      "text": "Aren Voss meets with Caron at the tavern to discuss debt settlement.",
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

- {'description': 'Propose a restructured payment plan to settle the debt gradually.'}

- {'description': 'Offer a specific item or service in lieu of coin.'}

- {'description': "Ask Caron about the 'vultures' currently controlling the road."}

- {'description': 'Scan the tavern for any potential threats or eavesdroppers.'}

### Context Telemetry

- rules: est=1187t trimmed=False
- narrate: est=2779t trimmed=False
- extract.scene: est=3693t trimmed=False attempts=1
- extract.state: est=2228t trimmed=False attempts=1
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
    "description": "The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "compendium_touch_order": [],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "As Caron taps the notched tally stick, he leans closer and whispers that the 'vultures' on the road have been seen wearing a specific crimson sigil, suggesting they are more organized than simple bandits.",
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
        "notes": "Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.",
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
        "id": "meeting_with_caron",
        "text": "Aren Voss meets with Caron at the tavern to discuss debt settlement.",
        "turn": 1
      }
    ],
    "scene_pressure": [],
    "tagline": "Facing The Old Creditor",
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
T2: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — … ers? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."

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
The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.

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
- Aren Voss meets with Caron at the tavern to discuss debt settlement.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."

GM DIRECTION (REVELATION, surface as npc_behavior):
As Caron taps the notched tally stick, he leans closer and whispers that the 'vultures' on the road have been seen wearing a specific crimson sigil, suggesting they are more organized than simple bandits.
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
- Caron (Old creditor) — Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.
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
quest_updates, recent_events, inventory

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
You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
quest_updates, recent_events, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player pays 500 credits to Caron to settle their debt.
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
- Aren Voss meets with Caron at the tavern to discuss debt settlement.

## items_gained
Stained ledger

## items_lost
credits

## CURRENT TURN NARRATION
You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player pays 500 credits to Caron to settle their debt.",
  "rolled": false,
  "total_ms": 2375.3,
  "tokens_in": 1089,
  "tokens_out": 1175
}
```

**Raw LLM output:**
```
{
  "intent": "The player pays 500 credits to Caron to settle their debt.",
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

You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "stained_ledger",
      "name": "Stained ledger",
      "notes": "A small, worn book used to track debts and tallies.",
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
      "id": "crimson_sigil_vultures",
      "text": "The road toughs are organized and wear a crimson sigil on their cloaks.",
      "turn": 0
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Ask Caron more about the crimson sigil group.'}",
    "{'text': 'Leave the tavern and head toward the Crossed Keys Inn.'}",
    "{'text': 'Search the tavern for anyone else wearing a crimson sigil.'}",
    "{'text': \"Check your ledger to see if Halden's business is related.\"}"
  ],
  "outcome_summary": "You successfully pay Caron 500 credits, clearing your debt and receiving a warning about an organized group wearing crimson sigils."
}
```

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "stained_ledger",
      "name": "Stained ledger",
      "notes": "A small, worn book used to track debts and tallies.",
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
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "crimson_sigil_vultures",
      "text": "The road toughs are organized and wear a crimson sigil on their cloaks.",
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

- {'text': 'Ask Caron more about the crimson sigil group.'}

- {'text': 'Leave the tavern and head toward the Crossed Keys Inn.'}

- {'text': 'Search the tavern for anyone else wearing a crimson sigil.'}

- {'text': "Check your ledger to see if Halden's business is related."}

### Context Telemetry

- rules: est=1266t trimmed=False
- narrate: est=3217t trimmed=False
- extract.scene: skipped
- extract.state: est=2220t trimmed=False attempts=1
- extract.progress: est=2200t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "inventory": {
    "added": [
      {
        "amount": 1,
        "id": "stained_ledger",
        "name": "Stained ledger",
        "notes": "A small, worn book used to track debts and tallies."
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
        "instruction": "As Caron taps the notched tally stick, he leans closer and whispers that the 'vultures' on the road have been seen wearing a specific crimson sigil, suggesting they are more organized than simple bandits.",
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
          "id": "crimson_sigil_vultures",
          "text": "The road toughs are organized and wear a crimson sigil on their cloaks.",
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
T3: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — … ’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."

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
The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Stained ledger**: A small, worn book used to track debts and tallies.

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
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."

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
- Caron (Old creditor) — Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.
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
*(skipped)*

### Extract Progress User Prompt
```
## active_domains
quest_updates

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player offers to perform a courier service for Halden in exchange for 200 credits.
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

## prior_turn_narration (T2 — for outcome_summary and actions context)
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."

## CURRENT TURN NARRATION
You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player offers to perform a courier service for Halden in exchange for 200 credits.",
  "rolled": false,
  "total_ms": 2671.6,
  "tokens_in": 1097,
  "tokens_out": 1201
}
```

**Raw LLM output:**
```
{
  "intent": "The player offers to perform a courier service for Halden in exchange for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "Halden may refuse the offer, leaving the player without extra credits.",
  "check": {
    "required": false,
    "skill": "",
    "difficulty": "",
    "tags": []
  }
}
```

### Narration

You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

### Extract Scene

*(skipped — domain not active this turn)*

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
      "id": "halden_contract_offered",
      "text": "Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.",
      "turn": 3
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Accept the ledger and promise Halden a safe delivery.'}",
    "{'text': 'Ask Halden for more information about the crimson-sigiled toughs.'}",
    "{'text': 'Negotiate for an advance on the 200 credits immediately.'}",
    "{'text': 'Scan the dark alleys for any signs of suspicious movement.'}"
  ],
  "outcome_summary": "You successfully met Halden at the town well and he has offered the 200 credit contract for delivering the Stained Ledger."
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
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "halden_contract_offered",
      "text": "Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.",
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

- {'text': 'Accept the ledger and promise Halden a safe delivery.'}

- {'text': 'Ask Halden for more information about the crimson-sigiled toughs.'}

- {'text': 'Negotiate for an advance on the 200 credits immediately.'}

- {'text': 'Scan the dark alleys for any signs of suspicious movement.'}

### Context Telemetry

- rules: est=1273t trimmed=False
- narrate: est=3532t trimmed=False
- extract.scene: skipped
- extract.state: skipped
- extract.progress: est=2384t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
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
          "id": "halden_contract_offered",
          "text": "Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.",
          "turn": 3
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
T4: I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. — … olds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

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
The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Stained ledger**: A small, worn book used to track debts and tallies.

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
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."

**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

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
- Caron (Old creditor) — Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.
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
The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor) — Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T4 context)
You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

## CURRENT TURN NARRATION
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
location_change, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | Stained ledger ×1 — A small, worn book used to track debts and tallies.

## scene_result
location: `merchant_road_outskirts`
(location changed)
## CURRENT TURN NARRATION
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
location_change, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
travel: Aren travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
## prior_turn_narration (T3 — for outcome_summary and actions context)
You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."

## CURRENT TURN NARRATION
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "travel",
  "intent": "Aren travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
  "rolled": false,
  "total_ms": 2347.3,
  "tokens_in": 1094,
  "tokens_out": 1178
}
```

**Raw LLM output:**
```
{
  "intent": "Aren travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
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

You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.

### Extract Scene

```json
{
  "scene_tags": [
    "travel"
  ],
  "scene_tagline": "The Lonely Merchant Road",
  "location_change": {
    "id": "merchant_road_outskirts",
    "name": "Merchant Road Outskirts",
    "description": "A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight."
  },
  "location_description": "The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Sitting at a table in the tavern, tapping a tally stick."
    },
    {
      "id": "halden",
      "last_seen_state": "Standing by the town well, handing over the Stained ledger."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "crimson_sigil_threat",
      "text": "Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "surface_as": "event",
    "instruction": "As Aren treks past the riverbank, a sudden, sharp snap of a dry reed echoes from the tall grass just beyond the moonlight's reach, followed by the unmistakable glint of a crimson sigil on a passing shadow."
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
      "id": "crimson_sigil_threat",
      "text": "Organized vultures wearing crimson sigils are prowling the merchant roads.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Scan the roadside reeds for any sign of crimson cloaks.'}",
    "{'description': 'Pick up the pace to reach the Crossed Keys Inn quickly.'}",
    "{'description': 'Check the Stained ledger for any additional notes or markings.'}",
    "{'description': 'Keep a hand on your weapon while traversing the dark road.'}"
  ],
  "outcome_summary": "You depart Marrow's Crossing and begin your trek along the merchant road, remaining vigilant of the crimson-sigil threats mentioned by Caron."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "merchant_road_outskirts",
    "name": "Merchant Road Outskirts",
    "description": "A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight."
  },
  "location_description": "The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "travel"
  ],
  "scene_tagline": "The Lonely Merchant Road",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Sitting at a table in the tavern, tapping a tally stick."
    },
    {
      "id": "halden",
      "last_seen_state": "Standing by the town well, handing over the Stained ledger."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "crimson_sigil_threat",
      "text": "Organized vultures wearing crimson sigils are prowling the merchant roads.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "crimson_sigil_threat",
      "text": "Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.",
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

- {'description': 'Scan the roadside reeds for any sign of crimson cloaks.'}

- {'description': 'Pick up the pace to reach the Crossed Keys Inn quickly.'}

- {'description': 'Check the Stained ledger for any additional notes or markings.'}

- {'description': 'Keep a hand on your weapon while traversing the dark road.'}

### Context Telemetry

- rules: est=1276t trimmed=False
- narrate: est=3993t trimmed=False
- extract.scene: est=4064t trimmed=False attempts=1
- extract.state: est=2166t trimmed=False attempts=1
- extract.progress: est=2229t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "last_seen_state": {
          "from": null,
          "to": "Sitting at a table in the tavern, tapping a tally stick."
        }
      },
      "halden": {
        "last_seen_state": {
          "from": null,
          "to": "Standing by the town well, handing over the Stained ledger."
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls.",
      "to": "A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight."
    },
    "id": {
      "from": "marrows_crossing",
      "to": "merchant_road_outskirts"
    },
    "name": {
      "from": "Marrow's Crossing",
      "to": "Merchant Road Outskirts"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As Aren treks past the riverbank, a sudden, sharp snap of a dry reed echoes from the tall grass just beyond the moonlight's reach, followed by the unmistakable glint of a crimson sigil on a passing shadow.",
        "surface_as": "event",
        "type": "complication"
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
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Sitting across from Aren Voss, tapping a notched tally stick on the table while demanding proof of intent to settle the debt.",
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
    "recent_events": {
      "added": [
        {
          "id": "crimson_sigil_threat",
          "text": "Organized vultures wearing crimson sigils are prowling the merchant roads.",
          "turn": 4
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
      "added": [
        {
          "id": "crimson_sigil_threat",
          "max_turns": null,
          "text": "Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.",
          "turn_added": 4,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "Facing The Old Creditor",
      "to": "The Lonely Merchant Road"
    },
    "tags": {
      "added": [
        "travel"
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
Location: Merchant Road Outskirts
## last_turn (tail of the most recent narrative)
T5: I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. — … imson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.

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
Merchant Road Outskirts (merchant_road_outskirts)
A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Stained ledger**: A small, worn book used to track debts and tallies.

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
- [BUILDING] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.
- Organized vultures wearing crimson sigils are prowling the merchant roads.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 3** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."

**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 3 + 5 +1 (stat) = 9 → PARTIAL
Directive: The persuade results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (COMPLICATION, surface as event):
As Aren treks past the riverbank, a sudden, sharp snap of a dry reed echoes from the tall grass just beyond the moonlight's reach, followed by the unmistakable glint of a crimson sigil on a passing shadow.
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
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
compendium_npc, inventory

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
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | Stained ledger ×1 — A small, worn book used to track debts and tallies.

## scene_result
location: `merchant_road_outskirts`

## CURRENT TURN NARRATION
You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
compendium_npc, inventory

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: Confront the two toughs at the inn door to demand an explanation for their presence.
## prior_turn_narration (T4 — for outcome_summary and actions context)
You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

## CURRENT TURN NARRATION
You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."
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
  "total_ms": 2921.4,
  "tokens_in": 1093,
  "tokens_out": 1212,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    3,
    5
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 9,
  "band": "partial",
  "outcome_summary": "Your attempt to demand an explanation met with mockery and a veiled threat from the crimson-sigiled guards."
}
```

**Raw LLM output:**
```
{
  "intent": "Confront the two toughs at the inn door to demand an explanation for their presence.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "The toughs may become hostile or refuse to answer, potentially leading to a physical altercation or being barred from the inn.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."

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
      "id": "crimson_sigil_guards",
      "text": "Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Demand passage to the inn and refuse their intimidation.'}",
    "{'description': 'Try to bribe Marcus to let you pass peacefully.'}",
    "{'description': 'Confront Bald Tough about the meaning of their crimson sigils.'}",
    "{'description': 'Scan the surrounding alleyways for any other hidden threats.'}"
  ],
  "outcome_summary": "Your attempt to demand an explanation met with mockery and a veiled threat from the crimson-sigiled guards."
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
  "scene_tags": [],
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "crimson_sigil_guards",
      "text": "Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.",
      "turn": 5
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

- {'description': 'Demand passage to the inn and refuse their intimidation.'}

- {'description': 'Try to bribe Marcus to let you pass peacefully.'}

- {'description': 'Confront Bald Tough about the meaning of their crimson sigils.'}

- {'description': 'Scan the surrounding alleyways for any other hidden threats.'}

### Context Telemetry

- rules: est=1280t trimmed=False
- narrate: est=4530t trimmed=False
- extract.scene: skipped
- extract.state: est=2316t trimmed=False attempts=1
- extract.progress: est=2221t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As Aren treks past the riverbank, a sudden, sharp snap of a dry reed echoes from the tall grass just beyond the moonlight's reach, followed by the unmistakable glint of a crimson sigil on a passing shadow.",
        "surface_as": "event",
        "type": "complication"
      },
      "to": null
    },
    "turn": {
      "from": 5,
      "to": 6
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
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "crimson_sigil_guards",
          "text": "Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.",
          "turn": 5
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
Location: Merchant Road Outskirts
## last_turn (tail of the most recent narrative)
T6: I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. — … his road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."

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
Merchant Road Outskirts (merchant_road_outskirts)
A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Stained ledger**: A small, worn book used to track debts and tallies.

## Quests
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
- [BUILDING] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.
- Organized vultures wearing crimson sigils are prowling the merchant roads.
- Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 4** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.

**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 2 + 1 +1 (stat) = 4 → FAIL
Directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor)
- Halden (Merchant)
- Edda (Innkeeper at the Crossed Keys)
- Matthew Estrada (Traveler)
- Bald Tough (Road thug)
- Scarred Tough (Road thug)
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
pc_condition, inventory

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

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `stained_ledger` | Stained ledger ×1 — A small, worn book used to track debts and tallies.

## scene_result
location: `merchant_road_outskirts`

## CURRENT TURN NARRATION
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
pc_condition, inventory

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to bribe the toughs to leave them alone by claiming the debt is settled.
## prior_turn_narration (T5 — for outcome_summary and actions context)
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.

## items_lost
credits

## CURRENT TURN NARRATION
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."
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
  "total_ms": 2910.4,
  "tokens_in": 1100,
  "tokens_out": 1218,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    2,
    1
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 4,
  "band": "fail",
  "outcome_summary": "Your attempt to bribe the thugs fails miserably, resulting in a heavy blow to your ribs and a direct physical confrontation."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the toughs to leave them alone by claiming the debt is settled.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "If the bribe is rejected or seen as a lie, the toughs may become violent or demand more money.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

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
  "pc_condition_add": [
    {
      "id": "winded",
      "label": "winded",
      "description": "A heavy blow to the solar plexus has knocked the breath from your lungs, making it difficult to breathe or speak clearly."
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
      "id": "ambush_at_crossed_keys",
      "text": "Marcus and a Bald Tough have ambushed Aren at the Crossed Keys Inn, rejecting his bribe and turning violent.",
      "turn": 6
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': \"Draw a weapon and defend yourself against the Bald Tough's assault.\"}",
    "{'description': 'Attempt to scramble away toward the dark merchant road to escape.'}",
    "{'description': 'Try to reason with Marcus one last time to de-escalate.'}",
    "{'description': 'Search the immediate area for anything to use as a makeshift weapon.'}"
  ],
  "outcome_summary": "Your attempt to bribe the thugs fails miserably, resulting in a heavy blow to your ribs and a direct physical confrontation."
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

```json
[
  {
    "field": "inventory_remove",
    "value": "credits",
    "reason": "Inventory item 'credits' does not exist"
  }
]
```

### Suggested Actions

- {'description': "Draw a weapon and defend yourself against the Bald Tough's assault."}

- {'description': 'Attempt to scramble away toward the dark merchant road to escape.'}

- {'description': 'Try to reason with Marcus one last time to de-escalate.'}

- {'description': 'Search the immediate area for anything to use as a makeshift weapon.'}

### Context Telemetry

- rules: est=1281t trimmed=False
- narrate: est=4966t trimmed=False
- extract.scene: skipped
- extract.state: est=2386t trimmed=False attempts=1
- extract.progress: est=2180t trimmed=False attempts=1

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
      "from": 1,
      "to": 0
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
Location: Merchant Road Outskirts
## last_turn (tail of the most recent narrative)
T7: I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. — … eaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

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
Merchant Road Outskirts (merchant_road_outskirts)
A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight.

## Inventory
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Stained ledger**: A small, worn book used to track debts and tallies.

## Quests
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
- [BUILDING] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.
- Organized vultures wearing crimson sigils are prowling the merchant roads.
- Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.

**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 2 + 2 +1 (stat) = 5 → FAIL
Directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden**
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor)
- Halden (Merchant)
- Edda (Innkeeper at the Crossed Keys)
- Matthew Estrada (Traveler)
- Bald Tough (Road thug)
- Scarred Tough (Road thug)
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
FAIL on charisma — The persuade fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`merchant_road_outskirts` | Merchant Road Outskirts
A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor)
- `halden` | Halden (Merchant)
- `innkeeper` | Edda (Innkeeper at the Crossed Keys)
- `matthew_estrada` | Matthew Estrada (Traveler)
- `tough_a` | Bald Tough (Road thug)
- `tough_b` | Scarred Tough (Road thug)

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `crimson_sigil_threat` [building] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts. (added turn 4)


⚠ Quest "Deliver Halden's Ledger" stalled for 5 turns.

⚠ Quest "Deliver the Stained Ledger" stalled for 3 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_stained_ledger` | Deliver the Stained Ledger



## previous_turn_narration (T7 context)
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

## CURRENT TURN NARRATION
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.
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
- `stained_ledger` | Stained ledger ×1 — A small, worn book used to track debts and tallies.

## scene_result
location: `crossed_keys_inn`
(location changed)
## CURRENT TURN NARRATION
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.
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
persuade: The player attempts to present the merchant seal and ledger to Halden to prove their identity or authority.
## prior_turn_narration (T6 — for outcome_summary and actions context)
You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."

## items_lost
stained_ledger

## CURRENT TURN NARRATION
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to present the merchant seal and ledger to Halden to prove their identity or authority.",
  "rolled": true,
  "total_ms": 2805.5,
  "tokens_in": 1105,
  "tokens_out": 1216,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    2,
    2
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 5,
  "band": "fail",
  "outcome_summary": "You successfully present the merchant seal and ledger to Halden, who receives them with visible relief and anxiety."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to present the merchant seal and ledger to Halden to prove their identity or authority.",
  "intent_verb": "persuade",
  "target": "Halden",
  "stakes": "Halden may reject the credentials, leading to further confrontation or loss of trust.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Ledger Is Delivered",
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside."
  },
  "location_description": "The atmosphere shifts from the biting chill of the outskirts to a thick, sensory-heavy tavern interior, though the tension remains high.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Engaged in a physical altercation with Aren Voss outside the inn."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Engaged in a physical altercation with Aren Voss outside the inn."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss.",
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
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "As Halden inspects the wax seal, he suddenly freezes, noticing a tiny, fresh scratch on the leather cover that wasn't there before\u2014a sign that someone may have attempted to peek inside during the transit."
  }
}
```

### Extract State

```json
{
  "inventory_add": [],
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
  "quest_updates": [],
  "recent_events_add": [
    {
      "id": "ledger_delivered",
      "text": "Voss successfully delivers the stained ledger and merchant seal to Halden.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Ask Halden what he knows about the crimson-sigiled men outside.'}",
    "{'description': 'Demand payment or further instructions now that the ledger is safe.'}",
    "{'description': 'Keep a watchful eye on the tavern door for Marcus and his partner.'}",
    "{'description': 'Order a strong drink to numb the pain in your ribs.'}"
  ],
  "outcome_summary": "You successfully present the merchant seal and ledger to Halden, who receives them with visible relief and anxiety."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "stained_ledger",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside."
  },
  "location_description": "The atmosphere shifts from the biting chill of the outskirts to a thick, sensory-heavy tavern interior, though the tension remains high.",
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "The Ledger Is Delivered",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Engaged in a physical altercation with Aren Voss outside the inn."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Engaged in a physical altercation with Aren Voss outside the inn."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss."
    }
  ],
  "recent_events_add": [
    {
      "id": "ledger_delivered",
      "text": "Voss successfully delivers the stained ledger and merchant seal to Halden.",
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

- {'description': 'Ask Halden what he knows about the crimson-sigiled men outside.'}

- {'description': 'Demand payment or further instructions now that the ledger is safe.'}

- {'description': 'Keep a watchful eye on the tavern door for Marcus and his partner.'}

- {'description': 'Order a strong drink to numb the pain in your ribs.'}

### Context Telemetry

- rules: est=1277t trimmed=False
- narrate: est=5437t trimmed=False
- extract.scene: est=4229t trimmed=False attempts=1
- extract.state: est=2289t trimmed=False attempts=1
- extract.progress: est=2231t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "Standing by the town well, handing over the Stained ledger.",
            "location_id": "crossed_keys_inn",
            "location_name": "Crossed Keys Inn",
            "turn": 8
          }
        }
      },
      "tough_a": {
        "last_seen_state": {
          "from": null,
          "to": "Engaged in a physical altercation with Aren Voss outside the inn."
        }
      },
      "tough_b": {
        "last_seen_state": {
          "from": null,
          "to": "Engaged in a physical altercation with Aren Voss outside the inn."
        }
      }
    }
  },
  "inventory": {
    "removed": [
      {
        "amount": 1,
        "id": "stained_ledger",
        "name": "Stained ledger",
        "notes": "A small, worn book used to track debts and tallies."
      }
    ]
  },
  "location": {
    "description": {
      "from": "A wide, packed earth and stone path cutting through tall reeds near the riverbank, illuminated by thin moonlight.",
      "to": "A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside."
    },
    "id": {
      "from": "merchant_road_outskirts",
      "to": "crossed_keys_inn"
    },
    "name": {
      "from": "Merchant Road Outskirts",
      "to": "Crossed Keys Inn"
    }
  },
  "meta": {
    "pending_gm_beat": {
      "from": null,
      "to": {
        "instruction": "As Halden inspects the wax seal, he suddenly freezes, noticing a tiny, fresh scratch on the leather cover that wasn't there before\u2014a sign that someone may have attempted to peek inside during the transit.",
        "surface_as": "npc_behavior",
        "type": "revelation"
      }
    },
    "turn": {
      "from": 7,
      "to": 8
    }
  },
  "pc": {
    "momentum": {
      "from": 0,
      "to": -1
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 4,
      "to": 7
    },
    "present_npcs": {
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "",
          "title": "Old creditor"
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
      "changed": [
        {
          "from": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "",
            "title": "Merchant"
          },
          "to": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss.",
            "title": "Merchant"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "ledger_delivered",
          "text": "Voss successfully delivers the stained ledger and merchant seal to Halden.",
          "turn": 7
        }
      ]
    },
    "tagline": {
      "from": "The Lonely Merchant Road",
      "to": "The Ledger Is Delivered"
    },
    "tags": {
      "added": [
        "dialogue"
      ],
      "removed": [
        "travel"
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
T8: I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. — … ching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.

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
A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside.

## Inventory
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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.
- Organized vultures wearing crimson sigils are prowling the merchant roads.
- Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.
- Voss successfully delivers the stained ledger and merchant seal to Halden.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 6** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."

**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: normal
Roll: 2 + 1 +1 (stat) = 4 → FAIL
Directive: The hack fails. The attempt fails outright — what you tried to do does not happen.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-2). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

GM DIRECTION (REVELATION, surface as npc_behavior):
As Halden inspects the wax seal, he suddenly freezes, noticing a tiny, fresh scratch on the leather cover that wasn't there before—a sign that someone may have attempted to peek inside during the transit.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Crossed Keys Inn: Standing by the town well, handing over the Stained ledger.
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
*(skipped)*

### Extract State User Prompt
```
## active_domains
inventory

## rules_outcome
FAIL on dexterity. The hack fails. The attempt fails outright — what you tried to do does not happen.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: dexterity
band: fail
directive: The hack fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn`

## CURRENT TURN NARRATION
You reach into your pocket and pull out the **Brass key**, its metal cool and heavy in your palm. You stand from the table, ignoring the dull ache in your ribs, and move toward the heavy timber entrance of the *Crossed Keys Inn*. The tavern is still loud with the boisterous chatter of patrons, but you focus on the lock mechanism near the door, trying to find a keyhole that might lead to a more private area or a back room.

You slide the key into the lock, but it meets a stubborn, unyielding resistance. There is no satisfying click; instead, the metal scrapes harshly against the internal tumblers with a grating sound that makes your teeth ache. The key won't turn, jammed by a mechanism that clearly wasn't meant for this specific bit of brass.

**Halden** watches you from his corner table, his eyes wide with a flicker of panic at your sudden movement toward the exit. "What are you doing?" he hisses, leaning forward so his voice won't carry to the boisterous crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
inventory

## rules_outcome
FAIL on dexterity.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
hack: The player attempts to use a brass key to unlock the inn's front door or find a back room.
## prior_turn_narration (T7 — for outcome_summary and actions context)
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

## CURRENT TURN NARRATION
You reach into your pocket and pull out the **Brass key**, its metal cool and heavy in your palm. You stand from the table, ignoring the dull ache in your ribs, and move toward the heavy timber entrance of the *Crossed Keys Inn*. The tavern is still loud with the boisterous chatter of patrons, but you focus on the lock mechanism near the door, trying to find a keyhole that might lead to a more private area or a back room.

You slide the key into the lock, but it meets a stubborn, unyielding resistance. There is no satisfying click; instead, the metal scrapes harshly against the internal tumblers with a grating sound that makes your teeth ache. The key won't turn, jammed by a mechanism that clearly wasn't meant for this specific bit of brass.

**Halden** watches you from his corner table, his eyes wide with a flicker of panic at your sudden movement toward the exit. "What are you doing?" he hisses, leaning forward so his voice won't carry to the boisterous crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."
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
  "total_ms": 2868.4,
  "tokens_in": 1084,
  "tokens_out": 1200,
  "skill": "dexterity",
  "difficulty": "normal",
  "dice": [
    2,
    1
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 4,
  "band": "fail",
  "outcome_summary": "The brass key fails to turn in the lock, leaving you stuck at the entrance while Halden warns you of the danger outside."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find a back room.",
  "intent_verb": "hack",
  "target": "inn's front door/back room",
  "stakes": "Being caught trespassing or failing to find a way out/in.",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You reach into your pocket and pull out the **Brass key**, its metal cool and heavy in your palm. You stand from the table, ignoring the dull ache in your ribs, and move toward the heavy timber entrance of the *Crossed Keys Inn*. The tavern is still loud with the boisterous chatter of patrons, but you focus on the lock mechanism near the door, trying to find a keyhole that might lead to a more private area or a back room.

You slide the key into the lock, but it meets a stubborn, unyielding resistance. There is no satisfying click; instead, the metal scrapes harshly against the internal tumblers with a grating sound that makes your teeth ache. The key won't turn, jammed by a mechanism that clearly wasn't meant for this specific bit of brass.

**Halden** watches you from his corner table, his eyes wide with a flicker of panic at your sudden movement toward the exit. "What are you doing?" he hisses, leaning forward so his voice won't carry to the boisterous crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."

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
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Try to force the lock or find an alternative entrance",
    "Ignore the door and confront Marcus and Bald Tough",
    "Whisper back to Halden to ask for his help",
    "Scan the tavern crowd for a potential distraction or exit"
  ],
  "outcome_summary": "The brass key fails to turn in the lock, leaving you stuck at the entrance while Halden warns you of the danger outside."
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
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Try to force the lock or find an alternative entrance

- Ignore the door and confront Marcus and Bald Tough

- Whisper back to Halden to ask for his help

- Scan the tavern crowd for a potential distraction or exit

### Context Telemetry

- rules: est=1276t trimmed=False
- narrate: est=6031t trimmed=False
- extract.scene: skipped
- extract.state: est=2172t trimmed=False attempts=1
- extract.progress: est=2158t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "pending_gm_beat": {
      "from": {
        "instruction": "As Halden inspects the wax seal, he suddenly freezes, noticing a tiny, fresh scratch on the leather cover that wasn't there before\u2014a sign that someone may have attempted to peek inside during the transit.",
        "surface_as": "npc_behavior",
        "type": "revelation"
      },
      "to": null
    },
    "turn": {
      "from": 8,
      "to": 9
    }
  },
  "pc": {
    "momentum": {
      "from": -1,
      "to": -2
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
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T9: I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. — … crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."

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
Crossed Keys Inn (crossed_keys_inn)
A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside.

## Inventory
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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.
- Organized vultures wearing crimson sigils are prowling the merchant roads.
- Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.
- Voss successfully delivers the stained ledger and merchant seal to Halden.

## Prior History (summarized — treat as background, not current scene)



## Turn 2 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

You pull out the heavy wooden chair opposite **Caron** and sit. The tavern is dim, lit by a few guttering tallow candles that cast long, dancing shadows against the timber walls. The man looks up from his cup, his eyes bloodshot and heavy with the weight of years spent collecting what is owed. He studies your face for a moment, looking for any sign of hesitation or deceit, before setting his drink down with a dull thud on the scarred tabletop.

"You've got the look of a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do."

He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed."


## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there.

"Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally.

He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver."


## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.

You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern.

**Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance.

"Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours."

He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation.


## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing.

The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement.

As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light.


## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light.

"I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?"

The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder.

Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 7** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother."

**Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now."

Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side.

**Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth."

*That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You reach into your pocket and pull out the **Brass key**, its metal cool and heavy in your palm. You stand from the table, ignoring the dull ache in your ribs, and move toward the heavy timber entrance of the *Crossed Keys Inn*. The tavern is still loud with the boisterous chatter of patrons, but you focus on the lock mechanism near the door, trying to find a keyhole that might lead to a more private area or a back room.

You slide the key into the lock, but it meets a stubborn, unyielding resistance. There is no satisfying click; instead, the metal scrapes harshly against the internal tumblers with a grating sound that makes your teeth ache. The key won't turn, jammed by a mechanism that clearly wasn't meant for this specific bit of brass.

**Halden** watches you from his corner table, his eyes wide with a flicker of panic at your sudden movement toward the exit. "What are you doing?" he hisses, leaning forward so his voice won't carry to the boisterous crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 2 + 3 +1 (stat) = 6 → FAIL
Directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-3). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Crossed Keys Inn: Standing by the town well, handing over the Stained ledger.
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss.
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
pc_condition, inventory

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

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn`

## CURRENT TURN NARRATION
You lean your weight against the coarse, cold stone of the *Crossed Keys Inn* wall, pressing your ear against the masonry to catch any sound from within. Your breath hitches as the movement agitates your **bruised ribs**, a sharp reminder of the heavy fist you took at the gate. "I have credits. Open up," you whisper into the dark, your voice barely a shadow of a sound against the heavy timber and stone.

With a trembling hand, you pull a single iron coin from your pouch and press it against the base of the wall, a desperate, nonsensical offering to the building itself. There is no response from the stone; no secret latch clicks, and no voice calls out from the other side. The heavy silence of the exterior is broken only by the muffled, boisterous laughter of the patrons inside, oblivious to your shadow-play at the threshold.

**Halden** stands up from his table, his shadow dancing wildly against the wall as he approaches you. He looks around the tavern nervously, his eyes darting toward the heavy doors where the crimson-sigiled men are stationed. "Voss, what in the gods' names are you doing?" he hisses, his voice thick with embarrassment and alarm. "You'll draw every eye in this room to us. Stop your nonsense and sit down before you bring the whole lot of them down on our heads."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## active_domains
pc_condition, inventory

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to bribe or persuade someone behind the inn wall to open a door.
## prior_turn_narration (T8 — for outcome_summary and actions context)
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.

## items_lost
iron_coin

## CURRENT TURN NARRATION
You lean your weight against the coarse, cold stone of the *Crossed Keys Inn* wall, pressing your ear against the masonry to catch any sound from within. Your breath hitches as the movement agitates your **bruised ribs**, a sharp reminder of the heavy fist you took at the gate. "I have credits. Open up," you whisper into the dark, your voice barely a shadow of a sound against the heavy timber and stone.

With a trembling hand, you pull a single iron coin from your pouch and press it against the base of the wall, a desperate, nonsensical offering to the building itself. There is no response from the stone; no secret latch clicks, and no voice calls out from the other side. The heavy silence of the exterior is broken only by the muffled, boisterous laughter of the patrons inside, oblivious to your shadow-play at the threshold.

**Halden** stands up from his table, his shadow dancing wildly against the wall as he approaches you. He looks around the tavern nervously, his eyes darting toward the heavy doors where the crimson-sigiled men are stationed. "Voss, what in the gods' names are you doing?" he hisses, his voice thick with embarrassment and alarm. "You'll draw every eye in this room to us. Stop your nonsense and sit down before you bring the whole lot of them down on our heads."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe or persuade someone behind the inn wall to open a door.",
  "rolled": true,
  "total_ms": 2827.7,
  "tokens_in": 1098,
  "tokens_out": 1211,
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
  "outcome_summary": "Your attempt to bribe the inn through the wall fails, and Halden's panicked reaction draws attention to your suspicious behavior."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe or persuade someone behind the inn wall to open a door.",
  "intent_verb": "persuade",
  "target": "unseen person behind the wall",
  "stakes": "The player might be discovered or ignored, potentially drawing unwanted attention from the men outside.",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You lean your weight against the coarse, cold stone of the *Crossed Keys Inn* wall, pressing your ear against the masonry to catch any sound from within. Your breath hitches as the movement agitates your **bruised ribs**, a sharp reminder of the heavy fist you took at the gate. "I have credits. Open up," you whisper into the dark, your voice barely a shadow of a sound against the heavy timber and stone.

With a trembling hand, you pull a single iron coin from your pouch and press it against the base of the wall, a desperate, nonsensical offering to the building itself. There is no response from the stone; no secret latch clicks, and no voice calls out from the other side. The heavy silence of the exterior is broken only by the muffled, boisterous laughter of the patrons inside, oblivious to your shadow-play at the threshold.

**Halden** stands up from his table, his shadow dancing wildly against the wall as he approaches you. He looks around the tavern nervously, his eyes darting toward the heavy doors where the crimson-sigiled men are stationed. "Voss, what in the gods' names are you doing?" he hisses, his voice thick with embarrassment and alarm. "You'll draw every eye in this room to us. Stop your nonsense and sit down before you bring the whole lot of them down on our heads."

*That action didn't resolve as expected. Trace `fa832ea9` — try rephrasing.*

### Extract Scene

*(skipped — domain not active this turn)*

### Extract State

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "iron_coin",
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
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Try to bribe Halden more convincingly to help you enter",
    "Search the exterior wall for a hidden entrance or latch",
    "Quietly slip past Halden and attempt to find another way in",
    "Confront Halden about the crimson-sigiled men's presence inside"
  ],
  "outcome_summary": "Your attempt to bribe the inn through the wall fails, and Halden's panicked reaction draws attention to your suspicious behavior."
}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

```json
[
  {
    "field": "inventory_remove",
    "value": "iron_coin",
    "reason": "Inventory item 'iron_coin' does not exist"
  }
]
```

### Suggested Actions

- Try to bribe Halden more convincingly to help you enter

- Search the exterior wall for a hidden entrance or latch

- Quietly slip past Halden and attempt to find another way in

- Confront Halden about the crimson-sigiled men's presence inside

### Context Telemetry

- rules: est=1281t trimmed=False
- narrate: est=6283t trimmed=False
- extract.scene: skipped
- extract.state: est=2315t trimmed=False attempts=1
- extract.progress: est=2185t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "turn": {
      "from": 9,
      "to": 10
    }
  },
  "pc": {
    "momentum": {
      "from": -2,
      "to": -3
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
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T10: I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall. — …  the whole lot of them down on our heads."

*That action didn't resolve as expected. Trace `fa832ea9` — try rephrasing.*

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
Crossed Keys Inn (crossed_keys_inn)
A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside.

## Inventory
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
- **Deliver the Stained Ledger** [active]

_(immutable section omitted — see Static Context > Seed State)_
## ACTIVE THREATS (must be reflected in narration)
- [BUILDING] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Aren Voss meets with Caron at the tavern to discuss debt settlement.
- The road toughs are organized and wear a crimson sigil on their cloaks.
- Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.
- Organized vultures wearing crimson sigils are prowling the merchant roads.
- Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.
- Voss successfully delivers the stained ledger and merchant seal to Halden.

## Prior History (summarized — treat as background, not current scene)
a man who's walked a long way just to face a shadow," **Caron** says, his voice a low rasp that barely carries over the distant sound of the river outside. He leans forward, resting his thick, calloused hands on the table. "I didn't expect you to show your face so soon after the road fell to those vultures. But you're here, and that's more than most would do." He reaches into a heavy leather pouch at his belt and pulls out a small, notched tally stick. He taps it against the table, a rhythmic, final sound. "I'm not a man for long-winded stories or excuses, Voss. You want this weight off your shoulders? Then show me you have what it takes to settle up, or at least show me you're serious about the terms we discussed." ## Turn 3 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. You pull your heavy pouch from your belt and slide the full stack of **Credits** across the scarred wood. The coins clink softly, a bright, metallic sound that feels too loud in the quiet tavern. **Caron** stares at the pile for a long moment, his bloodshot eyes tracking the movement of the wealth. He doesn't reach for it immediately; instead, he studies your steady hands, looking for a tremor that isn't there. "Five hundred," he mutters, more to himself than to you. He reaches out with a thick finger and hooks the edge of the pile, pulling the coins toward his side of the table with a decisive scrape. He reaches into a pocket of his heavy vest and produces a small, stained ledger. He flips through the parchment pages until he finds the entry marked with your name, then takes a charcoal stub from his belt. With a quick, decisive stroke, he draws a heavy line through the tally. He closes the book and leans in closer, his shadow stretching long over the table in the flickering candlelight. "The debt is marked, Voss. But don't think the road is any safer now that you're clear of me." His voice drops to a coarse whisper, his eyes darting briefly toward the tavern door. "Those vultures you heard about? They aren't just hungry travelers looking for a quick coin. They’ve been seen wearing a crimson sigil on their cloaks. They’re organized, and they’re hungry for more than just silver." ## Turn 4 — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. You stand up from the table, leaving the shadow of **Caron** behind, and push through the heavy tavern doors into the cool night air of Marrow's Crossing. The smell of river silt and peat smoke hangs thick in the street. You navigate the narrow, cobbled lanes until you find the town well, where a man stands hunched over a parchment map under the pale light of a street lantern. **Halden** looks up as you approach, his eyes squinting against the dim light. He is a man of middle years with a nervous twitch in his left eye and a heavy, ink-stained finger perpetually hovering over a pressed wax seal. He looks at your broad shoulders and the heavy pack you carry, gauging your capability at a glance. "Two hundred?" **Halden** repeats, his voice thin and strained. He looks at the map, then back at you, his gaze darting toward the dark alleys where the crimson-sigiled toughs are rumored to lurk. "That is a steep price for a simple delivery, Voss, but the roads are no longer what they were. I have no time for more delays or more thieves." He reaches into a small pouch at his waist and produces a heavy roll of silver and iron coins. "If you can get this to the Crossed Keys without a single page missing or a single seal broken, the coin is yours." He holds out a thick, leather-bound book—the **Stained ledger** you have been tasked to carry—waiting for your confirmation. ## Turn 5 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. You take the **Stained ledger** from **Halden**, feeling the weight of the parchment and the responsibility it carries. He nods curtly, his eyes darting once more toward the shadows of the town before you turn away. You shoulder your heavy pack, pull your **Traveler's cloak** tight against the biting night air, and steer your path toward the east gate of Marrow's Crossing. The gate is a heavy timber archway, guarded by a single sentry who barely looks up from his small brazier as you pass. Beyond the gate, the merchant road stretches out into the darkness, a ribbon of packed earth and stone cutting through the tall, rustling reeds near the riverbank. The moonlight is thin, casting long, distorted shapes from the trees that line the path, making every shadow seem thick with movement. As you trek along the road, the silence of the outskirts is broken only by the rhythmic crunch of your boots and the distant, low murmur of the river. The path is wide enough for a caravan, but tonight it feels unnervingly empty. Your eyes scan the periphery, looking for any flash of crimson or the silhouette of a crouched figure, but for now, the road remains a lonely stretch of shadow and silver light. ## Turn 6 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. You stride up to the heavy timber entrance of the *Crossed Keys Inn*, your shadow stretching long over the threshold. Two men stand guard at the doorway, blocking the path with a casual, practiced arrogance. They are broad-shouldered and clad in dark, heavy tunics, but it is the splash of color that catches your eye: a bright, crimson sigil stitched onto their cloaks, glowing dullly in the lantern light. "I'm not leaving until I hear your side," you say, your voice steady despite the dull ache in your ribs. "What are you doing here at the inn?" The taller of the two, a man with a broken nose and a hungry look in his eyes named **Marcus**, lets out a short, barking laugh. He shifts his weight, resting a hand on the hilt of a heavy club at his belt. He doesn't look intimidated; he looks amused by your audacity. "Our side? We're just making sure the right people pay the right prices to walk through these doors, traveler," he sneers, his eyes darting briefly to the heavy pack at your shoulder. Beside him, **Bald Tough** narrows his eyes, his gaze more calculating than his partner's. He steps half a pace closer, cutting off your direct line of sight to the tavern interior. "You've got a loud mouth for a man walking alone at this hour," he mutters, his voice a low threat. "Knowledge is expensive on this road, and you look like you're carrying a heavy purse. Maybe you should just turn around and find a different path." ## Turn 7 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. You reach into your pouch and pull out the heavy roll of silver and iron, dropping the **Credits** onto the dirt at their feet. The coins scatter with a dull, heavy clatter against the stones at the entrance of the *Crossed Keys Inn*. "Caron's coin is paid," you say, trying to project a confidence you don't entirely feel. "Go home and find something else to bother." **Marcus** looks down at the pile of silver, his eyes gleaming with a sudden, sharp greed. He doesn't move to pick it up; instead, he looks at you with a grin that is more a snarl than a smile. "Caron's business is Caron's business, traveler," he says, his voice dropping into a dangerous register. "But our business is right here, right now." Before you can react, **Bald Tough** lunges forward with unexpected speed. He doesn't reach for the money; he throws a heavy, closed fist aimed straight at your solar plexus. The blow connects with a sickening thud, catching you right in your already **bruised ribs**. The pain is a white-hot spike that collapses your lungs, forcing a ragged gasp from your throat as you stumble backward, clutching your side. **Marcus** laughs, a harsh sound that cuts through the cool night air, as he steps over the scattered coins to close the distance between you. "You think you can just toss a few bits at us and walk away?" he sneers, his hand moving toward the heavy club at his belt. "You're not leaving until we decide what you're worth." *That action didn't resolve as expected. Trace `83c84914` — try rephrasing.*

## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 8** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
You pull a heavy wooden chair away from the center of the room and sit across from **Halden** at a corner table. The tavern is thick with the smell of roasted meat and spilled ale, a sharp contrast to the biting chill you left at the gate. Your ribs throb with every breath, a dull, pulsing reminder of the encounter with the crimson-sigiled men outside.

You reach into your heavy coat and pull out the **Stained ledger**, its leather cover cool against your palm. With a steady hand, you slide the heavy merchant seal across the scarred tabletop toward him, followed by the book itself. **Halden** leans forward, his eyes darting nervously toward the tavern door before he focuses on the task at hand. He grips the ledger with trembling fingers, his ink-stained digits tracing the edges of the parchment as if checking for any sign of tampering.

"You actually made it," **Halden** whispers, his voice cracking with a mix of relief and exhaustion. He pulls the book closer to his chest, clutching it like a shield rather than a piece of cargo. He looks at you, his gaze lingering on the shadow of pain etched onto your face. "I told you the roads were dangerous, Voss. I didn't realize just how hungry those vultures had become." He pauses, his eyes searching yours for a moment of unspoken understanding before he begins to frantically check the integrity of the wax seals.

**Turn 9** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
You reach into your pocket and pull out the **Brass key**, its metal cool and heavy in your palm. You stand from the table, ignoring the dull ache in your ribs, and move toward the heavy timber entrance of the *Crossed Keys Inn*. The tavern is still loud with the boisterous chatter of patrons, but you focus on the lock mechanism near the door, trying to find a keyhole that might lead to a more private area or a back room.

You slide the key into the lock, but it meets a stubborn, unyielding resistance. There is no satisfying click; instead, the metal scrapes harshly against the internal tumblers with a grating sound that makes your teeth ache. The key won't turn, jammed by a mechanism that clearly wasn't meant for this specific bit of brass.

**Halden** watches you from his corner table, his eyes wide with a flicker of panic at your sudden movement toward the exit. "What are you doing?" he hisses, leaning forward so his voice won't carry to the boisterous crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."

**Turn 10** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
You lean your weight against the coarse, cold stone of the *Crossed Keys Inn* wall, pressing your ear against the masonry to catch any sound from within. Your breath hitches as the movement agitates your **bruised ribs**, a sharp reminder of the heavy fist you took at the gate. "I have credits. Open up," you whisper into the dark, your voice barely a shadow of a sound against the heavy timber and stone.

With a trembling hand, you pull a single iron coin from your pouch and press it against the base of the wall, a desperate, nonsensical offering to the building itself. There is no response from the stone; no secret latch clicks, and no voice calls out from the other side. The heavy silence of the exterior is broken only by the muffled, boisterous laughter of the patrons inside, oblivious to your shadow-play at the threshold.

**Halden** stands up from his table, his shadow dancing wildly against the wall as he approaches you. He looks around the tavern nervously, his eyes darting toward the heavy doors where the crimson-sigiled men are stationed. "Voss, what in the gods' names are you doing?" he hisses, his voice thick with embarrassment and alarm. "You'll draw every eye in this room to us. Stop your nonsense and sit down before you bring the whole lot of them down on our heads."

*That action didn't resolve as expected. Trace `fa832ea9` — try rephrasing.*

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 2 + 1 +1 (stat) = 4 → FAIL
Directive: The intimidate fails. The attempt fails outright — what you tried to do does not happen.

## momentum (engine-computed, advisory only)
MOMENTUM: LOW (-3). The player has been struggling. Unless the fiction demands
punishment, offer a small break...

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Marrow's Crossing
- **Halden** — last seen Crossed Keys Inn: Standing by the town well, handing over the Stained ledger.
- **Edda**
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Halden (Merchant) — Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## rules_outcome
FAIL on charisma — The intimidate fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`crossed_keys_inn` | Crossed Keys Inn
A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | Halden (Merchant) — Nervously inspecting the ledger, visibly shaken by the danger of the roads and the state of Aren Voss.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `crimson_sigil_threat` [building] Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts. (added turn 4)


⚠ Quest "Deliver Halden's Ledger" stalled for 8 turns.

⚠ Quest "Deliver the Stained Ledger" stalled for 6 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs
- `deliver_stained_ledger` | Deliver the Stained Ledger



## previous_turn_narration (T10 context)
You lean your weight against the coarse, cold stone of the *Crossed Keys Inn* wall, pressing your ear against the masonry to catch any sound from within. Your breath hitches as the movement agitates your **bruised ribs**, a sharp reminder of the heavy fist you took at the gate. "I have credits. Open up," you whisper into the dark, your voice barely a shadow of a sound against the heavy timber and stone.

With a trembling hand, you pull a single iron coin from your pouch and press it against the base of the wall, a desperate, nonsensical offering to the building itself. There is no response from the stone; no secret latch clicks, and no voice calls out from the other side. The heavy silence of the exterior is broken only by the muffled, boisterous laughter of the patrons inside, oblivious to your shadow-play at the threshold.

**Halden** stands up from his table, his shadow dancing wildly against the wall as he approaches you. He looks around the tavern nervously, his eyes darting toward the heavy doors where the crimson-sigiled men are stationed. "Voss, what in the gods' names are you doing?" he hisses, his voice thick with embarrassment and alarm. "You'll draw every eye in this room to us. Stop your nonsense and sit down before you bring the whole lot of them down on our heads."

*That action didn't resolve as expected. Trace `fa832ea9` — try rephrasing.*

## CURRENT TURN NARRATION
You shoulder your way through the thick crowd at the bar, your movement drawing a few curious glances from the boisterous drinkers. Your focus is entirely on **Matthew Estrada**, a man sitting alone at the edge of the heavy oak counter. He is lean and watchful, his eyes moving with a disciplined, rhythmic precision that has nothing to do with the tavern's revelry; he scans the room with the cold, calculating gaze of a soldier looking for a breach in a perimeter.

You reach out and clamp your hand around his wrist, your fingers digging into the coarse fabric of his sleeve. "Who are you really?" you demand, your voice cutting through the ambient noise with a sharp, authoritative edge. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch at your sudden aggression. Instead, his body remains eerily still, his eyes never leaving the heavy tavern doors even as you hold him. He waits a beat, a shadow of a grimace crossing his face, before he calmly reaches up with his free hand and pries your fingers off his arm with a strength that surprises you. He turns his head just enough to meet your gaze, his eyes hard and unforgiving. "You're making a spectacle of yourself, traveler," he says, his voice a low, controlled rasp. "And in a place like this, spectacles tend to get broken."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_domains
scene, inventory

## rules_outcome
FAIL on charisma. The intimidate fails. The attempt fails outright — what you tried to do does not happen.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: fail
directive: The intimidate fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn`

## CURRENT TURN NARRATION
You shoulder your way through the thick crowd at the bar, your movement drawing a few curious glances from the boisterous drinkers. Your focus is entirely on **Matthew Estrada**, a man sitting alone at the edge of the heavy oak counter. He is lean and watchful, his eyes moving with a disciplined, rhythmic precision that has nothing to do with the tavern's revelry; he scans the room with the cold, calculating gaze of a soldier looking for a breach in a perimeter.

You reach out and clamp your hand around his wrist, your fingers digging into the coarse fabric of his sleeve. "Who are you really?" you demand, your voice cutting through the ambient noise with a sharp, authoritative edge. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch at your sudden aggression. Instead, his body remains eerily still, his eyes never leaving the heavy tavern doors even as you hold him. He waits a beat, a shadow of a grimace crossing his face, before he calmly reaches up with his free hand and pries your fingers off his arm with a strength that surprises you. He turns his head just enough to meet your gaze, his eyes hard and unforgiving. "You're making a spectacle of yourself, traveler," he says, his voice a low, controlled rasp. "And in a place like this, spectacles tend to get broken."
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
intimidate: Confront Matthew Estrada to uncover his true identity and motives for his suspicious behavior.
## prior_turn_narration (T9 — for outcome_summary and actions context)
You reach into your pocket and pull out the **Brass key**, its metal cool and heavy in your palm. You stand from the table, ignoring the dull ache in your ribs, and move toward the heavy timber entrance of the *Crossed Keys Inn*. The tavern is still loud with the boisterous chatter of patrons, but you focus on the lock mechanism near the door, trying to find a keyhole that might lead to a more private area or a back room.

You slide the key into the lock, but it meets a stubborn, unyielding resistance. There is no satisfying click; instead, the metal scrapes harshly against the internal tumblers with a grating sound that makes your teeth ache. The key won't turn, jammed by a mechanism that clearly wasn't meant for this specific bit of brass.

**Halden** watches you from his corner table, his eyes wide with a flicker of panic at your sudden movement toward the exit. "What are you doing?" he hisses, leaning forward so his voice won't carry to the boisterous crowd. "Don't go poking around the doors, Voss. Not with those men outside still looking for a reason to start a fight."

## CURRENT TURN NARRATION
You shoulder your way through the thick crowd at the bar, your movement drawing a few curious glances from the boisterous drinkers. Your focus is entirely on **Matthew Estrada**, a man sitting alone at the edge of the heavy oak counter. He is lean and watchful, his eyes moving with a disciplined, rhythmic precision that has nothing to do with the tavern's revelry; he scans the room with the cold, calculating gaze of a soldier looking for a breach in a perimeter.

You reach out and clamp your hand around his wrist, your fingers digging into the coarse fabric of his sleeve. "Who are you really?" you demand, your voice cutting through the ambient noise with a sharp, authoritative edge. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch at your sudden aggression. Instead, his body remains eerily still, his eyes never leaving the heavy tavern doors even as you hold him. He waits a beat, a shadow of a grimace crossing his face, before he calmly reaches up with his free hand and pries your fingers off his arm with a strength that surprises you. He turns his head just enough to meet your gaze, his eyes hard and unforgiving. "You're making a spectacle of yourself, traveler," he says, his voice a low, controlled rasp. "And in a place like this, spectacles tend to get broken."
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
  "total_ms": 2792.8,
  "tokens_in": 1110,
  "tokens_out": 1220,
  "skill": "charisma",
  "difficulty": "normal",
  "dice": [
    2,
    1
  ],
  "stat_mod": 1,
  "diff_mod": 0,
  "cond_mod": 0,
  "final_total": 4,
  "band": "fail",
  "outcome_summary": "Your attempt to intimidate Matthew Estrada fails; he remains unnervingly calm and warns you of the consequences of your spectacle."
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

You shoulder your way through the thick crowd at the bar, your movement drawing a few curious glances from the boisterous drinkers. Your focus is entirely on **Matthew Estrada**, a man sitting alone at the edge of the heavy oak counter. He is lean and watchful, his eyes moving with a disciplined, rhythmic precision that has nothing to do with the tavern's revelry; he scans the room with the cold, calculating gaze of a soldier looking for a breach in a perimeter.

You reach out and clamp your hand around his wrist, your fingers digging into the coarse fabric of his sleeve. "Who are you really?" you demand, your voice cutting through the ambient noise with a sharp, authoritative edge. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch at your sudden aggression. Instead, his body remains eerily still, his eyes never leaving the heavy tavern doors even as you hold him. He waits a beat, a shadow of a grimace crossing his face, before he calmly reaches up with his free hand and pries your fingers off his arm with a strength that surprises you. He turns his head just enough to meet your gaze, his eyes hard and unforgiving. "You're making a spectacle of yourself, traveler," he says, his voice a low, controlled rasp. "And in a place like this, spectacles tend to get broken."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Soldier's Cold Gaze",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously watching the interaction from a distance after Voss's failed intimidation attempt.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "matthew_estrada",
      "notes": "Calmly prying Voss's hand off his wrist; remains watchful of the tavern doors.",
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
    "type": "revelation",
    "surface_as": "npc_behavior",
    "instruction": "As Matthew Estrada settles back into his watchful stance, he subtly shifts his position to block the view of the tavern doors from the rest of the room, suggesting he is intentionally shielding someone or something from view."
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
      "text": "Matthew Estrada displays disciplined, soldier-like behavior and reacts with surprising strength to physical confrontation.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'description': 'Press Matthew further about his military-like surveillance of the room.'}",
    "{'description': \"Back off and observe Matthew's next move from a distance.\"}",
    "{'description': 'Threaten Matthew again to force a more honest response.'}",
    "{'description': 'Scan the tavern for any of the men mentioned by Halden.'}"
  ],
  "outcome_summary": "Your attempt to intimidate Matthew Estrada fails; he remains unnervingly calm and warns you of the consequences of your spectacle."
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
  "scene_tagline": "A Soldier's Cold Gaze",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously watching the interaction from a distance after Voss's failed intimidation attempt."
    },
    {
      "id": "matthew_estrada",
      "notes": "Calmly prying Voss's hand off his wrist; remains watchful of the tavern doors."
    }
  ],
  "recent_events_add": [
    {
      "id": "matthew_estrada_suspicion",
      "text": "Matthew Estrada displays disciplined, soldier-like behavior and reacts with surprising strength to physical confrontation.",
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

- {'description': 'Press Matthew further about his military-like surveillance of the room.'}

- {'description': "Back off and observe Matthew's next move from a distance."}

- {'description': 'Threaten Matthew again to force a more honest response.'}

- {'description': 'Scan the tavern for any of the men mentioned by Halden.'}

### Context Telemetry

- rules: est=1288t trimmed=False
- narrate: est=6548t trimmed=False
- extract.scene: est=4143t trimmed=False attempts=1
- extract.state: est=2244t trimmed=False attempts=1
- extract.progress: est=2105t trimmed=False attempts=1

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
        "last_seen_state": "Sitting at a table in the tavern, tapping a tally stick.",
        "name": "Caron",
        "title": "Old creditor"
      },
      "halden": {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "last_seen": {
          "last_seen_state": "Standing by the town well, handing over the Stained ledger.",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
          "turn": 11
        },
        "last_seen_state": "Standing by the town well, handing over the Stained ledger.",
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
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
          "turn": 11
        },
        "name": "Matthew Estrada",
        "title": "Traveler"
      },
      "tough_a": {
        "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
        "last_seen_state": "Engaged in a physical altercation with Aren Voss outside the inn.",
        "name": "Bald Tough",
        "title": "Road thug"
      },
      "tough_b": {
        "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
        "last_seen_state": "Engaged in a physical altercation with Aren Voss outside the inn.",
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
    }
  ],
  "location": {
    "description": "A warm, bustling tavern filled with the scent of roasted meat and spilled ale, providing a stark contrast to the cold road outside.",
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn"
  },
  "meta": {
    "compendium_touch_order": [],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "As Matthew Estrada settles back into his watchful stance, he subtly shifts his position to block the view of the tavern doors from the rest of the room, suggesting he is intentionally shielding someone or something from view.",
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
    "momentum": -3,
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
    "location_entered_turn": 7,
    "present_npcs": [
      {
        "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
        "id": "halden",
        "name": "Halden",
        "notes": "Nervously watching the interaction from a distance after Voss's failed intimidation attempt.",
        "title": "Merchant"
      },
      {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "id": "matthew_estrada",
        "name": "Matthew Estrada",
        "notes": "Calmly prying Voss's hand off his wrist; remains watchful of the tavern doors.",
        "title": "Traveler"
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
        "id": "meeting_with_caron",
        "text": "Aren Voss meets with Caron at the tavern to discuss debt settlement.",
        "turn": 1
      },
      {
        "id": "crimson_sigil_vultures",
        "text": "The road toughs are organized and wear a crimson sigil on their cloaks.",
        "turn": 2
      },
      {
        "id": "halden_contract_offered",
        "text": "Halden offers 200 credits to deliver the Stained Ledger to the Crossed Keys Inn safely.",
        "turn": 3
      },
      {
        "id": "crimson_sigil_threat",
        "text": "Organized vultures wearing crimson sigils are prowling the merchant roads.",
        "turn": 4
      },
      {
        "id": "crimson_sigil_guards",
        "text": "Two men wearing crimson-sigiled cloaks are guarding the Crossed Keys Inn entrance.",
        "turn": 5
      },
      {
        "id": "ledger_delivered",
        "text": "Voss successfully delivers the stained ledger and merchant seal to Halden.",
        "turn": 7
      },
      {
        "id": "matthew_estrada_suspicion",
        "text": "Matthew Estrada displays disciplined, soldier-like behavior and reacts with surprising strength to physical confrontation.",
        "turn": 10
      }
    ],
    "recently_left": [],
    "recently_left_turns": 0,
    "scene_pressure": [
      {
        "id": "crimson_sigil_threat",
        "max_turns": null,
        "text": "Crimson-sigiled toughs are rumored to be lurking in the dark alleys and outskirts.",
        "turn_added": 4,
        "urgency": "building"
      }
    ],
    "tagline": "A Soldier's Cold Gaze",
    "tags": [
      "dialogue"
    ],
    "turn_entered": 7,
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
| 2 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 2: ['Aren Voss meets with Caron at the tavern to discuss debt settlement.'] |
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Voss'] |
| 3 | `universal.recent_events_add.turn_stamped` | 1 entries had turn=0/null instead of 3: ['The road toughs are organized and wear a crimson sigil on their cloaks.'] |
| 11 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Who', 'Instead', 'Your'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1187 | 2779 | 3693 | 2228 | 1737 | 0 | 0 |
| 3 | 1266 | 3217 | 0 | 2220 | 2200 | 0 | 0 |
| 4 | 1273 | 3532 | 0 | 0 | 2384 | 0 | 0 |
| 5 | 1276 | 3993 | 4064 | 2166 | 2229 | 0 | 0 |
| 6 | 1280 | 4530 | 0 | 2316 | 2221 | 0 | 0 |
| 7 | 1281 | 4966 | 0 | 2386 | 2180 | 0 | 0 |
| 8 | 1277 | 5437 | 4229 | 2289 | 2231 | 0 | 0 |
| 9 | 1276 | 6031 | 0 | 2172 | 2158 | 0 | 0 |
| 10 | 1281 | 6283 | 0 | 2315 | 2185 | 0 | 0 |
| 11 | 1288 | 6548 | 4143 | 2244 | 2105 | 0 | 0 |

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + progress | 2 | `- You arrived in Marrow's Crossing after three days on the r / - You heard rumors of road-toughs extorting travelers near t / - You found Caron in the tavern — he's been waiting for you.` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |

## Compaction Features
*(compaction did not fire during this run — likely because the run was shorter than `compact_every`. Judge: do not score compaction capabilities for this run; note this in your verdict.)*
