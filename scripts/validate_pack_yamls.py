#!/usr/bin/env python3
"""Validate all YAML files in packs/ parse correctly. Exit 1 on failure."""
from __future__ import annotations

from pathlib import Path

import yaml
import sys

packs_dir = Path("packs")
if not packs_dir.is_dir():
    print(f"  Packs directory not found: {packs_dir}")
    sys.exit(0)

yaml_files = sorted(packs_dir.rglob("*.yaml"))
errors: list[tuple[str, str]] = []
for f in yaml_files:
    try:
        yaml.safe_load(f.read_text())
    except Exception as e:
        msg = str(e).split("\n")[0]
        errors.append((str(f), msg))

if errors:
    for path, err in errors:
        print(f"  FAIL {path}: {err}")
    sys.exit(1)
else:
    print(f"  All pack YAML files parse OK ({len(yaml_files)} files)")
