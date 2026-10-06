from __future__ import annotations

import logging
from typing import Any

from fablethread.engine.config import EngineConfig
from fablethread.ev.checkers import CheckerResult, register_checker
from fablethread.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "convergence_threshold_context", "deterministic",
    requires_fields=["pacing_context.convergence_score", "pacing_context.scene_phase"],
    description="Verify gate thresholds use config values: RISING→CLIMAX uses enter_threshold, resolution uses exit_threshold",
)
def convergence_threshold_context(events: list[dict[str, Any]], *, config: Any = None) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        convergence_score = pc.get("convergence_score")
        turn_no = ev.get("turn")

        if i == 0:
            continue

        prev_ev = filtered[i - 1]
        prev_pc = extract_field(prev_ev, "pacing_context") or {}
        prev_phase = prev_pc.get("scene_phase", "SETUP")
        
        # Read turns_in_phase from previous turn's last_turn_state.scene
        prev_snap = extract_field(prev_ev, "last_turn_state") or {}
        prev_scene = prev_snap.get("scene") or {}
        prev_turns_in_phase = prev_scene.get("turns_in_phase", 0)

        # RISING→CLIMAX: require convergence >= enter_threshold AND min_turns met
        if prev_phase == "RISING" and phase == "CLIMAX":
            need_min = prev_turns_in_phase + 1 >= cfg.RISING_min
            need_conv = convergence_score is not None and convergence_score >= cfg.convergence_enter_threshold
            if not need_min or not need_conv:
                findings.append({
                    "turn": turn_no,
                    "check": "rising_climax_threshold",
                    "detail": f"RISING→CLIMAX at turn {turn_no}: turns_met={need_min}(prev_turns={prev_turns_in_phase}+1,min={cfg.RISING_min}), conv_met={need_conv}(score={convergence_score},enter={cfg.convergence_enter_threshold})",
                })
                all_passed = False

        # CLIMAX→RESOLUTION: require (convergence < exit_threshold AND min_turns) OR hard_cap
        elif prev_phase == "CLIMAX" and phase == "RESOLUTION":
            prev_climax_pc = extract_field(prev_ev, "pacing_context") or {}
            prev_climax_turn_count = prev_climax_pc.get("climax_turn_count", 0)
            hard_cap = prev_climax_turn_count + 1 >= cfg.climax_turn_limit
            min_turns = prev_turns_in_phase + 1 >= cfg.CLIMAX_min
            conv_low = convergence_score is not None and convergence_score < cfg.convergence_exit_threshold
            early_exit = min_turns and conv_low
            if not early_exit and not hard_cap:
                findings.append({
                    "turn": turn_no,
                    "check": "climax_resolution_threshold",
                    "detail": f"CLIMAX→RESOLUTION at turn {turn_no}: early_exit={early_exit}(turns={min_turns},conv_low={conv_low}), hard_cap={hard_cap}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="convergence_threshold_context", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="convergence_threshold_context", passed=True, score=1.0,
        detail=f"threshold context OK across {len(filtered)} events",
    )
