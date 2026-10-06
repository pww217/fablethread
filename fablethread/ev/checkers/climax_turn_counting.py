from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "climax_turn_counting", "deterministic",
    requires_fields=["pacing_context"],
    description="climax_turn_count increments in CLIMAX, resets on phase exit",
)
def climax_turn_counting(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        climax_count = pc.get("climax_turn_count", 0)
        turn_no = ev.get("turn")

        # climax_turn_count should only be > 0 when phase is CLIMAX
        if phase != "CLIMAX" and climax_count > 0:
            findings.append({
                "turn": turn_no,
                "check": "climax_count_zero_outside_climax",
                "detail": f"climax_turn_count={climax_count} but phase={phase!r} (expected 0 outside CLIMAX)",
            })
            all_passed = False

        # climax_turn_count should increment by 1 within CLIMAX
        if i > 0:
            prev_pc = extract_field(filtered[i - 1], "pacing_context") or {}
            prev_phase = prev_pc.get("scene_phase", "SETUP")
            prev_climax_count = prev_pc.get("climax_turn_count", 0)

            if phase == "CLIMAX" and prev_phase == "CLIMAX":
                # Should increment by 1
                if climax_count != prev_climax_count + 1:
                    findings.append({
                        "turn": turn_no,
                        "check": "climax_count_increments",
                        "detail": f"climax_turn_count={climax_count} != prev+1={prev_climax_count + 1}",
                    })
                    all_passed = False
            elif phase == "CLIMAX" and prev_phase != "CLIMAX":
                # Entering CLIMAX — should be 1
                if climax_count != 1:
                    findings.append({
                        "turn": turn_no,
                        "check": "climax_count_starts_at_one",
                        "detail": f"entering CLIMAX but climax_turn_count={climax_count} (expected 1)",
                    })
                    all_passed = False
            elif phase != "CLIMAX" and prev_phase == "CLIMAX":
                # Exiting CLIMAX — should reset to 0
                if climax_count != 0:
                    findings.append({
                        "turn": turn_no,
                        "check": "climax_count_resets_on_exit",
                        "detail": f"exiting CLIMAX but climax_turn_count={climax_count} (expected 0)",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="climax_turn_counting", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="climax_turn_counting", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
