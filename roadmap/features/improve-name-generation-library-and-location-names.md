---
title: "Improve Name Generation: Library Selection + Better Location Names"
status: scoping
urgency: 3
size: medium
created: 2026-06-24
labels:
  - engine
  - seed
---

# Improve Name Generation: Library Selection + Better Location Names

## Problem

The current Faker-based name generation has two compounding problems:

1. **Settlement names are first-name-derived trash.** Locations like `Evenshire`, `Aliceberg` — settlement names are generated from `faker.city()` which in many locales just returns `{FirstName} {suffix}` style names. These look absurd in play.

2. **Faker is wrong tool for fantasy/sci-fi/ancient genres.** Faker is designed for modern real-world name data. It cannot sensibly generate:
   - Fantasy names (elf, dwarf, orc, etc.)
   - Sci-fi names (colony worlds, alien-influenced cultures)
   - Ancient names (Greek, Roman, Egyptian, Norse, etc.)
   - Even alternate-history or mythic settings struggle.

The result is that non-historical/non-present-day packs get poor name quality, and the narrator has to work with a name pool that doesn't fit the setting at all.

## Proposed Solution

### 1. Pack-level library selection

Add a `name_library` (or `use_pynames: bool`) field to the pack manifest or scenario. The engine uses this to select which name library to use:

| Setting | Library | Notes |
|---------|---------|-------|
| `name_library: "faker"` (default) | Faker | Historical, present-day, realistic settings |
| `name_library: "pynames"` | [pynames](https://pypi.org/project/pynames/) | Fantasy, sci-fi, ancient, mythic, otherworldly |

This is a simple boolean/config trigger at the pack level — no per-NPC routing.

### 2. Fix location name generation

- **Current:** `faker.city()` produces first-name-based city names in many locales.
- **Fix:** Either (a) generate from surname pools instead of first names, or (b) use a separate location-name generator that produces proper place names (e.g., `{Surname}{suffix}` patterns, or a dedicated library).
- This fix should apply regardless of which name library is selected.

**2026-06-24:** Implemented surname-based location names (`last_name + suffix`). Also added surnames to all NPC/PC name generation (`first_name last_name` format).

### 3. pynames integration

`pynames` provides:
- Fantasy races (elf, dwarf, orc, goblin, etc.)
- Fantasy languages/roots
- Ancient names (Greek, Roman, Egyptian, etc.)
- It has a clean API — similar single-function call pattern to Faker.

Integration path:
- Add `pynames` to dependencies
- Create `ccya/engine/names_pynames.py` (mirrors `names.py` pattern)
- Add `name_library` field to pack manifest schema
- Route through `names.py` factory or directly in `seed.py` / `narrate.py` context builders

## References

- `ccya/engine/names.py` — current Faker-only implementation
- `ccya/engine/seed.py:155` — `generate_name_pool()` call site
- `ccya/engine/narrate.py:158` — `generate_npc_names_split()` call site
- `ccya/prompts/generate_seed_user.j2:37-43` — seed template name_pool rendering
- `ccya/prompts/narrate_user.j2:22-29` — narrate template npc_name_pool rendering

## Status

- `scoping` (surname suffix fix implemented 2026-06-24; pynames integration remaining)
