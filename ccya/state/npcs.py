"""NPC alias map and compendium order tracking."""

from __future__ import annotations

from typing import Any

from ccya.state.inventory import normalize_inventory_id


def build_npc_alias_map(npcs: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Returns alias -> canonical_id mapping for NPCs.

    The canonical ID maps to itself; all aliases map to the canonical ID.
    Both raw and normalized (snake_case) forms of aliases are indexed.
    """
    result: dict[str, str] = {}
    for npc_id, npc in npcs.items():
        if not isinstance(npc, dict):
            continue
        result[npc_id] = npc_id
        for alias in (npc.get("aliases") or []):
            if not isinstance(alias, str):
                continue
            result[alias.lower()] = npc_id
            # Also index the normalized form so "scarred soldier" matches "scarred_soldier"
            normalized = normalize_inventory_id(alias)
            result[normalized] = npc_id
    return result


def touch_compendium_order(state: dict[str, Any], npc_id: str) -> None:
    nid = normalize_inventory_id(npc_id)
    order: list[str] = state.setdefault("meta", {}).setdefault(
        "compendium_touch_order", []
    )
    if nid in order:
        order.remove(nid)
    order.append(nid)
