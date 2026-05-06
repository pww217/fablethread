"""full_cycle — 10-turn arc testing all mechanics across 4+ locations.

Starts peacefully in Marrow's Crossing, escalates through the road,
and ends with absurd edge cases. First 5 turns test core mechanics;
last 5 push boundaries.

All inputs are hard-coded for deterministic testing. The engine handles
mismatched assumptions gracefully (e.g. "talk to Caron" when he's not
there → engine narrates and moves on).

Designed for 10 turns. Use --turns 4 to test just the opening arc.

Expected emergent observations:
  - rules call fires on turns 2, 3, 5, 6, 7, 8, 9, 10
  - extract.state removes inventory on turns 2, 5, 8
  - extract.progress marks quest objectives done on turns 2, 3, 5
  - extract.scene shows location_change on turns 4, 6, 9
  - context_economy: recent_events shouldn't balloon by turn 10
  - scene_pressure should escalate across turns 7-10
  - momentum should swing based on band outcomes
  - compendium NPC bio should update on turns 3, 7, 10
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert


scenario = Scenario(
    id="full_cycle",
    pack="eval-pack",
    description="Peaceful start in Marrow's Crossing → debt settlement → courier contract → road travel → confrontation → absurd edge cases.",
    turns=[
        # --- Turn 1: Pure dialogue, no roll — quest: settle_the_debt ---
        Turn(
            input="Walk over to Caron's table and sit down across from him. I'm ready to talk about the debt.",
            phase="dialogue",
            expects=[
                "rules.required=false (pure social, no obstacle)",
                "scope skips inventory and pc_condition",
                "extract.state should be near-empty",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 2: Pay the debt — Cha check, inventory_remove credits, quest progress ---
        Turn(
            input="I slide 500 credits across the table to Caron and ask him to mark the debt cleared in his ledger.",
            phase="debt_settlement",
            expects=[
                "rules.required=true skill=charisma (social negotiation)",
                "extract.state.inventory_remove includes credits amount=500",
                "extract.progress marks settle_the_debt objectives done",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.state", field="inventory_remove", expected="credits", min_amount=500),
                TurnAssert(stream="extract.progress", field="quest_updates", expected="settle_the_debt"),
            ],
        ),
        # --- Turn 3: Accept courier contract — social, quest progress, NPC update ---
        Turn(
            input="I find Halden by the town well and offer to carry his ledger to the Crossed Keys Inn. I'll do it for 200 credits.",
            phase="quest_accept",
            expects=[
                "rules.required=true skill=charisma (negotiation)",
                "extract.progress marks deliver_the_ledger objectives done (accept contract)",
                "compendium_npc_update for halden",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.progress", field="quest_updates", expected="deliver_the_ledger"),
            ],
        ),
        # --- Turn 4: Location change — travel to the road ---
        Turn(
            input="I leave Marrow's Crossing by the east gate and head for the Crossed Keys Inn, following the merchant road.",
            phase="travel",
            expects=[
                "extract.scene.location_change to road or inn exterior",
                "scene_tags should include travel or exploration",
                "no rules call needed (pure movement)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
        # --- Turn 5: Encounter toughs — combat engagement, Strength/Cha check ---
        Turn(
            input="I walk up to the two toughs at the inn door and ask them what they're doing here. I'm not leaving until I hear their side.",
            phase="confrontation",
            expects=[
                "rules.required=true skill=strength|charisma (social combat)",
                "scope active_domains includes pc_condition",
                "scene_tags should include combat or social_conflict",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.scene", field="scene_tags", expected="combat"),
            ],
        ),
        # --- Turn 6: Pay off toughs — Cha + credits, quest progress ---
        Turn(
            input="I drop 200 credits on the ground between the toughs and tell them Caron's coin is paid — they can go home now.",
            phase="payoff",
            expects=[
                "rules.required=true skill=charisma",
                "extract.state.inventory_remove includes credits amount=200",
                "extract.progress marks clear_the_road_toughs done",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.state", field="inventory_remove", expected="credits", min_amount=200),
                TurnAssert(stream="extract.progress", field="quest_updates", expected="clear_the_road_toughs"),
            ],
        ),
        # --- Turn 7: Deliver ledger — quest completion, NPC update ---
        Turn(
            input="I sit across from Halden at his table, slide the merchant seal across, and hand him the ledger from my coat.",
            phase="quest_complete",
            expects=[
                "extract.progress marks deliver_the_ledger objectives done",
                "auto_complete should fire — quest status becomes completed",
                "compendium_npc_update for halden",
            ],
            asserts=[
                TurnAssert(stream="extract.progress", field="quest_updates", expected="deliver_the_ledger"),
            ],
        ),
        # --- Turn 8: Unconventional — try to use the brass key on the inn door ---
        Turn(
            input="I pull out the brass key Halden gave me and try to unlock the inn's front door with it. Maybe it opens a back room.",
            phase="unconventional_item_use",
            expects=[
                "rules.required=true skill=wits (investigation)",
                "extract.state.inventory_remove includes brass_key",
                "narration should honor the attempt even if it fails",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.state", field="inventory_remove", expected="brass_key"),
            ],
        ),
        # --- Turn 9: Absurd edge case — try to bribe a wall ---
        Turn(
            input="I press my ear against the inn's stone wall and whisper 'I have credits. Open up.' Then I offer a single credit to the wall.",
            phase="absurd_edge_case",
            expects=[
                "rules.required=true skill=charisma (absurd social attempt)",
                "narration should handle the absurdity without crashing",
                "extract.state should NOT remove credits (engine should reject or narrate failure)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.scene", field="scene_tags", expected="social"),
            ],
        ),
        # --- Turn 10: NPC development — confront Matthew Estrada, Cha check ---
        Turn(
            input="I approach Matthew Estrada at the bar, grab his wrist, and demand to know who he really is and why he's watching the room like a soldier.",
            phase="npc_development",
            expects=[
                "rules.required=true skill=charisma (aggressive social)",
                "compendium_npc_update for matthew_estrada",
                "narration should show character development or revelation",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
            ],
        ),
    ],
)
