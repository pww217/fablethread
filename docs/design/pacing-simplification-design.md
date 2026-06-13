# Pacing Simplification Design

## Purpose

Design authority for collapsing CCYA's four interlocking pacing systems into a single deterministic pass. This doc defines what changes, what stays, and what the target state looks like — implementers should not deviate from the decisions recorded here.

## Problem Statement

The pacing system is four state machines that all read and write each other's state across five computation phases in a single turn:

- `_compute_narrative_velocity()` reads momentum + deescalate + avoidance → writes narrative_velocity
- `_compute_narration_directive()` reads narrative_velocity + urgency + ages → writes directive
- `_compute_pacing_context()` reads directive + deescalate + momentum + consecutive_pressure + scene_motion → writes PacingContext struct
- Ruling phase writes deescalate (feeds narrative_velocity + gate)
- Post-extraction writes consecutive_pressure (feeds beat_locked next turn)

The result is a PacingContext struct with 5 fields and a floor-relief injection that has to re-derive half the same logic. The LLMs see only `outcome_hint` and `directive` and `gate` — the engine does 100 lines of computation to produce 3 prompt variables. Most of the intermediate variables (`narrative_velocity`, `deescalate`, `_ages`) are never persisted, never logged in the event stream, and exist only to feed the next step.

## Constraints

- Momentum (integer -3 to +3) must remain — it's the only deterministic dice-band feedback the player sees
- GM Beats (`pending_gm_beat` + `recent_beats`) must remain — storyteller output, not engine-computed
- Thread lifecycle urgency counts must remain — they feed the directive
- Prompt templates (narrate_user.j2, storytell_user.j2, _thread_list.j2) can be reordered but the variables they reference must stay stable unless explicitly renamed in this doc
- Floor relief injection (breathing_room when beat_locked without momentum crisis) is working correctly — only the condition evaluation should be simplified, not removed
- No backwards compatibility — old saves may have stale PacingContext fields; treat missing fields as neutral defaults

## Non-goals

- Not changing momentum deltas or the band→delta table
- Not changing how GM Beats flow through extraction
- Not changing thread lifecycle constraints (auto-latent, urgency decay, cap eviction)
- Not changing prompt template content or structure — only the variables fed to them
- Not changing save/load format for state — only the (unpersisted) PacingContext struct

## Decision Table

| Decision | What | Why |
|---|---|---|
| Eliminate narrative_velocity as intermediate | Directive computation reads momentum + deescalate + avoidance directly | Velocity was only consumed by directive; removing it collapses one computation pass and removes an unlogged variable that was source of confusion |
| Eliminate deescalate as separate variable | Gate reads outcome.band + urgent threads directly; directive reads the same condition directly | Deescalate was an intermediate float that existed only to be threshold-checked by gate and negated by velocity; both consumers can read the raw signals |
| Merge PacingContext into one computation pass | `_compute_pacing_context()` absorbs directive + velocity + ages into itself; no more pre-computation calls | The current 3-phase pipeline (velocity → directive → pacing_context) can be one function since nothing between them reads external state |
| Gate condition becomes forward-looking: "are urgent threads present AND non-negative momentum?" | Instead of "did you just succeed against urgent threads" | Retroactive gate is the root bug of TICK-44 — it blocks after success when threads should be *added* |
| Remove `summary` from PacingContext | Only used for logging; can be derived from the other fields in the log call site | Eliminates a field that was always redundant (summary = directive + beat_locked joined) |
| Keep `beat_locked` as a bool computed from consecutive_pressure OR momentum_floor | No change to trigger logic | It works correctly and is used by both directive (appends "; Resolve a Threat") and floor relief |

## Open Questions

- [OPEN: should the gate become an enum with more states, or stay binary?] If binary, "allow" is the forward-open state and "block" fires when momentum is negative AND there are urgent threads (escalation is already happening, don't pile on).
- [OPEN: what happens to `avoidance`?] Currently it feeds narrative_velocity → directive (pushes toward Breathe). Should this instead become a direct flag on the outcome that the directive check reads?

## Current State — What Exists

### Computation Pipeline (one turn)

```
Ruling phase:
  outcome.band → apply_momentum(state.pc.momentum)
  outcome.band + urgent threads → deescalate (0.0 | 0.6 | 1.0)

Step 0.5 (between ruling and narrate):
  deescalate + momentum + avoidance → narrative_velocity (via _compute_narrative_velocity)
  narrative_velocity + urgency + ages → directive (via _compute_narration_directive)
  directive + deescalate + momentum + consecutive_pressure + scene_motion + ages → PacingContext (via _compute_pacing_context)

Post-extraction:
  pending_gm_beat type → consecutive_pressure_turns counter
  beat_locked + NOT momentum_crisis + (beat is None or pressure-type) → floor relief injection
```

### PacingContext struct (current)

```
PacingContext:
  directive: str        # computed from velocity + urgency + ages
  outcome_hint: str     # computed from scene_motion + ages + impossible + beat_locked
  beat_locked: bool     # computed from consecutive_pressure OR momentum
  gate: str             # computed from deescalate
  summary: str          # computed from directive + beat_locked
```

One of these five fields (`summary`) is derived entirely from others. Two more (`directive`, `outcome_hint`) share the same age/urgency inputs. The struct has no reason to carry 5 fields when 3 would cover the same information.

### What LLMs Actually See

| Prompt | Variables from PacingContext |
|---|---|
| narrate_user.j2 | `outcome_hint` |
| narrate_system.j2 | none (only prose guidance about `pending_gm_beat`) |
| storytell_user.j2 | `directive`, `outcome_hint`, `gate` |
| storytell_system.j2 | none (prose guidance mapped from directive) |

The narrator needs exactly 1 field from PacingContext. The storyteller needs 3. The `beat_locked` field is consumed only by the engine (floor relief + directive secondary text). The `summary` field is consumed only by logging.

### Problems with Current State

- **Three computation passes where one would do.** `_compute_narrative_velocity` → `_compute_narration_directive` → `_compute_pacing_context` are called sequentially with no intervening state mutation. The first two produce intermediate values consumed only by the third.
- **Deescalate computes twice.** The condition "success + urgent threads" is evaluated in the ruling phase (to set deescalate) and then implicitly again by the gate (deescalate >= 0.5). The same boolean logic runs in two places.
- **Gate is retroactive.** It blocks after success when threads should be added. This is the TICK-44 root cause.
- **Narrative velocity formula is misleading.** It doesn't model "velocity" as a continuous signal — it's a priority switch: deescalate beats avoidance beats momentum. The name implies a scalar that should be accumulated across turns, but it's recomputed fresh every turn from the same inputs.
- **`_ages` dict is recomputed twice.** `_compute_ages()` runs once for ctx._ages, then again inside `_compute_narration_directive()` and `_compute_pacing_context()`.

## Proposed Solution

### Core Changes

**1. Collapse three passes into one.**

Replace `_compute_narrative_velocity`, `_compute_narration_directive`, and `_compute_pacing_context` with a single function `compute_pacing(...)` that takes the raw inputs (momentum, outcome, urgent_threads, consecutive_pressure, scene_motion, ages, avoidance) and returns a PacingContext struct.

The directive computation reads momentum and the outcome directly instead of going through a velocity intermediate. The gate reads the outcome and urgent threads directly instead of reading deescalate.

**2. Gate becomes forward-looking.**

```
gate = "block" if momentum < 0 and urgent_threads > 0 else "allow"
```

Rationale: if momentum is negative (player is losing) and there are urgent threats, don't let the storyteller add more — the player is already overwhelmed. If momentum is non-negative, let threads through. This inverts the current logic where gate blocks on *success*.

This means the `thread_deescalate_on_success` config key is no longer needed — the gate is no longer tied to successful rolls.

**3. Remove `summary` from PacingContext.**

The log call site can format `f"{directive}, beat_locked={beat_locked}"` instead. The struct carries 4 fields instead of 5.

**4. Compute ages once, pass explicitly.**

`_compute_ages()` is called once in the ruling phase. The ages dict is passed to `compute_pacing()` as a parameter, not recomputed internally.

### Alternatives Considered and Rejected

- **Rip out the gate entirely.** Rejected because the gate serves a real purpose: preventing thread pile-on when the player is already losing. The fix is to make it forward-looking, not to remove it.
- **Keep deescalate as a concept but rename it.** Rejected because the variable had exactly one meaningful value (>= 0.5) and one computation site. Merging its two consumers (velocity and gate) into direct signal reads eliminates the variable without adding complexity.
- **Make PacingContext a frozen dataclass with computed fields.** Rejected because FrozenInstanceError at runtime is worse than the current mutability. Simpler to build the struct in one pass and return it.
- **Remove `beat_locked` from PacingContext, compute it in place at both consumption sites.** Rejected because beat_locked is read by four different call sites (directive, floor relief, event logging, summary); centralizing the bool is cheaper than four identical condition evaluations.

## Failure Modes and Risks

- **Gate now blocks on negative momentum + urgent threads instead of success + urgent threads.** This changes the behavioral profile of the gate significantly. In a pressure cycle where the player is failing, the gate will stay closed longer. This is intentional — the player is under pressure, don't bury them — but it may produce different emergent patterns than the current system.
- **The gate no longer fires on non-urgent successes.** Previously, success with no urgent threads produced deescalate=0.0 → gate="allow". In the new system, non-negative momentum with no urgent threads also produces gate="allow". Same result.
- **The gate no longer fires at all on success with urgent threads.** This is the intentional fix for TICK-44 — success against urgent threads should be when the storyteller *can* add threads (to reflect the narrative consequence of succeeding against pressure).
- **Eliminating `narrative_velocity` means losing the avoidance path to Breathe.** The current system routes avoidance → velocity = -0.4 → directive = Breathe (if velocity < -0.3). This path needs to be preserved either as a direct check in the directive function or as a band input. [OPEN: choose which.]

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `narrative_velocity` (float) | `turn.py` computation pipeline | No replacement — directive reads raw inputs directly |
| `deescalate` (float, TurnContext._deescalate) | `turn.py` ruling phase | Merged into gate + directive checks |
| `summary` (str, PacingContext field) | `turn.py` PacingContext struct | Inline formatting at log call site |
| `narrative_velocity` (result field) | `_narrate_setup()` return tuple | Caller no longer needs it |
| `thread_deescalate_on_success` (config bool) | `config.py` | Gate is no longer tied to success |
| `_compute_narrative_velocity()` | `turn.py` | Logic merged into `compute_pacing()` |
| `_compute_narration_directive()` | `turn.py` | Logic merged into `compute_pacing()` |
| `narrative_velocity_pacing_factor` config key | `docs/architecture/pacing-systems.md` | Renamed to `momentum_pacing_factor` in source, but the source field `momentum_pacing_factor` stays |

## What Is Unchanged

- `MOMENTUM_DELTA` table in `rules.py` — band → delta mapping stays
- `apply_momentum()` in `state/momentum.py` — band → state.pc.momentum mutation stays
- `PacingContext` dataclass (except removing `summary`) — `directive`, `outcome_hint`, `beat_locked`, `gate` stay with same types
- `PacingContext.neutral()` factory — still returns default context
- `_compute_ages()` — still called once per turn; signature unchanged
- `PRESSURE_BEAT_TYPES` — same tuple, same consumers
- Beat lifecycle in extraction phase — expiry → replace → floor relief → pressure counter → history snapshot, unchanged
- Floor relief injection condition — same logic, just reads from the new `compute_pacing()` result
- Thread add gate enforcement in `turn.py:1235` — same site, reads from new PacingContext.gate value
- All prompt templates — variables they read (`directive`, `outcome_hint`, `gate`, `pending_beat`, `recent_beats`) are stable

## New Model Shapes

```python
@dataclass
class PacingContext:
    directive: str          # "Breathe" | "Scene Imperative" | "Overwhelm" | "Pressure" | "Tension" | "Scene Pressure" | "" (may include "; Resolve a Threat" when beat_locked)
    outcome_hint: str | None  # "hold" | "advance" | "transition"
    beat_locked: bool       # True when consecutive_pressure >= threshold OR momentum <= floor
    gate: Literal["block", "allow"]  # "block" when momentum < 0 and urgent threads > 0; "allow" otherwise
```

No `summary` field. `gate` values change from "block_escalate"/"allow" to "block"/"allow" (shorter, same meaning).

Config key `thread_deescalate_on_success` is removed. Config key `momentum_pacing_factor` stays but is no longer used by any pacing function (it was only consumed by `_compute_narrative_velocity`). It can be cleaned up in a follow-up once every reference to it is verified removable.

## Context for Implementing LLMs

- `ccya/engine/turn.py` — remove `_compute_narrative_velocity()` (lines 410-442), remove `_compute_narration_directive()` (lines 445-508), rewrite `_compute_pacing_context()` (lines 511-584) to absorb both, remove deescalate logic (lines 710-717), update `_narrate_setup()` (lines 761-841) to call new function
- `ccya/prompts/storytell_user.j2` — confirm gate value "block" vs "block_escalate" renders correctly in _thread_list.j2
- `ccya/prompts/sections/_thread_list.j2` — update gate string match for "block" instead of "block_escalate"
- `docs/architecture/pacing-systems.md` — rewrite to reflect single-pass computation, remove sections on narrative_velocity/deescalate
- `docs/architecture/step0-ruling.md` — remove deescalate discussion from PacingContext section
