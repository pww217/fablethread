"""Scene pressure expiry and urgency escalation."""

from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig

_log = logging.getLogger("ccya.engine")


def _expire_scene_pressures(
    state: dict[str, Any], delta: Any, config: EngineConfig | None = None, avoidance: bool = False
) -> None:
    """Remove expired pressures and escalate urgency based on age.

    NOTE: scene_pressure fields removed from StateDelta in Phase 01 migration.
    This module operates directly on state.scene_pressure[] for now; delta-based
    pressure operations will be consolidated into unified thread operations in
    later phases (04-05).
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    building_at = 6
    immediate_at = 10
    if config:
        building_at = config.scene_pressure_building_at
        immediate_at = config.scene_pressure_immediate_at

    avoidance_bonus = (config.avoidance_decay_per_turn if config else 1) if avoidance else 0

    for p in pressures:
        if not isinstance(p, dict):
            continue
        turn_added = p.get("turn_added")
        # Skip pressures without turn_added — they predate this tracking.
        if turn_added is None or turn_added == 0:
            continue
        max_turns = p.get("max_turns")
        age = current_turn - turn_added
        urgency = p.get("urgency", "background")
        effective_age = age + (avoidance_bonus if urgency != "immediate" else 0)

        # Explicit max_turns takes priority.
        if max_turns is not None and effective_age >= max_turns:
            continue

        # Configurable escalation thresholds for background→building and
        # building→immediate.
        if effective_age >= immediate_at and urgency == "building":
            p["urgency"] = "immediate"
            p["turn_became_immediate"] = current_turn
            if p.get("max_turns") is None:
                immediate_ttl = config.scene_pressure_immediate_ttl if config else 8
                turn_added_val = p.get("turn_added") or current_turn
                p["max_turns"] = turn_added_val + effective_age + immediate_ttl
        elif effective_age >= building_at and urgency == "background":
            p["urgency"] = "building"


def _purge_scene_pressures(
    state: dict[str, Any], delta: Any, *, location_changed: bool = False, combat_ended: bool = False, config: EngineConfig | None = None
) -> None:
    """Remove pressures that are no longer relevant.

    Called post-extraction, before _expire_scene_pressures.

    NOTE: scene_pressure fields removed from StateDelta in Phase 01 migration.
    This module operates directly on state.scene_pressure[] for now; delta-based
    pressure operations will be consolidated into unified thread operations in
    later phases (04-05).
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    max_age = (config.scene_pressure_max_age if config else 8)

    if location_changed:
        for p in pressures:
            if isinstance(p, dict):
                urgency = p.get("urgency", "background")
                if urgency == "background":
                    continue
        return

    for p in pressures:
        if not isinstance(p, dict):
            continue
        # Age cap
        turn_added = p.get("turn_added")
        if turn_added and turn_added > 0 and (current_turn - turn_added) >= max_age:
            continue
        # Combat end — remove immediate threats
        if combat_ended and p.get("urgency") == "immediate":
            continue
