from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "arc_goal_updates", "deterministic",
    requires_fields=["extraction.record", "last_turn_state"],
    description="goal_update overwrites long_term_objective",
)
def arc_goal_updates(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        record_output = ((extract_field(ev, "extraction") or {}).get("record") or {}).get("output") or {}
        goal_update = record_output.get("goal_update")

        if not goal_update or not isinstance(goal_update, dict):
            continue

        goal_lto = goal_update.get("long_term_objective", "")

        # If this turn also resolved the arc, arc_resolve.long_term_objective supersedes goal_update
        if record_output.get("arc_resolve"):
            continue

        # last_turn_state is captured post-turn (after goal_update is applied),
        # so the current turn's last_turn_state already has the goal_update
        # reflected. Compare against the CURRENT turn's long_term_objective to verify
        # the engine applied the goal_update correctly.
        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        long_term_objective = arc.get("long_term_objective", "")

        if goal_lto != long_term_objective:
            findings.append({
                "turn": ev.get("turn"),
                "check": "goal_update_applied",
                "detail": f"record emitted goal_update.long_term_objective='{goal_lto}' at turn {ev.get('turn')}, but state's long_term_objective='{long_term_objective}'",
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
