"""Shared pacing helpers: beat constraint map, phase-driven beat derivation.

This module encapsulates the beat constraint table in Python so both
`turn.py` (phase engine, directive computation) and `extraction.py`
(storytell context) can import it without circular imports.
"""

from __future__ import annotations

from math import ceil
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.engine.turn_context import PacingContext
from ccya.models import ArcThread, RulesOutcome


BEAT_BUCKETS: dict[str, list[str]] = {
    "pressure":  ["pressure", "complication", "escalation", "setback"],
    "situation": ["revelation", "twist", "hazard", "callback"],
    "relief":    ["opportunity", "breathing_room"],
}

BEAT_PHASE_MAP: dict[str, list[str]] = {
    "SETUP":       ["pressure", "complication", "escalation", "revelation", "twist", "opportunity", "callback", "breathing_room", "hazard"],
    "RISING":      ["pressure", "complication", "escalation", "revelation", "twist"],
    "CLIMAX":      ["pressure", "escalation", "complication"],
    "RESOLUTION":  ["breathing_room", "callback", "revelation"],
    "BREATHER":    ["opportunity", "revelation", "callback", "breathing_room", "hazard"],
}


def detect_spiral(
    recent_rolls: list[dict[str, Any]],
    consecutive_hard_threshold: int = 3,
    hard_ratio_threshold: tuple[int, int] = (3, 5),
) -> bool:
    """Return True if the rolling window shows a spiral: N consecutive hard+
    rolls, or M of the last N rolls are hard+.

    recent_rolls is ordered most-recent-first.
    """
    hard_bands = {"hard", "extreme"}

    # Check consecutive threshold: first N rolls all hard+
    if len(recent_rolls) >= consecutive_hard_threshold:
        consec = all(r.get("band") in hard_bands for r in recent_rolls[:consecutive_hard_threshold])
        if consec:
            return True

    # Check ratio threshold: M of last N hard+
    ratio_n, ratio_m = hard_ratio_threshold
    if len(recent_rolls) >= ratio_n:
        hard_count = sum(1 for r in recent_rolls[:ratio_n] if r.get("band") in hard_bands)
        if hard_count >= ratio_m:
            return True

    return False


def derive_allowed_beat_types(
    scene_phase: str,
    *,
    directive: str = "",
    spiral_detected: bool = False,
) -> list[str]:
    """Return the list of allowed beat types for the given scene phase.

    Priority order:
    1. Scene Imperative directive → situation-changers + opportunity
    2. Spiral detected → phase defaults minus pressure bucket
    3. Fallback → phase defaults
    """
    if directive == "Scene Imperative":
        return ["revelation", "hazard", "callback", "opportunity", "setback", "breathing_room"]

    base = BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))

    if spiral_detected:
        pressure_types = set(BEAT_BUCKETS["pressure"])
        return [b for b in base if b not in pressure_types]

    return base


def compute_convergence_score(
    scene_phase: str,
    active_threads: list[dict[str, Any]],
    scene_age: int,
    recent_beats: list[dict[str, Any]],
    current_outcome: RulesOutcome | None,
    config: EngineConfig,
) -> int:
    """Compute a 5-component convergence score for RISING→CLIMAX transition.

    Each component is worth +1. Threshold is config.convergence_threshold (default 3).
    Score cannot reach threshold without at least one urgent thread.
    Dormant threads are excluded from all components.
    Note: score CAN reach threshold without urgent threads via threat + scene_age + streak + dice.
    """
    score = 0

    # Component 1: any urgent thread (+1)
    any_urgent = any(
        t.get("urgency") == "urgent" and not t.get("dormant", False)
        for t in active_threads
    )
    if any_urgent:
        score += 1

    # Component 2: active threat (+1)
    any_threat = any(
        t.get("type") == "threat" and not t.get("dormant", False)
        for t in active_threads
    )
    if any_threat:
        score += 1

    # Component 3: Scene age (+1)
    if scene_age >= config.scene_pressure_threshold:
        score += 1

    # Component 4: Beat streak (+1)
    if recent_beats:
        n = len(recent_beats)
        window = recent_beats[: min(n, 5)]
        pressure_types = set(BEAT_BUCKETS["pressure"])
        pressure_count = sum(1 for b in window if b.get("type") in pressure_types)
        threshold = ceil(n * 0.6) if n < 5 else 3
        if pressure_count >= threshold:
            score += 1

    # Component 5: Dice weight (+1)
    if (
        any_urgent
        and current_outcome is not None
        and current_outcome.rolled
        and current_outcome.band in ("crit_fail", "fail")
    ):
        score += 1

    return score


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

    # Build summary for logging
    parts = [directive] if directive else []
    summary = ", ".join(parts) or "neutral"

    return PacingContext(
        directive=directive or "",
        outcome_hint=outcome_hint,
        summary=summary,
    )


def _compute_ages(state: dict[str, Any]) -> dict[str, int]:
    """Compute age/staleness counters for narration directives."""
    meta = state.get("meta") or {}
    scene = state.get("scene") or {}
    current_turn = meta.get("turn", 0)

    scene_entered = scene.get("turn_entered", 0)
    scene_age = current_turn - scene_entered

    return {
        "scene_age": scene_age,
    }


def _compute_scene_phase(
    state: dict[str, Any],
    ages: dict[str, int],
    config: EngineConfig,
    convergence_score: int = 0,
) -> dict[str, Any]:
    """Compute the scene phase using the 5-state machine.

    Transitions: SETUP→RISING, RISING→CLIMAX, CLIMAX→RESOLUTION,
    RESOLUTION→BREATHER, BREATHER→RISING.

    Mutates state["scene"] in place. Returns the updated scene dict.
    """
    scene = state.setdefault("scene", {})

    # Initialize new fields if missing
    scene.setdefault("scene_phase", "SETUP")
    scene.setdefault("climax_turn_count", 0)
    scene.setdefault("breather_turn_count", 0)
    scene.setdefault("turns_in_phase", 0)

    phase = scene.get("scene_phase", "SETUP")
    climax_turn_count = scene.get("climax_turn_count", 0)
    breather_turn_count = scene.get("breather_turn_count", 0)
    turns_in_phase = scene.get("turns_in_phase", 0) + 1

    # Count urgent threads
    _raw_threads = (state.get("long_term_objective") or {}).get("threads") or []
    thread_urgency_count = 0
    for t in _raw_threads:
        if isinstance(t, dict) and getattr(ArcThread.model_validate(t) if not isinstance(t, ArcThread) else t, "urgency", "normal") == "urgent":
            thread_urgency_count += 1

    # Phase transition logic
    if phase == "SETUP":
        if thread_urgency_count > 0 or turns_in_phase >= 3:
            phase = "RISING"
            turns_in_phase = 0

    elif phase == "RISING":
        if convergence_score >= config.convergence_threshold:
            phase = "CLIMAX"
            climax_turn_count = 1
            turns_in_phase = 0

    elif phase == "CLIMAX":
        climax_turn_count += 1
        if climax_turn_count >= config.climax_turn_limit:
            phase = "RESOLUTION"
            climax_turn_count = 0
            turns_in_phase = 0

    elif phase == "RESOLUTION":
        phase = "BREATHER"
        breather_turn_count = 1
        turns_in_phase = 0

    elif phase == "BREATHER":
        breather_turn_count += 1
        if thread_urgency_count > 0 or breather_turn_count >= config.breather_max_turns:
            phase = "RISING"
            breather_turn_count = 0
            turns_in_phase = 0

    # Compute curtain_call after phase may have changed
    _curtain_call = ""
    if phase == "CLIMAX":
        if climax_turn_count >= config.climax_turn_limit - 1:
            _curtain_call = "forced"
        elif climax_turn_count == 1:
            _curtain_call = "active"

    return {**scene, "scene_phase": phase, "climax_turn_count": climax_turn_count, "breather_turn_count": breather_turn_count, "turns_in_phase": turns_in_phase, "curtain_call": _curtain_call}


def _recent_turn_count(state: dict[str, Any]) -> int:
    """Return max turns needed — now each consumer only needs 1 ([-1:] slice)."""
    return 1
