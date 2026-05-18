"""pressure_lifecycle — Tests unified ArcThread scope-aware expiration across 8 turns.

Seeds a scene-scoped thread at turn 1, verifies it persists while location unchanged,
expires on location change (turn 4), then seeds an arc-scoped thread that persists
across locations until aged out via age-based demotion rules.

All thresholds derive from engine_mirror constants:
- THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE=True
- THREAD_ARC_DEMOTE_AGE=8 turns idle for active→False demotion
"""

from ccya.eval.scenario import Scenario, Turn


scenario = Scenario(
    id="pressure_lifecycle",
    pack="eval-pack",
    description="Tests unified ArcThread scope-aware expiration across 8 turns. Scene-scoped thread expires on location change; arc-scoped thread persists across locations.",
    seed_overrides={
        "arc.threads": [
            {
                "id": "debt_collector_approaching",
                "summary": "A debt collector is making inquiries in Marrow's Crossing.",
                "scope": "scene",
                "urgency": "background",
            }
        ]
    },
    turns=[
        Turn(
            input="I ask Caron quietly whether anyone has been looking for me lately.",
            phase="thread_seed_check",
            expects=[
                "arc.threads should include debt_collector_approaching (scope=scene) in narrate context",
                "rules.required=false (social inquiry, no obstacle)",
            ],
            asserts=[],
        ),
        Turn(
            input="I spend the afternoon making discreet inquiries at the market.",
            phase="thread_persists_unchanged_location",
            expects=[
                "scene-scoped thread should still be active — location unchanged from turn 1",
                "no expiration triggered (location_change=False)",
            ],
        ),
        Turn(
            input="I try to get a full meal and rest at the inn before dealing with anything.",
            phase="breathing_room",
            expects=[
                "scene-scoped thread still persists — location unchanged, no resolution in narration",
                "no escalation forced — low-stakes action",
            ],
        ),
        Turn(
            input="I duck into the alley behind the smithy when I hear heavy footsteps on the cobblestones.",
            phase="location_change_expire_scene_thread",
            expects=[
                "scene-scoped thread debt_collector_approaching should expire — location changed from Marrow's Crossing to alley/smithy area",
                "arc.threads[] in state snapshot should NOT include expired scene-scoped threads",
                "narration should reflect the new tension (footsteps approaching)",
            ],
        ),
        Turn(
            input="I confront whoever is following me — I tell them I'm not interested in trouble.",
            phase="arc_thread_persists_across_location",
            expects=[
                "rules.required=true skill=charisma",
                "an arc-scoped thread should be visible (created by Progress during this turn or previous)",
                "PacingContext.directive should reflect the confrontation context",
            ],
        ),
        Turn(
            input="I watch whoever I confronted leave and wait ten minutes before moving.",
            phase="arc_thread_persists_no_resolution",
            expects=[
                "arc-scoped thread should still be in arc.threads[] — no location change for scene threads, but this is scope=arc so it persists",
                "thread should not have expired yet (age-based demotion requires >=8 idle turns)",
            ],
        ),
        Turn(
            input="I head back to the inn and order a drink.",
            phase="location_change_no_effect_on_arc_thread",
            expects=[
                "arc-scoped thread persists across location change — only scope=scene threads expire on location change",
                "new scene-scoped threads may be created for new tensions in this location",
            ],
        ),
        Turn(
            input="I sit by the fire and check my inventory — count credits, check what I have.",
            phase="cooldown",
            expects=[
                "low-stakes, breathing room — no roll needed",
                "arc.threads[] should contain only threads that are still relevant (no expired scene-scoped threads)",
            ],
        ),
    ],
)
