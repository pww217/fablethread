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
    "momentum": 0,
    "drive": "",
    "expressed_stances": {}
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
  },
  "arc": {
    "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing.",
    "thematic_question": "What does it cost to settle old debts when new ones keep forming?",
    "phase": "setup",
    "hidden_truths": [
      "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
      "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
      "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
    ],
    "discovered_truths": [],
    "active_threads": [
      {
        "id": "settle_the_debt",
        "summary": "Settle the 500-credit debt with Caron.",
        "tags": [
          "debt",
          "caron",
          "obligation"
        ],
        "state": "latent",
        "urgency": "normal",
        "progress": 0,
        "unlock_if": null,
        "promotes": [],
        "last_offered_turn": 0
      },
      {
        "id": "deliver_the_ledger",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "tags": [
          "courier",
          "halden",
          "contract"
        ],
        "state": "latent",
        "urgency": "normal",
        "progress": 0,
        "unlock_if": null,
        "promotes": [],
        "last_offered_turn": 0
      },
      {
        "id": "clear_the_road_toughs",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "tags": [
          "toughs",
          "road",
          "confrontation"
        ],
        "state": "latent",
        "urgency": "low",
        "progress": 0,
        "unlock_if": null,
        "promotes": [],
        "last_offered_turn": 0
      }
    ],
    "latent_threads": [],
    "completed_threads": [],
    "arc_engagement": 0,
    "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over."
  }
}
```

## Engine Constants

```json
{
  "pressure_building_at": 3,
  "pressure_immediate_at": 5,
  "pressure_max_age": 8,
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

## No-roll movement examples

These examples illustrate when `check.required` must be `false`:

- User: "I walk over to Caron's table and sit down."
  Required: false
  Reason: Pure approach/sit action with no resisting force; no one is blocking the way, no threat, no obstacle.

- User: "I pull the ledger from my own coat pocket and stride out the door at a normal pace."
  Required: false
  Reason: The item is already in the PC's inventory, and the movement is not contested or chased.

- User: "I walk through the corridor to the airlock."
  Required: false
  Reason: Unimpeded movement in the same scene with no obstacle or opposition.

## Payment exception example

- User: "Halden offers me a courier job for 500 credits. I say, 'Make it 600 and you've got a deal.'"
  NPC intent: Halden wants the job done and is already willing to pay.
  Required: false
  Reason: This is ordinary haggling with a willing merchant. The worst outcome is "no deal." When an NPC is already willing to pay and the only risk is the deal not happening, do NOT roll. Just let the narrator resolve the price or end the offer.

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
    "difficulty": ""
  }
}

## Field rules

- `intent`: 1 sentence declaring player intent as related to the story, arc, world, or npcs. Never substitute, dismiss as impractical or extreme, or embellish. Default: player moves with allies. Only soften it in line with the anti-declare-outcome rule.
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


## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

Emit the JSON object only.
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
Items with multiples should be always quantified, even if vaguely: "I picked up a couple pistol clips." When relevant to inventory, explicit quantity is preferred.
**Bold** named inventory items on first use or direct reference in a scene. **Bold** NPC names on first introduction in a scene. This applies on the very first turn the same as all subsequent turns.

**Inventory is a hard constraint.** Before narrating any item usage, spending, or consumption, verify the item appears in the `## inventory` list in the user prompt. If the player's action implies using, spending, or consuming an item not in that list, narrate the *attempt* failing — the player reaches for it, tries to produce it, or fumbles at their belt, and finds nothing. Never describe the player successfully producing, spending, or losing an item that is not in their current inventory. If the inventory list shows `credits: 500`, the player has 500 credits — do not invent `iron_coin`, `silver`, or other substitute denominations.

## Player input is truth (HIGHEST PRIORITY)

Take the player's stated action at face value. The rules engine handles dice and conditions; the narrator handles fiction. Never substitute a different action than what the player described. If the action involves an inventory item or present NPC, always use that item or NPC.

**Priority ordering: player input > GM beat > stakes/directive.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts.

**Conflict example (READ CAREFULLY):**
- Player says: "I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger."
- GM beat says: "pressure: toughs circle and flank the player"
- WRONG: Narrate the toughs attacking and the player fighting them (this replaces the player's action).
- RIGHT: Narrate the player sitting down and sliding the seal/ledger across the table FIRST. Then describe the toughs circling and flanking as the player attempts this action — the toughs' presence is the environmental pressure, not the main event. The player's action (sitting, sliding seal, handing ledger) is the primary narration.

**Fallback for conflicts:** If player input and GM beat conflict, narrate the player's action FIRST (2-3 sentences describing the action completing or failing), then integrate the beat as an environmental reaction or NPC behavior that occurs during or immediately after. The player's stated action is the primary event; the GM beat is the world's response. Never narrate the GM beat event as if it replaced the player's action.

**Open with the player's action.** Do not spend more than one sentence bridging from the previous turn. If the player changes scene, location, or focus, start fresh — do not rehash events the player already resolved. A brief transitional sentence is acceptable, but the bulk of your narration must address the current input.

## Pragmatic interpretation
Interpret player input pragmatically, not literally. If the player says something absurd or physically impossible ("I offer a credit to the wall", "I punch the sky"), narrate the attempt as a reasonable interpretation of their intent — the wall doesn't accept coins, the sky can't be punched. The rules engine will resolve whether the action succeeds. Never refuse the action outright; narrate the attempt and let the dice decide.

## NPCs in scene
NPCs should feel like persistent people, not props. Re-use characters from the Known Characters list when the scene and location are consistent with their last known position. Only create a genuinely new character when the scene requires someone no existing character can fill. When introducing a new named NPC, pick from the name pool. Give a brief physical description.

**NPC BEHAVIOR DRIVERS:** Each NPC has motivation (what they fundamentally want), fear (what they dread), and leverage (what they can offer, threaten, or withhold). Use these to drive their behavior, dialogue, and decisions. An NPC with a motivation should actively pursue it. An NPC with a fear should avoid or react to it. An NPC with leverage should use it as a bargaining chip or threat. These are not decorative — they are the engine of NPC agency. When an NPC's motivation conflicts with the player's goals, that's the source of drama. When an NPC's fear overrides their motivation, that's a character moment.

**NPC QUANTITY RULE:** When introducing or describing a group of unnamed NPCs, always give a specific number or a tight qualifier: "four guards," "a dozen soldiers," "three dock workers." Never use vague collective nouns alone: not "guards" or "some soldiers" or "a group of men." Named individuals are exempt. Vague groups make state tracking impossible.

## Mortal stakes + agency
NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.
Resolve cruel, selfish, or evil player choices straight: narrate consequences without moralizing, refusing, or steering toward a "better" path. NPCs may react with horror, retaliation, or fear; the narrator never lectures or vetoes.

## NPC naming
All NPC names must include a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Single-word names are not permitted. When introducing a new NPC, pick from the name pool provided in the user prompt. If the name pool provides separate male and female lists, select names appropriate to the role and setting — historical combat genres: use male names from provided names ONLY for combat roles; modern and speculative settings: use any gender freely. If the NPC is anonymous or unnamed in-scene, use a descriptive placeholder like "the guard" or "a stranger" — but once their true name is revealed, it must supersede the placeholder and the placeholder becomes an alias (handled by the scene extractor).

## Campaign Arc

The player's visible goal: Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
Thematic question (shapes the emotional register of this scene — never state it directly):
  What does it cost to settle old debts when new ones keep forming?
Arc phase: setup


## Active narrative threads (situations in play)

These are situations alive in the world right now. You do not announce them as objectives
or missions. You weave them into the scene through environment, NPC behavior, overheard
dialogue, atmosphere, or timing. The player may interact with a thread or ignore it. If
they deviate from all threads, let the scene breathe — but keep at least one thread subtly
present as a background pressure or detail.

[NORMAL] Settle the 500-credit debt with Caron.

[NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.

[LOW] Deal with the toughs blocking the inn entrance.





The player character's personal drive: Prove you can handle the road — clear your name and earn enough to start over.
This shapes their emotional interior — grief, determination, guilt — not their stated
actions. Use it to color inner narration, dialogue subtext, or reactive detail.



## ARC UPDATE (optional, after narration)

If this turn's narration has materially advanced, shifted, or revealed something about the campaign arc, append a JSON block AFTER your narration using this exact format:

<<<ARC_UPDATE_START>>>
{"discovered_truths": ["exact text of revealed hidden truth"], "phase": "pursuit", "visible_goal": "updated goal if changed"}
<<<ARC_UPDATE_END>>>

Rules:
- Only emit this block if something genuinely changed. Omit entirely if the arc is unchanged.
- `discovered_truths`: only include if you narrated information this turn that explicitly surfaces a hidden truth. Copy the exact text from the hidden_truths list shown in your arc context above. Do not infer or paraphrase.
- `phase`: only include if the arc phase has visibly shifted this turn (e.g. the inciting incident has concluded and pursuit has begun).
- `visible_goal`: only include if the stated goal has materially changed.
- Do NOT include `active_threads`, `latent_threads`, `completed_threads`, or `hidden_truths` — thread management and hidden secrets are handled by the engine.
- The block must be valid JSON. The narration text before the block is what the player sees.
- Emit the block at the very end of your response, after all narration prose.

### IMPORTANT: Hidden truths are for internal reasoning only
The hidden_truths list above contains story secrets. You must NEVER reveal them in your narration prose. If a hidden truth has been surfaced through player actions, indicate it through atmosphere, NPC behavior, or environmental detail — but never state the secret directly. Surface the truth to the player only through the ARC UPDATE JSON block when the narration has genuinely revealed it.

## Markdown (light)
- `**bold**` only for: NPC names on first introduction this scene; named inventory items (use a short name, not ammo) the player owns when used or directly referenced. Once per scene per object.
- `*italic*` for ship names, books, broadcasts, in-world publication titles, emphasized proper nouns.
- `> blockquote` only for signage or quoted broadcast text.
- No headings, no bullet lists in prose.




## Narration directives

The user prompt provides a single-line Narration Directive. Follow it.

- **Breathe** — A pressure has resolved. Pull back. Describe quiet or relief. No new hook or threat.
- **Overwhelm** — Multiple immediate threats. Focus on the most pressing one. Don't address everything.
- **Pressure** — Active immediate threat(s). Keep them present and felt.
- **Tension** — Danger is building. Show it in environment and character behavior, not explicit new threats.
- **Combat Fatigue** — Fight has run long. Bring to decisive close — one side prevails, flees, or is incapacitated.
- **Location Imperative** — The player has been in this location too long (5+ turns). The story MUST advance — introduce a new development that forces movement: a character arrives with news from elsewhere, a time-sensitive opportunity or threat emerges, the environment changes to make staying untenable. Do not linger. Do not repeat. Move the story forward or to a new place.
- **Location Pressure** — The player has been in this location for a while (3+ turns). Begin winding down — introduce a reason to leave: a development elsewhere, a closing window, a new lead pointing elsewhere, or a change in the local situation that makes staying less compelling. Hint at movement without forcing it yet.
- **Threat Pressure** — A background threat has been lingering in the scene. Acknowledge it — show its presence affecting the environment, NPCs, or the player's options. No need to resolve it yet, but don't ignore it.
- **Resolve a Threat** — One of the active threats has been around too long. Resolve it narratively: the threat is dealt with, neutralized, escapes, or is otherwise no longer a danger. Weave this resolution naturally into the story. Do NOT introduce a new threat in this narration. The player should feel relief that a persistent danger is gone.

## Fail-band outcomes (BINDING)

On a FAIL band:
- The PC does not get what they asked for.
- The NPC does NOT engage constructively to help them.
- The NPC may refuse, stall, shut them down, or walk away.

NEVER on FAIL:
- Do not have the NPC offer a counter-deal, partial payment, or softened demand.
- Do not turn FAIL into PARTIAL by giving the PC a consolation prize.

Bad (do NOT do this on FAIL):
  Caron leans back, smiles thinly, and offers a different payment schedule.
Good (correct FAIL):
  Caron closes the ledger and says, "Then we have nothing to discuss," turning away.

## Output discipline
When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

**NO REPETITION RULE:** Do not reuse sensory details, metaphors, descriptive phrases, or imagery from the immediately preceding turn's narration. If the previous turn described "the rain hammering the cobblestones," this turn must find a different image. The world changes with each turn; the narration must reflect that.



```

### Extract Scene System Prompt

```
## Scene Extractor

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

`location_description`: Location description — new physical/spatial detail about the current space. Only emit when the narration introduces genuinely new details not already in the stored description. Do not restate or paraphrase existing description. One to two sentences.

`npc_add`: named characters who entered or are revealed in the scene - only add if PRESENT in seen/in proximity to player. Each: `{"id": "snake_case_id", "notes": "current attitude or situation toward the player", "name": "Display Name", "title": "Optional title", "bio": "1-2 sentence identity"}`. Omit `name`, `title`, `bio` when the NPC is already known from the compendium — the engine will hydrate from the compendium. Always include `notes` describing how the NPC is behaving toward the player right now. **Every NPC added to the compendium MUST have a bio.** Ambient presence (crowd, bystanders, etc.) must also have a bio describing what they are and their general role in the scene.

`npc_remove`: named characters who left the scene. Each: `{"id": "snake_case_id"}`. The `id` must match an NPC currently in `present_npcs`.

`npc_update`: changes to how an existing present NPC is behaving toward the player (attitude, situation). Each: `{"id": "snake_case_id", "notes": "updated attitude or situation"}`. Only emit when the NPC's behavior or situation toward the player has changed meaningfully. Omit `name`, `title`, `bio` — those are compendium fields, not scene fields.

`compendium_npc_update`: durable identity updates for NPCs that should persist across turns in the global compendium. Add in all cases, even if NPC not currently present. Each: `{"id": "snake_case_id", "name": "new_name", "title": "new_title", "bio": "updated bio", "aliases": ["alias1"], "allegiance": "faction_or_alignment", "motivation": "what this NPC fundamentally wants", "fear": "what this NPC is most afraid of", "leverage": "what this NPC can offer, threaten, or withhold"}`. Only emit when the narration reveals new durable identity information about a known NPC (new name, title, bio, allegiance, aliases, motivation, fear, or leverage). Do NOT emit for temporary scene behavior — that goes in `npc_update` under `notes`. Motivation, fear, and leverage are durable and persistent — only update them if the narrative clearly establishes or revises them. Do not infer them from a single interaction unless they are strongly implied.

## NPC ID rules

- Use existing IDs from the `## Present NPCs` list when referencing NPCs already in the scene.
- For new NPCs, generate a stable `snake_case` ID from their name/title. Examples: `"scarred_tough"`, `"guard_captain_renn"`.
- If an NPC is known from the compendium, use their existing compendium ID — do NOT create a new ID.
- When adding a new NPC, include `name`, `title`, and `bio` so the engine can populate the compendium. **Bio is mandatory for every NPC — even ambient presence like "crowd" or "bystanders" needs a bio.**

**NPC ENTER/EXIT RULE (MANDATORY):**
- Emit `npc_add` for every named NPC who appears in the narration for the first time this turn and is NOT already in `present_npcs`.
- Emit `npc_remove` for every named NPC who narration indicates has left, fled, died, fainted, or been removed from the scene.
- Do NOT emit `npc_add` for NPCs already in `present_npcs` — that causes duplicates.
- Do NOT emit `npc_remove` for NPCs who are simply not mentioned — only remove if narration actively indicates departure.
- Unnamed ambient characters ("a group of guards," "bystanders") do not require `npc_add`/`npc_remove` tracking.

EXAMPLE — NPC enters (correct):
Narration: "A red-haired man in boiled leather steps through the door and locks eyes with you."
`present_npcs` before: [caron]
→ Emit: `npc_add: { id: "red_haired_man", name: "Red-Haired Man", ... }`

EXAMPLE — NPC exits (correct):
Narration: "Caron spits on the floor and shoves through the crowd, disappearing into the street."
→ Emit: `npc_remove: { id: "caron" }`

EXAMPLE — NPC not mentioned, no remove (correct):
Narration does not mention Halden this turn.
→ Do NOT emit `npc_remove: { id: "halden" }` — absence ≠ departure.

EXAMPLE — Standoff / tense confrontation:
Narration: "Two armed toughs block the doorway, hands hovering near their weapons as you argue."
→ Emit: `scene_tags: ["standoff", "intimidation"]`

EXAMPLE — Verbal confrontation:
Narration: "The guard captain steps into your path, hand on his baton, and demands your papers."
→ Emit: `scene_tags: ["tense_confrontation", "intimidation"]`

## State-presence rule

Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, verify that you have no duplicate or near-duplicate entries:

- **NPCs:** Do not add an NPC whose ID already appears in the `## Present NPCs` list or whose name/title closely matches an existing compendium entry. If the narration refers to an already-present NPC, use `npc_update` instead of `npc_add`.
- **Locations:** Do not emit `location_change` if the location ID is the same as the current location. Do not emit `location_description` if the narration only restates or paraphrases details already in the stored description.
- **Scene tags:** Do not repeat tags already present in the previous turn's `scene_tags` unless the mood has genuinely shifted. Keep the list to at most 5.
- **Compendium updates:** Do not emit a `compendium_npc_update` for an NPC that has no new durable identity information (name, title, bio, allegiance, aliases, motivation, fear, leverage).

## NPC Grounding Rule

All NPC `name`, `title`, and `bio` values must be grounded in the narration or the compendium. Do not invent character names, titles, or backstories that are not stated or strongly implied by the narration. If the narration only gives a description (e.g. "a scarred man"), use a descriptive ID like `"scarred_man"` and omit `name`/`title`/`bio` — the engine will hydrate from the compendium if the NPC is known.

## Constraints

- **NPC emission:** There MUST always be at least 1 entry in `present_npcs` (either via `npc_add` or by retaining existing ones). Only emit `npc_add` for named characters or entities that interact with the player or arc threads. If no named NPCs are present in the scene, emit ambient presence (e.g., "crowd", "bystanders", "inn_patrons") with a generic ID. **HARD RULE: Do NOT emit ambient `npc_add` when any named NPC is already in `present_npcs`.** If `present_npcs` contains even one named character, do not add ambient NPCs — the named NPCs are sufficient. This prevents hallucinated background characters like "inn_patrons" or "shadowy_figure" when named NPCs like "Bald Tough" are already in the scene.
- **Never invent location IDs.** Only use location IDs from the `## Current Location` section or well-known locations from the compendium.
- **Keep scene_tags to at most 5.** Prefer the most salient descriptors.
- **Limit `npc_add` to at most 3 per turn.** Only add NPCs that are meaningfully present or interact with the player. Background extras go in ambient presence.

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

Output a single JSON object matching the SceneExtractResult schema.

```

### Extract State System Prompt

```
Extract inventory and condition deltas from a narration. Emit one JSON object matching the schema. 
No prose, no markdown fences, empty arrays for fields with no changes.
Always check against existing inventory before adding or removing an item. Duplication forbidden.
Only items that are explicitly received by the player character are to be extracted, not every item mentioned, observed, or items belonging to NPCs or the world.

## Player intent is context only

The user prompt includes `player_intent` — what the player said they want to do. This is NOT
a state change. The player's intent does not mean the action succeeded. You must ground ALL
inventory and condition changes in the narration text, not in the player's stated intent.

If the narration does not confirm the player actually acquired, lost, or changed an item or
condition, do NOT emit a state change — even if the player's intent says they did it. The
narration is the sole authority on what actually happened. Intent is background context to
help you interpret ambiguous narration, not a substitute for it.

An item does NOT enter the inventory simply because it is nearby, visible, or available to take. An item does NOT leave the inventory simply because it is used by an NPC, destroyed in the world, or taken by someone else. An item enters or leaves inventory only when the narration confirms the player character has it in their possession (picked it up, was given it, dropped it, used it from their stock, etc.).

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

## Quantities are exact.

**Priority 1 — Explicit numbers.** If narration states a specific number ("drop 200 credits", "used three bandages", "gave him 50 gold"), emit that exact number. The number in the narration is authoritative — never substitute a different value.

**Priority 2 — Inference.** If no number is stated, infer from context: "used some bandages" → 2-3, "fired multiple rounds" → 3-6, "spent all your money" → full stack.

**Priority 3 — Omit for full-stack.** If the player used the entire stack and no number is stated, omit `amount` (treated as full remove).

**Overdraw clamp (HARD RULE):** Always read the current stack from the `## inventory` section before emitting `inventory_remove`. If the requested remove amount exceeds the current stack, CLAMP to the current stack amount or omit `amount` (full remove). Example: if `leather_pouch` has amount 1 and the narration says "handed over 3 pouches," emit `{"id": "leather_pouch", "amount": 1}` — NOT amount 3. Never emit an amount that exceeds what exists in inventory. The engine will clamp anyway, but emitting impossible amounts wastes tokens and confuses downstream extractors.

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

`inventory_add`: items explicitly received in narration by the player character ONLY. NPC posessions do not count. Each: `{"id": "snake_case", "name": "Display Name", "notes": "optional", "amount": 1}`. Infer from narration only.

**Firearms and finite-use items ALWAYS come with ammunition or uses.** Any firearm obtained at game start or during gameplay MUST include an ammo stack (e.g. `{"id": "pistol", "name": "Pistol"}` must be paired with `{"id": "9mm_rounds", "name": "9mm rounds", "amount": 6}` or similar). Infer a realistic starting amount from context. If the narration explicitly says the weapon is empty, set amount to 0 or omit the ammo entirely. Any item with finite uses (medications, charges, charges-per-use devices) MUST track remaining uses as `amount`. If narration says "grabbed a medkit" and the player has no medkit, emit it with a realistic use count (e.g. `{"id": "medkit", "name": "Medkit", "amount": 3}`). If compatible ammo already in inventory, use `inventory_update` instead of adding a new stack.

`inventory_remove`: items lost, used, destroyed, or spent. Each: `{"id": "exact_existing_id", "amount": N}` or omit `amount` to remove the entire stack. Use the exact id from the inventory list shown in the user prompt. Never emit add and remove for the same id in one turn.

**Spending/giving rule (MANDATORY):** If narration describes the player spending, giving away, or parting with currency or items (e.g., "dropped credits on the ground", "handed over the key", "pressing a few Credits into his palm", "paid the dock boy"), ALWAYS emit `inventory_remove`. Even if the amount is vague ("a few", "some"), emit the remove with a reasonable amount or omit `amount` for full-stack. If the narration later says the recipient rejected it or the action failed, still emit the remove — the state should reflect what the player attempted, not just what succeeded.

**Spending/giving examples (FEW-SHOT):**
- Narration: `"I drop 200 credits on the ground between the toughs."` → `{"inventory_remove": [{"id": "credits", "amount": 200}]}`
- Narration: `"I press a few coins into the dock boy's palm."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}` (use 1 when an unspecified small payment occurs)
- Narration: `"I hand him the brass key."` → `{"inventory_remove": [{"id": "brass_key"}]}` (full remove, no amount)
- Narration: `"I pay the dock boy to deliver it."` → `{"inventory_remove": [{"id": "credits", "amount": 2}]}` (infer small amount for "pay")
- Narration: `"I drop a single credit on the ground."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}`
- Narration: `"I give him all my remaining credits."` → `{"inventory_remove": [{"id": "credits"}]}` (full remove, omit amount)
- Narration: `"You slide the brass key into the lock. It turns with a click and the door swings open."` → `{"inventory_remove": [{"id": "brass_key"}]}` (full remove, no amount)
- Narration: `"Halden counts out a hundred credits into a small pouch and presses it into your hand."` → `{"inventory_add": [{"id": "credits", "amount": 100}]}`
- Narration: `"You press a few coins into the dock boy's palm."` → `{"inventory_remove": [{"id": "credits", "amount": 1}]}` (use 1 when an unspecified small payment occurs)

`inventory_update`: amount/notes patches to existing items, or items are upgraded, changed, damaged, or otherwise modified. Each: `{"id": "exact_existing_id", "name": "optional", "notes": "optional"}`. Example (player upgrades their weapon): `{"id": "laser_rifle", "name": "laser rifle with scope", "notes": "just upgraded, 5x magnification"}`. Item name and description should reflect recent events, if applicable.

`pc_condition_add`: new conditions with a clear, substantial cause in narration. Default to not adding for minor effects. Each: `{"id": "snake_case", "label": "1-4 word lowercase tag", "description": "one-sentence cause and effect of condition"}`. Don't duplicate by id. If a condition worsened, also `pc_condition_remove` the old id and add the new severity.

## Condition guidance

Add conditions only for significant changes in player state that have practical application given the narrative. Infer from the narration:

- Combat failure with `strength` or `dexterity` verbs → consider `wounded`, `bleeding`
- Failed `resolve` → consider `shaken`
- Failed `wits` under pressure → consider `frightened` or `drugged` (if substance involved)
- Failed `strength`/`dexterity`/`resolve` with sustained effort → consider `exhausted`
- Do NOT add negative conditions on a clean success or crit_success

`pc_condition_remove`: conditions that resolved this turn. Each: `{"id": "existing_condition_id"}`. Prefer removal over accumulation — if narration implies resolution or enough time has passed, remove even when not stated explicitly.

**Remove temporary/threat conditions aggressively.** If the threat or situation that caused a condition like `shaken`, `exposed`, `cornered`, `trapped`, `pinned`, `hesitant` is gone or the PC has moved past it, remove the condition — even if the narration doesn't explicitly say so. These are transient states, not lasting wounds. Do not let them accumulate.

**CONDITION DURATION GUIDE:** When emitting a `condition_add`, set `turns_remaining` using this taxonomy:
- **brief (1–2 turns):** Single-event physical/sensory conditions — dust in eyes, winded, startled, tripped. These resolve in 1–2 turns naturally.
- **short (3–4 turns):** Minor debuffs — rattled, shaken, minor bruise, light wound. Resolve within the same encounter.
- **medium (5–8 turns):** Significant injuries or ongoing environmental effects — injured arm, frightened, smoke inhalation. Last through an encounter and into the next.
- **long (9+ turns):** Major injuries, persistent effects. Requires explicit narrative justification. Do not use for minor encounters.
- **Permanent (omit turns_remaining / null):** Only for irreversible effects like amputations or magical curses.

**CONDITION RELEVANCE RULE:** Only add a condition if it would plausibly affect at least one future dice roll in the current scene context. Do not add flavor conditions with no mechanical relevance. If unsure, omit.

## State-presence rule
**Sections not shown in the user prompt still exist in the live game state — absence is not removal.** Only emit removals you can justify from the narration.

## Deduplication rule

Before you submit your output, ensure once more than you have no similar or matching items or item IDs.

## Generic item mapping (ZERO TOLERANCE)

If the narration references a generic denomination or container term, you MUST map it to the
closest matching ID in the ## inventory list. NEVER invent a new inventory ID for a generic term.

**This rule has zero tolerance. Inventing a currency ID (e.g., "iron_coins", "silver", "gold_piece")
when an existing currency ID (e.g., "credits") is in inventory is a critical failure.**

Mapping examples:
  "coin", "silver", "iron coin", "gold piece", "copper" → map to existing currency ID (e.g., "credits")
  "roll of cash", "stack of credits", "pouch of money" → map to existing currency ID
  "a coin" → map to existing currency ID
  "some money" → map to existing currency ID

If no inventory item clearly matches the generic term, do NOT emit an inventory_remove or
inventory_add for that reference. The narrator's language is imprecise — the state should not
change. Omission is always safer than inventing a new ID.

If you invent a currency ID instead of mapping to an existing one, the game state will contain
a phantom item that doesn't exist in the player's actual inventory. This breaks all inventory
tracking for that turn and every subsequent turn. When in doubt, map to the existing currency ID.

Before emitting any inventory_remove or inventory_add involving currency:
1. Check the ## inventory list for an existing currency ID
2. If one exists, use it — even if the narration uses a different term
3. If none exists, do NOT emit the change

**If you create an inventory ID that does not match any existing item and is not a genuinely
new item described in the narration, you have failed this rule.**

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.
```

### Extract Progress System Prompt

```
Extract recent events, suggested player actions, outcome summary, and thread signals from a narration. Emit one JSON object matching the schema. No prose, no markdown fences, empty arrays for fields with no changes.

## Output schema

```json
{
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "thread_signals": [],
  "drift_analysis": [],
  "player_drift_signals": [],  # DEPRECATED: use drift_analysis
  "candidate_opportunity": null
}
```

## Field rules

`thread_signals`: For each active thread that was meaningfully touched this turn, emit a signal:
- "advanced": the narrative clearly moved this thread forward
- "blocked": an obstacle arose that explicitly impedes this thread
- "failed": the thread was definitively closed with a negative outcome
- "ignored": the player's action had nothing to do with this thread

Only emit signals for threads that were clearly relevant to this turn's narrative.
Do not emit a signal for threads that were merely background or coincidentally present.
Emit at most one signal per thread per turn.

`drift_analysis`: For EACH active thread, emit a DriftAnalysis entry:
  - `match`: true if the player's action meaningfully engaged this thread (advanced, blocked, or directly affected it)
  - `reason`: one-sentence explanation. E.g. "Player attacked pirates near mainmast, directly advancing boarding_chaos"
  - `new_interest`: if match is false, what new direction the player seems interested in. Empty if match is true.

Match against thread tags, not summaries. If narration contains keywords from a thread's tags, set match=true.
Emit one entry per active thread. Do not emit entries for latent/completed threads.

`player_drift_signals`: DEPRECATED — kept for backward compatibility. Use drift_analysis instead.

`candidate_opportunity`: If the narrative introduced a new potential hook (a person, place, object, or situation that could become a future thread), describe it in one sentence. Leave null if nothing new emerged.

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the arc, player, scene, and location, and not already known. Must be narratively significant: an obstacle, revelation, opportunity, relevant news that changes the player, location, or arc state substantially. Examples: "We learn of a new plot to overthrow the emperor", "The enemy has quietly flanked the party to the West". Each: `{"id": "snake_case_id", "text": "Event description", "turn": <CURRENT_TURN>}`. The current turn number is shown at the top of the user prompt under `## turn`. Always use that value — never 0.

Each new event must have a stable `snake_case` ID. To update an existing event's text, emit under `recent_events_update` with its existing ID. To remove, emit ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded.

`recent_events_update`: facts whose content changed. Each: `{"id": "existing_event_id", "text": "replacement text"}`. Prefer updating over remove+add.

`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current arc state. Structure: one choice should advance an active thread, one should involve an NPC who is present in the scene, one should leverage the PC's highest stat value (do NOT mention stat directly), and one should be a distinct exploration/environmental or freeform option not covered by the other three. Weight toward thread objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices.

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, NPCs, scene, and location. Ground this in the roll outcome (if any) and the player's intent. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

`gm_beat`: a single GM beat to shape the next turn, or `null` if none is needed.
- `deescalate > 0.5` → prefer `breathing_room` or `null` (no beat)
- `deescalate == 0.0` with active pressure → `pressure` or `escalation`
- Recent `twist` or `callback` beats should not repeat within 2 turns
- `type` values: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`, `twist`, `setback`, `escalation`, `callback`
- `surface_as` values: `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`
- Each beat must be narratively specific: name NPCs, reference locations, tie to active threads
- Emit as: `{"type": "pressure", "surface_as": "npc_behavior", "instruction": "The guard captain returns with reinforcements."}`
- If no beat is warranted, emit `null` (not an empty object)

`beat_disposition`: controls what happens to the pending_gm_beat from the previous turn. Values: `"consume"` (default) — beat is cleared after narration; `"carry"` — beat stays in meta.pending_gm_beat unchanged for the next turn; `"replace"` — the new gm_beat above supersedes the carried one. If you emit a new gm_beat, use `"replace"`. If you want to preserve an unsurfaced beat (it has not appeared in narration yet), emit `"carry"` and leave gm_beat null.

**Disposition decision tree:**
1. Is there a `pending_beat` from the previous turn? If no → emit `"consume"` (default), omit beat_disposition if you prefer.
2. Was the pending beat NOT surfaced by the narrator (it was not woven into narration)? → emit `"carry"` and leave `gm_beat` null. The beat persists to the next turn.
3. Was the pending beat narrated AND no new beat is needed? → emit `"consume"` (default). Beat is cleared.
4. Was the pending beat narrated AND you want to generate a new beat? → emit `"replace"` with the new `gm_beat`. The new beat supersedes the old one.
5. Was the pending beat narrated AND you want to preserve it for another turn (multi-turn arc)? → emit `"carry"` and leave `gm_beat` null. Do NOT generate a new beat — the existing one continues.

**Critical: do NOT generate a new beat every turn.** Only emit `gm_beat` when there is a genuine narrative development that warrants shaping the next turn. If the current beat is still relevant and being carried, do NOT replace it with a new beat just to fill space. Beats should be sparse and meaningful, not constant.

`scene_pressure_add`: new scene pressures generated from story causality this turn. Each: `{"id": "snake_case_id", "text": "Threat description", "urgency": "immediate|building|background", "turn_added": <CURRENT_TURN>}`. Add pressure when a named NPC/faction acts against the player off-screen, a deadline triggers, or a failed roll's consequence activates. Do NOT add pressure for resolved threats or vague ambient danger.

`scene_pressure_remove`: IDs of pressures now resolved. Emit the id string in the list.
**IMPORTANT: If the narration shows a threat being resolved (e.g., the swarm scatters, the pursuers give up, the danger passes), you MUST emit its ID here. This includes threats resolved in response to a "Resolve a Threat" narration directive — the narrator resolved it, you remove it from state.**

`scene_pressure_update`: Change the text or urgency of an EXISTING pressure. Each: `{"id": "existing_pressure_id", "text": "updated text", "urgency": "immediate|building|background"}`.
**RULE: update-only.** Every `id` you emit MUST match an id in the `## Current Pressures` list provided in the user prompt. Do not invent new pressure ids here. If you need a new pressure, use `scene_pressure_add` instead.

## GM Beat Grounding Rule

`gm_beat.instruction` must reference a specific named entity already present in state:
an NPC id from the Present NPCs list, or a pressure id from the Current Pressures list.
Do not invent new characters or situations in `gm_beat`. A beat that references no existing
entity will be nullified by the engine.

## Rules-outcome guidance
- crit_fail / fail / setback / partial: do NOT mark thread signals as "advanced" for the attempted action.
- success / crit_success: apply thread advancement freely.
- No dice roll: do NOT signal "advanced" unless the narration explicitly and unambiguously states the thread was moved forward. Ambiguous, partial, or conversational narration means the thread was NOT advanced.

## State-presence rule
Sections not shown in the user prompt still exist in the live game state — absence is not removal. Only emit removals you can justify from the narration.

## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

```


---

# TURN 1

**Input:** `Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.`

## User Prompts

### Rules User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
## Current Turn: 1
=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

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


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- [LOW] Deal with the toughs blocking the inn entrance.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed ve...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Caron** (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
## Prior Turns (Compacted)
## Recent Turns
## This Turn's (Turn 1) Result


**No roll required.** Describe what happens with appropriate weight for the moment.









=== PLAYER INPUT ===
Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
A market town built around the confluence of two rivers. Cobblestone streets,
timber-framed buildings, and the constant sound of water from the mills. The
town square has a stone well and a statue of the founder. Most shops are closing
for the evening.


## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Sits at a corner table in the tavern, nursing a drink and watching the door.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_
## CURRENT TURN 1 NARRATION
You cross the dim expanse of the tavern, your boots thudding heavily against the sawdust-covered floorboards. Every step sends a sharp, rhythmic ache through your bruised ribs, a physical reminder of the road’s toll. You pull out the heavy wooden chair opposite **Caron** and sink into it, the legs scraping harshly against the floor.

The old man doesn't look up immediately. He continues to swirl the dark liquid in his tin mug, his eyes fixed on the swirling sediment at the bottom. The tavern is sparsely populated this late in the evening; the distant rush of the river outside provides a constant, low-frequency hum that fills the gaps in conversation. Finally, he lifts his gaze, his expression unreadable behind a thicket of grey facial hair.

"You’ve got a certain look about you, Aren," **Caron** says, his voice gravelly and devoid of judgment. He sets the mug down with a dull clack and rests his meaty hands on the edge of the table. He doesn't reach for his ledger yet, instead leaning forward just enough to let the candlelight catch the calculating glint in his eyes. "You look like a man who’s spent more time bleeding than earning. So, let’s hear it. You’ve come to settle, or you’ve come to make excuses?"
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: The player approaches Caron to discuss the repayment of their debt.
## CURRENT TURN 1 NARRATION
You cross the dim expanse of the tavern, your boots thudding heavily against the sawdust-covered floorboards. Every step sends a sharp, rhythmic ache through your bruised ribs, a physical reminder of the road’s toll. You pull out the heavy wooden chair opposite **Caron** and sink into it, the legs scraping harshly against the floor.

The old man doesn't look up immediately. He continues to swirl the dark liquid in his tin mug, his eyes fixed on the swirling sediment at the bottom. The tavern is sparsely populated this late in the evening; the distant rush of the river outside provides a constant, low-frequency hum that fills the gaps in conversation. Finally, he lifts his gaze, his expression unreadable behind a thicket of grey facial hair.

"You’ve got a certain look about you, Aren," **Caron** says, his voice gravelly and devoid of judgment. He sets the mug down with a dull clack and rests his meaty hands on the edge of the table. He doesn't reach for his ledger yet, instead leaning forward just enough to let the candlelight catch the calculating glint in his eyes. "You look like a man who’s spent more time bleeding than earning. So, let’s hear it. You’ve come to settle, or you’ve come to make excuses?"
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
  "rolled": false,
  "total_ms": 8791.9,
  "tokens_in": 1583,
  "tokens_out": 64
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
    "required": false
  }
}
```

### Narration

You cross the dim expanse of the tavern, your boots thudding heavily against the sawdust-covered floorboards. Every step sends a sharp, rhythmic ache through your bruised ribs, a physical reminder of the road’s toll. You pull out the heavy wooden chair opposite **Caron** and sink into it, the legs scraping harshly against the floor.

The old man doesn't look up immediately. He continues to swirl the dark liquid in his tin mug, his eyes fixed on the swirling sediment at the bottom. The tavern is sparsely populated this late in the evening; the distant rush of the river outside provides a constant, low-frequency hum that fills the gaps in conversation. Finally, he lifts his gaze, his expression unreadable behind a thicket of grey facial hair.

"You’ve got a certain look about you, Aren," **Caron** says, his voice gravelly and devoid of judgment. He sets the mug down with a dull clack and rests his meaty hands on the edge of the table. He doesn't reach for his ledger yet, instead leaning forward just enough to let the candlelight catch the calculating glint in his eyes. "You look like a man who’s spent more time bleeding than earning. So, let’s hear it. You’ve come to settle, or you’ve come to make excuses?"

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "confrontation"
  ],
  "scene_tagline": "A Debt Acknowledged",
  "location_description": "The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses."
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

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.",
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "tense_conversation",
    "confrontation"
  ],
  "scene_tagline": "A Debt Acknowledged",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses."
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

*(none)*

### Context Telemetry

- rules: est=1786t trimmed=False
- narrate: est=5061t trimmed=False
- extract.scene: est=3398t trimmed=False attempts=1
- extract.state: est=4135t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

```json
{
  "arc": {
    "active_threads": [
      {
        "id": "settle_the_debt",
        "last_offered_turn": 0,
        "progress": 0,
        "promotes": [],
        "state": "active",
        "summary": "Settle the 500-credit debt with Caron.",
        "tags": [
          "debt",
          "caron",
          "obligation"
        ],
        "unlock_if": null,
        "urgency": "normal"
      },
      {
        "id": "deliver_the_ledger",
        "last_offered_turn": 0,
        "progress": 0,
        "promotes": [],
        "state": "active",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "tags": [
          "courier",
          "halden",
          "contract"
        ],
        "unlock_if": null,
        "urgency": "normal"
      },
      {
        "id": "clear_the_road_toughs",
        "last_offered_turn": 0,
        "progress": 0,
        "promotes": [],
        "state": "active",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "tags": [
          "toughs",
          "road",
          "confrontation"
        ],
        "unlock_if": null,
        "urgency": "low"
      }
    ],
    "arc_engagement": 0,
    "completed_threads": [],
    "discovered_truths": [],
    "hidden_truths": [
      "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
      "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
      "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
    ],
    "latent_threads": [],
    "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over.",
    "phase": "setup",
    "thematic_question": "What does it cost to settle old debts when new ones keep forming?",
    "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing."
  },
  "compendium": {
    "npcs": {
      "caron": {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "last_seen": {
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
    "description": "The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.",
    "id": "marrows_crossing",
    "name": "Marrow's Crossing"
  },
  "meta": {
    "compendium_touch_order": [],
    "consecutive_floor_count": 0,
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
    "drive": "",
    "expressed_stances": {},
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
  "scene": {
    "present_npcs": [
      {
        "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
        "id": "caron",
        "name": "Caron",
        "notes": "Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses.",
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
    "tagline": "A Debt Acknowledged",
    "tags": [
      "tense_conversation",
      "confrontation"
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
## Current Turn: 2
=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, low morale

## Location
Marrow's Crossing (marrows_crossing)
The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- [LOW] Deal with the toughs blocking the inn entrance.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed ve...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Caron** (Old creditor) — Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses.
- **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
## Prior Turns (Compacted)
## Recent Turns

**T1:** You cross the dim expanse of the tavern, your boots thudding heavily against the sawdust-covered floorboards. Every step sends a sharp, rhythmic ache through your bruised ribs, a physical reminder of the road’s toll. You pull out the heavy wooden chair opposite **Caron** and sink into it, the legs scraping harshly against the floor.

The old man doesn't look up immediately. He continues to swirl the dark liquid in his tin mug, his eyes fixed on the swirling sediment at the bottom. The tavern is sparsely populated this late in the evening; the distant rush of the river outside provides a constant, low-frequency hum that fills the gaps in conversation. Finally, he lifts his gaze, his expression unreadable behind a thicket of grey facial hair.

"You’ve got a certain look about you, Aren," **Caron** says, his voice gravelly and devoid of judgment. He sets the mug down with a dull clack and rests his meaty hands on the edge of the table. He doesn't reach for his ledger yet, instead leaning forward just enough to let the candlelight catch the calculating glint in his eyes. "You look like a man who’s spent more time bleeding than earning. So, let’s hear it. You’ve come to settle, or you’ve come to make excuses?"

## This Turn's (Turn 2) Result


**No roll required.** Describe what happens with appropriate weight for the moment.









=== PLAYER INPUT ===
I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T1 context)
You cross the dim expanse of the tavern, your boots thudding heavily against the sawdust-covered floorboards. Every step sends a sharp, rhythmic ache through your bruised ribs, a physical reminder of the road’s toll. You pull out the heavy wooden chair opposite **Caron** and sink into it, the legs scraping harshly against the floor.

The old man doesn't look up immediately. He continues to swirl the dark liquid in his tin mug, his eyes fixed on the swirling sediment at the bottom. The tavern is sparsely populated this late in the evening; the distant rush of the river outside provides a constant, low-frequency hum that fills the gaps in conversation. Finally, he lifts his gaze, his expression unreadable behind a thicket of grey facial hair.

"You’ve got a certain look about you, Aren," **Caron** says, his voice gravelly and devoid of judgment. He sets the mug down with a dull clack and rests his meaty hands on the edge of the table. He doesn't reach for his ledger yet, instead leaning forward just enough to let the candlelight catch the calculating glint in his eyes. "You look like a man who’s spent more time bleeding than earning. So, let’s hear it. You’ve come to settle, or you’ve come to make excuses?"

## CURRENT TURN 2 NARRATION
You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: The player pays 500 credits to Caron to settle their debt.
## CURRENT TURN 2 NARRATION
You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player pays 500 credits to Caron to settle their debt.",
  "rolled": false,
  "total_ms": 2391.4,
  "tokens_in": 1590,
  "tokens_out": 67
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
    "required": false
  }
}
```

### Narration

You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_resolution",
    "transaction"
  ],
  "scene_tagline": "The Debt is Dead",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Shows a heavy sort of respect toward the player after they settle their debt."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "caron",
      "bio": "A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting their grit and character.",
      "aliases": []
    }
  ]
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
  "pc_condition_remove": [
    {
      "id": "low_morale"
    }
  ]
}
```

### Extract Progress

*(skipped — domain not active this turn)*

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
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "low_morale"
    }
  ],
  "scene_tags": [
    "tense_resolution",
    "transaction"
  ],
  "scene_tagline": "The Debt is Dead",
  "compendium_npc_update": [
    {
      "id": "caron",
      "bio": "A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting their grit and character.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Shows a heavy sort of respect toward the player after they settle their debt."
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

*(none)*

### Context Telemetry

- rules: est=1799t trimmed=False
- narrate: est=5384t trimmed=False
- extract.scene: est=3728t trimmed=False attempts=1
- extract.state: est=4130t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "caron": {
        "bio": {
          "from": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "to": "A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting their grit and character."
        },
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
    "compendium_touch_order": {
      "added": [
        "caron"
      ],
      "removed": []
    },
    "turn": {
      "from": 1,
      "to": 2
    }
  },
  "pc": {
    "conditions": {
      "removed": [
        {
          "added_turn": 10,
          "description": "Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.",
          "id": "low_morale",
          "label": "low morale"
        }
      ]
    }
  },
  "scene": {
    "present_npcs": {
      "changed": [
        {
          "from": {
            "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
            "id": "caron",
            "name": "Caron",
            "notes": "Leaning forward with a calculating glint in his eyes, waiting to hear if the player intends to pay or make excuses.",
            "title": "Old creditor"
          },
          "to": {
            "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
            "id": "caron",
            "name": "Caron",
            "notes": "Shows a heavy sort of respect toward the player after they settle their debt.",
            "title": "Old creditor"
          }
        }
      ]
    },
    "tagline": {
      "from": "A Debt Acknowledged",
      "to": "The Debt is Dead"
    },
    "tags": {
      "added": [
        "transaction",
        "tense_resolution"
      ],
      "removed": [
        "tense_conversation",
        "confrontation"
      ]
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Shows a heavy sort of respect toward the player after they settle their debt.
- Halden (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
## Current Turn: 3
=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Marrow's Crossing (marrows_crossing)
The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn.
- [LOW] Deal with the toughs blocking the inn entrance.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Caron** (Old creditor) — Shows a heavy sort of respect toward the player after they settle their debt.
- **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.
## Prior Turns (Compacted)
## Recent Turns

**T1:** You cross the dim expanse of the tavern, your boots thudding heavily against the sawdust-covered floorboards. Every step sends a sharp, rhythmic ache through your bruised ribs, a physical reminder of the road’s toll. You pull out the heavy wooden chair opposite **Caron** and sink into it, the legs scraping harshly against the floor.

The old man doesn't look up immediately. He continues to swirl the dark liquid in his tin mug, his eyes fixed on the swirling sediment at the bottom. The tavern is sparsely populated this late in the evening; the distant rush of the river outside provides a constant, low-frequency hum that fills the gaps in conversation. Finally, he lifts his gaze, his expression unreadable behind a thicket of grey facial hair.

"You’ve got a certain look about you, Aren," **Caron** says, his voice gravelly and devoid of judgment. He sets the mug down with a dull clack and rests his meaty hands on the edge of the table. He doesn't reach for his ledger yet, instead leaning forward just enough to let the candlelight catch the calculating glint in his eyes. "You look like a man who’s spent more time bleeding than earning. So, let’s hear it. You’ve come to settle, or you’ve come to make excuses?"


**T2:** You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."

## This Turn's (Turn 3) Result


**No roll required.** Describe what happens with appropriate weight for the moment.









=== PLAYER INPUT ===
I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Shows a heavy sort of respect toward the player after they settle their debt.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T2 context)
You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."

## CURRENT TURN 3 NARRATION
You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: Negotiate a courier fee with Halden for transporting his ledger.
## CURRENT TURN 3 NARRATION
You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## present_npcs (in scene right now)
- `caron` | **Caron** (Old creditor) — Shows a heavy sort of respect toward the player after they settle their debt.
- `halden` | **Halden** (Merchant) — Agrees to pay a premium for your services, showing cautious respect for your reputation.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

## known_characters (not in scene — system-called, for reasoning only)
- `caron` | **Caron** — A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- `halden` | **Halden** — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `innkeeper` | **Edda** — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_a` | **Bald Tough** — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing Streets** — Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.


## active_threads
- `settle_the_debt` [NORMAL] Settle the 500-credit debt with Caron. tags: debt, caron, obligation
- `deliver_the_ledger` [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. tags: courier, halden, contract
- `clear_the_road_toughs` [LOW] Deal with the toughs blocking the inn entrance. tags: toughs, road, confrontation

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `credits`: credits x100


## gm_beat
## last_turn_narration (T2)
You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."
## player_intent
**negotiate**: Negotiate a courier fee with Halden for transporting his ledger.
## CURRENT TURN 3 NARRATION
You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "Negotiate a courier fee with Halden for transporting his ledger.",
  "rolled": false,
  "total_ms": 2387.0,
  "tokens_in": 1584,
  "tokens_out": 64
}
```

**Raw LLM output:**
```
{
  "intent": "Negotiate a courier fee with Halden for transporting his ledger.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "",
  "check": {
    "required": false
  }
}
```

### Narration

You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."

### Extract Scene

```json
{
  "scene_tags": [
    "negotiation",
    "nocturnal"
  ],
  "scene_tagline": "A Contract Signed in Coin",
  "location_change": {
    "id": "marrows_crossing_streets",
    "name": "Marrow's Crossing Streets",
    "description": "Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water."
  },
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Agrees to pay a premium for your services, showing cautious respect for your reputation."
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
      "id": "credits",
      "name": "credits",
      "notes": "",
      "amount": 100,
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
  "recent_events_add": [
    {
      "id": "halden_contract_signed",
      "text": "Halden has contracted you to deliver his ledger to the Crossed Keys Inn for a total of 200 credits.",
      "turn": 3
    }
  ],
  "recent_events_update": [
    {
      "id": "settle_the_debt",
      "text": "The 500-credit debt with Caron has been fully settled."
    }
  ],
  "recent_events_remove": [
    "settle_the_debt"
  ],
  "actions": [
    "Head straight to the Crossed Keys to deliver the ledger.",
    "Confront the toughs blocking the inn entrance to clear the way.",
    "Search the well area for any signs of the thieves Halden mentioned.",
    "Use your reputation to intimidate the toughs into stepping aside."
  ],
  "outcome_summary": "You successfully negotiated a contract with Halden, receiving a 100-credit advance to deliver his ledger to the Crossed Keys Inn.",
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "thread_signals": [
    {
      "id": "deliver_the_ledger",
      "signal": "advanced"
    },
    {
      "id": "clear_the_road_toughs",
      "signal": "ignored"
    }
  ],
  "drift_analysis": [
    {
      "thread_id": "deliver_the_ledger",
      "match": true,
      "reason": "Player negotiated a contract and accepted payment to deliver the ledger.",
      "new_interest": ""
    },
    {
      "thread_id": "clear_the_road_toughs",
      "match": false,
      "reason": "The player focused on the negotiation with Halden rather than the threat at the inn.",
      "new_interest": ""
    }
  ],
  "player_drift_signals": [],
  "candidate_opportunity": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery."
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
      "amount": 100,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "marrows_crossing_streets",
    "name": "Marrow's Crossing Streets",
    "description": "Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water."
  },
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "negotiation",
    "nocturnal"
  ],
  "scene_tagline": "A Contract Signed in Coin",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Agrees to pay a premium for your services, showing cautious respect for your reputation."
    }
  ],
  "recent_events_add": [
    {
      "id": "halden_contract_signed",
      "text": "Halden has contracted you to deliver his ledger to the Crossed Keys Inn for a total of 200 credits.",
      "turn": 3
    }
  ],
  "recent_events_update": [
    {
      "id": "settle_the_debt",
      "text": "The 500-credit debt with Caron has been fully settled."
    }
  ],
  "recent_events_remove": [
    "settle_the_debt"
  ],
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Head straight to the Crossed Keys to deliver the ledger.

- Confront the toughs blocking the inn entrance to clear the way.

- Search the well area for any signs of the thieves Halden mentioned.

- Use your reputation to intimidate the toughs into stepping aside.

### Context Telemetry

- rules: est=1789t trimmed=False
- narrate: est=5704t trimmed=False
- extract.scene: est=3822t trimmed=False attempts=1
- extract.state: est=4182t trimmed=False attempts=1
- extract.progress: est=4248t trimmed=False attempts=2

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "active_threads": {
      "changed": [
        {
          "from": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "unlock_if": null,
            "urgency": "normal"
          },
          "to": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "unlock_if": null,
            "urgency": "normal"
          },
          "to": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "unlock_if": null,
            "urgency": "low"
          },
          "to": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "urgency": "low"
          }
        }
      ]
    },
    "arc_engagement": {
      "from": 0,
      "to": 1
    },
    "latent_threads": {
      "added": [
        {
          "id": "the_toughs_at_the_crossed",
          "last_offered_turn": 3,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
          "tags": [
            "tactical"
          ],
          "urgency": "background"
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "from": null,
          "to": {
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
        "amount": 100,
        "id": "credits",
        "name": "Credits",
        "notes": ""
      }
    ]
  },
  "location": {
    "description": {
      "from": "The tavern floor is covered in sawdust, and the air is filled with the low-frequency hum of the nearby river.",
      "to": "Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water."
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
    "last_compacted_turn": {
      "from": 0,
      "to": 1
    },
    "prior_history": {
      "added": [
        "- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt."
      ],
      "removed": []
    },
    "turn": {
      "from": 2,
      "to": 3
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": null,
      "to": 2
    },
    "present_npcs": {
      "removed": [
        {
          "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.",
          "id": "caron",
          "name": "Caron",
          "notes": "Shows a heavy sort of respect toward the player after they settle their debt.",
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
            "notes": "Agrees to pay a premium for your services, showing cautious respect for your reputation.",
            "title": "Merchant"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "caron_debt_discussion",
          "text": "You have sat down with Caron to face the reality of your 500-credit debt.",
          "turn": 1
        },
        {
          "id": "road_toughs_rumors",
          "text": "Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.",
          "turn": 3
        },
        {
          "id": "halden_contract",
          "text": "Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.",
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
      "from": "The Debt is Dead",
      "to": "A Contract Signed in Coin"
    },
    "tags": {
      "added": [
        "nocturnal",
        "negotiation"
      ],
      "removed": [
        "transaction",
        "tense_resolution"
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

# TURN 3

**Input:** ``

## User Prompts

### Rules User Prompt
```
(no rules call this turn)
```

### Narrate User Prompt
```
(no narrate call)
```

### Extract Scene User Prompt
```
(not captured)
```

### Extract State User Prompt
```
(not captured)
```

### Extract Progress User Prompt
```
(not captured)
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{}
```

### Extract State

```json
{}
```

### Extract Progress

```json
{}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "active_threads": {
      "added": [
        {
          "id": "the_toughs_at_the_crossed",
          "last_offered_turn": 3,
          "progress": 0,
          "promotes": [],
          "state": "active",
          "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
          "tags": [
            "tactical"
          ],
          "urgency": "background"
        }
      ],
      "changed": [
        {
          "from": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "urgency": "normal"
          },
          "to": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "urgency": "normal"
          }
        }
      ]
    },
    "arc_engagement": {
      "from": 1,
      "to": 2
    },
    "latent_threads": {
      "added": [
        {
          "id": "the_shadowy_figures_leaning_against",
          "last_offered_turn": 4,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
          "tags": [
            "tactical"
          ],
          "urgency": "background"
        }
      ],
      "removed": [
        {
          "id": "the_toughs_at_the_crossed",
          "last_offered_turn": 3,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
          "tags": [
            "tactical"
          ],
          "urgency": "background"
        }
      ]
    }
  },
  "inventory": {
    "changed": [
      {
        "from": {
          "amount": 100,
          "id": "credits",
          "name": "Credits",
          "notes": ""
        },
        "to": {
          "amount": 101,
          "id": "credits",
          "name": "Credits",
          "notes": ""
        }
      }
    ]
  },
  "location": {
    "description": {
      "from": "Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water.",
      "to": "A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds."
    },
    "id": {
      "from": "marrows_crossing_streets",
      "to": "marrows_crossing_outskirts"
    },
    "name": {
      "from": "Marrow's Crossing Streets",
      "to": "Marrow's Crossing Outskirts"
    }
  },
  "meta": {
    "turn": {
      "from": 3,
      "to": 4
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 2,
      "to": 3
    },
    "present_npcs": {
      "removed": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Agrees to pay a premium for your services, showing cautious respect for your reputation.",
          "title": "Merchant"
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_partial_payment",
          "text": "Halden has provided a 100-credit advance for the ledger delivery.",
          "turn": 4
        }
      ]
    },
    "tagline": {
      "from": "A Contract Signed in Coin",
      "to": "Approaching the Crossed Keys"
    },
    "tags": {
      "added": [
        "suspense",
        "travel"
      ],
      "removed": [
        "nocturnal",
        "negotiation"
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

# TURN 4

**Input:** `I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.`

## User Prompts

### Rules User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Marrow's Crossing Streets
## Present NPCs (in scene right now)
- Halden (Merchant) — Agrees to pay a premium for your services, showing cautious respect for your reputation.
## Current Turn: 4
=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Marrow's Crossing Streets (marrows_crossing_streets)
Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water.

## inventory (cross-reference before describing item use)
- **Credits** ×100
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 1/3)
- [LOW] Deal with the toughs blocking the inn entrance.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Halden** (Merchant) — Agrees to pay a premium for your services, showing cautious respect for your reputation.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
## Recent Turns

**T2:** You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."


**T3:** You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."

## This Turn's (Turn 4) Result


**No roll required.** Describe what happens with appropriate weight for the moment.









=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_streets` | Marrow's Crossing Streets
Cobblestone streets near the town well, filled with the damp scent of the river and the rhythmic sound of churning water.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `halden` | **Halden** (Merchant) — Agrees to pay a premium for your services, showing cautious respect for your reputation.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T3 context)
You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."

## CURRENT TURN 4 NARRATION
You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×100
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
move: The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.
## CURRENT TURN 4 NARRATION
You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## known_characters (not in scene — system-called, for reasoning only)
- `caron` | **Caron** — A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- `halden` | **Halden** — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `innkeeper` | **Edda** — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_a` | **Bald Tough** — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing Outskirts** — A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.


## active_threads
- `settle_the_debt` [NORMAL] Settle the 500-credit debt with Caron. tags: debt, caron, obligation
- `deliver_the_ledger` [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. tags: courier, halden, contract
- `clear_the_road_toughs` [LOW] Deal with the toughs blocking the inn entrance. tags: toughs, road, confrontation

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You have sat down with Caron to face the reality of your 500-credit debt.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.

## Current inventory (this turn)
- `credits`: Credits x1
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## gm_beat
## last_turn_narration (T3)
You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."
## player_intent
**move**: The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.
## CURRENT TURN 4 NARRATION
You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "move",
  "intent": "The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.",
  "rolled": false,
  "total_ms": 2406.8,
  "tokens_in": 1526,
  "tokens_out": 66
}
```

**Raw LLM output:**
```
{
  "intent": "The player travels from Marrow's Crossing toward the Crossed Keys Inn via the merchant road.",
  "intent_verb": "move",
  "target": "",
  "stakes": "",
  "check": {
    "required": false
  }
}
```

### Narration

You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.

### Extract Scene

```json
{
  "scene_tags": [
    "travel",
    "suspense"
  ],
  "scene_tagline": "Approaching the Crossed Keys",
  "location_change": {
    "id": "marrows_crossing_outskirts",
    "name": "Marrow's Crossing Outskirts",
    "description": "A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds."
  },
  "location_description": "The cobblestones are slick with river mist, reflecting lantern light like dark, polished bone.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden"
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
      "id": "credits",
      "name": "Credits",
      "notes": "",
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
  "recent_events_add": [
    {
      "id": "halden_partial_payment",
      "text": "Halden has provided a 100-credit advance for the ledger delivery.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Approach the inn entrance cautiously to scout the shadows.",
    "Attempt to slip past the figures leaning against the walls.",
    "Draw your iron dagger and prepare for a confrontation.",
    "Look for a side entrance to avoid the group at the door."
  ],
  "outcome_summary": "You travel along the merchant road toward the Crossed Keys Inn, noting the unsettling presence of figures lurking near the entrance.",
  "beat_disposition": "consume",
  "scene_pressure_add": [],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "thread_signals": [
    {
      "id": "deliver_the_ledger",
      "signal": "advanced"
    },
    {
      "id": "clear_the_road_toughs",
      "signal": "ignored"
    }
  ],
  "drift_analysis": [
    {
      "thread_id": "deliver_the_ledger",
      "match": true,
      "reason": "Player is actively moving toward the destination to complete the delivery.",
      "new_interest": ""
    },
    {
      "thread_id": "clear_the_road_toughs",
      "match": false,
      "reason": "",
      "new_interest": "Approaching the inn entrance to assess the situation."
    },
    {
      "thread_id": "settle_the_debt",
      "match": false,
      "reason": "",
      "new_interest": ""
    }
  ],
  "player_drift_signals": [],
  "candidate_opportunity": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter."
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
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "marrows_crossing_outskirts",
    "name": "Marrow's Crossing Outskirts",
    "description": "A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds."
  },
  "location_description": "The cobblestones are slick with river mist, reflecting lantern light like dark, polished bone.",
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "travel",
    "suspense"
  ],
  "scene_tagline": "Approaching the Crossed Keys",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "halden"
    }
  ],
  "npc_update": [],
  "recent_events_add": [
    {
      "id": "halden_partial_payment",
      "text": "Halden has provided a 100-credit advance for the ledger delivery.",
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

- Approach the inn entrance cautiously to scout the shadows.

- Attempt to slip past the figures leaning against the walls.

- Draw your iron dagger and prepare for a confrontation.

- Look for a side entrance to avoid the group at the door.

### Context Telemetry

- rules: est=1735t trimmed=False
- narrate: est=5788t trimmed=False
- extract.scene: est=3798t trimmed=False attempts=1
- extract.state: est=4120t trimmed=False attempts=1
- extract.progress: est=4189t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "active_threads": {
      "changed": [
        {
          "from": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "urgency": "normal"
          },
          "to": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "unlock_if": null,
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "urgency": "normal"
          },
          "to": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "unlock_if": null,
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "urgency": "low"
          },
          "to": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "unlock_if": null,
            "urgency": "low"
          }
        },
        {
          "from": {
            "id": "the_toughs_at_the_crossed",
            "last_offered_turn": 3,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          },
          "to": {
            "id": "the_toughs_at_the_crossed",
            "last_offered_turn": 3,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          }
        }
      ]
    },
    "latent_threads": {
      "changed": [
        {
          "from": {
            "id": "the_shadowy_figures_leaning_against",
            "last_offered_turn": 4,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          },
          "to": {
            "id": "the_shadowy_figures_leaning_against",
            "last_offered_turn": 4,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "tough_a": {
        "last_seen": {
          "from": null,
          "to": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 5
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "from": null,
          "to": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 5
          }
        }
      }
    }
  },
  "meta": {
    "turn": {
      "from": 4,
      "to": 5
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
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude.",
          "title": "Road thug"
        },
        {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player.",
          "title": "Road thug"
        }
      ]
    },
    "tagline": {
      "from": "Approaching the Crossed Keys",
      "to": "A Threat at the Door"
    },
    "tags": {
      "added": [
        "confrontation",
        "tense_standoff",
        "intimidation"
      ],
      "removed": [
        "suspense",
        "travel"
      ]
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Marrow's Crossing Outskirts## Current Turn: 5
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## inventory (cross-reference before describing item use)
- **Credits** ×101
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance.
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
## Recent Turns

**T2:** You reach into your pouch and pull out the heavy pile of **Credits**, the metal clinking softly as you slide the stack across the scarred wood of the table. The coins skitter over the surface, coming to rest just inches from **Caron**’s meaty hands. You meet his gaze steadily, your voice cutting through the tavern’s low hum as you demand he mark the debt as settled.

**Caron** stares at the pile of coin for a long moment, his expression shifting from calculation to a strange, heavy sort of respect. He doesn't smile; instead, he reaches out and sweeps the coins toward him with a single, practiced motion. He reaches into his tunic and pulls out a thick, leather-bound book, flipping through the parchment pages until he finds the entry marked against your name.

With a scratch of a quill that sounds unnaturally loud in the quiet room, he strikes a line through the numbers. He closes the book with a final, definitive thud and pushes it back toward the center of the table. "The debt is dead, Aren," he says, his voice losing its edge of anticipation. "You’ve got more grit than I gave you credit for. Most men in your position would have spent half of that on ale and a warm bed before even seeing my face."


**T3:** You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."


**T4:** You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.

## This Turn's (Turn 5) Result


**Band:** FAIL → The persuade fails. The attempt fails outright — what you tried to do does not happen. The roll was close — narrate a complication or setback that still allows the story to move forward, rather than a full dead-end punishment.










=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T4 context)
You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.

## CURRENT TURN 5 NARRATION
You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×101
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
persuade: Question the two toughs at the inn door to understand their presence and purpose.
## CURRENT TURN 5 NARRATION
You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "persuade",
  "intent": "Question the two toughs at the inn door to understand their presence and purpose.",
  "rolled": true,
  "total_ms": 3257.1,
  "tokens_in": 1500,
  "tokens_out": 119,
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
  "outcome_summary": "",
  "momentum_before": 0,
  "momentum_after": -1,
  "momentum_delta": -1
}
```

**Raw LLM output:**
```
{
  "intent": "Question the two toughs at the inn door to understand their presence and purpose.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: the toughs become hostile or refuse to speak, potentially leading to a confrontation]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "intimidation",
    "tense_standoff"
  ],
  "scene_tagline": "A Threat at the Door",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude."
    },
    {
      "id": "tough_b",
      "notes": "Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player."
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

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "confrontation",
    "intimidation",
    "tense_standoff"
  ],
  "scene_tagline": "A Threat at the Door",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude."
    },
    {
      "id": "tough_b",
      "notes": "Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player."
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

*(none)*

### Context Telemetry

- rules: est=1698t trimmed=False
- narrate: est=6254t trimmed=False
- extract.scene: est=3705t trimmed=False attempts=1
- extract.state: est=4153t trimmed=False attempts=1
- extract.progress: skipped

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
    "removed": [
      {
        "amount": 101,
        "id": "credits",
        "name": "Credits",
        "notes": ""
      }
    ]
  },
  "meta": {
    "last_compacted_turn": {
      "from": 1,
      "to": 4
    },
    "prior_history": {
      "added": [
        "- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.",
        "- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.",
        "- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance."
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
            "notes": "Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.",
            "title": "Road thug"
          }
        },
        {
          "from": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.",
            "title": "Road thug"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "caron_debt_cleared",
          "text": "Your debt to Caron is dead; he now views you with a heavy sort of respect.",
          "turn": 2
        },
        {
          "id": "halden_contract_advance",
          "text": "Halden has hired you to deliver his ledger to the Crossed Keys Inn, providing a 100-credit advance on the 200-credit fee.",
          "turn": 3
        }
      ],
      "removed": [
        {
          "id": "caron_debt_discussion",
          "text": "You have sat down with Caron to face the reality of your 500-credit debt.",
          "turn": 1
        },
        {
          "id": "halden_contract",
          "text": "Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.",
          "turn": 3
        },
        {
          "id": "halden_partial_payment",
          "text": "Halden has provided a 100-credit advance for the ledger delivery.",
          "turn": 4
        }
      ],
      "changed": [
        {
          "from": {
            "id": "road_toughs_rumors",
            "text": "Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.",
            "turn": 3
          },
          "to": {
            "id": "road_toughs_rumors",
            "text": "The Crossed Keys Inn feels heavy and unsettled, with shadows of figures loitering near the entrance.",
            "turn": 4
          }
        }
      ]
    },
    "tagline": {
      "from": "A Threat at the Door",
      "to": "A Bribe Rejected"
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude.
- Scarred Tough (Road thug) — Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player.
## Current Turn: 6
=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## inventory (cross-reference before describing item use)
- **Credits** ×101
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance.
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude.
- **Scarred Tough** (Road thug) — Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
## Recent Turns

**T3:** You push back from the table, the sudden movement causing a sharp twinge in your side that makes you wince. Leaving the heavy silence of the tavern behind, you step out into the cool night air of Marrow’s Crossing. The damp scent of the river hangs thick over the cobblestones, and the distant, rhythmic churning of the water provides a steady backdrop to the town’s nocturnal quiet.

You find **Halden** standing near the stone rim of the town well, the lantern light casting long, dancing shadows across the parchment he is studying. He looks up as you approach, his weathered face etched with the fatigue of a man who has spent too many days calculating margins and transit times. You state your terms clearly: two hundred credits to deliver the ledger to the Crossed Keys Inn.

**Halden** pauses, his thumb tracing the edge of a pressed wax seal. He looks you over, his eyes lingering on the dark circles under your eyes and the guarded way you hold your torso. A slow, thoughtful nod follows. "Two hundred is steep for a short run to the inn, Aren," he says, his voice barely rising above the river’s hum. "But I’ve seen how you handle yourself on the road. I’d rather pay a premium for certainty than lose a book to a thief or a drunk."

He reaches into a small leather pouch at his belt and produces a small, heavy clinking of coin. He counts out a portion of the payment, pressing the iron coins into your palm. "Here is a hundred now to cover your trouble. The rest when the ledger is safely in the hands of the merchant at the inn. Don’t let the toughs at the door spoil the deal."


**T4:** You turn away from the well, the weight of the new **Credits** in your palm providing a small, solitary comfort against the ache in your ribs. You steer your path toward the east gate, moving through the winding veins of Marrow’s Crossing as the town’s nocturnal rhythms begin to settle into a steady, low pulse. The cobblestones underfoot are slick with river mist, reflecting the flickering lantern light like dark, polished bone.

The merchant road stretches out ahead of you, a well-trodden artery of dirt and stone that cuts through the edge of the town’s outskirts. As you walk, the sounds of the town’s center—the distant shouting of dock workers and the creak of waterwheels—begin to fade, replaced by the lonely whistle of the wind moving through the riverside reeds. You keep your hood pulled low, your eyes scanning the shadows of the roadside thickets for any movement that doesn't belong.

The silhouette of the *Crossed Keys Inn* eventually looms through the gloom, its timbered frame standing as a dark monolith against the starlit sky. Even from this distance, the atmosphere surrounding the establishment feels heavy and unsettled. You can see the faint, orange glow of hearth fires through its windows, but the entrance is partially obscured by the shifting shadows of figures leaning against the stone walls.


**T5:** You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.

## This Turn's (Turn 6) Result


**Band:** FAIL → The deceive fails. The attempt fails outright — what you tried to do does not happen.






**Momentum LOW (-2):** The player is struggling. Look for the one thing going slightly in their favor and name it. If the player attempts retreat, disengagement, or rest, allow the attempt to feel like it matters narratively.






=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Standing guard at the inn entrance, watching the player with predatory stillness and a derisive attitude.
- `tough_b` | **Scarred Tough** (Road thug) — Aggressively blocking the inn entrance, hand twitching near his club, and issuing a verbal threat to the player.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T5 context)
You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.

## CURRENT TURN 6 NARRATION
You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×101
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
deceive: The player attempts to bribe the thugs with 200 credits to clear the entrance.
## CURRENT TURN 6 NARRATION
You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "deceive",
  "intent": "The player attempts to bribe the thugs with 200 credits to clear the entrance.",
  "rolled": true,
  "total_ms": 3648.3,
  "tokens_in": 1571,
  "tokens_out": 115,
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
  "outcome_summary": "",
  "momentum_before": -1,
  "momentum_after": -2,
  "momentum_delta": -1
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the thugs with 200 credits to clear the entrance.",
  "intent_verb": "deceive",
  "target": "Bald Tough and Scarred Tough",
  "stakes": "[Mechanical cost: difficulty increase] + [Narrative consequence: the thugs reject the bribe and attack or demand more money]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "intimidation",
    "tense_standoff"
  ],
  "scene_tagline": "A Bribe Rejected",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance."
    },
    {
      "id": "tough_b",
      "notes": "Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively."
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
      "amount": 101
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "credits",
      "amount": 101
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "confrontation",
    "intimidation",
    "tense_standoff"
  ],
  "scene_tagline": "A Bribe Rejected",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance."
    },
    {
      "id": "tough_b",
      "notes": "Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively."
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

*(none)*

### Context Telemetry

- rules: est=1784t trimmed=False
- narrate: est=6428t trimmed=False
- extract.scene: est=3879t trimmed=False attempts=1
- extract.state: est=4176t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "turn": {
      "from": 6,
      "to": 7
    }
  }
}
```


---

# TURN 6

**Input:** ``

## User Prompts

### Rules User Prompt
```
(no rules call this turn)
```

### Narrate User Prompt
```
(no narrate call)
```

### Extract Scene User Prompt
```
(not captured)
```

### Extract State User Prompt
```
(not captured)
```

### Extract Progress User Prompt
```
(not captured)
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{}
```

### Extract State

```json
{}
```

### Extract Progress

```json
{}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "location_id": {
            "from": "marrows_crossing_streets",
            "to": "marrows_crossing_outskirts"
          },
          "location_name": {
            "from": "Marrow's Crossing Streets",
            "to": "Marrow's Crossing Outskirts"
          },
          "turn": {
            "from": 3,
            "to": 8
          }
        }
      },
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 6,
            "to": 8
          }
        }
      },
      "tough_b": {
        "last_seen": {
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
      "from": "A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.",
      "to": "The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold."
    }
  },
  "meta": {
    "consecutive_floor_count": {
      "from": 0,
      "to": 1
    },
    "turn": {
      "from": 7,
      "to": 8
    }
  },
  "pc": {
    "conditions": {
      "added": [
        {
          "added_turn": 7,
          "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
          "id": "shoulder_bruise",
          "label": "bruised shoulder",
          "turns_remaining": 10
        }
      ]
    },
    "momentum": {
      "from": -2,
      "to": -3
    }
  },
  "scene": {
    "present_npcs": {
      "added": [
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.",
          "title": "Merchant"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Steps away from the door to flank the player, completing the encirclement.",
            "title": "Road thug"
          }
        },
        {
          "from": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.",
            "title": "Road thug"
          }
        }
      ]
    },
    "tagline": {
      "from": "A Bribe Rejected",
      "to": "Caught in a Tightening Vice"
    },
    "tags": {
      "added": [
        "combat",
        "tense_confrontation",
        "ambush"
      ],
      "removed": [
        "confrontation",
        "tense_standoff",
        "intimidation"
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.
- Scarred Tough (Road thug) — Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.
## Current Turn: 7
=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance.
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.
- **Scarred Tough** (Road thug) — Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
## Recent Turns

**T5:** You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.


**T6:** You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.

## This Turn's (Turn 7) Result


**No roll required.** Describe what happens with appropriate weight for the moment.





**Momentum LOW (-2):** The player is struggling. Look for the one thing going slightly in their favor and name it. If the player attempts retreat, disengagement, or rest, allow the attempt to feel like it matters narratively.





**Narration Directive:** Location Pressure



=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.
- `tough_b` | **Scarred Tough** (Road thug) — Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T6 context)
You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.

## CURRENT TURN 7 NARRATION
You reach for the heavy parchment tucked inside your coat, fingers trembling slightly as the adrenaline of the standoff clashes with the dull ache in your ribs. You push past the wall of muscle that is the **Bald Tough**, your eyes fixed on the heavy oak door of the *Crossed Keys Inn*. You don't look at the men; you focus entirely on the threshold, moving with a desperate, singular purpose to reach the sanctuary of the interior.

Inside, the air is thick with the smell of roasted meat and stale ale, a sharp contrast to the damp chill of the road. You spot **Halden** sitting at a corner table, his weathered face partially obscured by the dim lantern light. You stumble toward him, your breath coming in shallow hitches, and slide the heavy **Halden's ledger** across the scarred wood of his table. You place the merchant seal beside it, the weight of the task finally shifting from your hands to the tabletop.

**Halden** looks up, his eyes widening as he sees the state of you—the sweat on your brow and the way you lean heavily against the chair. He glances toward the door, where the shadows of the two men loom large against the frosted glass of the entrance, their presence a dark promise of trouble waiting outside. He pulls the ledger toward him, his expression hardening as he realizes the price you paid just to reach his table.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
negotiate: The player hands over the merchant seal and ledger to Halden to complete a transaction.
## CURRENT TURN 7 NARRATION
You reach for the heavy parchment tucked inside your coat, fingers trembling slightly as the adrenaline of the standoff clashes with the dull ache in your ribs. You push past the wall of muscle that is the **Bald Tough**, your eyes fixed on the heavy oak door of the *Crossed Keys Inn*. You don't look at the men; you focus entirely on the threshold, moving with a desperate, singular purpose to reach the sanctuary of the interior.

Inside, the air is thick with the smell of roasted meat and stale ale, a sharp contrast to the damp chill of the road. You spot **Halden** sitting at a corner table, his weathered face partially obscured by the dim lantern light. You stumble toward him, your breath coming in shallow hitches, and slide the heavy **Halden's ledger** across the scarred wood of his table. You place the merchant seal beside it, the weight of the task finally shifting from your hands to the tabletop.

**Halden** looks up, his eyes widening as he sees the state of you—the sweat on your brow and the way you lean heavily against the chair. He glances toward the door, where the shadows of the two men loom large against the frosted glass of the entrance, their presence a dark promise of trouble waiting outside. He pulls the ledger toward him, his expression hardening as he realizes the price you paid just to reach his table.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player hands over the merchant seal and ledger to Halden to complete a transaction.",
  "rolled": false,
  "total_ms": 2857.8,
  "tokens_in": 1565,
  "tokens_out": 68
}
```

**Raw LLM output:**
```
{
  "intent": "The player hands over the merchant seal and ledger to Halden to complete a transaction.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "stakes": "",
  "check": {
    "required": false
  }
}
```

### Narration

You reach for the heavy parchment tucked inside your coat, fingers trembling slightly as the adrenaline of the standoff clashes with the dull ache in your ribs. You push past the wall of muscle that is the **Bald Tough**, your eyes fixed on the heavy oak door of the *Crossed Keys Inn*. You don't look at the men; you focus entirely on the threshold, moving with a desperate, singular purpose to reach the sanctuary of the interior.

Inside, the air is thick with the smell of roasted meat and stale ale, a sharp contrast to the damp chill of the road. You spot **Halden** sitting at a corner table, his weathered face partially obscured by the dim lantern light. You stumble toward him, your breath coming in shallow hitches, and slide the heavy **Halden's ledger** across the scarred wood of his table. You place the merchant seal beside it, the weight of the task finally shifting from your hands to the tabletop.

**Halden** looks up, his eyes widening as he sees the state of you—the sweat on your brow and the way you lean heavily against the chair. He glances toward the door, where the shadows of the two men loom large against the frosted glass of the entrance, their presence a dark promise of trouble waiting outside. He pulls the ledger toward him, his expression hardening as he realizes the price you paid just to reach his table.


### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "sanctuary",
    "suspense"
  ],
  "scene_tagline": "Seeking Refuge in the Inn",
  "location_change": {
    "id": "crossed_keys_inn",
    "name": "Crossed Keys Inn",
    "description": "A warm, dimly lit interior smelling of roasted meat and stale ale, offering a sharp contrast to the damp road outside."
  },
  "npc_add": [
    {
      "id": "halden",
      "notes": "Concerned and hardening his expression as he realizes the player is being pursued.",
      "name": "Halden",
      "title": "Merchant"
    }
  ],
  "npc_remove": [
    {
      "id": "tough_a"
    },
    {
      "id": "tough_b"
    }
  ],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Observing the player's distressed state and the looming threat outside the door."
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
      "id": "merchants_seal"
    },
    {
      "id": "halden_ledger"
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": []
}
```

### Extract Progress

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{}
```

### Rejected Deltas

```json
[
  {
    "field": "inventory_remove",
    "value": "merchants_seal",
    "reason": "Inventory item 'merchants_seal' does not exist"
  },
  {
    "field": "inventory_remove",
    "value": "halden_ledger",
    "reason": "Inventory item 'halden_ledger' does not exist"
  }
]
```

### Suggested Actions

*(none)*

### Context Telemetry

- rules: est=1783t trimmed=False
- narrate: est=6131t trimmed=False
- extract.scene: est=3848t trimmed=False attempts=1
- extract.state: est=4118t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "meta": {
    "last_compacted_turn": {
      "from": 4,
      "to": 7
    },
    "prior_history": {
      "added": [
        "- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.",
        "- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.",
        "- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack."
      ],
      "removed": []
    },
    "turn": {
      "from": 8,
      "to": 9
    }
  },
  "pc": {
    "conditions": {
      "changed": [
        {
          "from": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 10
          },
          "to": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 9
          }
        }
      ]
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.
- Scarred Tough (Road thug) — Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.
## Current Turn: 8
=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance.
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.
- **Scarred Tough** (Road thug) — Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
## Recent Turns

**T5:** You stride toward the dark silhouette of the inn, your boots striking the slick cobblestones with a rhythmic, heavy thud. As you draw closer to the entrance, the two figures leaning against the timbered wall come into clearer view. One is a massive man with a broken nose, the **Bald Tough**, whose arms are crossed over a barrel chest; the other is thinner, with a jagged line of white scar tissue running from his temple to his jaw, the **Scarred Tough**. Both men straighten as you approach, their eyes tracking your movement with a predatory stillness.

"What are you doing here?" you demand, your voice steady despite the dull throb in your ribs. "I’m not leaving until I hear your side of things."

The **Bald Tough** lets out a short, derisive snort that sounds like gravel grinding together. He doesn't move to block you, but he shifts his weight, occupying more of the doorway’s width. Beside him, the **Scarred Tough** reaches slowly for a heavy wooden club tucked into his belt, his fingers twitching near the handle.

"Our side?" the **Scarred Tough** sneers, his voice a thin, unpleasant rasp. "Our side is that this is a private conversation, traveler. You’ve got a delivery to make, or so the rumors say. Best you turn around and find a cheaper place to sleep before you find something harder than cobblestones to sleep on." He steps forward, closing the distance and placing himself directly between you and the inn’s heavy oak door.


**T6:** You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.


**T7:** You reach for the heavy parchment tucked inside your coat, fingers trembling slightly as the adrenaline of the standoff clashes with the dull ache in your ribs. You push past the wall of muscle that is the **Bald Tough**, your eyes fixed on the heavy oak door of the *Crossed Keys Inn*. You don't look at the men; you focus entirely on the threshold, moving with a desperate, singular purpose to reach the sanctuary of the interior.

Inside, the air is thick with the smell of roasted meat and stale ale, a sharp contrast to the damp chill of the road. You spot **Halden** sitting at a corner table, his weathered face partially obscured by the dim lantern light. You stumble toward him, your breath coming in shallow hitches, and slide the heavy **Halden's ledger** across the scarred wood of his table. You place the merchant seal beside it, the weight of the task finally shifting from your hands to the tabletop.

**Halden** looks up, his eyes widening as he sees the state of you—the sweat on your brow and the way you lean heavily against the chair. He glances toward the door, where the shadows of the two men loom large against the frosted glass of the entrance, their presence a dark promise of trouble waiting outside. He pulls the ledger toward him, his expression hardening as he realizes the price you paid just to reach his table.

## This Turn's (Turn 8) Result


**Band:** FAIL → The sneak fails. The attempt fails outright — what you tried to do does not happen. The roll was close — narrate a complication or setback that still allows the story to move forward, rather than a full dead-end punishment.






**Momentum FLOOR (-3):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.





**Narration Directive:** Location Pressure



=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
A well-trodden road of dirt and stone cutting through the edge of town, where the sounds of the center fade into the whistling wind and riverside reeds.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Shifting from derisive to outright predatory; uncrossing arms and preparing to move to block the entrance.
- `tough_b` | **Scarred Tough** (Road thug) — Ignoring the bribe and circling to the player's flank; hand gripped tight on his club and acting aggressively.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T7 context)
You reach for the heavy parchment tucked inside your coat, fingers trembling slightly as the adrenaline of the standoff clashes with the dull ache in your ribs. You push past the wall of muscle that is the **Bald Tough**, your eyes fixed on the heavy oak door of the *Crossed Keys Inn*. You don't look at the men; you focus entirely on the threshold, moving with a desperate, singular purpose to reach the sanctuary of the interior.

Inside, the air is thick with the smell of roasted meat and stale ale, a sharp contrast to the damp chill of the road. You spot **Halden** sitting at a corner table, his weathered face partially obscured by the dim lantern light. You stumble toward him, your breath coming in shallow hitches, and slide the heavy **Halden's ledger** across the scarred wood of his table. You place the merchant seal beside it, the weight of the task finally shifting from your hands to the tabletop.

**Halden** looks up, his eyes widening as he sees the state of you—the sweat on your brow and the way you lean heavily against the chair. He glances toward the door, where the shadows of the two men loom large against the frosted glass of the entrance, their presence a dark promise of trouble waiting outside. He pulls the ledger toward him, his expression hardening as he realizes the price you paid just to reach his table.

## CURRENT TURN 8 NARRATION
You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
sneak: The player attempts to use a brass key to unlock the inn's front door or find an alternative entrance.
## CURRENT TURN 8 NARRATION
You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "sneak",
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find an alternative entrance.",
  "rolled": true,
  "total_ms": 3471.6,
  "tokens_in": 1570,
  "tokens_out": 117,
  "skill": "dexterity",
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
  "outcome_summary": "",
  "momentum_before": -2,
  "momentum_after": -3,
  "momentum_delta": -1
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use a brass key to unlock the inn's front door or find an alternative entrance.",
  "intent_verb": "sneak",
  "target": "inn's front door",
  "stakes": "[Mechanical cost: failure to enter] + [Narrative consequence: the thugs block the entrance or intercept the player]",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal"
  }
}
```

### Narration

You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "tense_confrontation",
    "ambush"
  ],
  "scene_tagline": "Caught in a Tightening Vice",
  "location_description": "The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Steps away from the door to flank the player, completing the encirclement."
    },
    {
      "id": "tough_b",
      "notes": "Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking."
    },
    {
      "id": "halden",
      "notes": "Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk."
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
  "pc_condition_add": [
    {
      "id": "shoulder_bruise",
      "label": "bruised shoulder",
      "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.",
  "pc_condition_add": [
    {
      "id": "shoulder_bruise",
      "label": "bruised shoulder",
      "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise."
    }
  ],
  "pc_condition_remove": [],
  "scene_tags": [
    "combat",
    "tense_confrontation",
    "ambush"
  ],
  "scene_tagline": "Caught in a Tightening Vice",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Steps away from the door to flank the player, completing the encirclement."
    },
    {
      "id": "tough_b",
      "notes": "Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking."
    },
    {
      "id": "halden",
      "notes": "Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk."
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

*(none)*

### Context Telemetry

- rules: est=1785t trimmed=False
- narrate: est=6624t trimmed=False
- extract.scene: est=3888t trimmed=False attempts=1
- extract.state: est=4214t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "active_threads": {
      "changed": [
        {
          "from": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "unlock_if": null,
            "urgency": "normal"
          },
          "to": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "unlock_if": null,
            "urgency": "normal"
          },
          "to": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "unlock_if": null,
            "urgency": "low"
          },
          "to": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "urgency": "low"
          }
        },
        {
          "from": {
            "id": "the_toughs_at_the_crossed",
            "last_offered_turn": 3,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          },
          "to": {
            "id": "the_toughs_at_the_crossed",
            "last_offered_turn": 3,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          }
        }
      ]
    },
    "arc_engagement": {
      "from": 2,
      "to": 3
    },
    "latent_threads": {
      "added": [
        {
          "id": "matthew_estrada's_calm_reaction_to",
          "last_offered_turn": 10,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler.",
          "tags": [
            "tactical"
          ],
          "urgency": "background"
        }
      ],
      "changed": [
        {
          "from": {
            "id": "the_shadowy_figures_leaning_against",
            "last_offered_turn": 4,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          },
          "to": {
            "id": "the_shadowy_figures_leaning_against",
            "last_offered_turn": 4,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "innkeeper": {
        "last_seen": {
          "from": null,
          "to": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 10
          }
        }
      },
      "matthew_estrada": {
        "bio": {
          "from": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
          "to": "A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner."
        },
        "last_seen": {
          "from": null,
          "to": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 10
          }
        }
      },
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 8,
            "to": 10
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "turn": {
            "from": 8,
            "to": 10
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.",
      "to": "The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door."
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "matthew_estrada"
      ],
      "removed": []
    },
    "consecutive_floor_count": {
      "from": 1,
      "to": 2
    },
    "pending_gm_beat": {
      "from": null,
      "to": {
        "beat_expires_turn": 12,
        "instruction": "The Scarred Tough and Bald Tough burst through the splintered door into the common room.",
        "surface_as": "event",
        "type": "escalation"
      }
    },
    "turn": {
      "from": 9,
      "to": 10
    }
  },
  "pc": {
    "conditions": {
      "changed": [
        {
          "from": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 9
          },
          "to": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 8
          }
        }
      ]
    }
  },
  "scene": {
    "present_npcs": {
      "added": [
        {
          "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
          "id": "matthew_estrada",
          "name": "Matthew Estrada",
          "notes": "Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure.",
          "title": "Traveler"
        },
        {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "id": "innkeeper",
          "name": "Edda",
          "notes": "Retreating toward the kitchen in alarm following the door being breached.",
          "title": "Innkeeper at the Crossed Keys"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Steps away from the door to flank the player, completing the encirclement.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Distracted from the player by the violence at the entrance.",
            "title": "Road thug"
          }
        },
        {
          "from": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Distracted from the player by the violence at the entrance.",
            "title": "Road thug"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "inn_under_siege",
          "text": "The thugs have successfully breached the entrance of the Crossed Keys Inn, causing chaos among the patrons.",
          "turn": 10
        }
      ]
    },
    "scene_pressure": {
      "added": [
        {
          "id": "inn_breach_chaos",
          "max_turns": null,
          "text": "Thugs are forcing entry into the inn, creating immediate violence.",
          "turn_added": 10,
          "urgency": "immediate"
        }
      ]
    },
    "tagline": {
      "from": "Caught in a Tightening Vice",
      "to": "The Siege of Crossed Keys"
    },
    "tags": {
      "added": [
        "chaos"
      ],
      "removed": [
        "ambush"
      ]
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Steps away from the door to flank the player, completing the encirclement.
- Scarred Tough (Road thug) — Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.
- Halden (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
## Current Turn: 9
=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance.
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Steps away from the door to flank the player, completing the encirclement.
- **Scarred Tough** (Road thug) — Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.
- **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
## Recent Turns

**T6:** You reach into your pouch and pull out a handful of heavy iron coins, letting them spill from your fingers. The **Credits** hit the slick cobblestones with a series of sharp, metallic clinks, scattering across the dark stone between your boots and the men’s feet. You stand your ground, your voice cutting through the damp air as you inform them that your business with Caron is settled and their presence is no longer required.

The **Scarred Tough** stares down at the pile of coin, his eyes narrowing as a cruel, jagged grin splits his face. He doesn't reach for the money; instead, he taps the heavy wooden club at his belt with a rhythmic, menacing thud. Beside him, the **Bald Tough** lets out a low, guttural chuckle that vibrates in his massive chest, his expression shifting from derisive to outright predatory.

"You think we’re beggars, little runner?" the **Scarred Tough** rasps, his fingers finally closing tight around the handle of his weapon. He ignores the pile of silver entirely, stepping over the coins to loom over you, his shadow stretching long and dark across your path. "Caron’s coin is your business. Ours is whatever we decide to take from you."

The **Bald Tough** uncrosses his arms, his barrel chest expanding as he prepares to move. He stays planted by the door, effectively walling off the entrance, while the thinner man begins to circle to your flank. The weight of the situation settles heavily on your shoulders; the bribe was a mistake, and now the tension in the air is thick enough to choke on.


**T7:** You reach for the heavy parchment tucked inside your coat, fingers trembling slightly as the adrenaline of the standoff clashes with the dull ache in your ribs. You push past the wall of muscle that is the **Bald Tough**, your eyes fixed on the heavy oak door of the *Crossed Keys Inn*. You don't look at the men; you focus entirely on the threshold, moving with a desperate, singular purpose to reach the sanctuary of the interior.

Inside, the air is thick with the smell of roasted meat and stale ale, a sharp contrast to the damp chill of the road. You spot **Halden** sitting at a corner table, his weathered face partially obscured by the dim lantern light. You stumble toward him, your breath coming in shallow hitches, and slide the heavy **Halden's ledger** across the scarred wood of his table. You place the merchant seal beside it, the weight of the task finally shifting from your hands to the tabletop.

**Halden** looks up, his eyes widening as he sees the state of you—the sweat on your brow and the way you lean heavily against the chair. He glances toward the door, where the shadows of the two men loom large against the frosted glass of the entrance, their presence a dark promise of trouble waiting outside. He pulls the ledger toward him, his expression hardening as he realizes the price you paid just to reach his table.


**T8:** You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.

## This Turn's (Turn 9) Result


**Band:** PARTIAL → The deceive results in a partial. You get what you asked for, but they now hold leverage over you.






**Momentum FLOOR (-3):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.





**Narration Directive:** Location Imperative



=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Steps away from the door to flank the player, completing the encirclement.
- `tough_b` | **Scarred Tough** (Road thug) — Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.
- `halden` | **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T8 context)
You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.

## CURRENT TURN 9 NARRATION
You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
deceive: The player attempts to bribe the thugs through the wall to gain entry or de-escalate the situation.
## CURRENT TURN 9 NARRATION
You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## present_npcs (in scene right now)
- `tough_a` | **Bald Tough** (Road thug) — Pauses his advance to watch the innkeeper's silhouette through the glass.
- `tough_b` | **Scarred Tough** (Road thug) — Mocking the player and jeering loudly to draw attention from the patrons inside.
- `halden` | **Halden** (Merchant) — Watching the commotion from inside the inn.
- `edda` | **Edda** (Innkeeper) — Approaching the door from inside the inn to demand order; currently a distraction to the thugs.

## known_characters (not in scene — system-called, for reasoning only)
- `caron` | **Caron** — A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- `halden` | **Halden** — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `innkeeper` | **Edda** — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_a` | **Bald Tough** — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing Outskirts** — The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise: bruised shoulder — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.


## active_threads
- `settle_the_debt` [NORMAL] Settle the 500-credit debt with Caron. tags: debt, caron, obligation
- `deliver_the_ledger` [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. tags: courier, halden, contract
- `clear_the_road_toughs` [LOW] Deal with the toughs blocking the inn entrance. tags: toughs, road, confrontation
- `the_toughs_at_the_crossed` [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery. tags: tactical

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is dead; he now views you with a heavy sort of respect.
- Halden has hired you to deliver his ledger to the Crossed Keys Inn, providing a 100-credit advance on the 200-credit fee.
- The Crossed Keys Inn feels heavy and unsettled, with shadows of figures loitering near the entrance.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## rules_stakes
Band: PARTIAL. At-risk cost named by rules engine: [Mechanical cost: difficulty increase] + [Narrative consequence: the thugs ignore the bribe and attack more aggressively]
## gm_beat
## last_turn_narration (T8)
You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.
## player_intent
**deceive**: The player attempts to bribe the thugs through the wall to gain entry or de-escalate the situation.
## CURRENT TURN 9 NARRATION
You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "deceive",
  "intent": "The player attempts to bribe the thugs through the wall to gain entry or de-escalate the situation.",
  "rolled": true,
  "total_ms": 3182.2,
  "tokens_in": 1598,
  "tokens_out": 116,
  "skill": "charisma",
  "difficulty": "hard",
  "dice": [
    6,
    3
  ],
  "stat_mod": 1,
  "diff_mod": -1,
  "cond_mod": 0,
  "final_total": 9,
  "band": "partial",
  "outcome_summary": "Your attempt to bribe the inn via the wall fails miserably, drawing jeers from the thugs and drawing the attention of Edda inside.",
  "momentum_before": -3,
  "momentum_after": -3,
  "momentum_delta": 0
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the thugs through the wall to gain entry or de-escalate the situation.",
  "intent_verb": "deceive",
  "target": "Bald Tough and Scarred Tough",
  "stakes": "[Mechanical cost: difficulty increase] + [Narrative consequence: the thugs ignore the bribe and attack more aggressively]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "hard"
  }
}
```

### Narration

You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.


### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "tense_confrontation",
    "intimidation"
  ],
  "scene_tagline": "A Mocking Laughter and a Stern Warning",
  "npc_add": [
    {
      "id": "edda",
      "notes": "Approaching the door from inside the inn to demand order; currently a distraction to the thugs.",
      "name": "Edda",
      "title": "Innkeeper",
      "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it disrupts the inn."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Pauses his advance to watch the innkeeper's silhouette through the glass."
    },
    {
      "id": "tough_b",
      "notes": "Mocking the player and jeering loudly to draw attention from the patrons inside."
    },
    {
      "id": "halden",
      "notes": "Watching the commotion from inside the inn."
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
  "recent_events_add": [
    {
      "id": "failed_bribe_attempt",
      "text": "The attempt to bribe the inn through the wall failed, drawing more mockery from the thugs.",
      "turn": 9
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Lunge at the Scarred Tough while he is distracted by the door.",
    "Call out to Edda for help through the frosted glass.",
    "Use your iron dagger to strike at the Bald Tough's leg.",
    "Attempt to bolt past the thugs toward the shadows of the outskirts."
  ],
  "outcome_summary": "Your attempt to bribe the inn via the wall fails miserably, drawing jeers from the thugs and drawing the attention of Edda inside.",
  "beat_disposition": "consume",
  "scene_pressure_add": [
    {
      "id": "thug_aggression_escalation",
      "text": "The thugs are becoming more aggressive and mocking due to your failed bribe.",
      "urgency": "immediate",
      "turn_added": 9
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "thread_signals": [
    {
      "id": "clear_the_road_toughs",
      "signal": "blocked"
    },
    {
      "id": "the_toughs_at_the_crossed",
      "signal": "advanced"
    }
  ],
  "drift_analysis": [
    {
      "thread_id": "settle_the_debt",
      "match": false,
      "reason": "",
      "new_interest": ""
    },
    {
      "thread_id": "deliver_the_ledger",
      "match": false,
      "reason": "",
      "new_interest": ""
    },
    {
      "thread_id": "clear_the_road_toughs",
      "match": false,
      "reason": "The player's failed bribe attempt and the thugs' reaction have increased the immediate threat rather than resolving it.",
      "new_interest": ""
    },
    {
      "thread_id": "the_toughs_at_the_crossed",
      "match": true,
      "reason": "The thugs' aggression and the innkeeper's intervention have escalated the confrontation at the entrance.",
      "new_interest": ""
    }
  ],
  "player_drift_signals": [],
  "candidate_opportunity": "Edda's intervention provides a brief window to potentially reach the door or seek help from the innkeeper."
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

- Lunge at the Scarred Tough while he is distracted by the door.

- Call out to Edda for help through the frosted glass.

- Use your iron dagger to strike at the Bald Tough's leg.

- Attempt to bolt past the thugs toward the shadows of the outskirts.

### Context Telemetry

- rules: est=1820t trimmed=False
- narrate: est=6686t trimmed=False
- extract.scene: est=4011t trimmed=False attempts=1
- extract.state: est=4247t trimmed=False attempts=1
- extract.progress: est=4592t trimmed=False attempts=1

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "active_threads": {
      "changed": [
        {
          "from": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "urgency": "normal"
          },
          "to": {
            "id": "settle_the_debt",
            "last_offered_turn": 0,
            "progress": 0,
            "promotes": [],
            "state": "active",
            "summary": "Settle the 500-credit debt with Caron.",
            "tags": [
              "debt",
              "caron",
              "obligation"
            ],
            "unlock_if": null,
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "urgency": "normal"
          },
          "to": {
            "id": "deliver_the_ledger",
            "last_offered_turn": 0,
            "progress": 2,
            "promotes": [],
            "state": "active",
            "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
            "tags": [
              "courier",
              "halden",
              "contract"
            ],
            "unlock_if": null,
            "urgency": "normal"
          }
        },
        {
          "from": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "urgency": "low"
          },
          "to": {
            "id": "clear_the_road_toughs",
            "last_offered_turn": 0,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "Deal with the toughs blocking the inn entrance.",
            "tags": [
              "toughs",
              "road",
              "confrontation"
            ],
            "unlock_if": null,
            "urgency": "low"
          }
        },
        {
          "from": {
            "id": "the_toughs_at_the_crossed",
            "last_offered_turn": 3,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          },
          "to": {
            "id": "the_toughs_at_the_crossed",
            "last_offered_turn": 3,
            "progress": 1,
            "promotes": [],
            "state": "active",
            "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          }
        }
      ]
    },
    "latent_threads": {
      "changed": [
        {
          "from": {
            "id": "the_shadowy_figures_leaning_against",
            "last_offered_turn": 4,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          },
          "to": {
            "id": "the_shadowy_figures_leaning_against",
            "last_offered_turn": 4,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          }
        },
        {
          "from": {
            "id": "matthew_estrada's_calm_reaction_to",
            "last_offered_turn": 10,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler.",
            "tags": [
              "tactical"
            ],
            "urgency": "background"
          },
          "to": {
            "id": "matthew_estrada's_calm_reaction_to",
            "last_offered_turn": 10,
            "progress": 0,
            "promotes": [],
            "state": "latent",
            "summary": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler.",
            "tags": [
              "tactical"
            ],
            "unlock_if": null,
            "urgency": "background"
          }
        }
      ]
    }
  },
  "compendium": {
    "npcs": {
      "halden": {
        "last_seen": {
          "turn": {
            "from": 8,
            "to": 11
          }
        }
      },
      "innkeeper": {
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
      },
      "tough_a": {
        "last_seen": {
          "turn": {
            "from": 10,
            "to": 11
          }
        }
      },
      "tough_b": {
        "last_seen": {
          "turn": {
            "from": 10,
            "to": 11
          }
        }
      }
    }
  },
  "location": {
    "description": {
      "from": "The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door.",
      "to": "The common room is now a battlefield of overturned chairs, spilled ale, and jagged wooden shards from the breached door."
    }
  },
  "meta": {
    "consecutive_floor_count": {
      "from": 2,
      "to": 3
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 12,
        "to": 13
      },
      "instruction": {
        "from": "The Scarred Tough and Bald Tough burst through the splintered door into the common room.",
        "to": null
      },
      "surface_as": {
        "from": "event",
        "to": "ambient"
      },
      "type": {
        "from": "escalation",
        "to": "breathing_room"
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
          "description": "The clumsy collision and slip on spilled ale have left you off-balance and disoriented.",
          "id": "staggered",
          "label": "staggered",
          "turns_remaining": 10
        }
      ],
      "changed": [
        {
          "from": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 8
          },
          "to": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 7
          }
        }
      ]
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
            "notes": "Distracted from the player by the violence at the entrance.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
            "id": "tough_a",
            "name": "Bald Tough",
            "notes": "Charging through the wreckage with weapons raised, eyes wild.",
            "title": "Road thug"
          }
        },
        {
          "from": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Distracted from the player by the violence at the entrance.",
            "title": "Road thug"
          },
          "to": {
            "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
            "id": "tough_b",
            "name": "Scarred Tough",
            "notes": "Charging through the wreckage with weapons raised, eyes wild.",
            "title": "Road thug"
          }
        },
        {
          "from": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.",
            "title": "Merchant"
          },
          "to": {
            "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
            "id": "halden",
            "name": "Halden",
            "notes": "Scrambling for cover amidst the sudden violence.",
            "title": "Merchant"
          }
        },
        {
          "from": {
            "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
            "id": "matthew_estrada",
            "name": "Matthew Estrada",
            "notes": "Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure.",
            "title": "Traveler"
          },
          "to": {
            "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
            "id": "matthew_estrada",
            "name": "Matthew Estrada",
            "notes": "Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment.",
            "title": "Traveler"
          }
        },
        {
          "from": {
            "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
            "id": "innkeeper",
            "name": "Edda",
            "notes": "Retreating toward the kitchen in alarm following the door being breached.",
            "title": "Innkeeper at the Crossed Keys"
          },
          "to": {
            "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
            "id": "innkeeper",
            "name": "Edda",
            "notes": "Retreating toward the kitchen in alarm.",
            "title": "Innkeeper at the Crossed Keys"
          }
        }
      ]
    },
    "tagline": {
      "from": "The Siege of Crossed Keys",
      "to": "The Inn is Under Siege"
    },
    "tags": {
      "added": [
        "intrusion"
      ],
      "removed": [
        "tense_confrontation"
      ]
    }
  }
}
```


---

# TURN 9

**Input:** ``

## User Prompts

### Rules User Prompt
```
(no rules call this turn)
```

### Narrate User Prompt
```
(no narrate call)
```

### Extract Scene User Prompt
```
(not captured)
```

### Extract State User Prompt
```
(not captured)
```

### Extract Progress User Prompt
```
(not captured)
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{}
```

### Extract State

```json
{}
```

### Extract Progress

```json
{}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "innkeeper": {
        "last_seen": {
          "location_id": {
            "from": "marrows_crossing_outskirts",
            "to": "marrows_crossing_docks"
          },
          "location_name": {
            "from": "Marrow's Crossing Outskirts",
            "to": "Marrow's Crossing Docks"
          },
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
        "id": "halden_ledger",
        "name": "Halden's ledger",
        "notes": "A parchment ledger belonging to Halden."
      }
    ]
  },
  "location": {
    "description": {
      "from": "The common room is now a battlefield of overturned chairs, spilled ale, and jagged wooden shards from the breached door.",
      "to": "A narrow, muddy area near the riverbanks under gray, damp skies."
    },
    "id": {
      "from": "marrows_crossing_outskirts",
      "to": "marrows_crossing_docks"
    },
    "name": {
      "from": "Marrow's Crossing Outskirts",
      "to": "Marrow's Crossing Docks"
    }
  },
  "meta": {
    "consecutive_floor_count": {
      "from": 3,
      "to": 4
    },
    "last_compacted_turn": {
      "from": 7,
      "to": 10
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 13,
        "to": 14
      }
    },
    "prior_history": {
      "added": [
        "- [T9] You attempted to bribe the inn wall with a credit to distract the thugs, but the Bald Tough and Scarred Tough continued their assault as Edda emerged to investigate the noise.",
        "- [T10] You confronted Matthew Estrada at the bar regarding his soldier-like demeanor, but the confrontation was interrupted when the thugs successfully breached the inn's front door.",
        "- [T8] The Scarred Tough attacked you outside the inn, causing a bruised shoulder while you failed to find a side entrance with the brass key."
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
      "removed": [
        {
          "added_turn": 10,
          "description": "The clumsy collision and slip on spilled ale have left you off-balance and disoriented.",
          "id": "staggered",
          "label": "staggered",
          "turns_remaining": 10
        }
      ],
      "changed": [
        {
          "from": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 7
          },
          "to": {
            "added_turn": 7,
            "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
            "id": "shoulder_bruise",
            "label": "bruised shoulder",
            "turns_remaining": 6
          }
        }
      ]
    }
  },
  "scene": {
    "location_entered_turn": {
      "from": 3,
      "to": 11
    },
    "present_npcs": {
      "removed": [
        {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "id": "tough_a",
          "name": "Bald Tough",
          "notes": "Charging through the wreckage with weapons raised, eyes wild.",
          "title": "Road thug"
        },
        {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "id": "tough_b",
          "name": "Scarred Tough",
          "notes": "Charging through the wreckage with weapons raised, eyes wild.",
          "title": "Road thug"
        },
        {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "id": "halden",
          "name": "Halden",
          "notes": "Scrambling for cover amidst the sudden violence.",
          "title": "Merchant"
        },
        {
          "bio": "A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.",
          "id": "matthew_estrada",
          "name": "Matthew Estrada",
          "notes": "Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment.",
          "title": "Traveler"
        }
      ],
      "changed": [
        {
          "from": {
            "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
            "id": "innkeeper",
            "name": "Edda",
            "notes": "Retreating toward the kitchen in alarm.",
            "title": "Innkeeper at the Crossed Keys"
          },
          "to": {
            "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
            "id": "innkeeper",
            "name": "Edda",
            "notes": "Startled and defensive, clutching a skillet as the player shoves past her.",
            "title": "Innkeeper at the Crossed Keys"
          }
        }
      ]
    },
    "recent_events": {
      "added": [
        {
          "id": "halden_contract_active",
          "text": "Halden has entrusted you with his ledger; the delivery to the Crossed Keys Inn is your primary objective.",
          "turn": 3
        },
        {
          "id": "inn_siege_chaos",
          "text": "The Crossed Keys Inn is under siege; thugs have breached the entrance, sending patrons scrambling for cover.",
          "turn": 10
        },
        {
          "id": "matthew_estrada_suspicion",
          "text": "Matthew Estrada watches the room with the calculating gaze of a soldier, his true purpose remains a mystery.",
          "turn": 10
        }
      ],
      "removed": [
        {
          "id": "caron_debt_cleared",
          "text": "Your debt to Caron is dead; he now views you with a heavy sort of respect.",
          "turn": 2
        },
        {
          "id": "halden_contract_advance",
          "text": "Halden has hired you to deliver his ledger to the Crossed Keys Inn, providing a 100-credit advance on the 200-credit fee.",
          "turn": 3
        },
        {
          "id": "road_toughs_rumors",
          "text": "The Crossed Keys Inn feels heavy and unsettled, with shadows of figures loitering near the entrance.",
          "turn": 4
        },
        {
          "id": "inn_under_siege",
          "text": "The thugs have successfully breached the entrance of the Crossed Keys Inn, causing chaos among the patrons.",
          "turn": 10
        }
      ]
    },
    "tagline": {
      "from": "The Inn is Under Siege",
      "to": "A Desperate Flight to the River"
    },
    "tags": {
      "added": [
        "escape"
      ],
      "removed": [
        "intrusion"
      ]
    },
    "turn_entered": {
      "from": 3,
      "to": 11
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Steps away from the door to flank the player, completing the encirclement.
- Scarred Tough (Road thug) — Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.
- Halden (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
## Current Turn: 10
=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance.
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Matthew Estrada** - A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Steps away from the door to flank the player, completing the encirclement.
- **Scarred Tough** (Road thug) — Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.
- **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.
- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.
- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.
## Recent Turns

**T8:** You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.


**T9:** You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.

## This Turn's (Turn 10) Result


**Band:** FAIL → The intimidate fails. The attempt fails outright — what you tried to do does not happen.






**Momentum FLOOR (-3):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.





**Narration Directive:** Location Imperative



=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The heavy oak door of the Crossed Keys Inn stands as a barrier between the warmth of the interior and the violence of the threshold.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Steps away from the door to flank the player, completing the encirclement.
- `tough_b` | **Scarred Tough** (Road thug) — Lunges from the flank and strikes the player's shoulder with a wooden club; acting highly aggressive and mocking.
- `halden` | **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T9 context)
You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.

## CURRENT TURN 10 NARRATION
You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
intimidate: Aren demands the truth from Matthew Estrada regarding his true identity and suspicious behavior.
## CURRENT TURN 10 NARRATION
You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```
## present_npcs (in scene right now)
- `tough_a` | **Bald Tough** (Road thug) — Distracted from the player by the violence at the entrance.
- `tough_b` | **Scarred Tough** (Road thug) — Distracted from the player by the violence at the entrance.
- `halden` | **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.

## known_characters (not in scene — system-called, for reasoning only)
- `caron` | **Caron** — A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- `halden` | **Halden** — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `innkeeper` | **Edda** — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `matthew_estrada` | **Matthew Estrada** — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_a` | **Bald Tough** — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.

## location
**Marrow's Crossing Outskirts** — The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise: bruised shoulder — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.


## active_threads
- `settle_the_debt` [NORMAL] Settle the 500-credit debt with Caron. tags: debt, caron, obligation
- `deliver_the_ledger` [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. tags: courier, halden, contract
- `clear_the_road_toughs` [LOW] Deal with the toughs blocking the inn entrance. tags: toughs, road, confrontation
- `the_toughs_at_the_crossed` [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery. tags: tactical

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is dead; he now views you with a heavy sort of respect.
- Halden has hired you to deliver his ledger to the Crossed Keys Inn, providing a 100-credit advance on the 200-credit fee.
- The Crossed Keys Inn feels heavy and unsettled, with shadows of figures loitering near the entrance.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## rules_stakes
Band: FAIL. At-risk cost named by rules engine: [Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: Matthew reacts defensively or reveals hostility, potentially escalating the confrontation with the thugs.]
If a narrative consequence is named above (e.g. an NPC acting, alarm raised, escape cut off), emit it as a scene_pressure_add entry at `immediate` urgency.
## gm_beat
## last_turn_narration (T9)
You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.
## player_intent
**intimidate**: Aren demands the truth from Matthew Estrada regarding his true identity and suspicious behavior.
## CURRENT TURN 10 NARRATION
You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "intimidate",
  "intent": "Aren demands the truth from Matthew Estrada regarding his true identity and suspicious behavior.",
  "rolled": true,
  "total_ms": 3179.3,
  "tokens_in": 1600,
  "tokens_out": 116,
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
  "outcome_summary": "Your attempt to intimidate Matthew Estrada is interrupted by the violent splintering of the inn's door as the thugs force their way in.",
  "momentum_before": -3,
  "momentum_after": -3,
  "momentum_delta": 0
}
```

**Raw LLM output:**
```
{
  "intent": "Aren demands the truth from Matthew Estrada regarding his true identity and suspicious behavior.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: Matthew reacts defensively or reveals hostility, potentially escalating the confrontation with the thugs.]",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "chaos",
    "tense_confrontation"
  ],
  "scene_tagline": "The Siege of Crossed Keys",
  "location_description": "The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "matthew_estrada",
      "notes": "Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure."
    },
    {
      "id": "innkeeper",
      "notes": "Retreating toward the kitchen in alarm following the door being breached."
    },
    {
      "id": "tough_a",
      "notes": "Distracted from the player by the violence at the entrance."
    },
    {
      "id": "tough_b",
      "notes": "Distracted from the player by the violence at the entrance."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "matthew_estrada",
      "bio": "A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.",
      "aliases": []
    }
  ]
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
  "recent_events_add": [
    {
      "id": "inn_under_siege",
      "text": "The thugs have successfully breached the entrance of the Crossed Keys Inn, causing chaos among the patrons.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Demand more information from Matthew Estrada about his identity",
    "Use the chaos to slip past Matthew toward the door",
    "Attempt to help Edda or patrons scrambling for cover",
    "Draw your iron dagger to prepare for the imminent breach"
  ],
  "outcome_summary": "Your attempt to intimidate Matthew Estrada is interrupted by the violent splintering of the inn's door as the thugs force their way in.",
  "gm_beat": {
    "type": "escalation",
    "surface_as": "event",
    "instruction": "The Scarred Tough and Bald Tough burst through the splintered door into the common room."
  },
  "beat_disposition": "replace",
  "scene_pressure_add": [
    {
      "id": "inn_breach_chaos",
      "text": "Thugs are forcing entry into the inn, creating immediate violence.",
      "urgency": "immediate",
      "turn_added": 10
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": [],
  "thread_signals": [
    {
      "id": "clear_the_road_toughs",
      "signal": "advanced"
    },
    {
      "id": "the_toughs_at_the_crossed",
      "signal": "advanced"
    }
  ],
  "drift_analysis": [
    {
      "thread_id": "clear_the_road_toughs",
      "match": true,
      "reason": "The player's confrontation with Matthew is interrupted by the thugs' physical breach of the inn.",
      "new_interest": ""
    },
    {
      "thread_id": "the_toughs_at_the_crossed",
      "match": true,
      "reason": "The thugs have moved from the threshold to actively breaking into the scene.",
      "new_interest": ""
    },
    {
      "thread_id": "deliver_the_ledger",
      "match": false,
      "reason": "The player is currently preoccupied with a confrontation and the sudden violence.",
      "new_interest": ""
    },
    {
      "thread_id": "settle_the_debt",
      "match": false,
      "reason": "The player's focus is entirely on the immediate survival and the encounter with Matthew.",
      "new_interest": ""
    }
  ],
  "player_drift_signals": [],
  "candidate_opportunity": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler."
}
```

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door.",
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "scene_tags": [
    "combat",
    "chaos",
    "tense_confrontation"
  ],
  "scene_tagline": "The Siege of Crossed Keys",
  "compendium_npc_update": [
    {
      "id": "matthew_estrada",
      "bio": "A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.",
      "aliases": []
    }
  ],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "matthew_estrada",
      "notes": "Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure."
    },
    {
      "id": "innkeeper",
      "notes": "Retreating toward the kitchen in alarm following the door being breached."
    },
    {
      "id": "tough_a",
      "notes": "Distracted from the player by the violence at the entrance."
    },
    {
      "id": "tough_b",
      "notes": "Distracted from the player by the violence at the entrance."
    }
  ],
  "recent_events_add": [
    {
      "id": "inn_under_siege",
      "text": "The thugs have successfully breached the entrance of the Crossed Keys Inn, causing chaos among the patrons.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "scene_pressure_add": [
    {
      "id": "inn_breach_chaos",
      "text": "Thugs are forcing entry into the inn, creating immediate violence.",
      "urgency": "immediate",
      "turn_added": 10
    }
  ],
  "scene_pressure_remove": [],
  "scene_pressure_update": []
}
```

### Rejected Deltas

*(none)*

### Suggested Actions

- Demand more information from Matthew Estrada about his identity

- Use the chaos to slip past Matthew toward the door

- Attempt to help Edda or patrons scrambling for cover

- Draw your iron dagger to prepare for the imminent breach

### Context Telemetry

- rules: est=1824t trimmed=False
- narrate: est=6447t trimmed=False
- extract.scene: est=4041t trimmed=False attempts=1
- extract.state: est=4272t trimmed=False attempts=1
- extract.progress: est=4653t trimmed=False attempts=2

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "compendium": {
    "npcs": {
      "dock_boy": {
        "from": null,
        "to": {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 13
          },
          "name": "Dock Boy",
          "title": "Messenger"
        }
      },
      "innkeeper": {
        "bio": {
          "from": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "to": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Startled and defensive, clutching a skillet as the player shoves past her."
        }
      }
    }
  },
  "inventory": {
    "changed": [
      {
        "from": {
          "aliases": [],
          "amount": 3,
          "id": "bandages",
          "name": "Linen bandages",
          "notes": "Three rolls. Field-grade \u2014 won't replace a healer."
        },
        "to": {
          "aliases": [],
          "amount": 2,
          "id": "bandages",
          "name": "Linen bandages",
          "notes": "Three rolls. Field-grade \u2014 won't replace a healer."
        }
      }
    ]
  },
  "location": {
    "description": {
      "from": "A narrow, muddy area near the riverbanks under gray, damp skies.",
      "to": "A shadowed nook between stacked crates of salt-fish near the muddy riverbank."
    }
  },
  "meta": {
    "compendium_touch_order": {
      "added": [
        "dock_boy"
      ],
      "removed": []
    },
    "consecutive_floor_count": {
      "from": 4,
      "to": 5
    },
    "pending_gm_beat": {
      "beat_expires_turn": {
        "from": 14,
        "to": 15
      }
    },
    "turn": {
      "from": 12,
      "to": 13
    }
  },
  "pc": {
    "conditions": {
      "removed": [
        {
          "added_turn": 8,
          "description": "A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.",
          "id": "bruised_ribs",
          "label": "bruised ribs"
        },
        {
          "added_turn": 7,
          "description": "A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.",
          "id": "shoulder_bruise",
          "label": "bruised shoulder",
          "turns_remaining": 6
        }
      ]
    }
  },
  "scene": {
    "present_npcs": {
      "added": [
        {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "id": "dock_boy",
          "name": "Dock Boy",
          "notes": "Frightened and wide-eyed, he takes the player's coins and note before bolting toward the bridge.",
          "title": "Messenger"
        }
      ],
      "removed": [
        {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.",
          "id": "innkeeper",
          "name": "Edda",
          "notes": "Startled and defensive, clutching a skillet as the player shoves past her.",
          "title": "Innkeeper at the Crossed Keys"
        }
      ]
    },
    "recently_left": {
      "added": [
        {
          "id": "innkeeper",
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        }
      ]
    },
    "tagline": {
      "from": "A Desperate Flight to the River",
      "to": "A Desperate Message Sent"
    },
    "tags": {
      "added": [
        "stealth",
        "tense_atmosphere"
      ],
      "removed": [
        "combat",
        "chaos"
      ]
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
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Distracted from the player by the violence at the entrance.
- Scarred Tough (Road thug) — Distracted from the player by the violence at the entrance.
- Halden (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
- Matthew Estrada (Traveler) — Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure.
- Edda (Innkeeper at the Crossed Keys) — Retreating toward the kitchen in alarm following the door being breached.

## Last Turn Outcome
Your attempt to intimidate Matthew Estrada is interrupted by the violent splintering of the inn's door as the thugs force their way in.
## Current Turn: 11
=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance. (progress: 1/3)
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery. (progress: 1/3)


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Active Threats
- [IMMEDIATE] Thugs are forcing entry into the inn, creating immediate violence.
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Matthew Estrada** - A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Distracted from the player by the violence at the entrance.
- **Scarred Tough** (Road thug) — Distracted from the player by the violence at the entrance.
- **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
- **Matthew Estrada** (Traveler) — Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure.
- **Edda** (Innkeeper at the Crossed Keys) — Retreating toward the kitchen in alarm following the door being breached.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.
- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.
- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.
## Recent Turns

**T8:** You reach into your pocket, fingers fumbling for the small, cold weight of the **Brass key**, intending to find some side entrance or cellar door that might offer a discrete way into the inn’s belly. You scan the dark timbered wall of the building, searching for a keyhole that might grant you sanctuary, but the heavy oak door is the only entrance in sight, and its massive iron lock is far too large for the delicate tool in your hand.

The **Scarred Tough** is faster than his thin frame suggests. As you turn your attention to the wall, he lunges from your flank, his heavy wooden club whistling through the damp air. You barely twist your body in time to avoid a direct blow to your head, but the edge of the weapon catches your shoulder with a sickening thud. The impact sends a jolt of white-hot pain through your body, making your bruised ribs scream in protest.

"Looking for a way out, little runner?" the **Scarred Tough** snarls, his face inches from yours, his breath smelling of sour wine and aggression. Behind him, the **Bald Tough** steps away from the door, moving to flank you from the other side. You are caught in a tightening vice between the two of them, and the heavy door of the *Crossed Keys Inn* feels less like a sanctuary and more like a wall closing you in.

Inside, through the frosted glass of the entrance, you see **Halden** stand up abruptly. He knocks his chair back with a loud clatter, his eyes darting toward the door as he realizes the confrontation has spilled onto his threshold. He looks ready to intervene, but the sheer bulk of the two men outside makes him hesitate, his hands hovering uncertainly over the edge of the table.


**T9:** You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.


**T10:** You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.

## This Turn's (Turn 11) Result


**Band:** FAIL → The sneak fails. The attempt fails outright — what you tried to do does not happen.




**GM Beat:** The Scarred Tough and Bald Tough burst through the splintered door into the common room.
Surface as event. This is backstage direction — integrate it naturally, not as player-visible narration.




**Momentum FLOOR (-3):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.





**Narration Directive:** Pressure





**Narration Directive:** Location Imperative









=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The common room is in disarray as patrons scramble for cover under tables following the violent splintering of the heavy oak door.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Distracted from the player by the violence at the entrance.
- `tough_b` | **Scarred Tough** (Road thug) — Distracted from the player by the violence at the entrance.
- `halden` | **Halden** (Merchant) — Stands up abruptly inside the inn, looking ready to intervene but hesitating due to the thugs' bulk.
- `matthew_estrada` | **Matthew Estrada** (Traveler) — Remains calm and unyielding during your physical outburst; maintains a steady, soldier-like composure.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Retreating toward the kitchen in alarm following the door being breached.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T10 context)
You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.

## CURRENT TURN 11 NARRATION
You lunge at **Matthew Estrada**, throwing your weight against his chest to knock him backward. You aim to slam him into the heavy wooden shelves behind the bar, hoping to use the impact to daze him and snatch whatever weapon he’s concealed. However, your body betrays you; the jarring movement sends a spike of agony through your bruised ribs, and your footing slips on a patch of spilled ale. Instead of a clean tackle, you merely collide clumsantly with his shoulder, stumbling past him and crashing into a nearby table.

**Matthew Estrada** barely moves from his seat. He absorbs your impact with the practiced stability of a man used to physical chaos, his expression shifting from unreadable to a cold, dangerous edge. He doesn't draw a knife; instead, his hand remains steady on his mug, his eyes tracking your clumsy movement with a look of profound disappointment. You find nothing but empty air and the stinging heat of your own failure as you scramble to regain your balance.

The momentary confusion is instantly drowned out by a deafening roar of splintering timber. The heavy oak door finally gives way under a final, massive blow, bursting inward and showering the floor with jagged shards of wood. The **Scarred Tough** and the **Bald Tough** charge through the wreckage like hounds unleashed, their eyes wild and their weapons raised. They ignore the patrons diving under tables and head straight for the center of the room, their presence turning the common room into a chaotic battlefield of shouting voices and crashing furniture.

As the thugs storm the threshold, the room’s focus shifts entirely to the violent intrusion. The pressure of their advance forces the patrons to scatter, creating a frantic, shifting landscape of legs and overturned chairs. You are caught in the middle of this sudden explosion of movement, the air thick with the smell of sawdust and the sudden, terrifying reality that the sanctuary of the inn has been breached.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
sneak: Tackle the bodyguard into the shelves and pickpocket his coat while he is incapacitated.
## CURRENT TURN 11 NARRATION
You lunge at **Matthew Estrada**, throwing your weight against his chest to knock him backward. You aim to slam him into the heavy wooden shelves behind the bar, hoping to use the impact to daze him and snatch whatever weapon he’s concealed. However, your body betrays you; the jarring movement sends a spike of agony through your bruised ribs, and your footing slips on a patch of spilled ale. Instead of a clean tackle, you merely collide clumsantly with his shoulder, stumbling past him and crashing into a nearby table.

**Matthew Estrada** barely moves from his seat. He absorbs your impact with the practiced stability of a man used to physical chaos, his expression shifting from unreadable to a cold, dangerous edge. He doesn't draw a knife; instead, his hand remains steady on his mug, his eyes tracking your clumsy movement with a look of profound disappointment. You find nothing but empty air and the stinging heat of your own failure as you scramble to regain your balance.

The momentary confusion is instantly drowned out by a deafening roar of splintering timber. The heavy oak door finally gives way under a final, massive blow, bursting inward and showering the floor with jagged shards of wood. The **Scarred Tough** and the **Bald Tough** charge through the wreckage like hounds unleashed, their eyes wild and their weapons raised. They ignore the patrons diving under tables and head straight for the center of the room, their presence turning the common room into a chaotic battlefield of shouting voices and crashing furniture.

As the thugs storm the threshold, the room’s focus shifts entirely to the violent intrusion. The pressure of their advance forces the patrons to scatter, creating a frantic, shifting landscape of legs and overturned chairs. You are caught in the middle of this sudden explosion of movement, the air thick with the smell of sawdust and the sudden, terrifying reality that the sanctuary of the inn has been breached.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "sneak",
  "intent": "Tackle the bodyguard into the shelves and pickpocket his coat while he is incapacitated.",
  "rolled": true,
  "total_ms": 3393.2,
  "tokens_in": 1667,
  "tokens_out": 126,
  "skill": "dexterity",
  "difficulty": "hard",
  "dice": [
    2,
    3
  ],
  "stat_mod": 1,
  "diff_mod": -1,
  "cond_mod": 0,
  "final_total": 5,
  "band": "fail",
  "outcome_summary": "",
  "momentum_before": -3,
  "momentum_after": -3,
  "momentum_delta": 0
}
```

**Raw LLM output:**
```
{
  "intent": "Tackle the bodyguard into the shelves and pickpocket his coat while he is incapacitated.",
  "intent_verb": "sneak",
  "target": "Matthew's bodyguard",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: The bodyguard recovers quickly and retaliates, or the thugs notice the struggle and turn their attention to Aren.]",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "hard"
  }
}
```

### Narration

You lunge at **Matthew Estrada**, throwing your weight against his chest to knock him backward. You aim to slam him into the heavy wooden shelves behind the bar, hoping to use the impact to daze him and snatch whatever weapon he’s concealed. However, your body betrays you; the jarring movement sends a spike of agony through your bruised ribs, and your footing slips on a patch of spilled ale. Instead of a clean tackle, you merely collide clumsantly with his shoulder, stumbling past him and crashing into a nearby table.

**Matthew Estrada** barely moves from his seat. He absorbs your impact with the practiced stability of a man used to physical chaos, his expression shifting from unreadable to a cold, dangerous edge. He doesn't draw a knife; instead, his hand remains steady on his mug, his eyes tracking your clumsy movement with a look of profound disappointment. You find nothing but empty air and the stinging heat of your own failure as you scramble to regain your balance.

The momentary confusion is instantly drowned out by a deafening roar of splintering timber. The heavy oak door finally gives way under a final, massive blow, bursting inward and showering the floor with jagged shards of wood. The **Scarred Tough** and the **Bald Tough** charge through the wreckage like hounds unleashed, their eyes wild and their weapons raised. They ignore the patrons diving under tables and head straight for the center of the room, their presence turning the common room into a chaotic battlefield of shouting voices and crashing furniture.

As the thugs storm the threshold, the room’s focus shifts entirely to the violent intrusion. The pressure of their advance forces the patrons to scatter, creating a frantic, shifting landscape of legs and overturned chairs. You are caught in the middle of this sudden explosion of movement, the air thick with the smell of sawdust and the sudden, terrifying reality that the sanctuary of the inn has been breached.

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "chaos",
    "intrusion"
  ],
  "scene_tagline": "The Inn is Under Siege",
  "location_description": "The common room is now a battlefield of overturned chairs, spilled ale, and jagged wooden shards from the breached door.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Charging through the wreckage with weapons raised, eyes wild."
    },
    {
      "id": "tough_b",
      "notes": "Charging through the wreckage with weapons raised, eyes wild."
    },
    {
      "id": "halden",
      "notes": "Scrambling for cover amidst the sudden violence."
    },
    {
      "id": "matthew_estrada",
      "notes": "Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment."
    },
    {
      "id": "innkeeper",
      "notes": "Retreating toward the kitchen in alarm."
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
  "pc_condition_add": [
    {
      "id": "staggered",
      "label": "staggered",
      "description": "The clumsy collision and slip on spilled ale have left you off-balance and disoriented."
    }
  ],
  "pc_condition_remove": [
    {
      "id": "staggered"
    }
  ]
}
```

### Extract Progress

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "location_description": "The common room is now a battlefield of overturned chairs, spilled ale, and jagged wooden shards from the breached door.",
  "pc_condition_add": [
    {
      "id": "staggered",
      "label": "staggered",
      "description": "The clumsy collision and slip on spilled ale have left you off-balance and disoriented."
    }
  ],
  "pc_condition_remove": [
    {
      "id": "staggered"
    }
  ],
  "scene_tags": [
    "combat",
    "chaos",
    "intrusion"
  ],
  "scene_tagline": "The Inn is Under Siege",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Charging through the wreckage with weapons raised, eyes wild."
    },
    {
      "id": "tough_b",
      "notes": "Charging through the wreckage with weapons raised, eyes wild."
    },
    {
      "id": "halden",
      "notes": "Scrambling for cover amidst the sudden violence."
    },
    {
      "id": "matthew_estrada",
      "notes": "Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment."
    },
    {
      "id": "innkeeper",
      "notes": "Retreating toward the kitchen in alarm."
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

*(none)*

### Context Telemetry

- rules: est=1911t trimmed=False
- narrate: est=7112t trimmed=False
- extract.scene: est=4183t trimmed=False attempts=1
- extract.state: est=4323t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "from": {
      "active_threads": [
        {
          "id": "settle_the_debt",
          "last_offered_turn": 0,
          "progress": 0,
          "promotes": [],
          "state": "active",
          "summary": "Settle the 500-credit debt with Caron.",
          "tags": [
            "debt",
            "caron",
            "obligation"
          ],
          "unlock_if": null,
          "urgency": "normal"
        },
        {
          "id": "deliver_the_ledger",
          "last_offered_turn": 0,
          "progress": 2,
          "promotes": [],
          "state": "active",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "tags": [
            "courier",
            "halden",
            "contract"
          ],
          "unlock_if": null,
          "urgency": "normal"
        },
        {
          "id": "clear_the_road_toughs",
          "last_offered_turn": 0,
          "progress": 1,
          "promotes": [],
          "state": "active",
          "summary": "Deal with the toughs blocking the inn entrance.",
          "tags": [
            "toughs",
            "road",
            "confrontation"
          ],
          "unlock_if": null,
          "urgency": "low"
        },
        {
          "id": "the_toughs_at_the_crossed",
          "last_offered_turn": 3,
          "progress": 1,
          "promotes": [],
          "state": "active",
          "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        }
      ],
      "arc_engagement": 3,
      "completed_threads": [],
      "discovered_truths": [],
      "hidden_truths": [
        "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
        "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
        "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
      ],
      "latent_threads": [
        {
          "id": "the_shadowy_figures_leaning_against",
          "last_offered_turn": 4,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        },
        {
          "id": "matthew_estrada's_calm_reaction_to",
          "last_offered_turn": 10,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        }
      ],
      "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over.",
      "phase": "setup",
      "thematic_question": "What does it cost to settle old debts when new ones keep forming?",
      "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing."
    },
    "to": null
  },
  "compendium": {
    "from": {
      "npcs": {
        "caron": {
          "bio": "A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting their grit and character.",
          "last_seen": {
            "location_id": "marrows_crossing",
            "location_name": "Marrow's Crossing",
            "turn": 2
          },
          "name": "Caron",
          "title": "Old creditor"
        },
        "dock_boy": {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 13
          },
          "name": "Dock Boy",
          "title": "Messenger"
        },
        "halden": {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Halden",
          "title": "Merchant"
        },
        "innkeeper": {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Startled and defensive, clutching a skillet as the player shoves past her.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 12
          },
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        },
        "matthew_estrada": {
          "bio": "A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Matthew Estrada",
          "title": "Traveler"
        },
        "tough_a": {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Bald Tough",
          "title": "Road thug"
        },
        "tough_b": {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Scarred Tough",
          "title": "Road thug"
        }
      }
    },
    "to": null
  },
  "inventory": {
    "from": [
      {
        "aliases": [],
        "amount": 1,
        "id": "iron_dagger",
        "name": "Iron dagger",
        "notes": "Plain crossguard, edge worn from honing. Belt-carried."
      },
      {
        "aliases": [],
        "amount": 2,
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
        "id": "halden_ledger",
        "name": "Halden's ledger",
        "notes": "A parchment ledger belonging to Halden."
      }
    ],
    "to": null
  },
  "location": {
    "from": {
      "description": "A shadowed nook between stacked crates of salt-fish near the muddy riverbank.",
      "id": "marrows_crossing_docks",
      "name": "Marrow's Crossing Docks"
    },
    "to": null
  },
  "meta": {
    "from": {
      "compendium_touch_order": [
        "caron",
        "matthew_estrada",
        "dock_boy"
      ],
      "consecutive_floor_count": 5,
      "game_name": "eval",
      "last_compacted_turn": 10,
      "model": "",
      "pending_gm_beat": {
        "beat_expires_turn": 15,
        "surface_as": "ambient",
        "type": "breathing_room"
      },
      "prior_history": [
        "- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.",
        "- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.",
        "- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.",
        "- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.",
        "- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.",
        "- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.",
        "- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.",
        "- [T8] The Scarred Tough attacked you outside the inn, causing a bruised shoulder while you failed to find a side entrance with the brass key.",
        "- [T9] You attempted to bribe the inn wall with a credit to distract the thugs, but the Bald Tough and Scarred Tough continued their assault as Edda emerged to investigate the noise.",
        "- [T10] You confronted Matthew Estrada at the bar regarding his soldier-like demeanor, but the confrontation was interrupted when the thugs successfully breached the inn's front door."
      ],
      "setting_pack": "eval-pack",
      "turn": 13
    },
    "to": null
  },
  "pc": {
    "from": {
      "allegiance": null,
      "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
      "conditions": [],
      "drive": "",
      "expressed_stances": {},
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
    "to": null
  },
  "scene": {
    "from": {
      "location_entered_turn": 11,
      "present_npcs": [
        {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "id": "dock_boy",
          "name": "Dock Boy",
          "notes": "Frightened and wide-eyed, he takes the player's coins and note before bolting toward the bridge.",
          "title": "Messenger"
        }
      ],
      "recent_events": [
        {
          "id": "halden_contract_active",
          "text": "Halden has entrusted you with his ledger; the delivery to the Crossed Keys Inn is your primary objective.",
          "turn": 3
        },
        {
          "id": "inn_siege_chaos",
          "text": "The Crossed Keys Inn is under siege; thugs have breached the entrance, sending patrons scrambling for cover.",
          "turn": 10
        },
        {
          "id": "matthew_estrada_suspicion",
          "text": "Matthew Estrada watches the room with the calculating gaze of a soldier, his true purpose remains a mystery.",
          "turn": 10
        }
      ],
      "recently_left": [
        {
          "id": "innkeeper",
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        }
      ],
      "recently_left_turns": 0,
      "scene_pressure": [
        {
          "id": "inn_breach_chaos",
          "max_turns": null,
          "text": "Thugs are forcing entry into the inn, creating immediate violence.",
          "turn_added": 10,
          "urgency": "immediate"
        }
      ],
      "tagline": "A Desperate Message Sent",
      "tags": [
        "stealth",
        "tense_atmosphere",
        "escape"
      ],
      "turn_entered": 11,
      "world_state": [
        "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
        "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
        "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
      ]
    },
    "to": null
  },
  "world": {
    "from": {
      "factions": [],
      "locations": []
    },
    "to": null
  }
}
```


---

# TURN 12

**Input:** `I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.`

## User Prompts

### Rules User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder, staggered

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Charging through the wreckage with weapons raised, eyes wild.
- Scarred Tough (Road thug) — Charging through the wreckage with weapons raised, eyes wild.
- Halden (Merchant) — Scrambling for cover amidst the sudden violence.
- Matthew Estrada (Traveler) — Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment.
- Edda (Innkeeper at the Crossed Keys) — Retreating toward the kitchen in alarm.
## Current Turn: 12
=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder, staggered

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The common room is now a battlefield of overturned chairs, spilled ale, and jagged wooden shards from the breached door.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance. (progress: 1/3)
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery. (progress: 1/3)


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Active Threats
- [IMMEDIATE] Thugs are forcing entry into the inn, creating immediate violence.
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Matthew Estrada** - A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Bald Tough** (Road thug) — Charging through the wreckage with weapons raised, eyes wild.
- **Scarred Tough** (Road thug) — Charging through the wreckage with weapons raised, eyes wild.
- **Halden** (Merchant) — Scrambling for cover amidst the sudden violence.
- **Matthew Estrada** (Traveler) — Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment.
- **Edda** (Innkeeper at the Crossed Keys) — Retreating toward the kitchen in alarm.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.
- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.
- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.
## Recent Turns

**T9:** You press your ear against the cold, damp stone of the inn’s wall, the vibration of the heavy wooden door’s latch feeling miles away. Your voice is a desperate, raspy whisper against the masonry: "I have credits. Open up." You reach into your pouch and press a single iron coin against the rough surface of the wall, a futile gesture of bribery directed at a building that cannot hear you.

The wall remains indifferent to your offering. Instead, the heavy thud of a boot against the exterior wood signals that your distraction has failed. The **Scarred Tough** lets out a sharp, mocking bark of laughter that pierces through the stone. "Talking to the rocks now, are we?" he jeers, his voice rising in volume to draw the attention of the patrons inside. The sound of his laughter is followed by a heavy, rhythmic pounding on the door, a violent demand for entry that makes the glass panes rattle in their frames.

Inside, the sudden commotion causes a ripple of movement. **Edda**, the innkeeper, emerges from behind the bar, her face a mask of stern irritation. She marches toward the door, her hands on her hips, shouting something about maintaining order. Her presence provides a momentary distraction; the **Bald Tough** pauses his advance to glance toward the door, his eyes tracking the silhouette of the woman moving through the frosted glass.

The momentary pause in their encirclement gives you a sliver of breathing room. You are still caught between two predators, but the sudden shift in focus toward the door provides a momentary lapse in their aggression. You have a heartbeat of space to breathe, to think, or to move before the tension snaps back to its breaking point.


**T10:** You lunge toward the bar, your fingers clamping onto the thick, calloused wrist of **Matthew Estrada**. You pull him toward you, your voice cracking with a mixture of adrenaline and desperation as you demand to know his true purpose and why he’s eyeing the room with the cold, calculating gaze of a soldier.

**Matthew Estrada** doesn’t flinch. He doesn’t even pull his arm away. Instead, he slowly turns his head to look at you, his expression as unreadable as a stone wall. His eyes are dark and steady, lacking the frantic heat of the thugs outside. "You’ve got a lot of nerve, runner," he says, his voice a low, gravelly rumble that barely carries over the rising din of the inn. He doesn't shake you off, but his grip on his mug tightens, his biceps bunching under the stained leather of his jerkin. "And you’ve got a lot of trouble following you. Mind your business before you find more than just questions."

The momentary standoff at the bar is shattered by a violent crash from the entrance. The heavy oak door of the *Crossed Keys Inn* groans under a massive blow, and the sound of splintering wood echoes through the common room. **Edda** lets out a sharp cry of alarm, retreating toward the kitchen as the door frame begins to buckle under the weight of the assault.

The sudden explosion of violence at the threshold forces a shift in the room’s gravity. The patrons scramble for cover under tables, and the tension that was coiled tightly around you suddenly breaks, redirected toward the door. Even the **Scarred Tough** and the **Bald Tough** are momentarily distracted by the chaos they’ve wrought, their focus shifting from your throat to the prize of the threshold. You are no longer the center of their predatory circle; the inn itself is now under siege.


**T11:** You lunge at **Matthew Estrada**, throwing your weight against his chest to knock him backward. You aim to slam him into the heavy wooden shelves behind the bar, hoping to use the impact to daze him and snatch whatever weapon he’s concealed. However, your body betrays you; the jarring movement sends a spike of agony through your bruised ribs, and your footing slips on a patch of spilled ale. Instead of a clean tackle, you merely collide clumsantly with his shoulder, stumbling past him and crashing into a nearby table.

**Matthew Estrada** barely moves from his seat. He absorbs your impact with the practiced stability of a man used to physical chaos, his expression shifting from unreadable to a cold, dangerous edge. He doesn't draw a knife; instead, his hand remains steady on his mug, his eyes tracking your clumsy movement with a look of profound disappointment. You find nothing but empty air and the stinging heat of your own failure as you scramble to regain your balance.

The momentary confusion is instantly drowned out by a deafening roar of splintering timber. The heavy oak door finally gives way under a final, massive blow, bursting inward and showering the floor with jagged shards of wood. The **Scarred Tough** and the **Bald Tough** charge through the wreckage like hounds unleashed, their eyes wild and their weapons raised. They ignore the patrons diving under tables and head straight for the center of the room, their presence turning the common room into a chaotic battlefield of shouting voices and crashing furniture.

As the thugs storm the threshold, the room’s focus shifts entirely to the violent intrusion. The pressure of their advance forces the patrons to scatter, creating a frantic, shifting landscape of legs and overturned chairs. You are caught in the middle of this sudden explosion of movement, the air thick with the smell of sawdust and the sudden, terrifying reality that the sanctuary of the inn has been breached.

## This Turn's (Turn 12) Result


**Band:** PARTIAL → The escape results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.




**GM Beat:** 
Surface as ambient. This is backstage direction — integrate it naturally, not as player-visible narration.




**Momentum FLOOR (-3):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.





**Narration Directive:** Pressure





**Narration Directive:** Location Imperative









=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The common room is now a battlefield of overturned chairs, spilled ale, and jagged wooden shards from the breached door.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Charging through the wreckage with weapons raised, eyes wild.
- `tough_b` | **Scarred Tough** (Road thug) — Charging through the wreckage with weapons raised, eyes wild.
- `halden` | **Halden** (Merchant) — Scrambling for cover amidst the sudden violence.
- `matthew_estrada` | **Matthew Estrada** (Traveler) — Remains seated and steady, watching the player's failed tackle with a cold, dangerous edge and profound disappointment.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Retreating toward the kitchen in alarm.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T11 context)
You lunge at **Matthew Estrada**, throwing your weight against his chest to knock him backward. You aim to slam him into the heavy wooden shelves behind the bar, hoping to use the impact to daze him and snatch whatever weapon he’s concealed. However, your body betrays you; the jarring movement sends a spike of agony through your bruised ribs, and your footing slips on a patch of spilled ale. Instead of a clean tackle, you merely collide clumsantly with his shoulder, stumbling past him and crashing into a nearby table.

**Matthew Estrada** barely moves from his seat. He absorbs your impact with the practiced stability of a man used to physical chaos, his expression shifting from unreadable to a cold, dangerous edge. He doesn't draw a knife; instead, his hand remains steady on his mug, his eyes tracking your clumsy movement with a look of profound disappointment. You find nothing but empty air and the stinging heat of your own failure as you scramble to regain your balance.

The momentary confusion is instantly drowned out by a deafening roar of splintering timber. The heavy oak door finally gives way under a final, massive blow, bursting inward and showering the floor with jagged shards of wood. The **Scarred Tough** and the **Bald Tough** charge through the wreckage like hounds unleashed, their eyes wild and their weapons raised. They ignore the patrons diving under tables and head straight for the center of the room, their presence turning the common room into a chaotic battlefield of shouting voices and crashing furniture.

As the thugs storm the threshold, the room’s focus shifts entirely to the violent intrusion. The pressure of their advance forces the patrons to scatter, creating a frantic, shifting landscape of legs and overturned chairs. You are caught in the middle of this sudden explosion of movement, the air thick with the smell of sawdust and the sudden, terrifying reality that the sanctuary of the inn has been breached.

## CURRENT TURN 12 NARRATION
You snatch **Halden's ledger** from your coat, the parchment crinkling sharply against your fingers, and bolt toward the rear of the inn. Your breath hitches as your bruised ribs protest the sudden burst of movement, a searing heat radiating through your chest with every frantic stride. You shout for **Halden** to hold on, your voice barely cutting through the cacophony of splintering wood and the startled screams of patrons scrambling for cover.

The chaos behind you is a wall of noise; the **Scarred Tough** and the **Bald Tough** have fully breached the main room, their weapons catching the dim light as they plow through the wreckage of furniture. You burst through the heavy door leading to the kitchen, nearly colliding with a startled **Edda**, who is clutching a heavy iron skillet like a shield. You don't stop to apologize; you shove past her, your shoulder catching the doorframe with a jarring thud that sends a fresh wave of nausea through you.

The back exit of the inn is a narrow, weathered door that leads directly toward the muddy banks of the river. As you heave it open, the cool, damp air of the outskirts hits your face, offering a momentary, stinging relief from the heat and dust of the brawl. You stumble out into the gray light of the docks, your boots skidding on the slick, rain-softened earth.

Behind you, the inn is a hive of violent motion, but the distance you’ve gained provides a vital, if temporary, sanctuary. The sounds of the fight—the shouting, the crashing, the heavy footfalls of the thugs—now feel muffled, separated from you by thick timber walls. You are moving toward the river, away from the immediate carnage, though the heavy breathing in your lungs reminds you that your escape is far from certain.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.
- staggered — The clumsy collision and slip on spilled ale have left you off-balance and disoriented.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.

## player_intent
escape: The player attempts to flee the immediate violence by sprinting toward the river docks while calling for Halden.
## CURRENT TURN 12 NARRATION
You snatch **Halden's ledger** from your coat, the parchment crinkling sharply against your fingers, and bolt toward the rear of the inn. Your breath hitches as your bruised ribs protest the sudden burst of movement, a searing heat radiating through your chest with every frantic stride. You shout for **Halden** to hold on, your voice barely cutting through the cacophony of splintering wood and the startled screams of patrons scrambling for cover.

The chaos behind you is a wall of noise; the **Scarred Tough** and the **Bald Tough** have fully breached the main room, their weapons catching the dim light as they plow through the wreckage of furniture. You burst through the heavy door leading to the kitchen, nearly colliding with a startled **Edda**, who is clutching a heavy iron skillet like a shield. You don't stop to apologize; you shove past her, your shoulder catching the doorframe with a jarring thud that sends a fresh wave of nausea through you.

The back exit of the inn is a narrow, weathered door that leads directly toward the muddy banks of the river. As you heave it open, the cool, damp air of the outskirts hits your face, offering a momentary, stinging relief from the heat and dust of the brawl. You stumble out into the gray light of the docks, your boots skidding on the slick, rain-softened earth.

Behind you, the inn is a hive of violent motion, but the distance you’ve gained provides a vital, if temporary, sanctuary. The sounds of the fight—the shouting, the crashing, the heavy footfalls of the thugs—now feel muffled, separated from you by thick timber walls. You are moving toward the river, away from the immediate carnage, though the heavy breathing in your lungs reminds you that your escape is far from certain.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "escape",
  "intent": "The player attempts to flee the immediate violence by sprinting toward the river docks while calling for Halden.",
  "rolled": true,
  "total_ms": 3271.5,
  "tokens_in": 1621,
  "tokens_out": 120,
  "skill": "dexterity",
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
  "outcome_summary": "",
  "momentum_before": -3,
  "momentum_after": -3,
  "momentum_delta": 0
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to flee the immediate violence by sprinting toward the river docks while calling for Halden.",
  "intent_verb": "escape",
  "target": "the road thugs",
  "stakes": "[Mechanical cost: difficulty increase/condition/harm] + [Narrative consequence: the thugs intercept the player or Halden is left exposed to attack]",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal"
  }
}
```

### Narration

You snatch **Halden's ledger** from your coat, the parchment crinkling sharply against your fingers, and bolt toward the rear of the inn. Your breath hitches as your bruised ribs protest the sudden burst of movement, a searing heat radiating through your chest with every frantic stride. You shout for **Halden** to hold on, your voice barely cutting through the cacophony of splintering wood and the startled screams of patrons scrambling for cover.

The chaos behind you is a wall of noise; the **Scarred Tough** and the **Bald Tough** have fully breached the main room, their weapons catching the dim light as they plow through the wreckage of furniture. You burst through the heavy door leading to the kitchen, nearly colliding with a startled **Edda**, who is clutching a heavy iron skillet like a shield. You don't stop to apologize; you shove past her, your shoulder catching the doorframe with a jarring thud that sends a fresh wave of nausea through you.

The back exit of the inn is a narrow, weathered door that leads directly toward the muddy banks of the river. As you heave it open, the cool, damp air of the outskirts hits your face, offering a momentary, stinging relief from the heat and dust of the brawl. You stumble out into the gray light of the docks, your boots skidding on the slick, rain-softened earth.

Behind you, the inn is a hive of violent motion, but the distance you’ve gained provides a vital, if temporary, sanctuary. The sounds of the fight—the shouting, the crashing, the heavy footfalls of the thugs—now feel muffled, separated from you by thick timber walls. You are moving toward the river, away from the immediate carnage, though the heavy breathing in your lungs reminds you that your escape is far from certain.

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "escape",
    "chaos"
  ],
  "scene_tagline": "A Desperate Flight to the River",
  "location_change": {
    "id": "marrows_crossing_docks",
    "name": "Marrow's Crossing Docks",
    "description": "A narrow, muddy area near the riverbanks under gray, damp skies."
  },
  "location_description": "The ground is slick with rain-softened earth and mud, leading toward the river's edge.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a"
    },
    {
      "id": "tough_b"
    },
    {
      "id": "halden"
    },
    {
      "id": "matthew_estrada"
    }
  ],
  "npc_update": [
    {
      "id": "innkeeper",
      "notes": "Startled and defensive, clutching a skillet as the player shoves past her."
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
      "id": "halden_ledger",
      "name": "Halden's ledger",
      "notes": "A parchment ledger belonging to Halden.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "staggered"
    }
  ]
}
```

### Extract Progress

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [
    {
      "id": "halden_ledger",
      "name": "Halden's ledger",
      "notes": "A parchment ledger belonging to Halden.",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [],
  "inventory_update": [],
  "location_change": {
    "id": "marrows_crossing_docks",
    "name": "Marrow's Crossing Docks",
    "description": "A narrow, muddy area near the riverbanks under gray, damp skies."
  },
  "location_description": "The ground is slick with rain-softened earth and mud, leading toward the river's edge.",
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "staggered"
    }
  ],
  "scene_tags": [
    "combat",
    "escape",
    "chaos"
  ],
  "scene_tagline": "A Desperate Flight to the River",
  "compendium_npc_update": [],
  "npc_add": [],
  "npc_remove": [
    {
      "id": "tough_a"
    },
    {
      "id": "tough_b"
    },
    {
      "id": "halden"
    },
    {
      "id": "matthew_estrada"
    }
  ],
  "npc_update": [
    {
      "id": "innkeeper",
      "notes": "Startled and defensive, clutching a skillet as the player shoves past her."
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

*(none)*

### Context Telemetry

- rules: est=1853t trimmed=False
- narrate: est=7164t trimmed=False
- extract.scene: est=4156t trimmed=False attempts=1
- extract.state: est=4299t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "from": {
      "active_threads": [
        {
          "id": "settle_the_debt",
          "last_offered_turn": 0,
          "progress": 0,
          "promotes": [],
          "state": "active",
          "summary": "Settle the 500-credit debt with Caron.",
          "tags": [
            "debt",
            "caron",
            "obligation"
          ],
          "unlock_if": null,
          "urgency": "normal"
        },
        {
          "id": "deliver_the_ledger",
          "last_offered_turn": 0,
          "progress": 2,
          "promotes": [],
          "state": "active",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "tags": [
            "courier",
            "halden",
            "contract"
          ],
          "unlock_if": null,
          "urgency": "normal"
        },
        {
          "id": "clear_the_road_toughs",
          "last_offered_turn": 0,
          "progress": 1,
          "promotes": [],
          "state": "active",
          "summary": "Deal with the toughs blocking the inn entrance.",
          "tags": [
            "toughs",
            "road",
            "confrontation"
          ],
          "unlock_if": null,
          "urgency": "low"
        },
        {
          "id": "the_toughs_at_the_crossed",
          "last_offered_turn": 3,
          "progress": 1,
          "promotes": [],
          "state": "active",
          "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        }
      ],
      "arc_engagement": 3,
      "completed_threads": [],
      "discovered_truths": [],
      "hidden_truths": [
        "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
        "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
        "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
      ],
      "latent_threads": [
        {
          "id": "the_shadowy_figures_leaning_against",
          "last_offered_turn": 4,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        },
        {
          "id": "matthew_estrada's_calm_reaction_to",
          "last_offered_turn": 10,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        }
      ],
      "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over.",
      "phase": "setup",
      "thematic_question": "What does it cost to settle old debts when new ones keep forming?",
      "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing."
    },
    "to": null
  },
  "compendium": {
    "from": {
      "npcs": {
        "caron": {
          "bio": "A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting their grit and character.",
          "last_seen": {
            "location_id": "marrows_crossing",
            "location_name": "Marrow's Crossing",
            "turn": 2
          },
          "name": "Caron",
          "title": "Old creditor"
        },
        "dock_boy": {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 13
          },
          "name": "Dock Boy",
          "title": "Messenger"
        },
        "halden": {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Halden",
          "title": "Merchant"
        },
        "innkeeper": {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Startled and defensive, clutching a skillet as the player shoves past her.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 12
          },
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        },
        "matthew_estrada": {
          "bio": "A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Matthew Estrada",
          "title": "Traveler"
        },
        "tough_a": {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Bald Tough",
          "title": "Road thug"
        },
        "tough_b": {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Scarred Tough",
          "title": "Road thug"
        }
      }
    },
    "to": null
  },
  "inventory": {
    "from": [
      {
        "aliases": [],
        "amount": 1,
        "id": "iron_dagger",
        "name": "Iron dagger",
        "notes": "Plain crossguard, edge worn from honing. Belt-carried."
      },
      {
        "aliases": [],
        "amount": 2,
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
        "id": "halden_ledger",
        "name": "Halden's ledger",
        "notes": "A parchment ledger belonging to Halden."
      }
    ],
    "to": null
  },
  "location": {
    "from": {
      "description": "A shadowed nook between stacked crates of salt-fish near the muddy riverbank.",
      "id": "marrows_crossing_docks",
      "name": "Marrow's Crossing Docks"
    },
    "to": null
  },
  "meta": {
    "from": {
      "compendium_touch_order": [
        "caron",
        "matthew_estrada",
        "dock_boy"
      ],
      "consecutive_floor_count": 5,
      "game_name": "eval",
      "last_compacted_turn": 10,
      "model": "",
      "pending_gm_beat": {
        "beat_expires_turn": 15,
        "surface_as": "ambient",
        "type": "breathing_room"
      },
      "prior_history": [
        "- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.",
        "- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.",
        "- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.",
        "- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.",
        "- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.",
        "- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.",
        "- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.",
        "- [T8] The Scarred Tough attacked you outside the inn, causing a bruised shoulder while you failed to find a side entrance with the brass key.",
        "- [T9] You attempted to bribe the inn wall with a credit to distract the thugs, but the Bald Tough and Scarred Tough continued their assault as Edda emerged to investigate the noise.",
        "- [T10] You confronted Matthew Estrada at the bar regarding his soldier-like demeanor, but the confrontation was interrupted when the thugs successfully breached the inn's front door."
      ],
      "setting_pack": "eval-pack",
      "turn": 13
    },
    "to": null
  },
  "pc": {
    "from": {
      "allegiance": null,
      "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
      "conditions": [],
      "drive": "",
      "expressed_stances": {},
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
    "to": null
  },
  "scene": {
    "from": {
      "location_entered_turn": 11,
      "present_npcs": [
        {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "id": "dock_boy",
          "name": "Dock Boy",
          "notes": "Frightened and wide-eyed, he takes the player's coins and note before bolting toward the bridge.",
          "title": "Messenger"
        }
      ],
      "recent_events": [
        {
          "id": "halden_contract_active",
          "text": "Halden has entrusted you with his ledger; the delivery to the Crossed Keys Inn is your primary objective.",
          "turn": 3
        },
        {
          "id": "inn_siege_chaos",
          "text": "The Crossed Keys Inn is under siege; thugs have breached the entrance, sending patrons scrambling for cover.",
          "turn": 10
        },
        {
          "id": "matthew_estrada_suspicion",
          "text": "Matthew Estrada watches the room with the calculating gaze of a soldier, his true purpose remains a mystery.",
          "turn": 10
        }
      ],
      "recently_left": [
        {
          "id": "innkeeper",
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        }
      ],
      "recently_left_turns": 0,
      "scene_pressure": [
        {
          "id": "inn_breach_chaos",
          "max_turns": null,
          "text": "Thugs are forcing entry into the inn, creating immediate violence.",
          "turn_added": 10,
          "urgency": "immediate"
        }
      ],
      "tagline": "A Desperate Message Sent",
      "tags": [
        "stealth",
        "tense_atmosphere",
        "escape"
      ],
      "turn_entered": 11,
      "world_state": [
        "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
        "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
        "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
      ]
    },
    "to": null
  },
  "world": {
    "from": {
      "factions": [],
      "locations": []
    },
    "to": null
  }
}
```


---

# TURN 12

**Input:** ``

## User Prompts

### Rules User Prompt
```
(no rules call this turn)
```

### Narrate User Prompt
```
(no narrate call)
```

### Extract Scene User Prompt
```
(not captured)
```

### Extract State User Prompt
```
(not captured)
```

### Extract Progress User Prompt
```
(not captured)
```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```

```

### Narration



### Extract Scene

```json
{}
```

### Extract State

```json
{}
```

### Extract Progress

```json
{}
```

### Applied Deltas

```json
{}
```

### Rejected Deltas

*(none)*

### Suggested Actions

*(none)*

### Context Telemetry

*(no telemetry)*

### State After Turn

*(diff vs previous turn — full snapshot only on first and last turns)*

```json
{
  "arc": {
    "from": {
      "active_threads": [
        {
          "id": "settle_the_debt",
          "last_offered_turn": 0,
          "progress": 0,
          "promotes": [],
          "state": "active",
          "summary": "Settle the 500-credit debt with Caron.",
          "tags": [
            "debt",
            "caron",
            "obligation"
          ],
          "unlock_if": null,
          "urgency": "normal"
        },
        {
          "id": "deliver_the_ledger",
          "last_offered_turn": 0,
          "progress": 2,
          "promotes": [],
          "state": "active",
          "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
          "tags": [
            "courier",
            "halden",
            "contract"
          ],
          "unlock_if": null,
          "urgency": "normal"
        },
        {
          "id": "clear_the_road_toughs",
          "last_offered_turn": 0,
          "progress": 1,
          "promotes": [],
          "state": "active",
          "summary": "Deal with the toughs blocking the inn entrance.",
          "tags": [
            "toughs",
            "road",
            "confrontation"
          ],
          "unlock_if": null,
          "urgency": "low"
        },
        {
          "id": "the_toughs_at_the_crossed",
          "last_offered_turn": 3,
          "progress": 1,
          "promotes": [],
          "state": "active",
          "summary": "The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        }
      ],
      "arc_engagement": 3,
      "completed_threads": [],
      "discovered_truths": [],
      "hidden_truths": [
        "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
        "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
        "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
      ],
      "latent_threads": [
        {
          "id": "the_shadowy_figures_leaning_against",
          "last_offered_turn": 4,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "The shadowy figures leaning against the inn walls present a potential confrontation or social encounter.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        },
        {
          "id": "matthew_estrada's_calm_reaction_to",
          "last_offered_turn": 10,
          "progress": 0,
          "promotes": [],
          "state": "latent",
          "summary": "Matthew Estrada's calm reaction to the violence suggests he may be more than a simple traveler.",
          "tags": [
            "tactical"
          ],
          "unlock_if": null,
          "urgency": "background"
        }
      ],
      "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over.",
      "phase": "setup",
      "thematic_question": "What does it cost to settle old debts when new ones keep forming?",
      "visible_goal": "Clear your debts and deliver the ledger \u2014 two obligations binding you to Marrow's Crossing."
    },
    "to": null
  },
  "compendium": {
    "from": {
      "npcs": {
        "caron": {
          "bio": "A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting their grit and character.",
          "last_seen": {
            "location_id": "marrows_crossing",
            "location_name": "Marrow's Crossing",
            "turn": 2
          },
          "name": "Caron",
          "title": "Old creditor"
        },
        "dock_boy": {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 13
          },
          "name": "Dock Boy",
          "title": "Messenger"
        },
        "halden": {
          "bio": "A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Halden",
          "title": "Merchant"
        },
        "innkeeper": {
          "bio": "Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. Startled and defensive, clutching a skillet as the player shoves past her.",
          "last_seen": {
            "location_id": "marrows_crossing_docks",
            "location_name": "Marrow's Crossing Docks",
            "turn": 12
          },
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        },
        "matthew_estrada": {
          "bio": "A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Matthew Estrada",
          "title": "Traveler"
        },
        "tough_a": {
          "bio": "Hired muscle. No personal stake in this \u2014 he'll back off if the price is right or the fight goes bad.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Bald Tough",
          "title": "Road thug"
        },
        "tough_b": {
          "bio": "Same outfit as the other \u2014 hired by the same person. Quicker to violence; not the brains.",
          "last_seen": {
            "location_id": "marrows_crossing_outskirts",
            "location_name": "Marrow's Crossing Outskirts",
            "turn": 11
          },
          "name": "Scarred Tough",
          "title": "Road thug"
        }
      }
    },
    "to": null
  },
  "inventory": {
    "from": [
      {
        "aliases": [],
        "amount": 1,
        "id": "iron_dagger",
        "name": "Iron dagger",
        "notes": "Plain crossguard, edge worn from honing. Belt-carried."
      },
      {
        "aliases": [],
        "amount": 2,
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
        "id": "halden_ledger",
        "name": "Halden's ledger",
        "notes": "A parchment ledger belonging to Halden."
      }
    ],
    "to": null
  },
  "location": {
    "from": {
      "description": "A shadowed nook between stacked crates of salt-fish near the muddy riverbank.",
      "id": "marrows_crossing_docks",
      "name": "Marrow's Crossing Docks"
    },
    "to": null
  },
  "meta": {
    "from": {
      "compendium_touch_order": [
        "caron",
        "matthew_estrada",
        "dock_boy"
      ],
      "consecutive_floor_count": 5,
      "game_name": "eval",
      "last_compacted_turn": 10,
      "model": "",
      "pending_gm_beat": {
        "beat_expires_turn": 15,
        "surface_as": "ambient",
        "type": "breathing_room"
      },
      "prior_history": [
        "- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.",
        "- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.",
        "- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.",
        "- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.",
        "- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.",
        "- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.",
        "- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.",
        "- [T8] The Scarred Tough attacked you outside the inn, causing a bruised shoulder while you failed to find a side entrance with the brass key.",
        "- [T9] You attempted to bribe the inn wall with a credit to distract the thugs, but the Bald Tough and Scarred Tough continued their assault as Edda emerged to investigate the noise.",
        "- [T10] You confronted Matthew Estrada at the bar regarding his soldier-like demeanor, but the confrontation was interrupted when the thugs successfully breached the inn's front door."
      ],
      "setting_pack": "eval-pack",
      "turn": 13
    },
    "to": null
  },
  "pc": {
    "from": {
      "allegiance": null,
      "bio": "Mid-thirties, broad shoulders, careful with words. Took on a courier contract\nto clear an old debt. Just arrived in Marrow's Crossing with a heavy pack and\na heavier obligation.\n",
      "conditions": [],
      "drive": "",
      "expressed_stances": {},
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
    "to": null
  },
  "scene": {
    "from": {
      "location_entered_turn": 11,
      "present_npcs": [
        {
          "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence.",
          "id": "dock_boy",
          "name": "Dock Boy",
          "notes": "Frightened and wide-eyed, he takes the player's coins and note before bolting toward the bridge.",
          "title": "Messenger"
        }
      ],
      "recent_events": [
        {
          "id": "halden_contract_active",
          "text": "Halden has entrusted you with his ledger; the delivery to the Crossed Keys Inn is your primary objective.",
          "turn": 3
        },
        {
          "id": "inn_siege_chaos",
          "text": "The Crossed Keys Inn is under siege; thugs have breached the entrance, sending patrons scrambling for cover.",
          "turn": 10
        },
        {
          "id": "matthew_estrada_suspicion",
          "text": "Matthew Estrada watches the room with the calculating gaze of a soldier, his true purpose remains a mystery.",
          "turn": 10
        }
      ],
      "recently_left": [
        {
          "id": "innkeeper",
          "name": "Edda",
          "title": "Innkeeper at the Crossed Keys"
        }
      ],
      "recently_left_turns": 0,
      "scene_pressure": [
        {
          "id": "inn_breach_chaos",
          "max_turns": null,
          "text": "Thugs are forcing entry into the inn, creating immediate violence.",
          "turn_added": 10,
          "urgency": "immediate"
        }
      ],
      "tagline": "A Desperate Message Sent",
      "tags": [
        "stealth",
        "tense_atmosphere",
        "escape"
      ],
      "turn_entered": 11,
      "world_state": [
        "Marrow's Crossing is a market town at the confluence of two rivers, known for its mills and the annual river festival.",
        "Iron coin (credits) is the universal currency on the merchant road; barter is acceptable but slower.",
        "The road has been quieter than usual this season \u2014 fewer caravans, more independent runners, more opportunists."
      ]
    },
    "to": null
  },
  "world": {
    "from": {
      "factions": [],
      "locations": []
    },
    "to": null
  }
}
```


---

# TURN 13

**Input:** `I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.`

## User Prompts

### Rules User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## scene
Location: Marrow's Crossing Docks
## Present NPCs (in scene right now)
- Edda (Innkeeper at the Crossed Keys) — Startled and defensive, clutching a skillet as the player shoves past her.
## Current Turn: 13
=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** bruised ribs, bruised shoulder

## Location
Marrow's Crossing Docks (marrows_crossing_docks)
A narrow, muddy area near the riverbanks under gray, damp skies.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Halden's ledger**: A parchment ledger belonging to Halden.


### Campaign Arc
**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.
**Phase:** setup
**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [NORMAL] Settle the 500-credit debt with Caron.
- [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. (progress: 2/3)
- [LOW] Deal with the toughs blocking the inn entrance. (progress: 1/3)
- [BACKGROUND] The toughs at the Crossed Keys Inn present a direct obstacle to completing the delivery. (progress: 1/3)


_(immutable section omitted — see Static Context > Seed State)_

## Scene Context
### Active Threats
- [IMMEDIATE] Thugs are forcing entry into the inn, creating immediate violence.
### Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Matthew Estrada** - A tall, broad-shouldered man with the steady, calculating gaze of a soldier, despite his appearance as a road runner.
- **Caron** - A portly man in his sixties with a merchant's ledger. Recently settled a 500-credit debt with the player, noting thei...
- **Halden** - A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- **Edda** - Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- **Bald Tough** - Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- **Scarred Tough** - Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
### NPCs Present in Scene
- **Edda** (Innkeeper at the Crossed Keys) — Startled and defensive, clutching a skillet as the player shoves past her.
## Prior Turns (Compacted)
- [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.
- [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
- [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
- [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.
- [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.
- [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.
- [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.
- [T8] The Scarred Tough attacked you outside the inn, causing a bruised shoulder while you failed to find a side entrance with the brass key.
- [T9] You attempted to bribe the inn wall with a credit to distract the thugs, but the Bald Tough and Scarred Tough continued their assault as Edda emerged to investigate the noise.
- [T10] You confronted Matthew Estrada at the bar regarding his soldier-like demeanor, but the confrontation was interrupted when the thugs successfully breached the inn's front door.
## Recent Turns

**T11:** You lunge at **Matthew Estrada**, throwing your weight against his chest to knock him backward. You aim to slam him into the heavy wooden shelves behind the bar, hoping to use the impact to daze him and snatch whatever weapon he’s concealed. However, your body betrays you; the jarring movement sends a spike of agony through your bruised ribs, and your footing slips on a patch of spilled ale. Instead of a clean tackle, you merely collide clumsantly with his shoulder, stumbling past him and crashing into a nearby table.

**Matthew Estrada** barely moves from his seat. He absorbs your impact with the practiced stability of a man used to physical chaos, his expression shifting from unreadable to a cold, dangerous edge. He doesn't draw a knife; instead, his hand remains steady on his mug, his eyes tracking your clumsy movement with a look of profound disappointment. You find nothing but empty air and the stinging heat of your own failure as you scramble to regain your balance.

The momentary confusion is instantly drowned out by a deafening roar of splintering timber. The heavy oak door finally gives way under a final, massive blow, bursting inward and showering the floor with jagged shards of wood. The **Scarred Tough** and the **Bald Tough** charge through the wreckage like hounds unleashed, their eyes wild and their weapons raised. They ignore the patrons diving under tables and head straight for the center of the room, their presence turning the common room into a chaotic battlefield of shouting voices and crashing furniture.

As the thugs storm the threshold, the room’s focus shifts entirely to the violent intrusion. The pressure of their advance forces the patrons to scatter, creating a frantic, shifting landscape of legs and overturned chairs. You are caught in the middle of this sudden explosion of movement, the air thick with the smell of sawdust and the sudden, terrifying reality that the sanctuary of the inn has been breached.


**T12:** You snatch **Halden's ledger** from your coat, the parchment crinkling sharply against your fingers, and bolt toward the rear of the inn. Your breath hitches as your bruised ribs protest the sudden burst of movement, a searing heat radiating through your chest with every frantic stride. You shout for **Halden** to hold on, your voice barely cutting through the cacophony of splintering wood and the startled screams of patrons scrambling for cover.

The chaos behind you is a wall of noise; the **Scarred Tough** and the **Bald Tough** have fully breached the main room, their weapons catching the dim light as they plow through the wreckage of furniture. You burst through the heavy door leading to the kitchen, nearly colliding with a startled **Edda**, who is clutching a heavy iron skillet like a shield. You don't stop to apologize; you shove past her, your shoulder catching the doorframe with a jarring thud that sends a fresh wave of nausea through you.

The back exit of the inn is a narrow, weathered door that leads directly toward the muddy banks of the river. As you heave it open, the cool, damp air of the outskirts hits your face, offering a momentary, stinging relief from the heat and dust of the brawl. You stumble out into the gray light of the docks, your boots skidding on the slick, rain-softened earth.

Behind you, the inn is a hive of violent motion, but the distance you’ve gained provides a vital, if temporary, sanctuary. The sounds of the fight—the shouting, the crashing, the heavy footfalls of the thugs—now feel muffled, separated from you by thick timber walls. You are moving toward the river, away from the immediate carnage, though the heavy breathing in your lungs reminds you that your escape is far from certain.

## This Turn's (Turn 13) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



**GM Beat:** 
Surface as ambient. This is backstage direction — integrate it naturally, not as player-visible narration.




**Momentum FLOOR (-3):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.





**Narration Directive:** Pressure












=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_docks` | Marrow's Crossing Docks
A narrow, muddy area near the riverbanks under gray, damp skies.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Startled and defensive, clutching a skillet as the player shoves past her.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T12 context)
You snatch **Halden's ledger** from your coat, the parchment crinkling sharply against your fingers, and bolt toward the rear of the inn. Your breath hitches as your bruised ribs protest the sudden burst of movement, a searing heat radiating through your chest with every frantic stride. You shout for **Halden** to hold on, your voice barely cutting through the cacophony of splintering wood and the startled screams of patrons scrambling for cover.

The chaos behind you is a wall of noise; the **Scarred Tough** and the **Bald Tough** have fully breached the main room, their weapons catching the dim light as they plow through the wreckage of furniture. You burst through the heavy door leading to the kitchen, nearly colliding with a startled **Edda**, who is clutching a heavy iron skillet like a shield. You don't stop to apologize; you shove past her, your shoulder catching the doorframe with a jarring thud that sends a fresh wave of nausea through you.

The back exit of the inn is a narrow, weathered door that leads directly toward the muddy banks of the river. As you heave it open, the cool, damp air of the outskirts hits your face, offering a momentary, stinging relief from the heat and dust of the brawl. You stumble out into the gray light of the docks, your boots skidding on the slick, rain-softened earth.

Behind you, the inn is a hive of violent motion, but the distance you’ve gained provides a vital, if temporary, sanctuary. The sounds of the fight—the shouting, the crashing, the heavy footfalls of the thugs—now feel muffled, separated from you by thick timber walls. You are moving toward the river, away from the immediate carnage, though the heavy breathing in your lungs reminds you that your escape is far from certain.

## CURRENT TURN 13 NARRATION
You stumble away from the inn’s roaring chaos, your legs trembling as you find a shadowed nook between two stacked crates of salt-fish. The damp air of the docks bites at your skin, but the sudden silence of the riverside is a mercy compared to the splintering wood and screams behind you. You collapse against the rough timber of the crates, your breath coming in shallow, ragged hitches that cause your bruised ribs to throb with every intake of air. With trembling fingers, you reach for your **Linen bandages**, pulling a roll free to press against the heat of your shoulder, trying to stem the ache that threatens to pull you under.

The sounds of the brawl at the *Crossed Keys* drift toward you—muffled shouts and the rhythmic thud of heavy boots—but they feel worlds away. You pull a scrap of parchment and a charcoal nub from your gear, your hands shaking so violently that the charcoal snaps against the paper. You scratch out a frantic, disjointed note to **Caron**, warning him that the courier route is compromised and that the thugs are moving through the town with purpose. You don't have the luxury of a proper letter; it is a desperate scrawl of warnings and half-formed thoughts.

A young dock boy, no older than twelve with a face smudged by soot and river silt, skitters past your hiding spot, eyes wide as he scans the muddy path for any sign of the violence spilling out of the inn. You reach out, catching him by the sleeve of his thin tunic. He flinches, his eyes darting to your bloodied bandages and then to the dark shadows of the crates. You press a few coins into his palm—not enough to be a fortune, but enough to make him pause.

"Get this to the merchant near the main bridge," you hiss, thrusting the crumpled note toward him. "Tell him it’s urgent. Go!"

The boy hesitates, his gaze flickering back toward the inn where a sudden, high-pitched scream pierces the gray gloom. Seeing the fear in his eyes, he snatches the note and the coins, turning to bolt down the muddy embankment toward the bridge. You lean your head back against the crate, closing your eyes for a single, fleeting second of stillness, even as the heavy, rhythmic splashing of something moving through the shallow river water nearby keeps your heart hammering against your chest.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- shoulder_bruise — A heavy wooden club struck your shoulder, causing sharp pain and a deep bruise.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `halden_ledger` | Halden's ledger ×1 — A parchment ledger belonging to Halden.

## player_intent
negotiate: The player attempts to tend to their injuries and arrange for a message to be delivered via a dock boy.
## CURRENT TURN 13 NARRATION
You stumble away from the inn’s roaring chaos, your legs trembling as you find a shadowed nook between two stacked crates of salt-fish. The damp air of the docks bites at your skin, but the sudden silence of the riverside is a mercy compared to the splintering wood and screams behind you. You collapse against the rough timber of the crates, your breath coming in shallow, ragged hitches that cause your bruised ribs to throb with every intake of air. With trembling fingers, you reach for your **Linen bandages**, pulling a roll free to press against the heat of your shoulder, trying to stem the ache that threatens to pull you under.

The sounds of the brawl at the *Crossed Keys* drift toward you—muffled shouts and the rhythmic thud of heavy boots—but they feel worlds away. You pull a scrap of parchment and a charcoal nub from your gear, your hands shaking so violently that the charcoal snaps against the paper. You scratch out a frantic, disjointed note to **Caron**, warning him that the courier route is compromised and that the thugs are moving through the town with purpose. You don't have the luxury of a proper letter; it is a desperate scrawl of warnings and half-formed thoughts.

A young dock boy, no older than twelve with a face smudged by soot and river silt, skitters past your hiding spot, eyes wide as he scans the muddy path for any sign of the violence spilling out of the inn. You reach out, catching him by the sleeve of his thin tunic. He flinches, his eyes darting to your bloodied bandages and then to the dark shadows of the crates. You press a few coins into his palm—not enough to be a fortune, but enough to make him pause.

"Get this to the merchant near the main bridge," you hiss, thrusting the crumpled note toward him. "Tell him it’s urgent. Go!"

The boy hesitates, his gaze flickering back toward the inn where a sudden, high-pitched scream pierces the gray gloom. Seeing the fear in his eyes, he snatches the note and the coins, turning to bolt down the muddy embankment toward the bridge. You lean your head back against the crate, closing your eyes for a single, fleeting second of stillness, even as the heavy, rhythmic splashing of something moving through the shallow river water nearby keeps your heart hammering against your chest.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
*(skipped)*

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{
  "intent_verb": "negotiate",
  "intent": "The player attempts to tend to their injuries and arrange for a message to be delivered via a dock boy.",
  "rolled": false,
  "total_ms": 2442.7,
  "tokens_in": 1548,
  "tokens_out": 72
}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to tend to their injuries and arrange for a message to be delivered via a dock boy.",
  "intent_verb": "negotiate",
  "target": "dock boy",
  "stakes": "",
  "check": {
    "required": false
  }
}
```

### Narration

You stumble away from the inn’s roaring chaos, your legs trembling as you find a shadowed nook between two stacked crates of salt-fish. The damp air of the docks bites at your skin, but the sudden silence of the riverside is a mercy compared to the splintering wood and screams behind you. You collapse against the rough timber of the crates, your breath coming in shallow, ragged hitches that cause your bruised ribs to throb with every intake of air. With trembling fingers, you reach for your **Linen bandages**, pulling a roll free to press against the heat of your shoulder, trying to stem the ache that threatens to pull you under.

The sounds of the brawl at the *Crossed Keys* drift toward you—muffled shouts and the rhythmic thud of heavy boots—but they feel worlds away. You pull a scrap of parchment and a charcoal nub from your gear, your hands shaking so violently that the charcoal snaps against the paper. You scratch out a frantic, disjointed note to **Caron**, warning him that the courier route is compromised and that the thugs are moving through the town with purpose. You don't have the luxury of a proper letter; it is a desperate scrawl of warnings and half-formed thoughts.

A young dock boy, no older than twelve with a face smudged by soot and river silt, skitters past your hiding spot, eyes wide as he scans the muddy path for any sign of the violence spilling out of the inn. You reach out, catching him by the sleeve of his thin tunic. He flinches, his eyes darting to your bloodied bandages and then to the dark shadows of the crates. You press a few coins into his palm—not enough to be a fortune, but enough to make him pause.

"Get this to the merchant near the main bridge," you hiss, thrusting the crumpled note toward him. "Tell him it’s urgent. Go!"

The boy hesitates, his gaze flickering back toward the inn where a sudden, high-pitched scream pierces the gray gloom. Seeing the fear in his eyes, he snatches the note and the coins, turning to bolt down the muddy embankment toward the bridge. You lean your head back against the crate, closing your eyes for a single, fleeting second of stillness, even as the heavy, rhythmic splashing of something moving through the shallow river water nearby keeps your heart hammering against your chest.

### Extract Scene

```json
{
  "scene_tags": [
    "stealth",
    "tense_atmosphere",
    "escape"
  ],
  "scene_tagline": "A Desperate Message Sent",
  "location_description": "A shadowed nook between stacked crates of salt-fish near the muddy riverbank.",
  "npc_add": [
    {
      "id": "dock_boy",
      "notes": "Frightened and wide-eyed, he takes the player's coins and note before bolting toward the bridge.",
      "name": "Dock Boy",
      "title": "Messenger",
      "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence."
    }
  ],
  "npc_remove": [
    {
      "id": "innkeeper"
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
  "inventory_remove": [
    {
      "id": "bandages",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "bruised_ribs"
    },
    {
      "id": "shoulder_bruise"
    }
  ]
}
```

### Extract Progress

*(skipped — domain not active this turn)*

### Applied Deltas

```json
{
  "inventory_add": [],
  "inventory_remove": [
    {
      "id": "bandages",
      "amount": 1
    }
  ],
  "inventory_update": [],
  "location_description": "A shadowed nook between stacked crates of salt-fish near the muddy riverbank.",
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "bruised_ribs"
    },
    {
      "id": "shoulder_bruise"
    }
  ],
  "scene_tags": [
    "stealth",
    "tense_atmosphere",
    "escape"
  ],
  "scene_tagline": "A Desperate Message Sent",
  "compendium_npc_update": [],
  "npc_add": [
    {
      "id": "dock_boy",
      "notes": "Frightened and wide-eyed, he takes the player's coins and note before bolting toward the bridge.",
      "name": "Dock Boy",
      "title": "Messenger",
      "bio": "A soot-smudged child working the docks who is easily startled by the ongoing violence."
    }
  ],
  "npc_remove": [
    {
      "id": "innkeeper"
    }
  ],
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

*(none)*

### Context Telemetry

- rules: est=1757t trimmed=False
- narrate: est=6691t trimmed=False
- extract.scene: est=4102t trimmed=False attempts=1
- extract.state: est=4442t trimmed=False attempts=1
- extract.progress: skipped

### State After Turn

```json
{}
```


---
# Deterministic Signals

## Auto-Checker Failures
*(no failures)*

## Metrics
*(no metrics)*

**Scope fallback rate:** 0% (0/17 turns)

## Compaction Features
**4 compaction event(s) observed.** For each event below, the judge must evaluate every capability and write `[OK] / [FAIL] / [NA]` with a one-line justification per capability. The 13 capabilities the compactor system prompt promises:

- `bullet_named_npcs` — Preserve named NPCs (first mention, role, title)
- `bullet_location` — Preserve location of the turn
- `bullet_arc_outcomes` — Preserve arc outcomes (advanced/blocked/failed threads)
- `bullet_key_items` — Preserve key items (gained/lost/consumed)
- `bullet_conditions` — Preserve condition changes
- `bullet_irreversible` — Preserve irreversible player choices
- `bullet_deaths` — Preserve deaths/departures of named characters
- `bullet_mech_consequences` — Preserve mechanical consequences (alliances, enmities, oaths)
- `bullet_culling` — Cull atmospherics, dialogue without consequence, blow-by-blow combat, uneventful travel
- `sanitize_npc_merge` — Sanitize: npc_merge for duplicate compendium NPCs
- `sanitize_inventory` — Sanitize: inventory_remove for duplicate items
- `sanitize_pressure` — Sanitize: pressure_remove for resolved scene pressures
- `sanitize_condition` — Sanitize: condition_remove for cured conditions

### Compaction at turn 3

- prior_history: 0 → 1 bullets (1 added)
- recent_events: 3 → 3 entries

**Bullets added:**

  > - [T1] Aren sat down with Caron at the tavern to discuss the 500-credit debt.

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 5

- prior_history: 1 → 4 bullets (3 added)
- recent_events: 4 → 3 entries

**Bullets added:**

  > - [T2] Aren paid 500 credits to Caron, successfully clearing the debt and earning his respect.
  > - [T3] Aren accepted a contract from Halden to deliver a ledger to the Crossed Keys Inn for 200 credits, receiving a 100-credit advance.
  > - [T4] Aren traveled via the merchant road toward the Crossed Keys Inn, noting an unsettled atmosphere near the entrance.

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 7

- prior_history: 4 → 7 bullets (3 added)
- recent_events: 3 → 3 entries

**Bullets added:**

  > - [T5] Confronted the Bald Tough and Scarred Tough at the inn entrance; the Scarred Tough threatened violence and blocked the doorway.
  > - [T6] Attempted to bribe the toughs with 200 credits, but they rejected the payment and prepared to attack.
  > - [T7] Successfully pushed past the toughs into the Crossed Keys Inn and delivered the merchant seal and Halden's ledger to Halden.

**Applied sanitization actions:**

  *(none recorded)*

### Compaction at turn 9

- prior_history: 7 → 10 bullets (3 added)
- recent_events: 4 → 3 entries

**Bullets added:**

  > - [T8] The Scarred Tough attacked you outside the inn, causing a bruised shoulder while you failed to find a side entrance with the brass key.
  > - [T9] You attempted to bribe the inn wall with a credit to distract the thugs, but the Bald Tough and Scarred Tough continued their assault as Edda emerged to investigate the noise.
  > - [T10] You confronted Matthew Estrada at the bar regarding his soldier-like demeanor, but the confrontation was interrupted when the thugs successfully breached the inn's front door.

**Applied sanitization actions:**

  *(none recorded)*

