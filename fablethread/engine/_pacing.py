"""Shared pacing helpers: beat constraint map, phase-driven beat derivation.

This module encapsulates the beat constraint table in Python so both
`turn.py` (phase engine, directive computation) and `extraction.py`
(record context) can import it without circular imports.
"""

from __future__ import annotations

import logging

from typing import Any

from fablethread.engine.config import EngineConfig
from fablethread.engine.turn_context import PacingContext
from fablethread.models import ArcThread, Scene, WorldState

_log = logging.getLogger(__name__)


BEAT_BUCKETS: dict[str, list[str]] = {
    "tension":   ["pressure", "complication", "escalation", "setback"],
    "discovery": ["revelation", "twist", "callback"],
    "respite":   ["opportunity", "breathing_room"],
}

BEAT_PHASE_MAP: dict[str, list[str]] = {
    "SETUP":       ["pressure", "complication", "escalation", "revelation", "twist", "opportunity", "callback", "breathing_room"],
    "RISING":      ["pressure", "complication", "escalation", "revelation", "twist"],
    "CLIMAX":      ["pressure", "escalation", "complication", "revelation", "callback", "twist"],
    "RESOLUTION":  ["breathing_room", "callback", "revelation"],
    "BREATHER":    ["opportunity", "revelation", "callback", "breathing_room"],
}


def derive_allowed_beat_types(
    scene_phase: str,
    *,
    directive: str = "",
) -> list[str]:
    """Return the list of allowed beat types for the given scene phase.

    Priority order:
    1. Scene Imperative directive → phase defaults + situation-changers
    2. Fallback → phase defaults
    """
    base = BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))
    if directive == "Scene Imperative":
        extra = ["revelation", "callback", "opportunity", "setback", "breathing_room"]
        return list(dict.fromkeys(base + extra))  # dedupe, preserve order

    return base


def compute_convergence_score(
    scene_phase: str,
    active_threads: list[dict[str, Any]],
    recent_beats: list[dict[str, Any]],
    config: EngineConfig,
    turn_no: int,
    recent_rolls: list[dict[str, Any]],
) -> tuple[int, dict[str, int]]:
    """Compute a 5-component convergence score for RISING→CLIMAX transition.

    Components: urgent_thread (0-2), threat_thread (+1), beat_streak (+1),
    roll_starvation (+1), threat_density (+1). Total: 6.
    Threshold is config.convergence_threshold (default 2).
    Returns (score, components_dict) where components_dict has keys:
    urgent_thread, threat_thread, beat_streak, roll_starvation, threat_density.
    Dormant threads are excluded from all components.
    """
    score = 0
    components: dict[str, int] = {}

    # Component 1: urgent thread count (0-2, capped)
    urgent_count = sum(
        1 for t in active_threads
        if t.get("urgency") == "urgent" and not t.get("dormant", False)
    )
    urgent_capped = min(urgent_count, 2)
    score += urgent_capped
    components["urgent_thread"] = urgent_capped

    # Component 2: active threat (+1)
    any_threat = any(
        t.get("type") == "threat" and not t.get("dormant", False)
        for t in active_threads
    )
    if any_threat:
        score += 1
    components["threat_thread"] = 1 if any_threat else 0

    # (scene_age removed — used by narration directive, not convergence)

    # Component 4: Beat streak (+1) — carry-over for null beats, 2/4 threshold
    tension_types = set(BEAT_BUCKETS["tension"])
    pressure_count = 0
    if recent_beats:
        n = len(recent_beats)
        window = recent_beats[: min(n, 4)]
        # Carry over: null beats inherit the last known non-null type
        last_type = None
        for b in window:
            bt = b.get("type")
            if bt is not None:
                last_type = bt
            if last_type is not None and last_type in tension_types:
                pressure_count += 1
        threshold = 2
        if pressure_count >= threshold:
            score += 1
        components["beat_streak"] = 1 if pressure_count >= threshold else 0
    else:
        components["beat_streak"] = 0

    # Component 5: roll_starvation (+1)
    turns_since_last_roll = turn_no - recent_rolls[0]["turn"] if recent_rolls else None
    if turns_since_last_roll is not None and turns_since_last_roll >= config.roll_starvation_threshold:
        score += 1
    components["roll_starvation"] = 1 if (turns_since_last_roll is not None and turns_since_last_roll >= config.roll_starvation_threshold) else 0

    # Component 6: threat_density (+1)
    active_threat_count = sum(1 for t in active_threads if t.get("type") == "threat" and not t.get("dormant", False))
    if active_threat_count >= config.threat_density_threshold:
        score += 1
    components["threat_density"] = 1 if active_threat_count >= config.threat_density_threshold else 0

    return (score, components)


def _compute_narration_directive(
    scene_phase: str,
    thread_urgency_count: int,
    effective_scene_age: int,
    scene_pressure_threshold: int = 3,
    scene_imperative_threshold: int = 5,
) -> str:
    """Compute the narration directive string using a priority stack.

    Priority order (highest to lowest):
      1. Scene Imperative — effective_scene_age >= scene_imperative_threshold
      2. Scene Pressure   — effective_scene_age >= scene_pressure_threshold
      3. (empty)        — default
    """
    # Priority 1: Scene Imperative — stale scene
    if effective_scene_age >= scene_imperative_threshold:
        return "Scene Imperative"

    # Priority 2: Scene Pressure — approaching staleness
    if effective_scene_age >= scene_pressure_threshold:
        return "Scene Pressure"

    # Priority 3: empty (default)
    return ""


def _compute_pacing_context(
    scene_phase: str,
    thread_urgency_count: int,
    effective_scene_age: int,
    scene_motion: str = "hold",
    scene_pressure_threshold: int = 3,
    scene_imperative_threshold: int = 5,
    config: EngineConfig | None = None,
    convergence_score: int = 0,
) -> PacingContext:
    """Compute unified pacing context for Narrate and Progress steps.
    """
    # Compute directive using new signal set
    directive = _compute_narration_directive(
        scene_phase=scene_phase,
        thread_urgency_count=thread_urgency_count,
        effective_scene_age=effective_scene_age,
        scene_pressure_threshold=scene_pressure_threshold,
        scene_imperative_threshold=scene_imperative_threshold,
    )

    # outcome_hint: primarily driven by scene_motion from ruling engine.
    # When Scene Imperative fires (scene stale or crisis expired), override to "transition".
    outcome_hint: str | None = scene_motion

    if effective_scene_age >= scene_imperative_threshold:
        outcome_hint = "transition"

    # Convergence score hard gate — cannot be overridden by LLM scene_motion
    if config and convergence_score >= config.convergence_enter_threshold and scene_phase in ("SETUP", "RISING"):
        outcome_hint = "transition"

    # Build summary for logging
    parts = [directive] if directive else []
    summary = ", ".join(parts) or "neutral"

    return PacingContext(
        directive=directive or "",
        outcome_hint=outcome_hint,
        summary=summary,
    )


def _compute_ages(state: WorldState) -> dict[str, int]:
    """Compute age/staleness counters for narration directives."""
    current_turn = state.meta.turn

    scene_entered = state.scene.location_entered_turn
    scene_age = current_turn - scene_entered

    return {
        "scene_age": scene_age,
    }


def _compute_scene_phase(
    state: WorldState,
    ages: dict[str, int],
    config: EngineConfig,
    total_convergence_score: float = 0.0,
    turn_no: int = 0,
) -> Scene:
    """Compute the scene phase using the 5-state machine.

    Transitions: SETUP→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION,
    RESOLUTION→BREATHER, BREATHER→RISING.

    CLIMAX→RESOLUTION: signal-gated exit (early exit on thread resolution + low convergence,
    extension on sustained pressure, hard cap at climax_turn_limit + extension_max).

    Returns the updated scene model.
    """
    scene = state.scene

    phase = scene.scene_phase
    climax_turn_count = scene.climax_turn_count
    breather_turn_count = scene.breather_turn_count
    turns_in_phase = scene.turns_in_phase + 1
    turn_entered = scene.turn_entered

    # Count urgent threads
    thread_urgency_count = 0
    for t in state.long_term_objective.threads:
        arc = _to_arc_thread(t)
        if arc and arc.urgency == "urgent":
            thread_urgency_count += 1

    # Phase transition logic
    if phase == "SETUP":
        if thread_urgency_count > 0 or turns_in_phase >= 3 or (total_convergence_score >= 2 and turns_in_phase >= 2):
            phase = "RISING"
            turns_in_phase = 1
            turn_entered = turn_no

    elif phase == "RISING":
        if total_convergence_score >= config.convergence_enter_threshold and turns_in_phase >= config.RISING_min:
            phase = "CLIMAX"
            climax_turn_count = 1
            turns_in_phase = 1
            turn_entered = turn_no

    elif phase == "CLIMAX":
        climax_turn_count += 1
        # Early exit — evaluated EVERY CLIMAX turn (not just at the limit).
        # Signal sourced from state (end-of-prior-turn), not in-flight record result.
        thread_resolved_prev_turn = any(
            ct for ct in state.long_term_objective.completed_threads
            if ct.resolved_turn == turn_no - 1
        )
        if thread_resolved_prev_turn and total_convergence_score < config.convergence_exit_threshold and turns_in_phase >= config.CLIMAX_min:
            phase = "RESOLUTION"
            climax_turn_count = 0
            turns_in_phase = 1
            turn_entered = turn_no
        # Hard cap + extension — only evaluated at/after the limit
        elif climax_turn_count >= config.climax_turn_limit:
            # has_urgent_active_thread: explicit dormant filter (do NOT copy existing thread_urgency_count pattern)
            has_urgent_active_thread = any(
                t for t in state.long_term_objective.threads
                if isinstance(t, ArcThread) and t.urgency == "urgent" and not t.dormant
            )
            if total_convergence_score >= 3 and has_urgent_active_thread:
                if climax_turn_count >= config.climax_turn_limit + config.extension_max:
                    phase = "RESOLUTION"
                    climax_turn_count = 0
                    turns_in_phase = 1
                    turn_entered = turn_no
                # else stay in CLIMAX (extension active)
            else:
                phase = "RESOLUTION"
                climax_turn_count = 0
                turns_in_phase = 1
                turn_entered = turn_no
        # else: stay in CLIMAX (below limit, no early-exit signal)

    elif phase == "RESOLUTION":
        phase = "BREATHER"
        breather_turn_count = 1
        turns_in_phase = 1
        turn_entered = turn_no

    elif phase == "BREATHER":
        breather_turn_count += 1
        if (thread_urgency_count > 0 or breather_turn_count >= config.breather_max_turns) and turns_in_phase >= config.BREATHER_min:
            phase = "RISING"
            breather_turn_count = 0
            turns_in_phase = 1
            turn_entered = turn_no

    return Scene(
        scene_phase=phase,
        climax_turn_count=climax_turn_count,
        breather_turn_count=breather_turn_count,
        turns_in_phase=turns_in_phase,
        tags=list(scene.tags),
        world_state=list(scene.world_state),
        turn_entered=turn_entered,
        location_entered_turn=scene.location_entered_turn,
    )


def _to_arc_thread(t: Any) -> "ArcThread | None":
    """Convert t to ArcThread if possible, return None on failure."""
    if isinstance(t, ArcThread):
        return t
    try:
        return ArcThread.model_validate(t)
    except Exception as exc:
        _log.warning("Invalid arc thread object, skipping: %s", exc)
        return None
