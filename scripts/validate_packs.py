#!/usr/bin/env python3
"""Static pack validation — loads every pack and validates structural integrity.

Usage:
    python scripts/validate_packs.py [packs_dir]

Exits 1 if any pack fails validation. Exits 0 if all pass.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ccya.pack import load_pack, validate_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all packs")
    parser.add_argument("packs_dir", default="packs", nargs="?")
    args = parser.parse_args()

    packs_dir = Path(args.packs_dir)
    if not packs_dir.is_dir():
        print(f"ERROR: Packs directory not found: {packs_dir}", file=sys.stderr)
        return 1

    failed = []
    passed = []

    for namespace in ("default", "custom", "generated"):
        ns_dir = packs_dir / namespace
        if not ns_dir.is_dir():
            continue
        for pack_dir in sorted(ns_dir.iterdir()):
            if not pack_dir.is_dir():
                continue
            pack_id = f"{namespace}/{pack_dir.name}"
            try:
                pack = load_pack(pack_id, packs_dir)
                validate_pack(pack, pack_id)
                passed.append(pack_id)
            except Exception as e:
                failed.append((pack_id, str(e)))

    for pack_id in passed:
        print(f"PASS: {pack_id}")

    for pack_id, error in failed:
        print(f"FAIL: {pack_id}: {error}", file=sys.stderr)

    if failed:
        print(f"\n{len(passed)} passed, {len(failed)} failed", file=sys.stderr)
        return 1

    print(f"\n{len(passed)} passed, 0 failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
