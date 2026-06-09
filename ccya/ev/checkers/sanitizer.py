from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker

_log = logging.getLogger(__name__)


@register_checker(
    "sanitizer_lifecycle", "deterministic",
    requires_fields=["threads_updated", "threads_removed", "threads_resolved",
                    "threads_added", "goal_changed", "changes_detail"],
    needs_non_turn_events=True,
    needs_state=True,
    description="Verify sanitizer thread operations are valid against current state",
)
def sanitizer_lifecycle(events: list[dict[str, Any]], state: dict[str, Any]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    sanitizer_events = [ev for ev in events if ev.get("kind") == "sanitizer"]

    if not sanitizer_events:
        return CheckerResult(
            checker_id="sanitizer_lifecycle", passed=None, score=None,
            detail="no sanitizer events found (inconclusive)",
        )

    state_threads = {}
    state_arc = state.get("arc") or {}
    for t in state_arc.get("threads") or []:
        if isinstance(t, dict) and t.get("id"):
            state_threads[t["id"]] = t

    for sev in sanitizer_events:
        # threads_updated IDs exist in state.arc.threads
        for tid in (sev.get("threads_updated") or []):
            if tid not in state_threads:
                findings.append({
                    "check": "threads_updated_exist",
                    "detail": f"threads_updated references non-existent thread ID: {tid}",
                    "event_index": sev.get("turn"),
                })
                all_passed = False

        # threads_removed IDs exist in state.arc.threads (before removal)
        for tid in (sev.get("threads_removed") or []):
            if tid not in state_threads:
                findings.append({
                    "check": "threads_removed_exist",
                    "detail": f"threads_removed references non-existent thread ID: {tid}",
                    "event_index": sev.get("turn"),
                })
                all_passed = False

        # threads_resolved threads have resolution data
        for tid in (sev.get("threads_resolved") or []):
            if tid not in state_threads:
                findings.append({
                    "check": "threads_resolved_exist",
                    "detail": f"threads_resolved references non-existent thread ID: {tid}",
                    "event_index": sev.get("turn"),
                })
                all_passed = False

        # threads_added IDs don't conflict with existing threads
        for tid in (sev.get("threads_added") or []):
            if tid in state_threads:
                findings.append({
                    "check": "threads_added_conflict",
                    "detail": f"threads_added ID '{tid}' conflicts with existing thread",
                    "event_index": sev.get("turn"),
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
                    "event_index": sev.get("turn"),
                })
                all_passed = False

    # Check for orphan threads — threads in state that aren't referenced by any sanitizer event
    referenced_ids: set[str] = set()
    for sev in sanitizer_events:
        referenced_ids.update(sev.get("threads_updated") or [])
        referenced_ids.update(sev.get("threads_removed") or [])
        referenced_ids.update(sev.get("threads_resolved") or [])

    orphan_ids = set(state_threads.keys()) - referenced_ids

    if not all_passed:
        result = CheckerResult(
            checker_id="sanitizer_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
        if orphan_ids:
            result.findings.append({
                "check": "orphan_threads",
                "detail": f"threads in state never referenced by sanitizer events: {sorted(orphan_ids)}",
            })
        return result

    return CheckerResult(
        checker_id="sanitizer_lifecycle", passed=True, score=1.0,
        detail=f"all {len(sanitizer_events)} sanitizer events passed" + (
            f"; {len(orphan_ids)} unreferenced threads" if orphan_ids else ""
        ),
    )
