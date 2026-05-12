"""Scene pressure expiry and urgency escalation."""

from __future__ import annotations

import logging
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.models import StateDelta

_log = logging.getLogger("ccya.engine")


def _expire_scene_pressures(
    state: dict[str, Any], delta: StateDelta, config: EngineConfig | None = None, avoidance: bool = False
) -> None:
    """Remove expired pressures and escalate urgency based on age.

    Expired = current_turn - turn_added >= max_turns (if set).
    Escalation: background → building at config threshold, building → immediate at config threshold.
    Pressures without a valid turn_added (0 or missing) are skipped — they predate
    this tracking and should not be auto-expired.

    When avoidance=True, non-immediate pressures get an extra age increment
    (simulating time passing while the player creates distance).
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    removed_ids: set[str] = set()
    building_at = 6
    immediate_at = 10
    if config:
        building_at = config.scene_pressure_building_at
        immediate_at = config.scene_pressure_immediate_at

    avoidance_bonus = (config.avoidance_decay_per_turn if config else 1) if avoidance else 0

    # Skip IDs already removed by _purge_scene_pressures (same state read,
    # prevents duplicate entries in delta.scene_pressure_remove).
    already_removed: set[str] = set(delta.scene_pressure_remove)
    for p in pressures:
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        if pid in already_removed:
            continue
        turn_added = p.get("turn_added")
        # Skip pressures without turn_added — they predate this tracking.
        if turn_added is None or turn_added == 0:
            continue
        max_turns = p.get("max_turns")
        age = current_turn - turn_added
        urgency = p.get("urgency", "background")
        effective_age = age + (avoidance_bonus if urgency != "immediate" else 0)

        # Explicit max_turns (from scene_pressure_add) takes priority.
        if max_turns is not None and effective_age >= max_turns:
            removed_ids.add(pid)
            continue

        # Ambient/building pressures have a default TTL of 4 turns.
        # Immediate pressures do not have this cap — they persist until
        # explicitly removed by the extractor or by location/combat changes.
        if urgency in ("background", "building") and effective_age >= 4:
            # Escalate building → immediate instead of removing (gives the
            # extractor one more turn to react before forced removal).
            p["urgency"] = "immediate"
            p["turn_became_immediate"] = current_turn
            if p.get("max_turns") is None:
                immediate_ttl = config.scene_pressure_immediate_ttl if config else 8
                turn_added_val = p.get("turn_added") or current_turn
                p["max_turns"] = turn_added_val + effective_age + immediate_ttl
            _log.info(
                "pressure: escalated %r to immediate (from %s, effective_age=%d >= 4), max_turns=%s",
                pid, urgency, effective_age, p.get("max_turns"),
                extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "pressure"},
            )
            continue

        # Configurable escalation thresholds for building→immediate and background→building.
        # These only apply to pressures that survived the TTL cap above.
        if effective_age >= immediate_at and urgency == "building":
            p["urgency"] = "immediate"
            p["turn_became_immediate"] = current_turn
            if p.get("max_turns") is None:
                immediate_ttl = config.scene_pressure_immediate_ttl if config else 8
                turn_added_val = p.get("turn_added") or current_turn
                p["max_turns"] = turn_added_val + effective_age + immediate_ttl
            _log.info(
                "pressure: escalated %r to immediate (from building, effective_age=%d >= %d), max_turns=%s",
                pid, effective_age, immediate_at, p.get("max_turns"),
                extra={"turn": current_turn, "trace_id": "", "pack": "", "kind": "pressure"},
            )
        elif effective_age >= building_at and urgency == "background":
            p["urgency"] = "building"

    if removed_ids:
        delta.scene_pressure_remove.extend(sorted(removed_ids))


def _purge_scene_pressures(
    state: dict[str, Any], delta: StateDelta, *, location_changed: bool = False, combat_ended: bool = False, config: EngineConfig | None = None
) -> None:
    """Remove pressures that are no longer relevant.

    Called post-extraction, before _expire_scene_pressures.
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    max_age = (config.scene_pressure_max_age if config else 15)

    if location_changed:
        for p in pressures:
            if isinstance(p, dict):
                urgency = p.get("urgency", "background")
                if urgency == "background":
                    delta.scene_pressure_remove.append(p.get("id", ""))
        return

    removed: set[str] = set()
    for p in pressures:
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "")
        if pid in removed:
            continue
        # Age cap
        turn_added = p.get("turn_added")
        if turn_added and turn_added > 0 and (current_turn - turn_added) >= max_age:
            removed.add(pid)
            continue
        # Combat end — remove immediate threats
        if combat_ended and p.get("urgency") == "immediate":
            removed.add(pid)
            continue

    delta.scene_pressure_remove.extend(sorted(removed))
