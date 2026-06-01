"""Validate all YAML files in packs/ parse correctly. Exit 1 on failure."""
from pathlib import Path
import yaml
import sys

errors: list[tuple[str, str]] = []
for f in sorted(Path("packs").rglob("*.yaml")):
    try:
        yaml.safe_load(f.read_text())
    except Exception as e:
        msg = str(e).split("\n")[0]
        errors.append((str(f.relative_to(".")), msg))

if errors:
    for path, err in errors:
        print(f"  FAIL {path}: {err}")
    sys.exit(1)
else:
    print(f"  All pack YAML files parse OK ({len(list(Path('packs').rglob('*.yaml')))} files)")
