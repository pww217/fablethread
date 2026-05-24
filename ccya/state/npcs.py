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


NPC_SCENE_CAP = 8


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


def _apply_npc_to_present(npc: dict[str, Any], present: list[dict[str, Any]], comp: dict[str, Any], alias_map: dict[str, str]) -> str:
    """Add/update an NPC in present list. Returns resolved ID."""
    nid = npc["id"]
    resolved = _resolve_npc_id(nid, comp, alias_map)
    for i, p in enumerate(present):
        if p.get("id") == resolved:
            if npc.get("notes") is not None:
                present[i]["notes"] = npc["notes"]
            if npc.get("name") is not None and str(npc["name"]).strip():
                present[i]["name"] = str(npc["name"]).strip()
            if npc.get("title") is not None and str(npc["title"]).strip():
                present[i]["title"] = str(npc["title"]).strip()
            if npc.get("bio") is not None and str(npc["bio"]).strip():
                present[i]["bio"] = str(npc["bio"]).strip()
            return resolved
    ce = comp.get(resolved, {})
    row = {
        "id": resolved,
        "name": _hydrate_npc_text(npc.get("name"), ce.get("name")),
        "title": _hydrate_npc_text(npc.get("title"), ce.get("title")),
        "notes": npc.get("notes", ""),
        "bio": _hydrate_npc_text(npc.get("bio"), ce.get("bio")),
    }
    present.append(row)
    return resolved


def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
) -> dict[str, Any]:
    """Apply NPC scene deltas: add, remove, update present NPCs and compendium.

    Returns the mutated state dict. NPC_SCENE_CAP is enforced here.
    """
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})
    scene = state.setdefault("scene", {})
    old_present = list(state.get("scene", {}).get("present_npcs") or [])
    old_present_ids = {str(n.get("id", "")) for n in old_present if n.get("id")}
    new_present_ids: set[str] = set()

    has_npc_delta = bool(scene_result.npc_add or scene_result.npc_remove or scene_result.npc_update)
    if has_npc_delta:
        _log.debug(
            "apply_npc_scene_management turns=%s add=%d remove=%d update=%d compendium_update=%d",
            current_turn_no,
            len(scene_result.npc_add), len(scene_result.npc_remove),
            len(scene_result.npc_update), len(scene_result.compendium_npc_update),
        )
        alias_map = build_npc_alias_map(comp)
        present = list(old_present)

        removed_ids: set[str] = set()
        for npc_rem in scene_result.npc_remove:
            rid = _resolve_npc_id(npc_rem.id, comp, alias_map)
            npc_notes = ""
            for p in present:
                if p.get("id") == rid:
                    npc_notes = p.get("notes", "") or ""
                    break
            present = [p for p in present if p.get("id") != rid]
            removed_ids.add(rid)
            if rid in comp and npc_notes:
                existing_bio = (comp[rid].get("bio") or "").strip()
                if existing_bio:
                    comp[rid]["bio"] = f"{existing_bio} {npc_notes}"
                else:
                    comp[rid]["bio"] = npc_notes

        for npc_upd in scene_result.npc_update:
            _apply_npc_to_present(
                {"id": npc_upd.id, "notes": npc_upd.notes or "", "name": _strip_non_ascii(npc_upd.name or ""), "title": _strip_non_ascii(npc_upd.title or ""), "bio": _strip_non_ascii(npc_upd.bio or "")},
                present, comp, alias_map,
            )

        for add in scene_result.npc_add:
            add_id = add.id
            normalized_add = normalize_inventory_id(add_id)
            if normalized_add in alias_map and alias_map[normalized_add] != normalized_add:
                add_id = alias_map[normalized_add]
            if add.name:
                name_alias = add.name.lower().strip()
                if name_alias in alias_map and alias_map[name_alias] != name_alias:
                    add_id = alias_map[name_alias]
                if add_id not in comp:
                    name_match = _find_npc_by_name(add.name, comp)
                    if name_match:
                        add_id = name_match
            _apply_npc_to_present(
                {"id": add_id, "notes": add.notes or "", "name": _strip_non_ascii(add.name or ""), "title": _strip_non_ascii(add.title or ""), "bio": _strip_non_ascii(add.bio or "")},
                present, comp, alias_map,
            )
            entry = comp.setdefault(add_id, {})
            if add.name is not None and str(add.name).strip():
                entry["name"] = _strip_non_ascii(str(add.name).strip())
            elif "name" not in entry:
                entry["name"] = _hydrate_npc_text(add.name, entry.get("name"))
            if add.title is not None and str(add.title).strip():
                entry["title"] = _strip_non_ascii(str(add.title).strip())
            elif "title" not in entry:
                entry["title"] = _hydrate_npc_text(add.title, entry.get("title"))
            if add.bio is not None and str(add.bio).strip():
                entry["bio"] = _strip_non_ascii(str(add.bio).strip())
            elif "bio" not in entry:
                entry["bio"] = _hydrate_npc_text(add.bio, entry.get("bio"))
            touch_compendium_order(state, add_id)

        named_npcs = [p for p in present if p.get("id") != "ambient_crowd"]
        ambient_npcs = [p for p in present if p.get("id") == "ambient_crowd"]
        if len(named_npcs) > NPC_SCENE_CAP:
            evicted = named_npcs[NPC_SCENE_CAP:]
            named_npcs = named_npcs[:NPC_SCENE_CAP]
            present = named_npcs + ambient_npcs
            for evicted_npc in evicted:
                removed_ids.add(evicted_npc["id"])
            _log.debug("apply_npc_scene_management evicted=%d ids=%s", len(evicted), [e["id"] for e in evicted])

        scene["present_npcs"] = present
        new_present_ids = {str(p.get("id", "")) for p in present if p.get("id")}
    elif not old_present and comp:
        fallback_present: list[dict[str, Any]] = []
        for nid, entry in comp.items():
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            fallback_present.append({
                "id": nid,
                "name": name,
                "title": (entry.get("title") or "").strip(),
                "notes": "",
                "bio": (entry.get("bio") or "").strip(),
            })
        if fallback_present:
            scene["present_npcs"] = fallback_present[:NPC_SCENE_CAP]
            new_present_ids = {str(p.get("id", "")) for p in scene["present_npcs"] if p.get("id")}
        else:
            new_present_ids = set()
    else:
        new_present_ids = old_present_ids

    left_ids = old_present_ids - new_present_ids
    if left_ids:
        comp = state.get("compendium", {}).get("npcs", {})
        recently_left: list[dict[str, str]] = []
        for nid in sorted(left_ids):
            ce = comp.get(nid, {})
            recently_left.append({
                "id": nid,
                "name": ce.get("name", nid),
                "title": ce.get("title", ""),
            })
        scene["recently_left"] = recently_left
        scene.setdefault("recently_left_turns", 2)

    comp = state.setdefault("compendium", {}).setdefault("npcs", {})
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

        entry = comp.setdefault(resolved_id, {})
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

    return state
