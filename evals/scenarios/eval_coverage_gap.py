"""eval_coverage_gap — 8-turn scenario exercising ev1 findings.

Exercises: band-beat conflict, thread update urgency, orphan conditions,
surface_as drift, and skill variety. Relies on universal asserts from Phase 1
for much of the coverage.

Turns:
  T1: No-roll dialogue (establish scene)
  T2: Fail/setback roll — pressure beat is NOT expected (per prompt guidance)
  T3: No-roll with thread_update — urgency should change
  T4: Success/crit_success roll — escalation beat IS expected
  T5: Partial roll with orphan condition
  T6: Breathe directive — breathing_room surface_as=environmental
  T7: Breathe directive — breathing_room surface_as=ambient (surface drift trigger)
  T8: Different skill roll
"""

from ccya.eval.scenario import Scenario, Turn, TurnAssert


scenario = Scenario(
    id="eval_coverage_gap",
    pack="eval-pack",
    description="8-turn scenario exercising ev1 findings: band-beat conflict, thread updates, orphan conditions, surface_as patterns, and skill variety.",
    seed_overrides={
        "arc.threads": [
            {
                "id": "siege_preparations",
                "summary": "The village is stockpiling weapons and fortifying the eastern wall against an expected attack.",
                "scope": "arc",
                "urgency": "normal",
            }
        ]
    },
    turns=[
        Turn(
            input="I survey the village from the central square, taking note of the fortifications being built.",
            phase="establish_scene",
            expects=[
                "no roll (pure observation)",
                "arc thread siege_preparations should be visible in narrate context",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        Turn(
            input="I climb the eastern wall to inspect the fortifications, but my footing slips on loose stones.",
            phase="fail_setback_roll",
            expects=[
                "rules.required=true (risky action with clear obstacle)",
                "fail or setback band should NOT produce pressure/complication beat per prompt guidance",
                "if fail is near-miss (total >= 6), complication beat is allowed (near-miss exception)",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
        Turn(
            input="I find the foreman and ask how preparations are going.",
            phase="thread_update_dialogue",
            expects=[
                "no roll (dialogue, no obstacle)",
                "storytell may emit thread_update=siege_preparations — urgency change or summary update",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        Turn(
            input="I rally the workers at the eastern wall, leading by example to reinforce the weakest section.",
            phase="success_roll",
            expects=[
                "rules.required=true skill=strength or charisma (leadership by example)",
                "success or crit_success band — escalation beat IS expected (momentum gain creates opportunity)",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
        Turn(
            input="I inspect the supply stockpile to verify we have enough materials.",
            phase="partial_roll_with_condition",
            expects=[
                "rules.required=true skill=wits (inspection/investigation)",
                "partial outcome expected — succeed but at a cost",
                "condition may be added — orphan condition assert will fire if condition lacks CONDITION_MODS entry",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
        Turn(
            input="I take a moment to sit on a crate and breathe, watching the village go about its business.",
            phase="breathe_directive_environmental",
            expects=[
                "low momentum should trigger Breathe directive",
                "breathing_room beat with surface_as=environmental expected",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        Turn(
            input="I walk to the well and sit in the shade, letting the sounds of the village wash over me.",
            phase="breathe_directive_ambient",
            expects=[
                "Breathe directive continues (momentum still low)",
                "breathing_room beat with surface_as=ambient — if previous turn was environmental, this triggers surface_as drift detection",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="false"),
            ],
        ),
        Turn(
            input="I study the old battle maps in the village hall, looking for tactical advantages.",
            phase="different_skill_roll",
            expects=[
                "rules.required=true skill=wits (tactical analysis, perception under pressure)",
                "uses a different skill than previous turns for skill variety coverage",
            ],
            asserts=[
                TurnAssert(stream="ruling", field="rolled", expected="true"),
            ],
        ),
    ],
)
