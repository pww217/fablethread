# Pacing/Beat System — Plan 2/3: Core turn.py Rewiring

## Purpose

Implement all six design changes in `turn.py` and the supporting config field. This is the backend work — state mutations, trigger conditions, data collection. Prompt changes deferred to Plan 3.

## Problem Statement

Six interlocking failures produce zero useful pacing output across 51 turns: `beat_locked` is unreachable (counter tracks directives that never fire), floor relief is blocked by a `not pending_gm_beat` guard that is almost never satisfied, stale beats persist on null turns, beat diversity guidance is untestable (no history), Scene Imperative has no behavioral weight, and Breathe fires on false velocity signals (stealth conflated with relief). All six root causes are in `turn.py`.

## Constraints

- Pipeline order unchanged.
- Beat type vocabulary (9 types) unchanged.
- No backwards compatibility — old state fields (`consecutive_pressure_turns` keyed to directives) are replaced in place.
- The momentum floor fallback (`momentum <= -3`) is retained as a belt-and-suspenders trigger for `beat_locked`.
- Null beat cadence (1-in-4 guidance) is preserved.

## Non-goals

- Prompt changes (deferred to Plan 3).
- Test changes (tests are suspended during refactor).

## Solution

Execute the six changes in top-to-bottom `turn.py` file order (plus one `config.py` addition). Each change is a direct replacement described in the design doc — no new models, no pipeline reordering, no behavioral scope creep.

## Firm decisions

1. `recent_beats_max: int = 5` added to `EngineConfig` (config.py) with corresponding wire in `build_engine_config`. This controls the beat history window size.
2. Change 6 (Breathe) uses thread urgency only — no beat history check (design doc rationale: thread urgency is the correct signal; beat history adds nothing for this guard).
3. Change 1 re-keys to pressure beat types: `("pressure", "escalation", "complication")`.
4. Change 2 uses the same pressure type list for the override check.
5. Change 4a caps `recent_beats` at `config.recent_beats_max` entries, oldest first.
6. All pressure-type sets (changes 1 and 2) use the same tuple `("pressure", "escalation", "complication")` — extract to a module-level constant if used more than once, otherwise inline.

## Risks, Ambiguities, and Blockers

- The `_current_beat` variable in Change 2 is introduced in a new scope. Must ensure it doesn't shadow anything.
- `narrative_velocity < -0.3` combined with `urgent_count > 0` in Change 6: the velocity check is in place first, then thread urgency. Must ensure thread urgency is computed only when velocity is low, not on every call.
- Change 4a's append happens after floor relief. The `pending_gm_beat` read in Change 4a reflects state after any floor-relief override. This is by design (the history should reflect what the narrator actually sees).

## Status

`open`

---

## Phases

1 phase: all changes in execution order. Full turn.py context loaded once.

---

## Implementation

### Context files to load

- `ccya/engine/config.py` lines 100-213 (`EngineConfig` dataclass + `build_engine_config`)
- `ccya/engine/turn.py` lines 420-550 (`_compute_narration_directive` + `_compute_pacing_context`)
- `ccya/engine/turn.py` lines 994-1006 (gm_beat apply block)
- `ccya/engine/turn.py` lines 1089-1096 (floor relief injection)
- `ccya/engine/turn.py` lines 1183-1192 (consecutive_pressure counter update)
- `ccya/engine/turn.py` lines 750-758 (narrate pending_gm_beat TTL read — for reference)

### Detailed steps

#### Step 0 — Add `recent_beats_max` to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add a new field to the `EngineConfig` dataclass:
```
recent_beats_max: int = 5
```

Add to `build_engine_config`:
```
recent_beats_max=int(game.get("recent_beats_max", 5)),
```

Place near the existing beat-related fields (after `consecutive_pressure_threshold` at line 123).

**Why:** Change 4a caps the `recent_beats` list at N entries. The cap value must be configurable per the design doc.

**Validation:** `make check` passes.

---

#### Step 1 — Breathe trigger refinement (Change 6)

**File:** `ccya/engine/turn.py` line 440

**What:** Replace the single-line `if narrative_velocity < -0.3: return "Breathe"` with a guarded version:

```
if narrative_velocity < -0.3:
    urgent_count = sum(
        1 for t in scope_scene_threads
        if getattr(t, "urgency", "") == "urgent"
    )
    if urgent_count == 0:
        return "Breathe"
```

The old code:
```python
    if narrative_velocity < -0.3:
        return "Breathe"
```

When `urgent_count > 0`, the function falls through to the Scene Imperative check at line 445.

**Why:** Low velocity during active urgent threads is tactical avoidance, not genuine relief. The urgent thread presence is the discriminator the velocity signal alone cannot provide.

**Validation:** Trace through: when `narrative_velocity < -0.3` and `urgent_count == 0`, returns "Breathe" (same as before). When `urgent_count > 0`, falls through to Scene Imperative / Pressure / Tension. Confirm no other code depends on "Breathe" always firing at velocity < -0.3.

---

#### Step 2 — Null-clear pending_gm_beat (Change 3)

**File:** `ccya/engine/turn.py` lines 1000-1006

**What:** Add an `else` branch to the existing `if _new_beat and _new_beat.type:` block:

```python
            if _new_beat and _new_beat.type:
                _beat_dict = _new_beat.model_dump(exclude_none=True)
                _beat_dict["beat_expires_turn"] = turn_no + 2
                state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
            else:
                state.get("meta", {}).pop("pending_gm_beat", None)
```

The current code has no else branch — flow simply falls through.

**Why:** When the storyteller intentionally emits null, the old beat should not persist. This is the most targeted fix — clear stale beats specifically when null is emitted, leaving normal beat overwrites unaffected.

**Placement note:** This must go at line ~1006, immediately after the existing `if` block. NOT in the floor relief section at line 1089. The floor relief guard at line 1090 reads `pending_gm_beat` — the null-clear must run before that check.

**Validation:** Trace: when `_new_beat` is None or has no type, `pending_gm_beat` is popped from meta (no KeyError — `pop` with default None). When `_new_beat` has a type, the existing setter runs unchanged. Ensure `meta` dict exists before pop — `state.get("meta", {})` returns empty dict if meta is absent, and `pop` on a non-ref dict is safe (no assignment, just method call).

---

#### Step 3 — Floor relief guard replacement (Change 2)

**File:** `ccya/engine/turn.py` lines 1089-1096

**What:** Replace the existing floor relief block:

Old:
```python
            if _pc.beat_locked and not state.get("meta", {}).get("pending_gm_beat"):
                meta = state.setdefault("meta", {})
                meta["pending_gm_beat"] = {
                    "type": "breathing_room",
                    "surface_as": "ambient",
                    "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
                }
```

New:
```python
            if _pc.beat_locked:
                _current_beat = state.get("meta", {}).get("pending_gm_beat")
                if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
                    meta = state.setdefault("meta", {})
                    meta["pending_gm_beat"] = {
                        "type": "breathing_room",
                        "surface_as": "ambient",
                        "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
                    }
```

Where `PRESSURE_BEAT_TYPES` is a module-level constant defined once (or inline tuple) shared with Step 5:
```
PRESSURE_BEAT_TYPES = ("pressure", "escalation", "complication")
```

The `meta` variable used here must be declared before use. If `meta` was previously defined in a different scope, declare it inside this block or add `meta: dict = state.setdefault("meta", {})`.

**Why:** The old guard (`not pending_gm_beat`) blocked floor relief whenever storytell generated any beat (80%+ of turns). The replacement only overrides when:
- No beat exists (null turn — stale beat cleared by Step 2), OR
- The current beat is a pressure type (storyteller is stuck in a pressure loop)

When the storyteller already produced a non-pressure beat, let it stand.

**Timing note:** By the time this runs, Change 3's null-clear has already run (Step 2), so null turns leave `pending_gm_beat` absent. The `_current_beat is None` branch correctly captures this case.

**Validation:** Trace path A: `_pc.beat_locked=True`, `pending_gm_beat` is None → injects breathing_room. Trace path B: `_pc.beat_locked=True`, `pending_gm_beat.type` is "revelation" → no injection (non-pressure beat stands). Trace path C: `_pc.beat_locked=False` → no injection (unchanged from old behavior).

---

#### Step 4 — Append recent_beats history (Change 4a)

**File:** `ccya/engine/turn.py` — between floor relief (step 3, ~line 1096) and counter update (step 5, ~line 1183)

**What:** After the floor relief block and before the counter update, add:

```python
            # Beat history: snapshot pending_gm_beat after floor relief override
            _history_beat = state.get("meta", {}).get("pending_gm_beat")
            meta = state.setdefault("meta", {})
            meta.setdefault("recent_beats", []).append({
                "turn": turn_no,
                "type": _history_beat.get("type") if _history_beat else None,
                "surface_as": _history_beat.get("surface_as") if _history_beat else None,
            })
            # Cap at N entries, oldest first
            max_beats = config.recent_beats_max if config else 5
            if len(meta["recent_beats"]) > max_beats:
                meta["recent_beats"] = meta["recent_beats"][-max_beats:]
```

`config` is in scope as the function parameter of `run_turn` (line 821). The `meta` variable may already be defined from Step 3's scope — reuse the same variable or declare a fresh one with `meta = state.setdefault("meta", {})`.

Exact insertion point: between the end of the floor relief block (after Step 3's `meta["pending_gm_beat"] = ...` block) and before the counter update (Step 5).

**Why:** Beat history feeds the storyteller prompt (Plan 3) so the LLM can follow diversity guidance. The snapshot is taken after floor relief so the history reflects what the narrator actually received. Null beats are included as `{"type": null, "surface_as": null}`.

**Save/load compatibility:** `meta.setdefault("recent_beats", [])` handles missing key from pre-feature saves. No migration needed.

**Validation:** After one turn with a "pressure" beat, `meta["recent_beats"]` has `[{"turn": N, "type": "pressure", "surface_as": "npc_behavior"}]`. After 6 turns, list is capped at 5 entries (oldest dropped). After a null turn with floor relief override, entry shows `{"turn": N, "type": "breathing_room", "surface_as": "ambient"}`.

---

#### Step 5 — Re-key consecutive_pressure counter to beat types (Change 1)

**File:** `ccya/engine/turn.py` lines 1183-1192

**What:** Replace the existing counter update:

Old:
```python
        # Two-pass consecutive pressure counter update.
        if _extract_result is not None and _pc is not None:
            directive = _pc.directive or ""
            thread_updates = storyteller_result.thread_update if storyteller_result else []
            meta = state.setdefault("meta", {})
            current_pressure = meta.get("consecutive_pressure_turns", 0)
            if (directive in ("Pressure", "Overwhelm")) and not thread_updates:
                meta["consecutive_pressure_turns"] = current_pressure + 1
            else:
                meta["consecutive_pressure_turns"] = 0
```

New:
```python
        # Consecutive pressure counter: tracks storyteller beat types, not directives.
        if _extract_result is not None and _pc is not None:
            last_gm_beat_type = (
                storyteller_result.gm_beat.type
                if storyteller_result and storyteller_result.gm_beat
                else None
            )
            meta = state.setdefault("meta", {})
            current_pressure = meta.get("consecutive_pressure_turns", 0)
            if last_gm_beat_type in PRESSURE_BEAT_TYPES:
                meta["consecutive_pressure_turns"] = current_pressure + 1
            else:
                meta["consecutive_pressure_turns"] = 0
```

Where `PRESSURE_BEAT_TYPES` is the same module-level constant from Step 3: `PRESSURE_BEAT_TYPES = ("pressure", "escalation", "complication")`.

Define this constant once near the top of `turn.py` (after imports, before any function definitions).

**Why:** The old counter tracked directives ("Pressure"/"Overwhelm") that never fire in either game (0/51 turns). The new counter tracks the actual storyteller beat type — the signal that correlates with actual pressure. The three beat types `pressure`, `escalation`, `complication` are the pressure-type beats the storyteller generates.

**Null behavior:** When `storyteller_result.gm_beat` is None (null beat turn), `last_gm_beat_type` is None and does not match any pressure type → counter resets to 0. This is correct — null means nothing notable happened, which is effectively relief.

**Validation:** After 3 consecutive pressure-type beats, `consecutive_pressure_turns >= 3` triggers `beat_locked` in `_compute_pacing_context` (line 504). After a null or non-pressure beat, counter resets to 0.

---

### Tests to write or update

No tests (suspended during refactor). Run `make check` after all Plan 2 + Plan 3 changes are complete to verify lint and types.
