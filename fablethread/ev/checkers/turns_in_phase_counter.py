from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "turns_in_phase_counter", "deterministic",
    requires_fields=["pacing_context.scene_phase", "last_turn_state.scene"],
    description="Verify turns_in_phase starts at 1, increments by 1, resets on phase exit",
)
def turns_in_phase_counter(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        turn_no = ev.get("turn")

        snap = extract_field(ev, "last_turn_state") or {}
        scene = snap.get("scene") or {}
        turns_in_phase = scene.get("turns_in_phase", 0)

        if i == 0:
            # First event: turns_in_phase should be 1
            if turns_in_phase != 1:
                findings.append({
                    "turn": turn_no,
                    "check": "first_turn_starts_at_one",
                    "detail": f"first event: turns_in_phase={turns_in_phase} for phase={phase!r} (expected 1)",
                })
                all_passed = False
            continue

        prev_ev = filtered[i - 1]
        prev_pc = extract_field(prev_ev, "pacing_context") or {}
        prev_phase = prev_pc.get("scene_phase", "SETUP")
        prev_snap = extract_field(prev_ev, "last_turn_state") or {}
        prev_scene = prev_snap.get("scene") or {}
        prev_turns_in_phase = prev_scene.get("turns_in_phase", 0)

        # Same phase: should increment by 1
        if phase == prev_phase:
            expected = prev_turns_in_phase + 1
            if turns_in_phase != expected:
                findings.append({
                    "turn": turn_no,
                    "check": "same_phase_increments",
                    "detail": f"{phase}: turns_in_phase={turns_in_phase} != prev+1={expected}",
                })
                all_passed = False

        # Phase changed: should reset to 1
        elif phase != prev_phase:
            if turns_in_phase != 1:
                findings.append({
                    "turn": turn_no,
                    "check": "phase_change_resets",
                    "detail": f"phase changed {prev_phase}→{phase} but turns_in_phase={turns_in_phase} (expected 1)",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="turns_in_phase_counter", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="turns_in_phase_counter", passed=True, score=1.0,
        detail=f"turns_in_phase OK across {len(filtered)} events",
    )
