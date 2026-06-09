from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


def _is_hashable(v: Any) -> bool:
    return isinstance(v, (str, int, float, bool)) or v is None


@register_checker(
    "thread_lifecycle", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="thread_add applied, thread_update IDs valid",
)
def thread_lifecycle(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    for i, ev in enumerate(events):
        # thread_add applied
        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        thread_add = storytell_output.get("thread_add")
        if thread_add and isinstance(thread_add, dict):
            tid = thread_add.get("id")
            if tid and i + 1 < len(events):
                nxt = events[i + 1]
                nxt_arc = (extract_field(nxt, "state_snapshot") or {}).get("arc") or {}
                thread_ids: set[str] = set()
                for t in (nxt_arc.get("threads") or []):
                    if isinstance(t, dict) and t.get("id"):
                        thread_ids.add(t["id"])
                for t in (nxt_arc.get("completed_threads") or []):
                    if isinstance(t, dict) and t.get("id"):
                        thread_ids.add(t["id"])
                if tid not in thread_ids:
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "thread_add_applied",
                        "detail": f"thread added but never appeared in state: {tid}",
                    })
                    all_passed = False

        # thread_update IDs valid
        thread_updates = storytell_output.get("thread_update") or []
        if thread_updates:
            snap = extract_field(ev, "state_snapshot") or {}
            state_thread_ids = {
                t.get("id") for t in ((snap.get("arc") or {}).get("threads") or [])
                if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id")
            }
            bad = [t.get("id") for t in thread_updates
                   if isinstance(t, dict) and _is_hashable(t.get("id")) and t.get("id") not in state_thread_ids]
            if bad:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "thread_update_valid_id",
                    "detail": f"thread_update references unknown thread ID(s): {bad}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="thread_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="thread_lifecycle", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
