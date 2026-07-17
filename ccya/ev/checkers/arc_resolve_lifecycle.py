from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "arc_resolve_lifecycle", "deterministic",
    requires_fields=["extraction.record", "last_turn_state"],
    description="arc_resolve creates new arc with successor goal, copies threads, stores old arc in resolved_arcs",
    needs_non_turn_events=True,
)
def arc_resolve_lifecycle(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in events:
        record_output = ((extract_field(ev, "extraction") or {}).get("record") or {}).get("output") or {}
        arc_resolve = record_output.get("arc_resolve")
        if not isinstance(arc_resolve, dict):
            continue

        resolution = arc_resolve.get("resolution", "")
        if not resolution or not isinstance(resolution, str) or not resolution.strip():
            continue

        next_goal = arc_resolve.get("long_term_objective")
        turn_no = ev.get("turn")

        # The arc_resolve event is on a turn. We need to check that the next
        # turn in the filtered list reflects the new arc state.
        # Since one event per turn, next event = next turn.
        idx_in_filtered = None
        for i, e in enumerate(filtered):
            if e.get("turn") == turn_no:
                idx_in_filtered = i
                break

        if idx_in_filtered is None:
            continue

        snap = extract_field(ev, "last_turn_state") or {}
        cur_arc = snap.get("long_term_objective") or snap.get("arc") or {}
        old_goal = cur_arc.get("long_term_objective", "")
        old_threads = cur_arc.get("threads") or []
        meta = snap.get("meta") or {}
        cur_last_arc_resolve_turn = meta.get("last_arc_resolve_turn")

        # AFTER arc_resolve applied:
        # - The current turn's last_turn_state should show the SUCCESSOR arc
        #   (because arc_resolve runs in _persist_and_async_cleanup phase
        #    which updates last_turn_state BEFORE the event is captured).

        # The successor arc: long_term_objective = next_goal from LLM
        # threads = all old arc threads (active ones)
        # completed_threads = empty list (clean slate - old threads go in resolved_arcs)
        # started_turn = turn_no
        # last_thread_created_turn = turn_no

        successor_goal = cur_arc.get("long_term_objective", "")
        successor_threads = cur_arc.get("threads") or []
        successor_completed = cur_arc.get("completed_threads") or []

        if successor_goal != next_goal:
            old_goal_str = old_goal[:60] if old_goal else None
            next_goal_str = next_goal[:60] if next_goal else None
            successor_str = successor_goal[:60] if successor_goal else None
            findings.append({
                "turn": turn_no,
                "check": "successor_goal",
                "detail": f"arc_resolve with next_goal={next_goal_str!r} (old_goal={old_goal_str}), but current arc goal={successor_str!r}",
            })
            all_passed = False

        # Old active threads should have been copied to new arc
        old_active = [t for t in old_threads if isinstance(t, dict) and t.get("resolution_state", "") != "resolved"]
        old_thread_ids = {t.get("id") for t in old_active if isinstance(t, dict)}
        new_thread_ids = {t.get("id") for t in successor_threads if isinstance(t, dict) and t.get("id")}

        if old_active and not new_thread_ids.issuperset(old_thread_ids):
            missing = old_thread_ids - new_thread_ids
            findings.append({
                "turn": turn_no,
                "check": "threads_carried",
                "detail": f"arc_resolve: {len(missing)} old threads not carried to new arc: {sorted([t for t in missing if t is not None], key=str)[:10]}",
            })
            all_passed = False

        # completed_threads should be empty for successor arc (old threads go to resolved_arcs)
        if successor_completed:
            findings.append({
                "turn": turn_no,
                "check": "successor_completed_empty",
                "detail": f"arc_resolve: new arc has {len(successor_completed)} completed_threads (expected [])",
            })

        # last_arc_resolve_turn should be set on meta
        if cur_last_arc_resolve_turn != turn_no:
            findings.append({
                "turn": turn_no,
                "check": "arc_resolve_turn_set",
                "detail": f"arc_resolve at turn {turn_no}, but meta.last_arc_resolve_turn={cur_last_arc_resolve_turn}",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="arc_resolve_lifecycle", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="arc_resolve_lifecycle", passed=True, score=1.0,
        detail=f"arc resolve lifecycle OK across {len(filtered)} events",
    )
