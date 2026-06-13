"""State I/O: load/save YAML state, init save directories."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, cast

import yaml
from enum import Enum

_log = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1


def _assign_seed_personalities(state: dict[str, Any]) -> None:
    """Assign personality archetype ids to any NPCs missing one in the seed state."""
    from ccya.personality import ARCHETYPES, assign_personality
    
    npcs = (state.get("compendium") or {}).get("npcs", {})
    for npc_id, entry in npcs.items():
        if not isinstance(entry, dict):
            continue
        if entry.get("personality") and entry["personality"] in ARCHETYPES:
            continue
        arch = assign_personality(
            motivation=entry.get("motivation"),
            fear=entry.get("fear"),
            npc_id=npc_id,
        )
        entry["personality"] = arch.id


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
                "charisma": 2,
            },
            "conditions": [],
            "allegiance": None,
        },
        "location": {"id": "", "name": "", "description": ""},
        "inventory": [],
        "arc": {
            "visible_goal": "",
            "goal_context": "",
            "threads": [],
            "completed_threads": [],
            "resolution": None,
            "last_thread_created_turn": 0,
        },
        "resolved_arcs": [],
        "scene": {
            "tags": [],
            "world_state": [],
            "tagline": "",
            "turn_entered": 0,
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
        _log.debug("load_state path=%s not found — returning default state", path)
        return _default_state()
    with open(path) as f:
        content = f.read()
    try:
        raw: dict[str, Any] = cast(dict[str, Any], yaml.safe_load(content))
    except yaml.YAMLError as e:
        _log.warning("load_state path=%s malformed YAML — returning default state: %s", path, e)
        return _default_state()
    if not raw:
        _log.debug("load_state path=%s empty — returning default state", path)
        return _default_state()
    loaded_version = raw.get("schema_version", 0)
    if loaded_version == 0:
        raw = _migrate_v0_to_v1(content, raw)
    if loaded_version > CURRENT_SCHEMA_VERSION:
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

def init_save_dir(save_dir: Path, seed: dict[str, Any]) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    _assign_seed_personalities(seed)
    save_state(save_dir, seed)
    chronicle_path = save_dir / "chronicle.md"
    seed_meta = seed.get("__seed_meta__") or {}
    opening = seed_meta.get("opening_narrative")
    if opening:
        chronicle_path.write_text(f"\n## Turn 0 — Seed\n\n{opening.strip()}")
    else:
        chronicle_path.write_text("")
    (save_dir / "events.jsonl").write_text("")
    # Remove stale snapshot from a previous game
    (save_dir / "state_snapshot.yaml").unlink(missing_ok=True)
