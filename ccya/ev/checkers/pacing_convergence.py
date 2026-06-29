from __future__ import annotations

import logging
from math import ceil
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.engine._pacing import BEAT_BUCKETS, derive_allowed_beat_types
from ccya.ev.checkers import CheckerResult, register_checker
from ccya.ev.events import extract_field, filter_turn_events

_log = logging.getLogger(__name__)


@register_checker(
    "phase_transition_signals", "deterministic",
    requires_fields=["pacing_context", "last_turn_state"],
    description="Verify phase transition triggers match engine logic, not just state machine edges",
)
def phase_transition_signals(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "SETUP")
        turn_no = ev.get("turn")
        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        completed_threads = arc.get("completed_threads") or []
        convergence_score = pc.get("convergence_score")
        climax_turn_count = pc.get("climax_turn_count", 0)

        # For transition checks, we need the PREVIOUS turn's state
        # because the current turn's state reflects post-transition values
        prev_snap = None
        prev_urgent_count = 0
        prev_breather_turn_count = 0
        if i > 0:
            prev_ev = filtered[i - 1]
            prev_snap = extract_field(prev_ev, "last_turn_state") or {}
            prev_arc = prev_snap.get("arc") or prev_snap.get("long_term_objective") or {}
            prev_threads = prev_arc.get("threads") or []
            prev_urgent_count = sum(
                1 for t in prev_threads
                if isinstance(t, dict) and t.get("urgency") == "urgent" and not t.get("dormant", False)
            )
            prev_scene = prev_snap.get("scene") or {}
            prev_breather_turn_count = prev_scene.get("breather_turn_count", 0)

            # SETUP→RISING: fires when urgent thread appears OR turns_in_phase >= 3
            if i > 0:
                prev_ev = filtered[i - 1]
                prev_pc = extract_field(prev_ev, "pacing_context") or {}
                prev_phase = prev_pc.get("scene_phase", "SETUP")

                if prev_phase == "SETUP" and phase == "RISING":
                    has_urgent = prev_urgent_count > 0
                    # Read turns_in_phase from previous turn's scene (pacing_context
                    # turns_in_phase is post-transition, already reset to 0)
                    prev_scene = prev_snap.get("scene") or {}
                    prev_turns_in_phase = prev_scene.get("turns_in_phase", 0)
                    reached_turn_threshold = prev_turns_in_phase + 1 >= 3
                    if not has_urgent and not reached_turn_threshold:
                        findings.append({
                            "turn": turn_no,
                            "check": "setup_rising_trigger",
                            "detail": f"SETUP→RISING at turn {turn_no} without urgent thread (count={prev_urgent_count}) or turns_in_phase>=3 (prev_scene={prev_turns_in_phase})",
                        })
                        all_passed = False

            # RISING→CLIMAX: fires when smoothed_convergence >= enter_threshold AND min_turns met
            elif prev_phase == "RISING" and phase == "CLIMAX":
                prev_turns_in_phase = prev_scene.get("turns_in_phase", 0)
                min_turns_met = prev_turns_in_phase + 1 >= cfg.RISING_min
                convergence_met = convergence_score is not None and convergence_score >= cfg.convergence_enter_threshold
                if not min_turns_met or not convergence_met:
                    findings.append({
                        "turn": turn_no,
                        "check": "rising_climax_trigger",
                        "detail": f"RISING→CLIMAX at turn {turn_no} without min_turns (prev_turns_in_phase={prev_turns_in_phase}+1 >= {cfg.RISING_min}) or convergence>=enter_threshold (score={convergence_score} >= {cfg.convergence_enter_threshold})",
                    })
                    all_passed = False

            # CLIMAX→RESOLUTION: valid when either:
            #   - early exit: thread resolved prev turn AND convergence < exit_threshold AND min_turns met
            #   - hard cap: climax_turn_count >= limit
            elif prev_phase == "CLIMAX" and phase == "RESOLUTION":
                thread_resolved_prev = any(
                    (rt := ct.get("resolved_turn")) is not None and rt == turn_no - 1  # type: ignore[operator]
                    for ct in completed_threads
                )
                prev_turns_in_phase = prev_scene.get("turns_in_phase", 0)
                early_exit = thread_resolved_prev and (convergence_score is None or convergence_score < cfg.convergence_exit_threshold) and (prev_turns_in_phase + 1 >= cfg.CLIMAX_min)
                # Use previous turn's climax_turn_count since current turn's has been reset
                # Engine increments at start of current turn, so prev + 1 is what gets checked
                prev_climax_turn_count = prev_pc.get("climax_turn_count", 0)
                hard_cap = prev_climax_turn_count + 1 >= cfg.climax_turn_limit
                if not early_exit and not hard_cap:
                    findings.append({
                        "turn": turn_no,
                        "check": "climax_resolution_signal",
                        "detail": f"CLIMAX→RESOLUTION at turn {turn_no} without valid exit signal (resolved_prev={thread_resolved_prev}, convergence={convergence_score}, prev_climax_turn_count={prev_climax_turn_count}, limit={cfg.climax_turn_limit})",
                    })
                    all_passed = False

            # CLIMAX extension: stays when convergence >= 3 AND has_urgent, caps at limit + extension_max
            elif prev_phase == "CLIMAX" and phase == "CLIMAX":
                if climax_turn_count >= cfg.climax_turn_limit:
                    if convergence_score is not None and convergence_score >= 3 and prev_urgent_count > 0:
                        if climax_turn_count >= cfg.climax_turn_limit + cfg.extension_max:
                            findings.append({
                                "turn": turn_no,
                                "check": "climax_hard_cap",
                                "detail": f"CLIMAX hard cap exceeded: turn_count={climax_turn_count} >= limit={cfg.climax_turn_limit} + extension={cfg.extension_max}",
                            })
                            all_passed = False
                    elif convergence_score is not None and convergence_score < 3:
                        findings.append({
                            "turn": turn_no,
                            "check": "climax_extension_requirement",
                            "detail": f"CLIMAX extended past limit={cfg.climax_turn_limit} without convergence>=3 (score={convergence_score})",
                        })
                        all_passed = False
                    elif prev_urgent_count == 0:
                        findings.append({
                            "turn": turn_no,
                            "check": "climax_extension_urgent",
                            "detail": f"CLIMAX extended past limit={cfg.climax_turn_limit} without urgent thread",
                        })
                        all_passed = False

            # RESOLUTION→BREATHER: always fires (1-turn transition)
            elif prev_phase == "RESOLUTION" and phase == "BREATHER":
                # This is always valid, no check needed
                pass

            # BREATHER→RISING: fires when urgent thread OR breather_turn_count >= breather_max_turns, AND min_turns met
            elif prev_phase == "BREATHER" and phase == "RISING":
                prev_turns_in_phase = prev_scene.get("turns_in_phase", 0)
                min_turns_met = prev_turns_in_phase + 1 >= cfg.BREATHER_min
                if not min_turns_met:
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_rising_min_turns",
                        "detail": f"BREATHER→RISING at turn {turn_no} without min_turns (prev_turns_in_phase={prev_turns_in_phase}+1 >= {cfg.BREATHER_min})",
                    })
                    all_passed = False
                elif prev_urgent_count == 0 and prev_breather_turn_count < cfg.breather_max_turns:
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_rising_trigger",
                        "detail": f"BREATHER→RISING at turn {turn_no} without urgent thread (count={prev_urgent_count}) or breather_turn_count>={cfg.breather_max_turns} (prev={prev_breather_turn_count})",
                    })
                    all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="phase_transition_signals", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="phase_transition_signals", passed=True, score=1.0,
        detail=f"all {len(filtered)} turn events passed",
    )


@register_checker(
    "convergence_recompute", "deterministic",
    requires_fields=["pacing_context.convergence_components", "pacing_context.convergence_score", "last_turn_state"],
    description="Independently recompute convergence score from raw state and compare to stored value",
)
def convergence_recompute(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for i, ev in enumerate(filtered):
        pc = extract_field(ev, "pacing_context") or {}
        raw_components = pc.get("convergence_components") or {}
        convergence_score = pc.get("convergence_score")
        turn_no = ev.get("turn")

        if not raw_components:
            continue

        snap = extract_field(ev, "last_turn_state") or {}
        meta = snap.get("meta") or {}
        scene = snap.get("scene") or {}
        # Use convergence_threads from event if available (threads used for computation),
        # otherwise can't accurately recompute for old saves
        convergence_threads = pc.get("convergence_threads")
        if not convergence_threads:
            _log.debug("convergence_recompute: skipping turn %d (no convergence_threads in event)", turn_no)
            continue

        # Compute scene_age
        # meta.turn in last_turn_state is already incremented (post-turn),
        # but _compute_ages runs at ruling time (pre-increment), so subtract 1
        mt = meta.get("turn")
        current_turn = (mt if mt is not None else turn_no) - 1  # type: ignore[operator]
        # scene.turn_entered in last_turn_state is set by delta_builder AFTER
        # ruling, but _compute_ages runs at ruling time. Read from previous
        # turn's state to get the pre-delta_builder value.
        scene_entered = scene.get("turn_entered")
        if i > 0:
            prev_ev = filtered[i - 1]
            prev_lts = extract_field(prev_ev, "last_turn_state") or {}
            prev_scene = prev_lts.get("scene") or {}
            prev_scene_entered = prev_scene.get("turn_entered")
            if prev_scene_entered is not None:
                scene_entered = prev_scene_entered
        if scene_entered is None:
            # Fallback: scene_entered = current_turn - turns_in_phase + 1
            turns_in_phase = scene.get("turns_in_phase", 1)
            scene_entered = current_turn - turns_in_phase + 1
        scene_age = current_turn - scene_entered

        # Get recent_beats
        recent_beats = meta.get("recent_beats") or []

        # Get recent_rolls
        recent_rolls = meta.get("recent_rolls") or []

        # Recompute each component independently
        components: dict[str, int] = {}

        # Component 1: urgent_thread (0-2, capped count)
        urgent_count = sum(
            1 for t in convergence_threads
            if t.get("urgency") == "urgent" and not t.get("dormant", False)
        )
        components["urgent_thread"] = min(urgent_count, 2)

        # Component 2: threat_thread (+1 if any non-dormant threat-type thread)
        any_threat = any(
            t.get("type") == "threat" and not t.get("dormant", False)
            for t in convergence_threads
        )
        components["threat_thread"] = 1 if any_threat else 0

        # Component 3: scene_age (+1 if scene_age >= threshold)
        components["scene_age"] = 1 if scene_age >= cfg.scene_pressure_threshold else 0

        # Component 4: beat_streak (+1 if >=60% pressure beats in recent window)
        pressure_types = set(BEAT_BUCKETS["pressure"])
        last_non_null_type = None
        pressure_count = 0
        if recent_beats:
            n = len(recent_beats)
            window = recent_beats[:min(n, 5)]
            for b in window:
                bt = b.get("type")
                if bt is not None:
                    last_non_null_type = bt
                if last_non_null_type in pressure_types:
                    pressure_count += 1
            threshold = ceil(n * 0.6) if n < 5 else 3
            components["beat_streak"] = 1 if pressure_count >= threshold else 0
        else:
            components["beat_streak"] = 0

        # Component 5: roll_starvation (+1 if turns_since_last_roll >= threshold)
        turns_since_last_roll = None
        if recent_rolls:
            last_roll_turn = recent_rolls[0].get("turn") if isinstance(recent_rolls[0], dict) else None
            if last_roll_turn is not None:
                turns_since_last_roll = turn_no - last_roll_turn
        components["roll_starvation"] = 1 if (turns_since_last_roll is not None and turns_since_last_roll >= cfg.roll_starvation_threshold) else 0

        # Component 6: threat_density (+1 if active threat count >= threshold)
        active_threat_count = sum(
            1 for t in convergence_threads
            if t.get("type") == "threat" and not t.get("dormant", False)
        )
        components["threat_density"] = 1 if active_threat_count >= cfg.threat_density_threshold else 0

        # Compare recomputed components to stored components
        for name, recomputed_value in components.items():
            stored_value = raw_components.get(name, 0)
            if stored_value != recomputed_value:
                findings.append({
                    "turn": turn_no,
                    "check": "component_mismatch",
                    "detail": f"{name}: stored={stored_value}, recomputed={recomputed_value}",
                })
                all_passed = False

        # Compute expected total score (6 components, no stall_floor)
        expected_score = sum(components.values())

        if convergence_score is not None:
            diff = abs(expected_score - convergence_score)
            if diff > 0.01:
                findings.append({
                    "turn": turn_no,
                    "check": "score_mismatch",
                    "detail": f"expected {expected_score}, got {convergence_score} (diff={diff:.2f})",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="convergence_recompute", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="convergence_recompute", passed=True, score=1.0,
        detail=f"convergence recomputation OK across {len(filtered)} events",
    )


@register_checker(
    "curtain_call", "deterministic",
    requires_fields=["pacing_context", "last_turn_state"],
    description="Verify curtain_call state matches CLIMAX phase rules",
)
def curtain_call(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for ev in filtered:
        pc = extract_field(ev, "pacing_context") or {}
        phase = pc.get("scene_phase", "")
        climax_turn_count = pc.get("climax_turn_count", 0)
        turn_no = ev.get("turn")

        # Get curtain_call from last_turn_state.scene
        snap = extract_field(ev, "last_turn_state") or {}
        scene = snap.get("scene") or {}
        curtain_call = scene.get("curtain_call", "")

        if phase == "CLIMAX":
            # CLIMAX turn 1: curtain_call == "active"
            if climax_turn_count == 1:
                if curtain_call != "active":
                    findings.append({
                        "turn": turn_no,
                        "check": "curtain_call_active",
                        "detail": f"CLIMAX turn 1: expected curtain_call='active', got '{curtain_call}'",
                    })
                    all_passed = False
            # CLIMAX turn >= limit - 1: curtain_call == "forced"
            elif climax_turn_count >= cfg.climax_turn_limit - 1:
                if curtain_call != "forced":
                    findings.append({
                        "turn": turn_no,
                        "check": "curtain_call_forced",
                        "detail": f"CLIMAX turn {climax_turn_count} >= limit-1={cfg.climax_turn_limit-1}: expected curtain_call='forced', got '{curtain_call}'",
                    })
                    all_passed = False
            # CLIMAX turns between 2 and limit-2: curtain_call should be ""
            elif curtain_call != "":
                findings.append({
                    "turn": turn_no,
                    "check": "curtain_call_empty",
                    "detail": f"CLIMAX turn {climax_turn_count} (between 2 and limit-2): expected curtain_call='', got '{curtain_call}'",
                })
                all_passed = False
        else:
            # Non-CLIMAX: curtain_call should be ""
            if curtain_call != "":
                findings.append({
                    "turn": turn_no,
                    "check": "curtain_call_non_climax",
                    "detail": f"Non-CLIMAX phase '{phase}': expected curtain_call='', got '{curtain_call}'",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="curtain_call", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="curtain_call", passed=True, score=1.0,
        detail=f"curtain_call OK across {len(filtered)} events",
    )


@register_checker(
    "directive_beat_alignment", "deterministic",
    requires_fields=["ruling", "pacing_context", "last_turn_state"],
    description="Verify selected beat aligns with directive and phase constraints",
)
def directive_beat_alignment(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    filtered = filter_turn_events(events)

    for ev in filtered:
        ruling = extract_field(ev, "ruling") or {}
        selected_beat_idx = ruling.get("selected_beat")
        if not isinstance(selected_beat_idx, int):
            continue

        pc = extract_field(ev, "pacing_context") or {}
        directive = pc.get("directive", "")
        scene_phase = pc.get("scene_phase", "SETUP")
        turn_no = ev.get("turn")

        snap = extract_field(ev, "last_turn_state") or {}
        meta = snap.get("meta") or {}
        beat_candidates = meta.get("beat_candidates") or []

        if not isinstance(beat_candidates, list) or selected_beat_idx >= len(beat_candidates):
            continue

        beat = beat_candidates[selected_beat_idx]
        if not isinstance(beat, dict) or not beat.get("type"):
            continue

        beat_type = beat["type"]

        # Derive allowed beat types
        allowed = derive_allowed_beat_types(
            scene_phase,
            directive=directive,
        )

        # Check: selected beat type is in allowed types
        if beat_type not in allowed:
            findings.append({
                "turn": turn_no,
                "check": "beat_in_allowed",
                "detail":                 f"beat type '{beat_type}' not allowed (directive='{directive}', phase='{scene_phase}', allowed={sorted(allowed)})",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="directive_beat_alignment", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="directive_beat_alignment", passed=True, score=1.0,
        detail=f"directive-beat alignment OK across {len(filtered)} events",
    )
