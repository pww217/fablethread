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
    """Initialize a save directory from seed state YAML."""
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    # Create empty chronicle and events
    (save_dir / "chronicle.md").touch()
    (save_dir / "events.jsonl").touch()


def apply_delta(state: dict[str, Any], delta: StateDelta, *, established_facts_max: int = 10) -> dict[str, Any]:
    """Apply a validated StateDelta to the state dict. Returns the updated state."""
    import copy

    state = copy.deepcopy(state)

    # Inventory
    for item in delta.inventory_add:
        state["inventory"].append(_item_to_dict(item))

    for rid in delta.inventory_remove:
        state["inventory"] = [
            item for item in state["inventory"]
            if item.get("id") != rid
        ]

    # Location
    if delta.location_change:
        state["location"] = {
            "id": delta.location_change.id,
            "name": delta.location_change.name,
            "description": delta.location_change.description,
        }

    # Quests
    existing_quests = {q["id"]: q for q in state.get("quests", [])}
    for qu in delta.quest_updates:
        if qu.id in existing_quests:
            q = existing_quests[qu.id]
            if qu.title:
                q["title"] = qu.title
            if qu.status:
                q["status"] = qu.status
            if qu.objectives:
                for obj in qu.objectives:
                    if obj.description in [o.get("description", "") for o in q.get("objectives", [])]:
                        # Update existing objective
                        for o in q["objectives"]:
                            if o.get("description") == obj.description:
                                o["done"] = obj.done
                    else:
                        q.setdefault("objectives", []).append({
                            "description": obj.description,
                            "done": obj.done,
                        })
        else:
            state.setdefault("quests", []).append({
                "id": qu.id,
                "title": qu.title,
                "status": qu.status,
                "objectives": [
                    {"description": o.description, "done": o.done}
                    for o in qu.objectives
                ],
            })

    # PC conditions
    state.setdefault("pc", {}).setdefault("conditions", [])
    for c in delta.pc_condition_add:
        if c not in state["pc"]["conditions"]:
            state["pc"]["conditions"].append(c)
    state["pc"]["conditions"] = [
        c for c in state["pc"]["conditions"] if c not in delta.pc_condition_remove
    ]

    # Established facts
    existing_facts = state.get("scene", {}).get("established_facts", [])
    for fact in delta.established_facts:
        if not _fact_already_exists(fact, existing_facts):
            existing_facts.append(fact)
    # Cap at established_facts_max
    state.setdefault("scene", {})["established_facts"] = existing_facts[-established_facts_max:]

    # Meta
    meta = state.setdefault("meta", {})
    meta["turn"] = meta.get("turn", 0) + 1

    return state


def _item_to_dict(item: Any) -> dict[str, str]:
    if isinstance(item, dict):
        return item
    return {"id": item.id, "name": item.name, "notes": item.notes}


def _fact_already_exists(fact: str, existing: list[str]) -> bool:
    """Check if fact already exists (normalized exact match)."""
    normalized = " ".join(fact.lower().split())
    for ef in existing:
        if normalized == " ".join(ef.lower().split()):
            return True
    return False
