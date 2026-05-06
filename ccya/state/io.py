"""State I/O: load/save YAML state, init save directories, migration."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml

_log = logging.getLogger("ccya.state")

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
            "world_state": [],
            "recent_events": [],
            "tagline": "",
            "scene_pressure": [],
            "turn_entered": 0,
        },
        "compendium": {"npcs": {}},
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
    state.setdefault("meta", {}).setdefault("compendium_touch_order", [])

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


def load_state(save_dir: Path) -> dict[str, Any]:
    path = save_dir / "state.yaml"
    if not path.exists():
        return _default_state()
    with open(path) as f:
        raw = yaml.safe_load(f) or _default_state()
    _migrate_state(raw)
    return raw


def save_state(save_dir: Path, state: dict[str, Any]) -> None:
    tmp_path = save_dir / "state.yaml.tmp"
    real_path = save_dir / "state.yaml"
    with open(tmp_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
    os.replace(str(tmp_path), str(real_path))


def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")
