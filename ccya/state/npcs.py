"""NPC alias map, compendium order tracking, and scene management."""

from __future__ import annotations

import logging
import re
from typing import Any

from ccya.models import SceneExtractResult
from ccya.state.inventory import normalize_inventory_id

_log = logging.getLogger(__name__)

# Spelled-out quantity words that may prefix group NPC IDs/names.
# Used to collapse "two_militia_guards" / "five_militia_guards" into
# the same underlying group NPC identity ("militia_guards").
_STRIPPLABLE_QUANTITIES = frozenset({
    "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen", "twenty",
    "a", "an",
})


def build_npc_alias_map(npcs: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Returns alias -> canonical_id mapping for NPCs.

    The canonical ID maps to itself; all aliases map to the canonical ID.
    Both raw and normalized (snake_case) forms of aliases are indexed.
    For group NPCs, also indexes the quantity-stripped ID so that
    "militia_guards" resolves to the canonical "militia_guards" entry.
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
    # Index quantity-stripped IDs for group NPC resolution.
    # For group NPCs, pick the canonical ID (lowest alphabetically among
    # quantity variants, or the one without a quantity prefix if it exists).
    stripped_to_canonical: dict[str, str] = {}
    for npc_id, npc in npcs.items():
        if not isinstance(npc, dict):
            continue
        stripped = _strip_quantity_suffix(npc_id)
        if stripped != npc_id:
            if stripped not in stripped_to_canonical:
                stripped_to_canonical[stripped] = npc_id
            else:
                # Pick the canonical one: prefer one without quantity prefix,
                # otherwise lowest alphabetically.
                current = stripped_to_canonical[stripped]
                current_stripped = _strip_quantity_suffix(current)
                if current_stripped == current:
                    # Current is already the canonical (no quantity)
                    pass
                elif _strip_quantity_suffix(npc_id) == npc_id:
                    # New one is canonical
                    stripped_to_canonical[stripped] = npc_id
                elif npc_id < current:
                    # New one is alphabetically lower
                    stripped_to_canonical[stripped] = npc_id
    for stripped, canonical in stripped_to_canonical.items():
        if stripped not in result:
            result[stripped] = canonical
    _log.debug("build_npc_alias_map npcs=%d entries=%d", len(npcs), len(result))
    return result


def _resolve_group_npc_id(nid: str, comp: dict[str, Any], alias_map: dict[str, str]) -> str:
    """Resolve a group NPC ID to a canonical entry, collapsing quantity variants.

    If the ID has a quantity prefix (e.g., "militia_guards_five"), find or
    create a canonical entry for the underlying type (e.g., "militia_guards").
    Returns the canonical ID to use.
    """
    # Strip quantity prefix for group NPC resolution — check alias map FIRST
    # so that "militia_guards_four" resolves to the canonical "militia_guards_five"
    # (or whatever the alias map points to) even if "militia_guards_four" exists
    # in the compendium.
    nid_stripped = _strip_quantity_suffix(nid)
    if nid_stripped != nid:
        # Check if stripped ID maps to an existing entry
        if nid_stripped in alias_map:
            return alias_map[nid_stripped]
        # Check if any existing entry strips to the same ID
        for existing_id in comp:
            existing_stripped = _strip_quantity_suffix(existing_id)
            if existing_stripped == nid_stripped:
                return existing_id

    # Direct match in compendium (for non-group NPCs or when no quantity match found)
    if nid in comp:
        return nid

    # Check alias map for non-stripped ID
    if nid in alias_map and alias_map[nid] != nid:
        return alias_map[nid]

    # No match found — return original ID (will create new entry)
    return nid


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
    if not text:
        return text
    return re.compile(r"[^\x00-\x7F]").sub("", text).strip()


def _strip_quantity_suffix(raw: str) -> str:
    """Strip quantity words from group-NPC IDs/names for matching.

    Collapses "militia_guards_five" -> "militia_guards",
    "militia_guards_two" -> "militia_guards", etc.
    Leaves non-group IDs untouched (e.g. "phillip_seon" -> "phillip_seon").
    """
    if not raw:
        return raw
    s = raw.lower().strip()
    parts = s.split("_")
    if parts and parts[-1] in _STRIPPLABLE_QUANTITIES:
        stripped = "_".join(parts[:-1])
        if stripped:
            return stripped
    return s


def _find_npc_by_name(name: str, comp: dict[str, Any]) -> str | None:
    """Find an existing compendium NPC by name (case-insensitive).

    For group NPCs, also tries matching the underlying type after stripping
    quantity prefixes (so "Five militia guards" matches "Two militia guards").
    Returns canonical ID or None.
    """
    if not name:
        return None
    target = name.lower().strip()
    target_stripped = _strip_quantity_suffix(target)
    for npc_id, npc in comp.items():
        if not isinstance(npc, dict):
            continue
        existing_name = (npc.get("name") or "").lower().strip()
        if existing_name and existing_name == target:
            return npc_id
        # Group-NPC quantity-agnostic match: strip quantities from both
        # sides and compare the underlying type.
        if existing_name:
            existing_stripped = _strip_quantity_suffix(existing_name)
            if target_stripped and existing_stripped and target_stripped == existing_stripped:
                return npc_id
    return None


def apply_npc_scene_management(
    state: dict[str, Any],
    scene_result: SceneExtractResult,
    current_turn_no: int | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """Apply compendium_npc_update entries to compendium.npcs.

    Returns the mutated state dict. Compendium entries are merged into state.
    """
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})

    if scene_result.compendium_npc_update:
        _log.info(
            "apply_npc_scene_management compendium_update=%d", len(scene_result.compendium_npc_update),
            extra={"trace_id": trace_id, "turn": current_turn_no},
        )
        alias_map = build_npc_alias_map(comp)

        for comp_upd in scene_result.compendium_npc_update:
            nid = normalize_inventory_id(comp_upd.id)
            resolved_id = _resolve_group_npc_id(nid, comp, alias_map)

            # Also try name-based resolution (with quantity stripping).
            if comp_upd.name:
                name_alias = comp_upd.name.lower().strip()
                if name_alias in alias_map:
                    resolved_id = alias_map[name_alias]
                if resolved_id not in comp:
                    name_match = _find_npc_by_name(comp_upd.name, comp)
                    if name_match:
                        resolved_id = name_match

            # Consolidate: if we resolved to a quantity-embedded ID that has
            # other duplicates, merge them into the canonical entry.
            if resolved_id in comp:
                resolved_stripped = _strip_quantity_suffix(resolved_id)
                if resolved_stripped != resolved_id:
                    # Find all other entries that strip to the same ID
                    to_merge = []
                    for other_id in comp:
                        if other_id != resolved_id:
                            other_stripped = _strip_quantity_suffix(other_id)
                            if other_stripped == resolved_stripped:
                                to_merge.append(other_id)
                    # Merge duplicates into the canonical entry
                    for merge_id in to_merge:
                        _log.debug(
                            "apply_npc_scene_management merging duplicate group NPC %s into %s",
                            merge_id, resolved_id,
                        )
                        merge_entry = comp.pop(merge_id, {})
                        # Keep the first-seen turn from the earliest entry
                        if "first_seen_turn" not in comp[resolved_id] and "first_seen_turn" in merge_entry:
                            comp[resolved_id]["first_seen_turn"] = merge_entry["first_seen_turn"]
                        if "last_presence_turn" not in comp[resolved_id] and "last_presence_turn" in merge_entry:
                            comp[resolved_id]["last_presence_turn"] = merge_entry["last_presence_turn"]
                        if "last_seen_location" not in comp[resolved_id] and "last_seen_location" in merge_entry:
                            comp[resolved_id]["last_seen_location"] = merge_entry["last_seen_location"]
                        # Merge aliases
                        existing_aliases = set(comp[resolved_id].get("aliases") or [])
                        for a in (merge_entry.get("aliases") or []):
                            if a.lower() not in {x.lower() for x in existing_aliases}:
                                existing_aliases.add(a.lower())
                        if existing_aliases:
                            comp[resolved_id]["aliases"] = list(existing_aliases)
                        # Rebuild alias map to include merged entries
                        alias_map = build_npc_alias_map(comp)

            is_new = resolved_id not in comp
            entry = comp.setdefault(resolved_id, {})

            if is_new and current_turn_no is not None:
                entry["first_seen_turn"] = current_turn_no  # 0-based, matches narrate_user.j2 convention (T{{ npc.first_seen_turn }})
                location = state.get("location", {})
                entry["last_presence_turn"] = current_turn_no
                entry["last_seen_location"] = location.get("name", "")

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
            if comp_upd.motivation is not None:
                entry["motivation"] = comp_upd.motivation
            if comp_upd.fear is not None:
                entry["fear"] = comp_upd.fear
            if comp_upd.leverage is not None:
                entry["leverage"] = comp_upd.leverage
            if comp_upd.bond is not None:
                entry["bond"] = comp_upd.bond
            if comp_upd.personality is not None and not entry.get("personality"):
                _name = (comp_upd.name or entry.get("name") or "").strip()
                _aliases = comp_upd.aliases or entry.get("aliases") or []
                # Strip leading quantity word for group NPCs (e.g. "Two guards" → "guards")
                _name_parts = _name.lower().split()
                if _name_parts and _name_parts[0] in _STRIPPLABLE_QUANTITIES:
                    _name_stripped = " ".join(_name_parts[1:])
                else:
                    _name_stripped = _name.lower()
                # Unnamed NPCs: stripped name matches an alias
                if _name_stripped and any(_name_stripped == a.lower().strip() for a in _aliases):
                    pass
                else:
                    entry["personality"] = comp_upd.personality
                    _log.info(
                        "npc_scene_management.applied npc=%s personality=%s",
                        resolved_id, comp_upd.personality,
                        extra={"trace_id": trace_id, "turn": current_turn_no},
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
                    entry.pop("position", None)
            if comp_upd.presence == "departed":
                if comp_upd.departed_reason is not None:
                    entry["departed_reason"] = comp_upd.departed_reason
                if current_turn_no is not None:
                    entry["departed_turn"] = entry.get("departed_turn", current_turn_no)
                entry.pop("position", None)
            if comp_upd.presence == "nearby":
                if current_turn_no is not None:
                    entry["last_presence_turn"] = current_turn_no
            if comp_upd.position is not None:
                entry["position"] = comp_upd.position

    return state
