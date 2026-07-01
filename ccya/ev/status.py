"""ev.py status command — print session dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

from ccya.ev.play import EV_SAVES_DIR
from ccya.ev.session_config import load_session_config
from ccya.state.io import load_state


def cmd_status(flags: dict[str, str]) -> None:
    """Print session dashboard."""
    if "help" in flags:
        print("Usage: ev.py status [--save-dir DIR]")
        print()
        print("Print session dashboard: turn count, config, file paths.")
        print()
        print("Flags:")
        print("  --save-dir DIR    Specify session directory (defaults to evals/runs/latest)")
        print("  --help            Show this help")
        sys.exit(0)

    save_dir_str = flags.get("save-dir")
    if save_dir_str:
        save_dir = Path(save_dir_str)
    else:
        latest = EV_SAVES_DIR / "latest"
        if not latest.exists():
            print("Error: no session found. Run 'ev.py init' or specify --save-dir.", file=sys.stderr)
            sys.exit(1)
        save_dir = latest

    state = load_state(save_dir)
    session_config = load_session_config(save_dir)

    print(f"Session: {save_dir}")
    print(f"Turn:    {state.meta.turn}")

    if session_config:
        if session_config.get("pack"):
            print(f"Pack:    {session_config['pack']}")
        if session_config.get("model"):
            print(f"Model:   {session_config['model']}")
        if session_config.get("temp"):
            print(f"Temp:    {session_config['temp']}")
        player = session_config.get("player", {})
        if player.get("personality"):
            print(f"Personality: {player['personality']}")
    else:
        print("Config: none (using defaults)")

    print(f"Events:  {save_dir / 'events.jsonl'}")
    print(f"State:   {save_dir / 'state.yaml'}")
