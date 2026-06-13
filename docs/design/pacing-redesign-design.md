# Pacing Redesign — Simple Scene Rhythm

## Purpose

This document is the design authority for simplifying CCYA's pacing systems. It addresses why scenes drag, why punishment feels unfair, why new opportunities don't emerge organically, and why the system is too complex to maintain. It is for implementers and human reviewers.

## Problem Statement

CCYA's pacing system is designed to produce emergent scene rhythm through four interlocking subsystems (momentum, GM beats, pacing context, thread lifecycle). In practice, it produces three problems:

1. **Scenes and combat go too long.** Scene pressure and combat pressure rarely force movement alone. The system tries to force resolution instead of gently pushing toward it.
2. **Punishment feels unfair, wins feel earned-but-not-rewarding.** Players get ambushed, lose momentum, and the system withholds relief when they're losing hardest (floor relief explicitly skips momentum crisis). Difficulty bias keeps momentum negative for entire sessions. Winning triggers the gate that blocks storyteller from recording what the victory created.
3. **Complexity prevents iteration.** The system is too complex to hold in your head. Checkers are broken. Regressions are commonplace. You can't fix the gate without breaking something else because nobody knows what the something else is.

The one thing that works well: `advance`/`hold`/`transition` directives. Simple 3-value signals from `intent.scene_motion` that bypass the entire pacing machine and map directly to what the narrator needs.

## Constraints

- Must not break save compatibility — `state.yaml` fields must persist.
- Must not remove momentum entirely — it is a player-visible mechanic that works when not sabotaged by the gate.
- Must not remove GM beats — they are the primary storyteller guidance mechanism.
- Must not remove thread lifecycle — it is the storyteller's primary story management tool.
- Must not add new LLM calls to the turn pipeline — 5-call pipeline is fixed.
- Must not change the 3 ruling bands (crit_fail, fail, setback, partial, success, crit_success).

## Non-goals

- Fixing difficulty assignment bias (TICK-12) — this is a ruling-phase problem, not a pacing problem.
- Fixing goal format validation (TICK-47) — this is an extraction-phase problem.
- Fixing NPC agency (TICK-11) — this is a prompt problem, not a pacing problem.
- Fixing world state bloat (TICK-33) — this is a prompt/context problem.
- Fixing checkers (TICK-42) — this is a testing problem, not a pacing problem. (Though this design should make checkers easier to fix.)

## Decision Table

| Decision | What | Why |
|---|---|---|
| Remove `narrative_velocity` | Delete `_compute_narrative_velocity()`, replace its single consumer check with direct `deescalate` comparison | It is computed, logged, but never rendered in any prompt. Its only purpose is feeding the "Breathe" branch of directive computation, which can check `deescalate > 0.3` directly. |
| Remove `PacingContext.summary` | Delete the `summary` field from the dataclass | It is documented as "never sent to LLM" and only used in events.jsonl logging. Log individual fields directly if you need observability. |
| Keep `PacingContext.gate` | Retain `gate: Literal["block_escalate", "allow"]` | It is the primary mechanism for controlling storyteller thread creation after big successes. But change its trigger from "success against urgent threads" to "crit_success against urgent threads" so regular successes don't block thread creation. |
| Keep `PacingContext.beat_locked` | Retain `beat_locked: bool` | It is Python-only logic that triggers floor relief injection and thread cap enforcement. It is not visible to the LLM. |
| Keep `PacingContext.directive` | Retain directive computation but simplify the priority stack | The 6-level directive stack (Breathe → Scene Imperative → Overwhelm → Pressure → Tension → Scene Pressure) is too granular. Collapse to 3 levels: Breathe, Pressure, Normal. |
| Keep `PacingContext.outcome_hint` | Retain `outcome_hint: str | None` | This is the thing that works well. Simple 3-value signal that maps directly to what the narrator needs. |
| Keep `consecutive_pressure_turns` | Retain the counter | It is 3 lines of code at turn end feeding one boolean check. Not a separate system, just a counter. |
| Keep `pending_gm_beat` | Retain GM beat lifecycle | It is the primary storyteller guidance mechanism. Keep TTL, floor relief override, and expiry. |
| Fix floor relief | Remove the momentum-crisis exception | Floor relief should inject `breathing_room` whenever `beat_locked` fires, regardless of trigger source. Withholding relief when the player is losing hardest is the opposite of good pacing. |
| Fix gate trigger | Change from `deescalate >= 0.5` to `deescalate >= 1.0` | Gate should only fire on critical successes against urgent threads, not regular successes. Regular successes should allow the storyteller to record what the victory created. |
| Simplify directive to 3 levels | Breathe, Pressure, Normal (empty) | The 6-level stack produces marginal differences that the LLM cannot meaningfully distinguish. Breathe = de-escalation. Pressure = scene needs tension. Normal = storyteller's judgment. |
| Add scene-age pressure | When scene_age >= 3, append "Move the scene" to directive | This is the gentle push toward resolution that currently doesn't exist. Scene age alone should nudge the storyteller, not just force directives at 4-5 turns. |
| Remove `scene_pressure_threshold` config | Delete from EngineConfig | The simplified directive stack doesn't need a separate "Scene Pressure" secondary directive. Scene age is handled by the "Move the scene" append. |
| Remove `scene_imperative_threshold` config | Delete from EngineConfig | Scene Imperative at 4-5 turns is too late. Scene age >= 3 triggers "Move the scene" at 3 turns, which is the gentle nudge. Scene Imperative (hard stop) at 7+ turns if scene hasn't moved. |
| Remove `momentum_pacing_factor` config | Delete from EngineConfig | Momentum no longer feeds into narrative velocity, which is deleted. Momentum only affects beat_locked and floor relief. |

## Current State — What Exists

### Momentum System

`state.pc.momentum` is an integer in [-3, +3], set deterministically from ruling bands via `apply_momentum()` in `ccya/state/momentum.py`. It is clamped, has depth-based catch-up acceleration at -3, and feeds into three downstream systems:

1. **Narrative velocity** — a float scalar in [-1, 1] computed from deescalate, momentum, and avoidance. Never rendered in any prompt. Only affects the "Breathe" branch of directive computation.
2. **Beat locked** — dual trigger: `momentum <= -3` OR `consecutive_pressure_turns >= 3`. Triggers floor relief injection and thread cap enforcement.
3. **Floor relief exception** — when beat_locked is triggered by momentum crisis, floor relief is explicitly withheld. This is the core design flaw: the player is losing hardest and the system says "you don't deserve relief."

### GM Beat System

`state.meta.pending_gm_beat` carries a beat from storyteller to narrator across turns. 2-turn TTL. Beat types: complication, escalation, pressure, revelation, opportunity, breathing_room, twist, setback, callback. Pressure types (pressure, escalation, complication) feed `consecutive_pressure_turns` counter. Floor relief injects `breathing_room` when beat_locked fires (except momentum crisis).

### Pacing Context

`PacingContext` is a Python-computed struct with 5 fields:

- `directive` — 6-level priority stack (Breathe, Scene Imperative, Overwhelm, Pressure, Tension, Scene Pressure) + "; Resolve a Threat" appended when beat_locked
- `outcome_hint` — hold/advance/transition from scene_motion + scene age + urgency
- `beat_locked` — bool, dual trigger from consecutive pressure or momentum floor
- `gate` — block_escalate/allow, fires when deescalate >= 0.5
- `summary` — human-readable log, never sent to LLM

### Thread Lifecycle

`arc.threads[]` tracked by storyteller, enforced by engine. Urgency levels: background, normal, urgent. Urgent thread count feeds directive computation (3+ = Overwhelm, 1-2 = Pressure, 0 = Tension/Normal). Thread cap at 5 active, auto-latent at 3 turns untouched, urgency decay at 8 turns.

### How It All Interacts

```
Ruling Phase
  ├─ apply_momentum(state, band) → state.pc.momentum
  ├─ compute deescalate (0.0/0.6/1.0) → ctx._deescalate
  └─ compute ages → ctx._ages

Narrate Setup
  ├─ _compute_narrative_velocity() → narrative_velocity (never in prompts)
  ├─ _compute_pacing_context() → PacingContext
  │   ├─ _compute_narration_directive() → 6-level directive
  │   ├─ beat_locked dual-trigger → beat_locked bool
  │   ├─ outcome_hint from scene_motion → outcome_hint
  │   └─ gate from deescalate >= 0.5 → gate
  └─ Pass PacingContext to narrate + storytell prompts

Extraction Phase
  ├─ Storytell reads directive/gate/outcome_hint → selects gm_beat
  ├─ Floor relief injection → pending_gm_beat = breathing_room (EXCEPT momentum crisis)
  ├─ Consecutive pressure counter → state.meta.consecutive_pressure_turns
  └─ Thread add gated by PacingContext.gate
```

### Problems with Current State

1. **`narrative_velocity` is dead code.** Computed, logged in events, but never rendered in any prompt template. Only affects "Breathe" branch of directive computation, which could check `deescalate > 0.3` directly.

2. **`PacingContext.summary` is dead code.** Documented as "never sent to LLM". Only used in events.jsonl logging.

3. **Gate fires on success, not just critical success.** `deescalate >= 0.5` fires on regular success (0.6) AND critical success (1.0). This means winning a fight against pressure blocks thread creation, preventing the storyteller from recording what the victory created. This is the root cause of "you win → scene drags because nothing new enters."

4. **Floor relief withholds relief during momentum crisis.** The exception `if not triggered_by_momentum` in floor relief injection means the player gets no breathing_room when momentum hits -3, which is exactly when they need it most. This is the root cause of "punishment feels unfair."

5. **6-level directive stack is too granular.** The LLM cannot meaningfully distinguish between "Pressure", "Overwhelm", "Tension", and "Scene Pressure". These produce marginal differences in output that are indistinguishable in practice. The 3 working levels are Breathe, Pressure, and Normal.

6. **No gentle scene-age pressure.** Scene age only triggers directives at 3-4 turns (Scene Pressure secondary) and 5 turns (Scene Imperative). There is no gradual nudge between turns 1-3. Scenes naturally want to drag, and the system doesn't counter this until 3-4 turns have already passed.

7. **Checkers are broken.** momentum checkers read the wrong field, beat checkers don't understand floor relief exceptions, pacing checkers reference non-existent event fields. You cannot validate fixes.

## Proposed Solution

### Core Changes

#### 1. Remove `narrative_velocity`

Delete `_compute_narrative_velocity()` from `turn.py`. Replace its single consumer in `_compute_narration_directive()`:

```python
# Before:
if narrative_velocity < -0.3:
    if urgent_count == 0:
        return "Breathe"

# After:
if deescalate > 0.3 and urgent_count == 0:
    return "Breathe"
```

Deescalate is already 0.0, 0.6, or 1.0. The threshold check is identical logic, one less function, one less variable, one less thing in events.jsonl.

#### 2. Simplify directive to 3 levels

```python
def _compute_directive(deescalate, active_threads, ages, config, beat_locked):
    """Compute narration directive with 3 levels.
    
    Priority:
      1. Breathe — de-escalation from successful check, no urgent threads
      2. Pressure — scene needs tension (urgent threads OR scene age >= 3)
      3. Normal — empty string, storyteller's judgment
    """
    # 1. Breathe — de-escalation wins
    if deescalate > 0.3 and not any(t.urgency == "urgent" for t in active_threads):
        return "Breathe"
    
    urgent = sum(1 for t in active_threads if t.urgency == "urgent")
    scene_age = ages.get("effective_scene_age", 0)
    
    # 2. Pressure — urgent threads or scene getting stale
    if urgent >= 1 or scene_age >= 3:
        directive = "Pressure"
    else:
        directive = ""
    
    # Append scene movement nudge at age 3-6
    if 3 <= scene_age < 7:
        if directive:
            directive += "; Move the scene"
        else:
            directive = "Move the scene"
    
    # Append threat resolution when beat_locked (except Breathe)
    if beat_locked and directive != "Breathe":
        if directive:
            directive += "; Resolve a Threat"
        else:
            directive = "Resolve a Threat"
    
    return directive
```

The 3 levels are:
- **Breathe** — explicit de-escalation, no new pressure
- **Pressure** — scene needs tension (urgent threads OR stale scene)
- **Normal** (empty) — storyteller's judgment, with optional "Move the scene" nudge at age 3-6

#### 3. Fix gate trigger

Change from `deescalate >= 0.5` to `deescalate >= 1.0`:

```python
# Before:
if deescalate >= 0.5:
    gate = "block_escalate"

# After:
if deescalate >= 1.0:  # Only critical success against urgent threads
    gate = "block_escalate"
```

Regular successes (deescalate=0.6) no longer block thread creation. The storyteller can record what the victory created. Only critical successes (deescalate=1.0) block escalation, which is appropriate for dramatic victories that should have consequences.

#### 4. Fix floor relief

Remove the momentum-crisis exception:

```python
# Before:
if _pc.beat_locked:
    triggered_by_momentum = (cur_momentum <= config.momentum_floor)
    if not triggered_by_momentum:  # <-- THIS EXCEPTION IS REMOVED
        # inject breathing_room

# After:
if _pc.beat_locked:
    # Always inject breathing_room when beat_locked, regardless of trigger source
    _current_beat = state.get("meta", {}).get("pending_gm_beat")
    if _current_beat is None or _current_beat.get("type") in PRESSURE_BEAT_TYPES:
        # inject breathing_room
```

Floor relief should fire whenever beat_locked fires, regardless of whether it was triggered by consecutive pressure or momentum crisis. Withholding relief when the player is losing hardest is the opposite of good pacing.

#### 5. Simplify PacingContext

```python
@dataclass
class PacingContext:
    directive: str          # "Breathe" | "Pressure" | "Move the scene" | "Resolve a Threat" | ""
    outcome_hint: str | None  # "hold" | "advance" | "transition"
    gate: Literal["block_escalate", "allow"]
    beat_locked: bool       # Python-only: floor relief + thread cap
```

Remove `summary`. It is never sent to the LLM and only used in events.jsonl logging. Log individual fields directly if you need observability.

#### 6. Add scene-age pressure

The "Move the scene" append at scene_age >= 3 is the gentle push toward resolution that currently doesn't exist. It is not a hard directive — it is appended to the directive string as guidance. At age 3-6, it nudges the storyteller. At age 7+, the absence of "Move the scene" combined with the absence of urgent threads means the storyteller gets no directive at all, which is appropriate — if the scene has been stale for 7 turns, something is fundamentally wrong and no directive will fix it.

### Data Flow After Simplification

```
Ruling Phase
  ├─ apply_momentum(state, band) → state.pc.momentum
  ├─ compute deescalate (0.0/0.6/1.0) → ctx._deescalate
  └─ compute ages → ctx._ages

Narrate Setup
  ├─ _compute_pacing_context() → PacingContext
  │   ├─ _compute_directive() → 3-level directive + scene-age nudge
  │   ├─ beat_locked dual-trigger → beat_locked bool
  │   ├─ outcome_hint from scene_motion → outcome_hint
  │   └─ gate from deescalate >= 1.0 → gate
  └─ Pass PacingContext to narrate + storytell prompts

Extraction Phase
  ├─ Storytell reads directive/gate/outcome_hint → selects gm_beat
  ├─ Floor relief injection → pending_gm_beat = breathing_room (ALWAYS when beat_locked)
  ├─ Consecutive pressure counter → state.meta.consecutive_pressure_turns
  └─ Thread add gated by PacingContext.gate
```

### Alternatives Considered and Rejected

**Alternative 1: Remove momentum entirely.**
Rejected. Momentum is a player-visible mechanic that works when not sabotaged by the gate. Removing it would change the core feel of the game. The problem is not momentum — it is the gate and floor relief exception.

**Alternative 2: Remove GM beats.**
Rejected. GM beats are the primary storyteller guidance mechanism. They work well when not overridden by broken floor relief logic.

**Alternative 3: Keep 6-level directive stack.**
Rejected. The LLM cannot meaningfully distinguish between "Pressure", "Overwhelm", "Tension", and "Scene Pressure". These produce marginal differences in output that are indistinguishable in practice. The 3 working levels are Breathe, Pressure, and Normal.

**Alternative 4: Keep gate at deescalate >= 0.5.**
Rejected. This is the root cause of "you win → scene drags because nothing new enters." Regular successes should not block thread creation. Only critical successes should block escalation.

**Alternative 5: Keep floor relief exception for momentum crisis.**
Rejected. Withholding relief when the player is losing hardest is the opposite of good pacing. This is the root cause of "punishment feels unfair."

## Failure Modes and Risks

1. **3-level directive may be too coarse.** If the LLM needs more granularity, "Pressure" may not distinguish between "mild tension" and "full-on crisis." Mitigation: the "Resolve a Threat" append when beat_locked provides additional signal. The outcome_hint (advance/hold/transition) provides scene-motion signal. Together, they give the LLM more context than the old 6-level directive.

2. **Removing scene_pressure_threshold and scene_imperative_threshold may break config.** These are in EngineConfig and referenced in config.yaml. They must be removed from config loading or they will cause errors.

3. **Checkers will need updating.** The pacing checker references `consecutive_pressure_turns` which is still used. The beat checker references floor relief which is changing behavior. The momentum checker reads `momentum_before`/`momentum_after` which is unchanged. Checkers will need to be updated to match the new behavior.

4. **Events.jsonl will change.** `narrative_velocity` will no longer be logged. `PacingContext.summary` will no longer exist. Checkers that read these fields will break. This is acceptable — the fields were dead code.

5. **Old saves may have stale config.** If someone has `scene_pressure_threshold` or `scene_imperative_threshold` in their config.yaml, removing them from EngineConfig will cause a KeyError during config loading. Must use `.get()` with defaults or migrate config loading to ignore unknown keys.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `_compute_narrative_velocity()` | `turn.py` | Dead code — never rendered in prompts |
| `narrative_velocity` variable | `turn.py`, `narrate.py`, events.jsonl | Computed but never used by LLM |
| `PacingContext.summary` | `turn.py` | Never sent to LLM, only in events.jsonl |
| `scene_pressure_threshold` | `EngineConfig`, `config.py` | Replaced by scene-age append in directive |
| `scene_imperative_threshold` | `EngineConfig`, `config.py` | Scene age >= 3 triggers "Move the scene" at 3 turns |
| `momentum_pacing_factor` | `EngineConfig`, `config.py` | Momentum no longer feeds into narrative velocity |
| `thread_deescalate_on_success` | `EngineConfig`, `config.py` | [OPEN: keep this config? It controls whether deescalate fires at all. If removing it, deescalate should always fire on success against urgent threads.] |

## What Is Unchanged

- `state.pc.momentum` — still set from ruling bands, still clamped to [-3, +3], still has depth-based catch-up acceleration at -3.
- `state.meta.pending_gm_beat` — still carries beats across turns, still 2-turn TTL, still consumed by narrator and storyteller.
- `consecutive_pressure_turns` — still incremented at turn end when pressure beat emitted, still triggers beat_locked at threshold of 3.
- `arc.threads[]` — still tracked by storyteller, still enforced by engine (cap, staleness, urgency decay).
- `PRESSURE_BEAT_TYPES` — still `("pressure", "escalation", "complication")`.
- `apply_momentum()` — still in `ccya/state/momentum.py`, still deterministic from bands.
- `PacingContext.outcome_hint` — still hold/advance/transition from scene_motion + scene age + urgency.
- `PacingContext.beat_locked` — still dual trigger from consecutive pressure or momentum floor.
- `PacingContext.gate` — still `block_escalate`/`allow`, still gates thread_add in extraction.
- GM beat types — still complication, escalation, pressure, revelation, opportunity, breathing_room, twist, setback, callback.
- GM beat surfaces — still ambient, event, npc_behavior, environmental, player_discovery, item.
- Thread lifecycle — still auto-latent at 3 turns, still urgency decay at 8 turns, still cap at 5 active.
- 5-call pipeline — still ruling → narrate → scene extract → state extract → storytell.
- Ruling bands — still crit_fail, fail, setback, partial, success, crit_success.
- Dice resolution — still 1d12 + stat_mod + diff_mod, still in Python.
- Narrator system prompt — still second person, still player input is truth, still never repeat prior narration.
- Storyteller system prompt — still JSON output, still thread operations, still beat guidance.
- Save format — still state.yaml + events.jsonl + chronicle.md.
- Event schema — still one JSON line per turn, still contains ruling, narrate, extraction, applied, rejected fields.

## New Model Shapes

### PacingContext (simplified)

```python
@dataclass
class PacingContext:
    directive: str          # "Breathe" | "Pressure" | "Move the scene" | "Resolve a Threat" | ""
    outcome_hint: str | None  # "hold" | "advance" | "transition"
    gate: Literal["block_escalate", "allow"]
    beat_locked: bool       # Python-only: floor relief + thread cap
```

### EngineConfig (removed fields)

The following fields are removed from EngineConfig:
- `scene_pressure_threshold: int = 3`
- `scene_imperative_threshold: int = 4`
- `momentum_pacing_factor: float = 0.5`

The `thread_deescalate_on_success: bool = True` field is [OPEN: keep or remove?].

## Context for Implementing LLMs

Before starting any plan, read these files:

- `ccya/engine/turn.py` — contains `_compute_narrative_velocity()`, `_compute_narration_directive()`, `_compute_pacing_context()`, `PacingContext` dataclass, floor relief injection, gate enforcement, beat lifecycle
- `ccya/engine/config.py` — contains `EngineConfig` dataclass with pacing-related fields, `build_engine_config()` config loader
- `ccya/state/momentum.py` — contains `apply_momentum()`, momentum constants, depth-based catch-up acceleration
- `ccya/prompts/narrate_user.j2` — renders `outcome_hint`, `pending_beat`, does NOT render directive/gate/beat_locked/summary
- `ccya/prompts/storytell_user.j2` — renders `directive`, `outcome_hint`, `gate`, `pending_beat`, `recent_beats`
- `ccya/prompts/storytell_system.j2` — contains directive-to-beat mapping table, roll band-to-beat table, diversity rules
- `ccya/prompts/narrate_system.j2` — contains priority ordering, pacing guidance, NPC agency rules
- `ccya/ev/checkers/pacing.py` — pacing checker, references `consecutive_pressure_turns`, `outcome_hint`, `directive`, removed directives
- `ccya/ev/checkers/gm_beat.py` — beat checker, references `beat_locked`, floor relief, dual trigger, momentum floor
- `ccya/ev/checkers/momentum.py` — momentum checker, references `momentum_before`, `momentum_after`, `momentum_delta`, band deltas
- `docs/repomap.md` — module boundaries, cross-module contracts, pipeline overview
- `docs/architecture/OVERVIEW.md` — pipeline mechanics, data models, flowcharts
