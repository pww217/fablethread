"""State I/O: load/save YAML state, append events.jsonl, chronicle.md."""

from __future__ import annotations

import json
import os
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


def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    """Initialize (or reset) a save directory from seed state YAML."""
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    # Truncate both files so a New Game starts with a clean log and chronicle
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")


def apply_delta(state: dict[str, Any], delta: StateDelta, *, established_facts_max: int = 10) -> dict[str, Any]:
    """Apply a validated StateDelta to the state dict. Returns the updated state."""
    import copy

    state = copy.deepcopy(state)

    # Inventory — merge by id on add; partial or full remove; pin credits to top
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
        if item.id in by_id:
            ex = by_id[item.id]
            ex["amount"] = int(ex.get("amount", 1)) + amt
            if d.get("notes"):
                ex["notes"] = d["notes"]
        else:
            d["amount"] = amt
            inv.append(d)
            by_id = _by_id()

    for rem in delta.inventory_remove:
        if rem.id not in by_id:
            continue
        ex = by_id[rem.id]
        if rem.amount is None:
            inv = [x for x in inv if x.get("id") != rem.id]
        else:
            cur = int(ex.get("amount", 1))
            new_amt = max(0, cur - int(rem.amount))
            if new_amt <= 0:
                inv = [x for x in inv if x.get("id") != rem.id]
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

    for qu in delta.quest_updates:
        if qu.id in existing_quests:
            q = existing_quests[qu.id]
            if qu.title:
                q["title"] = qu.title
            if qu.status:
                q["status"] = qu.status
            if qu.objectives:
                for obj in qu.objectives:
                    matched = False
                    for o in q.get("objectives", []):
                        if o.get("description") == obj.description:
                            o["done"] = obj.done
                            o["failed"] = bool(obj.failed)
                            matched = True
                            break
                    if not matched:
                        q.setdefault("objectives", []).append({
                            "description": obj.description,
                            "done": obj.done,
                            "failed": bool(obj.failed),
                        })
            _apply_quest_status_side_effects(q)
        else:
            new_q: dict[str, Any] = {
                "id": qu.id,
                "title": qu.title,
                "status": qu.status or "active",
                "objectives": [
                    {"description": o.description, "done": o.done, "failed": bool(o.failed)}
                    for o in qu.objectives
                ],
            }
            state.setdefault("quests", []).append(new_q)
            existing_quests[qu.id] = new_q
            _apply_quest_status_side_effects(new_q)

    # PC conditions
    state.setdefault("pc", {}).setdefault("conditions", [])
    for c in delta.pc_condition_add:
        if c not in state["pc"]["conditions"]:
            state["pc"]["conditions"].append(c)
    state["pc"]["conditions"] = [
        c for c in state["pc"]["conditions"] if c not in delta.pc_condition_remove
    ]

    # Established facts — removals (normalized match) then additions
    existing_facts: list[str] = list(state.get("scene", {}).get("established_facts", []))
    remove_keys = {_normalize_fact(s) for s in delta.established_facts_remove}
    existing_facts = [f for f in existing_facts if _normalize_fact(f) not in remove_keys]
    for fact in delta.established_facts:
        if not _fact_already_exists(fact, existing_facts):
            existing_facts.append(fact)
    state.setdefault("scene", {})["established_facts"] = existing_facts[-established_facts_max:]

    # Scene tags — replace each turn if provided
    if delta.scene_tags:
        state["scene"]["tags"] = delta.scene_tags

    # Present NPCs — replace if provided (merges with location-change clear above)
    if delta.present_npcs:
        state["scene"]["present_npcs"] = [
            {"id": n.id, "name": n.name, "notes": n.notes}
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
