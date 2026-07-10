# Plan: F-15 — Pack validation gate

## Design Reference

- Design: `docs/design/to_scope/pack-validation-design.md`
- Related: `docs/design/to_scope/pack-parity-redesign.md` (depends on this)

## Problem Statement

Packs enter through two paths (YAML authoring and LLM generation) but neither validates against the same schema. `PackManifest` uses `extra: ignore` — typos silently drop. Several fields exist in every default `pack.yaml` but aren't declared. Generated packs derive `pack_name` but never write `description`, `version`, `mode`, or `files`. Scenario pool fields are never validated for duplicate IDs or broken `incompatible_with` references. `list_packs()` silently skips bad directories. The result: malformed packs cause silent failures later.

## Firm decisions (from design)

1. One golden schema — every pack (default, custom, generated) conforms to the same schema. Only `pc_situation_schema` keys vary between packs.
2. One validation function — `validate_pack(pack, pack_id)` called by both paths. No separate validation for different pack types.
3. Fail fast — validation runs at `load_pack()` time. Bad packs crash with clear actionable error messages.
4. `PackManifest` uses `extra: forbid`. All fields that exist in pack YAML files must be declared.
5. Structural validation only — no content quality checks.
6. `baseline_facts` is dead code — torn out. `world_facts` from `ScenarioBrief` is the universal canon mechanism.

## Scope

- **Phase 1:** Schema changes (PackManifest + ScenarioBrief) — add undeclared fields, `extra: forbid`, remove `baseline_facts`, `min_length=3` on `world_facts`
- **Phase 2:** `validate_pack()` function + `_validate_pool_entries()` helper
- **Phase 3:** Integrate validation into `load_pack()`, update `list_packs()` for warnings
- **Phase 4:** `scripts/validate_packs.py` static validation script

## Status

`completed`

---

## Phase 01: Schema changes (PackManifest + ScenarioBrief)

### Depends on

None — but this was already implemented in the previous session. Verify before proceeding.

### Context files to load

- `ccya/pack.py:237-254` — `PackFiles`, `PackManifest` models
- `ccya/pack.py:161-193` — `ScenarioBrief` model

### What changes

Schema changes were already applied:
- `PackFiles` class added (lines 237-239)
- `PackManifest` updated: `extra: forbid`, `description`, `version`, `mode`, `files` fields added, `baseline_facts` removed
- `ScenarioBrief.world_facts` updated: `min_length=3` added

### Verification

Check that `ccya/pack.py` matches the design spec. If any changes are missing, add them here.

### Why

Foundation for all subsequent validation. Without correct schema, validation can't run.

### Validation

- `make typecheck` passes (Pydantic schema is correct)
- `ev.py prompt-eval dump <save-dir> --turn 1` loads default packs without error

---

## Phase 02: `validate_pack()` function + `_validate_pool_entries()` helper

### Depends on

Phase 01 (schema changes verified)

### Context files to load

- `ccya/pack.py:289-335` — `load_pack()` function (integration point)
- `ccya/pack.py:338-365` — `list_packs()` function (needs warning behavior)

### What changes

Add two functions to `ccya/pack.py` before `list_packs()`:

1. `_validate_pool_entries(entries, pool_name) -> list[str]` — helper that checks:
   - Unique IDs within pool
   - All `incompatible_with` references resolve to valid IDs in the same pool
   - Returns list of IDs for caller use

2. `validate_pack(pack: Pack, pack_id: str | None = None) -> None` — main validation that checks:
   - Manifest structural: `id` non-empty, `name` non-empty, `mode` is `"dynamic"` or `"static"`
   - Dynamic mode: `scenario` must not be `None` if `mode == "dynamic"`
   - World facts minimum: `world_facts` must have at least 3 entries
   - Pool entry integrity: unique IDs, valid `incompatible_with` references for `situation_archetypes`, `arc_categories`, `character_dynamics`, `moral_pressures`, `npc_bonds`
   - Faction uniqueness: faction IDs must be unique
   - PC situation schema uniqueness: keys must be unique
   - Scene detail bundles uniqueness: IDs must be unique
   - Raises `ValueError` with single aggregated message listing all problems

### Where to change

`ccya/pack.py` — add before `list_packs()` (before line 338)

### Before (current):

```python
def list_packs(packs_dir: Path) -> list[PackManifest]:
    manifests: list[PackManifest] = []
```

### After:

```python
def _validate_pool_entries(entries: list[PoolEntry], pool_name: str) -> list[str]:
    """Helper for pool validation. Checks unique IDs and valid incompatible_with references.

    Returns the list of IDs for caller use (e.g., faction uniqueness check).
    """
    errors: list[str] = []
    seen_ids: dict[str, int] = {}
    for i, entry in enumerate(entries):
        if entry.id in seen_ids:
            errors.append(f"pool '{pool_name}' has duplicate ID '{entry.id}' (first at index {seen_ids[entry.id]}, duplicate at {i})")
        else:
            seen_ids[entry.id] = i
        for ref in entry.incompatible_with:
            if ref not in seen_ids and ref not in {e.id for e in entries}:
                errors.append(f"pool '{pool_name}' entry '{entry.id}' references non-existent incompatible_with ID '{ref}'")
    return list(seen_ids.keys())


def validate_pack(pack: Pack, pack_id: str | None = None) -> None:
    """Validate a pack's structural integrity.

    Called at the end of `load_pack()`. Raises `ValueError` with a single
    aggregated message listing every problem found. Each problem identifies
    the pack, the field path, and what's wrong.
    """
    label = f"Pack '{pack_id}'" if pack_id else "Pack"
    errors: list[str] = []

    # 1. Manifest structural
    if not pack.manifest.id.strip():
        errors.append(f"{label}: manifest.id is empty")
    if not pack.manifest.name.strip():
        errors.append(f"{label}: manifest.name is empty")
    if pack.manifest.mode not in ("dynamic", "static"):
        errors.append(f"{label}: manifest.mode must be 'dynamic' or 'static', got '{pack.manifest.mode}'")

    # 2. Dynamic mode requirements
    if pack.manifest.mode == "dynamic" and pack.scenario is None:
        errors.append(f"{label}: mode=dynamic requires scenario.yaml")

    # 3. World facts minimum
    if pack.scenario is not None and len(pack.scenario.world_facts) < 3:
        errors.append(f"{label}: scenario.world_facts must have at least 3 entries (has {len(pack.scenario.world_facts)})")

    # 4. Pool entry structural integrity
    pool_fields: list[tuple[str, list[PoolEntry]]] = [
        ("situation_archetypes", pack.scenario.situation_archetypes if pack.scenario else []),
        ("arc_categories", pack.scenario.arc_categories if pack.scenario else []),
        ("character_dynamics", pack.scenario.character_dynamics if pack.scenario else []),
        ("moral_pressures", pack.scenario.moral_pressures if pack.scenario else []),
        ("npc_bonds", pack.scenario.npc_bonds if pack.scenario else []),
    ]
    for pool_name, entries in pool_fields:
        if entries:
            _validate_pool_entries(entries, pool_name)

    # 5. Faction uniqueness
    if pack.scenario and pack.scenario.factions:
        _validate_pool_entries(pack.scenario.factions, "factions")

    # 6. PC situation schema uniqueness
    if pack.scenario and pack.scenario.pc_situation_schema:
        seen_keys: dict[str, int] = {}
        for i, entry in enumerate(pack.scenario.pc_situation_schema):
            if entry.key in seen_keys:
                errors.append(f"{label}: scenario.pc_situation_schema has duplicate key '{entry.key}' (first at index {seen_keys[entry.key]}, duplicate at {i})")
            else:
                seen_keys[entry.key] = i

    # 7. Scene detail bundles uniqueness
    if pack.scenario and pack.scenario.scene_detail_bundles:
        seen_bundles: dict[str, int] = {}
        for i, bundle in enumerate(pack.scenario.scene_detail_bundles):
            if bundle.id in seen_bundles:
                errors.append(f"{label}: scenario.scene_detail_bundles has duplicate ID '{bundle.id}' (first at index {seen_bundles[bundle.id]}, duplicate at {i})")
            else:
                seen_bundles[bundle.id] = i

    if errors:
        raise ValueError("; ".join(errors))


def list_packs(packs_dir: Path) -> list[PackManifest]:
```

### Why

This is the core validation logic. Both `load_pack()` and the static script call this function. It catches:
- Bad manifests (empty id/name, invalid mode)
- Missing scenario for dynamic packs
- Insufficient world facts (universal canon)
- Duplicate pool IDs (causes pool selection bugs)
- Broken `incompatible_with` references (causes seed crashes)

### Validation

- `make typecheck` passes
- `ev.py prompt-eval dump <save-dir> --turn 1` loads default packs without error (all pass)
- Manual test: create a pack with duplicate pool IDs — `load_pack()` raises `ValueError` with clear message

---

## Phase 03: Integrate validation into `load_pack()` and update `list_packs()`

### Depends on

Phase 02 (validate_pack function exists)

### Context files to load

- `ccya/pack.py:289-335` — `load_pack()` function

### What changes

1. Call `validate_pack(pack, pack_id)` at the end of `load_pack()`, before returning. Wrap in try/except — if validation fails, re-raise as `ValueError` with pack path context.

2. Update `list_packs()` to catch validation errors and log warnings instead of silently skipping. The pack picker should still render but mark invalid packs.

### Where to change

`ccya/pack.py:289-365` — `load_pack()` and `list_packs()`

### Before (current):

```python
def load_pack(pack_id: str, packs_dir: Path) -> Pack:
    pack_dir = _resolve_pack_dir(pack_id, packs_dir)
    # ... loading logic ...
    return Pack(
        manifest=manifest,
        scenario=scenario,
        opening_scene=opening_scene,
        style=style,
    )
```

### After:

```python
def load_pack(pack_id: str, packs_dir: Path) -> Pack:
    pack_dir = _resolve_pack_dir(pack_id, packs_dir)
    # ... loading logic unchanged ...
    pack = Pack(
        manifest=manifest,
        scenario=scenario,
        opening_scene=opening_scene,
        style=style,
    )
    validate_pack(pack, pack_id)
    return pack
```

For `list_packs()`, wrap the `PackManifest(**data)` call in try/except and also call `validate_pack()` — but log warnings instead of crashing:

```python
def list_packs(packs_dir: Path) -> list[PackManifest]:
    manifests: list[PackManifest] = []
    if not packs_dir.is_dir():
        return manifests
    search_dirs = [
        packs_dir / "generated",
        packs_dir / "default",
        packs_dir / "custom",
    ]
    seen: set[str] = set()
    for search in search_dirs:
        if not search.is_dir():
            continue
        for child in sorted(search.iterdir()):
            if not child.is_dir():
                continue
            manifest_path = child / "pack.yaml"
            if manifest_path.exists() and child.name not in seen:
                seen.add(child.name)
                try:
                    with open(manifest_path) as f:
                        data = yaml.safe_load(f) or {}
                    manifest = PackManifest(**data)
                    # Validate but don't crash — log warnings for invalid packs
                    try:
                        validate_pack(Pack(manifest=manifest), child.name)
                    except ValueError as ve:
                        _log.warning("Pack '%s' failed validation: %s", child.name, ve)
                    manifests.append(manifest)
                except Exception as err:
                    _log.warning("Skipping invalid pack manifest at %s: %s", manifest_path, err)

    return manifests
```

### Why

Makes validation mandatory for every pack load. `load_pack()` is the single entry point — all packs (default, custom, generated) pass through it. `list_packs()` logs warnings but doesn't crash — allows the UI to still render packs (with invalid status).

### Validation

- `make typecheck` passes
- `ev.py prompt-eval dump <save-dir> --turn 1` loads default packs without error
- Server starts without error with valid default packs
- Manual test: create a pack with invalid mode — `load_pack()` raises `ValueError`; `list_packs()` logs warning but returns manifest

---

## Phase 04: `scripts/validate_packs.py` static validation script

### Depends on

Phase 02 (validate_pack function exists)

### Context files to load

- `ccya/pack.py:289-365` — `load_pack()`, `list_packs()`, `validate_pack()`

### What changes

New file: `scripts/validate_packs.py`

Script that loads every pack in `packs/` and runs `validate_pack()` on each. Used for CI/pre-commit checks and manual verification. Exits 1 if any pack fails validation.

### Where to change

New file: `scripts/validate_packs.py`

### After:

```python
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
```

### Why

Static validation for CI/pre-commit/manual verification. Catches bad packs before they reach the server. The script is also useful for pack authors during development.

### Validation

- `python scripts/validate_packs.py` exits 0 with all default packs passing
- `python scripts/validate_packs.py` exits 1 when given a bad pack (test by creating one)

---

## Documentation updates

- `docs/repomap.md` — add `validate_pack()` and `_validate_pool_entries()` to `ccya/pack.py` section; add `scripts/validate_packs.py` to tooling section
- `docs/architecture/OVERVIEW.md` — add validation step to pack loading pipeline description
- `AGENTS.md` — add `scripts/validate_packs.py` to tooling notes (fast pack validation)
