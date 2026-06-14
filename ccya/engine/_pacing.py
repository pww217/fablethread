"""Shared pacing helpers: beat constraint map, phase-driven beat derivation.

This module encapsulates the beat constraint table in Python so both
`turn.py` (phase engine, directive computation) and `extraction.py`
(storytell context) can import it without circular imports.
"""

from __future__ import annotations

from typing import Any, TypedDict

from ccya.engine.config import EngineConfig


BEAT_BUCKETS: dict[str, list[str]] = {
    "pressure":  ["pressure", "complication", "escalation"],
    "situation": ["revelation", "twist", "hazard", "callback"],
    "relief":    ["opportunity", "breathing_room"],
}

BEAT_PHASE_MAP: dict[str, list[str]] = {
    "SETUP":       ["pressure", "complication", "escalation", "revelation", "twist", "opportunity", "callback", "breathing_room", "hazard"],
    "RISING":      ["pressure", "complication", "escalation", "revelation", "twist"],
    "CRISIS":      ["pressure", "escalation", "complication"],
    "RESOLUTION":  ["breathing_room", "callback", "revelation"],
    "BREATHER":    ["opportunity", "revelation", "callback", "breathing_room", "hazard"],
}


class RollRecord(TypedDict):
    turn: int
    band: str


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
    enforce_relief: bool = False,
) -> list[str]:
    """Return the list of allowed beat types for the given scene phase.

    Priority order:
    1. Scene Imperative directive → situation-changers + opportunity
    2. Breathe directive → relief + revelation + callback
    3. Spiral detected → phase defaults minus pressure bucket
    4. enforce_relief + CRISIS → only breathing_room (existing)
    5. Fallback → phase defaults
    """
    if directive == "Scene Imperative":
        return BEAT_BUCKETS["situation"] + ["opportunity"]

    if directive == "Breathe":
        return BEAT_BUCKETS["relief"] + ["revelation", "callback"]

    if scene_phase == "CRISIS" and enforce_relief:
        return ["breathing_room"]

    base = BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))

    if spiral_detected:
        pressure_types = set(BEAT_BUCKETS["pressure"])
        return [b for b in base if b not in pressure_types]

    return base


def derive_enforce_relief(scene_phase: str, consecutive_pressure_beats: int, config: EngineConfig) -> bool:
    """Return True when CRISIS phase has had enough consecutive pressure beats to force relief."""
    return scene_phase == "CRISIS" and consecutive_pressure_beats >= config.consecutive_pressure_threshold
