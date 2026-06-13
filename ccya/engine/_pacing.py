"""Shared pacing helpers: beat constraint map, phase-driven beat derivation.

This module encapsulates the beat constraint table in Python so both
`turn.py` (phase engine, directive computation) and `extraction.py`
(storytell context) can import it without circular imports.
"""

from __future__ import annotations

from ccya.engine.config import EngineConfig


BEAT_PHASE_MAP: dict[str, list[str]] = {
    "SETUP":       ["pressure", "complication", "escalation", "revelation", "twist", "opportunity", "callback", "breathing_room", "hazard"],
    "RISING":      ["pressure", "complication", "escalation", "revelation", "twist"],
    "CRISIS":      ["pressure", "escalation", "complication"],
    "RESOLUTION":  ["breathing_room", "callback", "revelation"],
    "BREATHER":    ["opportunity", "revelation", "callback", "breathing_room", "hazard"],
}


def derive_allowed_beat_types(scene_phase: str, *, enforce_relief: bool = False) -> list[str]:
    """Return the list of allowed beat types for the given scene phase.

    When enforce_relief is True and phase is CRISIS, returns only breathing_room.
    """
    if scene_phase == "CRISIS" and enforce_relief:
        return ["breathing_room"]
    return BEAT_PHASE_MAP.get(scene_phase, list(BEAT_PHASE_MAP["SETUP"]))


def derive_enforce_relief(scene_phase: str, consecutive_pressure_beats: int, config: EngineConfig) -> bool:
    """Return True when CRISIS phase has had enough consecutive pressure beats to force relief."""
    return scene_phase == "CRISIS" and consecutive_pressure_beats >= config.consecutive_pressure_threshold
