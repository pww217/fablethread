# Arc System Redesign — Implementation Plan

## Purpose

Implement the arc/thread lifecycle redesign per `docs/design/arc-system-design.md`: remove silent Python mechanics, add LLM-driven arc resolution and thread state management, and clean up dead fields across models, engine, state, and prompts.

## Problem Statement

The arc/thread system has no lifecycle (arcs persist forever with stale goals), relies on silent Python mechanics (progress counters, last_seen_turn demotion, urgency decay) that produce state changes without narrative justification, and contains dead fields (`promotes`, `unlock_if`, `pc_drive`, `hidden_truths`, `discovered_truths`, `progress`) that bloat models and prompts.

## Constraints

- No backward compatibility or migration. Full refactor — remove all dead fields.
- All design decisions in `docs/design/arc-system-design.md` are final.
- Each phase independently executable. No phase depends on prior phase context.
- Run `make check` (lint + typecheck) as final step after all phases complete.

## Non-goals

- Thread chaining via explicit references.
- Changes to world state, conditions, or inventory systems.
- Changes to narrator storytelling model beyond removing dead fields.
- Automatic thread culling.

## Solution

Four phases ordered by dependency: (1) models/config/state defaults — foundation for everything else; (2) engine core — replace `_apply_thread_signals()` with `_apply_thread_updates()` and `_apply_arc_resolve()`, update thread creation; (3) state plumbing — delta builder, context builders, narrate, seed, UI; (4) prompt templates — rewrite storytell_system.j2 instructions, update all templates for new field shapes.

## Firm decisions

1. Remove `progress`, `last_seen_turn`, `added_turn`, `urgency_set_turn`, `unlock_if`, `promotes` from `ArcThread`.
2. Remove `pc_drive`, `hidden_truths`, `discovered_truths` from `CampaignArc`.
3. Add `resolution`, `last_thread_created_turn` to `CampaignArc`.
4. Add `resolved_turn` to `ArcThread`.
5. Add `ThreadUpdate`, `ThreadDirective`, `ArcResolution` models.
6. Remove `thread_advance` from `StorytellerResult`, add `thread_update`, `arc_resolve`.
7. Remove `_apply_thread_signals()` entirely. Replace with `_apply_thread_updates()` and `_apply_arc_resolve()`.
8. Remove hard caps (`_ACTIVE_THREAD_CAP`, `_LATENT_THREAD_CAP`) and cooldowns (`thread_creation_cooldown`, `_PROMOTION_COOLDOWN_TURNS`, `_EXPIRE_SILENT_TURNS`).
9. Remove config fields: `thread_completion_threshold`, `thread_urgency_max_age`, `scene_thread_expire_silent_turns`, `track_scene_thread_progress`, `thread_creation_cooldown`.
10. Add config fields: `resolved_arc_ttl` (default 3), `completed_thread_ttl` (default 3).
11. `goal_context` stays on model but removed from all prompt templates.
12. `thematic_question` stays, mutable via `arc_resolve`, fed to both storyteller and narrator.
13. No `arc_update` operation. Arcs are static until resolved.
14. `thread_directives` on `arc_resolve` is opt-in — threads not mentioned carry over as-is.
15. `resolved_arcs` stored on state (not CampaignArc), TTL-pruned in prompts.
16. Key-based dedup and fuzzy merge kept as safety net for thread creation.

## Risks, Ambiguities, and Blockers

- `_compute_threat_ages()` uses `added_turn` or `last_seen_turn` to compute thread age. With both removed, this function needs replacement. The plan replaces it with arc-level `last_thread_created_turn`, which gives a single age for all threads. [QUESTION: is per-thread age needed for threat directives, or is one age for the whole arc acceptable? This is a functional change — threat directives will no longer be per-thread.]
- `_compute_pacing_context()` references `thread_advance` in the consecutive pressure counter logic (turn.py:1461). This needs updating since `thread_advance` is removed. The plan replaces it with `thread_update`.
- `pack.py:98` — `SeedEnvelope.pc_drive` field and `pack.py:337` — `envelope.seed_state.pc.drive` assignment both need removal. Not covered in any step.
- `server/tv.py:235` — special-case rendering for `thread_advance` needs to be replaced with `thread_update` rendering (and new `arc_resolve` rendering).
- `eval/runner.py:283-286` — `thread_advance` assertion logic needs updating.
- `eval/universal_asserts.py:703-751` — `thread_advance` references in consecutive pressure tracking assertions need updating.
- `eval/engine_mirror.py:64` — `storytell.extract` field set includes `"thread_advance"`, needs to be replaced with `"thread_update"` and `"arc_resolve"` added.
- `evals/scenarios/eval_coverage_gap.py` — `thread_advance` references in eval scenario.
- `tests/test_integration.py:82` and `tests/test_smoke.py:34,105` — `thread_advance` in test fixtures. Out of scope per AGENTS.md (tests removed during refactor), but listed for awareness.
- `generate_seed_system.j2:103,108` — TypeScript schema includes `hidden_truths`, `discovered_truths`, `pc_drive` in arc definition. Must be updated.
- `generate_seed_system.j2:39-49,190-198` — arc field guidance includes `hidden_truths`, `pc_drive`, `goal_context` generation instructions. Must be updated.
- `narrate_system.j2:88` — references `pc_drive` and `hidden_truths`. Must be updated.
- `generate_seed_user.j2:35` — references `pc_drive`. Must be updated.
- `pack.py:98`: `SeedEnvelope.pc_drive` field must be removed along with all `pc_drive` wiring in seed.py.

## Status
`open`

## Phases

4 phases covering: (1) model/config/state shape changes; (2) engine core rewrite; (3) state plumbing and context builders; (4) prompt template updates.

---

## Implementation — Phase 1: Models, Config, State Defaults

### Context files to load
- `ccya/models.py` (full)
- `ccya/engine/config.py` (lines 1-103 for EngineConfig dataclass, lines 139-172 for build_engine_config)
- `ccya/state/io.py` (lines 70-95 for default state)

### Detailed steps

#### Step 1.1 — Update ArcThread model

**File:** `ccya/models.py`

**What:** Rewrite `ArcThread` class (lines 28-47). Remove fields: `progress`, `last_seen_turn`, `added_turn`, `urgency_set_turn`, `unlock_if`, `promotes`. Add field: `resolved_turn: int | None = None`. Keep: `id`, `summary`, `scope`, `active`, `urgency`, `tags`, `resolution_state`, `outcome`, `key`.

```python
class ArcThread(BaseModel):
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    active: bool = True
    urgency: Literal["background", "normal", "urgent"] = "normal"
    tags: list[str] = Field(default_factory=list)
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
    key: str | None = None
```

**Why:** Design decisions D1-D5, D20. Removed all silent-mechanic and dead fields. Added `resolved_turn` for TTL tracking.

**Validation:** `python -c "from ccya.models import ArcThread; t = ArcThread(id='test', summary='test'); print(t.model_dump())"`

#### Step 1.2 — Update CampaignArc model

**File:** `ccya/models.py`

**What:** Rewrite `CampaignArc` class (lines 50-59). Remove fields: `hidden_truths`, `discovered_truths`, `pc_drive`. Add fields: `resolution: str | None = None`, `last_thread_created_turn: int = 0`. Keep: `visible_goal`, `thematic_question`, `goal_context`, `threads`, `completed_threads`.

```python
class CampaignArc(BaseModel):
    visible_goal: str = ""
    thematic_question: str = ""
    goal_context: str = ""
    threads: list[ArcThread] = Field(default_factory=list)
    completed_threads: list[ArcThread] = Field(default_factory=list)
    resolution: str | None = None
    last_thread_created_turn: int = 0
```

**Why:** Design decisions D6-D7, D14, D17. Removed dead fields. Added resolution and thread creation tracking.

**Validation:** `python -c "from ccya.models import CampaignArc; a = CampaignArc(); print(a.model_dump())"`

#### Step 1.3 — Add new models to models.py

**File:** `ccya/models.py`

**What:** Add `ThreadUpdate`, `ThreadDirective`, `ArcResolution` classes after `ThreadResolution` (around line 358). These need `from __future__ import annotations` at module top if not already present, since `ThreadDirective` is used in `ArcResolution.thread_directives` which is defined after it.

```python
class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: Literal["background", "normal", "urgent"] | None = None
    summary: str | None = None


class ThreadDirective(BaseModel):
    id: str
    action: Literal["drop", "move_latent"]


class ArcResolution(BaseModel):
    resolution: str
    visible_goal: str
    goal_context: str
    thematic_question: str | None = None
    thread_directives: list[ThreadDirective] = Field(default_factory=list)
```

**Why:** Design decisions D11, D12, D18. New extraction operations for storyteller.

**Validation:** `python -c "from ccya.models import ThreadUpdate, ThreadDirective, ArcResolution; print('OK')"`

#### Step 1.4 — Update StorytellerResult model

**File:** `ccya/models.py`

**What:** Update `StorytellerResult` (lines 383-421). Remove `thread_advance: list[str]`. Add `thread_update: list[ThreadUpdate] = Field(default_factory=list)` and `arc_resolve: ArcResolution | None = None`. Update imports if needed (add `ThreadUpdate`, `ArcResolution` to module-level imports if not already present).

```python
class StorytellerResult(BaseModel):
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    gm_beat: GMBeat | None = None
    thread_resolve: list[ThreadResolution] = Field(default_factory=list)
    thread_add: ArcThread | None = None
    thread_update: list[ThreadUpdate] = Field(default_factory=list)
    arc_resolve: ArcResolution | None = None
    world_state_add: list[WorldStateFact] = Field(default_factory=list)
    world_state_remove: list[str] = Field(default_factory=list)
```

**Why:** Design decisions D10, D11, D12. Replaced `thread_advance` with new operations.

**Validation:** `python -c "from ccya.models import StorytellerResult; r = StorytellerResult(); print(r.model_dump())"`

#### Step 1.5 — Update EngineConfig dataclass

**File:** `ccya/engine/config.py`

**What:** In `EngineConfig` dataclass (around lines 77-102), remove fields: `thread_urgency_max_age`, `track_scene_thread_progress`, `scene_thread_expire_silent_turns`, `thread_completion_threshold`, `thread_creation_cooldown`. Add fields: `resolved_arc_ttl: int = 3`, `completed_thread_ttl: int = 3`.

Keep: `thread_deescalate_on_success`, `avoidance_keywords`, `momentum_floor`, `momentum_ceiling`, `consecutive_pressure_threshold`, `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at`.

**Why:** Design decision D17. All timer-based config fields removed. TTL fields added.

**Validation:** `python -c "from ccya.engine.config import EngineConfig; from dataclasses import fields; print([f.name for f in fields(EngineConfig) if 'thread' in f.name or 'ttl' in f.name])"`

#### Step 1.6 — Update build_engine_config

**File:** `ccya/engine/config.py`

**What:** In `build_engine_config()` (lines 139-172), remove the mapping lines for removed config fields:
- Remove `thread_urgency_max_age=int(game.get("thread_urgency_max_age", 8)),`
- Remove `track_scene_thread_progress=bool(game.get("track_scene_thread_progress", True)),`
- Remove `scene_thread_expire_silent_turns=int(game.get("scene_thread_expire_silent_turns", 5)),`
- Remove `thread_completion_threshold=int(game.get("thread_completion_threshold", 3)),`
- Remove `thread_creation_cooldown=int(game.get("thread_creation_cooldown", 3)),`

Add mapping lines for new fields:
- `resolved_arc_ttl=int(game.get("resolved_arc_ttl", 3)),`
- `completed_thread_ttl=int(game.get("completed_thread_ttl", 3)),`

**Why:** Config builder must match the dataclass shape.

**Validation:** `python -c "from ccya.engine.config import build_engine_config; c = build_engine_config({}); print(c.resolved_arc_ttl, c.completed_thread_ttl)"`

#### Step 1.7 — Update default state

**File:** `ccya/state/io.py`

**What:** Update default arc state (lines 74-81). Remove `hidden_truths`, `discovered_truths`. Add `resolution: None`, `last_thread_created_turn: 0`.

```python
"arc": {
    "visible_goal": "",
    "thematic_question": "",
    "goal_context": "",
    "threads": [],
    "completed_threads": [],
    "resolution": None,
    "last_thread_created_turn": 0,
},
```

Also add `"resolved_arcs": []` to the top-level default state dict (around line 73, after `"arc"`).

**Why:** Default state must match new model shapes. `resolved_arcs` is a state-level field.

**Validation:** `python -c "from ccya.state.io import default_state; s = default_state(); print(s['arc'].keys()); print('resolved_arcs' in s)"`

### Tests to write or update

No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Implementation — Phase 2: Engine Core

### Context files to load
- `ccya/engine/turn.py` (lines 139-526 for constants, _apply_thread_signals, _apply_thread_resolutions; lines 563-662 for _compute_narration_directive; lines 747-771 for _compute_threat_ages; lines 1318-1455 for arc director pipeline and thread creation; lines 1458-1467 for consecutive pressure counter)
- `ccya/state/delta_builder.py` (lines 53-74 for _merge_arc_update)
- `ccya/models.py` (for new model shapes, already updated in Phase 1)

### Detailed steps

#### Step 2.1 — Remove constants and _apply_thread_signals

**File:** `ccya/engine/turn.py`

**What:** Delete the following constants (lines 139-149):
- `_ACTIVE_THREAD_CAP = 3`
- `_LATENT_THREAD_CAP = 4`
- `_EXPIRE_SILENT_TURNS = 5`
- `_PROMOTION_COOLDOWN_TURNS = 3`

Delete the entire `_apply_thread_signals()` function (lines 152-416). This function is replaced by `_apply_thread_updates()`.

**Why:** Design decision D17. No hard caps, no silent mechanics. Function is entirely replaced.

**Validation:** Verify the function is no longer referenced: `rg '_apply_thread_signals' ccya/`

#### Step 2.2 — Write _apply_thread_updates()

**File:** `ccya/engine/turn.py`

**What:** Create new function `_apply_thread_updates(state, storyteller_result) -> CampaignArc | None` at the location where `_apply_thread_signals` was. This function:

1. Validates arc from state, returns None if missing or invalid.
2. If `storyteller_result.thread_update` is empty, return None.
3. For each `ThreadUpdate` in `thread_update`:
   - Find the thread by `id` in `arc.threads`.
   - If not found, log WARNING and skip.
   - Apply the non-None fields (`active`, `urgency`, `summary`) via `model_copy`.
   - If `active` is set to `False`, log the demotion.
   - If `active` is set to `True`, log the reactivation.
4. Return a mutated `CampaignArc` if any update was applied, None otherwise.

The function does NOT enforce caps, cooldowns, or silent timers. It purely applies the storyteller's explicit state changes.

**Why:** Design decision D11. Replaces the old signal-based system with explicit storyteller control.

**Validation:** Create a test state with threads, call the function with a `ThreadUpdate`, verify the thread's state changed.

#### Step 2.3 — Write _apply_arc_resolve()

**File:** `ccya/engine/turn.py`

**What:** Create new function `_apply_arc_resolve(state, storyteller_result, config) -> CampaignArc | None` after `_apply_thread_updates()`. This function:

1. If `storyteller_result.arc_resolve` is None, return None.
2. Validate arc from state. If missing or invalid, log WARNING and return None.
3. Extract `ArcResolution` from the result.
4. Set `resolution` on the current arc.
5. Move the current arc to `state["resolved_arcs"]` (append to list). Set `resolved_turn` on the arc if not already set.
6. Process `thread_directives`:
   - For each directive with `action == "drop"`, remove the thread from `arc.threads`.
   - For each directive with `action == "move_latent"`, set `active = False` on the thread.
   - Threads not mentioned carry over as-is.
7. Create a new `CampaignArc` with:
   - `visible_goal` from `ArcResolution`
   - `goal_context` from `ArcResolution`
   - `thematic_question` from `ArcResolution` if provided, else keep the old arc's value
   - `threads` = surviving threads from step 6
   - `completed_threads` = empty list (or carry over recent completed threads within TTL)
   - `last_thread_created_turn` = current turn
8. Replace `state["arc"]` with the new arc.
9. Return the new `CampaignArc`.

Log at INFO level for arc resolution, WARNING for validation failures.

**Why:** Design decisions D12, D15, D18. Arc lifecycle: resolve, store, create successor.

**Validation:** Create a test state with an arc and threads, call with an `ArcResolution`, verify the old arc is in `resolved_arcs` and the new arc has the correct fields.

#### Step 2.4 — Update _apply_thread_resolutions()

**File:** `ccya/engine/turn.py`

**What:** Update `_apply_thread_resolutions()` (lines 418-526). When moving a thread to `completed_threads`, add `resolved_turn` set to the current turn number. Remove any references to removed fields (`progress`, `last_seen_turn`, `added_turn`, `urgency_set_turn`).

The `model_copy` call at line 479-482 becomes:
```python
updated_thread = thread.model_copy(update={
    "resolution_state": res.resolution_state,
    "outcome": res.outcome,
    "resolved_turn": turn_no,
})
```

**Why:** Design decision D16. TTL tracking for completed thread outcomes.

**Validation:** Verify resolved threads in `completed_threads` have `resolved_turn` set.

#### Step 2.5 — Update thread creation inline code

**File:** `ccya/engine/turn.py`

**What:** Update the thread creation block (lines 1341-1455). Remove:
- Pacing gate check (`_pc.gate == "allow"`) — keep this, it's still valid for pacing
- Cooldown check (`config.thread_creation_cooldown`) — remove entirely
- Active cap check (`active_count >= _ACTIVE_THREAD_CAP`) — remove entirely
- References to `last_seen_turn`, `added_turn`, `urgency_set_turn` in thread creation

Keep:
- Pacing gate check (`_pc is None or _pc.gate == "allow"`)
- Key collision check (exact match)
- Fuzzy auto-merge (≥70% token overlap)
- Scene-scoped thread handling

For new thread creation (the `if not fuzzy_merged` branch), remove the `active_cap` check. The storyteller is trusted to manage thread count. Remove `last_seen_turn` and `urgency_set_turn` from the `model_copy` update. Remove the `added_turn` assignment. Update `last_thread_created_turn` on the arc instead of `meta["last_thread_creation_turn"]`.

The new thread creation becomes:
```python
_updated_t = _new_thread.model_copy()
arc_with_new_thread = _existing_arc.model_copy(
    update={"threads": list(_existing_arc.threads) + [_updated_t],
            "last_thread_created_turn": turn_no_for_add}
)
```

**Why:** Design decisions D3, D17. No cooldowns, no caps. Thread creation tracking moves to arc level.

**Validation:** Verify thread creation still works with key dedup and fuzzy merge, but without cap/cooldown gates.

#### Step 2.6 — Update consecutive pressure counter logic

**File:** `ccya/engine/turn.py`

**What:** Update the consecutive pressure counter block (lines 1458-1467). The current logic references `thread_advance` from the extraction result:

```python
thread_advance = (_extract_result[4].thread_advance) if len(_extract_result) > 4 and _extract_result[4] else []
```

Since `thread_advance` is removed, this logic needs updating. The pressure counter increments when the directive is "Pressure" or "Overwhelm" AND no threads were advanced. Without `thread_advance`, we should use `thread_update` as the proxy — if no `thread_update` was emitted, the pressure counter increments.

Replace the reference to `thread_advance` with checking `thread_update`:
```python
thread_updates = storyteller_result.thread_update if storyteller_result else []
if (directive in ("Pressure", "Overwhelm")) and not thread_updates:
    meta["consecutive_pressure_turns"] = current_pressure + 1
```

**Why:** The `thread_advance` field no longer exists. `thread_update` is the closest proxy for "storyteller engaged with threads this turn."

**Validation:** Verify the pressure counter still increments/decrements correctly.

#### Step 2.7 — Update _compute_threat_ages()

**File:** `ccya/engine/turn.py`

**What:** Update `_compute_threat_ages()` (lines 747-771). The current function uses `added_turn` or `last_seen_turn` to compute per-thread age. Both fields are removed.

[QUESTION: The design removes all per-thread turn tracking. `_compute_threat_ages()` currently provides per-thread ages to the narration directive system (`threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at` — all still in config). Using `arc.last_thread_created_turn` gives all threads the same age, which eliminates per-thread threat differentiation. Two options: (1) Remove `_compute_threat_ages()` entirely and the config fields it feeds, since thread urgency is now storyteller-managed — threat imperatives based on age are a silent mechanic. (2) Keep per-thread age tracking by adding a `created_turn` field to ArcThread. Option (1) aligns with the design's "no silent mechanics" principle. Option (2) preserves threat directives but contradicts the design's removal of per-thread timers.]

If option (1): Remove `_compute_threat_ages()` entirely. Remove `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at` from `EngineConfig`. Remove the `threat_ages` computation and its consumers in `_compute_narration_directive()` and `_compute_pacing_context()`. Remove `threat_ages` from the narrate context builder.

If option (2): Add `created_turn: int | None = None` to `ArcThread` (set at thread creation time). Update `_compute_threat_ages()` to use `created_turn` instead of `added_turn/last_seen_turn`. Keep all threat config fields.

The plan proceeds with **option (1)** — remove threat ages and their config fields, since threat directives are a silent mechanic. If user chooses option (2), the plan needs an additional step to add `created_turn` to ArcThread.

**Remove:**
- `_compute_threat_ages()` function (lines 747-771)
- `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at` from `EngineConfig` dataclass and `build_engine_config()`
- `threat_ages` parameter from `_compute_narration_directive()` signature and body
- `threat_ages` from `_compute_pacing_context()` signature and its call sites
- `threat_ages` from narrate.py context builder

**Why:** Threat imperatives based on thread age are a silent mechanic (the engine decides when a thread is "old enough" to be a threat). With storyteller-managed urgency, this is unnecessary.

**Validation:** `rg 'threat_ages\|threat_pressure_at\|threat_imperative' ccya/engine/turn.py` should return no results.

#### Step 2.8 — Update arc director pipeline in run_turn()

**File:** `ccya/engine/turn.py`

**What:** Update the arc director section in `run_turn()` (lines 1318-1339). Replace the call to `_apply_thread_signals()` with `_apply_thread_updates()`. Add a call to `_apply_arc_resolve()`.

```python
# Arc director: process thread updates and arc resolution
if state.get("arc") and storyteller_result:
    thread_delta = _apply_thread_updates(state, storyteller_result)
    if thread_delta is not None:
        _merge_arc_update(state.setdefault("arc", {}), thread_delta)
        if delta is not None:
            delta = delta.model_copy(update={"arc_update": thread_delta})

    # Process arc resolution (resolves arc + creates successor)
    resolved_arc = _apply_arc_resolve(state, storyteller_result, config)
    if resolved_arc is not None:
        _merge_arc_update(state.setdefault("arc", {}), resolved_arc)
        if delta is not None:
            delta = delta.model_copy(update={"arc_update": resolved_arc})

    # Process thread resolutions (resolved/failed/abandoned -> completed)
    resolved_threads_arc = _apply_thread_resolutions(state, storyteller_result)
    if resolved_threads_arc is not None:
        _merge_arc_update(state.setdefault("arc", {}), resolved_threads_arc)
        if delta is not None:
            delta = delta.model_copy(update={"arc_update": resolved_threads_arc})
```

**Why:** Pipeline integration for new functions. Order matters: thread updates first, then arc resolution, then thread resolutions.

**Validation:** Verify the pipeline calls the new functions in the correct order.

#### Step 2.9 — Update eval files referencing thread_advance

**File:** `ccya/eval/universal_asserts.py`, `ccya/eval/runner.py`

**What:** 

In `universal_asserts.py` (lines 703-751), update `check_consecutive_pressure_tracking()` to reference `thread_update` instead of `thread_advance`. The function checks `storytell_output.get("thread_advance")` — change to `storytell_output.get("thread_update")`. Update all variable names and string references (`has_thread_advance` → `has_thread_update`, etc.).

In `runner.py` (lines 283-286), update the `thread_advance` assertion: change `a.field == "thread_advance"` to `a.field == "thread_update"` and update the corresponding output parsing.

**Why:** `thread_advance` field is removed. All references must point to `thread_update`.

**Validation:** `rg 'thread_advance' ccya/eval/` should return no results.

### Tests to write or update

No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Implementation — Phase 3: State Plumbing

### Context files to load
- `ccya/state/delta_builder.py` (lines 53-74 for _merge_arc_update)
- `ccya/prompts/context.py` (lines 76-139 for ArcThreadSummary, ArcThreadBlock; lines 265-286 for StorytellerBoundary)
- `ccya/engine/narrate.py` (lines 51-90 for arc context builder)
- `ccya/engine/seed.py` (lines 320-337 for arc seeding)
- `ccya/templates/_state_left.html` (lines 45-106 for arc UI display)

### Detailed steps

#### Step 3.1 — Update _merge_arc_update()

**File:** `ccya/state/delta_builder.py`

**What:** Update `_merge_arc_update()` (lines 53-74). Remove handling of: `pc_drive`, `hidden_truths`, `discovered_truths`. Add handling for: `resolution`, `last_thread_created_turn`.

The function should merge:
- `visible_goal` (if non-empty)
- `thematic_question` (if non-empty)
- `resolution` (if non-None)
- `last_thread_created_turn` (if non-zero)
- `threads[]` (full replacement via model_dump)
- `completed_threads[]` (full replacement via model_dump)

Remove the union-merge logic for `hidden_truths` and `discovered_truths`. Remove the `pc_drive` assignment.

**Why:** Design decisions D6, D7. Delta builder must match the new model shape.

**Validation:** `python -c "from ccya.state.delta_builder import _merge_arc_update; from ccya.models import CampaignArc; arc = {}; au = CampaignArc(visible_goal='test'); _merge_arc_update(arc, au); print(arc)"`

#### Step 3.2 — Update ArcThreadSummary

**File:** `ccya/prompts/context.py`

**What:** Update `ArcThreadSummary` (lines 76-88). Remove `last_seen_turn` field. Keep: `id`, `summary`, `scope`, `urgency`, `tags`, `active`.

Update the `from_state()` method on `ArcThreadBlock` (lines 101-139) to remove `last_seen_turn` from all three coercion paths (dict, ArcThreadSummary, ArcThread).

**Why:** Design decision D2. `last_seen_turn` is removed.

**Validation:** `python -c "from ccya.prompts.context import ArcThreadSummary; t = ArcThreadSummary(id='test', summary='test', scope='arc', urgency='normal', active=True); print(t.model_dump())"`

#### Step 3.3 — Update ArcThreadBlock

**File:** `ccya/prompts/context.py`

**What:** Update `ArcThreadBlock` (lines 91-139). Remove fields: `pc_drive`, `discovered_truths`, `hidden_truths`. Keep: `visible_goal`, `thematic_question`, `threads`.

Update `from_state()` to remove references to `pc_drive`, `discovered_truths`, `hidden_truths`.

Also update `StorytellerBoundary` docstring (line 270): remove `pc_drive` from the description of what `current_arc` provides via `_arc.j2`.

**Why:** Design decisions D6, D7. Dead fields removed from context boundary.

**Validation:** `python -c "from ccya.prompts.context import ArcThreadBlock; print(ArcThreadBlock.model_fields.keys())"`

#### Step 3.4 — Update narrate.py arc context builder

**File:** `ccya/engine/narrate.py`

**What:** Update the arc context builder (lines 51-75). Remove from `current_arc_ctx`: `goal_context`, `pc_drive`, `hidden_truths`, `last_seen_turn` from thread dicts, `completed_threads` (or keep completed_threads but TTL-filter them).

Add to `current_arc_ctx`: `resolution` (from arc), `resolved_arc` (from state's `resolved_arcs` list, TTL-filtered).

For threads, remove `last_seen_turn` from the dict comprehension. Filter `completed_threads` by TTL: only include threads where `current_turn - resolved_turn <= config.completed_thread_ttl`.

```python
current_arc_ctx = {
    "visible_goal": arc.get("visible_goal", ""),
    "thematic_question": arc.get("thematic_question", ""),
    "threads": [...],  # active threads only, no last_seen_turn
    "resolution": arc.get("resolution"),
    "resolved_arc": _get_resolved_arc(state, turn_no, config),  # TTL-filtered
    "completed_threads": _filter_completed_threads(arc, turn_no, config),  # TTL-filtered
}
```

**Why:** Design decisions D8, D15, D16, D19. Remove dead fields, add TTL-windowed context.

**Validation:** Verify the context dict has the correct keys and no removed fields.

#### Step 3.5 — Add TTL pruning helpers

**File:** `ccya/engine/narrate.py` (or `ccya/prompts/context.py`)

**What:** Add two helper functions:

1. `_filter_completed_threads(arc, turn_no, config) -> list[dict]`: Filter `completed_threads` to only include threads where `current_turn - resolved_turn <= config.completed_thread_ttl`. Return list of dicts suitable for prompt rendering.

2. `_get_resolved_arc(state, turn_no, config) -> dict | None`: Get the most recently resolved arc from `state["resolved_arcs"]` where `current_turn - resolved_turn <= config.resolved_arc_ttl`. Return dict with `visible_goal`, `resolution`, `goal_context` for prompt rendering.

**Why:** Design decisions D15, D16. TTL-based context windowing.

**Validation:** Create test data with completed threads at various `resolved_turn` values, verify only recent ones are returned.

#### Step 3.6 — Update seed.py and pack.py

**File:** `ccya/engine/seed.py`, `ccya/pack.py`

**What:** 

In `seed.py` (lines 320-337), update the arc seeding block. Remove:
- `pc_drive` wiring (lines 324-325: `envelope.seed_state.arc.pc_drive = envelope.pc_drive`)
- `added_turn` initialization (lines 332-333)
- `urgency_set_turn` initialization (lines 334-335)
- `pc_drive` wiring at lines 336-337: `envelope.seed_state.pc.drive = envelope.pc_drive`

Keep:
- Arc copy from envelope (lines 322-323)
- Active threads set to `active=True` (lines 330-331)

In `pack.py` (line 98), remove `pc_drive: str = ""` from `SeedEnvelope`.

**Why:** Design decisions D6, D3, D4. `pc_drive`, `added_turn`, `urgency_set_turn` are removed.

**Validation:** `python -c "from ccya.pack import SeedEnvelope; e = SeedEnvelope(seed_state=None, opening_narrative='test', actions=['a','b','c','d']); print(e)"` — verify no `pc_drive` field.

#### Step 3.7 — Update server/tv.py extraction display

**File:** `ccya/server/tv.py`

**What:** Update the special-case rendering for extraction fields (lines 234-256). Replace the `thread_advance` case (line 235) with `thread_update` rendering that shows thread ID, field changes, and new values. Add `arc_resolve` rendering.

The `thread_advance` block (lines 235-237) becomes a `thread_update` block that formats thread updates as `"thread_id: active=True, urgency=urgent"` or similar. Add a new `arc_resolve` block that shows the resolution string and new goal.

**Why:** `thread_advance` field is removed. New extraction fields need display.

**Validation:** Run the server and verify extraction display shows `thread_update` and `arc_resolve` correctly.

#### Step 3.8 — Update eval/engine_mirror.py extraction schema

**File:** `ccya/eval/engine_mirror.py`

**What:** Update the `storytell.extract` field set (line 64). Replace `"thread_advance"` with `"thread_update"` and add `"arc_resolve"`.

Current: `"storytell.extract": {"thread_advance", "thread_resolve", "thread_add"},`
New: `"storytell.extract": {"thread_update", "thread_resolve", "thread_add", "arc_resolve"},`

**Why:** Extraction schema must match `StorytellerResult` field names.

**Validation:** `python -c "from ccya.eval.engine_mirror import STORYTELL_FIELDS; print(STORYTELL_FIELDS)"`

#### Step 3.9 — Update _state_left.html

**File:** `ccya/templates/_state_left.html`

**What:** Update the arc display section (lines 45-106). Remove:
- `goal_context` tooltip rendering
- `pc_drive` rendering
- `discovered_truths` rendering

Keep:
- `visible_goal` display
- `thematic_question` display (if present)
- Active threads display
- Completed threads display (as "Log" section)

**Why:** Design decisions D8, D6, D7. Dead fields removed from UI.

**Validation:** Render the template with test data, verify no removed fields appear.

### Tests to write or update

No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Implementation — Phase 4: Prompt Templates

### Context files to load
- `ccya/prompts/sections/_arc.j2` (full)
- `ccya/prompts/sections/_thread_list.j2` (full)
- `ccya/prompts/storytell_system.j2` (full, especially lines 41-67 for thread operations)
- `ccya/prompts/storytell_user.j2` (full)
- `ccya/prompts/narrate_system.j2` (full, especially line 88 for arc guidance)
- `ccya/prompts/narrate_user.j2` (full, especially lines 40-69 for threads and arc)
- `ccya/prompts/generate_seed_system.j2` (lines 39-49 for arc generation guidance)

### Detailed steps

#### Step 4.1 — Update _arc.j2

**File:** `ccya/prompts/sections/_arc.j2`

**What:** Rewrite the template. Remove: `goal_context`, `pc_drive`, `discovered_truths`. Keep: `visible_goal`, `thematic_question`. Add: `resolved_arc` context block (when present).

```jinja
{% if current_arc and current_arc.visible_goal -%}
### Campaign Arc
**Goal:** {{ current_arc.visible_goal }}
{% if current_arc.thematic_question %}
**Thematic question:** {{ current_arc.thematic_question }}
{% endif %}
{%- if current_arc.resolved_arc -%}
### Previous Arc (resolved)
**Goal:** {{ current_arc.resolved_arc.visible_goal }}
**Resolution:** {{ current_arc.resolved_arc.resolution }}
{% endif %}
{%- else -%}
No active campaign arc.
{% endif -%}
```

**Why:** Design decisions D8, D9, D15. Remove dead fields, add resolved arc context.

**Validation:** Render with test data containing `visible_goal`, `thematic_question`, and optionally `resolved_arc`.

#### Step 4.2 — Update _thread_list.j2

**File:** `ccya/prompts/sections/_thread_list.j2`

**What:** Remove `last_seen_turn` rendering. Keep: `id`, `scope` tag, `active`/`latent` marker, `urgency`, `summary`.

```jinja
{% for t in threads %}{% set scope_tag = "[SCENE]" if t.scope == "scene" else "[ARC]" %}- `{{ t.id }}` {{ scope_tag }}{% if not t.active %} (latent){% endif %} [{{ t.urgency | upper }}] {{ t.summary }}
{% endfor -%}
```

**Why:** Design decision D2. `last_seen_turn` is removed.

**Validation:** Render with test threads, verify no "last seen T{n}" appears.

#### Step 4.3 — Rewrite storytell_system.j2 thread/arc instructions

**File:** `ccya/prompts/storytell_system.j2`

**What:** This is the most critical prompt change. Multiple sections need updating:

1. **Lines 10-11** (JSON schema example): Replace `"thread_advance": ["thread_id_1", "thread_id_2"]` with `"thread_update": [{"id": "thread_id", "active": true, "urgency": "urgent"}]` and add `"arc_resolve": {"resolution": "...", "visible_goal": "...", "goal_context": "..."}`.

2. **Lines 41-67** (thread operations guidance): Replace entirely. Remove `thread_advance` section. Add `thread_update` section (change active/latent/urgency/summary). Add `arc_resolve` section. Tighten `thread_add` section (actionable, arc-relevant). Add thread count context and soft cap guidance. Add instruction to prune stale latent threads.

3. **Line 58**: Remove `Use thread_advance if you're advancing progress toward completion; use thread_resolve if the turn ends the tension entirely.`

4. **Line 60**: Update the dedup instruction to reference `thread_update` instead of `thread_advance` for existing threads.

**Why:** Design decisions D10, D11, D12, D22. Complete rewrite of thread/arc operation guidance for the storyteller.

**Validation:** Render the template, verify all new operations are documented and old references removed.

#### Step 4.4 — Update storytell_user.j2

**File:** `ccya/prompts/storytell_user.j2`

**What:** Update the user prompt template. Changes:
- The `{% include "sections/_arc.j2" %}` block will automatically reflect changes from Step 4.1.
- Thread list rendering uses updated `_thread_list.j2` from Step 4.2.
- Add completed threads section with TTL window: show completed threads with their `outcome` and `resolution_state`, but only for threads where `current_turn - resolved_turn <= completed_thread_ttl`.
- Add resolved arc block (if present from context).

**Why:** Design decisions D16, D15. TTL-windowed context for completed threads and resolved arcs.

**Validation:** Render with test data including completed threads and a resolved arc.

#### Step 4.5 — Update narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Remove `pc_drive` and `hidden_truths` references. Keep `thematic_question` guidance. Add instruction that resolved arcs provide narrative continuity — the narrator should be aware of how the previous arc ended and weave that into the prose.

Update the campaign arc context guidance (around line 88): Change `"Your visible goal, thematic question, active threads, and pc_drive are provided in the context below. Use them as narrative guidance — never state the thematic question directly or reveal hidden_truths in prose."` to remove `pc_drive` and `hidden_truths`. The new text should reference `thematic_question` as the narrative lens and `resolved_arc` as continuity context.

**Why:** Design decisions D6, D8, D9. Dead fields removed, thematic question retained, resolved arc context added.

**Validation:** Render the template, verify no dead field references.

#### Step 4.6 — Update narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`

**What:** Update the user prompt template. Changes:
- Remove `goal_context` from the arc context block (it's UI-only, not a narrative signal).
- The `{% include "sections/_arc.j2" %}` block will reflect changes from Step 4.1.
- Thread list uses updated `_thread_list.j2` from Step 4.2.
- Add resolved arc context block (if present).
- Past resolutions section (completed_threads) should show TTL-windowed outcomes.

**Why:** Design decisions D8, D15, D16. Remove dead fields, add TTL context.

**Validation:** Render with test data, verify correct output.

#### Step 4.7 — Update generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Update the seed generation guidance. Multiple changes needed:

1. **Lines 39-49** (arc generation guidance): Remove references to `hidden_truths` and `pc_drive`. Update to match new `CampaignArc` shape: `visible_goal`, `thematic_question`, `goal_context`, `threads`.

2. **Lines 103, 108** (TypeScript schema): Remove `hidden_truths`, `discovered_truths`, `pc_drive` from the arc schema. Replace with new shape: `{visible_goal: string, goal_context: string, thematic_question: string, threads: ArcThread[], completed_threads: ArcThread[], resolution: string | null}`

3. **Lines 190-198** (field guidance): Remove `goal_context` guidance that says to express via `goal_context` (it's still on the model but guidance should clarify it's UI-only). Remove `hidden_truths` and `discovered_truths` guidance. Remove `pc_drive` guidance.

4. **Line 109**: Remove `pc_drive: string` from the top-level seed envelope schema.

**Why:** Design decisions D6, D7, D8. Seed generation must match the new model shape.

**Validation:** Render the template, verify seed guidance matches the new model.

#### Step 4.8 — Update generate_seed_user.j2

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Remove `pc_drive` reference (line 35). The line `{% if overrides.drive_hint %}- pc_drive: {{ overrides.drive_hint }}{% endif %}` should be removed since `pc_drive` is no longer part of `SeedEnvelope`.

**Why:** Design decision D6. `pc_drive` removed from seed envelope.

**Validation:** Render the template with test overrides, verify no `pc_drive` output.

### Tests to write or update

No tests to write (tests are temporarily removed during refactor per AGENTS.md).

---

## Final: Lint and Typecheck

After all four phases are complete, run:

```
make check
```

This runs `make lint` (ruff) + `make typecheck` (mypy). Fix any issues before committing.
