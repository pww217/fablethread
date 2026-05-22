"""momentum_high — Starts with momentum={MOMENTUM_MAX}.

Verifies narration tone reflects opportunity, not struggle, when momentum
is at its maximum. All momentum values derive from engine_mirror constants.
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert
from ccya.eval.engine_mirror import MOMENTUM_MAX


scenario = Scenario(
    id="momentum_high",
    pack="eval-pack",
    description=f"Starts with momentum={MOMENTUM_MAX}. Verifies narration tone reflects opportunity, not struggle.",
    seed_overrides={"meta.momentum": MOMENTUM_MAX},
    turns=[
        Turn(
            input="I walk up to Caron confidently and tell him the debt is settled before he can speak.",
            phase="high_momentum_social",
            expects=[
                f"Narrate should reflect HIGH MOMENTUM advisory from narrate_user.j2 (momentum={MOMENTUM_MAX})",
                "Raised stakes or elevated consequence expected in narration",
            ],
            asserts=[TurnAssert(stream="ruling", field="rolled", expected="true")],
        ),
        Turn(
            input="I pocket the ledger receipt and head for the door without looking back.",
            phase="momentum_maintained",
            expects=["momentum should remain elevated unless roll fails"],
        ),
        Turn(
            input="I try to fast-talk the innkeeper into giving me a free room for the night.",
            phase="momentum_spend",
            expects=[
                "rules.required=true skill=charisma",
                "difficulty should reflect favorable conditions given high momentum",
            ],
            asserts=[TurnAssert(stream="ruling", field="rolled", expected="true")],
        ),
    ],
)
