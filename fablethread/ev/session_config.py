"""Session config loading from ev.yaml in save directories."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_session_config(save_dir: Path) -> dict[str, Any] | None:
    """Load ev.yaml from save_dir. Returns None if file doesn't exist."""
    ev_yaml = save_dir / "ev.yaml"
    if not ev_yaml.exists():
        return None
    import yaml
    with open(ev_yaml) as f:
        data = yaml.safe_load(f) or {}
    return data


def resolve_auto_report(flags: dict[str, str], session_config: dict[str, Any] | None) -> bool:
    """Return auto_report with resolution: CLI flag > session_config > default False."""
    if "auto-report" in flags:
        return True
    if session_config is not None and session_config.get("auto_report"):
        return True
    return False
