"""NPC roster assembly: build from compendium with presence filter."""

from __future__ import annotations

import logging
import re
from typing import Any

from ccya.models import NpcPresence

_log = logging.getLogger(__name__)


def _is_named(name: str) -> bool:
    """Heuristic: a proper name has 2+ words with first and last capitalized."""
    if not name:
        return False
    words = name.strip().split()
    if len(words) < 2:
        return False
    first_word = words[0]
    last_word = words[-1]
    return bool(first_word and first_word[0].isupper() and last_word and last_word[0].isupper())


def _compute_npc_score(entry: dict[str, Any], comp: dict[str, Any], turn_no: int) -> int:
    raw = comp.get(entry.get("id", ""), {})
    if raw.get("party") is True:
        return 6
    name = entry.get("name") or ""
    if name and not _is_named(name):
        return 0
    last_turn = entry.get("last_presence_turn")
    if last_turn is not None and turn_no > 0:
        turns_ago = turn_no - last_turn
        if turns_ago < 5:
            recency = 2
        elif turns_ago < 10:
            recency = 1
        else:
            recency = 0
    else:
        recency = 0
    richness = 0
    for field in ("motivation", "fear", "leverage", "tie"):
        val = entry.get(field)
        if val and val != "unknown":
            richness += 1
    return recency + richness


def build_npc_roster(
    comp: dict[str, Any],
    *,
    turn_no: int = 0,
    presence_filter: str | None = None,
    max_entries: int = 12,
    sort_by_lru: bool = False,
    lru_order: list[str] | None = None,
    slim: bool = False,
) -> list[dict[str, Any]]:
    """Build sorted NPC roster from compendium, filtering by presence.

    When slim=True, only includes id, name, title, presence.
    Otherwise returns list of dicts with keys: id, name, title, bio, presence, motivation,
    fear, leverage, tie, notes, last_presence_turn, last_seen_location,
    departed_reason.
    """
    seen: dict[str, dict[str, Any]] = {}

    for nid, entry in comp.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("presence") == "archived" and not entry.get("departed_reason"):
            continue
        presence = entry.get("presence") or NpcPresence.KNOWN.value
        if presence_filter is not None and presence != presence_filter:
            continue
        name = entry.get("name") or ""
        if not name:
            continue
        if slim:
            seen[nid] = {
                "id": nid,
                "name": name,
                "title": _strip_non_ascii(entry.get("title") or ""),
                "presence": presence,
            }
        else:
            seen[nid] = {
                "id": nid,
                "name": name,
                "title": _strip_non_ascii(entry.get("title") or ""),
                "bio": (entry.get("bio") or "").strip() or None,
                "presence": presence,
                "motivation": entry.get("motivation") or None,
                "fear": entry.get("fear") or None,
                "leverage": entry.get("leverage") or None,
                "tie": entry.get("tie") or None,
                "notes": entry.get("notes") or None,
                "last_presence_turn": entry.get("last_presence_turn"),
                "last_seen_location": entry.get("last_seen_location") or None,
                "departed_reason": entry.get("departed_reason") or None,
            }

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
            key=lambda e: (order.get(str(e.get("presence") or ""), 3), lru_idx.get(e["id"], 9999), -_compute_npc_score(e, comp, turn_no)),
        )
    else:
        result = sorted(seen.values(), key=lambda e: (order.get(str(e.get("presence") or ""), 3), -_compute_npc_score(e, comp, turn_no), -(e.get("last_presence_turn") or 0), e["name"]))

    result = result[:max_entries]
    _log.debug("build_npc_roster roster=%d", len(result))
    return result


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    return re.compile(r"[^\x00-\x7F]").sub("", text).strip()
