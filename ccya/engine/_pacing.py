"""Shared pacing helpers: beat constraint map, phase-driven beat derivation.

This module encapsulates the beat constraint table in Python so both
`turn.py` (phase engine, directive computation) and `extraction.py`
(storytell context) can import it without circular imports.
"""

from __future__ import annotations

from math import ceil
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.models import RulesOutcome


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
