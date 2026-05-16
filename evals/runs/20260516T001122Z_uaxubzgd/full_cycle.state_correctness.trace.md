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
(not captured this run)
```

### Narrate System Prompt

```
(not captured this run)
```

### Extract Scene System Prompt

```
(not captured this run)
```

### Extract State System Prompt

```
(not captured this run)
```

### Extract Progress System Prompt

```
(not captured this run)
```


---

# TURN 1

**Input:** `Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.`

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

```

### Narration



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

```

### Narration



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

```

### Narration



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

*(none)*

### Context Telemetry

*(no telemetry)*

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

```

### Narration



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

*(none)*

### Context Telemetry

*(no telemetry)*

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

```

### Narration



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

```

### Narration



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

```

### Narration



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

```

### Narration



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

```

### Narration



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

*(none)*

### Context Telemetry

*(no telemetry)*

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

```

### Narration



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

*(none)*

### Context Telemetry

*(no telemetry)*

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

```

### Narration



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

```

### Narration



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

```

### Narration



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

- extract.progress: skipped

### State After Turn

```json
{}
```


---
# Deterministic Signals

## Auto-Checker Failures
| Turn | Assertion | Detail |
|---|---|---|
| 1 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Finally'] |
| 1 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 2 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 3 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 4 | `universal.location_change.applied` | location_change emitted but state.location.id unchanged: marrows_crossing_outskirts |
| 4 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 5 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 6 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 6 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 7 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Inside', 'Crossed'] |
| 7 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 8 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Inside', 'Crossed'] |
| 8 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 8 | `universal.narrate.pressure_directive_rendered` | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 9 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Inside'] |
| 9 | `universal.narrate.pressure_directive_rendered` | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 9 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 9 | `universal.narrate.pressure_directive_rendered` | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 10 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 10 | `universal.narrate.pressure_directive_rendered` | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 11 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Matthew', 'However', 'Estrada'] |
| 11 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 12 | `universal.location_change.applied` | location_change emitted but state.location.id unchanged: None |
| 12 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Halden'] |
| 12 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 12 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |
| 13 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Caron', 'Crossed', 'Linen'] |
| 13 | `universal.progress.actions_quality` | actions has 0 entries (expected 4) |

## Metrics
| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries | momentum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1786 | 5061 | 3398 | 4135 | 0 | 0 | 0 | — |
| 2 | 1799 | 5384 | 3728 | 4130 | 0 | 0 | 0 | — |
| 3 | 1789 | 5704 | 3822 | 4182 | 4248 | 1 | 1 | — |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 4 | 1735 | 5788 | 3798 | 4120 | 4189 | 0 | 0 | — |
| 5 | 1698 | 6254 | 3705 | 4153 | 0 | 0 | 0 | — |
| 6 | 1784 | 6428 | 3879 | 4176 | 0 | 0 | 0 | — |
| 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 7 | 1783 | 6131 | 3848 | 4118 | 0 | 0 | 0 | — |
| 8 | 1785 | 6624 | 3888 | 4214 | 0 | 0 | 0 | — |
| 9 | 1820 | 6686 | 4011 | 4247 | 4592 | 0 | 0 | — |
| 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 10 | 1824 | 6447 | 4041 | 4272 | 4653 | 1 | 1 | — |
| 11 | 1911 | 7112 | 4183 | 4323 | 0 | 0 | 0 | — |
| 12 | 1853 | 7164 | 4156 | 4299 | 0 | 0 | 0 | — |
| 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | — |
| 13 | 1757 | 6691 | 4102 | 4442 | 0 | 0 | 0 | — |

### Parse Error Details
**Turn 3** (1 error(s)):
- `2 validation errors for ProgressExtractResult
drift_analysis.0.thread_id
  Field required [type=missing, input_value={'match': True, 'reason':...ver_the_ledger thread.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
drift_analysis.1.thread_id
  Field required [type=missing, input_value={'match': False, 'reason'... than the road toughs.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing`
**Turn 10** (1 error(s)):
- `4 validation errors for ProgressExtractResult
drift_analysis.0.thread_id
  Field required [type=missing, input_value={'match': True, 'reason':... tension of the scene.'}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
drift_analysis.1.thread_id
  Field required [type=missing, input_value={'match': False, 'reason': ''}, input_type=dict]
    For further information visit https://errors.pydantic.dev/2.13/v/missing
drift_analysis.2.thread_id
  Field req`

**Scope fallback rate:** 0% (0/17 turns)
