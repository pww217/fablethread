# Cleanup: Remove Stale Code from Narration Simplification Migration

## Status
`completed`

## Phases

1 phase: remove all stale code left over from the narration-simplification migration — dead functions, unused parameters, misleading config keys, and eval references to deprecated field names.

## Issue

The narration-simplification design (merged via phases 01-06) consolidated `scene_pressure[]` into unified `arc.threads[]`, collapsed six pacing signals into `PacingContext`, removed `stakes`/`beat_disposition`/`advanced_threads` from models and prompts, and rewrote the thread lifecycle. However, several pieces of stale code were not cleaned up:

- `_check_floor_relief()` still exists as a separate side-channel function that injects beats independently of `PacingContext.beat_locked`, creating the race condition the design warned about
- The dead `ScenePressure` model remains defined but unused in models.py
- Stale comments on io.py line 79 reference "backward compatibility during transition period" for migration code that was never written and has been axed
- `_narrate_messages()` still accepts an unused `scene_pressure` parameter placed into context but consumed by zero templates
- Config keys use `scene_pressure_*` naming while EngineConfig fields use `thread_urgency_*`, creating a misleading dual vocabulary
- Eval code (`runner.py`, `engine_mirror.py`) references the deprecated `advanced_threads` field name

## Solution

Remove all stale code in one phase. The changes touch four modules: `turn.py` (remove `_check_floor_relief()`, remove call site, wire beat_locked into beat injection), `models.py` (delete dead ScenePressure class), `narrate.py` + `turn.py` (remove unused scene_pressure parameter wiring), and eval code (update field references). After cleanup the engine has a single floor-relief path via PacingContext.beat_locked with no dual mechanisms.

## Firm decisions

1. **No migration code.** The user explicitly axed all backward compatibility — remove stale comments about "backward compatibility during transition period" on io.py line 79.
2. **beat_locked replaces _check_floor_relief entirely.** beat_locked is computed in `_compute_pacing_context()` with a simple check (`momentum <= config.momentum_floor`). After this cleanup, the beat injection happens after apply_delta using beat_locked — no consecutive floor count tracking needed. The simpler check is sufficient because beat_locked already fires during pacing context computation and the beat can be injected post-delta.
3. **Config keys renamed to match EngineConfig.** `scene_pressure_building_at` → `thread_urgency_building_at`, etc. in config.yaml. This eliminates the dual vocabulary.

## Non-goals

- Do NOT update eval rubrics or scenarios (that's a separate open plan: 07-eval-rubrics-and-scenarios.md)
- Do NOT modify `_inject_location_pressure()` — it still produces valid ArcThread-style dicts used by other code paths
- Do NOT touch the `_candidate_to_latent_thread()` function body beyond confirming it is dead code and removing it

## Risks, Ambiguities, and Blockers

1. **beat_locked wiring after apply_delta.** The current beat injection via `_check_floor_relief` happens AFTER `apply_delta()`, meaning momentum has already been updated by the delta application. If we remove that function and wire beat_locked into post-delta beat injection instead, the timing changes slightly — beat_locked was computed with pre-apply-delta momentum but the new injection still happens after apply_delta. This is acceptable because beat_locked's check (`momentum <= config.momentum_floor`) uses the same threshold; the consecutive-turn tracking in `_check_floor_relief` adds precision that the simpler design intentionally dropped.

2. **Config key rename breaks existing save files.** Renaming `scene_pressure_*` keys to `thread_urgency_*` in config.yaml means any game config file on disk with the old keys will stop working. However, since migration/backward compatibility was axed and this is a dev-time config (not per-save), it's acceptable — users must update their config files.

3. **Eval runner field check.** The eval code at `runner.py:283` checks for `advanced_threads` in extraction output. After renaming to `thread_advance`, any existing scenario assertions referencing the old name will fail until 07-eval-rubrics-and-scenarios.md is implemented. This cleanup phase updates the mirror registry and runner field check; scenarios themselves are handled by the separate eval plan.

## Implementation — Phase 1: Remove stale code from narration simplification migration

### Context files to load
- `ccya/engine/turn.py` (full file)
- `ccya/models.py` (lines 430–445)
- `ccya/engine/narrate.py` (lines 35–95)
- `ccya/state/io.py` (lines 72–80)
- `config.yaml` (lines 16–35)
- `ccya/eval/runner.py` (lines 280–290)
- `ccya/eval/engine_mirror.py` (full file)

### Detailed steps

#### Step 1.1 — Remove `_check_floor_relief()` and wire beat_locked into post-delta beat injection

**File:** `ccya/engine/turn.py`

**What:** Delete the entire `_check_floor_relief()` function (lines ~1561–1598) and its call site on line ~1245. Replace with inline logic that checks `pacing_context.beat_locked` after apply_delta completes: if beat_locked is True and no pending_gm_beat exists, inject a breathing_room beat into state.meta (same shape as the old function produced).

The wiring point is immediately after the `apply_delta()` call on line ~1239-1243. The `_pc` variable from `_compute_pacing_context()` is already in scope at that location. Add:
```python
# Inject floor relief beat via PacingContext.beat_locked (replaces _check_floor_relief)
if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
    meta = state.setdefault("meta", {})
    meta["pending_gm_beat"] = {
        "type": "breathing_room",
        "surface_as": "ambient",
        "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
    }
```

**Why:** The design doc says beat_locked subsumes `_check_floor_relief()`. Having both run independently creates the race condition where directive and floor relief can conflict. A single authoritative path eliminates this.

**Validation:** Run `rg -n "_check_floor_relief" ccya/engine/turn.py` — should return no matches. Confirm `_pc.beat_locked` is used in the post-delta block by reading lines ~1239–1250 of turn.py after changes.

#### Step 1.2 — Delete dead `ScenePressure` model from models.py

**File:** `ccya/models.py`

**What:** Remove the entire `class ScenePressure(BaseModel)` definition (lines ~432–437). This class is never imported or used anywhere in production code after migration to unified ArcThread.

Also remove any import of `ScenePressure` from other modules if present (search for imports).

**Why:** Dead code. The model was superseded by the unified `ArcThread` with `scope: Literal["scene", "arc"]`. No production code references it.

**Validation:** Run `rg -n "ScenePressure" ccya/ --include="*.py"` — should return no matches (excluding plan docs and eval trace output). Confirm models.py still passes syntax check via `python3 -c "from ccya.models import ArcThread, CampaignArc; print('OK')"`.

#### Step 1.3 — Remove unused `scene_pressure` parameter from `_narrate_messages()` and its wiring in turn.py

**File:** `ccya/engine/narrate.py`

**What:** 
- Line ~38: remove the parameter `scene_pressure: list[dict[str, Any]] | None = None,` from the function signature
- Line ~91: remove `"scene_pressure": scene_pressure or [],` from the context dict construction

**File:** `ccya/engine/turn.py`

**What:** 
- Line ~1038: remove the argument `scene_pressure=_effective_pressure,` from the `_narrate_messages()` call
- The `_effective_pressure` variable (produced by `_inject_location_pressure()`) is still used elsewhere — do NOT delete it. Only remove the dead wiring into narrate.

**Why:** The parameter is accepted and placed into context but consumed by zero Jinja2 templates. It's dead wiring left over from before the template cleanup in phase 03 of the migration.

**Validation:** Run `rg -n "scene_pressure" ccya/engine/templates/` — should return no matches (confirming nothing consumes it). Confirm `_effective_pressure` is still used by running `rg -n "_effective_pressure" ccya/engine/turn.py`.

#### Step 1.4 — Clean up stale migration comments on io.py line 79

**File:** `ccya/state/io.py`

**What:** Remove the comment on line ~79 that says:
```
# scene_pressure removed from state.yaml schema, models.py StateDelta, apply_delta(), delta.py — migrated to arc.threads[] with scope: scene for backward compatibility during transition period 
```

Replace it with a clean empty line or remove the trailing comment entirely. The adjacent thread on line 77 already documents the unified model adequately.

**Why:** User explicitly axed all migration and backward compatibility. This comment implies migration code exists when it doesn't, creating false expectations for anyone reading the code.

**Validation:** Read io.py lines ~72–85 after changes to confirm no stale "backward compatibility" or "transition period" comments remain on the arc/threads section.

#### Step 1.5 — Rename config keys from `scene_pressure_*` to `thread_urgency_*` in config.yaml

**File:** `config.yaml`

**What:** In the game config block (lines ~24–28), rename:
- `scene_pressure_building_at: 3` → `thread_urgency_building_at: 3`
- `scene_pressure_immediate_at: 5` → `thread_urgency_immediate_at: 5`
- `scene_pressure_immediate_ttl: 8` → `thread_urgency_immediate_ttl: 8`

Also remove the comment on line ~24 that says "Scene pressure urgency escalation thresholds (turns)" and replace with a thread-focused comment.

Note: The config.py loading code already maps these to EngineConfig fields named `thread_urgency_*`, so no changes needed in config.py — it reads from game dict by key name, which will now match the renamed keys.

**Why:** Eliminates dual vocabulary (`scene_pressure_*` in YAML vs `thread_urgency_*` in Python). The engine config object uses thread-urgency-aware names; the YAML should too for consistency and discoverability.

**Validation:** Run `rg -n "scene_pressure" config.yaml` — should return no matches (except possibly comments referencing the old name, which is fine if they explain the rename). Confirm config.py still loads correctly by checking that it reads from `game.get("thread_urgency_building_at", 3)` etc.

#### Step 1.6 — Update eval runner field check and engine mirror registry

**File:** `ccya/eval/runner.py`

**What:** Lines ~283–287: Replace the `advanced_threads` field check with `thread_advance`:
```python
if a.field == "thread_advance":
    output = ((event.get("extraction") or {}).get("progress") or {}).get("output") or {}
    threads = output.get("thread_advance") or []
    passed = a.expected in threads
    detail = f"thread_advance[{a.expected}] {'found' if passed else 'not found'}"
```

**File:** `ccya/eval/engine_mirror.py`

**What:** Line ~55: Replace the KNOWN_ASSERT_FIELDS entry from `"extract.progress": {"advanced_threads"},` to `"extract.progress": {"thread_advance", "thread_resolve", "thread_add"},`. Add all three unified thread operation fields since scenarios may assert on any of them.

**Why:** The field names changed during migration. Eval code referencing old names would produce false-negative assertion failures and confuse the eval mirror validation.

**Validation:** Run `rg -n "advanced_threads" ccya/eval/ --include="*.py"` — should return no matches (excluding plan docs). Confirm engine_mirror.py's KNOWN_ASSERT_FIELDS now includes all three thread operation field names.

### Tests to write or update

No tests are written during this phase per AGENTS.md guidance that tests are temporarily removed during refactor. The `make check` command will validate syntax and type correctness.

### REPOMAP updates required

- If a repomap file exists in the touched modules' directories, verify it reflects:
  - `_check_floor_relief()` no longer listed as an exported/used function in turn.py
  - `ScenePressure` removed from models.py exports
  - `_narrate_messages()` signature updated (no scene_pressure parameter)
