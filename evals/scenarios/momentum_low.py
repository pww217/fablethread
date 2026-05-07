"""momentum_low — Starts with momentum={MOMENTUM_MIN}.

Verifies the engine offers small breaks per narrate_user.j2 advisory when
momentum is at its minimum. All momentum values derive from engine_mirror.
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert
from ccya.eval.engine_mirror import MOMENTUM_MIN


scenario = Scenario(
    id="momentum_low",
    pack="eval-pack",
    description=f"Starts with momentum={MOMENTUM_MIN}. Verifies engine offers small breaks per narrate_user.j2 advisory.",
    seed_overrides={"meta.momentum": MOMENTUM_MIN},
    turns=[
        Turn(
            input="I try to reason with Caron. Tell him I can get the money by nightfall.",
            phase="low_momentum_plea",
            expects=[
                f"Narrate should reflect LOW MOMENTUM advisory (momentum={MOMENTUM_MIN})",
                "Small break or partial success expected — not piling on",
            ],
            asserts=[TurnAssert(stream="rules", field="rolled", expected="true")],
        ),
        Turn(
            input="I accept whatever Caron says and leave the tavern quietly.",
            phase="low_momentum_exit",
            expects=["narration should not compound misery without reason"],
        ),
        Turn(
            input="I find a quiet corner and assess my options.",
            phase="low_momentum_recover",
            expects=[
                "rules.required=false (reflection, no obstacle)",
                "momentum should not drop further on no-roll turn",
            ],
            asserts=[TurnAssert(stream="rules", field="rolled", expected="false")],
        ),
    ],
)
