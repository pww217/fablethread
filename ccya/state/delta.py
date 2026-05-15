"""State delta application: apply_delta, reconcile_delta."""

from __future__ import annotations

import copy
import logging
import re
from typing import Any

from ccya.models import StateDelta
from ccya.state.inventory import (
    _fuzzy_match_inventory,
    normalize_inventory_id,
    resolve_inventory_canonical_id,
    resolve_inventory_remove_target,
)
from ccya.state.npcs import build_npc_alias_map, touch_compendium_order

_NAME_RE = re.compile(r"[^\x00-\x7F]")

_DEFAULT_CONDITION_TTL = 10
"""Default TTL in turns for conditions added without an explicit turns_remaining."""


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    result = _NAME_RE.sub("", text).strip()
    return result


_log = logging.getLogger("ccya.state")

PC_CONDITIONS_MAX: int = 5
"""Hard cap on simultaneous pc.conditions; oldest is evicted FIFO when exceeded."""


def _item_to_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        out = dict(item)
        if out.get("amount") is None or int(out.get("amount", 0) or 0) < 1:
            out["amount"] = 1
        return out
    amt = getattr(item, "amount", 1)
    result: dict[str, Any] = {
        "id": item.id,
        "name": item.name,
        "notes": item.notes,
        "amount": max(1, int(amt or 1)),
    }
    aliases = getattr(item, "aliases", None)
    if aliases:
        result["aliases"] = list(aliases)
    return result


def reconcile_delta(state: dict[str, Any], delta: StateDelta) -> list[str]:
    """Validate and clean `delta` against current `state`.

    Returns a list of warning strings for logging.
    Mutates delta in place.
    """
    warnings: list[str] = []

    # 1. Inventory: item in both add and remove -> drop from add
    add_ids = {i.id for i in delta.inventory_add}
    remove_ids = {r.id for r in delta.inventory_remove}
    conflict = add_ids & remove_ids
    if conflict:
        delta.inventory_add = [i for i in delta.inventory_add if i.id not in conflict]
        warnings.append(f"inventory conflict (add+remove same turn): {sorted(conflict)}")

    # 2. Conditions: don't add a condition already active
    existing_conds = {
        c.get("id") for c in (state.get("pc") or {}).get("conditions") or []
        if isinstance(c, dict)
    }
    remove_ids = {r.id for r in delta.pc_condition_remove}
    dupes = [c for c in delta.pc_condition_add if c.id in existing_conds and c.id not in remove_ids]
    if dupes:
        delta.pc_condition_add = [c for c in delta.pc_condition_add if c.id not in existing_conds and c.id not in remove_ids]
        warnings.append(f"duplicate condition add ignored: {[c.id for c in dupes]}")

    return warnings


def apply_delta(
    state: dict[str, Any], delta: StateDelta, *, recent_events_max: int = 20
) -> tuple[dict[str, Any], bool]:
    state = copy.deepcopy(state)

    inv: list[dict[str, Any]] = copy.deepcopy(state.get("inventory", []))
    for it in inv:
        if it.get("amount") is None or int(it.get("amount", 0) or 0) < 1:
            it["amount"] = 1

    def _by_id() -> dict[str, dict[str, Any]]:
        return {i["id"]: i for i in inv}

    by_id = _by_id()

    for item in delta.inventory_add:
        d = _item_to_dict(item)
        d["name"] = _strip_non_ascii(d.get("name", item.id))
        amt = max(1, int(d.get("amount") or 1))
        canonical = resolve_inventory_canonical_id(inv, item.id)
        target_id = canonical if canonical else item.id
        if target_id in by_id:
            ex = by_id[target_id]
            ex["amount"] = int(ex.get("amount", 1)) + amt
            if d.get("notes"):
                ex["notes"] = d["notes"]
            if d.get("aliases"):
                existing_aliases = set(ex.get("aliases") or [])
                for a in d["aliases"]:
                    if a.lower() not in {x.lower() for x in existing_aliases}:
                        existing_aliases.add(a.lower())
                ex["aliases"] = list(existing_aliases)
        else:
            # Fuzzy match safety net: check if name matches existing item
            fuzzy_id = _fuzzy_match_inventory(d.get("name", item.id), inv)
            if fuzzy_id and fuzzy_id in by_id:
                ex = by_id[fuzzy_id]
                ex["amount"] = int(ex.get("amount", 1)) + amt
                if d.get("notes"):
                    ex["notes"] = d["notes"]
                if d.get("aliases"):
                    existing_aliases = set(ex.get("aliases") or [])
                    for a in d["aliases"]:
                        if a.lower() not in {x.lower() for x in existing_aliases}:
                            existing_aliases.add(a.lower())
                    ex["aliases"] = list(existing_aliases)
                _log.info(
                    "inventory fuzzy merge: %s → %s (score via _fuzzy_match_inventory)",
                    d.get("name", item.id),
                    fuzzy_id,
                )
            else:
                d["amount"] = amt
                d["id"] = target_id
                inv.append(d)
                by_id = _by_id()

    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv, rem.id)
        if not canonical:
            continue
        ex = by_id[canonical]
        if rem.amount is None:
            inv = [x for x in inv if x.get("id") != canonical]
        else:
            amt_raw = int(rem.amount)
            if amt_raw <= 0:
                _log.warning(
                    "inventory_remove amount=%r coerced to full remove for %s",
                    rem.amount,
                    canonical,
                )
                inv = [x for x in inv if x.get("id") != canonical]
            else:
                cur = int(ex.get("amount", 1))
                new_amt = max(0, cur - amt_raw)
                if new_amt <= 0:
                    inv = [x for x in inv if x.get("id") != canonical]
                else:
                    ex["amount"] = new_amt
        by_id = _by_id()

    for u in delta.inventory_update:
        canonical = resolve_inventory_canonical_id(inv, u.id)
        if not canonical:
            continue
        ex = by_id[canonical]
        if u.name is not None:
            ex["name"] = _strip_non_ascii(u.name)
        if u.notes is not None:
            ex["notes"] = u.notes

    inv.sort(key=lambda x: 0 if x.get("id") == "credits" else 1)
    state["inventory"] = inv

    if delta.location_change:
        state["location"] = {
            "id": delta.location_change.id,
            "name": _strip_non_ascii(delta.location_change.name),
            "description": delta.location_change.description,
        }
        state.setdefault("scene", {})["present_npcs"] = []
        state.setdefault("scene", {})["recently_left"] = []
        state.setdefault("scene", {})["recently_left_turns"] = 0
        state["scene"]["turn_entered"] = state.get("meta", {}).get("turn", 0)
        state["scene"]["location_entered_turn"] = state.get("meta", {}).get("turn", 0)
    elif delta.location_description:
        state.setdefault("location", {})["description"] = delta.location_description

    current_turn = (state.get("meta") or {}).get("turn", 0)

    state.setdefault("pc", {}).setdefault("conditions", [])
    existing_conds: list[dict[str, Any]] = []
    for c in state["pc"]["conditions"]:
        if isinstance(c, dict):
            existing_conds.append(c)
        elif isinstance(c, str):
            cid = c.lower().strip().replace(" ", "_")
            existing_conds.append({"id": cid, "label": c, "description": "", "added_turn": 0})
    remove_ids = {r.id for r in delta.pc_condition_remove}
    existing_conds = [c for c in existing_conds if c.get("id") not in remove_ids]
    existing_ids = {c.get("id") for c in existing_conds}
    for ca in delta.pc_condition_add:
        cid = ca.id
        if not cid or cid in existing_ids:
            continue
        cond_dict = {
            "id": cid,
            "label": ca.label,
            "description": ca.description,
            "added_turn": current_turn,
        }
        if ca.turns_remaining is not None:
            cond_dict["turns_remaining"] = ca.turns_remaining
        else:
            cond_dict["turns_remaining"] = _DEFAULT_CONDITION_TTL
        existing_conds.append(cond_dict)
        existing_ids.add(cid)
    state["pc"]["conditions"] = existing_conds[-PC_CONDITIONS_MAX:]

    current_turn = (state.get("meta") or {}).get("turn", 0)
    scene = state.setdefault("scene", {})
    existing_events: list[dict[str, Any]] = list(scene.get("recent_events") or [])

    # Remove by ID
    for rid in delta.recent_events_remove:
        existing_events = [e for e in existing_events if e.get("id") != rid]

    # Update by ID
    for upd in delta.recent_events_update:
        for i, e in enumerate(existing_events):
            if e.get("id") == upd.id:
                existing_events[i]["text"] = _strip_non_ascii(upd.text)
                break

    # Add — reject if ID already exists
    existing_ids = {e.get("id") for e in existing_events}
    for evt in delta.recent_events_add:
        if evt.id not in existing_ids:
            existing_events.append({
                "id": evt.id,
                "text": _strip_non_ascii(evt.text),
                "turn": evt.turn or current_turn,
            })
            existing_ids.add(evt.id)

    # Evict oldest by turn (sort ascending, drop oldest)
    existing_events.sort(key=lambda e: e.get("turn", 0))
    recent_events_evicted = len(existing_events) > recent_events_max
    scene["recent_events"] = existing_events[-recent_events_max:]

    # --- scene_pressure ---
    pressures = list(scene.setdefault("scene_pressure", []))
    pressure_ids = {p.get("id") for p in pressures if isinstance(p, dict)}

    # Remove by ID
    for rid in delta.scene_pressure_remove:
        pressures = [p for p in pressures if p.get("id") != rid]
        pressure_ids.discard(rid)

    # Update by ID
    for upd in delta.scene_pressure_update:
        for i, p in enumerate(pressures):
            if isinstance(p, dict) and p.get("id") == upd.id:
                if upd.text:
                    pressures[i]["text"] = _strip_non_ascii(upd.text)
                if upd.urgency:
                    pressures[i]["urgency"] = upd.urgency
                break

    # Add — reject if ID already exists
    for press in delta.scene_pressure_add:
        if press.id not in pressure_ids:
            pressures.append({
                "id": press.id,
                "text": _strip_non_ascii(press.text),
                "urgency": press.urgency or "background",
                "turn_added": press.turn_added or current_turn,
                "max_turns": press.max_turns,
            })
            pressure_ids.add(press.id)

    scene["scene_pressure"] = pressures

    if delta.scene_tags:
        state["scene"]["tags"] = delta.scene_tags
        new_tags = set(delta.scene_tags)
        old_tags = set(state.get("scene", {}).get("tags") or [])
        if "combat" in new_tags and "combat" not in old_tags:
            state["scene"]["combat_started_turn"] = state.get("meta", {}).get("turn", 0)
        elif "combat" not in new_tags and "combat" in old_tags:
            state["scene"].pop("combat_started_turn", None)

    if delta.scene_tagline is not None:
        state.setdefault("scene", {})["tagline"] = _strip_non_ascii(delta.scene_tagline)

    # --- NPC scene management (delta-based: npc_add/npc_remove/npc_update) ---
    NPC_SCENE_CAP = 8
    old_present: list[dict[str, Any]] = list(state.get("scene", {}).get("present_npcs") or [])
    old_present_ids: set[str] = {str(n.get("id", "")) for n in old_present if n.get("id")}
    scene = state.setdefault("scene", {})
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})
    new_present_ids: set[str] = set()

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

    has_npc_delta = bool(delta.npc_add or delta.npc_remove or delta.npc_update)
    if has_npc_delta:
        alias_map = build_npc_alias_map(comp)
        present = list(old_present)

        removed_ids: set[str] = set()
        for rem in delta.npc_remove:
            rid = _resolve_npc_id(rem.id, comp, alias_map)
            present = [p for p in present if p.get("id") != rid]
            removed_ids.add(rid)
            # Store last_seen_state on compendium entry
            if rid in comp and rem.last_seen_state:
                comp[rid]["last_seen_state"] = rem.last_seen_state

        for upd in delta.npc_update:
            _apply_npc_to_present(
                {"id": upd.id, "notes": upd.notes or "", "name": _strip_non_ascii(upd.name or ""), "title": _strip_non_ascii(upd.title or ""), "bio": _strip_non_ascii(upd.bio or "")},
                present, comp, alias_map,
            )

        for add in delta.npc_add:
            # Check alias map before adding — prevent duplicate entries
            add_id = add.id
            normalized_add = normalize_inventory_id(add_id)
            if normalized_add in alias_map and alias_map[normalized_add] != normalized_add:
                add_id = alias_map[normalized_add]
            if add.name:
                name_alias = add.name.lower().strip()
                if name_alias in alias_map and alias_map[name_alias] != name_alias:
                    add_id = alias_map[name_alias]
                # Name collision: if ID is new but name matches existing NPC, route to existing
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

        scene["present_npcs"] = present
        new_present_ids = {str(p.get("id", "")) for p in present if p.get("id")}
    elif not old_present and comp:
        # No NPC deltas and compendium has NPCs — auto-populate present_npcs
        # (e.g., seed-generated NPCs on turn 0 that extraction didn't emit as npc_add)
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
    for u in delta.compendium_npc_update:
        nid = normalize_inventory_id(u.id)

        # Alias map lookup: if incoming name/id matches existing NPC alias, route to canonical
        resolved_id = nid
        # Check if the provided ID (normalized) maps to a different canonical ID
        if nid in alias_map and alias_map[nid] != nid:
            resolved_id = alias_map[nid]
        # Check if the NPC name matches any existing alias
        if u.name:
            name_alias = u.name.lower().strip()
            if name_alias in alias_map:
                resolved_id = alias_map[name_alias]
            # Name collision: if ID is new but name matches existing NPC, route to existing
            if resolved_id not in comp:
                name_match = _find_npc_by_name(u.name, comp)
                if name_match:
                    resolved_id = name_match

        entry = comp.setdefault(resolved_id, {})
        if u.name is not None:
            entry["name"] = _strip_non_ascii(u.name)
        if u.title is not None:
            entry["title"] = _strip_non_ascii(u.title)
        if u.bio is not None:
            entry["bio"] = _strip_non_ascii(u.bio)
        if u.aliases:
            existing_aliases = set(entry.get("aliases") or [])
            for a in u.aliases:
                if a.lower() not in {x.lower() for x in existing_aliases}:
                    existing_aliases.add(a.lower())
            entry["aliases"] = list(existing_aliases)
        if u.allegiance is not None:
            entry["allegiance"] = u.allegiance
        if u.motivation is not None:
            entry["motivation"] = u.motivation
        if u.fear is not None:
            entry["fear"] = u.fear
        if u.leverage is not None:
            entry["leverage"] = u.leverage
        touch_compendium_order(state, resolved_id)

    return state, recent_events_evicted
