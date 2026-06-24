from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker

_log = logging.getLogger(__name__)


@register_checker(
    "sanitizer_lifecycle", "deterministic",
    requires_fields=[],
    # Note: engine never emits 'threads_removed' — it moves threads to completed_threads[] instead
    needs_non_turn_events=True,
    needs_state=True,
    description="Verify sanitizer thread operations are valid against state at each sanitizer turn",
)
def sanitizer_lifecycle(events: list[dict[str, Any]], state: dict[str, Any]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    sanitizer_events = [ev for ev in events if ev.get("kind") == "sanitizer"]

    if not sanitizer_events:
        return CheckerResult(
            checker_id="sanitizer_lifecycle", passed=True, score=1.0,
            detail="no sanitizer events found (vacuously true)",
        )

    # Build turn number → state snapshot map from turn events
    turn_states: dict[int, dict[str, Any]] = {}
    for ev in events:
        ts = ev.get("turn")
        if ts is not None and "state_snapshot" in ev:
            turn_states[ts] = ev["state_snapshot"]

    for sev in sanitizer_events:
        sev_turn = sev.get("turn")
        # Get state at this sanitizer's turn, or fall back to END state
        if sev_turn and sev_turn in turn_states:
            arc = (turn_states[sev_turn].get("long_term_objective") or {})
        else:
            arc = state.get("long_term_objective") or {}

        state_threads: dict[str, dict[str, Any]] = {}
        for t in arc.get("threads") or []:
            if isinstance(t, dict) and t.get("id"):
                state_threads[t["id"]] = t

        # threads_updated IDs exist in state.arc.threads at this turn
        for tid in (sev.get("threads_updated") or []):
            if tid not in state_threads:
                findings.append({
                    "check": "threads_updated_exist",
                    "detail": f"threads_updated references non-existent thread ID: {tid}",
                    "event_index": sev_turn,
                })
                all_passed = False

        # threads_resolved threads exist in state.arc.threads at this turn
        for tid in (sev.get("threads_resolved") or []):
            if tid not in state_threads:
                findings.append({
                    "check": "threads_resolved_exist",
                    "detail": f"threads_resolved references non-existent thread ID: {tid}",
                    "event_index": sev_turn,
                })
                all_passed = False

        # threads_added IDs don't conflict with existing threads at this turn
        for tid in (sev.get("threads_added") or []):
            if tid in state_threads:
                findings.append({
                    "check": "threads_added_conflict",
                    "detail": f"threads_added ID '{tid}' conflicts with existing thread",
                    "event_index": sev_turn,
                })
                all_passed = False

        # goal_changed: verify changes_detail.goal.after != changes_detail.goal.before
        if sev.get("goal_changed"):
            changes_detail = sev.get("changes_detail") or {}
            goal_changes = changes_detail.get("goal") or {}
            if goal_changes.get("after") == goal_changes.get("before"):
                findings.append({
                    "check": "goal_changed_noop",
                    "detail": "goal_changed=True but after == before",
                    "event_index": sev_turn,
                })
                all_passed = False

    if not all_passed:
        result = CheckerResult(
            checker_id="sanitizer_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
        return result

    return CheckerResult(
        checker_id="sanitizer_lifecycle", passed=True, score=1.0,
        detail=f"all {len(sanitizer_events)} sanitizer events passed",
    )
