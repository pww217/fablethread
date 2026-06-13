# Plan 4: Cleanup — Delete Old Pacing System

## Purpose

Remove all references to the deleted pacing system (`momentum`, `narrative_velocity`, `consecutive_pressure_turns`, `beat_locked`, `pacing_gate`, `momentum_floor`, `momentum_pacing_factor`, `momentum_ceiling`, `Pressure`/`Overwhelm` directives) from every file in the codebase. After Plans 1-3 are implemented, these fields and signals have no consumers and no behavioral effect — they are dead code and stale state. Note: `consecutive_pressure_threshold` is kept — it's repurposed by the new phase engine.

## Problem Statement

Plans 1-3 implement the new phase-driven pacing system alongside the old system. After those plans, the old fields (`momentum`, `narrative_velocity`, `consecutive_pressure_turns`, `beat_locked`, `gate`, `momentum_floor`, `momentum_pacing_factor`, `momentum_ceiling`) still exist in `PacingContext`, `TurnResult`, `EngineConfig`, event logging, EV tools, server routes, UI templates, and config. They have no consumers in the new system — they are dead fields wasting tokens in events, confusing developers reading the code, and cluttering the settings UI. Removing them cleans up 28 files and eliminates 200+ lines of dead code. Note: `consecutive_pressure_threshold` is kept — it's repurposed by the new phase engine.

## Constraints

- Plans 1-3 must be fully implemented and verified before this plan executes.
- Old events in `events.jsonl` still contain old field names — this plan does not migrate old events. EV tools must handle missing fields gracefully (they already do, via `.get()` defaults).
- No backwards compatibility with saved game state. Old saves with `pc.momentum`, `meta.consecutive_pressure_turns`, etc. will have orphan keys that are never read — harmless.
- The `consecutive_pressure_beats` counter (replacement for `consecutive_pressure_turns`) is already implemented by Plan 2 step 2.7. This plan only removes the old counter.

## Non-goals

- No functional changes — the new phase system is untouched.
- No old-event data migration — `events.jsonl` retains old field names in historical turns.
- No design doc updates beyond removing references — the design doc (`major-narrative-mechanic-overhaul.md`) is the source of truth and already documents what is removed.
- No changes to the phase engine, directive computation, or prompt templates from Plans 1-3.

## Solution

Systematically delete or null out every reference to the 6 removed fields across Python, prompts, config, templates, EV tools, and docs. The strategy is: (1) delete entire modules/files when the file's sole purpose was the old system, (2) remove fields from models/dataclasses, (3) remove imports and call sites, (4) remove UI rendering, (5) update docs.

## Firm decisions

1. **`momentum` is deleted entirely** — the `state/momentum.py` module, all imports, all call sites, the field in `pc`, the setting in `config.yaml`. No replacement — phase covers its signal.
2. **`narrative_velocity` is deleted from `TurnResult`, `PacingContext`, event logging, and UI.** It's a float that measured the wrong thing. No replacement.
3. **`consecutive_pressure_turns` is deleted.** The new `consecutive_pressure_beats` (beat-type-based, Plan 2) is the replacement. The old event key `post_extraction_consecutive_pressure_turns` is removed from event dict.
4. **`beat_locked` is deleted from `PacingContext` and all consumers.** `enforce_relief` (computed from `consecutive_pressure_beats` + phase) replaces its floor-relief role. The `"; Resolve a Threat"` append behavior is deleted with no replacement.
5. **`gate` is deleted from `PacingContext` and all consumers.** Phase-derived `allowed_beat_types` replaces its thread-gating role.
6. **`momentum_floor`, `momentum_ceiling`, `momentum_pacing_factor` are deleted from `EngineConfig`** and `build_engine_config()`. The settings UI entries are removed. The `config.yaml` keys are removed. **`consecutive_pressure_threshold` is kept** — it's repurposed by the new phase engine (`_pacing.py:derive_enforce_relief`) to determine when CRISIS phase forces relief.
7. **`Pressure` and `Overwhelm` directives** are already removed from the directive computation (Plan 2). No further action needed.
8. **The EV `momentum_lifecycle` checker is deleted.** No replacement — phase coverage is tested by new checkers (future work).
9. **The `cmd_momentum_check` EV command is deleted.** No replacement — phase state can be inspected via existing `cmd_state` or `cmd_deltas`.

## Risks, Ambiguities, and Blockers

- Large blast radius (28 files). Each step is small (one field rename or deletion) but the aggregate is many edits. Recommended: execute in file-group order (models → config → core → EV → server → templates → docs), one file at a time, with `make check` at the end of each group.
- Old events.jsonl files still contain `momentum_before`, `narrative_velocity`, etc. EV tools that read old events will get `None` from `.get()` — already handled. No breakage expected.
- The `PacingContext` dataclass shrinks from 5 fields to 3 (`directive`, `outcome_hint`, `summary`). All code that constructs or reads `PacingContext` must be updated in a single pass.

## Status

`open`

## Phases

Single phase — all changes are deletions of the same conceptual system. File grouped into 7 logical groups for execution order.

## Implementation — Phase 4: Cleanup Old Pacing System

### Context files to load

- `ccya/state/momentum.py` — entire file (37 lines)
- `ccya/state/__init__.py` — re-exports
- `ccya/engine/turn.py` — `PacingContext` (100), `_compute_narrative_velocity` (411), `_compute_pacing_context` (485), `_narrate_setup` (794), `run_turn` (886), event dict (1385-1416), floor relief injection (1079-1085), gate enforcement (1277-1283)
- `ccya/engine/changes.py` — momentum diff tracking (80, 210-217, 302, 387-391)
- `ccya/engine/narrate.py` — `_narrate_messages()` momentum parameter (30, 83), gate reference (87)
- `ccya/engine/extraction.py` — gate reference in storytell context (274)
- `ccya/engine/_pacing.py` — `consecutive_pressure_threshold` usage (34)
- `ccya/models.py` — `TurnResult` (520, narrative_velocity at 540)
- `ccya/engine/config.py` — `EngineConfig` (98, momentum fields at 144-147, 164, recent_beats_max at 149), `build_engine_config` (197, mappings at 275-277, 285)
- `ccya/ev/checkers/momentum.py` — entire file
- `ccya/ev/checkers/gm_beat.py` — `beat_locked` checks (64-111)
- `ccya/ev/checkers/pacing.py` — `consecutive_pressure` checks (25-52)
- `ccya/ev/deltas.py` — momentum/beat_locked display (197-380)
- `ccya/ev/state_tools.py` — beat_locked (254-312), cmd_momentum_check (358-396), momentum field accessors (1058-1077, 1144-1151)
- `ccya/ev/play.py` — momentum synthetic data (108-363)
- `ccya/ev/output.py` — pc.momentum (206)
- `ccya/ev/events.py` — pc.momentum field accessor (345-351)
- `ccya/ev/__init__.py` — cmd_momentum_check import (214)
- `ccya/ev/checkers/__init__.py` — momentum checker import (124)
- `ccya/pack.py` — SeedPC.momentum field (27)
- `ccya/server/routes.py` — settings GET (741-742, 750, 766, 780-781), settings POST, engine rebuild comment (806)
- `ccya/server/tv.py` — TV delta (565-617, narrative_velocity at 572, 617)
- `ccya/templates/index.html` — momentum settings (301-302, 307-308, 391-392), debug display (1859-1863)
- `ccya/templates/_turn_viewer.html` — momentum display (268-274)
- `ccya/state/io.py` — default state (85)
- `ccya/config.yaml` — momentum settings (43-44)
- `docs/architecture/turn-viewer-ui.md` — beat_locked, gate, momentum references (line 88)
- `docs/architecture/persist.md` — beat_locked, gate references (line 10)

### Detailed steps

#### Group A: Module-level deletion

##### Step 4.A.1 — Delete `ccya/state/momentum.py`

**File:** `ccya/state/momentum.py` (entire file)

**What:** Delete the file. `apply_momentum()` is no longer called — phase transitions serve the pacing role that momentum partially covered.

**Why:** Entire module is dead code. `apply_momentum` is the only function, called from `turn.py:703,741`. Those call sites are removed in Step 4.B.4.

**Validation:** `ls ccya/state/momentum.py` returns "No such file or directory."

##### Step 4.A.2 — Remove momentum re-export from `ccya/state/__init__.py`

**File:** `ccya/state/__init__.py` — line 31, 37

**What:** Delete `from ccya.state.momentum import apply_momentum` and `"apply_momentum"` from `__all__`.

**Why:** Re-export references a deleted module.

**Validation:** `make check` passes.

##### Step 4.A.3 — Delete `ccya/ev/checkers/momentum.py`

**File:** `ccya/ev/checkers/momentum.py` (entire file)

**What:** Delete the file. The `momentum_lifecycle` checker validated band→momentum delta, bounds, and floor/no-relief behavior — all obsolete.

**Why:** The checker validates a deleted system.

**Validation:** `ls ccya/ev/checkers/momentum.py` returns "No such file or directory."

##### Step 4.A.4 — Remove momentum checker import from `ccya/ev/checkers/__init__.py`

**File:** `ccya/ev/checkers/__init__.py` — line 124

**What:** Remove `momentum,` from the imports line.

**Why:** Imports a deleted module.

**Validation:** `make check` passes.

##### Step 4.A.5 — Remove `cmd_momentum_check` import from `ccya/ev/__init__.py`

**File:** `ccya/ev/__init__.py` — line 214

**What:** Remove `from ccya.ev.state_tools import cmd_momentum_check` and its command registration (if any).

**Why:** Import references a function being deleted.

**Validation:** `make check` passes.

#### Group B: Core engine deletion

##### Step 4.B.1 — Remove `narrative_velocity` from `TurnResult`

**File:** `ccya/models.py` — line 540

**What:** Delete `narrative_velocity: float | None = None` from `TurnResult`.

**Why:** Field is no longer computed or consumed. The `TurnResult` is the SSE event payload — sending a dead field wastes tokens.

**Validation:** `from ccya.models import TurnResult; assert not hasattr(TurnResult(), 'narrative_velocity')`

##### Step 4.B.2 — Remove momentum fields from `EngineConfig`

**File:** `ccya/engine/config.py` — lines 144-145, 164

**What:** Delete 3 fields from `EngineConfig` dataclass:

```
momentum_floor: int = -3          # line 144
momentum_ceiling: int = 3          # line 145
momentum_pacing_factor: float = 0.5     # line 164
```

**Note:** `consecutive_pressure_threshold` (line 147) is NOT deleted — it's repurposed by the new phase engine (`_pacing.py:derive_enforce_relief`) to determine when CRISIS phase forces relief.

**Why:** These thresholds are consumed only by the old pacing system (`_compute_narrative_velocity`), which Plan 2 rewrote to not reference them.

**Validation:** `from ccya.engine.config import EngineConfig; ec = EngineConfig(); assert not hasattr(ec, 'momentum_floor')`

##### Step 4.B.3 — Remove momentum fields from `build_engine_config()`

**File:** `ccya/engine/config.py` — lines 275, 285

**What:** Delete the 3 corresponding mappings from `build_engine_config()`:

```
momentum_floor=int(game.get("momentum_floor", -3)),           # line 275
recent_beats_max=int(game.get("recent_beats_max", 5)),        # line 277 — KEEP
...
momentum_pacing_factor=float(game.get("momentum_pacing_factor", 0.5)),  # line 285
```

**Note:** `consecutive_pressure_threshold` (line 276) is NOT deleted — it's repurposed by the new phase engine. `recent_beats_max` (line 277) is also NOT deleted — it's still used by the beat history cap.

**Why:** `build_engine_config()` must match `EngineConfig` fields exactly. Deleted config fields cause a TypeError at construction time if still mapped.

**Validation:** `make check` passes.

##### Step 4.B.4 — Remove `apply_momentum` import and calls from `turn.py`

**File:** `ccya/engine/turn.py` — line 55, line 703, line 741

**What:** Delete `from ccya.state.momentum import apply_momentum` import. Delete calls at lines 703 and 741 where `apply_momentum(state, band)` is called after the dice roll and impossible-action synthesis.

**Why:** Momentum is not tracked in the new system. The phase engine drives pacing instead.

**Validation:** `grep 'apply_momentum' ccya/engine/turn.py` returns 0 matches.

##### Step 4.B.5 — Remove `_compute_narrative_velocity()` function

**File:** `ccya/engine/turn.py` — lines 411-442

**What:** Delete the entire `_compute_narrative_velocity()` function.

**Why:** Replaced by `tension_delta` from the ruling engine (Plan 1) and thread urgency count. No code calls it after Step 4.B.6.

**Validation:** `grep '_compute_narrative_velocity' ccya/engine/turn.py` returns 0 matches.

##### Step 4.B.6 — Simplify `PacingContext` dataclass

**File:** `ccya/engine/turn.py` — lines 100-111, 485-535

**What:** 
1. Remove `beat_locked` and `gate` fields from the `PacingContext` dataclass definition (lines 100-111). Update `neutral()` static method to not include these fields.
2. Update the `_compute_pacing_context()` function (lines 485-535): remove the `beat_locked` and `gate` default variable assignments (lines 512-516). Update the docstring at line 498 to remove the "Old fields" comment. Update the `PacingContext` construction at lines 529-534 to not include `beat_locked` and `gate`.

```python
@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str
    outcome_hint: str | None
    summary: str  # human-readable log string, never sent to LLM

    @staticmethod
    def neutral() -> PacingContext:
        return PacingContext(directive="", outcome_hint="hold", summary="neutral")
```

**Why:** `beat_locked` is replaced by `enforce_relief` (computed at derivation time, not stored). `gate` is always `"allow"` — no consumer needs it. The `PacingContext` is serialized to events and passed to prompts; removing dead fields saves tokens and reduces confusion.

**Validation:** `from ccya.engine.turn import PacingContext; pc = PacingContext.neutral(); assert not hasattr(pc, 'beat_locked'); assert not hasattr(pc, 'gate')`

##### Step 4.B.7 — Remove `momentum` from `_narrate_setup()`

**File:** `ccya/engine/turn.py` — lines 794-883

**What:** 
1. Remove the `momentum` parameter from the `_narrate_messages()` call at line 876 (remove `momentum=(state.get("pc") or {}).get("momentum", 0),`).
2. Remove the `narrative_velocity` variable assignment at lines 827-828.
3. Change the return type from `tuple[Any, Any, float]` to `tuple[Any, Any]` and update the return statement at line 883 to return only 2 values (`return _pc, narr_messages`).
4. Update the docstring at line 795 to remove the narrative_velocity reference.
5. Update the caller in `run_turn` at line 960 to unpack only 2 values: `_pc, narr_messages = await _narrate_setup(ctx)`.

**Why:** `_compute_narrative_velocity` is deleted in Step 4.B.5. The function shouldn't compute or return a dead signal. Momentum is passed to the narrator prompt but the design doc says to remove it.

**Validation:** `make check` passes. `_narrate_setup` returns 2 values, not 3.

##### Step 4.B.8 — Remove momentum/narrative_velocity/beat_locked/gate from event logging

**File:** `ccya/engine/turn.py` — lines 1385-1416 (ruling_event dict, event dict, pacing_context dict)

**What:** Remove `momentum_before`, `momentum_after`, `momentum_delta` from the ruling_event dict (lines 1385-1387). Remove `momentum_before`, `momentum_after`, `momentum_delta` from the top-level event dict (lines 1400-1402). Remove `beat_locked` and `gate` from the `pacing_context` dict (lines 1405-1406). Remove `narrative_velocity` from the event dict (line 1416).

Add `scene_phase`, `crisis_turn_count`, `breather_turn_count` to the pacing_context dict (already done by Plan 2 step 2.8 — verify presence).

**Why:** Events should only contain live, meaningful fields. Dead fields waste event storage and confuse EV tool readers.

**Validation:** Run one turn, inspect events.jsonl — no `momentum_before`, `momentum_after`, `momentum_delta`, `beat_locked`, `gate`, or `narrative_velocity` keys.

##### Step 4.B.9 — Remove `consecutive_pressure_turns` from end-of-turn lifecycle

**File:** `ccya/engine/turn.py` — lines 1415-1416

**What:** Delete the `consecutive_pressure_turns` counter block. Also remove `post_extraction_consecutive_pressure_turns` from the event dict (line 1415) and `narrative_velocity` from the event dict (line 1416).

**Why:** The old counter never worked (tracks directives that never fire). The new counter (beat-type-based) is the replacement.

**Validation:** `grep 'consecutive_pressure_turns' ccya/engine/turn.py` returns 0 matches.

##### Step 4.B.10 — Remove `PacingContext.gate` enforcement in thread-add block

**File:** `ccya/engine/turn.py` — lines 1277-1283

**What:** Remove the gate check block:

```python
# Enforce PacingContext gate on thread_add
if storyteller_result.thread_add:
    _new_thread = storyteller_result.thread_add
    turn_no_for_add = state.get("meta", {}).get("turn", 0) + 1
    gate_ok = _pc is None or _pc.gate == "allow"
    if not gate_ok:
        _log.debug("thread_add blocked by pacing gate %s at T%d", getattr(_pc, 'gate', 'unknown'), turn_no_for_add)
```

Keep the thread-add logic (the rest of the block after the gate check). Remove the `gate_ok` check and the `if not gate_ok` rejection. The phase system prevents inappropriate thread creation via `allowed_beat_types` in the storyteller prompt — no Python-side gate enforcement needed.

**Why:** `gate` is always `"allow"` after Plan 2. The gate-check block is dead code that adds indentation to the thread-add logic for no reason.

**Validation:** `grep 'gate' ccya/engine/turn.py` returns 0 matches (after all steps in this group, excluding the `_pacing.py` reference to `consecutive_pressure_threshold` which is handled separately).

##### Step 4.B.11 — Remove momentum diff tracking from `changes.py`

**File:** `ccya/engine/changes.py` — lines 80, 210-217, 302, 387-391

**What:** Remove the `momentum` list field from the changes dict (line 80). Remove the momentum diff computation block (lines 210-217). Remove `momentum` from the final changes dict assembly (line 302). Remove the momentum diff rendering in the diff display (lines 387-391).

**Why:** Momentum is deleted entirely per the design doc. Diff tracking for it is dead code.

**Validation:** `grep 'momentum' ccya/engine/changes.py` returns 0 matches.

##### Step 4.B.12 — Update floor relief injection to use new phase-based logic

**File:** `ccya/engine/turn.py` — lines 1079-1085

**What:** Replace the old `beat_locked` + `momentum_floor` check with the new `enforce_relief` / `consecutive_pressure_beats` / `scene_phase` logic. The old code:

```python
# MB-3: only inject floor relief when beat_locked is caused by consecutive pressure, not momentum crisis
if _pc.beat_locked:
    cur_momentum = int((state.get("pc") or {}).get("momentum", 0))
    triggered_by_momentum = (cur_momentum <= config.momentum_floor)
    # Don't inject ambient beats during momentum crisis — player needs escalation, not breathing room
    if not triggered_by_momentum:
```

Should be replaced with:

```python
# Floor relief: inject breathing_room when CRISIS phase has enough consecutive pressure beats
if _pc is not None:
    enforce_relief = _pc.get("enforce_relief", False) if isinstance(_pc, dict) else getattr(_pc, 'enforce_relief', False)
    if enforce_relief:
```

Actually, since `enforce_relief` is computed in `_compute_pacing_context` and stored in the state, read it from the pacing context or compute it inline. The key point: remove the old `beat_locked` + `momentum_floor` logic entirely.

**Why:** The old floor relief injection uses deleted fields (`beat_locked`, `momentum_floor`). The new system computes `enforce_relief` in `_pacing.py:derive_enforce_relief()` based on `scene_phase` + `consecutive_pressure_beats` + `config.consecutive_pressure_threshold`.

**Validation:** `grep 'beat_locked\|momentum_floor' ccya/engine/turn.py` returns 0 matches (after all steps in this group).

##### Step 4.B.13 — Remove momentum parameter from `_narrate_messages()` in `narrate.py`

**File:** `ccya/engine/narrate.py` — lines 30, 83, 87

**What:** Remove the `momentum: int = 0` parameter from `_narrate_messages()` (line 30). Remove `"momentum": momentum,` from the `user_ctx` dict (line 83). Remove `"gate": pacing_context.gate if pacing_context else None,` from the `user_ctx` dict (line 87).

**Why:** Momentum is deleted entirely per the design doc. The narrator prompt should not receive momentum or gate values. The design doc confirms: "Narrator prompt: remove momentum from context — phase covers its signal."

**Validation:** `grep 'momentum' ccya/engine/narrate.py` returns 0 matches.

##### Step 4.B.14 — Remove gate reference from `extraction.py` storytell context

**File:** `ccya/engine/extraction.py` — line 274

**What:** Remove the `"gate": pacing_context.gate if pacing_context else None,` line from the storytell context dict.

**Why:** `gate` is deleted from `PacingContext`. The storytell prompt should not receive gate values.

**Validation:** `grep 'gate' ccya/engine/extraction.py` returns 0 matches.

#### Group C: EV tools deletion

##### Step 4.C.1 — Remove momentum/beat_locked/consecutive_pressure from `deltas.py`

**File:** `ccya/ev/deltas.py` — lines 197-202, 351-380

**What:** Remove the momentum block from `_cmd_deltas_compact()` (lines 197-202) and from `cmd_mechanics()` (lines 351-372). Remove the `beat_locked` display (lines 374-376). Remove the `consecutive_pressure` display (lines 378-380). Keep the `outcome_hint` display and all other fields.

**Why:** EV tool displays deleted system fields.

**Validation:** `grep 'momentum\|beat_locked\|consecutive_pressure\|gate' ccya/ev/deltas.py` returns 0 matches.

##### Step 4.C.2 — Remove beat_locked from `state_tools.py`

**File:** `ccya/ev/state_tools.py` — lines 254-312 (`cmd_beats()`), lines 358-396 (`cmd_momentum_check()`), lines 1058-1077, 1144-1151 (field accessors)

**What:** In `cmd_beats()`, remove the `beat_locked` column from the beats table (lines 267, 284, 312). Delete the entire `cmd_momentum_check()` function (lines 358-396). Remove the `momentum_before`, `momentum_after`, `momentum_delta` field accessors from the field lookup functions (lines 1058-1077, 1144-1151).

**Why:** `beat_locked` is gone. Momentum check is obsolute. Field accessors return values that don't exist in events.

**Validation:** `make check` passes. `grep 'beat_locked\|momentum_check\|momentum_before\|momentum_after\|momentum_delta' ccya/ev/state_tools.py` returns 0 matches.

##### Step 4.C.3 — Update `pacing.py` checker for new consecutive_pressure_beats

**File:** `ccya/ev/checkers/pacing.py` — lines 25-52

**What:** Replace the `consecutive_pressure` check (lines 25-52) to read `post_extraction_consecutive_pressure_beats` instead of `post_extraction_consecutive_pressure_turns`. Change the field key and update the detail messages. The check logic (is pressure beat → counter should be >= 1, not pressure → counter should be 0) stays the same.

**Why:** The event field key changed from `_turns` to `_beats` (Plan 2 step 2.7). The checker must read the new key.

**Validation:** `grep 'consecutive_pressure_turns' ccya/ev/checkers/pacing.py` returns 0 matches. `grep 'consecutive_pressure_beats' ccya/ev/checkers/pacing.py` returns at least 1 match.

##### Step 4.C.4 — Update `gm_beat.py` checker for enforce_relief

**File:** `ccya/ev/checkers/gm_beat.py` — lines 64-111

**What:** Replace the `beat_locked` + `beat_locked_dual_trigger` checks (lines 64-111) with an `enforce_relief` check that reads `scene_phase` from the pacing context. New logic:

```python
# enforce_relief: when phase is CRISIS and consecutive_pressure_beats >= threshold,
# the pending_gm_beat should be "breathing_room" regardless of what storytell emitted
pacing_ctx = extract_field(ev, "pacing_context") or {}
scene_phase = pacing_ctx.get("scene_phase")
if scene_phase == "CRISIS":
    consecutive = extract_field(ev, "post_extraction_consecutive_pressure_beats") or 0
    if int(consecutive) >= 3:
        cur_beat_post = extract_field(ev, "post_turn_pending_beat") or ...
        cur_type = cur_beat_post.get("type") if isinstance(cur_beat_post, dict) else None
        if cur_type != "breathing_room":
            findings.append({
                "turn": ev.get("turn"),
                "check": "enforce_relief",
                "detail": f"CRISIS phase with {consecutive} consecutive pressure beats but pending_gm_beat.type={cur_type!r} (expected 'breathing_room')",
            })
```

Remove the old `beat_locked`, `floor_relief_injection`, and `beat_locked_dual_trigger` checks. Keep the `beat_consumed`, `beat_lifecycle`, and `binding_present` checks.

**Why:** `beat_locked` and momentum-based dual-trigger logic are deleted. `enforce_relief` is the replacement, driven by phase + consecutive pressure beats.

**Validation:** `grep 'beat_locked\|MOMENTUM_FLOOR\|floor_relief\|dual_trigger' ccya/ev/checkers/gm_beat.py` returns 0 matches.

##### Step 4.C.5 — Remove momentum from `play.py` synthetic data

**File:** `ccya/ev/play.py` — lines 108-110, 126-128, 142-165, 282-363

**What:** Remove `momentum_before`, `momentum_after`, `momentum_delta` from all synthetic turn result dicts and format output functions. The synthetic turn output should not include fields that no longer exist in production events.

**Why:** EV play mode generates synthetic TurnResult dicts that simulate real events. Including deleted fields would train developers to expect them.

**Validation:** `grep 'momentum' ccya/ev/play.py` returns 0 matches.

##### Step 4.C.6 — Remove pc.momentum from `output.py`

**File:** `ccya/ev/output.py` — line 206

**What:** Delete the `elif field == "pc.momentum":` handler block.

**Why:** `pc.momentum` no longer exists in state.

**Validation:** `grep 'pc.momentum' ccya/ev/output.py` returns 0 matches.

##### Step 4.C.7 — Remove `pc.momentum` field accessor from `events.py`

**File:** `ccya/ev/events.py` — lines 345-351

**What:** Delete the `elif field == "pc.momentum":` handler block that reads from the momentum changes list or ruling event.

**Why:** `pc.momentum` no longer exists in state. The field accessor returns values that don't exist.

**Validation:** `grep 'pc.momentum' ccya/ev/events.py` returns 0 matches.

#### Group D: Server + Templates deletion

##### Step 4.D.1 — Remove momentum settings from `routes.py`

**File:** `ccya/server/routes.py` — lines 741, 750, 766, 780-781, 806

**What:** Remove `momentum_floor` from the settings GET response (line 741). Remove `momentum_pacing_factor` from the settings GET response (line 750). Remove `momentum_floor` from the settings update loop (line 766, but keep `consecutive_pressure_threshold` — it's repurposed). Remove `momentum_pacing_factor` from the settings update loop (lines 780-781). Update the engine rebuild comment to remove the reference to momentum_floor (line 806).

**Why:** Server exposes settings that correspond to deleted `EngineConfig` fields. Removing from both read and write paths ensures no stale settings are saved/loaded.

**Validation:** `grep 'momentum_floor\|momentum_pacing_factor' ccya/server/routes.py` returns 0 matches. `grep 'consecutive_pressure_threshold' ccya/server/routes.py` should return hits (the kept field).

##### Step 4.D.1.5 — Remove `narrative_velocity` from SSE event payload in `routes.py`

**File:** `ccya/server/routes.py` — line 294

**What:** Remove `"narrative_velocity": result.narrative_velocity,` from the SSE event payload dict.

**Why:** `narrative_velocity` is removed from `TurnResult` in Step 4.B.1. The SSE event should not include dead fields.

**Validation:** `grep 'narrative_velocity' ccya/server/routes.py` returns 0 matches.

##### Step 4.D.2 — Remove momentum/narrative_velocity from `tv.py`

**File:** `ccya/server/tv.py` — lines 565-617

**What:** Remove `momentum_before`, `momentum_after` reads (lines 567-568). Remove `narrative_velocity` read (line 572). Remove `beat_locked` from pacing context (line 611). Remove `momentum_after`, `momentum_before`, `narrative_velocity` from the TV delta row dict (lines 614-617). Keep `outcome_hint`.

**Why:** Turn viewer shows momentum and velocity deltas that no longer exist.

**Validation:** `grep 'momentum\|narrative_velocity\|beat_locked' ccya/server/tv.py` returns 0 matches (outcome_hint can stay).

##### Step 4.D.3 — Remove momentum settings from `index.html`

**File:** `ccya/templates/index.html` — lines 301-302, 307-308, 391-392, 1859-1863

**What:** Remove the momentum settings section: `momentum_floor` input (lines 301-302) and `consecutive_pressure_threshold` input (lines 307-308). Remove the `momentum_pacing_factor` dropdown (lines 391-392). Remove `momentumVal` and `nvVal` from the debug display (lines 1859-1863) — keep only `gmBeatText` and `outcome_hint`.

**Why:** Settings UI exposes fields that no longer exist. Debug display shows null values for deleted fields.

**Validation:** `grep 'momentum\|narrative_velocity\|Momentum\|Velocity' ccya/templates/index.html` returns 0 matches.

##### Step 4.D.4 — Remove momentum display from `_turn_viewer.html`

**File:** `ccya/templates/_turn_viewer.html` — lines 261-274

**What:** Remove the gate display block (lines 261-265, `<template x-if="t.pacing_context.gate && t.pacing_context.gate !== 'allow'">`). Remove the momentum display block (lines 268-274, `<template x-if="t.momentum_after !== undefined">`). Keep the `outcome_hint` block.

**Why:** TV delta rows no longer contain gate or momentum fields.

**Validation:** `grep 'momentum\|pacing_context\.gate' ccya/templates/_turn_viewer.html` returns 0 matches.

#### Group E: Config + State deletion

##### Step 4.E.1 — Remove `momentum: 0` from default state

**File:** `ccya/state/io.py` — line 85

**What:** Delete `"momentum": 0,` from the default PC state dict.

**Why:** `momentum` is no longer a tracked PC attribute. Orphan key in old saves is harmless.

**Validation:** `grep '"momentum"' ccya/state/io.py` returns 0 matches.

##### Step 4.E.2 — Remove momentum fields from `config.yaml`

**File:** `ccya/config.yaml` — lines 43-44

**What:** Delete `momentum_floor: -3` from the `game:` section. Keep `consecutive_pressure_threshold: 3` (repurposed by the new phase engine) and `thread_deescalate_on_success`.

**Why:** Config entries for deleted EngineConfig fields silently ignored by `build_engine_config()`. Removing them is tidying.

**Validation:** `grep 'momentum_floor' ccya/config.yaml` returns 0 matches. `grep 'consecutive_pressure_threshold' ccya/config.yaml` should return 1 match (the kept field).

##### Step 4.E.3 — Remove `momentum` from `SeedPC` in `pack.py`

**File:** `ccya/pack.py` — line 27

**What:** Delete `momentum: int = 0` from the `SeedPC` Pydantic model.

**Why:** Momentum is deleted entirely per the design doc. Seed state generation should not include momentum.

**Validation:** `grep 'momentum' ccya/pack.py` returns 0 matches.

#### Group F: Documentation updates

##### Step 4.F.1 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:** Remove the `state/momentum.py` entry (line 30). Update the `turn.py` entry to remove `_compute_narrative_velocity`, `PacingContext` old field references. Update `config.py` entry to remove deleted config fields. Update `ev/checkers/momentum.py`, `ev/state_tools.py` entries.

**Why:** Repomap describes modules that no longer exist. Stale docs are bugs.

**Validation:** `grep 'momentum\|narrative_velocity\|beat_locked' docs/repomap.md` returns 0 hits for the deleted items (the phase engine references are fine).

##### Step 4.F.2 — Update `docs/architecture/step0-ruling.md`

**File:** `docs/architecture/step0-ruling.md`

**What:** Remove references to `_compute_narrative_velocity()`, `beat_locked` (line 73), `consecutive_pressure_turns`, `momentum` (line 77). Update the `_compute_pacing_context()` description to reflect the new phase-driven inputs.

**Why:** Architecture doc must match actual pipeline stage outputs.

**Validation:** `grep 'narrative_velocity\|beat_locked\|momentum\|consecutive_pressure_turns' docs/architecture/step0-ruling.md` returns 0 matches.

##### Step 4.F.3 — Update `docs/architecture/pacing-systems.md`

**File:** `docs/architecture/pacing-systems.md`

**What:** This entire doc describes the old pacing system. Replace its content with a stub: "This document describes the legacy pacing system (momentum, narrative_velocity, consecutive_pressure_turns, beat_locked, pacing_gate), which was removed in the Scene Phase & Pacing Redesign (see `docs/design/major-narrative-mechanic-overhaul.md` for the replacement). The current pacing system is driven by `scene_phase` and documented in the architecture pipeline docs."

Alternatively, rewrite the doc to document the new phase system. Given that the design doc is now the authority, a stub is sufficient until a dedicated architecture doc for the phase system is written.

**Why:** Stale documentation is worse than no documentation.

**Validation:** `grep 'momentum\|narrative_velocity\|consecutive_pressure_turns\|beat_locked' docs/architecture/pacing-systems.md` returns 0 matches.

##### Step 4.F.4 — Update `docs/architecture/turn-viewer-ui.md`

**File:** `docs/architecture/turn-viewer-ui.md` — line 88

**What:** Update the Pacing Context section to remove references to `beat_locked`, `gate`, and `momentum`. The section currently says: "summary (directive + "locked" suffix or "neutral"), gate (with colored badge, hidden when "allow"), momentum before→after with delta, band label (roll turns only), beat_locked flag (when true)." Replace with: "summary (directive + "locked" suffix or "neutral"), band label (roll turns only)."

**Why:** Turn viewer no longer displays beat_locked, gate, or momentum fields.

**Validation:** `grep 'beat_locked\|gate\|momentum' docs/architecture/turn-viewer-ui.md` returns 0 matches (except in the mermaid diagram which is fine).

##### Step 4.F.5 — Update `docs/architecture/persist.md`

**File:** `docs/architecture/persist.md` — line 10

**What:** Update the event field notes to remove `beat_locked` and `gate` from the `pacing_context` description. Change: "`pacing_context` is saved at the event level (with `directive`, `beat_locked`, `gate`, `outcome_hint`, `summary`)" to "`pacing_context` is saved at the event level (with `directive`, `outcome_hint`, `summary`)."

**Why:** `pacing_context` no longer contains `beat_locked` or `gate`.

**Validation:** `grep 'beat_locked\|gate' docs/architecture/persist.md` returns 0 matches.

##### Step 4.F.6 — Update `docs/architecture/step0-ruling.md` to remove `consecutive_pressure_threshold` reference

**File:** `docs/architecture/step0-ruling.md`

**What:** Remove any references to `consecutive_pressure_threshold` as a momentum-related config. The field is now only used by `_pacing.py:derive_enforce_relief()` for the new phase-based relief system.

**Why:** Architecture doc must match actual config usage.

**Validation:** `grep 'consecutive_pressure_threshold' docs/architecture/step0-ruling.md` — any hits should note it's now used by the phase engine, not the old momentum system.

### Tests to write or update

No automated tests (tests are temporarily removed during refactor). Verification:

1. **`make check` passes** — lint + typecheck after all changes.
2. **Start server, load a game** — no startup errors, settings panel has no momentum fields, debug display shows no momentum/velocity.
3. **Play 2 turns via ev.py** — events.jsonl contains no momentum/narrative_velocity/beat_locked/gate/consecutive_pressure_turns keys.
4. **Run checkers against events** — `pacing_directives` and `gm_beat_lifecycle` checkers pass (after updates).
5. **Turn viewer** — loads with no momentum columns.
