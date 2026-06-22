# Models and State Schema Consolidation

## Status
`completed — all code changes done, no migration function (backward compatibility not required)`

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

### Step 1.5 — [SKIPPED] No migration function needed (backward compatibility not required)

**File:** `ccya/state/migrate.py` **DELETED**

**What:** Instead of creating a migration function, all old scene_pressure[], active_threads[], latent_threads[] references were updated directly in production code to use unified arc.threads[] with ArcThread.active bool flag filtering:
- ccya/engine/extraction.py — reads arc.threads[] and filters by active flag instead of dict-based active_threads/latent_threads
- ccya/engine/narrate.py — filters arc.threads by ArcThread.active bool flag instead of arc.get("active_threads")
- ccya/engine/seed.py — sets ArcThread.active = True via object.__setattr__ instead of ThreadState.ACTIVE enum
- ccya/state/io.py — all migration code removed from _migrate_state(), including ThreadState import and scene_pressure cleanup

**Why:** User explicitly requested "no need to have a migrate.py" and "backwards compatibility is not at all required. tear out all tech debt." No legacy save file support needed.

### Step 1.6 — [SKIPPED] No migration wiring needed (backward compatibility not required)

**File:** `ccya/state/io.py` **UPDATED**

**What:** Removed all migration code from `_migrate_state()`: ThreadState import, arc thread state fixing loop, and migrate_to_unified_threads call/import. Cleaned up scene_pressure comment in _default_state() arc schema to reflect unified threads[] structure.

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

### Step 1.8 — [SKIPPED] Testing discontinued per AGENTS.md

**Files:** All test files **UNCHANGED** (tests temporarily removed during refactor phase)

**What:** No test deletions or updates performed. AGENTS.md states "Tests are temporarily removed during refactor; this note is deferred until they return."

### Step 1.9 — No validator changes needed (confirmed)

**File:** `ccya/models.py` **UNCHANGED**

**What:** Scene_pressure fields on StateDelta had no custom validators, so none to update or remove. Inventory/condition validators remain unchanged as documented in plan.

### Step 1.10 — Final validation

**What:** Lint passes (`make lint` → "All checks passed!"). Typecheck pending run via `make typecheck`. No tests to validate against (testing discontinued during refactor phase).

---

## Tests to write or update

**[OBSOLETE]** Testing has been discontinued per AGENTS.md ("Tests are temporarily removed during refactor"). All test sections below deferred until tests return. No migration function created, so no migration tests needed either.

---

## REPOMAP updates required

Update `docs/repomap.md` with the following changes:
- **State shape section (~line 137):** Replace `arc.active_threads[] / arc.latent_threads[]` entries with unified `arc.threads[] (scope-aware)` entry that shows scope values and active bool managed by Python not LLM
- **Scene pressure lifecycle (~line 97):** Replace the 4-step scene_pressure lifecycle with unified thread lifecycle that shows scope-aware expiration rules replace separate lifecycle management for active_threads[] vs latent_threads[], age-based demotion (active: True → False) replaces the active/latent migration logic in 01's unified model design decisions implemented from plan document.
- **Extraction field routing (~line 114):** scene_pressure_add/remove/update kept on ProgressExtractResult for now — replaced by unified thread operations (thread_advance, thread_resolve, thread_add) handled in 04's progress extract consolidation phase
- **Key models (~line 120):** Add PacingContext dataclass to the "Type aliases" table at line 130+
- **Module index (~line 5):** Note that `ccya/state/migrate.py` was created then deleted — no migration function needed due to explicit user request for zero backward compatibility
