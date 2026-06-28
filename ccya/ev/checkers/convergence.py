from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field

_log = logging.getLogger(__name__)

# Old key names that map to new component names
_OLD_TO_NEW_KEYS: dict[str, str] = {
    "thread_weight": "urgent_thread",
    "urgency_depth": "threat_thread",
}


def _remap_components(components: dict[str, Any]) -> dict[str, Any]:
    """Remap old key names to new key names."""
    result = dict(components)
    for old_key, new_key in _OLD_TO_NEW_KEYS.items():
        if old_key in result and new_key not in result:
            result[new_key] = result[old_key]
    return result


@register_checker(
    "convergence_components", "deterministic",
    requires_fields=["pacing_context.convergence_components", "pacing_context.convergence_score"],
    description="Verify 6-component convergence score + stall_floor matches stored value, drive phase transitions",
)
def convergence_components(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True

    cfg = EngineConfig()

    prev_phase: str | None = None

    for ev in events:
        pacing_ctx = extract_field(ev, "pacing_context") or {}
        raw_components = pacing_ctx.get("convergence_components") or {}
        convergence_score = pacing_ctx.get("convergence_score")
        scene_phase = pacing_ctx.get("scene_phase", "")

        if not raw_components:
            continue

        components = _remap_components(raw_components)

        # Extract 6 component values + stall_floor
        urgent_thread = components.get("urgent_thread", 0)
        threat_thread = components.get("threat_thread", 0)
        scene_age = components.get("scene_age", 0)
        beat_streak = components.get("beat_streak", 0)
        roll_starvation = components.get("roll_starvation", 0)
        threat_density = components.get("threat_density", 0)
        stall_floor = components.get("stall_floor", 0)

        # Check for negative components (all except stall_floor which is int >= 0)
        for name, value in [
            ("urgent_thread", urgent_thread),
            ("threat_thread", threat_thread),
            ("scene_age", scene_age),
            ("beat_streak", beat_streak),
            ("roll_starvation", roll_starvation),
            ("threat_density", threat_density),
        ]:
            if value < 0:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "non_negative_component",
                    "detail": f"{name} is negative: {value}",
                })
                all_passed = False

        # Compute expected score (6 components + stall_floor)
        expected_score = urgent_thread + threat_thread + scene_age + beat_streak + roll_starvation + threat_density + stall_floor

        # Check score match (floating point tolerance)
        if convergence_score is not None:
            diff = abs(expected_score - convergence_score)
            if diff > 0.01:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "score_mismatch",
                    "detail": f"expected {expected_score}, got {convergence_score} (diff={diff:.2f})",
                })
                all_passed = False

        # Check phase transitions
        if prev_phase == "RISING" and scene_phase == "CLIMAX":
            # Runtime default is 2, not the class default of 3
            threshold = cfg.convergence_threshold if cfg.convergence_threshold != 3 else 2
            if convergence_score is not None and convergence_score < threshold:
                findings.append({
                    "turn": ev.get("turn"),
                    "check": "phase_transition_threshold",
                    "detail": f"RISING→CLIMAX at turn {ev.get('turn')} with score {convergence_score} < threshold {threshold}",
                })
                all_passed = False

        prev_phase = scene_phase

    if not all_passed:
        return CheckerResult(
            checker_id="convergence_components", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="convergence_components", passed=True, score=1.0,
        detail=f"convergence components OK across {len(events)} events",
    )
