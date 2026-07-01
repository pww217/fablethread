"""State I/O: load/save YAML state, init save directories."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, cast

import yaml
from enum import Enum

from ccya.errors import ErrorKind
from ccya.models import WorldState

_log = logging.getLogger(__name__)


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
        "meta": {
            "turn": 0,
            "setting_pack": "",
            "model": "",
            "session_name": "",
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
            "situation": {},
        },
        "location": {"id": "", "name": "", "description": ""},
        "inventory": [],
        "long_term_objective": {
            "long_term_objective": "",
            "threads": [],
            "completed_threads": [],
            "resolution": None,
            "last_thread_created_turn": 0,
        },
        "resolved_arcs": [],
        "scene": {
            "tags": [],
            "world_state": [],
            "turn_entered": 0,
        },
        "compendium": {"npcs": {}},
        "world_state_candidates": [],
        "world": {
            "factions": [],
            "locations": [],
        },
    }


def load_state(save_dir: Path) -> WorldState:
    path = save_dir / "state.yaml"
    if not path.exists():
        _log.error("load_state path=%s not found — returning default state", path,
                    extra={"error_kind": ErrorKind.STATE_LOAD_FAILED})
        return WorldState.from_dict(_default_state())
    with open(path) as f:
        content = f.read()
    try:
        raw: dict[str, Any] = cast(dict[str, Any], yaml.safe_load(content))
    except yaml.YAMLError as e:
        _log.error("load_state path=%s malformed YAML — returning default state: %s", path, e,
                    extra={"error_kind": ErrorKind.STATE_LOAD_FAILED})
        return WorldState.from_dict(_default_state())
    if not raw:
        _log.error("load_state path=%s empty — returning default state", path,
                    extra={"error_kind": ErrorKind.STATE_LOAD_FAILED})
        return WorldState.from_dict(_default_state())
    return WorldState.from_dict(raw)


def save_state(save_dir: Path, state: WorldState) -> None:
    tmp_path = save_dir / "state.yaml.tmp"
    real_path = save_dir / "state.yaml"
    raw = state.to_dict()
    raw = _coerce_enums(raw)
    with open(tmp_path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, allow_unicode=True)
    os.replace(str(tmp_path), str(real_path))

def init_save_dir(save_dir: Path, seed: WorldState) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)
    save_state(save_dir, seed)
    chronicle_path = save_dir / "chronicle.md"
    chronicle_path.write_text("")
    opening = seed.pc.situation.get("opening")
    if opening:
        chronicle_path.write_text(f"\n## Turn 0 — Seed\n\n{opening.strip()}")
    else:
        chronicle_path.write_text("")
    (save_dir / "events.jsonl").write_text("")
    # Remove stale snapshot from a previous game

