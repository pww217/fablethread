"""NPC alias map, compendium order tracking, and scene management."""

from __future__ import annotations

import logging
from typing import Any

from ccya.models import SceneExtractResult
from ccya.state.inventory import normalize_inventory_id

_log = logging.getLogger(__name__)


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
            normalized = normalize_inventory_id(alias)
            result[normalized] = npc_id
    _log.debug("build_npc_alias_map npcs=%d entries=%d", len(npcs), len(result))
    return result


def touch_compendium_order(state: dict[str, Any], npc_id: str) -> None:
    nid = normalize_inventory_id(npc_id)
    order: list[str] = state.setdefault("meta", {}).setdefault(
        "compendium_touch_order", []
    )
    if nid in order:
        order.remove(nid)
    order.append(nid)
    _log.debug("touch_compendium_order npc=%s order_len=%d", npc_id, len(order))


def _strip_non_ascii(text: str) -> str:
    """Strip non-ASCII characters from text."""
    import re
    if not text:
        return text
    return re.compile(r"[^\x00-\x7F]").sub("", text).strip()


def _hydrate_npc_text(delta_val: str | None, stored: Any) -> str:
    st = str(stored).strip() if stored is not None else ""
    if delta_val is None:
        return st
    dv = str(delta_val).strip()
    if not dv:
        return st
    return dv


def _resolve_npc_id(nid: str, comp: dict[str, Any], alias_map: dict[str, str]) -> str:
    resolved = normalize_inventory_id(nid)
    if resolved in alias_map and alias_map[resolved] != resolved:
        resolved = alias_map[resolved]
    return resolved


def _find_npc_by_name(name: str, comp: dict[str, Any]) -> str | None:
    """Find an existing compendium NPC by name (case-insensitive). Returns canonical ID or None."""
    if not name:
        return None
    target = name.lower().strip()
    for npc_id, npc in comp.items():
        if not isinstance(npc, dict):
            continue
        existing_name = (npc.get("name") or "").lower().strip()
        if existing_name and existing_name == target:
            return npc_id
    return None


def strip_npcs_notes(state: dict[str, Any]) -> None:
    """Clear notes from all NPCs in the compendium.

    Notes are present-tense/this-turn-only — scene_extractor creates fresh ones each turn.
    Mutates state in-place so ruling/narration/extraction all see a clean slate.
    """
    npcs = (state.get("compendium") or {}).get("npcs", {})
    for npc_id, entry in npcs.items():
        if isinstance(entry, dict) and entry.get("presence") not in ("departed", "archived"):
            entry.pop("notes", None)


def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
) -> dict[str, Any]:
    """Apply compendium_npc_update entries to compendium.npcs.

    Returns the mutated state dict. Compendium entries are merged into state.
    """
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})

    if scene_result.compendium_npc_update:
        _log.debug(
            "apply_npc_scene_management turns=%s compendium_update=%d",
            current_turn_no,
            len(scene_result.compendium_npc_update),
        )
        alias_map = build_npc_alias_map(comp)

        for comp_upd in scene_result.compendium_npc_update:
            nid = normalize_inventory_id(comp_upd.id)
            resolved_id = nid
            if nid in alias_map and alias_map[nid] != nid:
                resolved_id = alias_map[nid]
            if comp_upd.name:
                name_alias = comp_upd.name.lower().strip()
                if name_alias in alias_map:
                    resolved_id = alias_map[name_alias]
                if resolved_id not in comp:
                    name_match = _find_npc_by_name(comp_upd.name, comp)
                    if name_match:
                        resolved_id = name_match

            is_new = resolved_id not in comp
            entry = comp.setdefault(resolved_id, {})

            if is_new and current_turn_no is not None:
                entry["first_seen_turn"] = current_turn_no  # 0-based, matches narrate_user.j2 convention (T{{ npc.first_seen_turn }})
                location = state.get("location", {})
                entry["last_seen"] = {
                    "turn": current_turn_no,
                    "location_id": location.get("id", ""),
                    "location_name": location.get("name", ""),
                }

            if comp_upd.name is not None:
                entry["name"] = _strip_non_ascii(comp_upd.name)
            if comp_upd.title is not None:
                entry["title"] = _strip_non_ascii(comp_upd.title)
            if comp_upd.bio is not None:
                entry["bio"] = _strip_non_ascii(comp_upd.bio)
            if comp_upd.aliases:
                existing_aliases = set(entry.get("aliases") or [])
                for a in comp_upd.aliases:
                    if a.lower() not in {x.lower() for x in existing_aliases}:
                        existing_aliases.add(a.lower())
                entry["aliases"] = list(existing_aliases)
            if comp_upd.allegiance is not None:
                entry["allegiance"] = comp_upd.allegiance
            if comp_upd.motivation is not None:
                entry["motivation"] = comp_upd.motivation
            if comp_upd.fear is not None:
                entry["fear"] = comp_upd.fear
            if comp_upd.leverage is not None:
                entry["leverage"] = comp_upd.leverage
            if comp_upd.personality is not None and not entry.get("personality"):
                entry["personality"] = comp_upd.personality
                _log.debug(
                    "apply_npc_scene_management npc=%s personality=%s",
                    resolved_id, comp_upd.personality,
                )
            # Engine fallback: assign personality for named NPCs that still lack one.
            # Unnamed NPCs (alias-only, no proper name) are intentionally skipped.
            if not entry.get("personality") and entry.get("name"):
                entry_aliases = [a.lower() for a in (entry.get("aliases") or [])]
                if entry["name"].lower().strip() not in entry_aliases:
                    from ccya.personality import assign_personality
                    arch = assign_personality(
                        motivation=entry.get("motivation"),
                        fear=entry.get("fear"),
                        npc_id=resolved_id,
                    )
                    entry["personality"] = arch.id
            if comp_upd.presence is not None:
                entry["presence"] = comp_upd.presence
                if comp_upd.presence == "present":
                    touch_compendium_order(state, resolved_id)
                elif comp_upd.presence == "known":
                    entry.pop("notes", None)
            if comp_upd.presence == "departed":
                if comp_upd.departed_reason is not None:
                    entry["departed_reason"] = comp_upd.departed_reason
                if comp_upd.departed_summary is not None:
                    entry["departed_summary"] = comp_upd.departed_summary
                if current_turn_no is not None:
                    entry["departed_turn"] = entry.get("departed_turn", current_turn_no)
                entry.pop("notes", None)
            if comp_upd.presence == "nearby":
                if current_turn_no is not None:
                    entry["nearby_since_turn"] = entry.get("nearby_since_turn", current_turn_no)
            if comp_upd.notes is not None:
                entry["notes"] = comp_upd.notes
            if comp_upd.position is not None:
                entry["position"] = comp_upd.position

    return state
