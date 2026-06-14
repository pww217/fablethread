from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "tension_monotonicity", "deterministic",
    requires_fields=["ruling"],
    description="tension_delta values are valid and consistent with phase transitions",
)
def tension_monotonicity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for ev in filtered:
        ruling = extract_field(ev, "ruling") or {}
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        tension_delta = ruling.get("tension_delta")
        turn_no = ev.get("turn")

        # tension_delta should be present
        if tension_delta is None:
            findings.append({
                "turn": turn_no,
                "check": "tension_delta_present",
                "detail": "tension_delta field missing from ruling event",
            })
            all_passed = False
            continue

        # tension_delta should be a valid value
        valid_deltas = {"escalates", "maintains", "de-escalates"}
        if tension_delta not in valid_deltas:
            findings.append({
                "turn": turn_no,
                "check": "tension_delta_valid",
                "detail": f"tension_delta={tension_delta!r} not in {valid_deltas}",
            })
            all_passed = False

        # Phase consistency: de-escalates should not appear in CRISIS
        # (CRISIS should have escalates or maintains)
        if phase == "CRISIS" and tension_delta == "de-escalates":
            findings.append({
                "turn": turn_no,
                "check": "crisis_tension",
                "detail": "CRISIS phase with tension_delta=de-escalates (expected escalates or maintains)",
            })
            all_passed = False

        # Phase consistency: escalates should not appear in BREATHER
        if phase == "BREATHER" and tension_delta == "escalates":
            findings.append({
                "turn": turn_no,
                "check": "breather_tension",
                "detail": "BREATHER phase with tension_delta=escalates (expected maintains or de-escalates)",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="tension_monotonicity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="tension_monotonicity", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
