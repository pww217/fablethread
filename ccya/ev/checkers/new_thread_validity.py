from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "new_thread_validity", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="thread_add entries have id/summary, no duplicates",
)
def new_thread_validity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for ev in events:
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        thread_add = storytell_output.get("thread_add")

        if not isinstance(thread_add, dict):
            continue

        tid = thread_add.get("id")
        if not tid or not isinstance(tid, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "thread_add_has_id",
                "detail": "thread_add missing or invalid id",
            })
            all_passed = False
            continue

        summary = thread_add.get("summary")
        if not summary or not isinstance(summary, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "thread_add_has_summary",
                "detail": f"thread id={tid!r} missing or invalid summary",
            })
            all_passed = False

        # Check no duplicate thread ids in state
        snap = extract_field(ev, "state_snapshot") or {}
        arc = snap.get("long_term_objective") or {}
        thread_ids = [
            t.get("id") for t in (arc.get("threads") or [])
            if isinstance(t, dict) and t.get("id") == tid
        ]
        if len(thread_ids) > 1:
            findings.append({
                "turn": ev.get("turn"),
                "check": "thread_add_no_duplicate",
                "detail": f"thread id={tid!r} appears multiple times in state after add",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="new_thread_validity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="new_thread_validity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
