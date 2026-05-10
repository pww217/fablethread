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

`location_description`: A short prose description of the current location's notable features.
**Before emitting, run this checklist:**
1. Does the narration contain NEW spatial, atmospheric, or structural details about the location?
2. Are those details absent from `## current_location_description` in the user prompt?
3. If the answer to BOTH is yes → emit the description.
4. If the answer to EITHER is no → set `location_description` to `null`.

**Default to null on uncertainty.** Omission is safer than redundant re-description.
If the narration only confirms the player is still in the same location without adding
environmental details, set to `null`.

`npc_add`: new NPCs entering the scene this turn. Each: `{"id": "snake_case", "notes": "current situation", "name": "Full Name", "title": "Role", "bio": "1-3 sentences"}`. Only include name/title/bio for genuinely new NPCs not in the compendium. Omit name/title/bio for ambient/extra NPCs. If an NPC was previously unnamed (referred to by descriptor), check the compendium roster — if it's the same character, use `npc_update` instead of `npc_add`. **Compendium NPCs are NOT in the scene by default. Emit `npc_add` for any NPC mentioned in the narration that is NOT in `present_npcs`, even if they appear in the compendium roster.**

**Compendium pre-check before npc_add:** Before adding an NPC, check the `## known_characters` list. If the NPC is already in the compendium (marked with [compendium] tag), do NOT emit `npc_add` — instead emit `npc_update` if their notes changed, or emit nothing if nothing changed. Only emit `npc_add` for genuinely new NPCs not in the compendium roster.

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
  "outcome_summary": ""
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
=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===
 /no_think
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
- `caron` | Caron (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- `halden` | Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs

## CURRENT TURN NARRATION
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."
## END CURRENT TURN NARRATION
 /no_think
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
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn`
(location changed)
## CURRENT TURN NARRATION
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
1

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player approaches Caron to discuss the repayment of their debt.
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
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
  "rolled": false,
  "total_ms": 9285.6,
  "tokens_in": 1224,
  "tokens_out": 1307
}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
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

The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Debt To Settle",
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight."
  },
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Hunched over a mug, tapping his tobacco-stained fingers impatiently; watching Voss with sharp, unforgiving eyes.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "innkeeper",
      "notes": "Wiping the bar at the Crossed Keys, glancing sideways at the noise of the chair.",
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
    "instruction": "As Caron waits for your response, he subtly shifts his weight, revealing a heavy, iron-bound ledger tucked partially beneath his bench\u2014the very item he is demanding from you."
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
    "{'text': 'Explain your current situation and propose a repayment plan.'}",
    "{'text': 'Offer him a portion of your current earnings immediately.'}",
    "{'text': 'Ask Caron if he has any work for a courier.'}",
    "{'text': 'Order a drink from Edda to settle your nerves.'}"
  ],
  "outcome_summary": "You successfully located Caron at the Crossed Keys Inn and confronted him about your debt."
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
    "description": "A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight."
  },
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
    "dialogue"
  ],
  "scene_tagline": "A Debt To Settle",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Hunched over a mug, tapping his tobacco-stained fingers impatiently; watching Voss with sharp, unforgiving eyes."
    },
    {
      "id": "innkeeper",
      "notes": "Wiping the bar at the Crossed Keys, glancing sideways at the noise of the chair."
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

- {'text': 'Explain your current situation and propose a repayment plan.'}

- {'text': 'Offer him a portion of your current earnings immediately.'}

- {'text': 'Ask Caron if he has any work for a courier.'}

- {'text': 'Order a drink from Edda to settle your nerves.'}

### Context Telemetry

- rules: est=1398t trimmed=False
- narrate: est=2943t trimmed=False
- extract.scene: est=3904t trimmed=False attempts=1
- extract.state: est=2549t trimmed=False attempts=1
- extract.progress: est=2617t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
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
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
          "turn": 1
        },
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
    "description": "A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.",
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn"
  },
  "meta": {
    "compendium_touch_order": [],
    "game_name": "eval",
    "last_compacted_turn": 0,
    "model": "",
    "pending_gm_beat": {
      "instruction": "As Caron waits for your response, he subtly shifts his weight, revealing a heavy, iron-bound ledger tucked partially beneath his bench\u2014the very item he is demanding from you.",
      "surface_as": "npc_behavior",
      "type": "revelation"
    },
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
    "location_entered_turn": 0,
    "present_npcs": [
      {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "id": "caron",
        "name": "Caron",
        "notes": "Hunched over a mug, tapping his tobacco-stained fingers impatiently; watching Voss with sharp, unforgiving eyes.",
        "title": "Old creditor"
      },
      {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "id": "innkeeper",
        "name": "Edda",
        "notes": "Wiping the bar at the Crossed Keys, glancing sideways at the noise of the chair.",
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
    "recently_left": [],
    "recently_left_turns": 0,
    "scene_pressure": [],
    "tagline": "A Debt To Settle",
    "tags": [
      "dialogue"
    ],
    "turn_entered": 0,
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
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T1: Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt. — … hat you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

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
Crossed Keys Inn (crossed_keys_inn)
A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.

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
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

GM DIRECTION (REVELATION, surface as npc_behavior):
As Caron waits for your response, he subtly shifts his weight, revealing a heavy, iron-bound ledger tucked partially beneath his bench—the very item he is demanding from you.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Hunched over a mug, tapping his tobacco-stained fingers impatiently; watching Voss with sharp, unforgiving eyes.
- Edda (Innkeeper at the Crossed Keys) — Wiping the bar at the Crossed Keys, glancing sideways at the noise of the chair.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`crossed_keys_inn` | Crossed Keys Inn
A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor) — Hunched over a mug, tapping his tobacco-stained fingers impatiently; watching Voss with sharp, unforgiving eyes.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping the bar at the Crossed Keys, glancing sideways at the noise of the chair.

_(immutable section omitted — see Static Context > Seed State)_

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `settle_the_debt` | Settle the Old Debt
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T1 context)
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

## CURRENT TURN NARRATION
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."
## END CURRENT TURN NARRATION
 /no_think
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
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn`

## CURRENT TURN NARRATION
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
2

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player attempts to settle their debt by paying 500 credits to Caron.
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

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## items_lost
credits

## CURRENT TURN NARRATION
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to settle their debt by paying 500 credits to Caron.",
  "rolled": false,
  "total_ms": 2542.9,
  "tokens_in": 1301,
  "tokens_out": 1389
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to settle their debt by paying 500 credits to Caron.",
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

You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "A Debt Paid In Gold",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "innkeeper",
      "notes": "Wiping the bar, observing the tension at the table.",
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
    "instruction": "Caron's predatory grin widens as he subtly shifts his weight, making it clear he is more interested in the ledger Voss is carrying than the 500 credits on the table."
  }
}
```

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
  "quest_updates": [
    {
      "id": "settle_the_debt",
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
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Demand Caron explain why he is eyeing your cargo",
    "Offer Caron more information in exchange for total freedom",
    "Intimidate Caron to keep him from touching your belongings",
    "Scan the tavern for any suspicious onlookers or threats"
  ],
  "outcome_summary": "You successfully present the 500 credits to Caron, but his attention shifts suspiciously toward the ledger you are carrying."
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
  "quest_updates": [
    {
      "id": "settle_the_debt",
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
  "scene_tagline": "A Debt Paid In Gold",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench."
    },
    {
      "id": "innkeeper",
      "notes": "Wiping the bar, observing the tension at the table."
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

- Demand Caron explain why he is eyeing your cargo

- Offer Caron more information in exchange for total freedom

- Intimidate Caron to keep him from touching your belongings

- Scan the tavern for any suspicious onlookers or threats

### Context Telemetry

- rules: est=1477t trimmed=False
- narrate: est=3409t trimmed=False
- extract.scene: est=4218t trimmed=False attempts=1
- extract.state: est=2542t trimmed=False attempts=1
- extract.progress: est=2624t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "last_seen": {
          "turn": {
            "from": 1,
            "to": 2
          }
        }
      },
      "innkeeper": {
        "last_seen": {
          "turn": {
            "from": 1,
            "to": 2
          }
        }
      }
    }
  },
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
      "instruction": {
        "from": "As Caron waits for your response, he subtly shifts his weight, revealing a heavy, iron-bound ledger tucked partially beneath his bench\u2014the very item he is demanding from you.",
        "to": "Caron's predatory grin widens as he subtly shifts his weight, making it clear he is more interested in the ledger Voss is carrying than the 500 credits on the table."
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
          "last_advanced_turn": 1,
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
    "present_npcs": {
      "changed": [
        {
          "from": {
            "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
            "id": "caron",
            "name": "Caron",
            "notes": "Hunched over a mug, tapping his tobacco-stained fingers impatiently; watching Voss with sharp, unforgiving eyes.",
            "title": "Old creditor"
          },
          "to": {
            "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
            "id": "caron",
            "name": "Caron",
            "notes": "Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.",
            "title": "Old creditor"
          }
        },
        {
          "from": {
            "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
            "id": "innkeeper",
            "name": "Edda",
            "notes": "Wiping the bar at the Crossed Keys, glancing sideways at the noise of the chair.",
            "title": "Innkeeper at the Crossed Keys"
          },
          "to": {
            "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
            "id": "innkeeper",
            "name": "Edda",
            "notes": "Wiping the bar, observing the tension at the table.",
            "title": "Innkeeper at the Crossed Keys"
          }
        }
      ]
    },
    "tagline": {
      "from": "A Debt To Settle",
      "to": "A Debt Paid In Gold"
    }
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
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T2: I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger. — … rade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

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
Crossed Keys Inn (crossed_keys_inn)
A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.

## inventory (cross-reference before describing item use)
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
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

**Turn 2** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: easy
Roll: 3 + 4 +1 (stat) +1 (diff) = 9 → PARTIAL
Directive: The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (REVELATION, surface as npc_behavior):
Caron's predatory grin widens as he subtly shifts his weight, making it clear he is more interested in the ledger Voss is carrying than the 500 credits on the table.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.
- Edda (Innkeeper at the Crossed Keys) — Wiping the bar, observing the tension at the table.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on charisma — The negotiate results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`crossed_keys_inn` | Crossed Keys Inn
A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor) — Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping the bar, observing the tension at the table.

_(immutable section omitted — see Static Context > Seed State)_

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T2 context)
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

## CURRENT TURN NARRATION
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
location_change, quest_updates, inventory, scene, compendium_npc

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
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrows_crossing_center`
(location changed)
## CURRENT TURN NARRATION
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
3

## active_domains
location_change, quest_updates, inventory, scene, compendium_npc

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
negotiate: The player offers to perform a delivery service for Halden in exchange for 200 credits.
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

## prior_turn_narration (T1 — for outcome_summary and actions context)
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

## items_gained
heavy satchel

## items_lost
credits

## CURRENT TURN NARRATION
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player offers to perform a delivery service for Halden in exchange for 200 credits.",
  "rolled": true,
  "total_ms": 3100.0,
  "tokens_in": 1305,
  "tokens_out": 1427,
  "skill": "charisma",
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
  "outcome_summary": "You successfully negotiated a 200-credit fee and secured the heavy satchel from Halden."
}
```

**Raw LLM output:**
```
{
  "intent": "The player offers to perform a delivery service for Halden in exchange for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "[Mechanical cost: loss of potential income] + [Narrative consequence: Halden refuses the offer or finds someone else to carry the ledger]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue",
    "exploration"
  ],
  "scene_tagline": "A Heavy Burden Accepted",
  "location_change": {
    "id": "marrows_crossing_center",
    "name": "Marrow's Crossing Center",
    "description": "A muddy town center centered around a stone well, lit by flickering street lanterns that cast long shadows across the sludge-filled streets."
  },
  "location_description": null,
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron",
      "last_seen_state": "Sitting alone at a table in the Crossed Keys Inn with the player's credits."
    },
    {
      "id": "innkeeper",
      "last_seen_state": "Observing the tension at the table inside the inn."
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Nervously handing a heavy satchel to Voss for delivery to the inn.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "halden_satchel_target",
      "text": "The heavy satchel Halden entrusted to you makes you a visible target for those watching the town.",
      "urgency": "building",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "revelation",
    "surface_as": "ambient",
    "instruction": "As Voss turns away from Halden, a pair of hooded figures near the town well pause their conversation and watch the exchange with intense, unblinking scrutiny."
  }
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "heavy_satchel",
      "name": "heavy satchel",
      "notes": "A heavy satchel containing a delivery for the Crossed Keys Inn.",
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
      "id": "halden_delivery_contract",
      "text": "Halden has entrusted Voss with a heavy, secretive satchel for delivery to the Crossed Keys Inn.",
      "turn": 3
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "{'text': 'Head back to the Crossed Keys to deliver the satchel.'}",
    "{'text': 'Search the immediate area around the well for suspicious eyes.'}",
    "{'text': 'Ask Halden more questions about the dangers on the road.'}",
    "{'text': 'Look for a quieter route back to the inn.'}"
  ],
  "outcome_summary": "You successfully negotiated a 200-credit fee and secured the heavy satchel from Halden."
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

- {'text': 'Head back to the Crossed Keys to deliver the satchel.'}

- {'text': 'Search the immediate area around the well for suspicious eyes.'}

- {'text': 'Ask Halden more questions about the dangers on the road.'}

- {'text': 'Look for a quieter route back to the inn.'}

### Context Telemetry

- rules: est=1484t trimmed=False
- narrate: est=3810t trimmed=False
- extract.scene: est=4302t trimmed=False attempts=1
- extract.state: est=2632t trimmed=False attempts=1
- extract.progress: est=2913t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "pending_gm_beat": {
      "instruction": {
        "from": "Caron's predatory grin widens as he subtly shifts his weight, making it clear he is more interested in the ledger Voss is carrying than the 500 credits on the table.",
        "to": "As Voss turns away from Halden, a pair of hooded figures near the town well pause their conversation and watch the exchange with intense, unblinking scrutiny."
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      }
    },
    "turn": {
      "from": 2,
      "to": 3
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
Location: Crossed Keys Inn
## last_turn (tail of the most recent narrative)
T3: I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits. — … ing both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

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
Crossed Keys Inn (crossed_keys_inn)
A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.

## inventory (cross-reference before describing item use)
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
The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."

**Turn 2** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

**Turn 3** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

GM DIRECTION (REVELATION, surface as ambient):
As Voss turns away from Halden, a pair of hooded figures near the town well pause their conversation and watch the exchange with intense, unblinking scrutiny.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive


NARRATE: No roll was required. Describe what happens with appropriate weight for the moment.




## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- Caron (Old creditor) — Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.
- Edda (Innkeeper at the Crossed Keys) — Wiping the bar, observing the tension at the table.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`crossed_keys_inn` | Crossed Keys Inn
A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (Old creditor) — Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Wiping the bar, observing the tension at the table.

_(immutable section omitted — see Static Context > Seed State)_

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T3 context)
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

## CURRENT TURN NARRATION
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
scene, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Apply inventory and condition changes based on what the narration describes — do NOT infer success or failure from a roll outcome.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `marrow_crossing_outskirts`
(location changed)
## CURRENT TURN NARRATION
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
4

## active_domains
scene, inventory

## no_dice_roll
No dice were rolled this turn. The rules engine determined the action has no mechanical obstacle (pure social, travel, or exploration). Do NOT complete quest objectives on this turn unless the narration explicitly and unambiguously states the objective is fulfilled.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
move: The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
## prior_turn_narration (T2 — for outcome_summary and actions context)
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

## CURRENT TURN NARRATION
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "move",
  "intent": "The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
  "rolled": false,
  "total_ms": 2508.0,
  "tokens_in": 1312,
  "tokens_out": 1397
}
```

**Raw LLM output:**
```
{
  "intent": "The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
  "intent_verb": "move",
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

The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

### Extract Scene

```json
{
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Eyes In The Shadows",
  "location_change": {
    "id": "marrow_crossing_outskirts",
    "name": "Marrow's Crossing Outskirts",
    "description": "A murky, uncertain gloom at the edge of town where the timbered east gate meets the winding merchant road."
  },
  "location_description": null,
  "npc_add": [
    {
      "id": "hooded_figure_1",
      "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
      "name": null,
      "title": "Hooded Figure",
      "bio": null
    },
    {
      "id": "hooded_figure_2",
      "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
      "name": null,
      "title": "Hooded Figure",
      "bio": null
    }
  ],
  "npc_remove": [],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "watchful_eyes",
      "text": "Two hooded figures are tracking your movement from the shadows of the east gate.",
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
    "instruction": "As Voss nears the inn, one of the hooded figures from the alcove breaks their silence, calling out a low, mocking whistle that echoes through the trees to signal the others."
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
      "id": "hooded_figures_watching",
      "text": "Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Quickly reach the Crossed Keys Inn to find safety.",
    "Stop and confront the hooded figures watching from the shadows.",
    "Scan the tree lines for any more movement or threats.",
    "Check the satchel to ensure the contents are secure."
  ],
  "outcome_summary": "You exit Marrow's Crossing under the unsettling gaze of two hooded figures, heading toward the Crossed Keys Inn."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "marrow_crossing_outskirts",
    "name": "Marrow's Crossing Outskirts",
    "description": "A murky, uncertain gloom at the edge of town where the timbered east gate meets the winding merchant road."
  },
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Eyes In The Shadows",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "hooded_figure_1",
      "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
      "title": "Hooded Figure"
    },
    {
      "id": "hooded_figure_2",
      "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
      "title": "Hooded Figure"
    }
  ],
  "npc_remove": [],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "hooded_figures_watching",
      "text": "Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "watchful_eyes",
      "text": "Two hooded figures are tracking your movement from the shadows of the east gate.",
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

- Quickly reach the Crossed Keys Inn to find safety.

- Stop and confront the hooded figures watching from the shadows.

- Scan the tree lines for any more movement or threats.

- Check the satchel to ensure the contents are secure.

### Context Telemetry

- rules: est=1486t trimmed=False
- narrate: est=4251t trimmed=False
- extract.scene: est=4414t trimmed=False attempts=1
- extract.state: est=2521t trimmed=False attempts=1
- extract.progress: est=2777t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "hooded_figure_1": {
        "from": null,
        "to": {
          "bio": "",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "marrow_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 4
          },
          "name": "",
          "title": "Hooded Figure"
        }
      },
      "hooded_figure_2": {
        "from": null,
        "to": {
          "bio": "",
          "last_seen": {
            "last_seen_state": "",
            "location_id": "marrow_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 4
          },
          "name": "",
          "title": "Hooded Figure"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A tavern filled with the scent of stale ale and woodsmoke, lit by flickering candlelight.",
      "to": "A murky, uncertain gloom at the edge of town where the timbered east gate meets the winding merchant road."
    },
    "id": {
      "from": "crossed_keys_inn",
      "to": "marrow_crossing_outskirts"
    },
    "name": {
      "from": "Crossed Keys Inn",
      "to": "Marrow's Crossing Outskirts"
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "hooded_figure_1",
        "hooded_figure_2"
      ],
      "removed": []
    },
    "pending_gm_beat": {
      "instruction": {
        "from": "As Voss turns away from Halden, a pair of hooded figures near the town well pause their conversation and watch the exchange with intense, unblinking scrutiny.",
        "to": "As Voss nears the inn, one of the hooded figures from the alcove breaks their silence, calling out a low, mocking whistle that echoes through the trees to signal the others."
      },
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
      "from": 3,
      "to": 4
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 0,
      "to": 3
    },
    "present_npcs": {
      "added": [
        {
          "bio": "",
          "id": "hooded_figure_1",
          "name": "",
          "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
          "title": "Hooded Figure"
        },
        {
          "bio": "",
          "id": "hooded_figure_2",
          "name": "",
          "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
          "title": "Hooded Figure"
        }
      ],
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Watching Voss with a predatory grin; has an iron-bound ledger hidden under his bench.",
          "title": "Old creditor"
        },
        {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "id": "innkeeper",
          "name": "Edda",
          "notes": "Wiping the bar, observing the tension at the table.",
          "title": "Innkeeper at the Crossed Keys"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "hooded_figures_watching",
          "text": "Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.",
          "turn": 4
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "watchful_eyes",
          "max_turns": null,
          "text": "Two hooded figures are tracking your movement from the shadows of the east gate.",
          "turn_added": 3,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "A Debt Paid In Gold",
      "to": "Eyes In The Shadows"
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
      "from": 0,
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
Location: Marrow's Crossing Outskirts
## last_turn (tail of the most recent narrative)
T4: I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road. — … ng with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

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
Marrow's Crossing Outskirts (marrow_crossing_outskirts)
A murky, uncertain gloom at the edge of town where the timbered east gate meets the winding merchant road.

## inventory (cross-reference before describing item use)
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
- [BUILDING] Two hooded figures are tracking your movement from the shadows of the east gate.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.

## Prior History (summarized — treat as background, not current scene)



## Turn 1 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 2** — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."

**Turn 3** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

**Turn 4** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 1 + 3 +1 (stat) = 5 → FAIL
Directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As Voss nears the inn, one of the hooded figures from the alcove breaks their silence, calling out a low, mocking whistle that echoes through the trees to signal the others.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Marrow's Crossing Outskirts
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
- **Bald Tough**
- **Scarred Tough**
## NPCs Present in Scene
- hooded_figure_1 (Hooded Figure) — Standing motionless in a stone alcove near the town well, watching Voss pass.
- hooded_figure_2 (Hooded Figure) — Standing motionless in a stone alcove near the town well, watching Voss pass.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
FAIL on charisma — The persuade fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale

## location
`marrow_crossing_outskirts` | Marrow's Crossing Outskirts
A murky, uncertain gloom at the edge of town where the timbered east gate meets the winding merchant road.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `hooded_figure_1` | hooded_figure_1 (Hooded Figure) — Standing motionless in a stone alcove near the town well, watching Voss pass.
- `hooded_figure_2` | hooded_figure_2 (Hooded Figure) — Standing motionless in a stone alcove near the town well, watching Voss pass.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `watchful_eyes` [building] Two hooded figures are tracking your movement from the shadows of the east gate. (added turn 3)


## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T4 context)
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

## CURRENT TURN NARRATION
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

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
location: `crossed_keys_inn_entrance`
(location changed)
## CURRENT TURN NARRATION
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
5

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player confronts the two toughs at the inn door to demand an explanation for their presence.
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
- Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.

## prior_turn_narration (T3 — for outcome_summary and actions context)
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

## CURRENT TURN NARRATION
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player confronts the two toughs at the inn door to demand an explanation for their presence.",
  "rolled": true,
  "total_ms": 3246.4,
  "tokens_in": 1303,
  "tokens_out": 1434,
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
  "outcome_summary": "Your attempt to persuade the thugs fails, leaving you face-to-face with two armed men demanding a toll."
}
```

**Raw LLM output:**
```
{
  "intent": "The player confronts the two toughs at the inn door to demand an explanation for their presence.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "[Mechanical cost: charisma check] + [Narrative consequence: the toughs may become hostile or refuse to speak, potentially leading to a confrontation or being barred from the inn]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

### Extract Scene

```json
{
  "scene_tags": [
    "combat"
  ],
  "scene_tagline": "A Toll Paid In Blood",
  "location_change": {
    "id": "crossed_keys_inn_entrance",
    "name": "Crossed Keys Inn Entrance",
    "description": "The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins."
  },
  "location_description": null,
  "npc_add": [
    {
      "id": "scarred_tough",
      "notes": "Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.",
      "name": "Scarred Tough",
      "title": "Road Tough",
      "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road."
    },
    {
      "id": "bald_tough",
      "notes": "A massive man with a shaved head and a missing ear, flanking the Scarred Tough.",
      "name": "Bald Tough",
      "title": "Road Tough",
      "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle."
    }
  ],
  "npc_remove": [
    {
      "id": "hooded_figure_1",
      "last_seen_state": "Watching from the stone alcove near the town well."
    },
    {
      "id": "hooded_figure_2",
      "last_seen_state": "Watching from the stone alcove near the town well."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "road_tax_confrontation",
      "text": "The Scarred Tough and his companion are blocking the inn entrance and demanding a tax.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "scene_pressure_remove": [
    "watchful_eyes"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "The Scarred Tough reaches for his heavy club, signaling to the Bald Tough to tighten the circle around Voss, making a peaceful exit through the inn doors impossible."
  }
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
      "description": "The aggressive confrontation with the inn guards has rattled your composure."
    }
  ],
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
      "id": "inn_toughs_confrontation",
      "text": "Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Try to bribe the Scarred Tough to let you pass.",
    "Threaten the thugs with your physical presence to clear the way.",
    "Demand to know who is paying them to block the inn.",
    "Look around the muddy street for a way to bypass them."
  ],
  "outcome_summary": "Your attempt to persuade the thugs fails, leaving you face-to-face with two armed men demanding a toll."
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
    "description": "The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins."
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
  "pc_condition_add": [
    {
      "id": "shaken",
      "label": "shaken",
      "description": "The aggressive confrontation with the inn guards has rattled your composure."
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "combat"
  ],
  "scene_tagline": "A Toll Paid In Blood",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "scarred_tough",
      "notes": "Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.",
      "name": "Scarred Tough",
      "title": "Road Tough",
      "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road."
    },
    {
      "id": "bald_tough",
      "notes": "A massive man with a shaved head and a missing ear, flanking the Scarred Tough.",
      "name": "Bald Tough",
      "title": "Road Tough",
      "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle."
    }
  ],
  "npc_remove": [
    {
      "id": "hooded_figure_1",
      "last_seen_state": "Watching from the stone alcove near the town well."
    },
    {
      "id": "hooded_figure_2",
      "last_seen_state": "Watching from the stone alcove near the town well."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "inn_toughs_confrontation",
      "text": "Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "road_tax_confrontation",
      "text": "The Scarred Tough and his companion are blocking the inn entrance and demanding a tax.",
      "urgency": "immediate",
      "turn_added": 0
    }
  ],
  "scene_pressure_remove": [
    "watchful_eyes"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Try to bribe the Scarred Tough to let you pass.

- Threaten the thugs with your physical presence to clear the way.

- Demand to know who is paying them to block the inn.

- Look around the muddy street for a way to bypass them.

### Context Telemetry

- rules: est=1492t trimmed=False
- narrate: est=4974t trimmed=False
- extract.scene: est=4475t trimmed=False attempts=2
- extract.state: est=2689t trimmed=False attempts=1
- extract.progress: est=3131t trimmed=False attempts=1

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
            "turn": 5
          }
        }
      },
      "hooded_figure_1": {
        "last_seen_state": {
          "from": null,
          "to": "Watching from the stone alcove near the town well."
        }
      },
      "hooded_figure_2": {
        "last_seen_state": {
          "from": null,
          "to": "Watching from the stone alcove near the town well."
        }
      },
      "scarred_tough": {
        "from": null,
        "to": {
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 5
          }
        }
      },
      "tough_a": {
        "bio": {
          "from": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "to": "A thick-necked enforcer for the road tax, known for his mocking whistle."
        },
        "title": {
          "from": "Road thug",
          "to": "Road Tough"
        }
      },
      "tough_b": {
        "bio": {
          "from": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "to": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road."
        },
        "title": {
          "from": "Road thug",
          "to": "Road Tough"
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "A murky, uncertain gloom at the edge of town where the timbered east gate meets the winding merchant road.",
      "to": "The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins."
    },
    "id": {
      "from": "marrow_crossing_outskirts",
      "to": "crossed_keys_inn_entrance"
    },
    "name": {
      "from": "Marrow's Crossing Outskirts",
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
      "instruction": {
        "from": "As Voss nears the inn, one of the hooded figures from the alcove breaks their silence, calling out a low, mocking whistle that echoes through the trees to signal the others.",
        "to": "The Scarred Tough reaches for his heavy club, signaling to the Bald Tough to tighten the circle around Voss, making a peaceful exit through the inn doors impossible."
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
          "description": "The aggressive confrontation with the inn guards has rattled your composure.",
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
          "last_advanced_turn": 4,
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
      "from": 3,
      "to": 4
    },
    "present_npcs": {
      "added": [
        {
          "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.",
          "title": "Road Tough"
        },
        {
          "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "A massive man with a shaved head and a missing ear, flanking the Scarred Tough.",
          "title": "Road Tough"
        }
      ],
      "removed": [
        {
          "bio": "",
          "id": "hooded_figure_1",
          "name": "",
          "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
          "title": "Hooded Figure"
        },
        {
          "bio": "",
          "id": "hooded_figure_2",
          "name": "",
          "notes": "Standing motionless in a stone alcove near the town well, watching Voss pass.",
          "title": "Hooded Figure"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "inn_toughs_confrontation",
          "text": "Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.",
          "turn": 5
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "road_tax_confrontation",
          "max_turns": null,
          "text": "The Scarred Tough and his companion are blocking the inn entrance and demanding a tax.",
          "turn_added": 4,
          "urgency": "immediate"
        }
      ],
      "removed": [
        {
          "id": "watchful_eyes",
          "max_turns": null,
          "text": "Two hooded figures are tracking your movement from the shadows of the east gate.",
          "turn_added": 3,
          "urgency": "building"
        }
      ]
    },
    "tagline": {
      "from": "Eyes In The Shadows",
      "to": "A Toll Paid In Blood"
    },
    "tags": {
      "added": [
        "combat"
      ],
      "removed": [
        "exploration"
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T5: I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side. — … han a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.

## inventory (cross-reference before describing item use)
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
- [IMMEDIATE] The Scarred Tough and his companion are blocking the inn entrance and demanding a tax.
## Recent Events
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.
- Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.

## Prior History (summarized — treat as background, not current scene)



## Turn 1 — Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.

The heavy scent of stale ale and woodsmoke hangs thick in the air of the Crossed Keys Inn as you navigate the narrow aisle toward the corner. **Caron** doesn't look up immediately; he remains hunched over his mug, his eyes fixed on the amber liquid as if searching for answers in the dregs. His skin looks like weathered parchment under the flickering candlelight, and his fingers, stained with tobacco, tap a rhythmic, impatient beat against the scarred wood of the table.

As you pull out the heavy chair, the wood groans against the floorboards, drawing a brief, sideways glance from **Edda** behind the bar. She returns to her wiping, her expression unreadable. Caron finally lifts his gaze, his eyes sharp and unforgiving, cutting through your fatigue. He doesn't offer a greeting or a seat of welcome; he simply stares at you for a long moment, gauging your resolve.

"You look like hell, Voss," Caron says, his voice a low rasp that barely carries over the distant murmur of the tavern. He pushes his half-empty mug aside, clearing a small space on the table between you. "The road hasn't been kind to your ribs or your luck. But luck won't settle what you owe me. Sit. Let's see if you've actually brought what I expect, or if I've wasted my time waiting for a ghost."


## Turn 2 — I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.

You reach into your pouch and pull out your 500 **Credits**, the heavy coins clinking as you slide them across the scarred wood toward him. The metallic sound rings clear against the low hum of the tavern, drawing a momentary silence from the patrons nearest your table. You lean forward, your bruised ribs protesting the movement, and meet his unforgiving stare with steady eyes. "The money is here," you say, your voice low but firm. "Mark it. I want this debt cleared."

**Caron** doesn't reach for the coins immediately. Instead, his eyes flick down to the pile of gold, then shift toward the shadows beneath his bench. As he shifts his weight to lean closer, the movement pulls his heavy coat aside, revealing the corner of a thick, iron-bound ledger tucked partially under the seat. 

A slow, predatory grin spreads across his weathered face, though it doesn't reach his eyes. He swipes the coins toward his side of the table with a swift, practiced motion of his tobacco-stained fingers. "You've got the coin, I'll give you that," he rasps, his hand hovering near the hidden book. "But a man who pays so readily usually has something else to trade. You're carrying more than just your weight, aren't you, Voss? I can smell the ink and parchment on you from here."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 3** — I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
The heavy atmosphere of the inn remains coiled around you as you stand, leaving Caron alone with your 500 credits and that unsettling, hungry look in his eyes. You push through the heavy timber doors of the Crossed Keys Inn, the cool night air of Marrow's Crossing biting at your face and offering a momentary respite from the woodsmoke. 

You navigate the muddy streets toward the center of town, your boots squelching in the sludge left by the afternoon's rain. Near the stone rim of the town well, where the light of a flickering street lantern casts long, dancing shadows, you spot **Halden**. He is a stout man with a frantic energy, his eyes darting toward every passing shadow as he adjusts a heavy satchel at his hip. 

"You're the runner, aren't you?" **Halden** asks, his voice hushed and hurried as you approach. He wipes sweat from his brow despite the chill, his eyes scanning your broad shoulders and your worn **Traveler's cloak**. "I need this delivered to the inn, and I need it done without eyes on it. The roads aren't what they used to be." 

You lean in close, your voice barely a whisper above the distant sound of the river. "I'll take it to the Crossed Keys. Two hundred credits for the trip, and I'll ensure it stays out of sight." 

**Halden** hesitates, his fingers tightening around the strap of his satchel, before he gives a curt, nervous nod. "Two hundred. It's steep, but I can't afford a delay. Take it. Just... keep your head down, Voss. There are eyes in this town that don't care for honest business." He thrusts the heavy satchel toward you, the weight of it promising both profit and a target on your back.

*That action didn't resolve as expected. Trace `767d5224` — try rephrasing.*

**Turn 4** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

**Turn 5** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 3 + 5 +1 (stat) = 9 → PARTIAL
Directive: The deceive results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (COMPLICATION, surface as npc_behavior):
The Scarred Tough reaches for his heavy club, signaling to the Bald Tough to tighten the circle around Voss, making a peaceful exit through the inn doors impossible.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Crossed Keys Inn Entrance
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
- **** — last seen Crossed Keys Inn Entrance
## NPCs Present in Scene
- Scarred Tough (Road Tough) — Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.
- Bald Tough (Road Tough) — A massive man with a shaved head and a missing ear, flanking the Scarred Tough.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on charisma — The deceive results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_entrance` | Crossed Keys Inn Entrance
The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_b` | Scarred Tough (Road Tough) — Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.
- `tough_a` | Bald Tough (Road Tough) — A massive man with a shaved head and a missing ear, flanking the Scarred Tough.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `road_tax_confrontation` [immediate] The Scarred Tough and his companion are blocking the inn entrance and demanding a tax. (added turn 4)


## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T5 context)
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

## CURRENT TURN NARRATION
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
PARTIAL on charisma. The deceive results in a partial. You get what you asked for, but they now hold leverage over you.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: partial
directive: The deceive results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road

## active_conditions
- `bruised_ribs` | bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- `low_morale` | low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.
- `shaken` | shaken — The aggressive confrontation with the inn guards has rattled your composure.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_entrance`

## CURRENT TURN NARRATION
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
6

## active_domains
scene, inventory, pc_condition, quest_updates, location_change, recent_events, compendium_npc

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
deceive: The player attempts to bribe the toughs with 200 credits to convince them to leave peacefully.
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
- Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.
- Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.

## prior_turn_narration (T4 — for outcome_summary and actions context)
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

## items_lost
credits

## CURRENT TURN NARRATION
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "deceive",
  "intent": "The player attempts to bribe the toughs with 200 credits to convince them to leave peacefully.",
  "rolled": true,
  "total_ms": 3117.5,
  "tokens_in": 1312,
  "tokens_out": 1434,
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
  "outcome_summary": "Your attempt to bribe the thugs fails as they realize they can extort even more from you, and they prepare to attack."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the toughs with 200 credits to convince them to leave peacefully.",
  "intent_verb": "deceive",
  "target": "the two toughs",
  "stakes": "[Mechanical cost: charisma check] + [Narrative consequence: the toughs reject the bribe and initiate a violent confrontation]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

### Extract Scene

```json
{
  "scene_tags": [
    "combat"
  ],
  "scene_tagline": "The Tax Just Went Up",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_b",
      "notes": "Has drawn his club and is now openly threatening Voss, claiming the bribe was a lie and demanding more.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "tough_a",
      "notes": "Stepping forward aggressively to flank Voss and block the path to the inn.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "road_tax_confrontation",
      "text": "The Scarred Tough has drawn his weapon and the Bald Tough is closing in; they are no longer just demanding a tax, they are actively threatening violence to seize more.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "As the Scarred Tough moves to strike, the Bald Tough reaches out with a meaty hand to grab the strap of Voss's satchel, attempting to rip it from his shoulder during the scuffle."
  }
}
```

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
      "description": "Your lie has backfired, leaving you indebted to the thugs' whims."
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
      "id": "thugs_refuse_bribe",
      "text": "The thugs rejected the 200 credit bribe and are now threatening Aren Voss for more.",
      "turn": 6
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Draw your iron dagger and prepare for a fight.",
    "Try to bluff again or offer more credits to de-escalate.",
    "Attempt to push past the Bald Tough toward the inn.",
    "Call out for help from patrons inside the Crossed Keys."
  ],
  "outcome_summary": "Your attempt to bribe the thugs fails as they realize they can extort even more from you, and they prepare to attack."
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

- Draw your iron dagger and prepare for a fight.

- Try to bluff again or offer more credits to de-escalate.

- Attempt to push past the Bald Tough toward the inn.

- Call out for help from patrons inside the Crossed Keys.

### Context Telemetry

- rules: est=1495t trimmed=False
- narrate: est=5509t trimmed=False
- extract.scene: est=4450t trimmed=False attempts=1
- extract.state: est=2688t trimmed=False attempts=1
- extract.progress: est=3100t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "bald_tough": {
        "from": {
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 5
          }
        },
        "to": null
      },
      "scarred_tough": {
        "from": {
          "last_seen": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 5
          }
        },
        "to": null
      }
    }
  },
  "meta": {
    "last_compacted_turn": {
      "from": 0,
      "to": 3
    },
    "pending_gm_beat": {
      "instruction": {
        "from": "The Scarred Tough reaches for his heavy club, signaling to the Bald Tough to tighten the circle around Voss, making a peaceful exit through the inn doors impossible.",
        "to": "As the Scarred Tough moves to strike, the Bald Tough reaches out with a meaty hand to grab the strap of Voss's satchel, attempting to rip it from his shoulder during the scuffle."
      }
    },
    "prior_history": {
      "added": [
        "- [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.",
        "- [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits.",
        "- [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight."
      ],
      "removed": []
    },
    "turn": {
      "from": 5,
      "to": 6
    }
  },
  "scene": {
    "recent_events": {
      "added": [
        {
          "id": "debt_settled",
          "text": "You have settled your debt with Caron, though his eyes remain hungry for more than just coin.",
          "turn": 2
        },
        {
          "id": "halden_contract",
          "text": "Halden has entrusted you with a heavy satchel to be delivered to the Crossed Keys Inn.",
          "turn": 3
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
          "id": "hooded_figures_watching",
          "text": "Two hooded figures in a stone alcove near the well watched Aren Voss leave the town with suspicious silence.",
          "turn": 4
        }
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T6: I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now. — … is eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.

## inventory (cross-reference before describing item use)
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
- [IMMEDIATE] The Scarred Tough and his companion are blocking the inn entrance and demanding a tax.
## Recent Events
- You have settled your debt with Caron, though his eyes remain hungry for more than just coin.
- Halden has entrusted you with a heavy satchel to be delivered to the Crossed Keys Inn.
- Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.
- [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight.
- [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits.



## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 4** — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.

**Turn 5** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

**Turn 6** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 6 + 1 +1 (stat) = 8 → PARTIAL
Directive: The persuade results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As the Scarred Tough moves to strike, the Bald Tough reaches out with a meaty hand to grab the strap of Voss's satchel, attempting to rip it from his shoulder during the scuffle.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Bald Tough**
- **Scarred Tough**
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Marrow's Crossing Outskirts
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
## NPCs Present in Scene
- Scarred Tough (Road Tough) — Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.
- Bald Tough (Road Tough) — A massive man with a shaved head and a missing ear, flanking the Scarred Tough.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on charisma — The persuade results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_entrance` | Crossed Keys Inn Entrance
The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_b` | Scarred Tough (Road Tough) — Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.
- `tough_a` | Bald Tough (Road Tough) — A massive man with a shaved head and a missing ear, flanking the Scarred Tough.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `road_tax_confrontation` [immediate] The Scarred Tough and his companion are blocking the inn entrance and demanding a tax. (added turn 4)


⚠ Quest "Deliver Halden's Ledger" stalled for 3 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T6 context)
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

## CURRENT TURN NARRATION
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
scene, inventory

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

## scene_result
location: `crossed_keys_inn_entrance`

## CURRENT TURN NARRATION
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
7

## active_domains
scene, inventory

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to use the merchant seal and ledger to prove their authority or payment status to Halden.
## prior_turn_narration (T5 — for outcome_summary and actions context)
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

## CURRENT TURN NARRATION
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to use the merchant seal and ledger to prove their authority or payment status to Halden.",
  "rolled": true,
  "total_ms": 3125.9,
  "tokens_in": 1314,
  "tokens_out": 1437,
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
  "outcome_summary": "Your attempt to use the merchant's authority only incited more violence, leaving you caught between a club swing and a brute grabbing your satchel."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use the merchant seal and ledger to prove their authority or payment status to Halden.",
  "intent_verb": "persuade",
  "target": "Halden",
  "stakes": "[Mechanical cost: charisma check] + [Narrative consequence: Halden rejects the proof and demands more credits or escalates the confrontation]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

### Extract Scene

```json
{
  "scene_tags": [
    "combat"
  ],
  "scene_tagline": "The Satchel Is Under Siege",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_b",
      "notes": "Lunged with a club at the player's ribs after a moment of hesitation.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "tough_a",
      "notes": "Lunged from the flank and is violently grabbing the player's satchel strap.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "road_tax_confrontation",
      "text": "The Bald Tough is actively attempting to steal the player's satchel while the Scarred Tough attacks.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "As the Bald Tough yanks on the satchel, the leather strap begins to fray and crack under the tension, threatening to spill Halden's Ledger into the mud during the struggle."
  }
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
      "description": "The brute's violent yank on your satchel has caused sharp, localized pain in your ribcage."
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
      "id": "thugs_ambush_inn",
      "text": "Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Wrestle the satchel back from the Bald Tough's grip.",
    "Strike the Scarred Tough to prevent his club from swinging again.",
    "Threaten the thugs with the authority of the merchant seal.",
    "Attempt to break free and flee toward the inn entrance."
  ],
  "outcome_summary": "Your attempt to use the merchant's authority only incited more violence, leaving you caught between a club swing and a brute grabbing your satchel."
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
    "combat"
  ],
  "scene_tagline": "The Satchel Is Under Siege",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_b",
      "notes": "Lunged with a club at the player's ribs after a moment of hesitation."
    },
    {
      "id": "tough_a",
      "notes": "Lunged from the flank and is violently grabbing the player's satchel strap."
    }
  ],
  "recent_events_add": [
    {
      "id": "thugs_ambush_inn",
      "text": "Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "road_tax_confrontation",
      "text": "The Bald Tough is actively attempting to steal the player's satchel while the Scarred Tough attacks.",
      "urgency": "immediate",
      "turn_added": 0
    }
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Wrestle the satchel back from the Bald Tough's grip.

- Strike the Scarred Tough to prevent his club from swinging again.

- Threaten the thugs with the authority of the merchant seal.

- Attempt to break free and flee toward the inn entrance.

### Context Telemetry

- rules: est=1491t trimmed=False
- narrate: est=4690t trimmed=False
- extract.scene: est=4385t trimmed=False attempts=1
- extract.state: est=2509t trimmed=False attempts=1
- extract.progress: est=2707t trimmed=False attempts=1

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
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 7
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "from": null,
          "to": {
            "last_seen_state": "",
            "location_id": "crossed_keys_inn_entrance",
            "location_name": "Crossed Keys Inn Entrance",
            "turn": 7
          }
        }
      }
    }
  },
  "meta": {
    "pending_gm_beat": {
      "instruction": {
        "from": "As the Scarred Tough moves to strike, the Bald Tough reaches out with a meaty hand to grab the strap of Voss's satchel, attempting to rip it from his shoulder during the scuffle.",
        "to": "As the Bald Tough yanks on the satchel, the leather strap begins to fray and crack under the tension, threatening to spill Halden's Ledger into the mud during the struggle."
      }
    },
    "turn": {
      "from": 6,
      "to": 7
    }
  },
  "scene": {
    "present_npcs": {
      "changed": [
        {
          "from": {
            "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Leaning against the inn doorframe, demanding a tax and eyeing the player's satchel.",
            "title": "Road Tough"
          },
          "to": {
            "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Lunged with a club at the player's ribs after a moment of hesitation.",
            "title": "Road Tough"
          }
        },
        {
          "from": {
            "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "A massive man with a shaved head and a missing ear, flanking the Scarred Tough.",
            "title": "Road Tough"
          },
          "to": {
            "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Lunged from the flank and is violently grabbing the player's satchel strap.",
            "title": "Road Tough"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "thugs_ambush_inn",
          "text": "Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.",
          "turn": 7
        }
      ]
    },
    "scene_pressure": {
      "changed": [
        {
          "from": {
            "id": "road_tax_confrontation",
            "max_turns": null,
            "text": "The Scarred Tough and his companion are blocking the inn entrance and demanding a tax.",
            "turn_added": 4,
            "urgency": "immediate"
          },
          "to": {
            "id": "road_tax_confrontation",
            "max_turns": null,
            "text": "The Bald Tough is actively attempting to steal the player's satchel while the Scarred Tough attacks.",
            "turn_added": 4,
            "urgency": "immediate"
          }
        }
      ]
    },
    "tagline": {
      "from": "A Toll Paid In Blood",
      "to": "The Satchel Is Under Siege"
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T7: I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat. — … igging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.

## inventory (cross-reference before describing item use)
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
- [IMMEDIATE] The Bald Tough is actively attempting to steal the player's satchel while the Scarred Tough attacks.
## Recent Events
- You have settled your debt with Caron, though his eyes remain hungry for more than just coin.
- Halden has entrusted you with a heavy satchel to be delivered to the Crossed Keys Inn.
- Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.
- Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.
- [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight.
- [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."

**Turn 6** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

**Turn 7** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Dexterity (3) | Difficulty: easy
Roll: 6 + 2 +1 (stat) +1 (diff) = 10 → SUCCESS
Directive: The sneak succeeds cleanly. Clean success — you do what you intended.

GM DIRECTION (COMPLICATION, surface as npc_behavior):
As the Bald Tough yanks on the satchel, the leather strap begins to fray and crack under the tension, threatening to spill Halden's Ledger into the mud during the struggle.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



RESOLUTION: The action lands. Deliver the outcome clearly — one physical, concrete consequence.

BREATHE: A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn. Show the aftermath, not the next crisis.






## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Bald Tough** — last seen Crossed Keys Inn Entrance
- **Scarred Tough** — last seen Crossed Keys Inn Entrance
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Marrow's Crossing Outskirts
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
## NPCs Present in Scene
- Scarred Tough (Road Tough) — Lunged with a club at the player's ribs after a moment of hesitation.
- Bald Tough (Road Tough) — Lunged from the flank and is violently grabbing the player's satchel strap.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
SUCCESS on dexterity — The sneak succeeds cleanly. Clean success — you do what you intended.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_entrance` | Crossed Keys Inn Entrance
The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_b` | Scarred Tough (Road Tough) — Lunged with a club at the player's ribs after a moment of hesitation.
- `tough_a` | Bald Tough (Road Tough) — Lunged from the flank and is violently grabbing the player's satchel strap.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `road_tax_confrontation` [immediate] The Bald Tough is actively attempting to steal the player's satchel while the Scarred Tough attacks. (added turn 4)

## deescalate
true — player succeeded on a check against active pressure. Do NOT add new pressures. Downgrade or remove existing ones.

⚠ Quest "Deliver Halden's Ledger" stalled for 4 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T7 context)
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

## CURRENT TURN NARRATION
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
location_change, inventory

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
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_entrance`
(location changed)
## CURRENT TURN NARRATION
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
8

## active_domains
location_change, inventory

## rules_outcome
SUCCESS on dexterity.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
sneak: The player attempts to use a brass key to unlock the inn's front door or find a back room.
## prior_turn_narration (T6 — for outcome_summary and actions context)
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

## CURRENT TURN NARRATION
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "sneak",
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find a back room.",
  "rolled": true,
  "total_ms": 3134.5,
  "tokens_in": 1309,
  "tokens_out": 1433,
  "skill": "dexterity",
  "difficulty": "easy",
  "dice": [
    6,
    2
  ],
  "stat_mod": 1,
  "diff_mod": 1,
  "cond_mod": 0,
  "final_total": 10,
  "band": "success",
  "outcome_summary": "You successfully use the brass key to unlock the inn's door and slip inside, momentarily escaping the thugs' reach."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find a back room.",
  "intent_verb": "sneak",
  "target": "inn's front door",
  "stakes": "[Mechanical cost: dexterity check] + [Narrative consequence: the door remains locked or an alarm/guard is alerted]",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "easy",
    "tags": []
  }
}
```

### Narration

The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.

### Extract Scene

```json
{
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Sanctuary Behind Heavy Timber",
  "location_change": {
    "id": "crossed_keys_inn_entrance",
    "name": "Crossed Keys Inn Entrance",
    "description": "A dim, musk-scented entryway providing a momentary reprieve from the damp street."
  },
  "location_description": null,
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Attempting to wrench the satchel from the player's shoulder outside the door."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Swinging a club at the player just as they ducked through the door."
    }
  ],
  "npc_update": [],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "road_tax_confrontation"
  ],
  "scene_pressure_update": [],
  "gm_beat": {
    "type": "breathing_room",
    "surface_as": "ambient",
    "instruction": "As the heavy door thuds shut, Edda the innkeeper looks up from the counter with a furrowed brow, her eyes darting between the frantic player and the muffled shouting of the thugs outside."
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
      "id": "inn_entry_escape",
      "text": "Voss successfully used the brass key to slip into the inn, narrowly escaping the thugs' grasp.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Bolt deeper into the inn to find a crowded room.",
    "Search for a back exit or a cellar entrance.",
    "Call out to the innkeeper for help or protection.",
    "Hide behind the entryway counter to catch your breath."
  ],
  "outcome_summary": "You successfully use the brass key to unlock the inn's door and slip inside, momentarily escaping the thugs' reach."
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
    "description": "A dim, musk-scented entryway providing a momentary reprieve from the damp street."
  },
  "quest_updates": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "exploration"
  ],
  "scene_tagline": "Sanctuary Behind Heavy Timber",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Attempting to wrench the satchel from the player's shoulder outside the door."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Swinging a club at the player just as they ducked through the door."
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "inn_entry_escape",
      "text": "Voss successfully used the brass key to slip into the inn, narrowly escaping the thugs' grasp.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [
    "road_tax_confrontation"
  ],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Bolt deeper into the inn to find a crowded room.

- Search for a back exit or a cellar entrance.

- Call out to the innkeeper for help or protection.

- Hide behind the entryway counter to catch your breath.

### Context Telemetry

- rules: est=1492t trimmed=False
- narrate: est=5168t trimmed=False
- extract.scene: est=4393t trimmed=False attempts=1
- extract.state: est=2553t trimmed=False attempts=1
- extract.progress: est=2746t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "tough_a": {
        "last_seen_state": {
          "from": null,
          "to": "Attempting to wrench the satchel from the player's shoulder outside the door."
        }
      },
      "tough_b": {
        "last_seen_state": {
          "from": null,
          "to": "Swinging a club at the player just as they ducked through the door."
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The heavy timber doors of the inn are blocked by two aggressive men in leather jerkins.",
      "to": "A dim, musk-scented entryway providing a momentary reprieve from the damp street."
    }
  },
  "meta": {
    "pending_gm_beat": {
      "instruction": {
        "from": "As the Bald Tough yanks on the satchel, the leather strap begins to fray and crack under the tension, threatening to spill Halden's Ledger into the mud during the struggle.",
        "to": "As the heavy door thuds shut, Edda the innkeeper looks up from the counter with a furrowed brow, her eyes darting between the frantic player and the muffled shouting of the thugs outside."
      },
      "surface_as": {
        "from": "npc_behavior",
        "to": "ambient"
      },
      "type": {
        "from": "complication",
        "to": "breathing_room"
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
  "scene": {
    "location_entered_turn": {
      "from": 4,
      "to": 7
    },
    "present_npcs": {
      "removed": [
        {
          "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Lunged with a club at the player's ribs after a moment of hesitation.",
          "title": "Road Tough"
        },
        {
          "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Lunged from the flank and is violently grabbing the player's satchel strap.",
          "title": "Road Tough"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "inn_entry_escape",
          "text": "Voss successfully used the brass key to slip into the inn, narrowly escaping the thugs' grasp.",
          "turn": 8
        }
      ]
    },
    "scene_pressure": {
      "removed": [
        {
          "id": "road_tax_confrontation",
          "max_turns": null,
          "text": "The Bald Tough is actively attempting to steal the player's satchel while the Scarred Tough attacks.",
          "turn_added": 4,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "The Satchel Is Under Siege",
      "to": "Sanctuary Behind Heavy Timber"
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
      "from": 4,
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T8: I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room. — … ub—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
A dim, musk-scented entryway providing a momentary reprieve from the damp street.

## inventory (cross-reference before describing item use)
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
- You have settled your debt with Caron, though his eyes remain hungry for more than just coin.
- Halden has entrusted you with a heavy satchel to be delivered to the Crossed Keys Inn.
- Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.
- Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.
- Voss successfully used the brass key to slip into the inn, narrowly escaping the thugs' grasp.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.
- [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight.
- [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.


## Turn 5 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 6** — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*

**Turn 7** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

**Turn 8** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 1 + 3 +1 (stat) = 5 → FAIL
Directive: The persuade fails. The attempt fails outright — what you tried to do does not happen.

GM DIRECTION (BREATHING_ROOM, surface as ambient):
As the heavy door thuds shut, Edda the innkeeper looks up from the counter with a furrowed brow, her eyes darting between the frantic player and the muffled shouting of the thugs outside.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



CONSEQUENCE: The action failed. One cost. Don't pile on. If crit_fail, the cost is severe — injury, loss, exposure.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Bald Tough** — last seen Crossed Keys Inn Entrance
- **Scarred Tough** — last seen Crossed Keys Inn Entrance
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Marrow's Crossing Outskirts
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn
- **Matthew Estrada**
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
FAIL on charisma — The persuade fails. The attempt fails outright — what you tried to do does not happen.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_entrance` | Crossed Keys Inn Entrance
A dim, musk-scented entryway providing a momentary reprieve from the damp street.

_(immutable section omitted — see Static Context > Seed State)_

⚠ Quest "Deliver Halden's Ledger" stalled for 5 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T8 context)
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.

## CURRENT TURN NARRATION
The heavy timber door thuds shut behind you, momentarily muffling the frantic scuffling and the curses of the thugs outside. You lean your weight against the wood, your breath coming in shallow, ragged gasps as your bruised ribs protest every movement. Desperation claws at your throat; your attempt to manipulate your way into the inn's good graces or perhaps bribe your way through the very architecture fails spectacularly. 

You press your ear against the cold, damp stone of the entryway wall, your voice a frantic, low whisper. "I have credits. Open up," you hiss into the masonry, your fingers fumbling for a single coin. You press a lone credit against the rough surface of the wall, a gesture as absurd as it is futile. The stone remains indifferent, cold and unyielding, offering no mechanical or magical response to your pathetic offering. 

The silence of the entryway is broken by the heavy, rhythmic thudding of fists against the door from the outside. "Open this door, runner!" the **Scarred Tough** bellows, his voice muffled but brimming with malice. 

From behind the low, polished wood of the service counter, **Edda** looks up. She is a woman with sharp, observant eyes and hair pulled back in a tight, practical knot, her face etched with the weary patience of someone who has seen too many petty brawls. She stares at you, her brow furrowed in confusion and annoyance as she watches you press your face against the wall. 

"Whatever trouble you've brought to my doorstep, keep it out there," **Edda** snaps, her voice cutting through your frantic state like a knife. She eyes your disheveled appearance and the heavy satchel, her expression hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
scene, compendium_npc, inventory

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

## scene_result
location: `crossed_keys_inn_entrance`

## CURRENT TURN NARRATION
The heavy timber door thuds shut behind you, momentarily muffling the frantic scuffling and the curses of the thugs outside. You lean your weight against the wood, your breath coming in shallow, ragged gasps as your bruised ribs protest every movement. Desperation claws at your throat; your attempt to manipulate your way into the inn's good graces or perhaps bribe your way through the very architecture fails spectacularly. 

You press your ear against the cold, damp stone of the entryway wall, your voice a frantic, low whisper. "I have credits. Open up," you hiss into the masonry, your fingers fumbling for a single coin. You press a lone credit against the rough surface of the wall, a gesture as absurd as it is futile. The stone remains indifferent, cold and unyielding, offering no mechanical or magical response to your pathetic offering. 

The silence of the entryway is broken by the heavy, rhythmic thudding of fists against the door from the outside. "Open this door, runner!" the **Scarred Tough** bellows, his voice muffled but brimming with malice. 

From behind the low, polished wood of the service counter, **Edda** looks up. She is a woman with sharp, observant eyes and hair pulled back in a tight, practical knot, her face etched with the weary patience of someone who has seen too many petty brawls. She stares at you, her brow furrowed in confusion and annoyance as she watches you press your face against the wall. 

"Whatever trouble you've brought to my doorstep, keep it out there," **Edda** snaps, her voice cutting through your frantic state like a knife. She eyes your disheveled appearance and the heavy satchel, her expression hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
9

## active_domains
scene, compendium_npc, inventory

## rules_outcome
FAIL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
persuade: The player attempts to bribe or persuade someone inside the inn to open the door using a single credit.
## prior_turn_narration (T7 — for outcome_summary and actions context)
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

## CURRENT TURN NARRATION
The heavy timber door thuds shut behind you, momentarily muffling the frantic scuffling and the curses of the thugs outside. You lean your weight against the wood, your breath coming in shallow, ragged gasps as your bruised ribs protest every movement. Desperation claws at your throat; your attempt to manipulate your way into the inn's good graces or perhaps bribe your way through the very architecture fails spectacularly. 

You press your ear against the cold, damp stone of the entryway wall, your voice a frantic, low whisper. "I have credits. Open up," you hiss into the masonry, your fingers fumbling for a single coin. You press a lone credit against the rough surface of the wall, a gesture as absurd as it is futile. The stone remains indifferent, cold and unyielding, offering no mechanical or magical response to your pathetic offering. 

The silence of the entryway is broken by the heavy, rhythmic thudding of fists against the door from the outside. "Open this door, runner!" the **Scarred Tough** bellows, his voice muffled but brimming with malice. 

From behind the low, polished wood of the service counter, **Edda** looks up. She is a woman with sharp, observant eyes and hair pulled back in a tight, practical knot, her face etched with the weary patience of someone who has seen too many petty brawls. She stares at you, her brow furrowed in confusion and annoyance as she watches you press your face against the wall. 

"Whatever trouble you've brought to my doorstep, keep it out there," **Edda** snaps, her voice cutting through your frantic state like a knife. She eyes your disheveled appearance and the heavy satchel, her expression hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "The player attempts to bribe or persuade someone inside the inn to open the door using a single credit.",
  "rolled": true,
  "total_ms": 3098.7,
  "tokens_in": 1307,
  "tokens_out": 1429,
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
  "outcome_summary": "Your desperate attempt to bribe the wall fails, leaving you trapped in the entryway while the thugs pound on the door and Edda watches with disdain."
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe or persuade someone inside the inn to open the door using a single credit.",
  "intent_verb": "persuade",
  "target": "occupants of the inn",
  "stakes": "[Mechanical cost: charisma check] + [Narrative consequence: the occupants ignore the plea or react aggressively to the interruption]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

The heavy timber door thuds shut behind you, momentarily muffling the frantic scuffling and the curses of the thugs outside. You lean your weight against the wood, your breath coming in shallow, ragged gasps as your bruised ribs protest every movement. Desperation claws at your throat; your attempt to manipulate your way into the inn's good graces or perhaps bribe your way through the very architecture fails spectacularly. 

You press your ear against the cold, damp stone of the entryway wall, your voice a frantic, low whisper. "I have credits. Open up," you hiss into the masonry, your fingers fumbling for a single coin. You press a lone credit against the rough surface of the wall, a gesture as absurd as it is futile. The stone remains indifferent, cold and unyielding, offering no mechanical or magical response to your pathetic offering. 

The silence of the entryway is broken by the heavy, rhythmic thudding of fists against the door from the outside. "Open this door, runner!" the **Scarred Tough** bellows, his voice muffled but brimming with malice. 

From behind the low, polished wood of the service counter, **Edda** looks up. She is a woman with sharp, observant eyes and hair pulled back in a tight, practical knot, her face etched with the weary patience of someone who has seen too many petty brawls. She stares at you, her brow furrowed in confusion and annoyance as she watches you press your face against the wall. 

"Whatever trouble you've brought to my doorstep, keep it out there," **Edda** snaps, her voice cutting through your frantic state like a knife. She eyes your disheveled appearance and the heavy satchel, her expression hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue"
  ],
  "scene_tagline": "No Sanctuary For Bribes",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Struggling with the player's satchel outside the door."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Bellowing threats and pounding on the door from the outside."
    }
  ],
  "npc_update": [
    {
      "id": "innkeeper",
      "notes": "Annoyed and suspicious of the player's frantic behavior and the thugs outside.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [
    {
      "id": "thugs_at_door",
      "text": "The Scarred Tough and Bald Tough are pounding on the door, demanding entry.",
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
    "instruction": "Edda slams a heavy iron latch onto the door to secure it, but the impact causes the wood to shudder violently under the Scarred Tough's heavy blows, signaling that the door won't hold for long."
  }
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
      "description": "Painful rib injuries making breathing difficult and movement labored."
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
      "id": "thugs_at_the_door",
      "text": "The Scarred Tough and Bald Tough are pounding on the inn door, demanding entry.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Beg Edda for sanctuary and offer the satchel as collateral.",
    "Barricade the door with furniture to stall the thugs.",
    "Try to reason with Edda about the danger outside.",
    "Search the entryway for a secondary exit or hiding spot."
  ],
  "outcome_summary": "Your desperate attempt to bribe the wall fails, leaving you trapped in the entryway while the thugs pound on the door and Edda watches with disdain."
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
  "scene_tagline": "No Sanctuary For Bribes",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a",
      "last_seen_state": "Struggling with the player's satchel outside the door."
    },
    {
      "id": "tough_b",
      "last_seen_state": "Bellowing threats and pounding on the door from the outside."
    }
  ],
  "npc_update": [
    {
      "id": "innkeeper",
      "notes": "Annoyed and suspicious of the player's frantic behavior and the thugs outside."
    }
  ],
  "recent_events_add": [
    {
      "id": "thugs_at_the_door",
      "text": "The Scarred Tough and Bald Tough are pounding on the inn door, demanding entry.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "thugs_at_door",
      "text": "The Scarred Tough and Bald Tough are pounding on the door, demanding entry.",
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

- Beg Edda for sanctuary and offer the satchel as collateral.

- Barricade the door with furniture to stall the thugs.

- Try to reason with Edda about the danger outside.

- Search the entryway for a secondary exit or hiding spot.

### Context Telemetry

- rules: est=1497t trimmed=False
- narrate: est=5509t trimmed=False
- extract.scene: est=4343t trimmed=False attempts=1
- extract.state: est=2648t trimmed=False attempts=1
- extract.progress: est=2768t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "innkeeper": {
        "last_seen": {
          "location_id": {
            "from": "crossed_keys_inn",
            "to": "crossed_keys_inn_entrance"
          },
          "location_name": {
            "from": "Crossed Keys Inn",
            "to": "Crossed Keys Inn Entrance"
          },
          "turn": {
            "from": 2,
            "to": 9
          }
        }
      },
      "tough_a": {
        "last_seen_state": {
          "from": "Attempting to wrench the satchel from the player's shoulder outside the door.",
          "to": "Struggling with the player's satchel outside the door."
        }
      },
      "tough_b": {
        "last_seen_state": {
          "from": "Swinging a club at the player just as they ducked through the door.",
          "to": "Bellowing threats and pounding on the door from the outside."
        }
      }
    }
  },
  "meta": {
    "pending_gm_beat": {
      "instruction": {
        "from": "As the heavy door thuds shut, Edda the innkeeper looks up from the counter with a furrowed brow, her eyes darting between the frantic player and the muffled shouting of the thugs outside.",
        "to": "Edda slams a heavy iron latch onto the door to secure it, but the impact causes the wood to shudder violently under the Scarred Tough's heavy blows, signaling that the door won't hold for long."
      },
      "surface_as": {
        "from": "ambient",
        "to": "npc_behavior"
      },
      "type": {
        "from": "breathing_room",
        "to": "complication"
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
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "id": "innkeeper",
          "name": "Edda",
          "notes": "Annoyed and suspicious of the player's frantic behavior and the thugs outside.",
          "title": "Innkeeper at the Crossed Keys"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "thugs_at_the_door",
          "text": "The Scarred Tough and Bald Tough are pounding on the inn door, demanding entry.",
          "turn": 9
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "thugs_at_door",
          "max_turns": null,
          "text": "The Scarred Tough and Bald Tough are pounding on the door, demanding entry.",
          "turn_added": 8,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "Sanctuary Behind Heavy Timber",
      "to": "No Sanctuary For Bribes"
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
Location: Crossed Keys Inn Entrance
## last_turn (tail of the most recent narrative)
T9: I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall. — … hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."

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
Crossed Keys Inn Entrance (crossed_keys_inn_entrance)
A dim, musk-scented entryway providing a momentary reprieve from the damp street.

## inventory (cross-reference before describing item use)
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
- [IMMEDIATE] The Scarred Tough and Bald Tough are pounding on the door, demanding entry.
## Recent Events
- You have settled your debt with Caron, though his eyes remain hungry for more than just coin.
- Halden has entrusted you with a heavy satchel to be delivered to the Crossed Keys Inn.
- Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.
- Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.
- Voss successfully used the brass key to slip into the inn, narrowly escaping the thugs' grasp.
- The Scarred Tough and Bald Tough are pounding on the inn door, demanding entry.

## Prior History (summarized — treat as background, not current scene)



## COMPACTED
- [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.
- [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight.
- [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits.

## Turn 4 — I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.

The weight of the satchel pulls at your shoulder, a constant, heavy reminder of your new contract. You turn your back on the town well, your boots churning through the thickening sludge of the streets as you head toward the east gate. The air grows colder as you approach the town's edge, the flickering light of the street lanterns falling behind you, leaving the outskirts in a murky, uncertain gloom. 

As you pass through the timbered archway of the east gate, your eyes catch a flicker of movement near the well you just left. Two hooded figures stand motionless in the shadows of a stone alcove, their conversation abruptly silenced as you pass. They don't move or speak, but you can feel their unblinking scrutiny boring into your back, tracking your progress toward the merchant road with a silence that feels more heavy than any spoken threat. 

You keep your head low, pulling your **Traveler's cloak** tighter against your chest to mask the shape of the satchel. The merchant road stretches out before you, a winding ribbon of mud and stone that leads back toward the warmth and noise of the Crossed Keys Inn. Every snap of a dry twig or rustle of wind in the riverside reeds makes your hand drift instinctively toward your **Iron dagger**, your eyes scanning the dark tree lines that flank the path. 

The inn looms ahead in the distance, its windows glowing like low-burning embers against the dark skyline of Marrow's Crossing. You quicken your pace, your bruised ribs throbbing with every heavy stride, driven by the need to finish this delivery and put the watchful eyes of the town behind you.


## Turn 5 — I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.

The heavy timber doors of the Crossed Keys Inn loom ahead, but your path is barred by two men leaning against the doorframe. They aren't the silent observers from the well; these men are broad-shouldered and thick-necked, wearing stained leather jerkins that suggest a life of petty violence. One of them, a man with a jagged scar running through his left eyebrow, pushes off the wood as you approach, his hand resting provocatively on a heavy club tucked into his belt. 

"You've got a lot of nerve, runner," the **Scarred Tough** sneers, his eyes flicking toward the heavy satchel at your side before settling on your face. He doesn't look intimidated by your broad shoulders or your steady gaze; instead, he looks amused, as if your presence is a minor inconvenience to his evening's work. "We aren't here for your questions. We're here because this road has a new tax, and you look like you're carrying a heavy purse."

The second man, a massive fellow with a shaved head and a missing ear, lets out a low, mocking whistle that rings through the damp air, a signal that carries a sharp, condescending edge. He steps forward to flank his companion, closing the distance and cutting off your direct line of approach to the entrance. 

"Move along, Voss," the **Scarred Tough** commands, his voice dropping to a threatening rumble as he steps into your personal space. "The inn is closed to your kind tonight unless you've got something more interesting than a mouth full of questions. Unless, of course, you're looking to settle your business with us right here in the mud."


## Turn 6 — I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.

You reach into your pouch and pull out 200 **Credits**, letting them fall from your hand. The heavy coins hit the muddy ground with a series of dull, metallic thuds, scattering amidst the sludge between your boots and theirs. "Caron's coin is paid," you say, your voice steady despite the throbbing in your ribs. "The debt is settled. Now clear the way and go home."

The **Scarred Tough** looks down at the scattered gold, his eyes glinting with a sudden, sharp greed. He doesn't reach for the money, though; instead, his hand shifts from his side to the heavy club at his belt. A slow, malicious grin curls his lips, revealing teeth stained by tobacco. "Caron's coin? That's a pretty lie, runner," he sneers, his fingers wrapping tightly around the wood of his weapon. "But if Caron's paying your taxes now, then he's paying ours too."

The **Bald Tough** doesn't wait for a command. He steps forward with a heavy, rhythmic stomp, his massive frame closing the gap to your left and cutting off your path toward the inn's entrance. He looms over you like a mountain of scarred flesh, his missing ear a jagged red notch in the dim light. 

The **Scarred Tough** draws his club from his belt with a whistling scrape of leather. "You think you can just toss a few coins and walk away? You've made this interesting, Voss. Now we know exactly what your business is worth." He gestures toward your satchel with the weapon, his eyes narrowing. "The tax just went up."

*That action didn't resolve as expected. Trace `3d9c6bdb` — try rephrasing.*




## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 7** — I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
The **Scarred Tough** lunges forward, his club whistling through the air toward your ribs, but your words and the sight of the gold cause a momentary flicker of hesitation in his eyes. He doesn't stand down, but he hesitates just long enough for your words to sink in—the implication that your business is worth more than a petty bribe. 

However, your attempt to buy your way out of the confrontation backfires as the **Bald Tough** reacts to your confidence. As the **Scarred Tough** swings, the massive man lunges from your flank, his meaty hand snaking out to grab the heavy strap of your satchel. He jerks it violently toward him, attempting to tear the weight from your shoulder and rip your contract away before you can even react to the club's approach. 

The weight of the satchel yanks your shoulder painfully, your bruised ribs screaming as your body is jerked sideways by the brute's strength. You manage to sidestep the worst of the club's arc, but the **Bald Tough** has a firm, bruising grip on your cargo, his eyes fixed on the heavy bulge of Halden's property. 

"You're not going anywhere with that," the **Bald Tough** grunts, his fingers digging into your shoulder through your **Traveler's cloak**. "If you won't pay the tax in coin, you'll pay it in goods."

**Turn 8** — I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.

**Turn 9** — I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
The heavy timber door thuds shut behind you, momentarily muffling the frantic scuffling and the curses of the thugs outside. You lean your weight against the wood, your breath coming in shallow, ragged gasps as your bruised ribs protest every movement. Desperation claws at your throat; your attempt to manipulate your way into the inn's good graces or perhaps bribe your way through the very architecture fails spectacularly. 

You press your ear against the cold, damp stone of the entryway wall, your voice a frantic, low whisper. "I have credits. Open up," you hiss into the masonry, your fingers fumbling for a single coin. You press a lone credit against the rough surface of the wall, a gesture as absurd as it is futile. The stone remains indifferent, cold and unyielding, offering no mechanical or magical response to your pathetic offering. 

The silence of the entryway is broken by the heavy, rhythmic thudding of fists against the door from the outside. "Open this door, runner!" the **Scarred Tough** bellows, his voice muffled but brimming with malice. 

From behind the low, polished wood of the service counter, **Edda** looks up. She is a woman with sharp, observant eyes and hair pulled back in a tight, practical knot, her face etched with the weary patience of someone who has seen too many petty brawls. She stares at you, her brow furrowed in confusion and annoyance as she watches you press your face against the wall. 

"Whatever trouble you've brought to my doorstep, keep it out there," **Edda** snaps, her voice cutting through your frantic state like a knife. She eyes your disheveled appearance and the heavy satchel, her expression hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (3) | Difficulty: normal
Roll: 2 + 6 +1 (stat) = 9 → PARTIAL
Directive: The intimidate results in a partial. You get what you asked for, but they now hold leverage over you.

GM DIRECTION (COMPLICATION, surface as npc_behavior):
Edda slams a heavy iron latch onto the door to secure it, but the impact causes the wood to shudder violently under the Scarred Tough's heavy blows, signaling that the door won't hold for long.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.





## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Bald Tough** — last seen Crossed Keys Inn Entrance
- **Scarred Tough** — last seen Crossed Keys Inn Entrance
- **** — last seen Marrow's Crossing Outskirts
- **** — last seen Marrow's Crossing Outskirts
- **Caron** — last seen Crossed Keys Inn
- **Halden**
- **Edda** — last seen Crossed Keys Inn Entrance
- **Matthew Estrada**
## NPCs Present in Scene
- Edda (Innkeeper at the Crossed Keys) — Annoyed and suspicious of the player's frantic behavior and the thugs outside.
_(immutable section omitted — see Static Context > Seed State)_
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===
 /no_think
```

### Extract Scene User Prompt
```
## rules_outcome
PARTIAL on charisma — The intimidate results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road
Stats: charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2
Conditions: bruised ribs, low morale, shaken

## location
`crossed_keys_inn_entrance` | Crossed Keys Inn Entrance
A dim, musk-scented entryway providing a momentary reprieve from the damp street.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `innkeeper` | Edda (Innkeeper at the Crossed Keys) — Annoyed and suspicious of the player's frantic behavior and the thugs outside.

_(immutable section omitted — see Static Context > Seed State)_
## scene_pressure (active threats — add/remove/update as fiction demands)
- `thugs_at_door` [immediate] The Scarred Tough and Bald Tough are pounding on the door, demanding entry. (added turn 8)


⚠ Quest "Deliver Halden's Ledger" stalled for 6 turns.

## active_quests (for gm_beat context only — quest objectives managed by progress extractor)
- `deliver_the_ledger` | Deliver Halden's Ledger
- `clear_the_road_toughs` | Clear the Road Toughs



## previous_turn_narration (T9 context)
The heavy timber door thuds shut behind you, momentarily muffling the frantic scuffling and the curses of the thugs outside. You lean your weight against the wood, your breath coming in shallow, ragged gasps as your bruised ribs protest every movement. Desperation claws at your throat; your attempt to manipulate your way into the inn's good graces or perhaps bribe your way through the very architecture fails spectacularly. 

You press your ear against the cold, damp stone of the entryway wall, your voice a frantic, low whisper. "I have credits. Open up," you hiss into the masonry, your fingers fumbling for a single coin. You press a lone credit against the rough surface of the wall, a gesture as absurd as it is futile. The stone remains indifferent, cold and unyielding, offering no mechanical or magical response to your pathetic offering. 

The silence of the entryway is broken by the heavy, rhythmic thudding of fists against the door from the outside. "Open this door, runner!" the **Scarred Tough** bellows, his voice muffled but brimming with malice. 

From behind the low, polished wood of the service counter, **Edda** looks up. She is a woman with sharp, observant eyes and hair pulled back in a tight, practical knot, her face etched with the weary patience of someone who has seen too many petty brawls. She stares at you, her brow furrowed in confusion and annoyance as she watches you press your face against the wall. 

"Whatever trouble you've brought to my doorstep, keep it out there," **Edda** snaps, her voice cutting through your frantic state like a knife. She eyes your disheveled appearance and the heavy satchel, her expression hardening. "We don't take bribes from people talking to the walls, and I won't have your blood staining my floorboards."

## CURRENT TURN NARRATION
You lunge toward the bar, your boots skidding on the sawdust-covered floor as you close the distance to **Matthew Estrada**. He sits alone in a corner booth, his posture unnaturally straight, eyes scanning the room with a disciplined, rhythmic precision that has nothing to do with a man nursing a drink. You reach out and seize his wrist in a tight, desperate grip, your fingers digging into his skin. "Who are you really?" you demand, your voice low and jagged. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch or even attempt to pull away. He simply turns his head toward you, his expression as cold and unreadable as a tombstone. His eyes aren't those of a traveler or a merchant; they are steady, calculating, and devoid of the typical tavern-goer's warmth. "You're making a scene, runner," he says, his voice a calm, low baritone that carries a weight of authority your frantic state lacks. "And your timing is as poor as your manners." 

The conversation is cut short by a violent, bone-jarring crash from the entrance. The heavy timber door groans under a massive impact, and the iron latch slams home with a deafening metallic clang as **Edda** tries to secure it. The entire entryway shudders, sending a cloud of dust falling from the ceiling beams. 

"They're coming through!" **Edda** shouts from behind the counter, her face pale as she grabs a heavy ceramic jug for defense. Outside, the muffled roar of the **Scarred Tough** and the heavy thud of the **Bald Tough**'s fists against the wood grow more frantic, the wood itself beginning to splinter under the relentless assault.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract State User Prompt
```
## active_domains
scene, inventory

## rules_outcome
PARTIAL on charisma. The intimidate results in a partial. You get what you asked for, but they now hold leverage over you.
- crit_fail / fail / setback: action did NOT succeed. Don't add items from a failed grab/purchase. MAY add a condition if new player state has occurred.
- partial: you got what you wanted but at a cost. Apply changes, but note any complications.
- success / crit_success: apply changes freely.

## roll_context
skill: charisma
band: partial
directive: The intimidate results in a partial. You get what you asked for, but they now hold leverage over you.## pc
Aren Voss — Reluctant courier on the merchant road

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## scene_result
location: `crossed_keys_inn_entrance`

## CURRENT TURN NARRATION
You lunge toward the bar, your boots skidding on the sawdust-covered floor as you close the distance to **Matthew Estrada**. He sits alone in a corner booth, his posture unnaturally straight, eyes scanning the room with a disciplined, rhythmic precision that has nothing to do with a man nursing a drink. You reach out and seize his wrist in a tight, desperate grip, your fingers digging into his skin. "Who are you really?" you demand, your voice low and jagged. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch or even attempt to pull away. He simply turns his head toward you, his expression as cold and unreadable as a tombstone. His eyes aren't those of a traveler or a merchant; they are steady, calculating, and devoid of the typical tavern-goer's warmth. "You're making a scene, runner," he says, his voice a calm, low baritone that carries a weight of authority your frantic state lacks. "And your timing is as poor as your manners." 

The conversation is cut short by a violent, bone-jarring crash from the entrance. The heavy timber door groans under a massive impact, and the iron latch slams home with a deafening metallic clang as **Edda** tries to secure it. The entire entryway shudders, sending a cloud of dust falling from the ceiling beams. 

"They're coming through!" **Edda** shouts from behind the counter, her face pale as she grabs a heavy ceramic jug for defense. Outside, the muffled roar of the **Scarred Tough** and the heavy thud of the **Bald Tough**'s fists against the wood grow more frantic, the wood itself beginning to splinter under the relentless assault.
## END CURRENT TURN NARRATION
 /no_think
```

### Extract Progress User Prompt
```
## turn
10

## active_domains
scene, inventory

## rules_outcome
PARTIAL on charisma.## pc
Aren Voss — Reluctant courier on the merchant road

## player_intent
intimidate: Aren Voss confronts Matthew Estrada to demand his true identity and purpose.
## prior_turn_narration (T8 — for outcome_summary and actions context)
The **Bald Tough**'s massive hand remains locked onto your satchel strap, his knuckles white as he tries to wrench the heavy load from your shoulder. The tension is agonizing; you can hear the frantic, rhythmic creak of the leather strap straining against your weight, the fibers groaning as they begin to fray and crack under the brute's violent tugging. 

Seizing the chaotic moment of the struggle, you reach into your pocket and fumble for the **Brass key**. You lunge toward the heavy timber doors of the inn, your boots slipping slightly in the churned mud as you try to bypass the **Scarred Tough**'s club. You thrust the small piece of metal toward the lock, your fingers trembling from the adrenaline and the sharp sting in your ribs. 

The key slides into the lock with a mechanical click that feels unnaturally loud amidst the scuffling of boots and heavy breathing. With a sharp twist, the tumblers yield. The heavy door groans on its hinges, swinging inward just enough to provide a narrow gap of sanctuary away from the thugs' grasping hands. 

You stumble through the threshold, the sudden transition from the damp, biting air of the street to the dim, musk-scented warmth of the inn's entryway providing a momentary reprieve. Behind you, the sounds of the struggle—the grunt of the **Bald Tough** and the whistling air of the club—are muffled by the thick wood of the door as it swings shut, momentarily separating you from the violence in the mud.

## CURRENT TURN NARRATION
You lunge toward the bar, your boots skidding on the sawdust-covered floor as you close the distance to **Matthew Estrada**. He sits alone in a corner booth, his posture unnaturally straight, eyes scanning the room with a disciplined, rhythmic precision that has nothing to do with a man nursing a drink. You reach out and seize his wrist in a tight, desperate grip, your fingers digging into his skin. "Who are you really?" you demand, your voice low and jagged. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch or even attempt to pull away. He simply turns his head toward you, his expression as cold and unreadable as a tombstone. His eyes aren't those of a traveler or a merchant; they are steady, calculating, and devoid of the typical tavern-goer's warmth. "You're making a scene, runner," he says, his voice a calm, low baritone that carries a weight of authority your frantic state lacks. "And your timing is as poor as your manners." 

The conversation is cut short by a violent, bone-jarring crash from the entrance. The heavy timber door groans under a massive impact, and the iron latch slams home with a deafening metallic clang as **Edda** tries to secure it. The entire entryway shudders, sending a cloud of dust falling from the ceiling beams. 

"They're coming through!" **Edda** shouts from behind the counter, her face pale as she grabs a heavy ceramic jug for defense. Outside, the muffled roar of the **Scarred Tough** and the heavy thud of the **Bald Tough**'s fists against the wood grow more frantic, the wood itself beginning to splinter under the relentless assault.
## END CURRENT TURN NARRATION
 /no_think
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "intimidate",
  "intent": "Aren Voss confronts Matthew Estrada to demand his true identity and purpose.",
  "rolled": true,
  "total_ms": 2981.8,
  "tokens_in": 1312,
  "tokens_out": 1426,
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
  "outcome_summary": "Your attempt to intimidate Matthew Estrada fails to crack his composure, and the situation escalates as the thugs begin battering down the inn door."
}
```

**Raw LLM output:**
```
{
  "intent": "Aren Voss confronts Matthew Estrada to demand his true identity and purpose.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "stakes": "[Mechanical cost: charisma check] + [Narrative consequence: Matthew reacts aggressively or alerts the innkeeper/guards to the disturbance]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal",
    "tags": []
  }
}
```

### Narration

You lunge toward the bar, your boots skidding on the sawdust-covered floor as you close the distance to **Matthew Estrada**. He sits alone in a corner booth, his posture unnaturally straight, eyes scanning the room with a disciplined, rhythmic precision that has nothing to do with a man nursing a drink. You reach out and seize his wrist in a tight, desperate grip, your fingers digging into his skin. "Who are you really?" you demand, your voice low and jagged. "And why are you watching this room like a soldier?"

**Matthew Estrada** doesn't flinch or even attempt to pull away. He simply turns his head toward you, his expression as cold and unreadable as a tombstone. His eyes aren't those of a traveler or a merchant; they are steady, calculating, and devoid of the typical tavern-goer's warmth. "You're making a scene, runner," he says, his voice a calm, low baritone that carries a weight of authority your frantic state lacks. "And your timing is as poor as your manners." 

The conversation is cut short by a violent, bone-jarring crash from the entrance. The heavy timber door groans under a massive impact, and the iron latch slams home with a deafening metallic clang as **Edda** tries to secure it. The entire entryway shudders, sending a cloud of dust falling from the ceiling beams. 

"They're coming through!" **Edda** shouts from behind the counter, her face pale as she grabs a heavy ceramic jug for defense. Outside, the muffled roar of the **Scarred Tough** and the heavy thud of the **Bald Tough**'s fists against the wood grow more frantic, the wood itself beginning to splinter under the relentless assault.

### Extract Scene

```json
{
  "scene_tags": [
    "dialogue",
    "combat"
  ],
  "scene_tagline": "The Door Is Splintering",
  "location_change": null,
  "location_description": null,
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "innkeeper",
      "notes": "Pale and defensive, grabbing a heavy ceramic jug to protect herself as the door begins to splinter.",
      "name": null,
      "title": null,
      "bio": null
    },
    {
      "id": "matthew_estrada",
      "notes": "Sitting in a corner booth, remaining unnaturally calm and disciplined despite the player's frantic physical contact.",
      "name": null,
      "title": null,
      "bio": null
    }
  ],
  "compendium_npc_update": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "thugs_at_door",
      "text": "The Scarred Tough and Bald Tough are splintering the entrance door with violent impacts.",
      "urgency": "immediate",
      "turn_added": 0,
      "max_turns": null
    }
  ],
  "gm_beat": {
    "type": "complication",
    "surface_as": "event",
    "instruction": "As the timber door begins to crack under the thugs' assault, a heavy splintering piece of wood flies inward, narrowly missing Matthew Estrada and striking the table near the player."
  }
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
      "id": "compromised",
      "label": "compromised",
      "description": "You intimidated Matthew Estrada, but his cold reaction suggests he now holds leverage over you."
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
      "id": "matthew_estrada_suspicion",
      "text": "Matthew Estrada exhibits disciplined, soldier-like behavior, suggesting he is more than a simple traveler.",
      "turn": 10
    },
    {
      "id": "thugs_attacking_inn",
      "text": "The Bald Tough and Scarred Tough are violently attempting to break into the inn.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Demand more answers from Matthew Estrada while the door splinters.",
    "Help Edda defend the entrance against the approaching thugs.",
    "Search the bar for a weapon to face the attackers.",
    "Try to slip away into the shadows of the inn."
  ],
  "outcome_summary": "Your attempt to intimidate Matthew Estrada fails to crack his composure, and the situation escalates as the thugs begin battering down the inn door."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "quest_updates": [],
  "pc_condition_add": [
    {
      "id": "compromised",
      "label": "compromised",
      "description": "You intimidated Matthew Estrada, but his cold reaction suggests he now holds leverage over you."
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "dialogue",
    "combat"
  ],
  "scene_tagline": "The Door Is Splintering",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "innkeeper",
      "notes": "Pale and defensive, grabbing a heavy ceramic jug to protect herself as the door begins to splinter."
    },
    {
      "id": "matthew_estrada",
      "notes": "Sitting in a corner booth, remaining unnaturally calm and disciplined despite the player's frantic physical contact."
    }
  ],
  "recent_events_add": [
    {
      "id": "matthew_estrada_suspicion",
      "text": "Matthew Estrada exhibits disciplined, soldier-like behavior, suggesting he is more than a simple traveler.",
      "turn": 10
    },
    {
      "id": "thugs_attacking_inn",
      "text": "The Bald Tough and Scarred Tough are violently attempting to break into the inn.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [
    {
      "id": "thugs_at_door",
      "text": "The Scarred Tough and Bald Tough are splintering the entrance door with violent impacts.",
      "urgency": "immediate",
      "turn_added": 0
    }
  ]
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Demand more answers from Matthew Estrada while the door splinters.

- Help Edda defend the entrance against the approaching thugs.

- Search the bar for a weapon to face the attackers.

- Try to slip away into the shadows of the inn.

### Context Telemetry

- rules: est=1503t trimmed=False
- narrate: est=6175t trimmed=False
- extract.scene: est=4517t trimmed=False attempts=1
- extract.state: est=2611t trimmed=False attempts=1
- extract.progress: est=2767t trimmed=False attempts=1

### State After Turn

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn",
          "location_name": "Crossed Keys Inn",
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
      "hooded_figure_1": {
        "bio": "",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrow_crossing_outskirts",
          "location_name": "Marrow's Crossing Outskirts",
          "turn": 4
        },
        "last_seen_state": "Watching from the stone alcove near the town well.",
        "name": "",
        "title": "Hooded Figure"
      },
      "hooded_figure_2": {
        "bio": "",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "marrow_crossing_outskirts",
          "location_name": "Marrow's Crossing Outskirts",
          "turn": 4
        },
        "last_seen_state": "Watching from the stone alcove near the town well.",
        "name": "",
        "title": "Hooded Figure"
      },
      "innkeeper": {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 10
        },
        "name": "Edda",
        "title": "Innkeeper at the Crossed Keys"
      },
      "matthew_estrada": {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 10
        },
        "name": "Matthew Estrada",
        "title": "Traveler"
      },
      "tough_a": {
        "bio": "A thick-necked enforcer for the road tax, known for his mocking whistle.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 7
        },
        "last_seen_state": "Struggling with the player's satchel outside the door.",
        "name": "Bald Tough",
        "title": "Road Tough"
      },
      "tough_b": {
        "bio": "A man with a jagged scar through his left eyebrow who enforces a new tax on the merchant road.",
        "last_seen": {
          "last_seen_state": "",
          "location_id": "crossed_keys_inn_entrance",
          "location_name": "Crossed Keys Inn Entrance",
          "turn": 7
        },
        "last_seen_state": "Bellowing threats and pounding on the door from the outside.",
        "name": "Scarred Tough",
        "title": "Road Tough"
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
    "description": "A dim, musk-scented entryway providing a momentary reprieve from the damp street.",
    "id": "crossed_keys_inn_entrance",
    "name": "Crossed Keys Inn Entrance"
  },
  "meta": {
    "compendium_touch_order": [
      "hooded_figure_1",
      "hooded_figure_2",
      "tough_b",
      "tough_a"
    ],
    "game_name": "eval",
    "last_compacted_turn": 3,
    "model": "",
    "pending_gm_beat": {
      "instruction": "As the timber door begins to crack under the thugs' assault, a heavy splintering piece of wood flies inward, narrowly missing Matthew Estrada and striking the table near the player.",
      "surface_as": "event",
      "type": "complication"
    },
    "prior_history": [
      "- [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.",
      "- [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight.",
      "- [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits."
    ],
    "setting_pack": "eval-pack",
    "turn": 10
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
        "added_turn": 4,
        "description": "The aggressive confrontation with the inn guards has rattled your composure.",
        "id": "shaken",
        "label": "shaken"
      },
      {
        "added_turn": 9,
        "description": "You intimidated Matthew Estrada, but his cold reaction suggests he now holds leverage over you.",
        "id": "compromised",
        "label": "compromised"
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
      "last_advanced_turn": 1,
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
      "last_advanced_turn": 4,
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
    }
  ],
  "scene": {
    "location_entered_turn": 7,
    "present_npcs": [
      {
        "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
        "id": "innkeeper",
        "name": "Edda",
        "notes": "Pale and defensive, grabbing a heavy ceramic jug to protect herself as the door begins to splinter.",
        "title": "Innkeeper at the Crossed Keys"
      },
      {
        "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
        "id": "matthew_estrada",
        "name": "Matthew Estrada",
        "notes": "Sitting in a corner booth, remaining unnaturally calm and disciplined despite the player's frantic physical contact.",
        "title": "Traveler"
      }
    ],
    "recent_events": [
      {
        "id": "debt_settled",
        "text": "You have settled your debt with Caron, though his eyes remain hungry for more than just coin.",
        "turn": 2
      },
      {
        "id": "halden_contract",
        "text": "Halden has entrusted you with a heavy satchel to be delivered to the Crossed Keys Inn.",
        "turn": 3
      },
      {
        "id": "inn_toughs_confrontation",
        "text": "Two thugs are blocking the entrance to the Crossed Keys Inn, demanding a 'tax' from travelers.",
        "turn": 5
      },
      {
        "id": "thugs_ambush_inn",
        "text": "Two thugs are attempting to rob Voss of his satchel outside the Crossed Keys Inn.",
        "turn": 7
      },
      {
        "id": "inn_entry_escape",
        "text": "Voss successfully used the brass key to slip into the inn, narrowly escaping the thugs' grasp.",
        "turn": 8
      },
      {
        "id": "thugs_at_the_door",
        "text": "The Scarred Tough and Bald Tough are pounding on the inn door, demanding entry.",
        "turn": 9
      },
      {
        "id": "matthew_estrada_suspicion",
        "text": "Matthew Estrada exhibits disciplined, soldier-like behavior, suggesting he is more than a simple traveler.",
        "turn": 10
      },
      {
        "id": "thugs_attacking_inn",
        "text": "The Bald Tough and Scarred Tough are violently attempting to break into the inn.",
        "turn": 10
      }
    ],
    "recently_left": [],
    "recently_left_turns": 0,
    "scene_pressure": [
      {
        "id": "thugs_at_door",
        "max_turns": null,
        "text": "The Scarred Tough and Bald Tough are splintering the entrance door with violent impacts.",
        "turn_added": 8,
        "urgency": "immediate"
      }
    ],
    "tagline": "The Door Is Splintering",
    "tags": [
      "dialogue",
      "combat"
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
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Credits', 'Instead', 'Voss'] |
| 8 | `universal.location_change.applied` | location_change emitted but state.location.id unchanged: crossed_keys_inn_entrance |
| 9 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Tough', 'Scarred'] |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1398 | 2943 | 3904 | 2549 | 2617 | 0 | 0 |
| 2 | 1477 | 3409 | 4218 | 2542 | 2624 | 0 | 0 |
| 3 | 1484 | 3810 | 4302 | 2632 | 2913 | 0 | 0 |
| 4 | 1486 | 4251 | 4414 | 2521 | 2777 | 0 | 0 |
| 5 | 1492 | 4974 | 4475 | 2689 | 3131 | 1 | 1 |
| 6 | 1495 | 5509 | 4450 | 2688 | 3100 | 0 | 0 |
| 7 | 1491 | 4690 | 4385 | 2509 | 2707 | 0 | 0 |
| 8 | 1492 | 5168 | 4393 | 2553 | 2746 | 0 | 0 |
| 9 | 1497 | 5509 | 4343 | 2648 | 2768 | 0 | 0 |
| 10 | 1503 | 6175 | 4517 | 2611 | 2767 | 0 | 0 |

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + progress | 7 | `- You arrived in Marrow's Crossing after three days on the r / - You heard rumors of road-toughs extorting travelers near t / - You found Caron in the tavern — he's been waiting for you.` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |

## Compaction Features
**5 compaction event(s) observed.** For each event below, the judge must evaluate every capability and write `[OK] / [FAIL] / [NA]` with a one-line justification per capability. The 14 capabilities the compactor system prompt promises:

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
- recent_events: 5 → 3 entries

**Bullets added:**

  > - [T1] Met with Caron at the Crossed Keys Inn to discuss your outstanding debt.
  > - [T2] Paid Caron 500 credits to settle your debt; he noted you are carrying more than just your weight.
  > - [T3] Contracted with Halden to deliver a heavy satchel to the Crossed Keys Inn for 200 credits.

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
- recent_events: 6 → 8 entries

**Bullets added:**

  *(none — compaction event detected but no bullets appended; flag this)*

**Applied sanitization actions:**

  *(none recorded)*

