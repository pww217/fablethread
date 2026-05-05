"""full_cycle — exercises dialogue, combat, quest progression in one run.

Designed against eval-pack's mid-game seed (turn=12). The arc:
  1. dialogue with Halden (no roll, no inventory change)
  2. attempt to bandage Halden — partial success — uses 2 bandages
  3. confront the toughs — combat, strength check
  4. take a hit — likely setback — adds a condition
  5. pay them off — charisma + credits — quest objective progresses
  6. hand the ledger to Halden — completes deliver_the_ledger objective

Expected emergent observations the judge / report should surface:
  - rules call should fire on turns 2, 3, 4, 5 (skill checks)
  - extract.state should remove inventory on turns 2 and 5
  - extract.progress should mark quest objectives done on turns 5 and 6
  - context_economy: by turn 6, recent_events shouldn't have ballooned
"""

from ccya.eval.scenario import Scenario, Turn


scenario = Scenario(
    id="full_cycle",
    pack="eval-pack",
    description="Six-turn arc: dialogue → bandage → confront → take hit → pay off → deliver.",
    turns=[
        Turn(
            input="Walk over to Halden's table and sit down across from him.",
            phase="dialogue",
            expects=[
                "rules.required=false (pure social, no obstacle)",
                "scope skips inventory and pc_condition",
                "extract.state should be near-empty",
            ],
        ),
        Turn(
            input="Tear open two bandages and wrap the gash on Halden's forearm before the bleeding gets worse.",
            phase="first_aid",
            expects=[
                "rules.required=true skill=wits|dexterity",
                "extract.state.inventory_remove includes bandages amount=2",
                "extract.scene.present_npcs still includes halden",
            ],
        ),
        Turn(
            input="Stand up, square my shoulders, and walk straight toward the bald tough at the door.",
            phase="combat_engage",
            expects=[
                "rules.required=true skill=strength|charisma",
                "scope active_domains includes pc_condition",
                "narration honors the rules band",
            ],
        ),
        Turn(
            input="Take the punch on the ribs and grab the bald tough's wrist before he can pull a knife.",
            phase="combat_take_hit",
            expects=[
                "rules.required=true skill=strength",
                "extract.state likely adds a pc_condition (cracked_ribs, winded, or similar)",
                "extract.state should NOT add bruised_ribs again (it already exists)",
            ],
        ),
        Turn(
            input="Drop a stack of 200 credits onto the table by the door and tell the toughs Caron's coin is paid; they can leave now.",
            phase="payoff",
            expects=[
                "rules.required=true skill=charisma",
                "extract.state.inventory_remove includes credits amount=200",
                "extract.progress.quest_updates marks 'Convince, pay, or remove the toughs' done",
            ],
        ),
        Turn(
            input="Sit back down across from Halden, slide the merchant seal across the table, and hand him the ledger from my coat.",
            phase="quest_complete",
            expects=[
                "extract.progress marks deliver_the_ledger objectives done",
                "auto_complete should fire — quest status should become completed",
                "extract.scene mentions both halden and the seal/ledger",
            ],
        ),
    ],
)
