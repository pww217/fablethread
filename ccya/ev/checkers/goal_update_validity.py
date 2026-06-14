from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "goal_update_validity", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="goal_update is non-empty string, differs from previous visible_goal",
)
def goal_update_validity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for i, ev in enumerate(events):
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        goal_update = storytell_output.get("goal_update")

        if not goal_update or not isinstance(goal_update, str):
            continue

        # If this turn also resolved the arc, arc_resolve.visible_goal supersedes goal_update
        if storytell_output.get("arc_resolve"):
            continue

        # goal_update must be non-empty (already checked above)
        if not goal_update.strip():
            findings.append({
                "turn": ev.get("turn"),
                "check": "goal_update_non_empty",
                "detail": "goal_update is empty or whitespace-only",
            })
            all_passed = False
            continue

        # Verify goal_update differs from previous visible_goal
        # state_snapshot is captured pre-turn, so verify against next turn event's state
        next_i = i + 1
        while next_i < len(events) and "state_snapshot" not in events[next_i]:
            next_i += 1
        if next_i >= len(events):
            continue

        next_ev = events[next_i]
        next_arc = (extract_field(next_ev, "state_snapshot") or {}).get("arc") or {}
        next_visible_goal = next_arc.get("visible_goal", "")

        if goal_update == next_visible_goal:
            findings.append({
                "turn": ev.get("turn"),
                "check": "goal_update_differs",
                "detail": f"goal_update='{goal_update}' equals next turn's visible_goal (no change detected)",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="goal_update_validity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="goal_update_validity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
