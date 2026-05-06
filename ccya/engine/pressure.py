"""Scene pressure expiry and urgency escalation."""

from __future__ import annotations

from typing import Any

from ccya.engine.config import EngineConfig
from ccya.models import StateDelta


def _expire_scene_pressures(
    state: dict[str, Any], delta: StateDelta, config: EngineConfig | None = None
) -> None:
    """Remove expired pressures and escalate urgency based on age.

    Expired = current_turn - turn_added >= max_turns (if set).
    Escalation: background → building at config threshold, building → immediate at config threshold.
    Pressures without a valid turn_added (0 or missing) are skipped — they predate
    this tracking and should not be auto-expired.
    """
    pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
    current_turn = (state.get("meta") or {}).get("turn", 0)
    removed_ids: set[str] = set()
    building_at = 6
    immediate_at = 10
    if config:
        building_at = config.scene_pressure_building_at
        immediate_at = config.scene_pressure_immediate_at

    for p in pressures:
        if not isinstance(p, dict):
            continue
        turn_added = p.get("turn_added")
        # Skip pressures without turn_added — they predate this tracking.
        if turn_added is None or turn_added == 0:
            continue
        max_turns = p.get("max_turns")
        if max_turns is not None and (current_turn - turn_added) >= max_turns:
            removed_ids.add(p.get("id", ""))
            continue
        age = current_turn - turn_added
        urgency = p.get("urgency", "background")
        if age >= immediate_at and urgency == "building":
            p["urgency"] = "immediate"
        elif age >= building_at and urgency == "background":
            p["urgency"] = "building"

    if removed_ids:
        delta.scene_pressure_remove.extend(sorted(removed_ids))