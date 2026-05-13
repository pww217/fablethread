# Wire scenario factions/locations to narrator prompt

## Status

`completed`

## Phases

1 phase: Pass `pack.scenario.factions` and `pack.scenario.locations` through the turn pipeline into `_narrate_messages()` so the narrator user prompt renders world faction/location context.

## Objective

The narrator user prompt template (`narrate_user.j2`) has `{% if world_factions %}` and `{% if world_locations %}` blocks, but these variables are never populated — `_world_factions` and `_world_locations` are always `[]` in `turn.py`, and `_narrate_messages()` doesn't accept them as parameters. Factions and locations are defined in `pack.scenario` (loaded from `scenario.yaml`) as `ScenarioBrief.factions` and `ScenarioBrief.locations`, but never flow through the turn pipeline. This change wires the same data through so the narrator can reference world factions and locations in prose.

## Non-goals

- Do not modify `Faction` or `NamedLocation` Pydantic models (in `pack.py`).
- Do not modify `scenario.yaml` format.
- Do not modify the eval harness — it already sources this data correctly for metadata.
- Do not modify `_slugify` or any names.py functions.
- Do not add factions/locations to state — they are pack-level static data, not persisted.

## Firm decisions

1. Add `pack_factions` and `pack_locations` parameters to `run_turn()` and `run_turn_retry()` signatures.
2. Pass them through to `_narrate_messages()` as `world_factions` and `world_locations`.
3. Add `world_factions` and `world_locations` parameters to `_narrate_messages()` signature and include them in the user template `user_ctx` dict only (not the system template — there is no faction/location block in `narrate_system.j2`).
4. Routes.py callers pass `pack.scenario.factions` / `pack.scenario.locations` when present, empty list otherwise.
5. Eval runner already passes `pack_narrator_rules` and `pack_world_rules` — add the same pattern for factions/locations.
6. The dead `_world_factions: list[dict[str, str]] = []` assignments in `turn.py` are replaced with the wired values.

## Conflicts and overlap

- **prompt-hygiene-corrected.md Step 1.1**: The prompt-hygiene plan references removing a `{% if world_factions or world_locations %}` block from `narrate_system.j2`. This block does not exist in the system template — it only exists in `narrate_user.j2`. The prompt-hygiene plan's Step 1.1 is **SUPERSEDED** for the system template portion. The prompt-hygiene plan's Risk #1 and Ambiguity #3 reference this nonexistent block and need updating (see ordering.md).
- **remove-faction-pool-system.md**: Already implemented and removed the old pool system; this plan adds the new scenario-based wiring that the old plan intentionally left out (templates were a non-goal).

## Implementation — Phase 1: Wire factions/locations through the turn pipeline

### Context files to load

1. `ccya/engine/turn.py`
2. `ccya/engine/narrate.py`
3. `ccya/server/routes.py`
4. `ccya/eval/runner.py`
5. `ccya/prompts/narrate_user.j2`
6. `ccya/pack.py` — `Faction`, `NamedLocation`, `ScenarioBrief` models
7. `tests/test_prompts.py`
8. `tests/test_engine_smoke.py`

### Detailed steps

#### Step 1.1 — Add parameters to `_narrate_messages()` in narrate.py

**File:** `ccya/engine/narrate.py`

**What:** Add `world_factions` and `world_locations` parameters to the `_narrate_messages()` signature and include them in `user_ctx`. Do NOT add them to the system template render — there is no faction/location block in `narrate_system.j2`.

**Why:** The user template blocks expect these variables. They need to be passed through the function.

**Code Snippet**
```python
# _narrate_messages() signature — add after turn_no: int = 0:
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],

# user_ctx dict — add after the "scene_pressure" line:
        "world_factions": world_factions,
        "world_locations": world_locations,
```

**Validation:** `_narrate_messages()` signature has 2 new optional parameters with defaults `[]`. The `user_ctx` dict includes the new keys.

#### Step 1.2 — Wire factions/locations in `run_turn()` and `run_turn_retry()` in turn.py

**File:** `ccya/engine/turn.py`

**What:**
1. Add `pack_factions` and `pack_locations` parameters to `run_turn()` signature (after `pack_world_rules`).
2. Add the same parameters to `run_turn_retry()` signature.
3. Replace the dead `_world_factions = []` / `_world_locations = []` assignments with actual data from `pack_factions`/`pack_locations`.
4. Pass `world_factions=_world_factions` and `world_locations=_world_locations` to `_narrate_messages()` in both call sites.

**Why:** The turn pipeline needs to source faction/location data from the pack and pass it to the narrator.

**Code Snippet**
```python
# run_turn() signature (around line 237, after pack_world_rules):
    pack_factions: list[dict[str, str]] = [],
    pack_locations: list[dict[str, str]] = [],

# run_turn_retry() signature (around line 1008, after pack_world_rules):
    pack_factions: list[dict[str, str]] = [],
    pack_locations: list[dict[str, str]] = [],

# In run_turn() body — replace lines 463-464:
# From:
        _world_factions: list[dict[str, str]] = []
        _world_locations: list[dict[str, str]] = []
# To:
        _world_factions = pack_factions if pack_factions else []
        _world_locations = pack_locations if pack_locations else []

# In run_turn() _narrate_messages() call — add after turn_no=turn_no:
            world_factions=_world_factions,
            world_locations=_world_locations,

# In run_turn_retry() body — replace lines 1113-1114:
# From:
        _world_factions: list[dict[str, str]] = []
        _world_locations: list[dict[str, str]] = []
# To:
        _world_factions = pack_factions if pack_factions else []
        _world_locations = pack_locations if pack_locations else []

# In run_turn_retry() _narrate_messages() call — add after scene_pressure line:
            world_factions=_world_factions,
            world_locations=_world_locations,
```

**Validation:** Both `run_turn` and `run_turn_retry` accept `pack_factions` and `pack_locations` as keyword-only parameters with `[]` defaults. The `_world_factions`/`_world_locations` variables are populated from these params. Both `_narrate_messages()` calls include the new keyword arguments.

#### Step 1.3 — Fix template field name mismatch in narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`

**What:** Change `f.alignment` to `f.disposition` on line 28. The `Faction` model (in `pack.py:108-112`) has `disposition` ("neutral" | "hostile" | "friendly"), not `alignment`.

**Why:** Without this fix, the user template faction block renders `(None)` for alignment — the disposition is never shown to the narrator in the user prompt.

**Code Snippet**
```jinja2
# Line 28: Change from:
{% for f in world_factions %}- **{{ f.name }}** ({{ f.alignment }}){% if f.alignment == "friendly" and pc_allegiance == f.id %} — your faction{% endif %}
# To:
{% for f in world_factions %}- **{{ f.name }}** ({{ f.disposition }}){% if f.disposition == "friendly" and pc_allegiance == f.id %} — your faction{% endif %}
```

**Validation:** The user template faction block renders disposition values ("neutral", "hostile", "friendly") matching the `Faction` model. The `pc_allegiance` comparison still works since `pc_allegiance` is the faction `id` string.

#### Step 1.4 — Enhance location block in narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`

**What:** The current location block (lines 58-62) only renders `loc.name`. Enhance it to also show `loc.type` for better context, matching the `NamedLocation` model fields (`id`, `name`, `type`, `description`).

**Why:** The `NamedLocation` model has `type` and `description` fields that provide useful context for the narrator. The current block wastes the opportunity to ground the narrator in the world.

**Code Snippet**
```jinja2
# Lines 58-62: Change from:
{% if world_locations and ages and ages.get('location_age', 0) >= 3 -%}
### Nearby Locations
{% for loc in world_locations %}- {{ loc.name }}
{% endfor -%}
{% endif -%}
# To:
{% if world_locations and ages and ages.get('location_age', 0) >= 3 -%}
### Nearby Locations
{% for loc in world_locations %}- **{{ loc.name }}** ({{ loc.type }})
{% endfor -%}
{% endif -%}
```

**Validation:** Location block renders `name` and `type` (e.g., "Marrow's Crossing (market town)").

#### Step 1.5 — Update routes.py callers

**File:** `ccya/server/routes.py`

**What:** Add `pack_factions` and `pack_locations` arguments to both `run_turn()` and `run_turn_retry()` calls, following the same pattern as `pack_narrator_rules` and `pack_world_rules`.

**Why:** The server needs to pass the pack's scenario data to the turn pipeline.

**Code Snippet**
```python
# GET /turn — run_turn() call (after line 113):
                pack_factions=[f.model_dump() for f in (_app_mod._active_pack.scenario.factions if _app_mod._active_pack.scenario else [])],
                pack_locations=[loc.model_dump() for loc in (_app_mod._active_pack.scenario.locations if _app_mod._active_pack.scenario else [])],

# GET /turn/retry — run_turn_retry() call (after line 211):
                pack_factions=[f.model_dump() for f in (_app_mod._active_pack.scenario.factions if _app_mod._active_pack.scenario else [])],
                pack_locations=[loc.model_dump() for loc in (_app_mod._active_pack.scenario.locations if _app_mod._active_pack.scenario else [])],
```

**Validation:** Both route handlers pass faction/location data from `pack.scenario` when present, empty list otherwise. Consistent with `pack_narrator_rules` / `pack_world_rules` pattern.

#### Step 1.6 — Update eval runner caller

**File:** `ccya/eval/runner.py`

**What:** Add `pack_factions` and `pack_locations` arguments to the `run_turn()` call in `run_scenario()`, following the same pattern.

**Why:** The eval harness needs to pass scenario data to the narrator for accurate evaluation.

**Code Snippet**
```python
# run_scenario() — run_turn() call (after line 505):
                pack_factions=[f.model_dump() for f in (pack.scenario.factions if pack.scenario else [])],
                pack_locations=[loc.model_dump() for loc in (pack.scenario.locations if pack.scenario else [])],
```

**Validation:** Eval runner passes faction/location data consistently with the server routes.

#### Step 1.7 — Test impact assessment

**File:** `tests/test_prompts.py`

**What:** No change needed. `_make_narrate_user_ctx()` includes `"world_factions": []` and `"world_locations": []` which are still part of `user_ctx` (the user template references them). The test renders `narrate_user.j2` directly — these keys remain in the context dict.

**File:** `tests/test_engine_smoke.py`

**What:** No change needed. The `_run()` and `_run_with_tokens()` helpers call `run_turn()` without the new parameters. Since they have `[]` defaults, existing tests pass through unchanged.

**Validation:** All existing tests continue to pass. The new parameters are optional with `[]` defaults.

### Tests to write or update

- `tests/test_engine_smoke.py`: Add a test that verifies `pack_factions` data appears in the rendered user prompt. Use `_FakeLLM` to capture the messages, then assert the system prompt contains faction names from the passed `pack_factions` list.

### REPOMAP updates required

- `docs/REPOMAP/engine.md`:
  - `_narrate_messages`: Add `world_factions`, `world_locations` to the parameter list.
  - `run_turn`: Add `pack_factions`, `pack_locations` to the signature.
  - `run_turn_retry`: Add `pack_factions`, `pack_locations` to the signature.

### Risks

1. **Token budget impact:** Adding faction/location data to the prompt increases user prompt size. The existing token budget trimming (`trim_messages`) handles this — no config change needed.
2. **Legacy packs without scenario:** Packs without `scenario.yaml` will pass empty lists, which is correct — the `{% if world_factions %}` blocks render empty.
3. **Location age gate:** The location block only renders when `ages.get('location_age', 0) >= 3`. This means locations won't appear in early turns. This is intentional — it prevents the narrator from being overwhelmed with world context on turn 1.

## Ambiguities requiring resolution before execution

None.
