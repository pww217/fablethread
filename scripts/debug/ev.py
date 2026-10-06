#!/usr/bin/env python3
"""CLI entry point for ev tooling. Delegates to fablethread.ev."""

import sys

if sys.version_info < (3, 13):
    print(f"Error: ev.py requires Python 3.13+. You are using {sys.version.split()[0]}.", file=sys.stderr)
    print("Use: .venv/bin/python scripts/debug/ev.py <command>", file=sys.stderr)
    sys.exit(1)

from fablethread.ev import main

if __name__ == "__main__":
    main()
