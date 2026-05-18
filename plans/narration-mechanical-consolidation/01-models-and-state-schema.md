# Models and State Schema Consolidation

## Status
`open`

## Phases

Seven phases consolidating two redundant tension systems (scene_pressure[] + arc.active_threads/latent_threads) into one unified ArcThread model with scope-aware Python management. Phase 01 defines core types and migrates schema; phase 02 implements PacingContext computation in turn.py orchestrator; phase 03 updates Narrate prompt to consume PacingContext directive+beat_hint; phases 04-05 consolidate Progress Extract prompts, replace scene_pressure/advanced_threads/candidate_opportunity with unified thread operations (thread_advance/thread_resolve/thread_add), and wire delta application for arc.threads[] scope-aware lifecycle management; phase 06 validates no orphaned references to removed primitives remain in production code.

## Issue

Two redundant tension systems (`scene_pressure[]` + `arc.active_threads[]/latent_threads[]`) with separate schemas, lifecycles, and LLM instruction sets double the prompt complexity in Progress Extract. Pacing signals are scattered across 3+ functions with implicit cross-talk instead of a single explicit interface. Stakes from Rules is redundant noise in Progress prompts. Beat_disposition output field encodes information Python already has access to directly from state mutations.

## Solution (North Star)

All story tension converges into one unified model: `ArcThread` on `state.arc.threads[]`. Every thread has a scope (`scene` or `arc`) and an `active: bool` managed by Python age rules, not the LLM. All pacing decisions collapse into a single struct: `PacingContext`. The engine makes authoritative pacing choices in one place instead of 3+ scattered functions fighting over what tone to set on any given turn. Stakes removed from IntentEnvelope — band + verb/target provide sufficient failure cost context without free-text noise. Beat_disposition removed from ProgressExtractResult — Python infers it directly from state mutations.

## Firm decisions
1. Thread scope is exactly 2 values: `"scene"` (short-lived, expires on scene change) and `"arc"` (persistent across scenes). No third scope for now.
2. Python manages thread `active: bool` flag based on age rules — LLM does not write it directly.
3. Stakes removal relies on band + verb/target from Rules providing sufficient failure cost context without free-text stakes string; edge cases handled by prose reading in Progress step, not Narrate or Rules.

## Non-goals
- Prompt template changes (handled in 03/04)
- Engine integration for PacingContext computation (handled in 02)
- Delta application logic updates (handled in 05)

## Design Decisions Implemented From Plan Document
This phase implements the following decisions from `plans/narration-simplification-design.md`:
1. Core Change: Unified ArcThread (replaces ScenePressure) — scope field, active bool managed by Python not LLM
2. Remove scene_pressure[] → merge into unified arc.threads[] with scope: scene
3. Remove active_threads/latent_threads split → replace with active: bool on unified thread
4. New unified thread model shape (ArcThread dataclass at models.py)
5. PacingContext struct definition (PacingContext dataclass in turn.py or engine/)
6. Migration Notes for State Files — 1:1 mapping of scene_pressure[] entries to ArcThread(scope=scene), active_threads[] → ArcThread(scope=arc, active=True), latent_threads[] → ArcThread(scope=arc, active=False)
7. Remove stakes (firm decision) from IntentEnvelope in models.py

## Risks, Ambiguities, and Blockers
- **Ambiguity:** Migration function needs to handle edge cases where a thread exists in both `scene_pressure[]` and `active_threads[]` with the same id — should it merge or overwrite? Default: scene_pressure entry wins (it's more recent by definition).
- **Risk:** Existing tests reference ScenePressure, IntentEnvelope.stakes, BeatDisposition fields directly. All test assertions need updating to match new schema. Delete tests for removed primitives rather than retrofitting them.

## Dependencies
None — first in chain. Every subsequent plan depends on these types existing before importing or using them.

---

## Implementation Steps

### Step 1.0 — Define unified ArcThread model (models.py)

**File:** `ccya/models.py`

**What:** Replace the current `ArcThread` class (line 52-63) with a unified shape that has a `scope: Literal["scene", "arc"]` field and an `active: bool = True` flag instead of `state: ThreadState`. The old fields (`unlock_if`, `promotes`) are preserved because the engine handles them directly on thread_resolve/advance.

**Why:** This is the foundation type that 02-05 all depend on importing. It replaces both ScenePressure (via scope=scene) and ArcThread (via scope=arc). The ThreadState enum becomes unused for arc threads but may still be referenced by legacy code in 01's migration path — see Step 1.3.

**Code Snippet:**
```python
class ArcThread(BaseModel):
 id: str
 summary: str
 scope: Literal["scene", "arc"] # replaces scene_pressure + arc threads split
 active: bool = True # False = dormant/latent; set by Python, not LLM
 urgency: Literal["background", "normal", "urgent"] = "normal" # maps from ThreadState urgency
 tags: list[str] = Field(default_factory=list)
 progress: int = 0 # incremented by thread_advance (LLM writes this on advance)
 last_seen_turn: int | None = None # for age-based active/latent demotion in Python
 added_turn: int | None = None # Python-managed lifecycle tracking

 # Fields from old ArcThread that are preserved — engine handles these directly on resolve/advance:
 unlock_if: str | None = None
 promotes: list[str] = Field(default_factory=list)
```

**Validation:** Run `python -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='t', scope='scene'); print(t.model_dump())"` — verify it serializes correctly with all fields.

### Step 1.1 — Define PacingContext dataclass (turn.py)

**File:** `ccya/engine/turn.py`

**What:** Add a new `PacingContext` dataclass at the top of turn.py (after imports, before existing functions). This struct consolidates all pacing signals that were previously scattered across 3+ functions. It will be returned by `_compute_pacing_context()` in phase 02 — for now we just define the type so 01's scope is complete and 02 can import it without circular deps issues.

**Why:** PacingContext is the interface boundary that 02 creates, 03 consumes (directive+beat_hint), 04 consumes (full struct). Defining it in 01 ensures all phases reference the same type definition rather than each defining their own version.

**Code Snippet:**
```python
@dataclass
class PacingContext:
 """Consolidated pacing decision for Narrate and Progress steps."""
 directive: str # "Breathe" | "Pressure" | "MoveOn" | "Escalate" | ""
 beat_hint: str | None # suggested gm_beat type, or None (sent to Narrator when a beat is pending)
 beat_locked: bool # True: floor relief fired — Progress MUST emit breathing_room beat and gate is force-closed
 gate: Literal["block_add", "block_escalate", "allow"] # Progress may only add threads when allow
 summary: str # human-readable log string, never sent to LLM

 @staticmethod
 def neutral() -> PacingContext:
 """Default pacing context for turns without special conditions."""
 return PacingContext(directive="", beat_hint=None, beat_locked=False, gate="allow", summary="neutral")
```

**Validation:** Run `python -c "from ccya.engine.turn import PacingContext; pc = PacingContext.neutral(); print(pc.directive)"` — verify it instantiates without errors.

### Step 1.2 — Remove stakes from IntentEnvelope (models.py)

**File:** `ccya/models.py`

**What:** Delete the `stakes: str = ""` field from `IntentEnvelope` at line 134. The model becomes:
```python
class IntentEnvelope(BaseModel):
 intent: str = Field(default="", max_length=200)
 intent_verb: str = Field(default="act", max_length=24)
 target: str = ""
 check: RulesCheck = Field(default_factory=RulesCheck)
```

**Why:** Stakes is a free-text string from the Rules LLM describing what's at risk. It flows into Progress to help calibrate failure cost, but narration already encodes the outcome — if the band was FAIL, the narrator wrote the failure. Band + verb/target provide sufficient failure cost context without free-text noise (confirmed firm decision in discussions).

**Validation:** Run `python -c "from ccya.models import IntentEnvelope; e = IntentEnvelope(intent='test'); print(e.model_dump())"` — verify it serializes without a stakes key. Also run `grep -r '\.stakes' ccya/` to find any direct attribute access that will break (will be fixed in 03+04).

### Step 1.3 — Remove beat_disposition from ProgressExtractResult (models.py)

**File:** `ccya/models.py`

**What:** Delete the `beat_disposition: Literal["consume", "carry", "replace"] = "consume"` field at line 500 of `ProgressExtractResult`. The model becomes:
```python
class ProgressExtractResult(BaseModel):
 recent_events_add: list[RecentEvent] = Field(default_factory=list)
 recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
 recent_events_remove: list[str] = Field(default_factory=list)
 actions: list[str] = Field(default_factory=list)
 outcome_summary: str = ""
 gm_beat: GMBeat | None = None
 scene_pressure_add: list[ScenePressure] = Field(default_factory=list) # REMOVED in 04's unified operations — keep for now, removed when 04 runs
 scene_pressure_remove: list[str] = Field(default_factory=list) # same note
 scene_pressure_update: list[ScenePressure] = Field(default_factory=list) # same note
 advanced_threads: list[str] = Field(default_factory=list) # REMOVED in 04's unified operations — keep for now, removed when 04 runs
 candidate_opportunity: str | None = None # REMOVED in 04's unified operations — keep for now, removed when 04 runs

 @model_validator(mode="after")
 def _nullify_invalid_gm_beat(self) -> "ProgressExtractResult":
 if self.gm_beat is not None:
 if not self.gm_beat.instruction or not self.gm_beat.type:
 self.gm_beat = None
 return self

 @field_validator("actions", mode="before") #... unchanged
```

**Why:** Beat_disposition encodes information Python already has from state mutations (gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat). No LLM output field needed for information the engine already has access to directly.

Note: scene_pressure_add/remove/update, advanced_threads, candidate_opportunity are NOT removed here — they will be replaced by unified operations in 04's Progress Extract consolidation phase. We keep them in models.py now because 03+04 implement that change together with prompt updates. Removing the fields prematurely would break 02 (which needs PacingContext to exist before 04 can replace these outputs).

**Validation:** Run `python -c "from ccya.models import ProgressExtractResult; r = ProgressExtractResult(); print(r.model_dump())"` — verify it serializes without a beat_disposition key. Also run `grep -r 'beat_disposition' ccya/` to find direct attribute access that will break (will be fixed in 05 when turn.py's beat lifecycle handling at line 920 is updated).

### Step 1.4 — Remove scene_pressure fields from StateDelta (models.py)

**File:** `ccya/models.py`

**What:** Delete the three scene_pressure fields from `StateDelta` at lines 274-276:
```python
scene_pressure_add: list[ScenePressure] = Field(default_factory=list) # REMOVED — migrated to unified arc.threads[] with scope: scene in 01's unified model
scene_pressure_remove: list[str] = Field(default_factory=list) # same note
scene_pressure_update: list[ScenePressure] = Field(default_factory=list) # same note
```

**Why:** These fields are migrated to `arc.threads[]` with scope: scene in the unified ArcThread model (Step 1.0). The state mutation layer will handle thread operations directly instead of separate pressure operations (handled in 05's delta application phase).

Note: ScenePressure class itself is NOT deleted here — it may still be referenced by migration code or legacy save file handling that runs before the unified schema takes effect. It can be removed after 06 validates no references remain.

**Validation:** Run `python -c "from ccya.models import StateDelta; d = StateDelta(); print(d.model_dump())"` — verify it serializes without scene_pressure keys. Also run `grep -r 'scene_pressure_add\|scene_pressure_remove\|scene_pressure_update' ccya/` to find direct attribute access that will break (will be fixed in 05 when turn.py's pressure purge/expire logic at lines 949-972 is updated).

### Step 1.5 — Create migration function (ccya/state/migrate.py)

**File:** `ccya/state/migrate.py` (new file)

**What:** Create a standalone Python module with the `_migrate_to_unified_threads()` function that merges existing save file lists on load:
```python
"""State migration for unified ArcThread model."""

from __future__ import annotations

import logging
from typing import Any

_log = logging.getLogger(__name__)

def migrate_to_unified_threads(state: dict[str, Any]) -> bool:
 """Merge scene_pressure[], active_threads[], latent_threads[] into unified arc.threads[].

 Returns True if migration was performed (old keys detected), False otherwise.
 Called from load_state() in state/io.py after _migrate_state().
 """
 needs_migration = False

 # 1. Migrate scene_pressure[] → ArcThread(scope=scene, active=True)
 pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
 if pressures:
 needs_migration = True
 for p in pressures:
 if not isinstance(p, dict):
 continue
 urgency_str = p.get("urgency", "background")
 urgency_map = {
 "immediate": "urgent",
 "building": "normal", # escalation handled by Python age rules now
 "background": "background",
 }
 arc_thread = {
 "id": str(p.get("id", "")),
 "summary": p.get("text", ""), # text → summary mapping from migration notes in design doc
 "scope": "scene",
 "active": True,
 "urgency": urgency_map.get(urgency_str, "normal"),
 "tags": [], # tags preserved if present on pressure entry (unlikely)
 "progress": 0, # scene pressures don't have progress counter in old model; Python manages lifecycle via age rules instead
 "last_seen_turn": None, # set by engine on first turn seen
 "added_turn": p.get("turn_added"), # for age-based demotion tracking
 }
 state.setdefault("arc", {}).setdefault("threads", []).append(arc_thread)

 # 2. Migrate active_threads[] → ArcThread(scope=arc, active=True)
 arc = state.setdefault("arc", {})
 old_active = list(arc.get("active_threads") or [])
 if old_active:
 needs_migration = True
 for t in old_active:
 if not isinstance(t, dict):
 continue
 urgency_str = t.get("urgency", "normal") # urgency preserved from old ArcThread (was a string)
 arc_thread = {k: v for k, v in t.items() if k not in ("state",)} # drop state field — Python manages active bool now
 arc_thread["scope"] = "arc"
 arc_thread["active"] = True # was ACTIVE → always true on migration
 arc_thread.setdefault("urgency", urgency_str) # preserve existing urgency if present after dropping state key
 for t in old_active: # second pass to set fields that were dropped (unlock_if, promotes preserved from original dict)
 tid = str(t.get("id"))
 for unified in arc["threads"]: # find matching thread by id — migration notes say preserve existing fields including unlock_if and promotes handled directly by engine on resolve/advance
 if unified.get("id") == tid:
 break # already set from dict copy above

 # 3. Migrate latent_threads[] → ArcThread(scope=arc, active=False)
 old_latent = list(arc.get("latent_threads") or [])
 if old_latent:
 needs_migration = True
 for t in old_latent:
 if not isinstance(t, dict):
 continue
 urgency_str = t.get("urgency", "normal") # urgency preserved from old ArcThread (was a string)
 arc_thread = {k: v for k, v in t.items() if k not in ("state",)} # drop state field — Python manages active bool now
 arc_thread["scope"] = "arc"
 arc_thread["active"] = False # was LATENT → always false on migration
 arc_thread.setdefault("urgency", urgency_str) # preserve existing urgency if present after dropping state key

 # 4. Write merged list to state.arc.threads[] (already appended above in steps 1-3)

 # 5. Remove old keys — clean up after merging into unified format for backward compatibility during transition period
 if needs_migration:
 scene = state.get("scene") or {}
 scene.pop("scene_pressure", None) # removed from state.yaml schema, models.py StateDelta, apply_delta(), delta.py in 01's unified model migration notes

 arc_keys_to_remove = ["active_threads", "latent_threads"] # migrate to unified arc.threads[] with scope: scene for active/latent split removal
 for key in arc_keys_to_remove:
 if key in arc:
 del arc[key] # replaced by unified arc.threads[] with active: bool on unified thread

 return needs_migration
```

**Why:** Existing save files will have `state.scene.scene_pressure[]` and `state.arc.active_threads[]` / `state.arc.latent_threads[]`. This migration function runs on load (called from `_migrate_state()` in state/io.py) so 05's delta application logic never sees unmigrated format at runtime after 01 is applied. The 1:1 mapping follows the design doc notes exactly: scene_pressure entries become ArcThread(scope=scene), active_threads become ArcThread(scope=arc, active=True), latent_threads become ArcThread(scope=arc, active=False). Existing fields (unlock_if, promotes) are preserved because the engine handles them directly on thread_resolve/advance.

**Validation:** Create a test fixture YAML with scene_pressure[], active_threads[], and latent_threads[] populated with realistic data (urgency levels: immediate/building/background for pressures; turn_added timestamps for age tracking). Load it via `load_state()` — verify that after migration, state.arc.threads[] contains the correct unified entries with proper scope values, no old keys remain in the dict, and urgency mapping is correct (immediate→urgent, building→normal, background→background).

### Step 1.6 — Wire migration into load_state (state/io.py)

**File:** `ccya/state/io.py`

**What:** Call `_migrate_to_unified_threads()` at the end of `_migrate_state()`, after all existing migrations complete:
```python
# At end of _migrate_state(), after ThreadState fix block (~line 150):
 # Migrate to unified ArcThread threads (Phase 01)
 from ccya.state.migrate import migrate_to_unified_threads

 if migrate_to_unified_threads(state): # migration notes for state files executed on load in 01's unified model — migrate scene_pressure[] entries to ArcThread(scope=scene), active_threads[] → ArcThread(scope=arc, active=True), latent_threads[] → ArcThread(scope=arc, active=False)
 _log.info("state: migrated to unified arc.threads[] (scope-aware)") # scope-aware expiration rules replace separate lifecycle management for active_threads[] vs latent_threads[], age-based demotion (active: True → False) replaces the active/latent migration logic in 01's unified model design decisions implemented from plan document
```

**Why:** This ensures every state file loaded after 01 runs gets migrated on-the-fly. The 05 delta application phase never sees unmigrated format at runtime because 06 validates that all production code references the unified schema

**Validation:** Load a state file with old keys — verify `_migrate_state()` calls `migrate_to_unified_threads()`, which returns True and removes scene_pressure, active_threads, latent_threads from the dict after creating unified arc.threads[]. Also run `python -c "from ccya.state.io import load_state; s = load_state(Path('test_save_dir')); print(s['arc'].keys())"` — verify 'threads' key exists in arc dict on a migrated state file (no active_threads or latent_threads keys).

### Step 1.7 — Update _default_state() for unified schema (state/io.py)

**File:** `ccya/state/io.py`

**What:** Replace the old arc shape (`"arc": {}`) with the new unified format in `_default_state()` at line 72:
```python
 "arc": {
 "visible_goal": "",
 "thematic_question": "",
 "hidden_truths": [],
 "discovered_truths": [],
 "threads": [], # unified arc.threads[] replaces active_threads/latent_threads split — scope-aware expiration rules replace separate lifecycle management for active_threads vs latent_threads, age-based demotion (active: True → False) replaces the active/latent migration logic in design decisions implemented from plan document
 "completed_threads": [],
 }, # scene_pressure removed from state.yaml schema, models.py StateDelta, apply_delta(), delta.py — migrated to arc.threads[] with scope: scene for backward compatibility during transition period 
```

**Why:** New games created from scratch need the unified schema immediately, not just migrated save files. The `scene_pressure: []` key is removed because it's been migrated to arc.threads[] with scope: scene (confirmed 01 migration notes for state files executed on load in 01's unified model).

**Validation:** Run `python -c "from ccya.state.io import _default_state; s = _default_state(); print('scene_pressure' not in s['scene']); print('threads' in s['arc'])"` — verify scene_pressure key is absent from scene dict and threads key exists in arc dict on a fresh state file (no active_threads or latent_threads keys).

### Step 1.8 — Delete tests for removed primitives (test files)

**Files:** All test files that reference `ScenePressure`, `IntentEnvelope.stakes`, `ProgressExtractResult.beat_disposition`. Run `grep -r 'stakes\|beat_disposition' ccya/tests/` to find them all, then delete the entire test file or remove the specific test functions that assert on removed fields. Do not retrofit tests — if a primitive is deleted in 01's unified model , its corresponding test should be deleted too, not adapted to pass on the new schema.

**What:** Delete tests for:
- `ScenePressure` model (if a standalone test file exists) — replaced by unified ArcThread with scope field in 01's unified model design decisions implemented from plan document
- `IntentEnvelope.stakes` tests — stakes removed from IntentEnvelope in 01's unified model confirmed firm decision that band + verb/target provide sufficient failure cost context without free-text noise
- `ProgressExtractResult.beat_disposition` tests — beat_disposition removed from ProgressExtractResult because Python infers it directly from state mutations (gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat)

**Why:** AGENTS.md says "one source of truth per concept" and "remove dead code immediately." Tests that assert on deleted primitives are dead code — they don't validate anything useful after 01's unified model is applied

**Validation:** After deletion, `make check && make test` should pass without errors related to removed fields. If a test file contains BOTH relevant and irrelevant tests, keep the relevant ones — only delete the specific functions that assert on 01's unified model primitives.

### Step 1.9 — Update StateDelta field validators for removed scene_pressure fields (models.py)

**File:** `ccya/models.py`

**What:** The `_coerce_inventory_remove`, `_coerce_condition_add`, and `_coerce_condition_remove` validators on StateDelta are unchanged — they validate inventory/condition operations that still exist. No validator changes needed in 01's unified model because scene_pressure fields were removed without custom validators on them (they used default_factory=list).

**Why:** Explicit note that no validator changes are needed — prevents implementer from wasting time retrofitting validators for fields that never had custom validation logic. The 05 delta application phase will handle unified thread operations directly instead of separate pressure operations

**Validation:** Run `python -c "from ccya.models import StateDelta; d = StateDelta(scene_pressure_add=[{'id': 'x'}]); print(d.scene_pressure_add)"` — verify that scene_pressure fields are truly removed from the model. If a KeyError is raised when trying to set a removed field, the removal worked correctly.

### Step 1.10 — Final validation for 01 (make check && make test)

**What:** Run `make check && make test` as the final gate for 01's unified model implementation. All tests must pass before proceeding to 02.

**Why:** 02 depends on PacingContext type existing for import without circular deps issues, so 01's unified model must be complete and passing before 03+04 implement their prompt changes.

**Validation:** `make check && make test` passes with zero failures. If any failure is related to a removed primitive , that's a 01 issue — fix it here, don't defer to 02-05.

---

## Tests to write or update

### Test: `test_migrate_to_unified_threads_scene_pressure`
**File:** `ccya/tests/test_state.py` (new test function)
**What:** Create a state dict with `scene_pressure=[{"id": "sp1", "text": "threat", "urgency": "immediate", "turn_added": 5}]`. Call `_migrate_to_unified_threads(state)` directly. Assert that:
- `state["arc"]["threads"]` contains exactly one entry with id="sp1", scope="scene", active=True, urgency="urgent" (matching urgency_map in migrate.py)
- `state["scene"]["scene_pressure"]` no longer exists (key removed)

### Test: `test_migrate_to_unified_threads_active_latent_split`
**File:** `ccya/tests/test_state.py` (new test function)
**What:** Create a state dict with arc containing `active_threads=[{"id": "at1", "urgency": "normal"}]` and `latent_threads=[{"id": "lt1", "urgency": "background"}]`. Call `_migrate_to_unified_threads(state)` directly. Assert that:
- `state["arc"]["threads"]` contains two entries: at1 (scope="arc", active=True) and lt1 (scope="arc", active=False)
- `state["arc"]["active_threads"]` and `state["arc"]["latent_threads"]` keys are removed.

### Test: `test_intent_envelope_no_stakes_field`
**File:** `ccya/tests/test_models.py` (new test function)
**What:** Create an IntentEnvelope with just intent and target fields. Assert that the resulting model has NO "stakes" key when serialized via `.model_dump()`. Also assert that creating it without a stakes argument does not raise a TypeError

### Test: `test_progress_extract_result_no_beat_disposition_field`
**File:** `ccya/tests/test_models.py` (new test function)
**What:** Create a ProgressExtractResult with just recent_events_add and actions fields. Assert that the resulting model has NO "beat_disposition" key when serialized via `.model_dump()`. Also assert that creating it without a beat_disposition argument does not raise a TypeError

### Test: `test_state_delta_no_scene_pressure_fields`
**File:** `ccya/tests/test_models.py` (new test function)
**What:** Create a StateDelta with just inventory_add and location_change fields. Assert that the resulting model has NO "scene_pressure_add", "scene_pressure_remove", or "scene_pressure_update" keys when serialized via `.model_dump()`. Also assert that creating it without scene_pressure arguments does not raise a TypeError

### Test: `test_default_state_has_unified_arc_schema`
**File:** `ccya/tests/test_io.py` (new test function)
**What:** Call `_default_state()` directly. Assert that:
- `"scene_pressure"` key does NOT exist in the scene dict
- `"threads"` key EXISTS in the arc dict with an empty list value.

### Test: `test_pacing_context_neutral_factory`
**File:** `ccya/tests/test_models.py` (new test function)
**What:** Import PacingContext from turn.py and call `.neutral()`. Assert that the resulting object has directive="", beat_hint=None, beat_locked=False, gate="allow", summary="neutral"

### Test: `test_arc_thread_unified_model_serialization`
**File:** `ccya/tests/test_models.py` (new test function)
**What:** Create an ArcThread with scope="scene", active=True, urgency="urgent". Assert that the resulting model serializes correctly via `.model_dump()` and includes all expected fields: id, summary, scope, active, urgency, tags, progress, last_seen_turn, added_turn

---

## REPOMAP updates required

Update `docs/repomap.md` with the following changes:
- **State shape section (~line 137):** Replace `arc.active_threads[] / arc.latent_threads[]` entries with unified `arc.threads[] (scope-aware)` entry that shows scope values and active bool managed by Python not LLM
- **Scene pressure lifecycle (~line 97):** Replace the 4-step scene_pressure lifecycle with unified thread lifecycle that shows scope-aware expiration rules replace separate lifecycle management for active_threads[] vs latent_threads[], age-based demotion (active: True → False) replaces the active/latent migration logic in 01's unified model design decisions implemented from plan document.
- **Extraction field routing (~line 114):** Remove scene_pressure_add/remove/update from ProgressExtractResult fields — replaced by unified thread operations (thread_advance, thread_resolve, thread_add) handled in 04's progress extract consolidation phase
- **Key models (~line 120):** Add PacingContext dataclass to the "Type aliases" table at line 130+
- **Module index (~line 5):** Note that `ccya/state/migrate.py` is a new file for unified ArcThread migration on state load
