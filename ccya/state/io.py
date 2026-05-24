"""State I/O: load/save YAML state, init save directories."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import yaml
from enum import Enum

_log = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1


def _migrate_v0_to_v1(content: str, raw: dict[str, Any]) -> dict[str, Any]:
    """Migrate a legacy (v0) state to v1.

    Applies the existing regex fix for corrupted ThreadState YAML tags.
    """
    content = re.sub(
        r"(state:\s*)!!python/object/apply:ccya\.models\.ThreadState\n(\s+)-\s+(\w+)",
        r"\1\3",
        content,
    )
    raw = yaml.safe_load(content) or _default_state()
    raw["schema_version"] = CURRENT_SCHEMA_VERSION
    return raw


def _coerce_enums(obj: Any) -> Any:
    """Recursively convert Enum values to their string values for YAML serialization."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _coerce_enums(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_coerce_enums(v) for v in obj]
    return obj


def _default_state() -> dict[str, Any]:
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
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
        "arc": {
            "visible_goal": "",
            "thematic_question": "",
            "hidden_truths": [],
            "discovered_truths": [],
            "threads": [],
            "completed_threads": [],
        },
        "scene": {
            "tags": [],
            "world_state": [],
            "recent_events": [],
            "tagline": "",
            "turn_entered": 0,
            "present_npcs": [],
        },
        "compendium": {"npcs": {}},
        "world": {
            "factions": [],
            "locations": [],
        },
    }


def load_state(save_dir: Path) -> dict[str, Any]:
    path = save_dir / "state.yaml"
    if not path.exists():
        return _default_state()
    with open(path) as f:
        content = f.read()
    raw = yaml.safe_load(content) or _default_state()
    loaded_version = raw.get("schema_version", 0)
    if loaded_version == 0:
        raw = _migrate_v0_to_v1(content, raw)
    elif loaded_version > CURRENT_SCHEMA_VERSION:
        _log.warning(
            "state schema version %d is newer than engine version %d — loading anyway",
            loaded_version, CURRENT_SCHEMA_VERSION,
        )
    return raw


def save_state(save_dir: Path, state: dict[str, Any]) -> None:
    tmp_path = save_dir / "state.yaml.tmp"
    real_path = save_dir / "state.yaml"
    state = _coerce_enums(state)
    with open(tmp_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, allow_unicode=True)
    os.replace(str(tmp_path), str(real_path))


def _convert_seed_recent_events(seed: dict[str, Any]) -> None:
    """Convert string-format recent_events to proper dicts with id field."""
    scene = seed.get("scene", {}) or {}
    events = scene.get("recent_events") or []
    if not events:
        return
    converted = []
    for i, evt in enumerate(events):
        if isinstance(evt, str):
            import uuid as _uuid
            converted.append({"id": f"seed_evt_{_uuid.uuid4().hex[:8]}", "text": evt})
        elif isinstance(evt, dict) and "id" not in evt:
            import uuid as _uuid
            converted.append({**evt, "id": f"seed_evt_{_uuid.uuid4().hex[:8]}"})
        else:
            converted.append(evt)
    scene["recent_events"] = converted


def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    _convert_seed_recent_events(seed)
    save_state(save_dir, seed)
    (save_dir / "chronicle.md").write_text("")
    (save_dir / "events.jsonl").write_text("")
