"""State I/O: load/save YAML state, init save directories, migration."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
from enum import Enum

_log = logging.getLogger("ccya.state")


def _coerce_enums(obj: Any) -> Any:
    """Recursively convert Enum values to their string values for YAML serialization."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _coerce_enums(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce_enums(v) for v in obj]
    return obj

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
            "last_compacted_turn": 0,
            "prior_history": [],
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
            "allegiance": None,
        },
        "location": {"id": "", "name": "", "description": ""},
        "inventory": [],
        "arc": {},
        "scene": {
            "tags": [],
            "world_state": [],
            "recent_events": [],
            "tagline": "",
            "scene_pressure": [],
            "turn_entered": 0,
            "present_npcs": [],
        },
        "compendium": {"npcs": {}},
        "world": {
            "factions": [],
            "locations": [],
        },
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
    if "allegiance" not in pc:
        pc["allegiance"] = None

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

    # Migrate world key (Phase 5)
    if "world" not in state:
        state["world"] = {"factions": [], "locations": []}
    else:
        w = state.setdefault("world", {})
        if "factions" not in w:
            w["factions"] = []
        if "locations" not in w:
            w["locations"] = []

    # Migrate prior_history and last_compacted_turn
    meta = state.setdefault("meta", {})
    if not isinstance(meta.get("prior_history"), list):
        meta["prior_history"] = []
    if not isinstance(meta.get("last_compacted_turn"), int) or meta["last_compacted_turn"] < 0:
        meta["last_compacted_turn"] = 0

    # Fix arc thread states — active list should have ACTIVE, latent list should have LATENT
    from ccya.models import ThreadState

    arc = state.get("arc")
    if arc:
        for t in arc.get("active_threads", []):
            if isinstance(t, dict) and t.get("state") != ThreadState.ACTIVE.value:
                t["state"] = ThreadState.ACTIVE.value
        for t in arc.get("latent_threads", []):
            if isinstance(t, dict) and t.get("state") != ThreadState.LATENT.value:
                t["state"] = ThreadState.LATENT.value


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
        content = f.read()
    # Fix corrupted ThreadState tags from previous yaml.dump without _coerce_enums
    content = re.sub(
        r"(state:\s*)!!python/object/apply:ccya\.models\.ThreadState\n(\s+)-\s+(\w+)",
        r"\1\3",
        content,
    )
    raw = yaml.safe_load(content) or _default_state()
    _migrate_state(raw)
    return raw


def save_state(save_dir: Path, state: dict[str, Any]) -> None:
    tmp_path = save_dir / "state.yaml.tmp"
    real_path = save_dir / "state.yaml"
    state = _coerce_enums(state)
    with open(tmp_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
    os.replace(str(tmp_path), str(real_path))


def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")
