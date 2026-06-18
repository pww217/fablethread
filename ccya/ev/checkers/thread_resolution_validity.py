from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


def _apply_sanitizer_changes_to_arc(
    snap: dict[str, Any], sanitizer_ev: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply sanitizer thread changes to a state_snapshot's arc.

    The state_snapshot captured at the end of a turn doesn't include sanitizer
    changes (which run after the snapshot). This function reconstructs the arc
    state as it would appear after the sanitizer runs, so the checker can
    validate against the state the storyteller actually saw in the next turn.
    """
    if not sanitizer_ev:
        return snap

    snap = dict(snap)
    arc = dict(snap.get("arc") or {})
    threads = list(arc.get("threads") or [])
    completed = list(arc.get("completed_threads") or [])

    changes_detail = sanitizer_ev.get("changes_detail") or {}

    # Apply added threads
    for added in changes_detail.get("added") or []:
        if not isinstance(added, dict):
            continue
        tid = added.get("id")
        if not tid:
            continue
        # Don't duplicate
        if any(t.get("id") == tid for t in threads):
            continue
        threads.append({
            "id": tid,
            "summary": added.get("summary", ""),
            "urgency": added.get("urgency", "normal"),
            "active": True,
            "progress": [],
        })

    # Apply resolved threads (move from active to completed)
    for resolved in changes_detail.get("resolved") or []:
        if not isinstance(resolved, dict):
            continue
        tid = resolved.get("id")
        if not tid:
            continue
        # Remove from active threads
        threads = [t for t in threads if t.get("id") != tid]
        # Add to completed
        completed.append({
            "id": tid,
            "summary": "",
            "resolution_state": resolved.get("resolution_state", "resolved"),
            "outcome": resolved.get("outcome", ""),
        })

    # Apply updated threads (update progress)
    for tid, update in (changes_detail.get("updated") or {}).items():
        if not isinstance(update, dict):
            continue
        for t in threads:
            if t.get("id") == tid:
                progress = update.get("progress")
                if isinstance(progress, dict) and progress.get("after"):
                    t["progress"] = [
                        {"kind": p["kind"] if isinstance(p, dict) else "advancement", "text": p["text"] if isinstance(p, dict) else p}
                        for p in progress["after"]
                    ]
                urgency = update.get("fields")
                if isinstance(urgency, list):
                    for f in urgency:
                        if isinstance(f, dict) and f.get("field") == "urgency":
                            t["urgency"] = f.get("after", t.get("urgency", "normal"))
                break

    arc["threads"] = threads
    arc["completed_threads"] = completed
    snap["arc"] = arc
    return snap


@register_checker(
    "thread_resolution_validity", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="thread_resolve entries have valid id/resolution_state/outcome",
)
def thread_resolution_validity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    prev_snap: dict[str, Any] | None = None
    prev_sanitizer: dict[str, Any] | None = None

    for ev in events:
        # Capture the previous turn's state_snapshot before updating.
        # state_snapshot is captured post-turn (after thread_resolve moves threads
        # to completed_threads), so the resolved threads won't be in the current
        # arc's threads or completed_threads.
        prev_snap_for_this = prev_snap
        prev_sanitizer_for_this = prev_sanitizer
        if ev.get("kind") is None and "state_snapshot" in ev:
            prev_snap = ev["state_snapshot"]
        if ev.get("kind") == "sanitizer":
            prev_sanitizer = ev

        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        thread_resolves = storytell_output.get("thread_resolve") or []

        if not thread_resolves:
            continue

        snap = prev_snap_for_this or {}
        # Reconstruct arc state by applying sanitizer changes from the previous turn.
        # This ensures we validate against the state the storyteller actually saw.
        snap = _apply_sanitizer_changes_to_arc(snap, prev_sanitizer_for_this)
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
