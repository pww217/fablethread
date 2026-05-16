"""NPC roster assembly: merge present/known/recently_left into a single list."""

from __future__ import annotations

from typing import Any

from ccya.models import NpcPresence


def build_npc_roster(
    present_npcs: list[dict[str, Any]],
    known_npcs: list[dict[str, Any]],
    recently_left: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Merge present, known, and recently_left NPCs into one ordered list.

    Priority order: PRESENT > JUST_LEFT > KNOWN.
    Dedup by id — the highest-priority presence wins.

    Returns a list of dicts suitable for Jinja rendering (not RosterEntry dataclass
    instances), with keys: id, name, title, bio, presence, motivation, fear,
    leverage, notes, last_seen.
    """
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
            "notes": n.get("notes") or None,
            "last_seen": None,
        }

    for n in recently_left:
        nid = n.get("id", "") if isinstance(n, dict) else ""
        if not nid or nid in seen:
            continue
        seen[nid] = {
            "id": nid,
            "name": n.get("name") or "",
            "title": n.get("title") or "",
            "bio": None,
            "presence": NpcPresence.JUST_LEFT.value,
            "motivation": None,
            "fear": None,
            "leverage": None,
            "notes": None,
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
            "notes": None,
            "last_seen": n.get("last_seen") or None,
        }

    order = {
        NpcPresence.PRESENT.value: 0,
        NpcPresence.JUST_LEFT.value: 1,
        NpcPresence.NEARBY.value: 2,
        NpcPresence.KNOWN.value: 3,
    }
    return sorted(seen.values(), key=lambda e: (order.get(e["presence"], 3), e["name"]))
