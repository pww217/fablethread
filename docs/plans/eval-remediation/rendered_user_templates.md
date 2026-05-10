# Rendered Pipeline User Templates

All 5 pipeline user templates rendered with sample data.

---

## rules_user

```jinja2
{{% raw %}}
## pc
Kael Voss | Wounded mercenary
Stats: strength=4 agility=3 will=2
Conditions: wounded

## scene
Location: Crossed Keys Inn
## present_npcs (in scene right now)
- Caron (the broker) — wants payment

## last_turn (tail of the most recent narrative)
T5: I talk to Caron — You approach Caron at the corner table.

## Current Turn: 6
=== PLAYER INPUT ===
I want to negotiate with Caron.
=== END PLAYER INPUT ===

Emit the IntentEnvelope JSON only.
{{% endraw %}}
```

---

## narrate_user

```jinja2
{{% raw %}}
## Player Character
**Kael Voss** — Wounded mercenary
Stats: strength=4 agility=3 will=2
Conditions: wounded
## Location
Crossed Keys Inn (crossed_keys)
A dimly lit tavern
## Recently Left (do NOT write dialogue or action for these — may briefly acknowledge their departure)
- Old NPC (the bartender)
## inventory (cross-reference before describing item use)
- **pistol**: loaded

## Quests
- **Collect debt** [active]
  - [ ] Find Halden

<<<TRACE_IMMUTABLE_START>>>
## World State (immutable)
- {'id': 'halden_debt', 'text': 'Halden owes you 500 credits'}

<<<TRACE_IMMUTABLE_END>>>
## ACTIVE THREATS (must be reflected in narration)
- [IMMEDIATE] Toughs at the door
## Recent Events
- Met Caron

## Prior History (summarized — treat as background, not current scene)
T4: Player arrived at the inn.
## Recent Turns (most recent last — these are done, not current)
## RECENT TURNS
**Turn 5** — 
You talked to Caron about the debt.

## rules_outcome (BINDING — narrate this result; do NOT invert)
Charisma (2) | Difficulty: 
Roll: 3 + 4 -1 (cond) = 6 → PARTIAL
Directive: Success with cost.

GM DIRECTION (COMPLICATION, surface as ambient):
The toughs are getting impatient.
This is a backstage instruction, not player-visible narration. Integrate it naturally.

## Narration Directive



COMPLICATION: Partial success. They got something; something else got worse. One new wrinkle — not a catastrophe.






PRESSURE: Active immediate threat(s). Keep them present and felt.



## Known Characters
Before introducing anyone new, check this list. Re-use characters when they could plausibly be present.
- **Caron** — last seen Crossed Keys Inn: negotiating
## NPCs Present in Scene
- Caron (the broker) — wants payment
## Compendium Bios (rich identity data for NPCs you interact with)
- **Caron** (the broker) — A smooth-talking information broker with a network of informants.
<<<TRACE_IMMUTABLE_START>>>
## Known Factions
- **The Syndicate** (hostile)
<<<TRACE_IMMUTABLE_END>>>
<<<TRACE_IMMUTABLE_START>>>
## name_pool (use one of these when introducing a new named NPC)
**Male:** Dren · Kael · Mira
**Female:** Sera · Veyla

<<<TRACE_IMMUTABLE_END>>>
## Current Turn: ?
=== PLAYER INPUT ===
I negotiate with Caron.
=== END PLAYER INPUT ===
{{% endraw %}}
```

---

## extract_scene_user

```jinja2
{{% raw %}}
## Current Turn: 6

## pc
Kael Voss — Wounded mercenary
Stats: strength=4 agility=3
Conditions: wounded

## location
`crossed_keys` | Crossed Keys Inn
A dimly lit tavern

## present_npcs (currently in scene — emit npc_update for these if narration mentions them)
- `caron` | Caron (the broker) — wants payment

<<<TRACE_IMMUTABLE_START>>>
## known_characters (compendium — reuse `id` for npc_add/npc_update/compendium_npc_update)
- `caron` | Caron [broker,info] — smooth talker

<<<TRACE_IMMUTABLE_END>>>
## current_location_description (emit location_description only if narration adds NEW details)
Crossed Keys Inn - dimly lit, few patrons


## previous_turn_narration (T5 context)
You approached Caron at the corner table.

## CURRENT TURN NARRATION
You lean in close to Caron and lower your voice. 'I need to know who's behind the ledger theft.'
## END CURRENT TURN NARRATION
{{% endraw %}}
```

---

## extract_state_user

```jinja2
{{% raw %}}
## Current Turn: 6

## pc
Kael Voss — Wounded mercenary

## active_conditions
- `wounded` | wounded — hit

## inventory (current stacks — read amount before emitting `inventory_remove`)
- `pistol` | pistol ×1 — loaded

## scene_result
location: `crossed_keys`

## CURRENT TURN NARRATION
You lean in close to Caron and lower your voice. 'I need to know who's behind the ledger theft.'
## END CURRENT TURN NARRATION
{{% endraw %}}
```

---

## extract_progress_user

```jinja2
{{% raw %}}
## Current Turn: 6

## pc
Kael Voss — Wounded mercenary

## player_intent
attempt: negotiate
## quest_threshold
Close quests when objectives are met.

## active_quests
- `q1` | Collect debt
  objectives:
    1. [ ] Find Halden

## recent_events (don't duplicate; emit recent_events_add/update/remove for changes)
- Met Caron

## rules_stakes
Band: PARTIAL. At-risk cost named by rules engine: The toughs will break your legs if you don't pay.
## gm_beat (optional — leave null if nothing meaningful is ready)
Emit a gm_beat when the story arc genuinely calls for it — a named NPC reacts, a thread escalates, an offscreen consequence surfaces, a moment of relief is earned.
Do NOT emit a beat if this turn was routine action, minor dialogue, or you have nothing specific and concrete to say.

If `pending_beat` below is set and was not yet surfaced by the narrator, emit `beat_disposition: "carry"` and leave `gm_beat` null. If it should be replaced, emit `beat_disposition: "replace"` and a new `gm_beat`. Otherwise emit `beat_disposition: "consume"` (default).

## pending_beat (carried from previous turn — not yet surfaced)
Type: complication | Expires at turn: T7
Instruction: The toughs are getting impatient.
## scene_pressure_add (generate new threats from story causality only)
Add pressure when: a named NPC or faction acts against the player off-screen, a quest deadline triggers, a failed roll's stated consequence activates, or a world-state change creates a new threat.
Do NOT add pressure for things the narrator already described as resolved or for vague ambient danger. Prefer 0–1 new pressures per turn.
## quest_ages
- `q1`: 3 turns stalled

## Current Pressures
- [p1] (immediate) Toughs at the door

## last_turn_narration (T5 — context for this turn's outcome)
You talked to Caron about the debt.

## CURRENT TURN NARRATION
You lean in close to Caron and lower your voice. 'I need to know who's behind the ledger theft.'
## END CURRENT TURN NARRATION
{{% endraw %}}
```

---

