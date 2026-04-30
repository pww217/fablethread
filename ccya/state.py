"""State I/O: load/save YAML state, append events.jsonl, chronicle.md."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from ccya.models import StateDelta


def load_state(save_dir: Path) -> dict[str, Any]:
    """Load the current game state from YAML."""
    path = save_dir / "state.yaml"
    if not path.exists():
        return _default_state()
    with open(path) as f:
        return yaml.safe_load(f) or _default_state()


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
        },
        "pc": {"name": "", "concept": "", "stats": {}, "conditions": []},
        "location": {"id": "", "name": "", "description": ""},
        "inventory": [],
        "quests": [],
        "scene": {"tags": [], "present_npcs": [], "established_facts": []},
    }


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


def resolve_inventory_canonical_id(inventory: list[dict[str, Any]], raw_id: str) -> str | None:
    """Return the stored id for an item whose normalized id matches raw_id."""
    want = normalize_inventory_id(raw_id)
    for it in inventory:
        if normalize_inventory_id(it.get("id", "")) == want:
            return str(it["id"])
    return None


def apply_delta(state: dict[str, Any], delta: StateDelta, *, established_facts_max: int = 10) -> dict[str, Any]:
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
        canonical = resolve_inventory_canonical_id(inv, rem.id)
        if not canonical:
            continue
        ex = by_id[canonical]
        if rem.amount is None:
            inv = [x for x in inv if x.get("id") != canonical]
        else:
            cur = int(ex.get("amount", 1))
            new_amt = max(0, cur - int(rem.amount))
            if new_amt <= 0:
                inv = [x for x in inv if x.get("id") != canonical]
            else:
                ex["amount"] = new_amt
        by_id = _by_id()

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
    elif delta.location_description:
        state.setdefault("location", {})["description"] = delta.location_description

    # Quests — upsert + objective merge + status side-effects (completed / failed)
    existing_quests: dict[str, dict[str, Any]] = {q["id"]: q for q in state.get("quests", [])}

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
                        want = _normalize_obj_desc(obj.description) if obj.description is not None else ""
                        for o in objs:
                            if want and _normalize_obj_desc(o.get("description")) == want:
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
                                "failed": bool(obj.failed) if obj.failed is not None else False,
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

    # PC conditions — add then remove (strings)
    state.setdefault("pc", {}).setdefault("conditions", [])
    for c in delta.pc_condition_add:
        if c not in state["pc"]["conditions"]:
            state["pc"]["conditions"].append(c)
    state["pc"]["conditions"] = [
        c for c in state["pc"]["conditions"] if c not in delta.pc_condition_remove
    ]

    # Established facts — remove → update → add (preserves position on update)
    existing_facts: list[str] = list(state.get("scene", {}).get("established_facts") or [])
    remove_keys = {_normalize_fact(s) for s in delta.established_facts_remove}
    existing_facts = [f for f in existing_facts if _normalize_fact(f) not in remove_keys]
    for upd in delta.established_facts_update:
        nk = _normalize_fact(upd.old)
        matched = False
        for i, f in enumerate(existing_facts):
            if _normalize_fact(f) == nk:
                existing_facts[i] = upd.new
                matched = True
                break
        if not matched and upd.new and not _fact_already_exists(upd.new, existing_facts):
            existing_facts.append(upd.new)
    for fact in delta.established_facts_add:
        if not _fact_already_exists(fact, existing_facts):
            existing_facts.append(fact)
    state.setdefault("scene", {})["established_facts"] = existing_facts[-established_facts_max:]

    # Scene tags — replace each turn if provided
    if delta.scene_tags:
        state["scene"]["tags"] = delta.scene_tags

    # Present NPCs — replace when non-empty (avoid wiping on [])
    if delta.present_npcs:
        state["scene"]["present_npcs"] = [
            {"id": n.id, "name": n.name, "title": n.title, "notes": n.notes}
            for n in delta.present_npcs
        ]

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
