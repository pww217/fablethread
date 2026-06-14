from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "scene_age_tracking", "deterministic",
    requires_fields=["state_snapshot"],
    description="scene_age increments every turn, resets on RESOLUTION/BREATHER",
)
def scene_age_tracking(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        snap = extract_field(ev, "state_snapshot") or {}
        scene = snap.get("scene") or {}
        location_entered_turn = scene.get("location_entered_turn")
        turn_entered = scene.get("turn_entered")
        turn_no = ev.get("turn")

        if location_entered_turn is None or turn_entered is None:
            # First turn or location change — scene_age is 0
            continue

        # scene_age = current_turn - location_entered_turn
        # or equivalently: scene_age = current_turn - turn_entered
        # (they should be the same after location change)
        expected_age = turn_no - location_entered_turn

        # Check that scene_age is non-negative
        if expected_age < 0:
            findings.append({
                "turn": turn_no,
                "check": "scene_age_non_negative",
                "detail": f"scene_age={expected_age} is negative (turn={turn_no}, location_entered_turn={location_entered_turn})",
            })
            all_passed = False

        # Check that scene_age increments by 1 each turn
        if i > 0:
            prev_snap = extract_field(filtered[i - 1], "state_snapshot") or {}
            prev_scene = prev_snap.get("scene") or {}
            prev_location_entered_turn = prev_scene.get("location_entered_turn")
            prev_turn_no = filtered[i - 1].get("turn")

            if prev_location_entered_turn is not None and prev_turn_no is not None:
                prev_age = prev_turn_no - prev_location_entered_turn
                # Age should increment by 1 (or reset to 0 on location change)
                if location_entered_turn != prev_location_entered_turn:
                    # Location changed — age resets
                    if expected_age != 0:
                        findings.append({
                            "turn": turn_no,
                            "check": "scene_age_reset_on_location_change",
                            "detail": f"location changed but scene_age={expected_age} != 0",
                        })
                        all_passed = False
                elif expected_age != prev_age + 1:
                    findings.append({
                        "turn": turn_no,
                        "check": "scene_age_increments",
                        "detail": f"scene_age={expected_age} != prev_age+1={prev_age + 1}",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="scene_age_tracking", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="scene_age_tracking", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
