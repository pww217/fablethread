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
    """Load the current game state from YAML."""
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
    """One-time field renames and defaults for older saves."""
    pc = state.setdefault("pc", {})
    if pc.get("concept") and not pc.get("tagline"):
        pc["tagline"] = (pc.get("concept") or "").strip()
    if "concept" in pc:
        del pc["concept"]
    if "tagline" not in pc:
        pc["tagline"] = ""
    if "bio" not in pc:
        pc["bio"] = ""

    # Migrate old 4-stat names to the unified 6-stat set.
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
    # Seed compendium from present_npcs when empty (first load of older saves / fresh seed)
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


def save_state(save_dir: Path, state: dict[str, Any]) -> None:
    """Atomically save game state to YAML (write tmp then rename)."""
    tmp_path = save_dir / "state.yaml.tmp"
    real_path = save_dir / "state.yaml"
    with open(tmp_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
    os.replace(str(tmp_path), str(real_path))


def _default_state() -> dict[str, Any]:
    """Return a minimal default state structure."""
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
        },
        "compendium": {"npcs": {}},
    }


def touch_compendium_order(state: dict[str, Any], npc_id: str) -> None:
    """Move npc_id to end of LRU touch list (most recent)."""
    nid = normalize_inventory_id(npc_id)
    order: list[str] = state.setdefault("meta", {}).setdefault(
        "compendium_touch_order", []
    )
    if nid in order:
        order.remove(nid)
    order.append(nid)


def append_event(save_dir: Path, event: dict[str, Any]) -> None:
    """Append a turn event to events.jsonl (source of truth)."""
    path = save_dir / "events.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(event, default=str) + "\n")


def append_chronicle(save_dir: Path, text: str) -> None:
    """Append text to the chronicle file."""
    path = save_dir / "chronicle.md"
    with open(path, "a") as f:
        f.write("\n" + text)


def load_chronicle_tail(save_dir: Path, max_tokens: int) -> str:
    """Load the tail of chronicle.md, clipped to max_tokens words."""
    path = save_dir / "chronicle.md"
    if not path.exists():
        return ""
    text = path.read_text()
    words = text.split()
    if len(words) <= max_tokens:
        return text
    return " ".join(words[-max_tokens:])


def load_recent_events(save_dir: Path, n: int) -> list[dict[str, Any]]:
    """Load the last N events from events.jsonl."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = path.read_text().strip().split("\n")
    events = []
    for line in lines:
        if line.strip():
            events.append(json.loads(line))
    return events[-n:] if n > 0 else []


_TURN_HEADER = re.compile(r"^## Turn (\d+) — (.+)$", re.MULTILINE)


def load_recent_chronicle_turns(save_dir: Path, n: int) -> list[dict[str, Any]]:
    """Parse chronicle.md into the last n turn blocks for narrate recent-turns context.

    Each block is shaped like append_chronicle: ``## Turn N — input`` then blank line then narrative.
    Full narrative text is included (not truncated).
    """
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
    """Initialize (or reset) a save directory from seed state YAML."""
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    # Truncate both files so a New Game starts with a clean log and chronicle
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")


def normalize_inventory_id(raw: str) -> str:
    """Normalize inventory item ids for merge/remove lookup."""
    if not isinstance(raw, str):
        raw = str(raw)
    s = raw.lower().strip()
    s = re.sub(r"[\-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    return s or "_"


def resolve_inventory_canonical_id(
    inventory: list[dict[str, Any]], raw_id: str
) -> str | None:
    """Return the stored id for an item whose normalized id matches raw_id."""
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        if normalize_inventory_id(it.get("id", "")) == want:
            return str(it["id"])
    return None


def resolve_inventory_remove_target(
    inventory: list[dict[str, Any]], raw_id: str
) -> str | None:
    """Resolve id or normalized item name to stored inventory id for remove operations."""
    c = resolve_inventory_canonical_id(inventory, raw_id)
    if c:
        return c
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        nm = it.get("name")
        if isinstance(nm, str) and normalize_inventory_id(nm) == want:
            return str(it["id"])
    return None


def apply_delta(
    state: dict[str, Any], delta: StateDelta, *, recent_events_max: int = 15
) -> dict[str, Any]:
    """Apply a validated StateDelta to the state dict. Returns the updated state."""
    import copy

    state = copy.deepcopy(state)

    # Inventory — merge by normalized id on add; partial or full remove; pin credits to top
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
                # amount: 0 or negative — treat as full stack remove (LLM mistake)
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

    # Location — clear NPCs when moving to a new place
    if delta.location_change:
        state["location"] = {
            "id": delta.location_change.id,
            "name": delta.location_change.name,
            "description": delta.location_change.description,
        }
        state.setdefault("scene", {})["present_npcs"] = []
        state.setdefault("scene", {})["recently_left"] = []
        state.setdefault("scene", {})["recently_left_turns"] = 0
    elif delta.location_description:
        state.setdefault("location", {})["description"] = delta.location_description

    # Quests — upsert + objective merge + status side-effects (completed / failed)
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
        """Auto-complete an active quest when all its objectives are done."""
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

    # Auto-complete active quests whose objectives are all done
    for q in existing_quests.values():
        _auto_complete_quest(q)

    # PC conditions — structured (id-based dedup), add then remove, FIFO cap
    state.setdefault("pc", {}).setdefault("conditions", [])
    existing_conds: list[dict] = []
    for c in state["pc"]["conditions"]:
        if isinstance(c, dict):
            existing_conds.append(c)
        elif isinstance(c, str):
            # Migrate legacy string conditions on first touch
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

    # Recent events — remove → update → add (preserves position on update; FIFO cap)
    existing_events: list[str] = list(state.get("scene", {}).get("recent_events") or [])
    remove_keys = {_normalize_fact(s) for s in delta.recent_events_remove}
    existing_events = [
        f for f in existing_events if _normalize_fact(f) not in remove_keys
    ]
    for upd in delta.recent_events_update:
        nk = _normalize_fact(upd.old)
        matched = False
        for i, f in enumerate(existing_events):
            if _normalize_fact(f) == nk:
                existing_events[i] = upd.new
                matched = True
                break
        if (
            not matched
            and upd.new
            and not _fact_already_exists(upd.new, existing_events)
        ):
            existing_events.append(upd.new)
    for fact in delta.recent_events_add:
        if not _fact_already_exists(fact, existing_events):
            existing_events.append(fact)
    state.setdefault("scene", {})["recent_events"] = existing_events[
        -recent_events_max:
    ]

    # Scene tags — replace each turn if provided
    if delta.scene_tags:
        state["scene"]["tags"] = delta.scene_tags

    if delta.scene_tagline is not None:
        state.setdefault("scene", {})["tagline"] = delta.scene_tagline

    # Present NPCs — replace when non-empty (avoid wiping on []);
    # hydrate name/title/bio from compendium when delta omits them (token-saving path).
    # Capture old ids before applying so we can compute recently_left.
    old_present_ids: set[str] = {
        n.get("id") for n in state.get("scene", {}).get("present_npcs", [])
    }
    if delta.present_npcs:
        comp = state.setdefault("compendium", {}).setdefault("npcs", {})

        def _hydrate_npc_text(delta_val: str | None, stored: Any) -> str:
            st = str(stored).strip() if stored is not None else ""
            if delta_val is None:
                return st
            dv = str(delta_val).strip()
            if not dv:
                return st
            return dv

        rows: list[dict[str, Any]] = []
        for n in delta.present_npcs:
            nid = normalize_inventory_id(n.id)
            ce_raw = comp.get(nid)
            ce = ce_raw if isinstance(ce_raw, dict) else {}
            name = _hydrate_npc_text(n.name, ce.get("name"))
            title = _hydrate_npc_text(n.title, ce.get("title"))
            bio = _hydrate_npc_text(n.bio, ce.get("bio"))
            notes = n.notes or ""
            row = {
                "id": n.id,
                "name": name,
                "title": title,
                "notes": notes,
                "bio": bio,
            }
            rows.append(row)
            entry = comp.setdefault(nid, {})
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
            touch_compendium_order(state, nid)
        state.setdefault("scene", {})["present_npcs"] = rows

    # Compute recently_left: NPCs in old present_npcs but not in new.
    # Returnees (in both old and new) are excluded automatically.
    # Use delta.present_npcs for new ids (not state, which may not have been updated).
    new_present_ids: set[str] = {
        n.id for n in (delta.present_npcs or [])
    }
    left_ids = old_present_ids - new_present_ids
    scene = state.setdefault("scene", {})
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

    for u in delta.compendium_npc_update:
        nid = normalize_inventory_id(u.id)
        comp = state.setdefault("compendium", {}).setdefault("npcs", {})
        entry = comp.setdefault(nid, {})
        if u.name is not None:
            entry["name"] = u.name
        if u.title is not None:
            entry["title"] = u.title
        if u.bio is not None:
            entry["bio"] = u.bio
        touch_compendium_order(state, nid)

    return state


def _item_to_dict(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        out = dict(item)
        if out.get("amount") is None or int(out.get("amount", 0) or 0) < 1:
            out["amount"] = 1
        return out
    amt = getattr(item, "amount", 1)
    return {
        "id": item.id,
        "name": item.name,
        "notes": item.notes,
        "amount": max(1, int(amt or 1)),
    }


PC_CONDITIONS_MAX: int = 5
"""Hard cap on simultaneous pc.conditions; oldest is evicted FIFO when exceeded."""


def _normalize_fact(text: Any) -> str:
    """Normalize a fact string for dedup / removal matching."""
    if not isinstance(text, str):
        text = str(text)
    return " ".join(text.lower().split())


def _fact_already_exists(fact: str, existing: list[str]) -> bool:
    """Check if fact already exists (normalized exact match)."""
    nk = _normalize_fact(fact)
    for ef in existing:
        if nk == _normalize_fact(ef):
            return True
    return False
