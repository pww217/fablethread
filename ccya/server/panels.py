"""Panel context helpers used by route handlers."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from ccya.state import load_recent_chronicle_turns, load_state

from .metrics import _recent_turn_metrics

_app = sys.modules["ccya.server.app"]


def _load_current_state() -> dict[str, Any]:
    return load_state(_app.SAVE_DIR)


def _load_rules_map(save_dir: Path) -> dict[int, dict[str, Any]]:
    """Build a turn→rules map from events.jsonl."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return {}
    import json

    raw = path.read_text().strip()
    if not raw:
        return {}
    rules_map: dict[int, dict[str, Any]] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        turn = int(ev.get("turn") or 0)
        rules = ev.get("rules")
        if rules and isinstance(rules, dict):
            rules_map[turn] = rules
    return rules_map


def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict[str, Any]]:
    """Return the last n turns from chronicle.md for page-reload continuity (full narrative)."""
    turns = load_recent_chronicle_turns(save_dir, n)
    rules_map = _load_rules_map(save_dir)
    return [
        {
            "turn": t["turn"],
            "input": t["input"],
            "narrative": t["narrative"],
            "rules": rules_map.get(t["turn"]),
        }
        for t in turns
    ]


def _load_last_actions(save_dir: Path) -> list[str]:
    """Return the actions list from the most recent turn event."""
    import json

    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = [ln for ln in path.read_text().strip().splitlines() if ln.strip()]
    if not lines:
        return []
    try:
        ev = json.loads(lines[-1])
        return ev.get("actions") or []
    except (json.JSONDecodeError, KeyError):
        return []


def _get_opening() -> str:
    if _app._active_pack.manifest.mode == "dynamic":
        return _app._dynamic_opening
    return _app._active_pack.opening_text


def _get_opening_actions() -> list[str]:
    if _app._active_pack.manifest.mode == "dynamic":
        return _app._dynamic_opening_actions
    return _app._active_pack.opening_actions


def _debug_context() -> dict[str, Any]:
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    return {
        "errors": list(_app._ERRORS_LOG),
        "turns": _recent_turn_metrics(_app.SAVE_DIR, 10),
        "mock_mode": mock_mode,
        "state": _load_current_state(),
        "log_llm_io": _app.engine_config.log_llm_io,
        "log_prompts": _app.engine_config.log_prompts,
        "log_file": _app.config.get("logging", {}).get("file", "logs/llm-g.log"),
    }
