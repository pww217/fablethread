# Remove general random faction/location pool system

## Status
`open`

## Part of
Standalone

## Dependencies
- None

## Conflicts and overlap
None. This plan only removes dead code paths and unused parameters. No other open plan touches `names.py` pool functions, `routes.py` new-game faction seeding, or `turn.py` world fallback logic.

## Objective
Tear out the general random faction and location pool system (`generate_faction_pool`, `generate_location_pool` in `names.py` and their wiring in `routes.py`, `seed.py`, `turn.py`). These functions generate generic names like "The Iron Hand" and "Coppergate" that compete with the seed-based faction system — faction names from `scenario.yaml` that are grounded in world facts, lore, and the seed fiction. After this change, factions and locations come exclusively from `pack.scenario` and are injected as `pack_factions` / `pack_locations` into the turn pipeline.

## Non-goals
- Do not modify `generate_name_pool`, `generate_npc_names`, `generate_npc_names_split` — these are still used for NPC name anchoring.
- Do not modify prompt templates.
- Do not modify `Faction` or `NamedLocation` Pydantic models.
- Do not modify `scenario.yaml` format or `ScenarioBrief` model.

## Affected files
| File | Change type | Summary |
|---|---|---|
| `ccya/engine/names.py` | modify | Delete `generate_faction_pool()` and `generate_location_pool()` functions and their docstrings |
| `ccya/engine/seed.py` | modify | Remove `faction_pool_seed` / `location_pool_seed` metadata assignment (Phase 5 block) |
| `ccya/server/routes.py` | modify | Remove `generate_faction_pool` / `generate_location_pool` import; remove pool seeding in `/new-game` and `/new-game/reroll` |
| `ccya/engine/turn.py` | modify | Remove `pack_factions`, `pack_locations` parameters from `run_turn` and `run_turn_retry`; remove `state.world` fallback for factions/locations |
| `ccya/engine/narrate.py` | modify | Remove `world_factions` and `world_locations` parameters from `_narrate_messages()` |
| `docs/REPOMAP/engine.md` | modify | Remove `generate_faction_pool` / `generate_location_pool` from names.py table; update `run_turn` signature |
| `docs/REPOMAP/pack.md` | modify | Remove `generate_faction_pool` / `generate_location_pool` references |
| `docs/REPOMAP/directory.md` | modify | Remove `generate_faction_pool` / `generate_location_pool` from names.py entry |
| `plans/TODO.md` | modify | Remove or strike through "Organization/faction name pool" item under P4 |

## Firm decisions
1. `generate_name_pool`, `generate_npc_names`, `generate_npc_names_split` are retained — still used for NPC name anchoring in `narrate.py`.
2. `pack_factions` and `pack_locations` parameters are removed entirely from `run_turn` and `run_turn_retry` — no replacement parameter needed.
3. `world_factions` and `world_locations` parameters are removed entirely from `_narrate_messages()` — no replacement needed.
4. The `state["world"]["factions"]` and `state["world"]["locations"]` legacy paths are removed — no migration needed since they were only populated by the torn-out pool functions.
5. `faction_pool_seed` and `location_pool_seed` metadata keys are removed from `seed_state.meta` — no migration needed.

## Implementation — Phase 1: Remove pool functions and their callers

### Context files to load
1. `ccya/engine/names.py`
2. `ccya/engine/seed.py`
3. `ccya/server/routes.py`
4. `ccya/engine/turn.py`
5. `ccya/engine/narrate.py`

### Overview
Delete `generate_faction_pool()` and `generate_location_pool()` from `names.py`, remove their import and calls in `routes.py` and `seed.py`, and clean up the now-unused `pack_factions`/`pack_locations` parameters and `state.world` fallback in `turn.py` and `narrate.py`.

### Detailed steps

#### Step 1.1 — Delete pool functions from names.py

**File:** `ccya/engine/names.py`

**What:** Remove `generate_faction_pool()` (lines 104–138) and `generate_location_pool()` (lines 141–175) along with their docstrings.

**Why:** These functions generate generic names ("The Iron Hand", "Coppergate") that compete with seed-based faction names from `scenario.yaml`. They are no longer needed.

**Code Snippet**
```python
# Delete lines 104–175 entirely:
#   def generate_faction_pool(...)
#   def generate_location_pool(...)
# Keep _slugify() — still used by generate_name_pool indirectly? No, it's not.
# Actually _slugify is only used by the two deleted functions. Remove it too.
# Keep everything else: _build_weighted_fakers, _pick, _ensure_ascii,
#   generate_name_pool, generate_npc_names, generate_npc_names_split
```

**Validation:** `names.py` should still export `generate_name_pool`, `generate_npc_names`, `generate_npc_names_split`, `_build_weighted_fakers`, `_pick`, `_ensure_ascii`. No other code should import `generate_faction_pool` or `generate_location_pool`.

### Tests to write or update
None needed. No tests reference these functions.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Remove `generate_faction_pool` and `generate_location_pool` from names.py function table entry.
- `docs/REPOMAP/pack.md`: Remove `generate_faction_pool` and `generate_location_pool` references.
- `docs/REPOMAP/directory.md`: Remove `generate_faction_pool` and `generate_location_pool` from names.py entry.

### Risks
1. **`_slugify` used elsewhere:** If `_slugify` is used by any other code, removing it would break things. Mitigation: grep confirms it is only used by the two deleted functions.

### Tests to update
- `tests/test_engine_smoke.py:TestTurnPipeline.test_pack_factions_in_narrate_system` — Remove `pack_factions` and `pack_locations` arguments from the `run_turn()` call. Remove assertions for "Test Faction", "hostile", "Test Location". Keep assertions for "Rule one." and "Rule two." (narrator rules still tested).

## Implementation — Phase 2: Remove pool seeding from routes.py and seed.py

### Context files to load
1. `ccya/server/routes.py`
2. `ccya/engine/seed.py`

### Overview
Remove the `generate_faction_pool` / `generate_location_pool` import and calls in `routes.py` (new-game and reroll endpoints), and remove the `faction_pool_seed` / `location_pool_seed` metadata assignment in `seed.py`.

### Detailed steps

#### Step 2.1 — Remove pool import and calls from routes.py

**File:** `ccya/server/routes.py`

**What:** 
1. Remove `generate_faction_pool, generate_location_pool` from the import on line 24.
2. Remove lines 344–349 in `/new-game` (dynamic pack branch): the `faction_pool_seed` / `location_pool_seed` extraction and pool generation calls.
3. Remove lines 378–383 in `/new-game/reroll`: the same pool generation calls.

**Why:** These calls populate `state["world"]["factions"]` and `state["world"]["locations"]` with randomly generated names. Since we're removing the pool functions and the `state.world` fallback, these calls serve no purpose.

**Code Snippet**
```python
# Line 24: Change from:
from ccya.engine.names import generate_faction_pool, generate_location_pool
# To:
# (remove the import entirely)

# In /new-game (around lines 344-349), remove:
#         # Phase 5: seed world factions and locations
#         meta = seed.setdefault("meta", {})
#         faction_seed = meta.pop("faction_pool_seed", None)
#         location_seed = meta.pop("location_pool_seed", None)
#         seed.setdefault("world", {})["factions"] = generate_faction_pool(faction_seed)
#         seed.setdefault("world", {})["locations"] = generate_location_pool(location_seed)

# In /new-game/reroll (around lines 378-383), remove:
#         # Phase 5: seed world factions and locations
#         meta = seed.setdefault("meta", {})
#         faction_seed = meta.pop("faction_pool_seed", None)
#         location_seed = meta.pop("location_pool_seed", None)
#         seed.setdefault("world", {})["factions"] = generate_faction_pool(faction_seed)
#         seed.setdefault("world", {})["locations"] = generate_location_pool(location_seed)
```

**Validation:** `routes.py` should still import and use `generate_seed` from `ccya.engine`. No references to `generate_faction_pool` or `generate_location_pool` should remain.

### Tests to write or update
None needed. No tests reference these functions.

### REPOMAP updates required
None (routes.py not in REPOMAP).

### Risks
1. **`meta.pop("faction_pool_seed", None)` side effect:** If `meta` is shared and the pop modifies the envelope's metadata, removing the pop could leave stale keys. Mitigation: `meta` is `seed.setdefault("meta", {})` which is a local dict derived from `envelope.seed_state.model_dump()` — no shared state.

#### Step 2.2 — Remove pool seed metadata from seed.py

**File:** `ccya/engine/seed.py`

**What:** Remove lines 251–254:
```python
# Phase 5: seed world factions and locations
seed_val = seed or hash(envelope.seed_state.meta.get("game_name", ""))
envelope.seed_state.meta["faction_pool_seed"] = seed_val
envelope.seed_state.meta["location_pool_seed"] = seed_val + 1
```

**Why:** These metadata keys were only consumed by `routes.py` to call the pool functions. With those functions and callers removed, the metadata is dead.

**Code Snippet**
```python
# Remove lines 251-254 entirely:
#         # Phase 5: seed world factions and locations
#         seed_val = seed or hash(envelope.seed_state.meta.get("game_name", ""))
#         envelope.seed_state.meta["faction_pool_seed"] = seed_val
#         envelope.seed_state.meta["location_pool_seed"] = seed_val + 1
```

**Validation:** `seed.py` should still call `_soft_validate_seed` and return the envelope. No references to `faction_pool_seed` or `location_pool_seed` should remain.

### Tests to write or update
None needed.

### REPOMAP updates required
- `docs/REPOMAP/seed.md`: Remove "injects baseline_facts into `world_state` → clears `compendium_touch_order` → seeds faction/location pools" from the engine integration description.

### Risks
None.

## Implementation — Phase 3: Remove unused parameters and fallbacks from turn.py and narrate.py

### Context files to load
1. `ccya/engine/turn.py`
2. `ccya/engine/narrate.py`

### Overview
Remove `pack_factions` and `pack_locations` parameters from `run_turn` and `run_turn_retry` signatures, remove the `state.world` fallback for factions/locations, and remove `world_factions` / `world_locations` parameters from `_narrate_messages()`.

### Detailed steps

#### Step 3.1 — Remove parameters and fallback from turn.py

**File:** `ccya/engine/turn.py`

**What:**
1. Remove `pack_factions`, `pack_locations` parameters from `run_turn()` signature (lines 242–243).
2. Remove `pack_factions`, `pack_locations` parameters from `run_turn_retry()` signature (lines 904–905).
3. Remove the `state.world` fallback block (lines 456–462 in `run_turn` and lines 1009–1015 in `run_turn_retry`):
```python
# Phase 5: world context from pack scenario (primary) or state world (legacy)
_world = state.get("world") or {}
_world_factions = pack_factions if pack_factions else list(_world.get("factions") or [])
_world_locations = pack_locations if pack_locations else list(_world.get("locations") or [])
_pc_allegiance = (state.get("pc") or {}).get("allegiance")
_pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
_pack_world_rules = pack_world_rules if pack_world_rules else []
```
Replace with:
```python
_pc_allegiance = (state.get("pc") or {}).get("allegiance")
_pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
_pack_world_rules = pack_world_rules if pack_world_rules else []
_world_factions: list[dict[str, str]] = []
_world_locations: list[dict[str, str]] = []
```

**Why:** `pack_factions` and `pack_locations` are always passed by `routes.py` (as empty list when no scenario). The `state.world` fallback was the legacy path for the torn-out pool system. Since we removed the pool functions and their callers, `state.world` will never contain faction/location data.

**Code Snippet**
```python
# run_turn() signature (lines 234-246):
# Remove:
#     pack_factions: list[dict[str, str]] = [],
#     pack_locations: list[dict[str, str]] = [],
#     pack_narrator_rules: list[str] = [],
#     pack_world_rules: list[str] = [],
# Keep:
#     pack_narrator_rules: list[str] = [],
#     pack_world_rules: list[str] = [],

# run_turn_retry() signature (lines 895-908):
# Same removal: remove pack_factions and pack_locations parameters.

# In run_turn() body (around lines 456-462):
# Replace:
#         # Phase 5: world context from pack scenario (primary) or state world (legacy)
#         _world = state.get("world") or {}
#         _world_factions = pack_factions if pack_factions else list(_world.get("factions") or [])
#         _world_locations = pack_locations if pack_locations else list(_world.get("locations") or [])
#         _pc_allegiance = (state.get("pc") or {}).get("allegiance")
#         _pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
#         _pack_world_rules = pack_world_rules if pack_world_rules else []
# With:
#         _pc_allegiance = (state.get("pc") or {}).get("allegiance")
#         _pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
#         _pack_world_rules = pack_world_rules if pack_world_rules else []
#         _world_factions: list[dict[str, str]] = []
#         _world_locations: list[dict[str, str]] = []

# In run_turn_retry() body (around lines 1009-1015):
# Same replacement.
```

**Validation:** `turn.py` should still call `_narrate_messages()` with `world_factions=_world_factions` and `world_locations=_world_locations` (now always empty lists). No references to `pack_factions` or `pack_locations` should remain.

### Tests to write or update
None needed. Existing tests pass `pack_factions` and `pack_locations` to `run_turn` — those calls will need to drop those arguments.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Update `run_turn` signature to remove `pack_factions` and `pack_locations` parameters.

### Risks
1. **Test code passes `pack_factions`/`pack_locations`:** `test_engine_smoke.py:TestTurnPipeline.test_pack_factions_in_narrate_system` passes `pack_factions` and `pack_locations` to `run_turn`. Mitigation: Remove those arguments and the corresponding assertions. Keep the `pack_narrator_rules` assertions.

#### Step 3.2 — Remove parameters from narrate.py

**File:** `ccya/engine/narrate.py`

**What:**
1. Remove `world_factions` and `world_locations` parameters from `_narrate_messages()` signature (lines 33–34).
2. Remove `world_factions` and `world_locations` from the `user_ctx` dict (lines 55–56).
3. Remove `world_factions` and `world_locations` from the system template render call (lines 63–64).

**Why:** These parameters are always empty lists now (passed as `[]` from `turn.py`). The templates render empty faction/location blocks when the lists are empty, which is the correct behavior — no factions to reference means no faction blocks.

**Code Snippet**
```python
# _narrate_messages() signature:
# Remove:
#     world_factions: list[dict[str, str]] = [],
#     world_locations: list[dict[str, str]] = [],

# user_ctx dict:
# Remove:
#         "world_factions": world_factions,
#         "world_locations": world_locations,

# System template render:
# Remove:
#         "world_factions": world_factions,
#         "world_locations": world_locations,
```

**Validation:** `_narrate_messages()` should still render `narrate_system.j2` and `narrate_user.j2` with the remaining context. The `world_factions` and `world_locations` template variables will be undefined, causing the `{% if world_factions %}` and `{% if world_locations %}` blocks to render empty (correct behavior).

### Tests to write or update
None needed.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: Remove `world_factions` and `world_locations` from `_narrate_messages` signature.

### Risks
None.

## Ambiguities requiring resolution before execution
None.

## TODO.md update

Under `## P4 — World Continuity`, strike through:
```markdown
- ~~**Organization/faction name pool** — seeded at game start, injected with political context — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`~~
```

Reason: The faction pool system has been torn out entirely. Factions now come exclusively from `scenario.yaml` via the seed-based system.
