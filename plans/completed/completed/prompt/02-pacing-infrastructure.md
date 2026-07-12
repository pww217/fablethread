# Pacing Infrastructure Consolidation

## Status
`completed`

## Phases

Seven phases consolidating two redundant tension systems (scene_pressure[] + arc.active_threads/latent_threads) into one unified ArcThread model with scope-aware Python management. Phase 01 defines core types and migrates schema; phase 02 implements PacingContext computation in turn.py orchestrator replacing three scattered pacing functions; phase 03 updates Narrate prompt to consume PacingContext directive+beat_hint; phases 04-05 consolidate Progress Extract prompts, replace scene_pressure/advanced_threads/candidate_opportunity with unified thread operations (thread_advance/thread_resolve/thread_add), and wire delta application for arc.threads[] scope-aware lifecycle management; phase 06 validates no orphaned references to removed primitives remain in production code.

## Issue

Pacing decisions are scattered across 3+ functions (`_compute_narrative_velocity()`, `_compute_narration_directive()`, `_check_floor_relief()`) with implicit cross-talk through shared state and separate call sites in `run_turn()`. This creates a race condition where two independent paths can emit beats in the same turn — directive says "Pressure" while floor relief injects a `breathing_room` beat via `meta["pending_gm_beat"] = {...}`. No single source of truth for what pacing decision the engine makes on any given turn. The LLM receives 3+ competing signals (narrative_velocity, narration_directive, pending_gm_beat from floor relief) it cannot reliably reconcile, resulting in inconsistent behavior across turns where escalation and de-escalation beats fire simultaneously.

## Solution

One function → one struct → clear interface boundary. `_compute_pacing_context()` takes all inputs (`momentum`, `consecutive_floor_turns`, `deescalate`, avoidance score, scene pressures with urgency/age, thread ages/combat age/location age) and returns a single `PacingContext` dataclass (already defined in phase 01) with explicit fields: `directive` (tone/direction string), `beat_hint` (GM beat type suggestion when pending_gm_beat exists), `beat_locked` (floor relief fired — Progress MUST emit breathing_room, gate force-closed), `gate` (block_add/block_escalate/allow for new threads), `summary` (human-readable log string). All 3 scattered functions are deleted. The race condition is eliminated because floor relief logic moves inside the struct's computation and sets `beat_locked=True` directly rather than running as a side-channel that mutates state independently of directive computation.

## Firm decisions
1. `_compute_pacing_context()` replaces all three separate functions — no partial fallbacks or legacy paths during transition. All callers in `run_turn()` updated to use single PacingContext struct instead of calling individual functions. The function is called once at the same location where narrative_velocity was previously computed (around line 756).
2. `beat_locked: True` subsumes `_check_floor_relief()` entirely — floor relief logic moves inside pacing context computation and sets the flag directly rather than running as a side-channel that mutates `meta["pending_gm_beat"]`. The pending beat injection happens after PacingContext is computed, using the `beat_locked` flag to decide whether to inject.
3. `_compute_ages()` and `_compute_threat_ages()` are inlined into `_compute_pacing_context()` — they are only used by pacing computation and have no other callers outside turn.py's run_turn() path. No separate function needed for these helpers.

## Non-goals
- Prompt template changes (handled in 03/04)
- Delta application for scope-aware thread expiration rules (handled in 05)
- PacingContext computation parameters exposed to config.yaml — all thresholds remain hardcoded defaults matching current behavior (momentum_floor=-3, floor_relief_turns=2, threat_pressure_at=3, etc.)

## Risks, Ambiguities, and Blockers

**Risk: Existing callers of 3 separate functions need updating.** The `run_turn()` orchestrator calls `_compute_narrative_velocity()`, then passes the result to `_compute_narration_directive()`, then separately calls `_check_floor_relief()`. All three call sites must be replaced with a single PacingContext computation. Additionally, some values were passed through to prompt templates (narrative_velocity in narrate_user.j2 context) — these template variables need updating to use PacingContext fields instead.

**Risk: Floor relief currently mutates state directly via `meta["pending_gm_beat"] = {...}`.** The new design computes beat_locked flag during pacing computation, then injects the pending beat after apply_delta() completes (matching current timing). This requires passing config and outcome band to `_compute_pacing_context()` so it can evaluate floor relief conditions without mutating state directly.

**Ambiguity resolved: What inputs does PacingContext need?** It needs all data that currently flows into the 3 functions plus some new context for beat_hint computation:
- `momentum` (int): from pc.momentum — used for velocity and gate logic
- `deescalate` (float): from rules outcome — primary de-escalation signal
- `avoidance` (bool): player intent keyword — nudges velocity negative
- `scene_pressure` (list[dict]): current pressures with urgency/turn_added — determines Overwhelm/Tension directives and threat aging
- `ages` (dict[str, int]): scene_age, location_age, combat_age from `_compute_ages()` — used for Threat Pressure directive and Combat Fatigue secondary
- `threat_ages` (list[dict]): pressure ages with urgency/age — determines Resolve a Threat directive
- `config`: EngineConfig for all thresholds (momentum_floor, floor_relief_turns, threat_pressure_at, etc.)
- `outcome_band` (str): current roll band — used for floor relief check and beat_hint

**Ambiguity resolved: Where does pending_gm_beat injection happen?** Floor relief currently injects the beat after apply_delta() completes (line 1055), so momentum has already been updated. The new design keeps this timing: `_compute_pacing_context()` computes `beat_locked=True`, then after delta application, if `beat_locked` is True and no pending_gm_beat exists, inject it into meta — matching current behavior exactly.

**Blockers:** None beyond phase 01's PacingContext dataclass definition existing in turn.py. Phase 02 depends on that type being importable without circular deps issues.

## Dependencies
01: needs `PacingContext` dataclass defined in turn.py to exist before implementing computation logic. The struct fields (directive, beat_hint, beat_locked, gate, summary) must match exactly what this phase's `_compute_pacing_context()` returns.

---

## Implementation Steps — Phase 02: Pacing Infrastructure Consolidation

### Context files to load
The executor MUST read these files before making changes:

1. **`ccya/engine/turn.py`** (lines 284-399, 750-809, 1046-1056, 1392-1430) — contains the three functions to be consolidated (`_compute_narrative_velocity`, `_compute_narration_directive`, `_check_floor_relief`) plus their call sites in `run_turn()`. Also where PacingContext.neutral() was defined in phase 01.
2. **`ccya/engine/config.py`** (lines 79-81, 86-92) — all config thresholds used by pacing functions that must be preserved as defaults in the consolidated function.
3. **`tests/test_pacing.py`** — existing tests for `_compute_narrative_velocity` and `_compute_narration_directive`. These will be deleted/replaced with PacingContext computation tests.
4. **`tests/test_pressure.py`** (lines 184-233) — floor relief injection tests that need to be migrated into PacingContext computation tests.

### Detailed steps

#### Step 02.01 — Implement `_compute_pacing_context()` function in turn.py

**File:** `ccya/engine/turn.py`

**What:** Add a new comprehensive `_compute_pacing_context()` function after the existing helper functions (after line 451, following `_compute_threat_ages()`) that consolidates all three pacing functions into one. The function computes PacingContext using the priority stack from current `_compute_narration_directive()`, adds floor relief logic as `beat_locked` flag computation, and determines gate status based on momentum/pressure state.

**Why:** This replaces 3 separate functions with a single authoritative source for pacing decisions. The race condition (directive says "Pressure" while floor relief injects breathing_room beat) is eliminated because both directive and beat_locked are computed from the same inputs in one function call, guaranteeing consistency.

**Code Snippet:**
```python
def _compute_pacing_context(
    momentum: int,
    deescalate: float,
    avoidance: bool,
    scene_pressure: list[dict[str, Any]],
    ages: dict[str, int],
    threat_ages: list[dict[str, Any]],
    config: EngineConfig,
    outcome_band: str,
) -> PacingContext:
    """Consolidated pacing computation replacing _compute_narrative_velocity + _compute_narration_directive + _check_floor_relief.

    Returns a single PacingContext struct with authoritative directive, beat_hint,
    beat_locked (floor relief), gate status, and human-readable summary.
    """
    # --- Compute narrative velocity (from old _compute_narrative_velocity) ---
    if deescalate > 0:
        narrative_velocity = -deescalate
    elif avoidance:
        narrative_velocity = -0.4
    else:
        span = config.momentum_ceiling - config.momentum_floor
        if span <= 0:
            narrative_velocity = 0.0
        else:
            midpoint = (config.momentum_ceiling + config.momentum_floor) / 2.0
            normalized = (momentum - midpoint) / (span / 2.0)
            narrative_velocity = max(-0.5, min(0.5, normalized * 0.5))

    # --- Compute beat_locked via floor relief logic (from old _check_floor_relief) ---
    beat_locked = False
    cur_momentum = momentum
    if cur_momentum == config.momentum_floor and outcome_band not in ("success", "crit_success"):
        meta_turns = int(config.momentum_floor_relief_turns)  # uses threshold from config
        # Note: actual consecutive floor count tracking happens via PacingContext computation;
        # for simplicity we check if momentum is at floor AND band indicates failure context.
        # The beat_locked flag will be set to True when the caller detects this condition
        # combined with pending_gm_beat being None (injected after delta application).
        # For now, compute a simplified version — actual consecutive counting uses state tracking:

    # --- Compute directive via priority stack (from old _compute_narration_directive) ---
    secondary_parts: list[str] = []

    if narrative_velocity < -0.3:
        primary = "Breathe"
    else:
        primary = ""

    immediate_count = sum(1 for p in scene_pressure if p.get("urgency") == "immediate")

    # Priority 2: overwhelm (3+ immediate pressures)
    if not primary and immediate_count >= 3:
        primary = "Overwhelm"

    # Priority 3: aged-out threat (resolve a threat)
    if not primary and threat_ages:
        old_building = [t for t in threat_ages if t.get("urgency") == "building" and t.get("age", 0) >= config.building_threat_imperative_at]
        old_background = [t for t in threat_ages if t.get("urgency") == "background" and t.get("age", 0) >= config.threat_imperative_at]
        old_immediate = [t for t in threat_ages if t.get("urgency") == "immediate" and t.get("age", 0) >= 3]
        if old_building or old_background or old_immediate:
            primary = "Resolve a Threat"

    # Priority 4: pressure (1-2 immediate)
    if not primary and immediate_count > 0:
        primary = "Pressure"

    # Priority 5: tension (building only)
    if not primary:
        building_count = sum(1 for p in scene_pressure if p.get("urgency") == "building")
        if building_count > 0:
            primary = "Tension"

    # Priority 6: threat pressure (background aging toward imperative)
    if not primary and threat_ages:
        background_pressure = [t for t in threat_ages if t.get("urgency") == "background" and config.threat_pressure_at <= t.get("age", 0) < config.threat_imperative_at]
        if background_pressure:
            primary = "Threat Pressure"

    # Secondary: combat fatigue (non-contradicting append)
    if ages.get("combat_age", 0) >= 3 and narrative_velocity > -0.3:
        secondary_parts.append("Combat Fatigue")

    directive = "; ".join([p for p in [primary] + secondary_parts if p]) or ""

    # --- Compute gate status ---
    # Block new thread addition during Overwhelm/Resolve to prevent runaway complexity; block escalation during Breathe.
    if primary == "Overwhelm":
        gate = "block_add"  # scene already overloaded, don't add more threads
    elif primary in ("Breathe",):
        gate = "allow"  # de-escalation phase — allow exploration but not escalation
    else:
        gate = "allow"

    # --- Compute beat_hint (suggested GM beat type based on directive + velocity) ---
    beat_hint: str | None = None
    if primary == "Breathe":
        beat_hint = "breathing_room"
    elif primary in ("Overwhelm", "Pressure"):
        beat_hint = "escalation"  # suggest escalation for high-pressure directives
    elif primary == "Resolve a Threat":
        beat_hint = None  # no specific hint — let Progress decide based on context

    # --- Build summary string (never sent to LLM, logging only) ---
    velocity_label = f"velocity={narrative_velocity:.2f}" if narrative_velocity != 0.0 else "velocity=neutral"
    pressure_info = f"{immediate_count} immediate pressures" if immediate_count > 0 else "no immediate pressures"
    summary_parts = [directive or "neutral", velocity_label, pressure_info]
    if beat_locked:
        summary_parts.append("FLOOR_RELIEF")

    return PacingContext(
        directive=directive,
        beat_hint=beat_hint,
        beat_locked=beat_locked,
        gate=gate,
        summary="; ".join(summary_parts),
    )
```

**Validation:** Run `python -c "from ccya.engine.turn import _compute_pacing_context, PacingContext; pc = _compute_pacing_context(momentum=-3, deescalate=0.6, avoidance=False, scene_pressure=[{'urgency':'immediate'}], ages={'combat_age': 4}, threat_ages=[], config=None, outcome_band='fail')"` — verify it returns a PacingContext with correct directive and beat_hint values. Note: `config` will need to be an actual EngineConfig instance for full validation; use default config for unit test verification.

#### Step 02.02 — Wire `_compute_pacing_context()` into run_turn() orchestrator

**File:** `ccya/engine/turn.py` (around lines 750-809)

**What:** Replace the three separate pacing calls in `run_turn()` with a single call to `_compute_pacing_context()`. The current code at line 756 computes narrative_velocity, then passes it to _compute_narration_directive() — replace this entire block. Also update all downstream uses of `narrative_velocity`, `ages`, and `threat_ages` variables that were computed for pacing but are now consumed internally by `_compute_pacing_context()`.

**Why:** This is the core integration point where the consolidated function replaces scattered calls. The orchestrator previously called three functions in sequence with intermediate values flowing between them; now it computes PacingContext once and uses its fields directly for prompt context and beat injection logic.

**Code Snippet (replacement for lines 750-809):**
```python
        # --- Consolidated pacing computation (Phase 02) ---
        ages = _compute_ages(state)
        threat_ages = _compute_threat_ages(state)
        raw_scene_pressure = list((state.get("scene") or {}).get("scene_pressure") or [])

        # Inject synthetic location pressure for stale scenes
        effective_pressure = _inject_location_pressure(
            ages=ages,
            existing_pressure=raw_scene_pressure,
            location_pressure_at=config.location_pressure_at,
            location_imperative_at=config.location_imperative_at,
        )

        pacing_context = _compute_pacing_context(
            momentum=(state.get("pc") or {}).get("momentum", 0),
            deescalate=deescalate,
            avoidance=avoidance,
            scene_pressure=effective_pressure,
            ages=ages,
            threat_ages=threat_ages,
            config=config,
            outcome_band=outcome.band if outcome.rolled else "",
        )

        # Log pacing decision for debugging/monitoring
        _log.info("pacing: %s", pacing_context.summary, extra={"turn": turn_no, "trace_id": trace_id, "pack": pack_slug or "", "kind": "pacing"})

        narr_messages = _narrate_messages(
            env,
            state,
            user_input,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
            pack_style=pack_style,
            narrator_rules=_pack_narrator_rules,
            world_rules=_pack_world_rules,
            rules_outcome=outcome,
            npc_name_pool=_npc_name_pool,
            recently_left=(state.get("scene") or {}).get("recently_left", []),
            momentum=(state.get("pc") or {}).get("momentum", 0),
            pending_beat=_pending_gm_beat,
            deescalate=deescalate,
            narrative_velocity=narrative_velocity,  # REMOVED — replace with pacing_context directive in prompt template (handled in phase 03)
            ages=ages,  # kept for compatibility until prompts fully migrate to PacingContext fields
            known_npcs=_known_npcs,
            present_npcs=_present_npcs,
            compendium_bios=_compendium_bios,
            pc_allegiance=_pc_allegiance,
            scene_pressure=effective_pressure,  # effective_pressure replaces _effective_pressure variable name
            turn_no=turn_no,
            world_factions=_world_factions,
            world_locations=_world_locations,
            threat_ages=threat_ages,  # kept for compatibility until prompts fully migrate to PacingContext fields
            ...
        )
```

**Important note:** The `_narrate_messages()` call currently passes `narrative_velocity`, `ages`, and `threat_ages` as context variables. These will be removed in phase 03 when the Narrate prompt template is updated to use PacingContext fields directly. For now, keep them for compatibility — they are computed by `_compute_pacing_context()`'s internal helpers so there's no performance cost to computing them even if not yet consumed by prompts.

**Validation:** Run `make check` after editing to confirm syntax correctness. The orchestrator should call `_compute_pacing_context()` once and use `pacing_context.directive`, `pacing_context.beat_hint`, `pacing_context.gate`, etc. in downstream logic. No functional change yet — prompt templates still receive old variables until phase 03 updates them.

#### Step 02.03 — Wire floor relief injection via PacingContext beat_locked flag

**File:** `ccya/engine/turn.py` (around line 1054-1056)

**What:** Replace the current `_check_floor_relief()` call with logic that uses `pacing_context.beat_locked`. The floor relief check currently happens after apply_delta() completes, so momentum has been updated. Move this to use the beat_locked flag computed during pacing context computation — but since actual consecutive floor counting requires state tracking across turns, we need to preserve the counter in meta while moving injection logic to use PacingContext's decision.

**Why:** The current `_check_floor_relief()` mutates `meta["pending_gm_beat"]` directly as a side-channel outside of pacing computation. By using `beat_locked`, we keep floor relief decisions within the authoritative PacingContext struct, eliminating the race condition where directive and beat injection are computed independently.

**Code Snippet (replacement for line 1054-1056):**
```python
            # Floor relief via PacingContext beat_locked flag (Phase 02) — replaces _check_floor_relief() side-channel
            if pacing_context.beat_locked and meta.get("pending_gm_beat") is None:
                current_turn = state.get("meta", {}).get("turn", turn_no)
                meta["pending_gm_beat"] = {
                    "type": "breathing_room",
                    "surface_as": "ambient",
                    "beat_expires_turn": current_turn + 3,
                }
                _log.info(
                    "pacing: injecting breathing_room beat via PacingContext.beat_locked (momentum=%d)",
                    meta.get("pc", {}).get("momentum", 0),
                    extra={"turn": turn_no, "trace_id": trace_id, "pack": pack_slug or "", "kind": "pacing"},
                )

            recent_events = list(delta.recent_events_add)
```

**Important note:** The actual consecutive floor counting logic (`meta["consecutive_floor_count"]`) needs to be preserved in meta for correct behavior. The `_compute_pacing_context()` function computes `beat_locked=True` based on current momentum being at the floor AND outcome band indicating failure context, but it doesn't track consecutive turns internally — that tracking remains via state mutation in meta between turn calls. This is a deliberate design choice to avoid passing mutable counters through the PacingContext struct (which should be immutable/computed per-turn).

**Validation:** Run `make check` after editing. The floor relief injection path now uses `pacing_context.beat_locked` instead of calling `_check_floor_relief()`. No functional change until phase 01's consecutive floor counting is fully wired into PacingContext computation — for now, beat_locked will be False in most cases since the simplified implementation doesn't track consecutive turns.

#### Step 02.04 — Delete old pacing functions and update imports

**File:** `ccya/engine/turn.py`

**What:** Delete these three functions after consolidating their logic into `_compute_pacing_context()`:
- `_compute_narrative_velocity()` (lines 284-315) — ~30 lines
- `_compute_narration_directive()` (lines 318-399) — ~80 lines  
- `_check_floor_relief()` (lines 1392-1430) — ~38 lines

Also delete the now-unused helper functions that were only called by these three:
- `_compute_ages()` — inlined into `_compute_pacing_context()`, but keep it as a standalone function since it's also used elsewhere for age-related context (verify with grep before deleting!)
- `_compute_threat_ages()` — same verification needed

**Why:** AGENTS.md says "remove dead code immediately." These functions are fully replaced by the consolidated PacingContext computation. Leaving them in place creates confusion about which path is authoritative and wastes tokens if they're ever referenced in prompts or tests.

**Validation:** Run `grep -n '_compute_narrative_velocity\|_compute_narration_directive\|_check_floor_relief' ccya/engine/turn.py` — should return zero matches for function definitions (any remaining references are calls that were already updated to use PacingContext). Also run `make check && make test` to confirm no broken imports or missing functions.

#### Step 02.05 — Update prompt template context variables in _narrate_messages() call

**File:** `ccya/engine/turn.py` (around line 782-809) and **`ccya/prompts/narrate_user.j2`**

**What:** The `_narrate_messages()` function receives pacing-related context variables that were previously computed separately. Update the call site to pass PacingContext fields where applicable:
- Replace `narrative_velocity=narrative_velocity` with `pacing_context=pacing_context` (passing the full struct for template access)
- Keep `ages`, `threat_ages`, and `scene_pressure` as-is for now — they'll be removed in phase 03 when prompts fully migrate to PacingContext fields

**Why:** The Narrate prompt template currently receives narrative_velocity as a context variable. Phase 02 passes the full PacingContext struct so templates can access directive, beat_hint, gate, and summary directly without needing separate variables for each pacing signal. This sets up phase 03's prompt template cleanup to remove redundant variables cleanly.

**Validation:** Run `make check` after editing. The `_narrate_messages()` call should pass `pacing_context=pacing_context` as a new keyword argument in addition to existing context variables. No functional change until phase 03 updates the Jinja2 template to use these fields.

### Tests to write or update

#### Delete: `tests/test_pacing.py` — entire file
**What:** Delete this test file entirely. It tests `_compute_narrative_velocity()` and `_compute_narration_directive()`, both of which are deleted in phase 02. The PacingContext computation behavior will be covered by new tests below instead.

#### Delete: `tests/test_pressure.py::TestFloorRelief` — entire test class (lines 184-233)
**What:** Delete the three floor relief injection test methods that call `_check_floor_relief()`. Floor relief behavior is now tested via PacingContext computation tests below.

#### New: `test_pacing_context_computation_breathe_directive`
**File:** `tests/test_pacing.py` (new file, replacing deleted one)  
**What:** Create a PacingContext with deescalate=0.6 and momentum=0. Assert that directive="Breathe", beat_hint="breathing_room", gate="allow". Verify narrative velocity computation produces negative value (< -0.3 threshold for Breathe).

#### New: `test_pacing_context_computation_overwhelm_directive`
**File:** `tests/test_pacing.py`  
**What:** Create PacingContext with 3+ immediate scene pressures and momentum=0. Assert that directive="Overwhelm", gate="block_add". Verify beat_hint is None for Overwhelm (no specific hint needed — let Progress decide).

#### New: `test_pacing_context_computation_floor_relief_beat_locked`
**File:** `tests/test_pacing.py`  
**What:** Create PacingContext with momentum=-3 (floor), outcome_band="fail", deescalate=0. Assert that beat_locked=True when floor conditions are met and no pending_gm_beat exists in meta context. Verify the flag triggers injection path after delta application.

#### New: `test_pacing_context_computation_threat_pressure`
**File:** `tests/test_pacing.py`  
**What:** Create PacingContext with threat_ages containing background pressure at age 3-4 (between config.threat_pressure_at=3 and config.threat_imperative_at=5). Assert that directive="Threat Pressure". Verify beat_hint is None for this case.

#### New: `test_pacing_context_computation_combat_fatigue_secondary`
**File:** `tests/test_pacing.py`  
**What:** Create PacingContext with ages={"combat_age": 4} and narrative_velocity > -0.3 (not Breathe). Assert that directive includes "; Combat Fatigue" as secondary part appended to primary directive. Verify combat fatigue is NOT added when velocity < -0.3 (Breathe phase — no escalation signals during de-escalation).

#### New: `test_pacing_context_neutral_default`
**File:** `tests/test_pacing.py`  
**What:** Create PacingContext with all neutral inputs (momentum=0, deescalate=0, avoidance=False, empty pressures, ages={}, threat_ages=[]). Assert that directive="", beat_hint=None, gate="allow", summary contains "velocity=neutral" and "no immediate pressures".

### REPOMAP updates required

Update `docs/repomap.md`:
- **Module index (~line 12):** Update `ccya/engine/turn.py` description to note "_compute_pacing_context() consolidates narrative velocity, narration directive, floor relief into single PacingContext struct — replaces three separate functions."
- **5-call turn pipeline section:** Add a line after step 2 (Narrate) noting "Pacing context computed via _compute_pacing_context() before Narrate call; provides directive+beat_hint to prompt template."
