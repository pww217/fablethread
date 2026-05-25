"""NPC roster assembly: merge present/known into a single list."""

from __future__ import annotations

import logging
from typing import Any

from ccya.models import NpcPresence


_log = logging.getLogger(__name__)


def build_npc_roster(
    present_npcs: list[dict[str, Any]],
    known_npcs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge present and known NPCs with priority PRESENT > KNOWN."""
    seen: dict[str, dict[str, Any]] = {}

    for n in present_npcs:
        nid = n.get("id", "")
        if not nid:
            continue
        seen[nid] = {
            "id": nid,
            "name": n.get("name") or "",
            "title": n.get("title") or "",
            "bio": (n.get("bio") or "").strip() or None,
            "presence": NpcPresence.PRESENT.value,
            "motivation": n.get("motivation") or None,
            "fear": n.get("fear") or None,
            "leverage": n.get("leverage") or None,
            "bond": n.get("bond") or None,
            "notes": n.get("notes") or None,
            "last_seen": None,
        }

    for n in known_npcs:
        nid = n.get("id", "")
        if not nid or nid in seen:
            continue
        seen[nid] = {
            "id": nid,
            "name": n.get("name") or "",
            "title": n.get("title") or "",
            "bio": n.get("bio") or None,
            "presence": NpcPresence.KNOWN.value,
            "motivation": n.get("motivation") or None,
            "fear": n.get("fear") or None,
            "leverage": n.get("leverage") or None,
            "bond": n.get("bond") or None,
            "notes": None,
            "last_seen": n.get("last_seen") or None,
        }

    order = {
        NpcPresence.PRESENT.value: 0,
        NpcPresence.NEARBY.value: 2,
        NpcPresence.KNOWN.value: 3,
    }
    result = sorted(seen.values(), key=lambda e: (order.get(e["presence"], 3), e["name"]))
    NPC_SCENE_CAP = 8
    if len(result) > NPC_SCENE_CAP:
        _log.warning("build_npc_roster merged roster size %d exceeds cap %d", len(result), NPC_SCENE_CAP)
    else:
        _log.info("build_npc_roster complete roster=%d", len(result))
    return result
