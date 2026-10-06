from __future__ import annotations

import logging
from typing import Any

from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "breather_enforcement", "deterministic",
    requires_fields=["pacing_context"],
    description="breather auto-transitions to RISING after breather_max_turns (default 3)",
)
def breather_enforcement(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    breather_max_turns = 3  # default from EngineConfig

    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        breather_count = pc.get("breather_turn_count", 0)
        turn_no = ev.get("turn")

        # breather_turn_count should only be > 0 when phase is BREATHER
        if phase != "BREATHER" and breather_count > 0:
            findings.append({
                "turn": turn_no,
                "check": "breather_count_zero_outside_breather",
                "detail": f"breather_turn_count={breather_count} but phase={phase!r} (expected 0 outside BREATHER)",
            })
            all_passed = False

        # breather should auto-transition to RISING after breather_max_turns
        if phase == "BREATHER" and breather_count >= breather_max_turns:
            # Check next turn — should be RISING
            if i + 1 < len(filtered):
                next_ev = filtered[i + 1]
                next_pc = extract_field(next_ev, "pacing_context") or {}
                next_phase = next_pc.get("scene_phase", "SETUP")
                if next_phase != "RISING":
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_auto_transition",
                        "detail": f"BREATHER with breather_turn_count={breather_count} >= {breather_max_turns} but next phase={next_phase!r} (expected RISING)",
                    })
                    all_passed = False

        # breather_turn_count should increment by 1 within BREATHER
        if i > 0:
            prev_pc = extract_field(filtered[i - 1], "pacing_context") or {}
            prev_phase = prev_pc.get("scene_phase", "SETUP")
            prev_breather_count = prev_pc.get("breather_turn_count", 0)

            if phase == "BREATHER" and prev_phase == "BREATHER":
                # Should increment by 1
                if breather_count != prev_breather_count + 1:
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_count_increments",
                        "detail": f"breather_turn_count={breather_count} != prev+1={prev_breather_count + 1}",
                    })
                    all_passed = False
            elif phase == "BREATHER" and prev_phase != "BREATHER":
                # Entering BREATHER — should be 1
                if breather_count != 1:
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_count_starts_at_one",
                        "detail": f"entering BREATHER but breather_turn_count={breather_count} (expected 1)",
                    })
                    all_passed = False
            elif phase != "BREATHER" and prev_phase == "BREATHER":
                # Exiting BREATHER — should reset to 0
                if breather_count != 0:
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_count_resets_on_exit",
                        "detail": f"exiting BREATHER but breather_turn_count={breather_count} (expected 0)",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="breather_enforcement", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="breather_enforcement", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )
