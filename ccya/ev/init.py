"""ev.py init command — create a new session: save dir + ev.yaml."""

from __future__ import annotations

import sys

from pathlib import Path
from typing import Any


def cmd_init(flags: dict[str, str], args: list[str]) -> None:
    """Create a new session: save dir + ev.yaml."""
    if "help" in flags:
        print("Usage: ev.py init [--pack PACK] [--model MODEL] [--temp N] [--save-dir DIR]")
        print()
        print("Create a new session directory with ev.yaml config.")
        print()
        print("Flags:")
        print("  --pack NAME           Start with a pack (generates state.yaml)")
        print("  --model NAME          Default LLM model")
        print("  --temp N              Default temperature")
        print("  --save-dir DIR        Custom save directory path")
        print("  --help                Show this help")
        sys.exit(0)

    import yaml

    pack = flags.get("pack")
    model = flags.get("model")
    temp = flags.get("temp")
    save_dir_str = flags.get("save-dir")

    # Determine save directory
    if save_dir_str:
        save_dir = Path(save_dir_str)
        save_dir.mkdir(parents=True, exist_ok=True)
    else:
        from ccya.ev.play import _create_play_session
        save_dir = _create_play_session(pack=pack)

    # If --pack given, initialize state
    if pack:
        from ccya.ev.play import _build_play_config, _ensure_seed_generated

        config = _build_play_config(flags)
        _ensure_seed_generated(save_dir, pack, config)

    # Write ev.yaml
    ev_config: dict[str, Any] = {}
    if pack:
        ev_config["pack"] = pack
    if model:
        ev_config["model"] = model
    if temp:
        ev_config["temp"] = float(temp)

    if ev_config:
        ev_yaml_path = save_dir / "ev.yaml"
        with open(ev_yaml_path, "w") as f:
            yaml.dump(ev_config, f, default_flow_style=False)
        print(f"Session created: {save_dir}")
        print(f"Config: {ev_yaml_path}")
    else:
        print(f"Session created: {save_dir}")
        print("No config flags provided — run 'ev.py status' to see session details.")
