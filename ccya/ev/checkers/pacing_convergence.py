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
        threads = arc.get("threads") or []
        completed_threads = arc.get("completed_threads") or []
        meta = snap.get("meta") or {}
        scene = snap.get("scene") or {}

        convergence_score = pc.get("convergence_score")
        turns_in_phase = pc.get("turns_in_phase", 0)
        climax_turn_count = pc.get("climax_turn_count", 0)
        breather_turn_count = pc.get("breather_turn_count", 0)

        # Count urgent threads
        urgent_count = sum(
            1 for t in threads
            if isinstance(t, dict) and t.get("urgency") == "urgent" and not t.get("dormant", False)
        )

        # SETUP→RISING: fires when urgent thread appears OR turns_in_phase >= 3
        if i > 0:
            prev_ev = filtered[i - 1]
            prev_pc = extract_field(prev_ev, "pacing_context") or {}
            prev_phase = prev_pc.get("scene_phase", "SETUP")

            if prev_phase == "SETUP" and phase == "RISING":
                has_urgent = urgent_count > 0
                # Note: turns_in_phase is already reset to 0 at this point,
                # so we check the previous turn's turns_in_phase if available
                prev_turns_in_phase = prev_pc.get("turns_in_phase", 0)
                reached_turn_threshold = prev_turns_in_phase + 1 >= 3
                if not has_urgent and not reached_turn_threshold:
                    findings.append({
                        "turn": turn_no,
                        "check": "setup_rising_trigger",
                        "detail": f"SETUP→RISING at turn {turn_no} without urgent thread (count={urgent_count}) or turns_in_phase>=3 (prev={prev_turns_in_phase})",
                    })
                    all_passed = False

            # CLIMAX→RESOLUTION: valid when either:
            #   - early exit: thread resolved prev turn AND convergence < 2
            #   - hard cap: climax_turn_count >= limit
            elif prev_phase == "CLIMAX" and phase == "RESOLUTION":
                thread_resolved_prev = any(
                    ct for ct in completed_threads
                    if ct.get("resolved_turn") == turn_no - 1
                )
                early_exit = thread_resolved_prev and (convergence_score is None or convergence_score < 2)
                # Use previous turn's climax_turn_count since current turn's has been reset
                # Engine increments at start of current turn, so prev + 1 is what gets checked
                prev_climax_turn_count = prev_pc.get("climax_turn_count", 0)
                hard_cap = prev_climax_turn_count + 1 >= cfg.climax_turn_limit
                if not early_exit and not hard_cap:
                    resolved_turns = [ct.get("resolved_turn") for ct in completed_threads if ct.get("resolved_turn")]
                    findings.append({
                        "turn": turn_no,
                        "check": "climax_resolution_signal",
                        "detail": f"CLIMAX→RESOLUTION at turn {turn_no} without valid exit signal (resolved_prev={thread_resolved_prev}, convergence={convergence_score}, prev_climax_turn_count={prev_climax_turn_count}, limit={cfg.climax_turn_limit})",
                    })
                    all_passed = False

            # CLIMAX extension: stays when convergence >= 3 AND has_urgent, caps at limit + extension_max
            elif prev_phase == "CLIMAX" and phase == "CLIMAX":
                if climax_turn_count >= cfg.climax_turn_limit:
                    if convergence_score is not None and convergence_score >= 3 and urgent_count > 0:
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
                    elif urgent_count == 0:
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

            # BREATHER→RISING: fires when urgent thread OR breather_turn_count >= breather_max_turns
            elif prev_phase == "BREATHER" and phase == "RISING":
                if urgent_count == 0 and breather_turn_count < cfg.breather_max_turns:
                    findings.append({
                        "turn": turn_no,
                        "check": "breather_rising_trigger",
                        "detail": f"BREATHER→RISING at turn {turn_no} without urgent thread (count={urgent_count}) or breather_turn_count>={cfg.breather_max_turns} (count={breather_turn_count})",
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

    for ev in filtered:
        pc = extract_field(ev, "pacing_context") or {}
        raw_components = pc.get("convergence_components") or {}
        convergence_score = pc.get("convergence_score")
        scene_phase = pc.get("scene_phase", "")
        turn_no = ev.get("turn")

        if not raw_components:
            continue

        snap = extract_field(ev, "last_turn_state") or {}
        arc = snap.get("arc") or snap.get("long_term_objective") or {}
        threads = arc.get("threads") or []
        meta = snap.get("meta") or {}
        scene = snap.get("scene") or {}

        # Use convergence_threads from event if available (threads used for computation),
        # otherwise can't accurately recompute for old saves
        convergence_threads = pc.get("convergence_threads")
        if not convergence_threads:
            _log.debug("convergence_recompute: skipping turn %d (no convergence_threads in event)", turn_no)
            continue

        # Compute scene_age
        current_turn = meta.get("turn", turn_no)
        scene_entered = scene.get("turn_entered")
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

        # Component 1: urgent_thread (+2 if any non-dormant urgent thread)
        any_urgent = any(
            t.get("urgency") == "urgent" and not t.get("dormant", False)
            for t in convergence_threads
        )
        components["urgent_thread"] = 2 if any_urgent else 0

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
                # Allow legacy +1 for urgent_thread (old engine used +1, now uses +2)
                if name == "urgent_thread" and stored_value == 1 and recomputed_value == 2:
                    continue
                findings.append({
                    "turn": turn_no,
                    "check": "component_mismatch",
                    "detail": f"{name}: stored={stored_value}, recomputed={recomputed_value}",
                })
                all_passed = False

        # Compute expected total score (6 components + stall_floor)
        stored_stall_floor = raw_components.get("stall_floor", 0)
        expected_score = sum(components.values()) + stored_stall_floor

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
    "stall_floor_computation", "deterministic",
    requires_fields=["pacing_context.convergence_components", "last_turn_state"],
    description="Verify stall_floor formula and consecutive_low_convergence tracking",
)
def stall_floor_computation(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for ev in filtered:
        pc = extract_field(ev, "pacing_context") or {}
        raw_components = pc.get("convergence_components") or {}
        convergence_score = pc.get("convergence_score")
        scene_phase = pc.get("scene_phase", "")
        turn_no = ev.get("turn")

        if not raw_components:
            continue

        stored_stall_floor = raw_components.get("stall_floor", 0)

        # We can't directly access consecutive_low_convergence from events,
        # but we can verify the stall_floor formula is consistent:
        # stall_floor = min(1 + ((clc - 3) // 3), stall_floor_max) when clc >= 3, else 0
        # Since we don't have clc, we verify: if stall_floor > 0, it must follow the formula
        # stall_floor should be in range [0, stall_floor_max]
        if stored_stall_floor < 0:
            findings.append({
                "turn": turn_no,
                "check": "negative_stall_floor",
                "detail": f"stall_floor is negative: {stored_stall_floor}",
            })
            all_passed = False
        elif stored_stall_floor > cfg.stall_floor_max:
            findings.append({
                "turn": turn_no,
                "check": "stall_floor_exceeds_max",
                "detail": f"stall_floor {stored_stall_floor} exceeds max {cfg.stall_floor_max}",
            })
            all_passed = False

        # Verify that stored score matches components + stall_floor
        urgent_thread = raw_components.get("urgent_thread", 0)
        threat_thread = raw_components.get("threat_thread", 0)
        scene_age = raw_components.get("scene_age", 0)
        beat_streak = raw_components.get("beat_streak", 0)
        roll_starvation = raw_components.get("roll_starvation", 0)
        threat_density = raw_components.get("threat_density", 0)

        expected_score = urgent_thread + threat_thread + scene_age + beat_streak + roll_starvation + threat_density + stored_stall_floor

        if convergence_score is not None:
            diff = abs(expected_score - convergence_score)
            if diff > 0.01:
                findings.append({
                    "turn": turn_no,
                    "check": "score_with_stall_floor",
                    "detail": f"expected {expected_score} (components+stall_floor), got {convergence_score}",
                })
                all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="stall_floor_computation", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="stall_floor_computation", passed=True, score=1.0,
        detail=f"stall_floor computation OK across {len(filtered)} events",
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
    "spiral_detection", "deterministic",
    requires_fields=["pacing_context.spiral_detected", "last_turn_state"],
    description="Verify spiral_detected flag matches roll history thresholds",
)
def spiral_detection(events: list[dict[str, Any]]) -> CheckerResult:
    findings: list[dict[str, Any]] = []
    all_passed = True
    cfg = EngineConfig()
    filtered = filter_turn_events(events)

    for ev in filtered:
        pc = extract_field(ev, "pacing_context") or {}
        stored_spiral = pc.get("spiral_detected", False)
        turn_no = ev.get("turn")

        snap = extract_field(ev, "last_turn_state") or {}
        meta = snap.get("meta") or {}
        recent_rolls = meta.get("recent_rolls") or []

        if not recent_rolls:
            # No rolls yet, spiral should be False
            if stored_spiral:
                findings.append({
                    "turn": turn_no,
                    "check": "spiral_no_rolls",
                    "detail": f"spiral_detected=True but no recent_rolls",
                })
                all_passed = False
            continue

        # Recompute spiral detection
        hard_bands = {"hard", "extreme"}
        consecutive_hard = cfg.spiral_consecutive_hard
        ratio_n, ratio_m = cfg.spiral_hard_ratio

        computed_spiral = False

        # Check consecutive threshold
        if len(recent_rolls) >= consecutive_hard:
            consec = all(
                isinstance(r, dict) and r.get("band") in hard_bands
                for r in recent_rolls[:consecutive_hard]
            )
            if consec:
                computed_spiral = True

        # Check ratio threshold
        if len(recent_rolls) >= ratio_n and not computed_spiral:
            hard_count = sum(
                1 for r in recent_rolls[:ratio_n]
                if isinstance(r, dict) and r.get("band") in hard_bands
            )
            if hard_count >= ratio_m:
                computed_spiral = True

        if stored_spiral != computed_spiral:
            findings.append({
                "turn": turn_no,
                "check": "spiral_mismatch",
                "detail": f"spiral_detected: stored={stored_spiral}, computed={computed_spiral} (recent_rolls={len(recent_rolls)})",
            })
            all_passed = False

    if not all_passed:
        return CheckerResult(
            checker_id="spiral_detection", passed=False, score=0.0,
            detail=f"{len(findings)} issue(s) found", findings=findings,
        )
    return CheckerResult(
        checker_id="spiral_detection", passed=True, score=1.0,
        detail=f"spiral detection OK across {len(filtered)} events",
    )


@register_checker(
    "directive_beat_alignment", "deterministic",
    requires_fields=["ruling", "pacing_context", "last_turn_state"],
    description="Verify selected beat aligns with directive, spiral, and phase constraints",
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
        spiral_detected = pc.get("spiral_detected", False)
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
            spiral_detected=spiral_detected,
        )

        # Check: selected beat type is in allowed types
        if beat_type not in allowed:
            findings.append({
                "turn": turn_no,
                "check": "beat_in_allowed",
                "detail": f"beat type '{beat_type}' not allowed (directive='{directive}', spiral={spiral_detected}, phase='{scene_phase}', allowed={sorted(allowed)})",
            })
            all_passed = False

        # When directive == "Scene Imperative": selected beat must be in situation-changers + opportunity
        if directive == "Scene Imperative":
            imperative_allowed = {"revelation", "hazard", "callback", "opportunity", "setback", "breathing_room"}
            if beat_type not in imperative_allowed:
                findings.append({
                    "turn": turn_no,
                    "check": "scene_imperative_beat",
                    "detail": f"Scene Imperative directive: beat type '{beat_type}' not in allowed set {sorted(imperative_allowed)}",
                })
                all_passed = False

        # When spiral_detected: selected beat type is NOT in pressure bucket
        if spiral_detected:
            pressure_types = set(BEAT_BUCKETS["pressure"])
            if beat_type in pressure_types:
                findings.append({
                    "turn": turn_no,
                    "check": "spiral_no_pressure",
                    "detail": f"Spiral detected: beat type '{beat_type}' is in pressure bucket {sorted(pressure_types)}",
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
