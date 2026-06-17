from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "thread_resolution_validity", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="thread_resolve entries have valid id/resolution_state/outcome",
)
def thread_resolution_validity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    prev_snap: dict[str, Any] | None = None

    for ev in events:
        # Capture the previous turn's state_snapshot before updating.
        # state_snapshot is captured post-turn (after thread_resolve moves threads
        # to completed_threads), so the resolved threads won't be in the current
        # arc's threads or completed_threads.
        prev_snap_for_this = prev_snap
        if "state_snapshot" in ev:
            prev_snap = ev["state_snapshot"]

        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        thread_resolves = storytell_output.get("thread_resolve") or []

        if not thread_resolves:
            continue

        snap = prev_snap_for_this or {}
        arc = snap.get("arc") or {}
        thread_ids = {
            t.get("id") for t in (arc.get("threads") or [])
            if isinstance(t, dict) and t.get("id")
        }
        completed_ids = {
            t.get("id") for t in (arc.get("completed_threads") or [])
            if isinstance(t, dict) and t.get("id")
        }
        all_thread_ids = thread_ids | completed_ids

        for tr in thread_resolves:
            if not isinstance(tr, dict):
                continue

            tid = tr.get("id")
            if not tid:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "thread_resolve_has_id",
                    "detail": "thread_resolve entry missing id",
                })
                all_passed = False
                continue

            if tid not in all_thread_ids:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "thread_resolve_exists",
                    "detail": f"thread_resolve references unknown thread id: {tid!r}",
                })
                all_passed = False

            resolution_state = tr.get("resolution_state")
            valid_states = {"resolved", "failed", "abandoned"}
            if resolution_state not in valid_states:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "thread_resolve_valid_state",
                    "detail": f"thread_resolve id={tid!r} has invalid resolution_state={resolution_state!r} (expected one of {valid_states})",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_resolution_validity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_resolution_validity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
