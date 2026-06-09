"""Panel context helpers used by route handlers."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any
from ccya.state import load_last_narration, load_state

from .metrics import _recent_turn_metrics

_log = logging.getLogger(__name__)

_app = sys.modules["ccya.server.app"]


def _load_current_state() -> dict[str, Any]:
    state = load_state(_app.SAVE_DIR)
    _log.debug("_load_current_state keys=%s", list(state.keys()))
    return state


def _load_ruling_map(save_dir: Path) -> dict[int, dict[str, Any]]:
    """Build a turn→rules map from events.jsonl."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        _log.debug("_load_ruling_map path=%s not found", path)
        return {}
    import json

    raw = path.read_text().strip()
    if not raw:
        return {}
    ruling_map: dict[int, dict[str, Any]] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            _log.warning("Skipping malformed events.jsonl line in _load_ruling_map: %s", e)
            continue
        turn = int(ev.get("turn") or 0)
        rules = ev.get("ruling")
        if rules and isinstance(rules, dict):
            ruling_map[turn] = rules
    _log.debug("_load_ruling_map entries=%d", len(ruling_map))
    return ruling_map


def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict[str, Any]]:
    """Return the last n turns from chronicle.md (excluding turn 0 seed)."""
    all_turns = load_last_narration(save_dir, n + 1)
    turns = [t for t in all_turns if t["turn"] != 0]
    ruling_map = _load_ruling_map(save_dir)
    _log.debug("_load_recent_history n=%d turns=%d ruling_entries=%d", n, len(turns), len(ruling_map))
    return [
        {
            "turn": t["turn"],
            "input": t["input"],
            "narrative": t["narrative"],
            "ruling": ruling_map.get(t["turn"]),
        }
        for t in turns[-n:]
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
        actions = ev.get("actions") or []
        _log.debug("_load_last_actions count=%d", len(actions))
        return actions
    except (json.JSONDecodeError, KeyError) as e:
        _log.warning("Failed to parse last action from events.jsonl: %s", e)
        return []


def _load_opening_from_chronicle(save_dir: Path) -> str | None:
    """Extract the opening narrative from turn 0 in chronicle.md. Returns None if not found."""
    from ccya.state.chronicle import _TURN_HEADER
    
    path = save_dir / "chronicle.md"
    if not path.exists():
        return None
    
    text = path.read_text()
    matches = list(_TURN_HEADER.finditer(text))
    for m in matches:
        if int(m.group(1)) == 0:
            narrative = text[m.end():].strip()
            return narrative if narrative else None
    return None


def _get_opening() -> str:
    return _app._dynamic_opening


def _get_opening_outcome_summary() -> str:
    return _app._dynamic_opening_outcome


def _get_opening_actions() -> list[str]:
    return _app._dynamic_opening_actions


def _debug_context() -> dict[str, Any]:
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    state = _load_current_state()
    _log.debug("_debug_context state_keys=%s mock=%s", list(state.keys()), mock_mode)
    return {
        "errors": [],        "turns": _recent_turn_metrics(_app.SAVE_DIR, 10),
        "mock_mode": mock_mode,
        "state": state,
        "log_llm_io": _app.engine_config.log_llm_io,
        "log_prompts": _app.engine_config.log_prompts,
        "log_file": "logs/game.log",
    }
