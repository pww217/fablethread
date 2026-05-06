"""State I/O: load/save YAML state, append events.jsonl, chronicle.md."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

from ccya.models import StateDelta

_log = logging.getLogger("ccya.state")


def load_state(save_dir: Path) -> dict[str, Any]:
    path = save_dir / "state.yaml"
    if not path.exists():
        return _default_state()
    with open(path) as f:
        raw = yaml.safe_load(f) or _default_state()
    _migrate_state(raw)
    return raw


_STAT_RENAME: dict[str, str] = {
    "body": "strength",
    "mind": "wits",
    "tech": "lore",
    "social": "charisma",
}
_STAT_DEFAULTS: dict[str, int] = {
    "strength": 2,
    "dexterity": 2,
    "wits": 2,
    "lore": 2,
    "charisma": 2,
    "resolve": 2,
}


def _migrate_state(state: dict[str, Any]) -> None:
    pc = state.setdefault("pc", {})
    if pc.get("concept") and not pc.get("tagline"):
        pc["tagline"] = (pc.get("concept") or "").strip()
    if "concept" in pc:
        del pc["concept"]
    if "tagline" not in pc:
        pc["tagline"] = ""
    if "bio" not in pc:
        pc["bio"] = ""
    if "momentum" not in pc:
        pc["momentum"] = 0

    stats = pc.setdefault("stats", {})
    for old, new in _STAT_RENAME.items():
        if old in stats and new not in stats:
            stats[new] = stats.pop(old)
        elif old in stats:
            del stats[old]
    for stat, default in _STAT_DEFAULTS.items():
        if stat not in stats:
            stats[stat] = default

    state.setdefault("scene", {})
    if "tagline" not in state["scene"]:
        state["scene"]["tagline"] = ""
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})
    state.setdefault("meta", {}).setdefault("compendium_touch_order", [])
    if not comp:
        for npc in state.get("scene", {}).get("present_npcs") or []:
            if not isinstance(npc, dict):
                continue
            nid = normalize_inventory_id(str(npc.get("id", "")))
            if not nid or nid == "_":
                continue
            comp[nid] = {
                "name": npc.get("name", ""),
                "title": npc.get("title", ""),
                "bio": npc.get("bio", ""),
            }
            touch_compendium_order(state, nid)

    # Migrate string recent_events to object form
    _migrate_recent_events(state)

    # Migrate quests missing status field
    for q in state.get("quests") or []:
        if isinstance(q, dict) and "status" not in q:
            q["status"] = "active"


def _migrate_recent_events(state: dict[str, Any]) -> None:
    """Upgrade string recent_events to object form in-place."""
    events = (state.get("scene") or {}).get("recent_events") or []
    if events and isinstance(events[0], str):
        def _slugify(s: str) -> str:
            words = re.sub(r"[^a-z0-9 ]", "", s.lower()).split()[:6]
            return "_".join(words) or "event"
        seen: set[str] = set()
        migrated: list[dict[str, Any]] = []
        for e in events:
            base_id = _slugify(e)
            slug = base_id
            counter = 1
            while slug in seen:
                slug = f"{base_id}_{counter}"
                counter += 1
            seen.add(slug)
            migrated.append({"id": slug, "text": e, "turn": 0})
        state["scene"]["recent_events"] = migrated


_MOMENTUM_MIN: int = -3
_MOMENTUM_MAX: int = 3


def apply_momentum(state: dict[str, Any], band: str) -> None:
    """Update pc.momentum deterministically from a rules band.

    Clamped to [-3, +3]. Mutates state in place.
    """
    from ccya.rules import MOMENTUM_DELTA

    pc = state.setdefault("pc", {})
    current = int(pc.get("momentum", 0))
    delta = MOMENTUM_DELTA.get(band, 0)
    pc["momentum"] = max(_MOMENTUM_MIN, min(_MOMENTUM_MAX, current + delta))


def save_state(save_dir: Path, state: dict[str, Any]) -> None:
    tmp_path = save_dir / "state.yaml.tmp"
    real_path = save_dir / "state.yaml"
    with open(tmp_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
    os.replace(str(tmp_path), str(real_path))


def _default_state() -> dict[str, Any]:
    return {
        "meta": {
            "game_name": "default",
            "turn": 0,
            "setting_pack": "",
            "model": "",
            "compendium_touch_order": [],
        },
        "pc": {
            "name": "",
            "tagline": "",
            "bio": "",
            "stats": {
                "strength": 2,
                "dexterity": 2,
                "wits": 2,
                "lore": 2,
                "charisma": 2,
                "resolve": 2,
            },
            "conditions": [],
            "momentum": 0,
        },
        "location": {"id": "", "name": "", "description": ""},
        "inventory": [],
        "quests": [],
        "scene": {
            "tags": [],
            "present_npcs": [],
            "world_state": [],
            "recent_events": [],
            "tagline": "",
            "scene_pressure": [],
            "turn_entered": 0,
        },
        "compendium": {"npcs": {}},
    }


def touch_compendium_order(state: dict[str, Any], npc_id: str) -> None:
    nid = normalize_inventory_id(npc_id)
    order: list[str] = state.setdefault("meta", {}).setdefault(
        "compendium_touch_order", []
    )
    if nid in order:
        order.remove(nid)
    order.append(nid)


def append_event(save_dir: Path, event: dict[str, Any]) -> None:
    path = save_dir / "events.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(event, default=str) + "\n")


def append_chronicle(save_dir: Path, text: str) -> None:
    path = save_dir / "chronicle.md"
    with open(path, "a") as f:
        f.write("\n" + text)


_TURN_HEADER = re.compile(r"^## Turn (\d+) — (.+)$", re.MULTILINE)


def load_chronicle_tail(
    save_dir: Path, max_tokens: int, skip_last_n_turns: int = 0
) -> str:
    path = save_dir / "chronicle.md"
    if not path.exists():
        return ""
    text = path.read_text()
    if skip_last_n_turns > 0:
        matches = list(_TURN_HEADER.finditer(text))
        if matches:
            cut_at = (
                matches[-skip_last_n_turns].start()
                if skip_last_n_turns <= len(matches)
                else 0
            )
            text = text[:cut_at]
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[-max_tokens:])


def load_recent_events(save_dir: Path, n: int) -> list[dict[str, Any]]:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    events = []
    for line in lines:
        if line.strip():
            events.append(json.loads(line))
    return events[-n:] if n > 0 else []


def load_recent_chronicle_turns(save_dir: Path, n: int) -> list[dict[str, Any]]:
    path = save_dir / "chronicle.md"
    if not path.exists():
        return []
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    if not matches:
        return []
    turns: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        turn_num = int(m.group(1))
        turn_input = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        narrative = text[body_start:body_end].strip()
        turns.append({"turn": turn_num, "input": turn_input, "narrative": narrative})
    return turns[-n:] if n > 0 else []


def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")


def normalize_inventory_id(raw: str) -> str:
    if not isinstance(raw, str):
        raw = str(raw)
    s = raw.lower().strip()
    s = re.sub(r"[\-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s or "_"


def resolve_inventory_canonical_id(
    inventory: list[dict[str, Any]], raw_id: str
) -> str | None:
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        if normalize_inventory_id(it.get("id", "")) == want:
            return str(it["id"])
        for alias in (it.get("aliases") or []):
            if isinstance(alias, str) and normalize_inventory_id(alias) == want:
                return str(it["id"])
    return None


def resolve_inventory_remove_target(
    inventory: list[dict[str, Any]], raw_id: str
) -> str | None:
    c = resolve_inventory_canonical_id(inventory, raw_id)
    if c:
        return c
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        nm = it.get("name")
        if isinstance(nm, str) and normalize_inventory_id(nm) == want:
            return str(it["id"])
    return None


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
    state: dict[str, Any], delta: StateDelta, *, recent_events_max: int = 15
) -> dict[str, Any]:
    import copy

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
            ex["name"] = u.name
        if u.notes is not None:
            ex["notes"] = u.notes

    inv.sort(key=lambda x: 0 if x.get("id") == "credits" else 1)
    state["inventory"] = inv

    if delta.location_change:
        state["location"] = {
            "id": delta.location_change.id,
            "name": delta.location_change.name,
            "description": delta.location_change.description,
        }
        state.setdefault("scene", {})["present_npcs"] = []
        state.setdefault("scene", {})["recently_left"] = []
        state.setdefault("scene", {})["recently_left_turns"] = 0
        state.setdefault("scene", {})["turn_entered"] = state.get("meta", {}).get("turn", 0)
    elif delta.location_description:
        state.setdefault("location", {})["description"] = delta.location_description

    existing_quests: dict[str, dict[str, Any]] = {
        q["id"]: q for q in state.get("quests", [])
    }

    def _apply_quest_status_side_effects(q: dict[str, Any]) -> None:
        st = q.get("status") or "active"
        if st == "completed":
            for o in q.get("objectives", []):
                o["done"] = True
                o["failed"] = False
        elif st == "failed":
            for o in q.get("objectives", []):
                if not o.get("done"):
                    o["failed"] = True

    def _auto_complete_quest(q: dict[str, Any]) -> None:
        if q.get("status") != "active":
            return
        objs = q.get("objectives", [])
        if objs and all(o.get("done") for o in objs):
            q["status"] = "completed"
            _apply_quest_status_side_effects(q)

    def _normalize_obj_desc(text: Any) -> str:
        if not isinstance(text, str):
            text = str(text or "")
        s = " ".join(text.lower().split())
        return s.rstrip(".!?")

    for qu in delta.quest_updates:
        if qu.id in existing_quests:
            q = existing_quests[qu.id]
            if qu.title:
                q["title"] = qu.title
            if qu.status:
                q["status"] = qu.status
            if qu.objectives:
                objs = q.setdefault("objectives", [])
                for obj in qu.objectives:
                    matched = False
                    if obj.index is not None:
                        idx = int(obj.index) - 1
                        if 0 <= idx < len(objs):
                            o = objs[idx]
                            if obj.done is not None:
                                o["done"] = obj.done
                            if obj.failed is not None:
                                o["failed"] = bool(obj.failed)
                            matched = True
                    if not matched:
                        want = (
                            _normalize_obj_desc(obj.description)
                            if obj.description is not None
                            else ""
                        )
                        for o in objs:
                            if (
                                want
                                and _normalize_obj_desc(o.get("description")) == want
                            ):
                                if obj.done is not None:
                                    o["done"] = obj.done
                                if obj.failed is not None:
                                    o["failed"] = bool(obj.failed)
                                matched = True
                                break
                    if not matched and obj.description:
                        objs.append(
                            {
                                "description": obj.description,
                                "done": obj.done if obj.done is not None else False,
                                "failed": bool(obj.failed)
                                if obj.failed is not None
                                else False,
                            },
                        )
            _apply_quest_status_side_effects(q)
        else:
            new_q: dict[str, Any] = {
                "id": qu.id,
                "title": qu.title,
                "status": qu.status or "active",
                "objectives": [
                    {
                        "description": o.description or "",
                        "done": o.done if o.done is not None else False,
                        "failed": bool(o.failed) if o.failed is not None else False,
                    }
                    for o in qu.objectives
                    if o.description
                ],
            }
            state.setdefault("quests", []).append(new_q)
            existing_quests[qu.id] = new_q
            _apply_quest_status_side_effects(new_q)

    for q in existing_quests.values():
        _auto_complete_quest(q)

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
    current_turn = (state.get("meta") or {}).get("turn", 0)
    for ca in delta.pc_condition_add:
        cid = ca.id
        if not cid or cid in existing_ids:
            continue
        existing_conds.append({
            "id": cid,
            "label": ca.label,
            "description": ca.description,
            "added_turn": current_turn,
        })
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
                existing_events[i]["text"] = upd.text
                break

    # Add — reject if ID already exists
    existing_ids = {e.get("id") for e in existing_events}
    for evt in delta.recent_events_add:
        if evt.id not in existing_ids:
            existing_events.append({
                "id": evt.id,
                "text": evt.text,
                "turn": evt.turn or current_turn,
            })
            existing_ids.add(evt.id)

    # Evict oldest by turn (sort ascending, drop oldest)
    existing_events.sort(key=lambda e: e.get("turn", 0))
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
                    pressures[i]["text"] = upd.text
                if upd.urgency:
                    pressures[i]["urgency"] = upd.urgency
                break

    # Add — reject if ID already exists
    for press in delta.scene_pressure_add:
        if press.id not in pressure_ids:
            pressures.append({
                "id": press.id,
                "text": press.text,
                "urgency": press.urgency or "background",
                "turn_added": press.turn_added or current_turn,
                "max_turns": press.max_turns,
            })
            pressure_ids.add(press.id)

    scene["scene_pressure"] = pressures

    if delta.scene_tags:
        state["scene"]["tags"] = delta.scene_tags

    if delta.scene_tagline is not None:
        state.setdefault("scene", {})["tagline"] = delta.scene_tagline

    # --- NPC scene management ---
    # Delta-based (npc_add/npc_remove/npc_update) takes priority over
    # legacy present_npcs full-replacement.
    NPC_SCENE_CAP = 6
    old_present: list[dict[str, Any]] = list(state.get("scene", {}).get("present_npcs") or [])
    old_present_ids: set[str] = {str(n.get("id", "")) for n in old_present if n.get("id")}
    scene = state.setdefault("scene", {})
    comp = state.setdefault("compendium", {}).setdefault("npcs", {})
    # Track new present IDs separately (like original code) so empty present_npcs
    # correctly computes recently_left as all old NPCs having left.
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

    def _apply_npc_to_present(npc: dict[str, Any], present: list[dict[str, Any]], comp: dict[str, Any], alias_map: dict[str, str]) -> str:
        """Add/update an NPC in present list. Returns resolved ID."""
        nid = npc["id"]
        resolved = _resolve_npc_id(nid, comp, alias_map)
        # Check if already present
        for i, p in enumerate(present):
            if p.get("id") == resolved:
                # Update existing
                if npc.get("notes") is not None:
                    present[i]["notes"] = npc["notes"]
                if npc.get("name") is not None and str(npc["name"]).strip():
                    present[i]["name"] = str(npc["name"]).strip()
                if npc.get("title") is not None and str(npc["title"]).strip():
                    present[i]["title"] = str(npc["title"]).strip()
                if npc.get("bio") is not None and str(npc["bio"]).strip():
                    present[i]["bio"] = str(npc["bio"]).strip()
                return resolved
        # Add new
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

    if delta.npc_add or delta.npc_remove or delta.npc_update:
        # --- Delta-based NPC merge ---
        alias_map = build_npc_alias_map(comp)
        present = list(old_present)

        # Process removes first
        removed_ids: set[str] = set()
        for rem in delta.npc_remove:
            rid = _resolve_npc_id(rem.id, comp, alias_map)
            present = [p for p in present if p.get("id") != rid]
            removed_ids.add(rid)

        # Process updates
        for upd in delta.npc_update:
            _apply_npc_to_present(
                {"id": upd.id, "notes": upd.notes or "", "name": upd.name, "title": upd.title, "bio": upd.bio},
                present, comp, alias_map,
            )

        # Process adds
        for add in delta.npc_add:
            _apply_npc_to_present(
                {"id": add.id, "notes": add.notes or "", "name": add.name, "title": add.title, "bio": add.bio},
                present, comp, alias_map,
            )
            # Update compendium with new durable info
            entry = comp.setdefault(add.id, {})
            if add.name is not None and str(add.name).strip():
                entry["name"] = str(add.name).strip()
            elif "name" not in entry:
                entry["name"] = _hydrate_npc_text(add.name, entry.get("name"))
            if add.title is not None and str(add.title).strip():
                entry["title"] = str(add.title).strip()
            elif "title" not in entry:
                entry["title"] = _hydrate_npc_text(add.title, entry.get("title"))
            if add.bio is not None and str(add.bio).strip():
                entry["bio"] = str(add.bio).strip()
            elif "bio" not in entry:
                entry["bio"] = _hydrate_npc_text(add.bio, entry.get("bio"))
            touch_compendium_order(state, add.id)

        # Enforce 6-NPC cap: evict least relevant named NPCs
        named_npcs = [p for p in present if p.get("id") != "ambient_crowd"]
        ambient_npcs = [p for p in present if p.get("id") == "ambient_crowd"]
        if len(named_npcs) > NPC_SCENE_CAP:
            # Evict from the end (oldest/least relevant)
            evicted = named_npcs[NPC_SCENE_CAP:]
            named_npcs = named_npcs[:NPC_SCENE_CAP]
            present = named_npcs + ambient_npcs
            for evicted_npc in evicted:
                removed_ids.add(evicted_npc["id"])

        scene["present_npcs"] = present
        new_present_ids = {str(p.get("id", "")) for p in present if p.get("id")}

    elif delta.present_npcs:
        # --- Legacy full-replacement (backward compat, non-empty) ---
        alias_map = build_npc_alias_map(comp)

        rows: list[dict[str, Any]] = []
        for n in delta.present_npcs:
            nid = normalize_inventory_id(n.id)

            # Alias map lookup: if incoming name/id matches existing NPC alias, route to canonical
            resolved_id = nid
            if nid in alias_map and alias_map[nid] != nid:
                resolved_id = alias_map[nid]
            if n.name:
                name_alias = n.name.lower().strip()
                if name_alias in alias_map:
                    resolved_id = alias_map[name_alias]

            ce_raw = comp.get(resolved_id)
            ce = ce_raw if isinstance(ce_raw, dict) else {}
            name = _hydrate_npc_text(n.name, ce.get("name"))
            title = _hydrate_npc_text(n.title, ce.get("title"))
            bio = _hydrate_npc_text(n.bio, ce.get("bio"))
            notes = n.notes or ""
            row = {
                "id": resolved_id,
                "name": name,
                "title": title,
                "notes": notes,
                "bio": bio,
            }
            rows.append(row)
            entry = comp.setdefault(resolved_id, {})
            if n.name is not None and str(n.name).strip():
                entry["name"] = str(n.name).strip()
            elif "name" not in entry:
                entry["name"] = row["name"]
            if n.title is not None and str(n.title).strip():
                entry["title"] = str(n.title).strip()
            elif "title" not in entry:
                entry["title"] = row["title"]
            if n.bio:
                entry["bio"] = n.bio
            elif "bio" not in entry:
                entry["bio"] = row["bio"]
            touch_compendium_order(state, resolved_id)
        scene["present_npcs"] = rows
        new_present_ids = {r["id"] for r in rows}

    # Compute recently_left: NPCs in old present_npcs but not in new.
    # Always runs after both delta and legacy paths.
    # new_present_ids is tracked separately so empty present_npcs correctly
    # computes recently_left as all old NPCs having left.
    left_ids = old_present_ids - new_present_ids
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

        entry = comp.setdefault(resolved_id, {})
        if u.name is not None:
            entry["name"] = u.name
        if u.title is not None:
            entry["title"] = u.title
        if u.bio is not None:
            entry["bio"] = u.bio
        if u.aliases:
            existing_aliases = set(entry.get("aliases") or [])
            for a in u.aliases:
                if a.lower() not in {x.lower() for x in existing_aliases}:
                    existing_aliases.add(a.lower())
            entry["aliases"] = list(existing_aliases)
        touch_compendium_order(state, resolved_id)

    return state


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


PC_CONDITIONS_MAX: int = 5
"""Hard cap on simultaneous pc.conditions; oldest is evicted FIFO when exceeded."""


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


def _fuzzy_match_inventory(name: str, inventory: list[dict[str, Any]]) -> str | None:
    """Returns canonical ID if `name` is a likely duplicate of an existing item.

    Uses token overlap — no external dependencies. Threshold 0.6.
    If all incoming tokens are contained in the candidate, uses containment score.
    """
    name_tokens = set(name.lower().split())
    if not name_tokens:
        return None
    best_id, best_score = None, 0.0
    for item in inventory:
        if not isinstance(item, dict):
            continue
        candidate_tokens: set[str] = set()
        item_name = item.get("name", "")
        if isinstance(item_name, str):
            candidate_tokens |= set(item_name.lower().split())
        for alias in (item.get("aliases") or []):
            if isinstance(alias, str):
                candidate_tokens |= set(alias.lower().split())
        if not candidate_tokens:
            continue
        overlap = len(name_tokens & candidate_tokens)
        if name_tokens.issubset(candidate_tokens):
            # Full containment: incoming is a subset of existing (e.g. "dagger" in "worn dagger")
            score = overlap / len(name_tokens)
        else:
            score = overlap / max(len(name_tokens), len(candidate_tokens))
        if score > best_score:
            best_score = score
            best_id = item["id"]
    return best_id if best_score >= 0.6 else None
