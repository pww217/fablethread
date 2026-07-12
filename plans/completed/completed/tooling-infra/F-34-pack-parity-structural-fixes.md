# Plan: F-34 — Pack parity: manifest fields, pool min counts, pre-write validation

## Design Reference

- Design: `docs/design/to_scope/pack-parity-redesign.md`

## Problem Statement

Generated packs have three structural gaps vs default packs: missing `description` and `files` on PackManifest, no pool min count enforcement in `validate_pack()`, and no pre-write validation in `generate_pack.py`. These gaps let malformed or incomplete packs reach disk and crash at startup rather than at generation time.

## Firm decisions (from design)

1. `version` and `mode` are removed from PackManifest (both dead/unused fields).
2. `pc_situation_schema` has no minimum count — a pack may legitimately have 0 keys.
3. Content quality is a non-goal; focus on structural parity only.
4. No backward compatibility — old packs that don't conform are simply invalid.
5. All phases touch one concern each; ordered by dependency.

## Scope

- **Phase 1:** Fix `generate_pack.py` to set `description` and `files` on PackManifest + add pool min counts to `validate_pack()`
- **Phase 2:** Add pre-write validation in `generate_pack.py`

## Status

`completed`

---

## Phase 01: Manifest fields + pool min counts

### Depends on

None

### Context files to load

- `ccya/engine/generate_pack.py:149-155` — PackManifest construction (missing `description` and `files`)
- `ccya/pack.py:382-395` — `validate_pack()` pool validation (no min count checks)
- `ccya/pack.py:242-253` — PackManifest schema (current state)

### What changes

**1. `ccya/engine/generate_pack.py` — set `description` and `files` on generated PackManifest.**

The LLM generates `brief.description` in ScenarioBrief. Use it for the manifest description. For `files`, set `world` and `scenario` to the filenames being written.

**2. `ccya/pack.py` — add min count checks to `validate_pack()`.**

Add one-liner per pool: check `len(entries) >= 1` for `situation_archetypes`, `arc_categories`, `character_dynamics`, `moral_pressures`, `npc_bonds`. `factions` and `pc_situation_schema` have no min count per design.

### Where to change

`ccya/engine/generate_pack.py:149-155` — PackManifest constructor

**Before (current):**
```python
manifest = PackManifest(
    id=pack_id,
    name=pack_name,
    tone_tags=tone_tags,
    name_locales=brief.name_locales,
    use_male_only_names=False,
)
```

**After:**
```python
manifest = PackManifest(
    id=pack_id,
    name=pack_name,
    description=brief.description or "",
    tone_tags=tone_tags,
    files=PackFiles(world="world.md", scenario="scenario.yaml"),
    name_locales=brief.name_locales,
    use_male_only_names=False,
)
```

`ccya/pack.py:382-395` — pool validation in `validate_pack()`

**Where to change:** After the existing `_validate_pool_entries()` call (line 393), add min count check.

**Before (current):**
```python
    for pool_name, entries in pool_fields:
        if entries:
            try:
                _validate_pool_entries(entries, pool_name)
            except ValueError as ve:
                errors.append(f"{label}: {ve}")
```

**After:**
```python
    for pool_name, entries in pool_fields:
        if not entries:
            errors.append(f"{label}: scenario.{pool_name} pool must have at least 1 entry (has 0)")
        else:
            try:
                _validate_pool_entries(entries, pool_name)
            except ValueError as ve:
                errors.append(f"{label}: {ve}")
```

### Why

Generated packs are missing `description` and `files` fields that default packs have. This creates structural parity gaps — the manifest schema allows them but the generator never populates them. Pool min counts prevent `_select_from_pool()` ValueError at seed time by catching empty pools at pack load time instead.

### Validation

- `make check` passes
- `ev.py pack-list` shows generated packs with `description` and `files` populated
- Loading a generated pack with empty pool passes validation; loading one with 0-entry pool fails with clear error

---

## Phase 02: Pre-write validation in generate_pack.py

### Depends on

Phase 01

### Context files to load

- `ccya/engine/generate_pack.py:126-168` — `generate_pack_from_brief()` flow (brief → scenario.yaml → pack.yaml)
- `ccya/pack.py:356-425` — `validate_pack()` function

### What changes

**`ccya/engine/generate_pack.py` — call `validate_pack()` before writing files.**

After `ScenarioBrief` is assembled from LLM output (line ~126), construct a temporary `Pack` with the brief and call `validate_pack()`. If it raises, retry the LLM (already wrapped in retry loop). Only write files if validation passes.

### Where to change

`ccya/engine/generate_pack.py:118-134` — after brief assembly, before file writes

**Where to change:** Insert validation after brief is built (around line 126) and before `scenario.yaml` write (line 130).

**After (inserted code):**
```python
from ccya.pack import Pack, validate_pack

# Validate before writing to disk
temp_pack = Pack(manifest=PackManifest(id=pack_id, name=pack_name), scenario=brief)
validate_pack(temp_pack, pack_id=pack_id)
```

### Why

Currently `generate_pack.py` writes files to disk without validating the LLM output. A malformed generated pack crashes at startup, not at generation time. Pre-write validation catches LLM errors early and triggers a retry within the existing retry loop.

### Validation

- `make check` passes
- `ev.py run --scenario <bad-pack-scenario>` retries on validation failure instead of writing broken files
- `packs/` only contains packs that pass `validate_pack()`

---

## Documentation updates

- `docs/architecture/step2c-record.md` — update PackManifest schema reference (remove `version`, `mode` from any remaining mentions)
- `docs/repomap.md` — update `validate_pack()` entry to note pool min count checks
- `AGENTS.md` — no changes needed (already notes `version`/`mode` removed)
