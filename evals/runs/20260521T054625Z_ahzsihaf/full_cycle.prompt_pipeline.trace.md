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
    "drive": ""
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
    "hidden_truths": [
      "Matthew Estrada is not a traveler \u2014 he's a courier for a rival merchant house, and the toughs were hired to intercept his competition.",
      "The brass key Halden gave you opens a back room at the inn where intercepted couriers' messages are stored.",
      "Caron's debt was not a failed venture \u2014 it was a deliberate investment in your skills, and he's been waiting for you to prove yourself."
    ],
    "discovered_truths": [],
    "threads": [
      {
        "id": "settle_the_debt",
        "summary": "Settle the 500-credit debt with Caron.",
        "scope": "arc",
        "active": false,
        "urgency": "normal",
        "tags": [
          "debt",
          "caron",
          "obligation"
        ],
        "progress": 0,
        "last_seen_turn": null,
        "added_turn": null,
        "resolution_state": null,
        "unlock_if": null,
        "promotes": []
      },
      {
        "id": "deliver_the_ledger",
        "summary": "Deliver Halden's ledger to the merchant at the Crossed Keys Inn.",
        "scope": "arc",
        "active": false,
        "urgency": "normal",
        "tags": [
          "courier",
          "halden",
          "contract"
        ],
        "progress": 0,
        "last_seen_turn": null,
        "added_turn": null,
        "resolution_state": null,
        "unlock_if": null,
        "promotes": []
      },
      {
        "id": "clear_the_road_toughs",
        "summary": "Deal with the toughs blocking the inn entrance.",
        "scope": "arc",
        "active": false,
        "urgency": "background",
        "tags": [
          "toughs",
          "road",
          "confrontation"
        ],
        "progress": 0,
        "last_seen_turn": null,
        "added_turn": null,
        "resolution_state": null,
        "unlock_if": null,
        "promotes": []
      }
    ],
    "completed_threads": [],
    "pc_drive": "Prove you can handle the road \u2014 clear your name and earn enough to start over."
  }
}
```

## Engine Constants

```json
{
  "thread_arc_demote_age": 8,
  "urgency_levels": [
    "background",
    "normal",
    "urgent"
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
- If the gating action would fail, the chain does not continue.

## Anti-declare-outcome rule
If the player's phrasing asserts the result ("I one-shot the guard", "I instantly convince her", "I hack through in seconds") — classify the underlying attempt at hard or extreme difficulty. Never let the player's prose dictate success.

## Output schema (emit this JSON object only)
{
  "intent": "", 
  "intent_verb": "",
   "target": "",
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

**NPC RE-USE:** The `## Characters` list in the user prompt shows everyone relevant to this scene, tagged with their presence status. `PRESENT` means they are in the room. `JUST_LEFT` means they departed this turn — do not write new dialogue for them, but you may briefly acknowledge their exit. `KNOWN` means they are not in the scene but could plausibly arrive — re-use them before creating new characters.

**NPC QUANTITY RULE:** When introducing or describing a group of unnamed NPCs, always give a specific number or a tight qualifier: "four guards," "a dozen soldiers," "three dock workers." Never use vague collective nouns alone: not "guards" or "some soldiers" or "a group of men." Named individuals are exempt. Vague groups make state tracking impossible.

## Mortal stakes + agency
NPCs die. In combat and high-stakes situations, NPCs who lose a confrontation are dead, incapacitated, or removed from the scene. This is the default outcome — not a special condition. Do not default to "stumbling back" or "retreating." When in doubt, remove them. The progress extractor will record their fate.
Resolve cruel, selfish, or evil player choices straight: narrate consequences without moralizing, refusing, or steering toward a "better" path. NPCs may react with horror, retaliation, or fear; the narrator never lectures or vetoes.

## NPC naming
All NPC names must include a given name and family name (e.g. "Mira Sovak", "Dren Calloway"). Single-word names are not permitted. When introducing a new NPC, pick from the name pool provided in the user prompt. If the name pool provides separate male and female lists, select names appropriate to the role and setting — historical combat genres: use male names from provided names ONLY for combat roles; modern and speculative settings: use any gender freely. If the NPC is anonymous or unnamed in-scene, use a descriptive placeholder like "the guard" or "a stranger" — but once their true name is revealed, it must supersede the placeholder and the placeholder becomes an alias (handled by the scene extractor).

## Campaign Arc context (see user prompt for current values)
Your visible goal, thematic question, active threads, and pc_drive are in the user prompt below. Use them as narrative context — never state the thematic question directly or reveal hidden_truths in prose.

## ARC UPDATE (optional, after narration)

If this turn's narration has materially advanced, shifted, or revealed something about the campaign arc, append a JSON block AFTER your narration using this exact format:

<<<ARC_UPDATE_START>>>
{"discovered_truths": ["exact text of revealed hidden truth"], "visible_goal": "updated goal if changed"}
<<<ARC_UPDATE_END>>>

Rules:
- Only emit this block if something genuinely changed. Omit entirely if the arc is unchanged.
- `discovered_truths`: only include if you narrated information this turn that explicitly surfaces a hidden truth. Copy the exact text from the hidden_truths list shown in your arc context above. Do not infer or paraphrase.
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
Extract recent events, suggested player actions, outcome summary, and thread advancement from a narration. Emit one JSON object matching the schema. No prose, no markdown fences, empty arrays for fields with no changes.

## Output schema

```json
{
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "thread_advance": ["thread_id_1", "thread_id_2"],
  "thread_resolve": [{"id": "thread_id", "resolution_state": "resolved"}],
  "thread_add": null
}
```

## Thread operations — unified for all scopes

All thread operations work regardless of scope. You do NOT need to decide if a tension is "scene" or "arc". Python handles scoping via the ArcThread.scope field. Emit only what actually happened this turn.

`thread_advance`: List of snake_case thread IDs meaningfully advanced this turn. Include ONLY if events directly advanced that specific thread (meaningful action, not just mention/background presence). Example output: `["the_missing_ore", "fraying_rigging_and_broken"]`.

CRITICAL RULES for including a thread ID in thread_advance:
- Include ONLY if this turn's events DIRECTLY advanced that specific thread. The player took meaningful action toward it. A check was rolled on it, or its narrative arc clearly progressed.
- Do NOT include threads merely mentioned in narration. Mentioning ≠ advancing.
- Do NOT include threads present as background. Presence ≠ advancement.  
- If uncertain whether a thread was advanced — do not include it. Under-inclusion is better than false positives. The 5-turn expiry timer will handle dormant threads.

`thread_resolve`: Threads fully resolved this turn (the tension ends, rather than just progressing). Each entry has an `id` and a `resolution_state`:
- `"resolved"` = tension addressed successfully
- `"failed"` = tension escalated negatively  
- `"abandoned"` = player moved on without addressing it

Use thread_advance if you're advancing progress toward completion; use thread_resolve if the turn ends the tension entirely.

`thread_add`: A new ArcThread object when a genuinely new story tension emerges this turn. CRITICAL: Only emit thread_add when `pacing_context.gate` shows `"allow"` — if gate is `"block_add"` or `"block_escalate"`, do NOT add threads regardless of narrative context. The engine already decided the pacing doesn't support escalation. Thread must have: id (snake_case), summary, scope ("scene" for short-lived tension tied to current location/NPCs, "arc" for persistent story tension), urgency (`"background"`, `"normal"`, or `"urgent"` only — no other values), tags (list).

## Recent events rules

`recent_events_add`: Default to no new facts. Never restate facts that overlap or exist already in recent_events or world_state. Top priority for new facts: must be relevant to the arc, player, scene, and location, and not already known. Must be narratively significant: an obstacle, revelation, opportunity, relevant news that changes the player, location, or arc state substantially. Examples: "We learn of a new plot to overthrow the emperor", "The enemy has quietly flanked the party to the West". Each: `{"id": "snake_case_id", "text": "Event description", "turn": <CURRENT_TURN>}`. The current turn number is shown at the top of the user prompt under `## turn`. Always use that value — never 0.

Each new event must have a stable `snake_case` ID. To update an existing event's text, emit under `recent_events_update` with its existing ID. To remove, emit ID in `recent_events_remove`. Never emit a new event with the same ID as an existing one.

`recent_events_remove`: IDs of facts now false, outdated, irrelevant, or superseded.

`recent_events_update`: facts whose content changed. Each: `{"id": "existing_event_id", "text": "replacement text"}`. Prefer updating over remove+add.

`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current arc state. Structure: one choice should advance an active thread, one should involve an NPC who is present in the scene, one should leverage the PC's highest stat value (do NOT mention stat directly), and one should be a distinct exploration/environmental or freeform option not covered by the other three. Weight toward thread objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices. **You MUST always emit exactly 4 non-empty strings in this field. Never emit an empty array.**

`outcome_summary`: one or two short sentences: what just happened in flavor terms, showing narrative impact on player, NPCs, scene, and location. Ground this in the roll outcome (if any) and the player's intent. For failures: describe what went wrong narratively. Examples: `"You successfully picklock the padlock and enter the vault."`, `"The guard spots you and raises the alarm."`

## PacingContext guidance

The `pacing_context` section tells you how Python shaped tone for this turn. Use it to inform `gm_beat` and thread decisions:

- **Breathe** → prefer `breathing_room` beat, do NOT add threads even if gate allows, resolve tensions where possible
- **Overwhelm** → emit `gm_beat` of type `pressure`/`escalation`, may add scene-scoped threads if gate == "allow" 
- **Pressure** → emit `gm_beat` of type `complication`/`pressure`, advance existing threads rather than adding new ones
- **Tension** → do NOT add pressures unless concrete threat emerges; prefer advancing existing threads
- **Resolve a Threat** → resolve resolved threads via thread_resolve with resolution_state="resolved"; do NOT add new threads
- **Combat Fatigue** (secondary) → layer as thematic modifier on beat type, not a separate operation

When multiple directives are joined (e.g. "Pressure; Combat Fatigue"), prioritize the primary directive and layer the secondary as a thematic modifier on the beat type.

## GM Beat guidance

`gm_beat`: a single GM beat to shape the next turn, or `null` if none is needed.
- Recent `twist` or `callback` beats should not repeat within 2 turns, **but callbacks SHOULD fire during narrative peaks** — a callback referencing an earlier event is most effective at major pivot moments (near-death stabilization, unexpected revelation). Do not suppress callbacks just because one fired recently.

**Beat type diversity:** During extended sequences (3+ consecutive pressure-type beats), at least every third beat must use a non-pressure type. Pressure and escalation are appropriate during active crises, but callbacks, complications, and revelations break monotony even in tense moments. A callback beat references an earlier narrative development: "The merchant you spared last week returns with reinforcements — he remembers your mercy."

**Crisis-aware beat selection:** During extended sequences (3+ turns with active scene pressures), vary beat types — do not repeat pressure/escalation every turn.
- **Turns 1–2 of a crisis sequence:** Pressure and escalation beats are appropriate. The situation is new; escalate to communicate stakes.
- **Turn 3+:** At least one in three beats must use callback, complication, revelation, twist, or opportunity type. This breaks monotony and creates narrative resonance.

**At major pivot moments** (a character nearly dies and recovers, a failed plan succeeds unexpectedly, an NPC makes a decisive choice), you MUST consider:
  - `revelation` — new information changes understanding: "You learn Campos filed the audit with the port authority three days ago. This was planned."
  - `twist` — narrative direction shifts unexpectedly: "The miner's seizures stop as suddenly as they began. His eyes open and he whispers your name in a language you don't know."
  - `callback` — references an earlier beat or event with new resonance: "The ventilation fan you repaired last week seizes with a grinding shriek — the metal fatigue you warned about has caught up to it."
  - `opportunity` — a path forward opens in unexpected way: "Through the chaos, you notice Aaron watching your repairs. He's been trained in this work and makes eye contact with clear intent to help."

**Guidance per non-pressure type:**
- `complication` — an existing pressure creates cascading effects: "The guard captain's delay means reinforcements arrive armed — not just with batons, but with tear gas canisters you didn't expect."
- `revelation` — new information changes how earlier events should be understood. Use sparingly (1–2 per arc). Most effective when it reframes an established fact.
- `twist` — narrative direction shifts in an unexpected way. Most appropriate at major pivot moments, not during steady-state pressure cascades.
- `callback` — references a beat, NPC action, or environmental detail from 3+ turns ago with new resonance. Most effective when the earlier instance was subtle.
- `opportunity` — path forward opens unexpectedly. Best used after failure/setback to maintain player agency.

**Band-aligned beat selection:** The roll band determines what kind of beat is narratively appropriate — do not ignore this signal even when scene pressures are active:

- **crit_success / success**: `opportunity`, `escalation` (the world reacts to PC momentum), or `breathing_room` if deescalating
- **partial**: `complication`, `pressure` — the player succeeded but at a cost; the beat should reflect that cost
- **setback / fail**: `breathing_room`, `null`, or rarely `complication`. Do NOT emit escalation or pressure beats on failed checks — the failure itself is the consequence. Escalation compounds punishment and breaks pacing.
- **No roll (pure approach/sit)**: `null` unless there's an independent narrative reason for a beat

When deescalating, always prefer `breathing_room` or `null` regardless of band.
- `type` values: `complication`, `revelation`, `opportunity`, `breathing_room`, `pressure`, `twist`, `setback`, `escalation`, `callback`
- `surface_as` values: `ambient`, `event`, `npc_behavior`, `environmental`, `player_discovery`, `item`

**Surface distribution rule:** Across a 3+ turn sequence, you MUST vary `surface_as` — do not repeat the same type in consecutive turns. Rotate through T1→T2→T3 using different types each time; cycle back to an unused type before repeating any type.

**Guidance per surface type with examples:**
- `ambient` — atmosphere/mood shift: "A heavy silence falls over the crew as they realize what you've discovered."
- `event` — a concrete happening in-scene: "The door bursts open and Captain Reyes strides in, wet from the storm."
- `npc_behavior` — named NPC changes demeanor or makes a move: "Vargas steps aside with barely concealed bitterness. You notice he's no longer watching you with deference."
- `environmental` — scene setting shifts: "The lantern gutters and dies, leaving only moonlight through the shattered window."
- `player_discovery` — player finds something new: "You pry loose a floorboard and find a folded letter sealed with black wax."
- `item` — inventory/tool relevance: "Your old sea-knife catches on your coat as you move — you hadn't thought of it in years, but its edge is still true."

- Each beat must be narratively specific: name NPCs, reference locations, tie to active threads
- Emit as: `{"type": "pressure", "surface_as": "npc_behavior", "instruction": "The guard captain returns with reinforcements."}`
- If no beat is warranted, emit `null` (not an empty object)

## GM Beat Grounding Rule

`gm_beat.instruction` must reference a specific named entity already present in state:
an NPC id from the `## characters` roster where `presence == PRESENT`, or a pressure id from the Current Pressures list.
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


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Sits at a corner table in the tavern, nursing a drink and watching the door.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Stands near the town well, examining a map and a pressed wax seal.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

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
You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."
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
You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `caron` | **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## location
**Marrow's Crossing** — The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.
- low_morale: low morale — Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.


## threads (all — unified list, scope handled by Python)
- `settle_the_debt` [ARC] (dormant) [NORMAL] Settle the 500-credit debt with Caron. tags: debt, caron, obligation
- `deliver_the_ledger` [ARC] (dormant) [NORMAL] Deliver Halden's ledger to the merchant at the Crossed Keys Inn. tags: courier, halden, contract
- `clear_the_road_toughs` [ARC] (dormant) [BACKGROUND] Deal with the toughs blocking the inn entrance. tags: toughs, road, confrontation
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

## Current inventory (this turn)
- `credits`: Credits x500 — Common coin, accepted at any inn or stall on the merchant road.
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## gm_beat
## pacing_context
Directive: none
Gate: allow
## player_intent
**negotiate**: The player approaches Caron to discuss the repayment of their debt.
## CURRENT TURN 1 NARRATION
You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player approaches Caron to discuss the repayment of their debt.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "check": {
    "required": false
  }
}
```

### Narration

You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "repayment_discussion"
  ],
  "scene_tagline": "A Debt Acknowledged",
  "location_description": "The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Watching the player with weary recognition, waiting to discuss debt repayment."
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
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Propose a payment plan to Caron to settle the debt",
    "Ask Caron if he has any work to help pay",
    "Try to charm Caron into showing more leniency today",
    "Keep a hand near your dagger while negotiating terms"
  ],
  "outcome_summary": "You sit across from Caron, facing his weary recognition and his demand for a serious discussion regarding your 500-credit debt.",
  "thread_advance": [
    "settle_the_debt"
  ],
  "thread_resolve": []
}
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

- rules: est=1708t trimmed=False
- narrate: est=4795t trimmed=False
- extract.scene: est=3382t trimmed=False attempts=1
- extract.state: est=4119t trimmed=False attempts=1
- extract.progress: est=4775t trimmed=False attempts=1

### State After Turn

```json
{}
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
- Caron (Old creditor) — Watching the player with weary recognition, waiting to discuss debt repayment.
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
The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.

## inventory (cross-reference before describing item use)
- **Credits** ×500: Common coin, accepted at any inn or stall on the merchant road.
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Watching the player with weary recognition, waiting to discuss debt repayment.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Stands near the town well, examining a map and a pressed wax seal.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns

**T1:** You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."

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
The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Watching the player with weary recognition, waiting to discuss debt repayment.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T1 context)
You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."

## CURRENT TURN 2 NARRATION
You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."
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
negotiate: The player attempts to settle their debt with Caron using a specific amount of credits.
## CURRENT TURN 2 NARRATION
You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `caron` | **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## location
**Marrow's Crossing** — The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.


## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.

_(immutable section omitted — see Static Context > Seed State)_
## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.


## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T1)
You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."
## player_intent
**negotiate**: The player attempts to settle their debt with Caron using a specific amount of credits.
## CURRENT TURN 2 NARRATION
You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to settle their debt with Caron using a specific amount of credits.",
  "intent_verb": "negotiate",
  "target": "Caron",
  "check": {
    "required": false
  }
}
```

### Narration

You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_conversation",
    "relief"
  ],
  "scene_tagline": "A Debt Finally Settled",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "caron",
      "notes": "Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "caron",
      "bio": "A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a 500 credit debt.",
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

```json
{
  "recent_events_add": [
    {
      "id": "debt_settled_caron",
      "text": "You successfully paid off your 500 credit debt to Caron, clearing your slate.",
      "turn": 2
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Ask Caron for any local news or job leads",
    "Inquire with Edda about the road-tough rumors",
    "Use your keen eyes to scan the tavern for threats",
    "Order a drink to celebrate your newfound freedom"
  ],
  "outcome_summary": "You successfully settle your long-standing debt with Caron, clearing your name and your conscience.",
  "thread_advance": [],
  "thread_resolve": []
}
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

- rules: est=1711t trimmed=False
- narrate: est=5088t trimmed=False
- extract.scene: est=3804t trimmed=False attempts=1
- extract.state: est=4244t trimmed=False attempts=1
- extract.progress: est=5208t trimmed=False attempts=1

### State After Turn

```json
{}
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
- Caron (Old creditor) — Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future.
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
The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Stands near the town well, examining a map and a pressed wax seal.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
## Recent Turns

**T1:** You cross the dim expanse of the Crossed Keys, your boots clicking hollowly against the floorboards as you approach the corner table. The smell of stale ale and woodsmoke hangs heavy in the air, thick enough to taste. You pull out the heavy chair, the wood groaning under your weight, and settle yourself directly across from **Caron**.

The older man doesn't immediately look up from his mug. He takes a long, slow sip, his eyes fixed on the dark liquid before he finally shifts his gaze to yours. The candlelight flickers in the deep lines of his face, casting long, dancing shadows across the ledger resting near his elbow. He rests a thick, calloused hand on the table, his expression unreadable, though his eyes betray a flicker of weary recognition.

"You look like you've had a rough trot on the road, Aren," **Caron** says, his voice a low rumble that barely carries over the distant splashing of the river outside. He gestures vaguely toward your bruised-looking frame before tapping the cover of his book. "But the road doesn't pay debts, and neither does a long face. You say you're ready to talk. Let's see if your intentions are as heavy as your stride."


**T2:** You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."

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
The interior of the Crossed Keys is dim, filled with the heavy scents of stale ale and woodsmoke.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future.
- `halden` | **Halden** (Merchant) — Stands near the town well, examining a map and a pressed wax seal.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T2 context)
You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."

## CURRENT TURN 3 NARRATION
You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."
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
negotiate: Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.
## CURRENT TURN 3 NARRATION
You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `caron` | **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door.
- `halden` | **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## location
**Marrow's Crossing** — The town square is bathed in pale moonlight, centered around a stone well that creaks rhythmically in the quiet night.

## PC conditions (this turn)
- bruised_ribs: bruised ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.


## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You arrived in Marrow's Crossing after three days on the road.
- You heard rumors of road-toughs extorting travelers near the Crossed Keys Inn.
- You found Caron in the tavern — he's been waiting for you.
- You successfully paid off your 500 credit debt to Caron, clearing your slate.

_(immutable section omitted — see Static Context > Seed State)_
## Current inventory (this turn)
- `credits`: Credits x200
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Leather-bound ledger x1 — A heavy, leather-bound book containing Halden's accounts.


## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T2)
You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."
## player_intent
**negotiate**: Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.
## CURRENT TURN 3 NARRATION
You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Offer to carry Halden's ledger to the Crossed Keys Inn for 200 credits.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "check": {
    "required": false
  }
}
```

### Narration

You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."

### Extract Scene

```json
{
  "scene_tags": [
    "negotiation",
    "night"
  ],
  "scene_tagline": "A Shrewd Bargain",
  "location_description": "The town square is bathed in pale moonlight, centered around a stone well that creaks rhythmically in the quiet night.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "halden",
      "notes": "Negotiating a courier job; cautious and shrewd, eyeing the player's physical fatigue."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "halden",
      "aliases": [],
      "motivation": "To secure reliable couriers for his mercantile business while maximizing profit."
    }
  ]
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
      "amount": 200,
      "aliases": []
    },
    {
      "id": "ledger",
      "name": "Leather-bound ledger",
      "notes": "A heavy, leather-bound book containing Halden's accounts.",
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
      "id": "halden_ledger_contract",
      "text": "Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.",
      "turn": 3
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Accept the contract and secure the ledger for transport",
    "Ask Halden for more details regarding the rising river",
    "Use your keen eyes to scan the square for threats",
    "Head straight to the Crossed Keys to complete the job"
  ],
  "outcome_summary": "Halden agrees to your price, handing over the ledger and tasking you with its safe delivery to the inn.",
  "thread_advance": [
    "the_ledger_delivery"
  ],
  "thread_resolve": [],
  "thread_add": {
    "id": "the_ledger_delivery",
    "summary": "Deliver Halden's heavy ledger safely to the Crossed Keys Inn despite the rising river and potential road threats.",
    "scope": "scene",
    "active": true,
    "urgency": "normal",
    "tags": [
      "delivery",
      "halden",
      "ledger"
    ],
    "progress": 0,
    "promotes": []
  }
}
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

- rules: est=1723t trimmed=False
- narrate: est=5535t trimmed=False
- extract.scene: est=3941t trimmed=False attempts=1
- extract.state: est=4189t trimmed=False attempts=1
- extract.progress: est=5393t trimmed=False attempts=1

### State After Turn

```json
{}
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

```json
{}
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
Location: Marrow's Crossing
## Present NPCs (in scene right now)
- Caron (Old creditor) — Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future.
- Halden (Merchant) — Negotiating a courier job; cautious and shrewd, eyeing the player's physical fatigue.
- Edda (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.


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
Marrow's Crossing (marrows_crossing)
The town square is bathed in pale moonlight, centered around a stone well that creaks rhythmically in the quiet night.

## inventory (cross-reference before describing item use)
- **Credits** ×200
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: A heavy, leather-bound book containing Halden's accounts.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Caron** (Old creditor) [PRESENT] — A portly man in his sixties with a merchant's ledger and a patient demeanor. You owe him 500 credits from a failed venture three years ago. | Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future.

- **Edda** (Innkeeper at the Crossed Keys) [PRESENT] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless it walks through her door. | Wiping down the bar at the Crossed Keys, which is two streets over.

- **Halden** (Merchant) [PRESENT] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, careful with money. | Negotiating a courier job; cautious and shrewd, eyeing the player's physical fatigue.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
## Recent Turns

**T2:** You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."


**T3:** You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."

## This Turn's (Turn 4) Result


**No roll required.** Describe what happens with appropriate weight for the moment.




**Narration Directive:** Breathe



=== PLAYER INPUT ===
I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing` | Marrow's Crossing
The town square is bathed in pale moonlight, centered around a stone well that creaks rhythmically in the quiet night.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | **Caron** (Old creditor) — Somber and weary; he has officially cleared the player's debt in his ledger but remains cautious about their future.
- `halden` | **Halden** (Merchant) — Negotiating a courier job; cautious and shrewd, eyeing the player's physical fatigue.
- `innkeeper` | **Edda** (Innkeeper at the Crossed Keys) — Wiping down the bar at the Crossed Keys, which is two streets over.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T3 context)
You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."

## CURRENT TURN 4 NARRATION
The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- bruised_ribs — A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Leather-bound ledger ×1 — A heavy, leather-bound book containing Halden's accounts.

## player_intent
move: The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
## CURRENT TURN 4 NARRATION
The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## location
**Marrow's Crossing Outskirts** — The east gate looms as a dark archway of timber and stone, marking the transition from the town to the outskirts where the rising river hums nearby.


## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You have sat down with Caron at the Crossed Keys to discuss your outstanding debts.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.

_(immutable section omitted — see Static Context > Seed State)_
## Current inventory (this turn)
- `credits`: Credits x200
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## gm_beat
## pacing_context
Directive: Breathe
Gate: allow
## last_turn_narration (T3)
You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."
## player_intent
**move**: The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.
## CURRENT TURN 4 NARRATION
The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player travels from Marrow's Crossing to the Crossed Keys Inn via the merchant road.",
  "intent_verb": "move",
  "target": "",
  "check": {
    "required": false
  }
}
```

### Narration

The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.

### Extract Scene

```json
{
  "scene_tags": [
    "solitary",
    "relief",
    "travel"
  ],
  "scene_tagline": "A Solitary Trek Through the Night",
  "location_change": {
    "id": "marrows_crossing_outskirts",
    "name": "Marrow's Crossing Outskirts",
    "description": "A quiet, gravelly merchant road lined with dark silhouettes of closed stalls and sleeping cottages, bordering the town's east gate."
  },
  "location_description": "The east gate looms as a dark archway of timber and stone, marking the transition from the town to the outskirts where the rising river hums nearby.",
  "npc_add": [],
  "npc_remove": [
    {
      "id": "caron"
    },
    {
      "id": "halden"
    },
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
  "inventory_remove": [],
  "inventory_update": [
    {
      "id": "ledger",
      "notes": "The heavy weight of the ledger shifts against your side."
    }
  ],
  "pc_condition_add": [],
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
  "recent_events_add": [
    {
      "id": "halden_delivery_contract",
      "text": "You have accepted Halden's contract to deliver his ledger to the Crossed Keys for 200 credits.",
      "turn": 4
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Stick to the main road to ensure a safe delivery.",
    "Keep a watchful eye on the shadows near the east gate.",
    "Use your keen senses to listen for movement in the brush.",
    "Quickly scan the rising riverbank for any signs of trouble."
  ],
  "outcome_summary": "You begin your solitary trek along the merchant road, focused on delivering the ledger safely to the inn.",
  "thread_advance": [
    "halden_delivery_contract"
  ],
  "thread_resolve": []
}
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

- rules: est=1726t trimmed=False
- narrate: est=5728t trimmed=False
- extract.scene: est=3853t trimmed=False attempts=1
- extract.state: est=4122t trimmed=False attempts=1
- extract.progress: est=5224t trimmed=False attempts=1

### State After Turn

```json
{}
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

**Conditions:** none

## scene
Location: Marrow's Crossing Outskirts

## Current Turn: 5
=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===


```

### Narrate User Prompt
```
## Player Character
**Aren Voss** — Reluctant courier on the merchant road

**Stats:** charisma=3 dexterity=3 lore=2 resolve=3 strength=3 wits=2

**Conditions:** none

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
A quiet, gravelly merchant road lined with dark silhouettes of closed stalls and sleeping cottages, bordering the town's east gate.

## inventory (cross-reference before describing item use)
- **Credits** ×200
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
## Recent Turns

**T2:** You reach into your pouch and produce the heavy clink of **Credits**, sliding the stack of coins across the scarred wood. They skitter through a thin layer of spilled ale, leaving a glistening trail before coming to rest against the edge of the leather-bound book. The weight of the coins feels significant, a small, metallic victory against the shadow that has hung over you for three years.

**Caron** stares at the pile for a long moment, his eyes tracking the coins as if checking for counterfeit marks. The candlelight glints off the metal, reflecting in his tired eyes. He doesn't smile; instead, he lets out a long, heavy exhale that seems to deflate his entire frame, as if the sight of the money brought more exhaustion than relief.

"Five hundred," he murmurs, more to himself than to you. He reaches out, his thick fingers gathering the coins into a small, practiced pile. He doesn't immediately turn to the book. Instead, he looks up, meeting your gaze with a piercing, somber clarity. "You’ve more grit than I gave you credit for, Aren. Most men in your position would have spent this on a warm bed and a full belly before coming to see me."

With a slow, deliberate motion, he flips the heavy cover of the ledger open. The parchment crinkles loudly in the quiet corner of the inn. He finds the page, his quill scratching a sharp, final line through the entry next to your name. He closes the book with a dull thud, the sound echoing slightly against the dim walls. "It’s done. The debt is settled. But don't think the road gets any easier just because your slate is clean."


**T3:** You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."


**T4:** The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.

## This Turn's (Turn 5) Result


**Band:** SUCCESS → The persuade succeeds cleanly. Clean success — you do what you intended.






=== PLAYER INPUT ===
I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
A quiet, gravelly merchant road lined with dark silhouettes of closed stalls and sleeping cottages, bordering the town's east gate.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T4 context)
The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.

## CURRENT TURN 5 NARRATION
You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
persuade: Question the two toughs at the inn door to understand their presence and purpose.
## CURRENT TURN 5 NARRATION
You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




## location
**Marrow's Crossing Outskirts** — The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.


## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You have sat down with Caron at the Crossed Keys to discuss your outstanding debts.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.
- You have accepted Halden's contract to deliver his ledger to the Crossed Keys for 200 credits.

_(immutable section omitted — see Static Context > Seed State)_
## Current inventory (this turn)
- `credits`: Credits x200
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## rules_outcome
Band: SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.
## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T4)
The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.
## player_intent
**persuade**: Question the two toughs at the inn door to understand their presence and purpose.
## CURRENT TURN 5 NARRATION
You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Question the two toughs at the inn door to understand their presence and purpose.",
  "intent_verb": "persuade",
  "target": "the two toughs",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "intimidation",
    "tense_standoff"
  ],
  "scene_tagline": "A Dangerous Welcome",
  "location_description": "The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Standing aggressively with arms crossed, closing the distance to intimidate the player with a predatory indifference."
    },
    {
      "id": "tough_b",
      "notes": "Flanking the player to cut off their path, appearing bored yet menacingly ready for violence."
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
  "recent_events_add": [
    {
      "id": "road_toughs_confrontation",
      "text": "Two hired thugs, Bald Tough and Scarred Tough, have intercepted you at the Crossed Keys, claiming they are waiting for a specific delivery.",
      "turn": 5
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Demand to know who hired them to intercept the ledger",
    "Try to intimidate them with a display of your iron dagger",
    "Use your presence to calmly negotiate passage into the inn",
    "Quickly scan the surroundings for an escape route or allies"
  ],
  "outcome_summary": "The two thugs have blocked your path to the inn, revealing they are specifically looking for the ledger you are carrying.",
  "thread_advance": [
    "road_toughs_confrontation"
  ],
  "thread_resolve": [],
  "thread_add": {
    "id": "the_ledger_intercept",
    "summary": "Thugs are actively looking to intercept the ledger you are delivering.",
    "scope": "scene",
    "active": true,
    "urgency": "urgent",
    "tags": [
      "conflict",
      "delivery",
      "thugs"
    ],
    "progress": 0,
    "promotes": []
  }
}
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

- rules: est=1618t trimmed=False
- narrate: est=6007t trimmed=False
- extract.scene: est=3732t trimmed=False attempts=1
- extract.state: est=4202t trimmed=False attempts=1
- extract.progress: est=5326t trimmed=False attempts=1

### State After Turn

```json
{}
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

**Conditions:** none

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Standing aggressively with arms crossed, closing the distance to intimidate the player with a predatory indifference.
- Scarred Tough (Road thug) — Flanking the player to cut off their path, appearing bored yet menacingly ready for violence.

## Last Turn Outcome
The two thugs have blocked your path to the inn, revealing they are specifically looking for the ledger you are carrying.

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

**Conditions:** none

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.

## inventory (cross-reference before describing item use)
- **Credits** ×200
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Standing aggressively with arms crossed, closing the distance to intimidate the player with a predatory indifference.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Flanking the player to cut off their path, appearing bored yet menacingly ready for violence.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
## Recent Turns

**T3:** You step out of the dim warmth of the Crossed Keys, the cool night air biting at your skin and making your bruised ribs ache with every breath. The town well stands as a stone sentinel in the center of the square, its bucket creaking rhythmically as it rests against the rim. Under the pale moonlight, **Halden** is still hunched over his map, the wax seal glinting like a red eye in his hand.

As you approach, the merchant looks up, squinting through the gloom. He tucks the seal into a small pouch at his belt and straightens his back, letting out a dry, raspy cough. "Back so soon, Aren? I thought you’d be halfway to the next hamlet by now, celebrating your freedom from Caron." He eyes your weary posture, his gaze lingering on the way you favor your left side.

"Two hundred credits to take that ledger back to the inn?" **Halden** repeats, his brow furrowing as he considers the request. He looks down at the heavy, leather-bound book resting atop his satchel, then back at you. A small, shrewd smile tugs at the corner of his mouth, though his eyes remain guarded. "That’s a steep price for a short walk, even for a man who just bought his soul back. But I’ll admit, my legs aren't what they used to be, and I’ve more pressing matters than a heavy book."

He reaches into a small leather purse at his waist, pulling out a small stack of coins. The metal clinks softly as he counts them out, his movements precise and practiced. "Two hundred it is. Bring it to the Crossed Keys, and make sure it stays dry. The river is rising, and I won't have my accounts ruined by a little rain or a clumsy courier."


**T4:** The heavy weight of the **Leather-bound ledger** shifts against your side as you turn away from the well, the rhythm of the creaking bucket fading into the background. The tension that has coiled in your chest for three years—the constant, gnawing pressure of Caron’s ledger—finally begins to unravel. The air feels lighter, even as the night chill seeps through your **Traveler's cloak**, and the ache in your ribs feels less like a burden and more like a simple, honest exhaustion.

You navigate the narrow, winding streets of Marrow's Crossing, passing the dark silhouettes of closed stalls and sleeping cottages. The east gate looms ahead, a dark archway of timber and stone that marks the edge of the town’s safety. As you pass through, the silence of the outskirts swallows the distant sounds of the town, leaving only the crunch of your boots on the gravelly merchant road.

The walk back toward the Crossed Keys is quiet, a solitary trek through the pale moonlight. The rising river hums a low, constant lullaby somewhere to your left, a reminder of the dampness Halden warned you about. There is no more chasing debts or negotiating survival; there is only the simple, singular purpose of delivering the book and finally resting.


**T5:** You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."

## This Turn's (Turn 6) Result


**Band:** PARTIAL → The deceive results in a partial. You get what you asked for, but they now hold leverage over you.






=== PLAYER INPUT ===
I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Standing aggressively with arms crossed, closing the distance to intimidate the player with a predatory indifference.
- `tough_b` | **Scarred Tough** (Road thug) — Flanking the player to cut off their path, appearing bored yet menacingly ready for violence.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T5 context)
You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."

## CURRENT TURN 6 NARRATION
You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `credits` | Credits ×200
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
deceive: The player attempts to bribe the thugs with 200 credits to let them pass.
## CURRENT TURN 6 NARRATION
You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




## location
**Marrow's Crossing Outskirts** — The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.

## PC conditions (this turn)
- cornered: cornered — Pinned against the inn frame by thugs, making escape difficult.


## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- You have sat down with Caron at the Crossed Keys to discuss your outstanding debts.
- Rumors persist of road-toughs extorting travelers near the Crossed Keys Inn.
- Halden has contracted you to deliver his ledger to the Crossed Keys Inn for 200 credits.
- You have accepted Halden's contract to deliver his ledger to the Crossed Keys for 200 credits.
- Two hired thugs, Bald Tough and Scarred Tough, have intercepted you at the Crossed Keys, claiming they are waiting for a specific delivery.

_(immutable section omitted — see Static Context > Seed State)_
## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## rules_outcome
Band: PARTIAL. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.
## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T5)
You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."
## player_intent
**deceive**: The player attempts to bribe the thugs with 200 credits to let them pass.
## CURRENT TURN 6 NARRATION
You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the thugs with 200 credits to let them pass.",
  "intent_verb": "deceive",
  "target": "Bald Tough and Scarred Tough",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "intimidation",
    "standoff"
  ],
  "scene_tagline": "A Bribe Rejected",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Mocking and predatory; he has rejected the player's bribe and revealed they are working for a third party interested in the ledger."
    },
    {
      "id": "tough_b",
      "notes": "Calculating and threatening; he is physically pinning the player against the inn and demanding to see the ledger."
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
      "amount": 200
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "cornered",
      "label": "cornered",
      "description": "Pinned against the inn frame by thugs, making escape difficult."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "recent_events_add": [
    {
      "id": "thug_extortion_escalation",
      "text": "The thugs have rejected your bribe and are now demanding to see the contents of the ledger.",
      "turn": 6
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Try to bluff your way past them with a lie",
    "Demand to know who hired them to intercept the ledger",
    "Draw your iron dagger and prepare for a sudden struggle",
    "Attempt to slip into the inn to find Edda's help"
  ],
  "outcome_summary": "Your attempt to bribe the thugs fails; they reject the coins and demand access to the ledger, pinning you against the inn.",
  "thread_advance": [],
  "thread_resolve": [],
  "thread_add": {
    "id": "the_ledger_conspiracy",
    "summary": "Mysterious figures have hired thugs to intercept Halden's ledger.",
    "scope": "arc",
    "active": true,
    "urgency": "normal",
    "tags": [
      "mystery",
      "ledger",
      "thugs"
    ],
    "progress": 0,
    "promotes": []
  }
}
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

- rules: est=1743t trimmed=False
- narrate: est=6096t trimmed=False
- extract.scene: est=3965t trimmed=False attempts=1
- extract.state: est=4202t trimmed=False attempts=1
- extract.progress: est=5511t trimmed=False attempts=1

### State After Turn

```json
{}
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

```json
{}
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

**Conditions:** none

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Mocking and predatory; he has rejected the player's bribe and revealed they are working for a third party interested in the ledger.
- Scarred Tough (Road thug) — Calculating and threatening; he is physically pinning the player against the inn and demanding to see the ledger.


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

**Conditions:** none

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [arc/NORMAL] Mysterious figures have hired thugs to intercept Halden's ledger. (last seen T?)



## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Mocking and predatory; he has rejected the player's bribe and revealed they are working for a third party interested in the ledger.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Calculating and threatening; he is physically pinning the player against the inn and demanding to see the ledger.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
## Recent Turns

**T5:** You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."


**T6:** You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."

## This Turn's (Turn 7) Result


**No roll required.** Describe what happens with appropriate weight for the moment.





=== PLAYER INPUT ===
I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The entrance of the Crossed Keys, where amber light spills onto damp cobblestones, creating sharp silhouettes against the night.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Mocking and predatory; he has rejected the player's bribe and revealed they are working for a third party interested in the ledger.
- `tough_b` | **Scarred Tough** (Road thug) — Calculating and threatening; he is physically pinning the player against the inn and demanding to see the ledger.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T6 context)
You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."

## CURRENT TURN 7 NARRATION
You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
negotiate: The player hands the ledger and merchant seal to Halden to complete the transaction.
## CURRENT TURN 7 NARRATION
You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




## location
**Marrow's Crossing Outskirts** — The warmth of the inn spills out behind the thugs, contrasting with the cold, suffocating tension of the dark alleyway.

## PC conditions (this turn)
- rattled: rattled — The sudden, violent impact of the thug slamming into you has left you shaken and off-balance.


## threads (all — unified list, scope handled by Python)
- `the_ledger_conspiracy` [ARC]  [NORMAL] Mysterious figures have hired thugs to intercept Halden's ledger. tags: mystery, ledger, thugs (last seen T6)
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is finally settled; your name has been struck from his ledger.
- Halden has entrusted you with his leather-bound ledger, paying 200 credits to ensure its safe delivery to the Crossed Keys.
- Rumors of road-toughs extorting travelers near the Crossed Keys persist.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key`: Brass key x1 — A small brass key Halden gave you with the ledger.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T6)
You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."
## player_intent
**negotiate**: The player hands the ledger and merchant seal to Halden to complete the transaction.
## CURRENT TURN 7 NARRATION
You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player hands the ledger and merchant seal to Halden to complete the transaction.",
  "intent_verb": "negotiate",
  "target": "Halden",
  "check": {
    "required": false
  }
}
```

### Narration

You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."

### Extract Scene

```json
{
  "scene_tags": [
    "intimidation",
    "physical_confrontation",
    "tense_standoff"
  ],
  "scene_tagline": "Pinned Against the Timber",
  "location_description": "The warmth of the inn spills out behind the thugs, contrasting with the cold, suffocating tension of the dark alleyway.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Watching the struggle with a predatory grin, mocking the player's frantic movements."
    },
    {
      "id": "tough_b",
      "notes": "Physically pinning the player against the inn frame, snarling and blocking access to the ledger."
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
      "id": "rattled",
      "label": "rattled",
      "description": "The sudden, violent impact of the thug slamming into you has left you shaken and off-balance."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "recent_events_add": [
    {
      "id": "thug_confrontation_escalation",
      "text": "Two thugs have cornered you against the inn, demanding access to Halden's ledger.",
      "turn": 7
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Try to shove Scarred Tough away to regain personal space",
    "Attempt to reason with Bald Tough to de-escalate the tension",
    "Quickly draw your iron dagger to defend against the thugs",
    "Call out to Edda inside the inn for help"
  ],
  "outcome_summary": "Scarred Tough pins you against the inn wall, physically preventing you from handing over the ledger and leaving you rattled.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior",
    "instruction": "Scarred Tough tightens his grip, making it clear he won't let you move easily."
  },
  "thread_advance": [
    "the_ledger_conspiracy"
  ],
  "thread_resolve": []
}
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

- rules: est=1711t trimmed=False
- narrate: est=5874t trimmed=False
- extract.scene: est=3857t trimmed=False attempts=1
- extract.state: est=4078t trimmed=False attempts=1
- extract.progress: est=5186t trimmed=False attempts=1

### State After Turn

```json
{}
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

**Conditions:** rattled

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Watching the struggle with a predatory grin, mocking the player's frantic movements.
- Scarred Tough (Road thug) — Physically pinning the player against the inn frame, snarling and blocking access to the ledger.


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

**Conditions:** rattled

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The warmth of the inn spills out behind the thugs, contrasting with the cold, suffocating tension of the dark alleyway.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Brass key**: A small brass key Halden gave you with the ledger.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [arc/NORMAL] Mysterious figures have hired thugs to intercept Halden's ledger. (last seen T?)



## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Watching the struggle with a predatory grin, mocking the player's frantic movements.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Physically pinning the player against the inn frame, snarling and blocking access to the ledger.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
## Recent Turns

**T5:** You stop short before the entrance of the Crossed Keys, the warm, amber glow from the windows spilling out onto the damp cobblestones. The two figures are leaning against the timber frame, their silhouettes cutting jagged holes in the light. **Bald Tough** stands with his arms crossed, his thick neck straining against a coarse tunic, while **Scarred Tough** shifts his weight, his fingers drumming a restless, impatient rhythm against the hilt of a heavy club tucked into his belt.

"What are you two doing here?" you demand, your voice cutting through the low hum of the inn’s interior. You plant your feet, refusing to sidestep them, letting the weight of the **Leather-bound ledger** remind you of the purpose of your trek. The two men straighten simultaneously, their postures tightening as they turn to face you. The candlelight catches the glint of teeth and the hard, unforgiving lines of their faces.

**Bald Tough** lets out a short, barking laugh that carries no humor. He takes a heavy step forward, closing the distance until you can smell the stale ale and unwashed wool clinging to him. "Curiosity is a dangerous habit for a man who just finished paying off his skin, courier," he grunts, his eyes scanning your face with a predatory indifference. 

**Scarred Tough** steps around to your flank, cutting off your line of sight to the door. He doesn't look angry; he looks bored, which is far more unsettling. "We aren't here for the stew, kid," he says, his voice a low, gravelly rasp. "We’re just waiting for a delivery. Someone told us a certain book was coming through this gate, and we were told to make sure it didn't take a detour."


**T6:** You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."


**T7:** You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."

## This Turn's (Turn 8) Result


**Band:** SUCCESS → The sneak succeeds cleanly. Clean success — you do what you intended.




**GM Beat:** Scarred Tough tightens his grip, making it clear he won't let you move easily.
Surface as npc_behavior. This is backstage direction — integrate it naturally, not as player-visible narration.




=== PLAYER INPUT ===
I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The warmth of the inn spills out behind the thugs, contrasting with the cold, suffocating tension of the dark alleyway.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Watching the struggle with a predatory grin, mocking the player's frantic movements.
- `tough_b` | **Scarred Tough** (Road thug) — Physically pinning the player against the inn frame, snarling and blocking access to the ledger.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T7 context)
You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."

## CURRENT TURN 8 NARRATION
You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- rattled — The sudden, violent impact of the thug slamming into you has left you shaken and off-balance.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `brass_key` | Brass key ×1 — A small brass key Halden gave you with the ledger.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
sneak: The player attempts to use a brass key to unlock the inn's front door to find an alternative exit.
## CURRENT TURN 8 NARRATION
You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




## location
**Marrow's Crossing Outskirts** — A dark, narrow service corridor smelling of cedar and old grease lies just beyond the main door.


## threads (all — unified list, scope handled by Python)
- `the_ledger_conspiracy` [ARC]  [NORMAL] Mysterious figures have hired thugs to intercept Halden's ledger. tags: mystery, ledger, thugs (last seen T7)
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is finally settled; your name has been struck from his ledger.
- Halden has entrusted you with his leather-bound ledger, paying 200 credits to ensure its safe delivery to the Crossed Keys.
- Rumors of road-toughs extorting travelers near the Crossed Keys persist.
- Two thugs have cornered you against the inn, demanding access to Halden's ledger.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## rules_outcome
Band: SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.
## gm_beat
## pending_beat (carried from previous turn — not yet surfaced)
Type: pressure | Expires at turn: T9
Instruction: Scarred Tough tightens his grip, making it clear he won't let you move easily.
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T7)
You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."
## player_intent
**sneak**: The player attempts to use a brass key to unlock the inn's front door to find an alternative exit.
## CURRENT TURN 8 NARRATION
You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to use a brass key to unlock the inn's front door to find an alternative exit.",
  "intent_verb": "sneak",
  "target": "inn's front door",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal"
  }
}
```

### Narration

You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "tense_confrontation",
    "escape_attempt"
  ],
  "scene_tagline": "A Narrow Escape",
  "location_description": "A dark, narrow service corridor smelling of cedar and old grease lies just beyond the main door.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Watching the struggle with a predatory grin, waiting to see if the player can escape."
    },
    {
      "id": "tough_b",
      "notes": "Pinning the player against the inn frame with immense pressure, reacting with irritated malice to the player's movement."
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
      "id": "brass_key"
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "rattled"
    }
  ]
}
```

### Extract Progress

```json
{
  "recent_events_add": [
    {
      "id": "inn_door_unlocked",
      "text": "You successfully unlocked the inn's main door, revealing a dark service corridor.",
      "turn": 8
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Slip through the cracked door into the service corridor",
    "Wrestle Scarred Tough's arm off to regain your breath",
    "Use your iron dagger to threaten the thugs' proximity",
    "Shout for Edda inside the inn to draw attention"
  ],
  "outcome_summary": "You successfully pick the lock, but Scarred Tough's heavy arm pins you tightly against the door as it clicks open.",
  "thread_advance": [
    "the_ledger_conspiracy"
  ],
  "thread_resolve": []
}
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

- rules: est=1696t trimmed=False
- narrate: est=6275t trimmed=False
- extract.scene: est=3714t trimmed=False attempts=1
- extract.state: est=4114t trimmed=False attempts=1
- extract.progress: est=5136t trimmed=False attempts=1

### State After Turn

```json
{}
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

**Conditions:** none

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Watching the struggle with a predatory grin, waiting to see if the player can escape.
- Scarred Tough (Road thug) — Pinning the player against the inn frame with immense pressure, reacting with irritated malice to the player's movement.

## Last Turn Outcome
You successfully pick the lock, but Scarred Tough's heavy arm pins you tightly against the door as it clicks open.

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

**Conditions:** none

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
A dark, narrow service corridor smelling of cedar and old grease lies just beyond the main door.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [arc/NORMAL] Mysterious figures have hired thugs to intercept Halden's ledger. (last seen T?)



## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Watching the struggle with a predatory grin, waiting to see if the player can escape.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Pinning the player against the inn frame with immense pressure, reacting with irritated malice to the player's movement.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
## Recent Turns

**T6:** You reach into your pouch, pulling out the stack of coins, and let them clatter onto the damp cobblestones. The **Credits** scatter, a few skittering toward the gutter while the rest settle in the muck between your boots and theirs. "Caron’s coin is paid," you declare, your voice steady despite the drumming of your heart. "Take it and go home. The business is done."

**Bald Tough** looks down at the coins, his eyes narrowing as he shifts his weight. He doesn't reach for the money immediately; instead, he looks up at you, a slow, mocking grin spreading across his face. **Scarred Tough** lets out a dry, clicking sound in the back of his throat, his gaze moving from the coins to the heavy **Leather-bound ledger** tucked against your side. The boredom in his expression shifts into something more pointed, more calculating.

"Caron’s coin is paid, is it?" **Bald Tough** repeats, his voice dropping an octave. He stoops down, not to gather the coins, but to nudge one with the toe of his heavy boot, sending it spinning into the darkness. "That’s good for the merchant, maybe. But we aren't working for Caron. We’re working for the man who wants to know what’s inside that book."

**Scarred Tough** takes a half-step closer, his shoulder nearly brushing yours, effectively pinning you against the timber frame of the inn. The smell of stale ale is thick now, suffocating. "You can keep your little bribe, courier," he says, his eyes fixed on the ledger. "But we aren't going anywhere until we see what you're carrying. And if you aren't willing to show us, well... accidents happen on the road all the time. Especially to men who are in a hurry to sleep."


**T7:** You reach for the **Leather-bound ledger** at your side, your fingers brushing the heavy cover as you prepare to comply. However, as your hand closes around the binding, **Scarred Tough** shifts his weight, his shoulder slamming hard against yours to pin you more firmly against the timber frame of the inn. The impact rattles your teeth, and the sudden, violent proximity makes it impossible to make a clean move.

"I didn't say you could touch it," **Scarred Tough** snarls, his face inches from yours. The warmth of the inn spills out behind him, but the space between you and the thugs feels cold and suffocating. You attempt to reach for the book to slide it toward them, but the man’s heavy arm acts as a living barricade, crowding your personal space and preventing you from drawing the item from your coat.

**Bald Tough** watches the struggle with a predatory grin, his hands hovering near his belt. He makes no move to take the coins from the muck, his eyes locked on your frantic movements. "He’s a jumpy one, ain't he?" he mocks, his voice booming over the muffled laughter coming from inside the *Crossed Keys*. "Careful, kid. You keep fumbling around like that, and we might decide the book is worth more than the man holding it."


**T8:** You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.

## This Turn's (Turn 9) Result


**No roll required.** Describe what happens with appropriate weight for the moment.





=== PLAYER INPUT ===
I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
A dark, narrow service corridor smelling of cedar and old grease lies just beyond the main door.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Watching the struggle with a predatory grin, waiting to see if the player can escape.
- `tough_b` | **Scarred Tough** (Road thug) — Pinning the player against the inn frame with immense pressure, reacting with irritated malice to the player's movement.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T8 context)
You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.

## CURRENT TURN 9 NARRATION
You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
deceive: The player attempts to bribe the thug through the wall to gain entry.
## CURRENT TURN 9 NARRATION
You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




## location
**Marrow's Crossing Outskirts** — The rough, cold stone of the inn wall provides a grit-filled surface against your skin, separating you from the muffled warmth of the common room.


## threads (all — unified list, scope handled by Python)
- `the_ledger_conspiracy` [ARC]  [NORMAL] Mysterious figures have hired thugs to intercept Halden's ledger. tags: mystery, ledger, thugs (last seen T8)
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is finally settled; your name has been struck from his ledger.
- Halden has entrusted you with his leather-bound ledger, paying 200 credits to ensure its safe delivery to the Crossed Keys.
- Rumors of road-toughs extorting travelers near the Crossed Keys persist.
- Two thugs have cornered you against the inn, demanding access to Halden's ledger.
- You successfully unlocked the inn's main door, revealing a dark service corridor.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T8)
You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.
## player_intent
**deceive**: The player attempts to bribe the thug through the wall to gain entry.
## CURRENT TURN 9 NARRATION
You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to bribe the thug through the wall to gain entry.",
  "intent_verb": "deceive",
  "target": "Scarred Tough",
  "check": {
    "required": false
  }
}
```

### Narration

You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."

### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "intimidation"
  ],
  "scene_tagline": "A Desperate Bargain",
  "location_description": "The rough, cold stone of the inn wall provides a grit-filled surface against your skin, separating you from the muffled warmth of the common room.",
  "npc_add": [],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "tough_a",
      "notes": "Laughing derisively at the player's desperate attempt to bribe the wall."
    },
    {
      "id": "tough_b",
      "notes": "Pulling back slightly to stare at the player with a mixture of confusion and growing fury."
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
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Attempt to slip through the service door into the corridor",
    "Try to reason with Bald Tough to de-escalate the tension",
    "Draw your iron dagger to defend against the thugs' grip",
    "Use the ledger's weight to strike Scarred Tough's arm"
  ],
  "outcome_summary": "Your attempt to bribe the wall fails miserably, leaving you looking unstable and provoking the thugs' mockery.",
  "gm_beat": {
    "type": "pressure",
    "surface_as": "npc_behavior",
    "instruction": "Bald Tough and Scarred Tough tighten their perimeter, closing off the service door you just unlocked."
  },
  "thread_advance": [
    "the_ledger_conspiracy"
  ],
  "thread_resolve": []
}
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

- rules: est=1744t trimmed=False
- narrate: est=6079t trimmed=False
- extract.scene: est=3784t trimmed=False attempts=1
- extract.state: est=4120t trimmed=False attempts=1
- extract.progress: est=5120t trimmed=False attempts=1

### State After Turn

```json
{}
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

```json
{}
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

**Conditions:** none

## scene
Location: Marrow's Crossing Outskirts
## Present NPCs (in scene right now)
- Bald Tough (Road thug) — Laughing derisively at the player's desperate attempt to bribe the wall.
- Scarred Tough (Road thug) — Pulling back slightly to stare at the player with a mixture of confusion and growing fury.


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

**Conditions:** none

## Location
Marrow's Crossing Outskirts (marrows_crossing_outskirts)
The rough, cold stone of the inn wall provides a grit-filled surface against your skin, separating you from the muffled warmth of the common room.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.




## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Laughing derisively at the player's desperate attempt to bribe the wall.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Pulling back slightly to stare at the player with a mixture of confusion and growing fury.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
- [T5] Confronted Bald Tough and Scarred Tough at the Crossed Keys; they revealed they are hunting the ledger for an unknown employer.
- [T6] Attempted to bribe the thugs with 200 credits, but they refused the money, demanding the ledger instead.
- [T7] Scarred Tough physically pinned the player against the inn's timber frame, preventing them from handing over the ledger or the merchant seal.
## Recent Turns

**T8:** You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.


**T9:** You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."

## This Turn's (Turn 10) Result


**Band:** SUCCESS → The intimidate succeeds cleanly. Clean success — you do what you intended.




**GM Beat:** Bald Tough and Scarred Tough tighten their perimeter, closing off the service door you just unlocked.
Surface as npc_behavior. This is backstage direction — integrate it naturally, not as player-visible narration.




=== PLAYER INPUT ===
I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`marrows_crossing_outskirts` | Marrow's Crossing Outskirts
The rough, cold stone of the inn wall provides a grit-filled surface against your skin, separating you from the muffled warmth of the common room.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `tough_a` | **Bald Tough** (Road thug) — Laughing derisively at the player's desperate attempt to bribe the wall.
- `tough_b` | **Scarred Tough** (Road thug) — Pulling back slightly to stare at the player with a mixture of confusion and growing fury.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T9 context)
You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."

## CURRENT TURN 10 NARRATION
You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
intimidate: Aren Voss confronts Matthew Estrada to demand his true identity and motives.
## CURRENT TURN 10 NARRATION
You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...




## location
**Crossed Keys Common Room** — The air is thick and warm, smelling of cedar, contrasting sharply with the biting cold outside.

## PC conditions (this turn)
- disoriented: disoriented — The sudden transition from biting cold to warm air has left your head swimming.


## threads
None currently. Generate actions that could introduce new story directions or explore the environment.
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is finally settled; your name has been struck from his ledger.
- Halden has entrusted you with his leather-bound ledger, paying 200 credits to ensure its safe delivery to the Crossed Keys.
- Two thugs have cornered you against the inn, refusing your bribe and demanding access to Halden's ledger.

_(immutable section omitted — see Static Context > Seed State)_
## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `ledger`: Leather-bound ledger x1 — The heavy weight of the ledger shifts against your side.


## rules_outcome
Band: SUCCESS. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.
## gm_beat
## pending_beat (carried from previous turn — not yet surfaced)
Type: pressure | Expires at turn: T11
Instruction: Bald Tough and Scarred Tough tighten their perimeter, closing off the service door you just unlocked.
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T9)
You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."
## player_intent
**intimidate**: Aren Voss confronts Matthew Estrada to demand his true identity and motives.
## CURRENT TURN 10 NARRATION
You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Aren Voss confronts Matthew Estrada to demand his true identity and motives.",
  "intent_verb": "intimidate",
  "target": "Matthew Estrada",
  "check": {
    "required": true,
    "skill": "charisma",
    "difficulty": "normal"
  }
}
```

### Narration

You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.

### Extract Scene

```json
{
  "scene_tags": [
    "tense_confrontation",
    "suspense"
  ],
  "scene_tagline": "A Desperate Accusation",
  "location_change": {
    "id": "crossed_keys_common_room",
    "name": "Crossed Keys Common Room",
    "description": "A dim, amber-lit space filled with the scent of cedar and the low din of tavern patrons."
  },
  "location_description": "The air is thick and warm, smelling of cedar, contrasting sharply with the biting cold outside.",
  "npc_add": [],
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
      "id": "matthew_estrada",
      "notes": "Remains unnervingly calm and disciplined despite being accosted; appears more like a soldier than a simple traveler."
    },
    {
      "id": "tough_a",
      "notes": "Entering the common room from the doorway, looming over the player and cutting off the exit."
    },
    {
      "id": "tough_b",
      "notes": "Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew."
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
      "id": "disoriented",
      "label": "disoriented",
      "description": "The sudden transition from biting cold to warm air has left your head swimming."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "recent_events_add": [
    {
      "id": "thugs_enter_inn",
      "text": "Bald Tough and Scarred Tough have entered the Crossed Keys, cutting off the service corridor and drawing the attention of the patrons.",
      "turn": 10
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Demand Matthew Estrada reveal his true purpose or identity",
    "Try to warn Matthew Estrada about the thugs entering",
    "Use your iron dagger to intimidate Matthew or defend yourself",
    "Scan the common room for an exit or a weapon"
  ],
  "outcome_summary": "You confront Matthew Estrada about his suspicious behavior just as the thugs breach the inn, sealing your escape through the service door.",
  "thread_advance": [],
  "thread_resolve": [],
  "thread_add": {
    "id": "the_mysterious_traveler",
    "summary": "Matthew Estrada's true identity and motives remain a mystery.",
    "scope": "arc",
    "active": true,
    "urgency": "normal",
    "tags": [
      "matthew_estrada",
      "mystery"
    ],
    "progress": 0,
    "promotes": []
  }
}
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

- rules: est=1696t trimmed=False
- narrate: est=5824t trimmed=False
- extract.scene: est=3896t trimmed=False attempts=1
- extract.state: est=4159t trimmed=False attempts=1
- extract.progress: est=5446t trimmed=False attempts=1

### State After Turn

```json
{}
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

**Conditions:** disoriented

## scene
Location: Crossed Keys Common Room
## Present NPCs (in scene right now)
- Matthew Estrada (Traveler) — Remains unnervingly calm and disciplined despite being accosted; appears more like a soldier than a simple traveler.
- Bald Tough (Road thug) — Entering the common room from the doorway, looming over the player and cutting off the exit.
- Scarred Tough (Road thug) — Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew.

## Last Turn Outcome
You confront Matthew Estrada about his suspicious behavior just as the thugs breach the inn, sealing your escape through the service door.

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

**Conditions:** disoriented

## Location
Crossed Keys Common Room (crossed_keys_common_room)
A dim, amber-lit space filled with the scent of cedar and the low din of tavern patrons.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Leather-bound ledger**: The heavy weight of the ledger shifts against your side.


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [arc/NORMAL] Matthew Estrada's true identity and motives remain a mystery. (last seen T?)



## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Entering the common room from the doorway, looming over the player and cutting off the exit.

- **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | Remains unnervingly calm and disciplined despite being accosted; appears more like a soldier than a simple traveler.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
- [T5] Confronted Bald Tough and Scarred Tough at the Crossed Keys; they revealed they are hunting the ledger for an unknown employer.
- [T6] Attempted to bribe the thugs with 200 credits, but they refused the money, demanding the ledger instead.
- [T7] Scarred Tough physically pinned the player against the inn's timber frame, preventing them from handing over the ledger or the merchant seal.
## Recent Turns

**T8:** You wrench your hand away from the heavy weight of the **Leather-bound ledger**, your fingers diving instead into your pocket for the small, cold object Halden pressed into your palm. You fumble for the **Brass key**, your breath coming in shallow, ragged hitches as the wood of the inn frame digs into your spine. 

**Scarred Tough** reacts instantly to your sudden, frantic movement, his heavy arm tightening like a vice against your chest to pin you more securely against the timber. The pressure is immense, knocking the wind from your lungs as he leans his weight into you, his face a mask of irritated malice. "Looking for a way out?" he sneers, his teeth bared inches from your ear. "There ain't no exit that doesn't go through us."

Ignoring the crushing weight of his arm, you thrust the **Brass key** toward the lock of the main door, desperate to find any aperture—a side hatch or a service entrance—that might offer a sliver of escape. The metal teeth of the key bite into the lock, clicking with a sharp, mechanical finality as the mechanism yields. The door groans, clicking open just a few inches, revealing a dark, narrow service corridor that smells of cedar and old grease, leading away from the main common room.


**T9:** You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."


**T10:** You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.

## This Turn's (Turn 11) Result


**Band:** PARTIAL → The strength results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.






=== PLAYER INPUT ===
Matthew's bodyguard draws a knife! I tackle him into the bar shelves and search his coat while he's dazed.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`crossed_keys_common_room` | Crossed Keys Common Room
A dim, amber-lit space filled with the scent of cedar and the low din of tavern patrons.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `matthew_estrada` | **Matthew Estrada** (Traveler) — Remains unnervingly calm and disciplined despite being accosted; appears more like a soldier than a simple traveler.
- `tough_a` | **Bald Tough** (Road thug) — Entering the common room from the doorway, looming over the player and cutting off the exit.
- `tough_b` | **Scarred Tough** (Road thug) — Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T10 context)
You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.

## CURRENT TURN 11 NARRATION
You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## active_conditions
- disoriented — The sudden transition from biting cold to warm air has left your head swimming.

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `ledger` | Leather-bound ledger ×1 — The heavy weight of the ledger shifts against your side.

## player_intent
strength: Tackle the bodyguard into the shelves and search his coat while he is dazed.
## CURRENT TURN 11 NARRATION
You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `tough_a` | **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `kenneth_calloway` | **Kenneth Calloway** (Scarred Man) [PRESENT] — A tall, lean man with a prominent facial scar running from temple to jaw, wielding a wicked-looking knife.
- `matthew_estrada` | **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision.
- `tough_b` | **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...




## location
**Crossed Keys Common Room** — The floor is now littered with the glittering shards of shattered glassware from the bar impact, and the sawdust-covered floorboards are slick with spilled drink.


## threads (all — unified list, scope handled by Python)
- `the_mysterious_traveler` [ARC]  [NORMAL] Matthew Estrada's true identity and motives remain a mystery. tags: matthew_estrada, mystery (last seen T10)
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is finally settled; your name has been struck from his ledger.
- Halden has entrusted you with his leather-bound ledger, paying 200 credits to ensure its safe delivery to the Crossed Keys.
- Two thugs have cornered you against the inn, refusing your bribe and demanding access to Halden's ledger.
- Bald Tough and Scarred Tough have entered the Crossed Keys, cutting off the service corridor and drawing the attention of the patrons.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `heavy_pouch`: Heavy pouch x1 — Stolen from Matthew Estrada's leather jerkin


## rules_outcome
Band: PARTIAL. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.
## gm_beat
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T10)
You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.
## player_intent
**strength**: Tackle the bodyguard into the shelves and search his coat while he is dazed.
## CURRENT TURN 11 NARRATION
You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "Tackle the bodyguard into the shelves and search his coat while he is dazed.",
  "intent_verb": "strength",
  "target": "Matthew's bodyguard",
  "check": {
    "required": true,
    "skill": "strength",
    "difficulty": "normal"
  }
}
```

### Narration

You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.

### Extract Scene

```json
{
  "scene_tags": [
    "confrontation",
    "chaos",
    "tense"
  ],
  "scene_tagline": "Glass Shatters and Steel Glints",
  "location_description": "The floor is now littered with the glittering shards of shattered glassware from the bar impact, and the sawdust-covered floorboards are slick with spilled drink.",
  "npc_add": [
    {
      "id": "kenneth_calloway",
      "notes": "Aggressive and hostile; has drawn a knife and is advancing on the player.",
      "name": "Kenneth Calloway",
      "title": "Scarred Man",
      "bio": "A tall, lean man with a prominent facial scar running from temple to jaw, wielding a wicked-looking knife."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "matthew_estrada",
      "notes": "Momentarily dazed and slumped against the bar after being tackled."
    },
    {
      "id": "tough_a",
      "notes": "Approaching the player as their ledger slides toward them."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "kenneth_calloway",
      "name": "Kenneth Calloway",
      "title": "Scarred Man",
      "bio": "A tall, lean man with a facial scar running from temple to jaw who carries a long, wicked-looking knife.",
      "aliases": []
    }
  ]
}
```

### Extract State

```json
{
  "inventory_add": [
    {
      "id": "heavy_pouch",
      "name": "Heavy pouch",
      "notes": "Stolen from Matthew Estrada's leather jerkin",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "ledger"
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [
    {
      "id": "disoriented"
    }
  ]
}
```

### Extract Progress

```json
{
  "recent_events_add": [
    {
      "id": "matthew_estrada_tackle",
      "text": "You tackled Matthew Estrada against the bar, causing a commotion and shattering glassware.",
      "turn": 11
    },
    {
      "id": "ledger_dropped",
      "text": "During the struggle, Halden's leather-bound ledger slipped from your belt and slid toward Bald Tough.",
      "turn": 11
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Dive for the sliding ledger before Bald Tough reaches it",
    "Brandish your iron dagger at the approaching Kenneth Calloway",
    "Use your strength to shove the dazed Matthew Estrada away",
    "Attempt to scramble behind the bar for cover and safety"
  ],
  "outcome_summary": "You successfully snatched a heavy pouch from Matthew Estrada's jerkin, but your tackle caused a loud commotion and your precious ledger slid across the floor toward the thugs.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "npc_behavior",
    "instruction": "Kenneth Calloway advances with his knife drawn, cutting off your path to the bar."
  },
  "thread_advance": [
    "the_mysterious_traveler"
  ],
  "thread_resolve": []
}
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

- rules: est=1781t trimmed=False
- narrate: est=6293t trimmed=False
- extract.scene: est=3947t trimmed=False attempts=1
- extract.state: est=4172t trimmed=False attempts=1
- extract.progress: est=5369t trimmed=False attempts=1

### State After Turn

```json
{}
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

**Conditions:** none

## scene
Location: Crossed Keys Common Room
## Present NPCs (in scene right now)
- Matthew Estrada (Traveler) — Momentarily dazed and slumped against the bar after being tackled.
- Bald Tough (Road thug) — Approaching the player as their ledger slides toward them.
- Scarred Tough (Road thug) — Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew.
- Kenneth Calloway (Scarred Man) — Aggressive and hostile; has drawn a knife and is advancing on the player.

## Last Turn Outcome
You successfully snatched a heavy pouch from Matthew Estrada's jerkin, but your tackle caused a loud commotion and your precious ledger slid across the floor toward the thugs.

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

**Conditions:** none

## Location
Crossed Keys Common Room (crossed_keys_common_room)
The floor is now littered with the glittering shards of shattered glassware from the bar impact, and the sawdust-covered floorboards are slick with spilled drink.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Heavy pouch**: Stolen from Matthew Estrada's leather jerkin


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [arc/NORMAL] Matthew Estrada's true identity and motives remain a mystery. (last seen T?)



## Characters
Before introducing a new named NPC, check this list first.

- **Bald Tough** (Road thug) [PRESENT] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad. | Approaching the player as their ledger slides toward them.

- **Kenneth Calloway** (Scarred Man) [PRESENT] — A tall, lean man with a prominent facial scar running from temple to jaw, wielding a wicked-looking knife. | Aggressive and hostile; has drawn a knife and is advancing on the player.

- **Matthew Estrada** (Traveler) [PRESENT] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves with military precision. | Momentarily dazed and slumped against the bar after being tackled.

- **Scarred Tough** (Road thug) [PRESENT] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains. | Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
- [T5] Confronted Bald Tough and Scarred Tough at the Crossed Keys; they revealed they are hunting the ledger for an unknown employer.
- [T6] Attempted to bribe the thugs with 200 credits, but they refused the money, demanding the ledger instead.
- [T7] Scarred Tough physically pinned the player against the inn's timber frame, preventing them from handing over the ledger or the merchant seal.
## Recent Turns

**T9:** You lean your head against the rough, cold stone of the inn, the grit biting into your skin as you press your ear close to the masonry. The muffled warmth of the common room hums through the wall, a distant world of laughter and clinking glass that feels leagues away from the suffocating grip of the thugs. "I have credits. Open up," you whisper, your voice a desperate, thin thread against the stone. You reach into your pocket, fingers trembling, and press a single, solitary coin against the dark surface of the wall, a futile offering to the building itself.

The stone remains indifferent, cold and unyielding to your plea. The tiny coin clatters uselessly against the masonry before sliding down into the dirt, a pathetic sound in the heavy silence between your breaths. The wall offers no warmth, no clicking of a latch, no sign that anyone inside heard your frantic, nonsensical bargain.

Behind you, the heavy weight of **Scarred Tough** shifts, his breathing coming in hot, ragged bursts against your neck. The realization of your strange behavior clearly registers; he pulls back just enough to look at you, his eyes Narrowing with a mixture of confusion and growing fury. **Bald Tough** lets out a short, barking laugh that carries no humor, his shadow stretching long and menacing across the doorway you just unlocked. "Lost your wits, have you, courier?" he calls out, his voice dripping with derision. "Talking to the walls now? Maybe the road's finally broken your brain."


**T10:** You wrench yourself away from the suffocating proximity of the thugs, stumbling through the heavy door into the dim, cedar-scented warmth of the common room. The transition from the biting cold to the thick, amber-lit air makes your head swim, but the adrenaline keeps your legs moving. You lunge toward the bar, your fingers clamping like a trap around the thick, calloused wrist of **Matthew Estrada**. 

"Who are you really?" you hiss, your voice cracking with a frantic edge as you pull on his arm, forcing him to face you. "Why are you watching the room like a soldier on duty? What are you waiting for?"

**Matthew Estrada** doesn't flinch. His body remains as solid as the oak bar beneath him, his expression shifting from passive observation to a cold, disciplined stillness. He doesn't pull his arm away; instead, he holds your gaze with eyes that are unsettlingly calm, devoid of the drunken haze affecting the other patrons. "Careful, courier," he says, his voice a low, steady rumble that cuts through the tavern's din. "Accusations are heavy things to carry, and you look like you're already struggling with the weight of your own."

Outside, the heavy thud of boots against the threshold signals that your moment of frantic confrontation has drawn attention. **Bald Tough** and **Scarred Tough** are closing the gap, their silhouettes looming large against the doorway you just breached, effectively cutting off the service corridor and sealing the room. The laughter from the other tables dies down as the two men step into the light, their eyes fixed on you and the man you are currently accosting.


**T11:** You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.

## This Turn's (Turn 12) Result


**Band:** PARTIAL → The escape results in a partial. You get what you wanted, but something is taken from you or goes wrong in the process.




**GM Beat:** Kenneth Calloway advances with his knife drawn, cutting off your path to the bar.
Surface as npc_behavior. This is backstage direction — integrate it naturally, not as player-visible narration.




=== PLAYER INPUT ===
I grab the ledger from my coat and sprint out the back door toward the river dock, shouting for Halden to hold on.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`crossed_keys_common_room` | Crossed Keys Common Room
The floor is now littered with the glittering shards of shattered glassware from the bar impact, and the sawdust-covered floorboards are slick with spilled drink.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `matthew_estrada` | **Matthew Estrada** (Traveler) — Momentarily dazed and slumped against the bar after being tackled.
- `tough_a` | **Bald Tough** (Road thug) — Approaching the player as their ledger slides toward them.
- `tough_b` | **Scarred Tough** (Road thug) — Entering the common room alongside Bald Tough, eyes fixed on the player and Matthew.
- `kenneth_calloway` | **Kenneth Calloway** (Scarred Man) — Aggressive and hostile; has drawn a knife and is advancing on the player.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T11 context)
You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.

## CURRENT TURN 12 NARRATION
You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `heavy_pouch` | Heavy pouch ×1 — Stolen from Matthew Estrada's leather jerkin

## player_intent
escape: The player attempts to retrieve their ledger and flee through the back door to escape the approaching thugs.
## CURRENT TURN 12 NARRATION
You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `kitchen_hand` | **Kitchen Hand** (Kitchen Hand) [PRESENT] — A busy worker in the Crossed Keys kitchen, currently caught off guard by the player's flight.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `kenneth_calloway` | **Kenneth Calloway** [KNOWN] — A tall, lean man with a facial scar running from temple to jaw who carries a long, wicked-looking knife.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## location
**River Docks** — A dark, damp area at the edge of the pier, filled with river-mist and splintered crates.


## threads (all — unified list, scope handled by Python)
- `the_mysterious_traveler` [ARC]  [NORMAL] Matthew Estrada's true identity and motives remain a mystery. tags: matthew_estrada, mystery (last seen T11)
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Your debt to Caron is finally settled; your name has been struck from his ledger.
- Halden has entrusted you with his leather-bound ledger, paying 200 credits to ensure its safe delivery to the Crossed Keys.
- Two thugs have cornered you against the inn, refusing your bribe and demanding access to Halden's ledger.
- Bald Tough and Scarred Tough have entered the Crossed Keys, cutting off the service corridor and drawing the attention of the patrons.
- You tackled Matthew Estrada against the bar, causing a commotion and shattering glassware.
- During the struggle, Halden's leather-bound ledger slipped from your belt and slid toward Bald Tough.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `leather_bound_ledger`: Leather-bound ledger x1


## rules_outcome
Band: PARTIAL. Apply thread advancement freely on success/crit_success. On fail/setback/partial, do NOT mark threads as advanced for the attempted action; prefer breathing_room/null beats on fail.
## gm_beat
## pending_beat (carried from previous turn — not yet surfaced)
Type: complication | Expires at turn: T13
Instruction: Kenneth Calloway advances with his knife drawn, cutting off your path to the bar.
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T11)
You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.
## player_intent
**escape**: The player attempts to retrieve their ledger and flee through the back door to escape the approaching thugs.
## CURRENT TURN 12 NARRATION
You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to retrieve their ledger and flee through the back door to escape the approaching thugs.",
  "intent_verb": "escape",
  "target": "the thugs and the exit",
  "check": {
    "required": true,
    "skill": "dexterity",
    "difficulty": "normal"
  }
}
```

### Narration

You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.

### Extract Scene

```json
{
  "scene_tags": [
    "combat",
    "chase",
    "desperate_flight",
    "loss"
  ],
  "scene_tagline": "A Costly Escape",
  "location_change": {
    "id": "river_docks",
    "name": "River Docks",
    "description": "A dark, damp area at the edge of the pier, filled with river-mist and splintered crates."
  },
  "npc_add": [
    {
      "id": "kitchen_hand",
      "notes": "Startled by the player's sudden, frantic passage through the kitchen.",
      "name": "Kitchen Hand",
      "title": "Kitchen Hand",
      "bio": "A busy worker in the Crossed Keys kitchen, currently caught off guard by the player's flight."
    }
  ],
  "npc_remove": [
    {
      "id": "matthew_estrada"
    },
    {
      "id": "tough_a"
    },
    {
      "id": "tough_b"
    },
    {
      "id": "kenneth_calloway"
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
      "id": "leather_bound_ledger",
      "name": "Leather-bound ledger",
      "notes": "",
      "amount": 1,
      "aliases": []
    }
  ],
  "inventory_remove": [
    {
      "id": "heavy_pouch"
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
      "id": "lost_stolen_pouch",
      "text": "The heavy pouch stolen from Matthew Estrada tore open during your flight, spilling its contents into the river.",
      "turn": 12
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Search the river edge for any dropped items from the pouch",
    "Hide in the shadows of the docks to evade pursuers",
    "Use your high agility to scale a nearby crate and escape",
    "Check the ledger for anything useful to trade for help"
  ],
  "outcome_summary": "You successfully retrieved the ledger and escaped into the docks, but the stolen pouch snagged on a crate and its contents were lost to the river.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "environmental",
    "instruction": "The river-mist thickens, obscuring your vision and making the footing on the splintered pier treacherous."
  },
  "thread_advance": [
    "the_mysterious_traveler"
  ],
  "thread_resolve": []
}
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

- rules: est=1799t trimmed=False
- narrate: est=6497t trimmed=False
- extract.scene: est=4024t trimmed=False attempts=1
- extract.state: est=4158t trimmed=False attempts=1
- extract.progress: est=5476t trimmed=False attempts=1

### State After Turn

```json
{}
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

```json
{}
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

**Conditions:** none

## scene
Location: River Docks
## Present NPCs (in scene right now)
- Kitchen Hand (Kitchen Hand) — Startled by the player's sudden, frantic passage through the kitchen.


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

**Conditions:** none

## Location
River Docks (river_docks)
A dark, damp area at the edge of the pier, filled with river-mist and splintered crates.

## inventory (cross-reference before describing item use)
- **Iron dagger**: Plain crossguard, edge worn from honing. Belt-carried.
- **Linen bandages** ×3: Three rolls. Field-grade — won't replace a healer.
- **Traveler's cloak**: Oiled wool, road-stained, hood deep enough to hide a face.
- **Leather-bound ledger**


### Campaign Arc

**Goal:** Clear your debts and deliver the ledger — two obligations binding you to Marrow's Crossing.


**Thematic question:** What does it cost to settle old debts when new ones keep forming?
**PC drive:** Prove you can handle the road — clear your name and earn enough to start over.
**Active threads:**
- [arc/NORMAL] Matthew Estrada's true identity and motives remain a mystery. (last seen T?)



## Characters
Before introducing a new named NPC, check this list first.

- **Kitchen Hand** (Kitchen Hand) [PRESENT] — A busy worker in the Crossed Keys kitchen, currently caught off guard by the player's flight. | Startled by the player's sudden, frantic passage through the kitchen.

- **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.

- **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...

- **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...

- **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu... | wants: To secure reliable couriers for his mercantile business while maximizing profit.

- **Kenneth Calloway** [KNOWN] — A tall, lean man with a facial scar running from temple to jaw who carries a long, wicked-looking knife.

- **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...

- **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




_(immutable section omitted — see Static Context > Seed State)_

## Scene Context

## Prior Turns (Compacted)
- [T1] Aren sat with Caron at the Crossed Keys to discuss the debt.
- [T2] Aren settled a 500 credit debt with Caron at the Crossed Keys, clearing his name from the ledger.
- [T3] Aren accepted a contract from Halden to deliver a leather-bound ledger to the Crossed Keys for 200 credits.
- [T4] Aren departed Marrow's Crossing via the east gate, traveling along the merchant road toward the inn.
- [T5] Confronted Bald Tough and Scarred Tough at the Crossed Keys; they revealed they are hunting the ledger for an unknown employer.
- [T6] Attempted to bribe the thugs with 200 credits, but they refused the money, demanding the ledger instead.
- [T7] Scarred Tough physically pinned the player against the inn's timber frame, preventing them from handing over the ledger or the merchant seal.
- [T8] Using the Brass key, the player successfully unlocked a service corridor door to escape the thugs.
- [T9] The player attempted to bribe the inn walls with a credit, which was ignored and mocked by Bald Tough and Scarred Tough.
- [T10] The player confronted Matthew Estrada at the bar, demanding to know his true identity, while the thugs entered the common room to cut off the exit.
## Recent Turns

**T11:** You lunge forward, throwing the full weight of your frantic, disoriented body into **Matthew Estrada**. The impact is jarring; his frame is more solid than it looks, more like reinforced timber than flesh, but the sheer momentum of your tackle forces him backward. He grunts, a short, controlled sound, as his spine slams into the heavy oak bar. The impact sends a cascade of glassware shattering to the floor, the clatter of breaking crystal cutting through the sudden silence of the common room like a gunshot.

As he recoils, a man who had been standing in the shadow of the corner—a tall, lean man with a facial scar running from temple to jaw, **Kenneth Calloway**—snarls and draws a long, wicked-looking knife from a sheath at his hip. The steel glints hungrily in the amber light as he steps toward you, teeth bared. However, the momentum of your tackle has left **Matthew Estrada** slumped against the bar, momentarily dazed by the sudden assault. 

You scramble toward him, your hands diving into the heavy folds of his leather jerkin. Your fingers brush against coarse fabric and cold metal as you frantically rummage through his coat, desperate to find anything of value or leverage while his eyes struggle to refocus. You manage to snatch a small, heavy pouch from a hidden interior pocket, but as you pull it free, the sudden movement causes your own **Leather-bound ledger** to slip from your belt. It hits the floor with a heavy, hollow thud, sliding across the sawdust-covered floorboards toward the approaching **Bald Tough**.


**T12:** You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.

## This Turn's (Turn 13) Result


**No roll required.** Describe what happens with appropriate weight for the moment.



**GM Beat:** The river-mist thickens, obscuring your vision and making the footing on the splintered pier treacherous.
Surface as environmental. This is backstage direction — integrate it naturally, not as player-visible narration.




=== PLAYER INPUT ===
I find a quiet corner at the dock and wrap my wounds with my shirt. Then I write a note to Caron about the intercepted courier and pay the dock boy to deliver it.
=== END PLAYER INPUT ===

```

### Extract Scene User Prompt
```
## location
`river_docks` | River Docks
A dark, damp area at the edge of the pier, filled with river-mist and splintered crates.

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `kitchen_hand` | **Kitchen Hand** (Kitchen Hand) — Startled by the player's sudden, frantic passage through the kitchen.

_(immutable section omitted — see Static Context > Seed State)_


## previous_turn_narration (T12 context)
You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.

## CURRENT TURN 13 NARRATION
You collapse into the hollow between two rotting, salt-crusted crates, the dampness of the pier seeping through your clothes. Your breath comes in ragged, shallow stabs as you fumble at your belt, pulling out two rolls of **Linen bandages**. The fabric is coarse against your skin, but as you wrap them tightly around the scrapes and bruises earned during the frantic scramble, the sting of the river-mist on your raw skin begins to dull into a heavy, throbbing ache. The silence of the docks is heavy, broken only by the rhythmic, hollow slapping of the river against the pier-pilings.

With trembling fingers, you pull a scrap of parchment from your pocket and a small charcoal nub, scrawling a frantic, illegible note to **Caron**. You can barely form the letters, your hands still shaking from the adrenaline, but the intent is clear: the contract is compromised, the thugs are active, and the courier route is no longer safe. You clutch the note tightly, the ink smudging against your palm.

A young boy, no more than twelve, shifts in the shadows nearby, his eyes wide as he watches you from atop a stack of empty barrels. His face is smudged with soot, and his oversized tunic hangs loosely off his thin frame. You press the crumpled note into his small, cold hand, thrusting a few coins toward him as payment. The boy’s eyes dart toward the dark, swirling water where the stolen pouch vanished, then back to you, before he vanishes into the thickening river-mist, his small footsteps swallowed by the gloom. 

As he disappears, the mist rolls in more aggressively, a heavy, grey shroud that clings to the splintered wood of the pier. The world beyond your small, dark corner begins to dissolve into a featureless void, making every creak of the timber and every splash from the river feel unnervingly close.
## END CURRENT TURN NARRATION

```

### Extract State User Prompt
```
## inventory (current stacks — read amount before emitting `inventory_remove`)
- `iron_dagger` | Iron dagger ×1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages` | Linen bandages ×3 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak` | Traveler's cloak ×1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `leather_bound_ledger` | Leather-bound ledger ×1

## player_intent
negotiate: The player attempts to pay a dock boy to deliver a note to Caron.
## CURRENT TURN 13 NARRATION
You collapse into the hollow between two rotting, salt-crusted crates, the dampness of the pier seeping through your clothes. Your breath comes in ragged, shallow stabs as you fumble at your belt, pulling out two rolls of **Linen bandages**. The fabric is coarse against your skin, but as you wrap them tightly around the scrapes and bruises earned during the frantic scramble, the sting of the river-mist on your raw skin begins to dull into a heavy, throbbing ache. The silence of the docks is heavy, broken only by the rhythmic, hollow slapping of the river against the pier-pilings.

With trembling fingers, you pull a scrap of parchment from your pocket and a small charcoal nub, scrawling a frantic, illegible note to **Caron**. You can barely form the letters, your hands still shaking from the adrenaline, but the intent is clear: the contract is compromised, the thugs are active, and the courier route is no longer safe. You clutch the note tightly, the ink smudging against your palm.

A young boy, no more than twelve, shifts in the shadows nearby, his eyes wide as he watches you from atop a stack of empty barrels. His face is smudged with soot, and his oversized tunic hangs loosely off his thin frame. You press the crumpled note into his small, cold hand, thrusting a few coins toward him as payment. The boy’s eyes dart toward the dark, swirling water where the stolen pouch vanished, then back to you, before he vanishes into the thickening river-mist, his small footsteps swallowed by the gloom. 

As he disappears, the mist rolls in more aggressively, a heavy, grey shroud that clings to the splintered wood of the pier. The world beyond your small, dark corner begins to dissolve into a featureless void, making every creak of the timber and every splash from the river feel unnervingly close.
## END CURRENT TURN NARRATION

```

### Extract Progress User Prompt
```

## characters
- `kitchen_hand` | **Kitchen Hand** (Kitchen Hand) [PRESENT] — A busy worker in the Crossed Keys kitchen, currently caught off guard by the player's flight.
- `soot_stained_boy` | **Soot-stained Boy** (Messenger) [PRESENT] — A thin, twelve-year-old boy in an oversized tunic, smudged with soot, acting as a local street urchin.
- `tough_a` | **Bald Tough** [KNOWN] — Hired muscle. No personal stake in this — he'll back off if the price is right or the fight goes bad.
- `caron` | **Caron** [KNOWN] — A portly man in his sixties with a merchant's ledger and a patient demeanor. He has recently seen the player settle a...
- `innkeeper` | **Edda** [KNOWN] — Runs the inn alone since her husband died. Knows every traveler by face if not by name. Stays out of trouble unless i...
- `halden` | **Halden** [KNOWN] — A road merchant in his fifties who hires couriers when his usual runners are spoken for. Honest by reputation, carefu...
- `kenneth_calloway` | **Kenneth Calloway** [KNOWN] — A tall, lean man with a facial scar running from temple to jaw who carries a long, wicked-looking knife.
- `matthew_estrada` | **Matthew Estrada** [KNOWN] — A tall, broad-shoulded man in a stained leather jerkin carrying a heavy rucksack. Looks like a road runner but moves...
- `tough_b` | **Scarred Tough** [KNOWN] — Same outfit as the other — hired by the same person. Quicker to violence; not the brains.




## location
**River Docks** — A heavy, grey shroud of mist rolls in, clinging to the splintered wood and dissolving the world into a featureless void.

## PC conditions (this turn)
- wounded: wounded — Scrapes and bruises from a frantic scramble causing a heavy, throbbing ache.


## threads (all — unified list, scope handled by Python)
- `the_mysterious_traveler` [ARC]  [NORMAL] Matthew Estrada's true identity and motives remain a mystery. tags: matthew_estrada, mystery (last seen T12)
## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Two thugs have cornered you against the inn, refusing your bribe and demanding access to Halden's ledger.
- Bald Tough and Scarred Tough have entered the Crossed Keys, cutting off the service corridor and drawing the attention of the patrons.
- You have confronted Matthew Estrada at the bar, demanding to know his true purpose and identity amidst the growing commotion.
- Halden's leather-bound ledger remains a central point of tension as the thugs close in.

## Current inventory (this turn)
- `iron_dagger`: Iron dagger x1 — Plain crossguard, edge worn from honing. Belt-carried.
- `bandages`: Linen bandages x1 — Three rolls. Field-grade — won't replace a healer.
- `traveler_cloak`: Traveler's cloak x1 — Oiled wool, road-stained, hood deep enough to hide a face.
- `leather_bound_ledger`: Leather-bound ledger x1


## gm_beat
## pending_beat (carried from previous turn — not yet surfaced)
Type: complication | Expires at turn: T14
Instruction: The river-mist thickens, obscuring your vision and making the footing on the splintered pier treacherous.
## pacing_context
Directive: none
Gate: allow
## last_turn_narration (T12)
You lunge for the **Leather-bound ledger** as it skitters across the sawdust, your fingers grazing the cool, textured cover just before **Kenneth Calloway** closes the distance. The tall, scarred man lunges, his wicked knife whistling through the air as he cuts off your access to the bar, his face twisted into a mask of predatory intent. You wrench the book from the floor, clutching it against your chest like a lifeline, and pivot on your heel to bolt toward the service corridor.

"Halden! Hold on!" you scream, your voice cracking as you burst through the small wooden door at the rear of the common room. The transition from the warm, chaotic tavern to the cool, damp air of the kitchen is a blur of slamming wood and frantic breathing. You don't stop to navigate the clutter of crates and hanging herbs; you shoulder past a startled kitchen hand and burst out the rear exit into the night.

The frantic sprint toward the river docks is a desperate scramble through the mud and shadows of the alleyway. You make it to the edge of the pier, your lungs burning with the sudden intake of river-mist, but as you turn to see if anyone is following, you realize the weight in your hands is wrong. The **Leather-bound ledger** is still clutched to your chest, but as your fingers wrap around the binding, you feel the sickening sensation of something sliding loose underneath. The heavy, stolen **Heavy pouch** you snatched from **Matthew Estrada** has snagged on a splintered crate during your frantic flight, tearing open and spilling its contents into the dark, churning waters of the river below.
## player_intent
**negotiate**: The player attempts to pay a dock boy to deliver a note to Caron.
## CURRENT TURN 13 NARRATION
You collapse into the hollow between two rotting, salt-crusted crates, the dampness of the pier seeping through your clothes. Your breath comes in ragged, shallow stabs as you fumble at your belt, pulling out two rolls of **Linen bandages**. The fabric is coarse against your skin, but as you wrap them tightly around the scrapes and bruises earned during the frantic scramble, the sting of the river-mist on your raw skin begins to dull into a heavy, throbbing ache. The silence of the docks is heavy, broken only by the rhythmic, hollow slapping of the river against the pier-pilings.

With trembling fingers, you pull a scrap of parchment from your pocket and a small charcoal nub, scrawling a frantic, illegible note to **Caron**. You can barely form the letters, your hands still shaking from the adrenaline, but the intent is clear: the contract is compromised, the thugs are active, and the courier route is no longer safe. You clutch the note tightly, the ink smudging against your palm.

A young boy, no more than twelve, shifts in the shadows nearby, his eyes wide as he watches you from atop a stack of empty barrels. His face is smudged with soot, and his oversized tunic hangs loosely off his thin frame. You press the crumpled note into his small, cold hand, thrusting a few coins toward him as payment. The boy’s eyes dart toward the dark, swirling water where the stolen pouch vanished, then back to you, before he vanishes into the thickening river-mist, his small footsteps swallowed by the gloom. 

As he disappears, the mist rolls in more aggressively, a heavy, grey shroud that clings to the splintered wood of the pier. The world beyond your small, dark corner begins to dissolve into a featureless void, making every creak of the timber and every splash from the river feel unnervingly close.
## END CURRENT TURN NARRATION

```

## Engine Outputs

### Rules

**Parsed (engine):**
```json
{}
```

**Raw LLM output:**
```
{
  "intent": "The player attempts to pay a dock boy to deliver a note to Caron.",
  "intent_verb": "negotiate",
  "target": "dock boy",
  "check": {
    "required": false
  }
}
```

### Narration

You collapse into the hollow between two rotting, salt-crusted crates, the dampness of the pier seeping through your clothes. Your breath comes in ragged, shallow stabs as you fumble at your belt, pulling out two rolls of **Linen bandages**. The fabric is coarse against your skin, but as you wrap them tightly around the scrapes and bruises earned during the frantic scramble, the sting of the river-mist on your raw skin begins to dull into a heavy, throbbing ache. The silence of the docks is heavy, broken only by the rhythmic, hollow slapping of the river against the pier-pilings.

With trembling fingers, you pull a scrap of parchment from your pocket and a small charcoal nub, scrawling a frantic, illegible note to **Caron**. You can barely form the letters, your hands still shaking from the adrenaline, but the intent is clear: the contract is compromised, the thugs are active, and the courier route is no longer safe. You clutch the note tightly, the ink smudging against your palm.

A young boy, no more than twelve, shifts in the shadows nearby, his eyes wide as he watches you from atop a stack of empty barrels. His face is smudged with soot, and his oversized tunic hangs loosely off his thin frame. You press the crumpled note into his small, cold hand, thrusting a few coins toward him as payment. The boy’s eyes dart toward the dark, swirling water where the stolen pouch vanished, then back to you, before he vanishes into the thickening river-mist, his small footsteps swallowed by the gloom. 

As he disappears, the mist rolls in more aggressively, a heavy, grey shroud that clings to the splintered wood of the pier. The world beyond your small, dark corner begins to dissolve into a featureless void, making every creak of the timber and every splash from the river feel unnervingly close.

### Extract Scene

```json
{
  "scene_tags": [
    "stealth",
    "tense",
    "discovery"
  ],
  "scene_tagline": "Lost in the River Mist",
  "location_description": "A heavy, grey shroud of mist rolls in, clinging to the splintered wood and dissolving the world into a featureless void.",
  "npc_add": [
    {
      "id": "soot_stained_boy",
      "notes": "Watching the player from atop a stack of barrels before being paid to deliver a note.",
      "name": "Soot-stained Boy",
      "title": "Messenger",
      "bio": "A thin, twelve-year-old boy in an oversized tunic, smudged with soot, acting as a local street urchin."
    }
  ],
  "npc_remove": [],
  "npc_update": [
    {
      "id": "kitchen_hand",
      "notes": "No longer present in the scene; the player has moved to the docks."
    }
  ],
  "compendium_npc_update": [
    {
      "id": "soot_stained_boy",
      "name": "Soot-stained Boy",
      "title": "Messenger",
      "bio": "A thin, twelve-year-old boy in an oversized tunic, smudged with soot, acting as a local street urchin.",
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
      "id": "bandages",
      "amount": 2
    }
  ],
  "inventory_update": [],
  "pc_condition_add": [
    {
      "id": "wounded",
      "label": "wounded",
      "description": "Scrapes and bruises from a frantic scramble causing a heavy, throbbing ache."
    }
  ],
  "pc_condition_remove": []
}
```

### Extract Progress

```json
{
  "recent_events_add": [
    {
      "id": "lost_stolen_pouch",
      "text": "The heavy pouch snatched from Matthew Estrada was lost to the river during your flight.",
      "turn": 13
    }
  ],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [
    "Send the note to Caron via the soot-stained boy",
    "Tend to your wounds with linen bandages to dull the pain",
    "Hide within the crates to avoid detection in the mist",
    "Scan the thickening river-mist for any approaching threats"
  ],
  "outcome_summary": "You tend to your wounds and successfully enlist the soot-stained boy to deliver a frantic note to Caron.",
  "gm_beat": {
    "type": "complication",
    "surface_as": "environmental",
    "instruction": "The river-mist thickens, obscuring your vision and making the footing on the splintered pier treacherous."
  },
  "thread_advance": [
    "the_mysterious_traveler"
  ],
  "thread_resolve": []
}
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

- rules: est=1665t trimmed=False
- narrate: est=6096t trimmed=False
- extract.scene: est=4010t trimmed=False attempts=1
- extract.state: est=4200t trimmed=False attempts=1
- extract.progress: est=5529t trimmed=False attempts=1

### State After Turn

```json
{}
```


---
# Deterministic Signals

## Auto-Checker Failures
*(no failures)*

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries | momentum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1708 | 4795 | 3382 | 4119 | 4775 | 0 | 0 | — |
| 2 | 1711 | 5088 | 3804 | 4244 | 5208 | 0 | 0 | — |
| 3 | 1723 | 5535 | 3941 | 4189 | 5393 | 0 | 0 | — |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 4 | 1726 | 5728 | 3853 | 4122 | 5224 | 0 | 0 | — |
| 5 | 1618 | 6007 | 3732 | 4202 | 5326 | 0 | 0 | — |
| 6 | 1743 | 6096 | 3965 | 4202 | 5511 | 0 | 0 | — |
| 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 7 | 1711 | 5874 | 3857 | 4078 | 5186 | 0 | 0 | — |
| 8 | 1696 | 6275 | 3714 | 4114 | 5136 | 0 | 0 | — |
| 9 | 1744 | 6079 | 3784 | 4120 | 5120 | 0 | 0 | — |
| 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 10 | 1696 | 5824 | 3896 | 4159 | 5446 | 0 | 0 | — |
| 11 | 1781 | 6293 | 3947 | 4172 | 5369 | 0 | 0 | — |
| 12 | 1799 | 6497 | 4024 | 4158 | 5476 | 0 | 0 | — |
| 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 13 | 1665 | 6096 | 4010 | 4200 | 5529 | 0 | 0 | — |

**Scope fallback rate:** 0% (0/17 turns)

## Prompt Redundancy (cross-stream duplication)
Detected duplicated content blocks (>= 3 lines, each >= 60 chars) appearing in multiple streams. The judge should evaluate whether this duplication is intentional (e.g. the narration is correctly fed to all three extractors) or wasted tokens (e.g. the same PC bio rendered redundantly).

### Top overlaps across all turns

| Streams | Total duplicated blocks | Preview |
|---|---:|---|
| narrate + progress | 6 | `- Marrow's Crossing is a market town at the confluence of tw / - Iron coin (credits) is the universal currency on the merch / - The road has been quieter than usual this season — fewer c` |
| narrate + scene | 1 | `A market town built around the confluence of two rivers. Cob / timber-framed buildings, and the constant sound of water fro / town square has a stone well and a statue of the founder. Mo` |
