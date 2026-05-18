# Config Renaming + Computation Migration (Phase 06b)

## Status
`open`

## Phases

2 tasks: (1) rename EngineConfig `scene_pressure_*` fields to thread-urgency-aware names, update config loading and all references, (2) migrate `_compute_narration_directive()` and `_compute_pacing_context()` from taking raw `list[dict] scene_pressure` parameter to deriving urgency counts from `arc.threads[] scope=scene`.

## Issue (North Star)

After phases 01-06 implement unified ArcThread + PacingContext architecture, EngineConfig still uses `scene_pressure_*` naming for urgency escalation thresholds that now govern arc-scoped thread age-based demotion and scene-scoped location-change expiry. The computation functions `_compute_narration_directive()` (line 365) and `_compute_pacing_context()` (line 449) in turn.py still accept `scene_pressure: list[dict[str, Any]]` as a raw parameter — Decision D7 from phase 05 says these should derive urgency data from unified `arc.threads[] scope=scene` instead of reading legacy scene_pressure dicts. This creates confusion: the config and computation layers use outdated terminology that doesn't match the unified model.

## Solution (North Star)

1. Rename EngineConfig fields: `scene_pressure_building_at` → `thread_urgency_building_at`, `scene_pressure_immediate_at` → `thread_urgency_immediate_at`, `scene_pressure_max_age` → `thread_urgency_max_age`, `scene_pressure_deescalate_on_success` → `thread_deescalate_on_success`, `scene_pressure_immediate_ttl` → `thread_urgency_immediate_ttl`. Update all references in turn.py, config.py defaults section and build_engine_config(). Keep game.yaml keys as-is for backward compat (config loading maps old keys to new field names).

2. Migrate `_compute_narration_directive()` from taking raw scene_pressure dicts to deriving urgency counts from `arc.threads[] scope=scene`: replace `sum(1 for p in scene_pressure if p.get("urgency") == "immediate")` with equivalent filter on unified threads; same for building/normal urgency counts. Update `_compute_pacing_context()` signature and call sites (turn.py lines 886, 915) to pass derived thread list instead of raw pressure dicts.

## Firm decisions
1. Config field renaming: rename all `scene_pressure_*` fields in EngineConfig to use clearer naming that reflects unified model (`thread_urgency_building_at`, etc.). Keep game.yaml config keys as-is for backward compatibility — build_engine_config() maps old keys to new field names via explicit defaults dict. This avoids breaking existing campaign configs while making the Python API clear.

2. Computation migration: `_compute_narration_directive()` derives urgency counts from `arc.threads[] scope=scene` where `active=True`. The function signature changes from `(narrative_velocity, scene_pressure: list[dict], ages, threat_ages, ...)` to `(narrative_velocity, threads_scope_scene: list[ArcThread], ages, threat_ages, ...)`. Internal urgency counting uses ArcThread.urgency field instead of dict.get("urgency"). This eliminates the last code path that reads raw scene_pressure dicts for computation (state writes were already removed in phase 06).

3. `_compute_pacing_context()` passes derived `arc.threads[] scope=scene` to `_compute_narration_directive()`. The caller sites at turn.py lines ~886 and ~915 build the thread list via `[t for t in arc.threads if t.scope == "scene" and t.active]` instead of passing raw pressure dicts from state.

## Risks, Ambiguities, and Blockers
- **Risk:** Config renaming changes field names that may be referenced by external code or tests. Must update all references across the codebase (turn.py uses config.scene_pressure_building_at etc.). Check for any game.yaml files in test fixtures that use old keys — those are fine since build_engine_config() maps them via defaults.
- **Ambiguity:** Should `scene_pressure_immediate_ttl` be renamed to something like `thread_urgency_immediate_ttl` or dropped entirely? Phase 05 design says urgency escalation is replaced by scope-aware rules, but the TTL may still influence PacingContext directive computation. Decision: keep it with new name for now; if unused after migration, delete in a follow-up cleanup phase.
- **Blocker:** None identified. This phase only touches config.py and turn.py (computation functions + call sites).

## Dependencies
Phases 01-06 must complete — unified ArcThread model exists with `scope: Literal["scene", "arc"]` and `urgency: Literal["background", "normal", "urgent"]` fields that computation migration depends on. Phase 05 Decision D2 (ArcThread.resolution_state) is NOT a dependency for this phase.

---

## Implementation Steps

### Step 6b.1 — Rename EngineConfig scene_pressure_* fields to thread_urgency_* names

**File:** `ccya/engine/config.py`

**What:** Five field renames in the EngineConfig dataclass:
- Line 67: `scene_pressure_building_at: int = 3` → `thread_urgency_building_at: int = 3`
- Line 68: `scene_pressure_immediate_at: int = 5` → `thread_urgency_immediate_at: int = 5`
- Line 70: `scene_pressure_max_age: int = 8` → `thread_urgency_max_age: int = 8`
- Line 83: `scene_pressure_deescalate_on_success: bool = True` → `thread_deescalate_on_success: bool = True`
- Line 73: `scene_pressure_immediate_ttl: int = 8` → `thread_urgency_immediate_ttl: int = 8`

Update comments to reflect unified model context (e.g., "Scene pressure urgency escalation thresholds" → "Thread urgency escalation thresholds"). Update build_engine_config() mapping lines 151-164 to use new field names while keeping old game.yaml keys for backward compat.

**Why:** The `scene_pressure_*` naming implies a separate scene_pressure[] model that no longer exists after phases 01-06. Renaming makes the Python API consistent with unified ArcThread terminology and clarifies what these thresholds govern (thread urgency escalation, not pressure dicts).

**Validation:** Read config.py after changes to confirm: all five fields renamed; build_engine_config() uses new field names in return statement while game.yaml keys remain unchanged for backward compat. Run `python -c "from ccya.engine.config import EngineConfig; c = EngineConfig(); print(c.thread_urgency_building_at)"` — verify defaults accessible via new names.

### Step 6b.2 — Update all references to renamed config fields in turn.py

**File:** `ccya/engine/turn.py`

**What:** Find and replace all references to the five old field names:
- `config.scene_pressure_building_at` → `config.thread_urgency_building_at` (appears at line 472)
- `config.scene_pressure_immediate_at` — check if referenced anywhere in turn.py defaults or logic
- `config.scene_pressure_max_age` — check usage; may be used for age-based demotion thresholds
- `config.scene_pressure_deescalate_on_success` → `config.thread_deescalate_on_success` (appears at line 752)
- `config.scene_pressure_immediate_ttl` — check if referenced anywhere

Also update any references in other files: compactor.py, narrate.py, eval/engine_mirror.py. Check for config field usage across the codebase via grep before making changes.

**Why:** Renaming fields without updating all call sites causes NameError at runtime. This step ensures consistency after Step 6b.1 renames the dataclass fields.

**Validation:** Run `rg -n "scene_pressure_building_at|scene_pressure_immediate_at|scene_pressure_max_age|scene_pressure_deescalate_on_success|scene_pressure_immediate_ttl" --glob="*.py" ccya/` — verify zero results (except in build_engine_config() mapping lines which keep old keys for backward compat).

### Step 6b.3 — Migrate _compute_narration_directive from scene_pressure dicts to arc.threads[] scope=scene

**File:** `ccya/engine/turn.py`

**What:** Rewrite `_compute_narration_directive()` (lines 365-446):
1. Change signature: replace `scene_pressure: list[dict[str, Any]]` with `scope_scene_threads: list["ArcThread"]`
2. Replace urgency counting logic:
   - Line 397: `immediate_count = sum(1 for p in scene_pressure if p.get("urgency") == "immediate")` → `immediate_count = sum(1 for t in scope_scene_threads if t.urgency == "urgent")` (note: ArcThread.urgency uses "urgent" not "immediate")
   - Line 426: `building_count = sum(1 for p in scene_pressure if p.get("urgency") == "building")` → `building_count = sum(1 for t in scope_scene_threads if t.urgency == "background")` (note: ArcThread uses "background"/"normal"/"urgent", not "building"/"immediate")
3. Update docstring to reflect unified thread model instead of scene_pressure urgency levels

**Why:** Decision D7 from phase 05 says narration directive computation should derive from unified threads, not legacy pressure dicts. This eliminates the last code path that reads raw `list[dict]` scene_pressure data for computation (state writes were already removed in phase 06). The ArcThread.urgency values are "background"/"normal"/"urgent", mapping to old "building"/"normal"/"immediate".

**Validation:** Read the function after changes to confirm: signature uses `scope_scene_threads: list["ArcThread"]`; urgency counting references ArcThread.urgency field (not dict.get()); docstring updated; no remaining references to scene_pressure parameter name in function body.

### Step 6b.4 — Migrate _compute_pacing_context and update call sites

**File:** `ccya/engine/turn.py`

**What:** Three changes:
1. Update `_compute_pacing_context()` signature (line 452): replace `scene_pressure: list[dict[str, Any]]` with `scope_scene_threads: list["ArcThread"]`
2. Pass derived thread list to `_compute_narration_directive()`: line 467 changes from `scene_pressure=scene_pressure` to `scope_scene_threads=scope_scene_threads` (or whatever the new param name is)
3. Update caller sites at lines ~886 and ~915: replace passing of raw pressure dicts with derived thread lists built via `[t for t in arc.threads if t.scope == "scene" and t.active]`

Check all call sites by searching for `_compute_pacing_context(` to find every invocation location.

**Why:** This completes the migration from scene_pressure→arc.threads[] computation path. The callers now build thread lists from unified state instead of reading legacy pressure dicts, maintaining single source of truth (arc.threads[]) throughout the pipeline.

**Validation:** Run `rg -n "_compute_pacing_context\(" ccya/engine/turn.py` — verify all call sites pass derived ArcThread list. Read each caller to confirm thread derivation logic is correct (`scope == "scene"` filter).

### Step 6b.5 — Update narrate_user.j2 prompt: scene_pressure→threads scope=scene rendering

**File:** `ccya/prompts/narrate_user.j2` (lines 39-41)

**What:** Replace the Jinja block that renders `state.scene.scene_pressure`:
```jinja
{% if state.scene.scene_pressure -%}
...
{% for p in state.scene.scene_pressure %}- [{{ p.urgency | upper }}] {{ p.text }}
```
With equivalent rendering from unified threads: derive urgency labels from ArcThread.urgency values ("background"→BACKGROUND, "normal"→NORMAL, "urgent"→URGENT) and use `arc.threads[]` scope=scene filter instead of state.scene["scene_pressure"].

**Why:** The prompt still references the deleted scene_pressure model. If a campaign has no legacy data (post-migration), this block would produce empty output even when active threads exist. Update to render from unified arc.threads[] for consistency with engine behavior.

**Validation:** Read the file after changes to confirm: Jinja template uses `arc.threads` instead of `state.scene.scene_pressure`; urgency rendering maps ArcThread.urgency values correctly; no syntax errors in template (run `python -c "from jinja2 import Environment, FileSystemLoader; e = Environment(loader=FileSystemLoader('ccya/prompts')); t = e.get_template('narrate_user.j2'); print('ok')"`).

### Step 6b.6 — Update engine_mirror.py: rename threshold constants from urgency-escalation to scope-aware rules

**File:** `ccya/eval/engine_mirror.py` (lines 18-20)

**What:** Replace lines 18-20:
```python
PRESSURE_BUILDING_AT: int = _defaults.scene_pressure_building_at   # background → building
PRESSURE_IMMEDIATE_AT: int = _defaults.scene_pressure_immediate_at  # building → immediate
PRESSURE_MAX_AGE: int = _defaults.scene_pressure_max_age
```
With scope-aware lifecycle rule constants (aligns with Phase 07 Step 7.5 but done here since config fields are renamed):
```python
THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE: bool = True        # scene-scoped threads expire when location changes
THREAD_ARC_DEMOTE_AGE: int = _defaults.thread_urgency_max_age  # arc-scoped threads demote active:True→False after this many turns without last_seen_turn update

# For trace injection into judge prompts — maps from ArcThread.urgency values (background/normal/urgent)
URGENCY_LEVELS: tuple[str, ...] = ("background", "normal", "urgent")
```

Also update `constants_block()` function to inject unified thread lifecycle rules instead of urgency escalation thresholds. Update line 91 (`KNOWN_SEED_PATHS`) from `"scene.scene_pressure"` → `"arc.threads"`.

**Why:** engine_mirror.py is the read-only mirror that eval scenarios and build_trace import constants from. If it hardcodes urgency-escalation thresholds (now renamed to thread_urgency_*), all scenario files would fail on a unified engine even if behavior is correct. This step prepares for Phase 07 rubric updates by having consistent constant names ready.

**Validation:** Run `python -c "from ccya.eval.engine_mirror import THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE, THREAD_ARC_DEMOTE_AGE; print(THREAD_SCENE_EXPIRE_ON_LOCATION_CHANGE); print(THREAD_ARC_DEMOTE_AGE)"` — verify unified lifecycle constants exist and have correct values.

### Step 6b.7 — Final validation: run make check after all changes

**What:** Run `make check && make typecheck` as the final gate for phase 06b (lint + typecheck). Fix any errors from renamed fields or changed function signatures.

**Why:** Config renaming and computation migration touch multiple files with different calling conventions — a single validation run catches cross-module inconsistencies before Phase 07 begins.

---

## Tests to write or update

### Test: `test_config_thread_urgency_fields`
**File:** `ccya/tests/test_engine_config.py` (new test function)  
**What:** Import EngineConfig and verify new field names exist with correct defaults: `thread_urgency_building_at == 3`, `thread_urgency_immediate_at == 5`, `thread_urgency_max_age == 8`, `thread_deescalate_on_success == True`. Verify build_engine_config() accepts old game.yaml keys (`scene_pressure_building_at`) and maps them to new field names.

### Test: `test_compute_narration_directive_from_threads`
**File:** `ccya/tests/test_turn.py` (new test function)  
**What:** Call `_compute_narration_directive()` with a list of ArcThread objects where scope=scene, active=True, varying urgency values. Assert directive output matches expected priority stack: urgent→"Pressure"/"Overwhelm", background→"Tension". Verify no dict-based pressure data is needed.

### Test: `test_compute_pacing_context_passes_threads`
**File:** `ccya/tests/test_turn.py` (new test function)  
**What:** Call `_compute_pacing_context()` with ArcThread objects instead of raw dicts. Assert returned PacingContext has correct directive derived from thread urgency values. Verify no scene_pressure parameter accepted anywhere in call chain.

---

## REPOMAP updates required

Update `docs/repomap.md` with the following changes:
- **EngineConfig section:** Note that config fields renamed from `scene_pressure_*` to `thread_urgency_*` naming convention after this phase completes.
- **Computation functions:** Update `_compute_narration_directive()` and `_compute_pacing_context()` descriptions to note they derive urgency from unified ArcThread objects instead of raw scene_pressure dicts.

(End of file)
