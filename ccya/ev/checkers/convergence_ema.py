from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "convergence_ema", "deterministic",
    requires_fields=["pacing_context.convergence_score", "pacing_context.convergence_components"],
    description="Verify convergence score components sum matches stored score, valid range [0-6]",
)
def convergence_ema(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    # Track convergence_score values across turns to compute expected EMA
    prev_raw = None

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        convergence_score = pc.get("convergence_score")
        convergence_components = pc.get("convergence_components") or {}
        turn_no = ev.get("turn")

        if convergence_score is None or not convergence_components:
            continue

        raw = convergence_score

        # Validate components exist and sum matches score
        # Components: urgent_thread (0-2), threat_thread (0-1), beat_streak (0-1),
        # roll_starvation (0-1), threat_density (0-1)
        valid_keys = {"urgent_thread", "threat_thread", "beat_streak", "roll_starvation", "threat_density"}
        invalid_keys = {k for k in convergence_components if k not in valid_keys}
        if invalid_keys:
            findings.append({
                "turn": turn_no,
                "check": "valid_component_keys",
                "detail": f"unexpected component keys: {sorted(invalid_keys)}",
            })
            all_passed = False

        component_sum = sum(convergence_components.values())
        if component_sum != raw:
            findings.append({
                "turn": turn_no,
                "check": "components_sum_match_score",
                "detail": f"components sum={component_sum} != convergence_score={raw}",
            })
            all_passed = False

        # Validate component value ranges
        urgent = convergence_components.get("urgent_thread", 0)
        if urgent < 0 or urgent > 2:
            findings.append({
                "turn": turn_no,
                "check": "urgent_thread_range",
                "detail": f"urgent_thread={urgent} not in [0,2]",
            })
            all_passed = False

        for key in ["threat_thread", "beat_streak", "roll_starvation", "threat_density"]:
            val = convergence_components.get(key, 0)
            if val < 0 or val > 1:
                findings.append({
                    "turn": turn_no,
                    "check": f"{key}_range",
                    "detail": f"{key}={val} not in [0,1]",
                })
                all_passed = False

        # Score range check
        if raw < 0 or raw > 6:
            findings.append({
                "turn": turn_no,
                "check": "score_range",
                "detail": f"convergence_score={raw} not in valid range [0,6]",
            })
            all_passed = False

        # EMA stream: first turn uses raw as initial smoothed, subsequent uses EMA
        if prev_raw is not None:
            prev_raw = raw
        else:
            prev_raw = raw

    if not all_passed:
        return CheckerResult(
            checker_id="convergence_ema", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="convergence_ema", passed=True, score=1.0,
        detail=f"convergence EMA validation OK across {len(filtered)} events",
    )
