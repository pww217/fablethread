from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "arc_goal_updates", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="goal_update overwrites visible_goal",
)
def arc_goal_updates(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        goal_update = storytell_output.get("goal_update")

        if not goal_update or not isinstance(goal_update, str):
            continue

        arc = (extract_field(ev, "state_snapshot") or {}).get("arc") or {}
        visible_goal = arc.get("visible_goal", "")

        if goal_update != visible_goal:
            findings.append({
                "turn": ev.get("turn"),
                "check": "goal_update_applied",
                "detail": f"storytell emitted goal_update='{goal_update}' but arc.visible_goal='{visible_goal}'",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="arc_goal_updates", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="arc_goal_updates", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
