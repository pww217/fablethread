from __future__ import annotations

import logging
from typing import Any

from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "convergence_ema", "deterministic",
    requires_fields=["pacing_context.convergence_score", "pacing_context.convergence_components"],
    description="Verify convergence score EMA smoothing is consistent across turns",
)
def convergence_ema(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    from ccya.engine.config import EngineConfig
    cfg = EngineConfig()
    alpha = cfg.convergence_alpha

    # Track smoothed values across turns to validate EMA relationship
    prev_smoothed = 0.0

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        convergence_score = pc.get("convergence_score")
        convergence_components = pc.get("convergence_components") or {}
        turn_no = ev.get("turn")

        if convergence_score is None or not convergence_components:
            continue

        raw_sum = sum(convergence_components.values())

        # Validate components exist and have correct keys
        valid_keys = {"urgent_thread", "threat_thread", "beat_streak", "roll_starvation", "threat_density"}
        invalid_keys = {k for k in convergence_components if k not in valid_keys}
        if invalid_keys:
            findings.append({
                "turn": turn_no,
                "check": "valid_component_keys",
                "detail": f"unexpected component keys: {sorted(invalid_keys)}",
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
        if convergence_score < 0 or convergence_score > 6:
            findings.append({
                "turn": turn_no,
                "check": "score_range",
                "detail": f"convergence_score={convergence_score} not in valid range [0,6]",
            })
            all_passed = False

        # EMA validation: smoothed = alpha * raw_sum + (1-alpha) * prev_smoothed
        # convergence_score stores int(smoothed)
        expected_smoothed = alpha * raw_sum + (1 - alpha) * prev_smoothed
        expected_int = int(expected_smoothed)

        if convergence_score != expected_int:
            findings.append({
                "turn": turn_no,
                "check": "ema_smoothed",
                "detail": f"expected int(smoothed)={expected_int}, got {convergence_score} (raw={raw_sum}, prev_smoothed={prev_smoothed:.2f}, smoothed={expected_smoothed:.2f})",
            })
            all_passed = False

        prev_smoothed = expected_smoothed

    if not all_passed:
        return CheckerResult(
            checker_id="convergence_ema", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="convergence_ema", passed=True, score=1.0,
        detail=f"convergence EMA validation OK across {len(filtered)} events",
    )
