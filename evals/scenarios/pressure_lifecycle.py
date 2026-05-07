"""pressure_lifecycle — Tests scene_pressure urgency escalation and expiry.

Seeds a BACKGROUND pressure at turn 1, verifies escalation to BUILDING
by turn 3-4, IMMEDIATE by turn 6, and expiry by turn 8 (max_turns reached).

All turn-number thresholds derive from engine_mirror constants, not
hardcoded values.
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert
from ccya.eval.engine_mirror import PRESSURE_BUILDING_AT, PRESSURE_IMMEDIATE_AT


scenario = Scenario(
    id="pressure_lifecycle",
    pack="eval-pack",
    description="Tests scene_pressure urgency escalation and expiry across 8 turns.",
    seed_overrides={
        "scene.scene_pressure": [
            {
                "id": "debt_collector_approaching",
                "text": "A debt collector is making inquiries in Marrow's Crossing.",
                "urgency": "background",
                "max_turns": 7,
            }
        ]
    },
    turns=[
        Turn(
            input="I ask Caron quietly whether anyone has been looking for me lately.",
            phase="pressure_seed_check",
            expects=[
                "scene_pressure should be visible in narrate context",
                "rules.required=false (social inquiry, no obstacle)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
        Turn(
            input="I spend the afternoon making discreet inquiries at the market.",
            phase="pressure_build_1",
            expects=[f"urgency should advance toward building (threshold: age {PRESSURE_BUILDING_AT})"],
        ),
        Turn(
            input="I try to get a full meal and rest at the inn before dealing with anything.",
            phase="breathing_room",
            expects=["no escalation forced — low-stakes action"],
        ),
        Turn(
            input="I duck into the alley behind the smithy when I hear heavy footsteps on the cobblestones.",
            phase="pressure_building",
            expects=[
                f"urgency should be building or immediate by now (building_at={PRESSURE_BUILDING_AT}, immediate_at={PRESSURE_IMMEDIATE_AT})",
                "scope should include pc_condition if physical",
            ],
            asserts=[
                TurnAssert(
                    stream="extract.scene",
                    field="scene_tags",
                    expected="combat",
                ),
            ],
        ),
        Turn(
            input="I confront the collector directly — I tell him the debt is settled and show him Caron's ledger mark.",
            phase="pressure_confront",
            expects=[
                "rules.required=true skill=charisma",
                "narration should reflect high urgency (IMMEDIATE)",
            ],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
            ],
        ),
        Turn(
            input="I watch the collector leave the square and wait ten minutes before moving.",
            phase="pressure_resolve_check",
            expects=[
                "pressure should be resolved or expired",
                "extract.progress should NOT re-add the same pressure",
            ],
        ),
        Turn(
            input="I head back to the inn and order a drink.",
            phase="post_pressure",
            expects=[
                "scene_pressure list should be empty or contain only new entries",
                "no ACTIVE THREATS in narrate context",
            ],
        ),
        Turn(
            input="I sit by the fire and check my inventory — count credits, check the ledger.",
            phase="cooldown",
            expects=["low-stakes, breathing room — no roll needed"],
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="false"),
            ],
        ),
    ],
)
