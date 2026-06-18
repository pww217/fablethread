from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.checkers.thread_resolution_validity import _apply_sanitizer_changes_to_arc
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)


@register_checker(
    "arc_resolution_validity", "deterministic",
    requires_fields=["extraction.storytell", "state_snapshot"],
    description="arc_resolve has resolution + visible_goal, drop_threads reference existing threads",
)
def arc_resolution_validity(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    prev_snap: dict[str, Any] | None = None
    prev_sanitizer: dict[str, Any] | None = None

    for ev in events:
        # Capture the previous turn's state_snapshot before updating.
        # state_snapshot is captured post-turn, so it represents the arc state
        # AFTER this turn's processing — which is the pre-resolution state for
        # the NEXT turn's arc_resolve.
        prev_snap_for_this = prev_snap
        prev_sanitizer_for_this = prev_sanitizer
        if ev.get("kind") is None and "state_snapshot" in ev:
            prev_snap = ev["state_snapshot"]
        if ev.get("kind") == "sanitizer":
            prev_sanitizer = ev

        storytell_output = ((extract_field(ev, "extraction") or {}).get("storytell") or {}).get("output") or {}
        arc_resolve = storytell_output.get("arc_resolve")

        if not isinstance(arc_resolve, dict):
            continue

        # Skip empty arc_resolves (LLM sometimes emits empty dict)
        resolution = arc_resolve.get("resolution")
        if not resolution or not isinstance(resolution, str) or not resolution.strip():
            continue
        if not resolution or not isinstance(resolution, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "arc_resolve_has_resolution",
                "detail": "arc_resolve missing or invalid resolution",
            })
            all_passed = False

        visible_goal = arc_resolve.get("visible_goal")
        if not visible_goal or not isinstance(visible_goal, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "arc_resolve_has_visible_goal",
                "detail": "arc_resolve missing or invalid visible_goal",
            })
            all_passed = False

        goal_context = arc_resolve.get("goal_context")
        if not goal_context or not isinstance(goal_context, str):
            findings.append({
                "turn": ev.get("turn"),
                "check": "arc_resolve_has_goal_context",
                "detail": "arc_resolve missing or invalid goal_context",
            })
            all_passed = False

        # Check drop_threads reference existing threads in the arc BEFORE this turn's resolution.
        # prev_snap_for_this holds the previous turn's state_snapshot, which is the
        # pre-resolution state for this turn's arc_resolve.
        drop_threads = arc_resolve.get("drop_threads") or []
        if drop_threads:
            snap = prev_snap_for_this or {}
            # Reconstruct arc state by applying sanitizer changes from the previous turn.
            # This ensures we validate against the state the storyteller actually saw.
            snap = _apply_sanitizer_changes_to_arc(snap, prev_sanitizer_for_this)
            arc = snap.get("arc") or {}
            thread_ids = {
                t.get("id") for t in (arc.get("threads") or [])
                if isinstance(t, dict) and t.get("id")
            }

            for tid in drop_threads:
                if tid not in thread_ids:
                    findings.append({
                        "turn": ev.get("turn"),
                        "check": "drop_thread_exists",
                        "detail": f"arc_resolve.drop_threads references unknown thread id: {tid!r}",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="arc_resolution_validity", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="arc_resolution_validity", passed=True, score=1.0,
        detail=f"all {len(events)} turn events passed",
    )
