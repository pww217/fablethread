from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    ("SETUP", "RISING"),
    ("RISING", "CLIMAX"),
    ("CLIMAX", "RESOLUTION"),
    ("RESOLUTION", "BREATHER"),
    ("BREATHER", "RISING"),
}


@register_checker(
    "phase_transition", "deterministic",
    requires_fields=["pacing_context"],
    description="Validate phase engine transitions follow the state machine",
)
def phase_transition(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")

        # Check transitions (skip first turn)
        if i > 0:
            prev_ev = filtered[i - 1]
            prev_pc = extract_field(prev_ev, "pacing_context") or {}
            prev_phase = prev_pc.get("scene_phase", "SETUP")

            # Same phase is always valid (phase persists across turns)
            if prev_phase == phase:
                continue

            # All other transitions must be in VALID_TRANSITIONS
            if (prev_phase, phase) not in VALID_TRANSITIONS:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "valid_transition",
                    "detail": f"invalid phase transition: {prev_phase} → {phase}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="phase_transition", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="phase_transition", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
