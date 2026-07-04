from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "goal_update_validity", "deterministic",
    requires_fields=["extraction.record", "last_turn_state"],
    description="goal_update is non-empty string, differs from previous long_term_objective",
)
def goal_update_validity(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    prev_snap: dict[str, Any] | None = None

    for ev in events:
        # Capture the previous turn's last_turn_state before updating.
        # last_turn_state is captured post-turn (after goal_update is applied),
        # so the current turn's last_turn_state already has the goal_update
        # reflected. We need the PREVIOUS turn's long_term_objective to verify the
        # goal_update actually changed something.
        prev_snap_for_this = prev_snap
        if "last_turn_state" in ev:
            prev_snap = ev["last_turn_state"]

        record_output = ((extract_field(ev, "extraction") or {}).get("record") or {}).get("output") or {}
        goal_update = record_output.get("goal_update")

        if not goal_update or not isinstance(goal_update, dict):
            continue

        goal_lto = goal_update.get("long_term_objective", "")

        # If this turn also resolved the arc, arc_resolve.long_term_objective supersedes goal_update
        if record_output.get("arc_resolve"):
            continue

        # goal_update must be non-empty (already checked above)
        if not goal_lto.strip():
            findings.append({
                "turn": ev.get("turn"),
                "check": "goal_update_non_empty",
                "detail": "goal_update.long_term_objective is empty or whitespace-only",
            })
            all_passed = False
            continue

        # Verify goal_update differs from the previous turn's long_term_objective.
        # prev_snap_for_this holds the previous turn's last_turn_state, which
        # is the pre-goal_update state for this turn.
        prev_arc = (prev_snap_for_this or {}).get("arc") or {}
        prev_long_term_objective = prev_arc.get("long_term_objective", "")

        if goal_lto == prev_long_term_objective:
            findings.append({
                "turn": ev.get("turn"),
                "check": "goal_update_differs",
                "detail": f"goal_update.long_term_objective='{goal_lto}' equals previous turn's long_term_objective (no change)",
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
