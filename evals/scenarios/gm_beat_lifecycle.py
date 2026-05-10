"""gm_beat_lifecycle — Verifies pending_gm_beat lifecycle.

Tests that:
1. extract.progress generates a pending_gm_beat
2. The beat appears in the next turn's narrate context
3. The beat is consumed (absent from state) by turn N+2

Uses state_yaml assertions to check state_snapshot for pending_gm_beat.
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert


scenario = Scenario(
    id="gm_beat_lifecycle",
    pack="eval-pack",
    description="Verifies pending_gm_beat is set by extract.progress, surfaced in next narration, and consumed.",
    turns=[
        Turn(
            input="I settle the debt with Caron.",
            phase="setup_1",
            asserts=[TurnAssert(stream="rules", field="rolled", expected="false")],
        ),
        Turn(
            input="I pay Caron the 500 credits and ask him to clear my name in the ledger.",
            phase="setup_2",
            asserts=[
                TurnAssert(stream="rules", field="rolled", expected="true"),
                TurnAssert(stream="extract.progress", field="quest_updates", expected="settle_the_debt"),
            ],
        ),
        Turn(
            input="I find Halden by the town well and offer to courier his ledger.",
            phase="gm_beat_trigger",
            expects=[
                "extract.progress should generate a pending_gm_beat here",
                "state_yaml.pending_gm_beat should be present after this turn",
                "beat_disposition should be present in progress extraction output",
            ],
            asserts=[
                TurnAssert(stream="extract.progress", field="beat_disposition"),
                TurnAssert(stream="state_yaml", field="pending_gm_beat.present"),
            ],
        ),
        Turn(
            input="I head east out of town on the merchant road.",
            phase="gm_beat_surface",
            expects=[
                "narrate should reflect the gm_beat instruction",
                "pending_gm_beat should be consumed after this turn (beat_disposition defaults to 'consume')",
            ],
            asserts=[
                TurnAssert(stream="state_yaml", field="pending_gm_beat.absent"),
            ],
        ),
        Turn(
            input="I keep moving, watching the road ahead.",
            phase="gm_beat_consumed",
            expects=["No pending_gm_beat should persist beyond 1 turn"],
            asserts=[
                TurnAssert(stream="state_yaml", field="pending_gm_beat.absent"),
            ],
        ),
    ],
)
