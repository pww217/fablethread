"""NPC roster assembly: build from compendium with presence filter."""

from __future__ import annotations

import logging
import re
from typing import Any

from ccya.models import NpcPresence

_log = logging.getLogger(__name__)


def build_npc_roster(
    comp: dict[str, Any],
    *,
    presence_filter: str | None = None,
    max_entries: int = 10,
    sort_by_lru: bool = False,
    lru_order: list[str] | None = None,
    personality_registry: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build sorted NPC roster from compendium, filtering by presence.

    Returns list of dicts with keys: id, name, title, bio, presence, motivation,
    fear, leverage, bond, notes, last_seen.
    """
    seen: dict[str, dict[str, Any]] = {}

    for nid, entry in comp.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("presence") == "archived":
            continue
        presence = entry.get("presence") or NpcPresence.KNOWN.value
        if presence_filter is not None and presence != presence_filter:
            continue
        name = entry.get("name") or ""
        if not name:
            continue
        seen[nid] = {
            "id": nid,
            "name": name,
            "title": _strip_non_ascii(entry.get("title") or ""),
            "bio": (entry.get("bio") or "").strip() or None,
            "presence": presence,
            "motivation": entry.get("motivation") or None,
            "fear": entry.get("fear") or None,
            "leverage": entry.get("leverage") or None,
            "bond": entry.get("bond") or None,
            "notes": entry.get("notes") or None,
            "last_seen": entry.get("last_seen") or None,
            "departed_reason": entry.get("departed_reason") or None,
        }

        if personality_registry and isinstance(entry, dict):
            arch_id = entry.get("personality")
            if arch_id and arch_id in personality_registry:
                arch = personality_registry[arch_id]
                seen[nid]["personality_label"] = getattr(arch, "label", arch_id)
                seen[nid]["personality_traits"] = ", ".join(getattr(arch, "traits", ())) if hasattr(arch, "traits") else ""
                seen[nid]["personality_speech_hint"] = getattr(arch, "speech_hint", "")

    order = {
        NpcPresence.PRESENT.value: 0,
        NpcPresence.NEARBY.value: 2,
        NpcPresence.KNOWN.value: 3,
        NpcPresence.DEPARTED.value: 5,
    }
    if sort_by_lru and lru_order:
        lru_idx = {nid: i for i, nid in enumerate(reversed(lru_order))}
        result = sorted(
            seen.values(),
            key=lambda e: (order.get(e["presence"], 3), lru_idx.get(e["id"], 9999)),
        )
    else:
        result = sorted(seen.values(), key=lambda e: (order.get(e["presence"], 3), e["name"]))

    result = result[:max_entries]
    _log.debug("build_npc_roster roster=%d", len(result))
    return result


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    return re.compile(r"[^\x00-\x7F]").sub("", text).strip()
