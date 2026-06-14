# Pacing Directive & Beat Constraint Overhaul

## Purpose

Design authority for plans that rewire how pacing directives (Scene Imperative, Scene Pressure, Breathe) interact with beat-type constraints and outcome hints (hold/advance/transition), fixing the death-spiral loop where a player gets stuck in the same scene with compounding pressure beats.

## Problem Statement

The existing pacing system has three directives (Breathe, Scene Pressure, Scene Imperative) and three outcome hints (hold, advance, transition). Scene Imperative fires correctly when a scene is stale (age >= 4), and `outcome_hint` can be "transition" when the scene must end. But these signals are only **text hints in the LLM prompt** — the hard beat-type constraints are gated exclusively by scene phase (SETUP/RISING/CRISIS/RESOLUTION/BREATHER). When Scene Imperative fires while the scene phase is RISING (which allows `pressure`, `complication`, `escalation`), the LLM can and does select beats that compound the player's situation rather than breaking the loop. The result is a death spiral: the system says "break the loop" but the tools it gives the LLM keep tightening the vice.

## Constraints

- No changes to thread management, thread forcing, or thread resolution logic. Pacing only.
- No new config knobs unless required by a decision below. Simplicity > configurability.
- The three pacing directives + three outcome hints are the vocabulary. Do not add new directives or hints.
- Scene phase (SETUP/RISING/CRISIS/RESOLUTION/BREATHER) and its transitions remain unchanged.
- The beat type taxonomy (9 types) remains unchanged.
- Must not regress existing behavior for normal (non-spiral) scenes.

## Non-goals

- Thread forcing, thread lifecycle changes, or thread-level resolution forcing. Not touching threads.
- Condition counting or condition-based signals. Use roll difficulty band history instead.
- New beat types, new surfaces, or new scene phases.
- Changes to how actions are generated or how the narrator works.
- Arc-level pacing or arc resolution changes.
- New config UI or save-state migration. Config additions must be minimal and backward-compatible.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Beat constraints are filtered by directive | When Scene Imperative fires, `derive_allowed_beat_types()` restricts beats to scene-changing types regardless of scene phase. When Breathe fires, restrict to calming/de-escalation beats. Scene Pressure and empty directive use existing phase-based constraints unchanged. | The root cause: Scene Imperative says "break loop" but allows pressure/complication beats that compound the problem. Directives must be able to override the phase-based default. |
| Death spiral detection uses roll difficulty history | Track the last N roll bands. If X+/N are "hard" or above, or if the same band repeats Y+ consecutive turns, the spiral flag activates. | Conditions can be positive or negative, making them ambiguous. Roll difficulty is a clean binary signal: the player is struggling. |
| Spiral flag → override beat constraints | When spiral flag is active (and no Scene Imperative has already triggered), `derive_allowed_beat_types()` is called with `spiral=True` which excludes pressure/escalation/complication and adds `opportunity`, `revelation`, `twist`. | The spiral means the player is overwhelmed — more pressure beats make it worse. They need a way out, not another wall. Spiral is weaker than Scene Imperative (Scene Imperative already forces transition). |
| `outcome_hint` does NOT constrain beats, but amplifies the directive's effect | outcome_hint remains a text prompt to the LLM. Only the directive triggers hard beat constraints. However, when outcome_hint is "transition" AND Scene Imperative fires, the beat filter is stricter (only `revelation`, `twist`, `opportunity` — no `escalation` or `callback`). | outcome_hint comes from the ruling engine (LLM's own scene_motion judgment) and is less reliable than the code-computed directive. Giving it hard-constraint power would let a bad LLM judgment lock out necessary beats. |
| Breathe directive restricts beats to de-escalation | When Breathe fires, allowed beats become `["breathing_room", "callback", "revelation", "opportunity"]` — no pressure, no complication, no escalation. | Breathe means the scene is de-escalating. Letting it still allow pressure beats contradicts the directive's purpose. |
| Scene Pressure uses phase defaults unchanged | Scene Pressure is a soft warning (age >= 3). No hard beat constraints needed — the phase map already handles this via RISING/CRISIS progression. | Scene Pressure is not a strong enough signal to warrant override. Only Scene Imperative, Breathe, and spiral get special treatment. |

## Open Questions (Resolved)

- [RESOLVED: Roll window = 5 turns, threshold = 3/5 hard or 3 consecutive hard. "Hard" is the floor — "extreme" alone is too rare to be reliable. Matches `recent_beats` window convention.]
- [RESOLVED: Spiral flag affects both narrate and storytell pipelines. Narrate gets a soft nudge ("write an exit vector"); storytell gets the hard beat constraint. Low cost: pass `spiral_detected` into `_narrate_messages()` same way as `pacing_context`.]
- [RESOLVED: Non-instant decay. `spiral_decay_turns: int = 2` — two non-hard rolls to clear the flag. Single-turn decay is too aggressive (one lucky roll clears the help).]
- [RESOLVED: Scene Imperative at SETUP age 4 is genuinely stale and should fire unconditionally. Phase-agnostic backstop is correct. No conditional softening — more edge-case complexity than the problem warrants.]
- [RESOLVED: Breathe + avoidance keywords are already handled by `tension_delta == "de-escalates"`. The avoidance keyword list feeds into tension_delta computation. No change needed unless play-testing shows it's not firing.]

(All open questions resolved.)

## Current State — What Exists

### Directive computation (`turn.py:409-445`)

Priority stack:
1. **Breathe** — `tension_delta == "de-escalates" AND thread_urgency_count == 0`
2. **Scene Imperative** — `(CRISIS AND crisis_turn_count >= crisis_turn_limit) OR effective_scene_age >= scene_imperative_threshold`
3. **Scene Pressure** — `effective_scene_age >= scene_pressure_threshold`
4. **empty** — default

Directives are mutually exclusive (priority stack). Only one fires.

### Outcome hint / scene_motion (`turn.py:475-480`, `models.py:175`)

- `scene_motion` is set by the ruling LLM in `IntentEnvelope`: `"hold"`, `"advance"`, or `"transition"`
- `outcome_hint` in `PacingContext` copies `scene_motion`, overridden to `"transition"` when CRISIS hits turn limit
- Outcome hint is rendered as text in both narrate and storytell prompts, with narrative guidance for each value

### Beat constraints (`_pacing.py:13-19`)

| Phase | Allowed beats |
|---|---|
| SETUP | all 9 types |
| RISING | pressure, complication, escalation, revelation, twist |
| CRISIS | pressure, escalation, complication |
| RESOLUTION | breathing_room, callback, revelation |
| BREATHER | opportunity, revelation, callback, breathing_room, hazard |

Plus `enforce_relief` override: when CRISIS has >= 3 consecutive pressure beats, only `breathing_room`.

### Data flow

```mermaid
flowchart LR
    R[Ruling step] -->|scene_motion, tension_delta| TC[Turn._compute_pacing_context]
    S[Scene state] -->|scene_phase, effective_scene_age| TC
    TC -->|directive, outcome_hint| N[Narrate prompt]
    TC -->|directive, outcome_hint| ST[Storytell prompt]
    P[_pacing.py] -->|allowed_beat_types by phase| ST
    
    subgraph Beat selection in storytell
        ST -->|phase: RISING, allowed: pressure/complication/...| LLM
        N -->|"outcome: transition"| LLM
        LLM -->|gm_beat: {type: "complication"}| B[beat output]
    end
```

### Problems with Current State

1. **Scene Imperative allows compounding beats**: Scene Imperative fires at age >= 4, but the beat constraint table is read from scene phase only. If phase is RISING (which it usually is by age 4), the allowed beats include `pressure`, `complication`, `escalation` — the exact beats that keep the player stuck. The prompt text tells the LLM "break the loop" but offers no mechanical constraint to enforce it. Scene Imperative's purpose and the available beat palette are contradictory.

2. **No death-spiral detection**: The system has no signal for "the player is losing repeatedly." `consecutive_pressure_beats` tracks one dimension (did the LLM pick pressure beats?), not roll outcomes. A player can fail 5 rolls in a row and nothing in the pacing system notices.

3. **Breathe directive has no teeth**: When Breathe fires, the prompt text says the scene de-escalates, but the beat constraints are still phase-dependent. Breathe can fire during RISING and still allow `pressure`/`escalation`. The directive is contradicted by the available beats.

4. **`enforce_relief` is the only directive-aware beat constraint, and it's too narrow**: It only fires in CRISIS with 3+ consecutive pressure beats, and only forces `breathing_room`. It doesn't handle the more common case: stale RISING scene with compounding beats.

## Proposed Solution

### Core Changes

#### 1. `derive_allowed_beat_types()` gains directive and spiral awareness

New signature:
```python
def derive_allowed_beat_types(
    scene_phase: str,
    *,
    directive: str = "",
    enforce_relief: bool = False,
    spiral_detected: bool = False,
) -> list[str]:
```

Logic (priority order):
1. If `directive == "Scene Imperative"`: return `["opportunity", "revelation", "twist"]`. Rationale: the scene MUST change. These beats create change — a new path forward, a reveal that recontextualizes the situation, or an inversion of the status quo. Escalation was the problem beat; it does not belong in the exit list.
2. If `directive == "Breathe"`: return `["breathing_room", "callback", "revelation", "opportunity"]`. Rationale: de-escalation beats only.
3. If `spiral_detected` (and no directive override above): start from phase-based defaults, then remove `pressure`, `complication`, `escalation`. Add `opportunity`, `revelation`, `twist` if not already present. Rationale: break the spiral without forcing scene exit.
4. If `enforce_relief` and `scene_phase == "CRISIS"`: return `["breathing_room"]` (existing behavior, unchanged).
5. Otherwise: return `BEAT_PHASE_MAP.get(scene_phase, ...)` (existing behavior, unchanged).

Priority hierarchy within the function: Scene Imperative > Breathe > spiral > enforce_relief > phase defaults.

#### 2. Death spiral detection based on roll difficulty

New function in `_pacing.py`:
```python
def detect_spiral(
    recent_rolls: list[RollRecord],
    consecutive_hard_threshold: int = 3,
    hard_ratio_threshold: tuple[int, int] = (3, 5),
) -> bool:
    """Return True if the player is in a death spiral based on roll outcomes.

    A spiral is detected when:
    - X+ consecutive rolls are "hard" or worse, OR
    - Y+/Z recent rolls are "hard" or worse
    """
```

Where `RollRecord` is a simple dataclass/holder tracking the band per turn. The turn pipeline already has `rules_outcome` — just need to collect the band and pass it to `_pacing.py`.

The threshold constants go in `EngineConfig`:
- `spiral_consecutive_hard: int = 3` — consecutive hard rolls to trigger
- `spiral_hard_ratio: tuple[int, int] = (3, 5)` — 3 of last 5 hard rolls to trigger

#### 3. Wire directive and spiral into the call site

In `extraction.py:275-282`, the call to `derive_allowed_beat_types` currently passes only `scene_phase` and `enforce_relief`. It needs to also pass:
- `directive` from `pacing_context.directive`
- `spiral_detected` from the new spiral detection function

#### 5. Timing: when spiral is computed in the turn pipeline

The pipeline order for a single turn is:

```
1. _ruling_phase()           → produces rules_outcome (roll band)
2. Append roll band to state.meta["recent_rolls"]
3. _compute_scene_phase()    → determines scene phase
4. _compute_pacing_context() → produces directive + outcome_hint
5. _compute_spiral_detected()→ reads recent_rolls, emits bool
6. narrate pipeline          → receives spiral_detected flag
7. extraction / storytell    → receives spiral_detected, calls derive_allowed_beat_types()
```

**The current turn's roll counts same-turn.** RulesOutcome is available before `_compute_pacing_context()` runs, so the spiral flag is computed from recent_rolls that *includes* this turn's roll. This means a third consecutive hard roll on turn 10 immediately constrains beats on turn 10 — the player doesn't have to suffer another turn before the system responds.

`recent_rolls` is stored in `state["meta"]["recent_rolls"]` as a capped list of `{"turn": N, "band": "hard"}` dicts (max 5 entries). Appended in the turn runner right after `_ruling_phase()` returns. Only turns with a `rolled=True` outcome produce an entry — non-roll turns are skipped and do not decay the window.

The spiral flag is computed in a new function `_compute_spiral_detected()` called just before the narrate pipeline. It reads `state["meta"]["recent_rolls"]` and checks the configured thresholds. The flag is stored in the `TurnContext` (the `_ctx` dataclass) so both narrate and storytell pipelines can read it without recomputing.

`PacingContext` gains an optional `spiral_detected: bool = False` field so the flag is logged and visible to checkers and debugging tools, but the primary carrier is the turn context object.

#### 4. Prompt template changes

- `storytell_system.j2`: Update the phase-beat constraint table to note that directives can override it. Add a section explaining the spiral mechanic: "When a spiral is detected (repeated hard rolls), the system restricts beats to non-pressure types to provide an exit vector."
- `storytell_user.j2`: No structural changes needed — it already renders `allowed_beat_types` from the computed list. The restriction happens upstream.
- `narrate_user.j2`: If `spiral_detected` is passed, add a brief hint: "The player is in a downward spiral. Write an exit vector — a way through, a revelation, or a shift in circumstances." Kept minimal; the narrator's job is narration, not beat selection, so the nudge is soft.
- `narrate_user.j2`: No changes. outcome_hint text guidance is already adequate.

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Make outcome_hint ("transition") a hard beat constraint | outcome_hint comes from the ruling LLM (LLM's own judgment of scene_motion). Using it as a hard constraint gives a single LLM call veto power over the beat system. The ruling LLM could incorrectly set "transition" on turn 2, locking out escalation beats needed for tension. The directive (code-computed from age/phase) is a more reliable signal. |
| Use condition count as spiral signal | Conditions can be positive (buffed, inspired, protected) or negative. Counting them conflates good and bad states. Roll difficulty is a direct measure of struggle. |
| Thread forcing as spiral breaker | Out of scope for this design. The pacing system should create the opportunity for scene change; threads are a separate concern. Thread forcing would be a follow-up if pacing fixes aren't sufficient. |
| Add a new directive (e.g., "Spiral Breaker") | The existing three directives + spiral flag cover the space. A fourth directive would require priority-stack changes and more prompt text. Using a boolean flag (`spiral_detected`) that modifies beat constraints without becoming a directive is simpler. |
| Track roll *values* (not bands) | Raw roll totals are noisy — a 4 vs a 7 on a normalized check can both be "normal" difficulty. Bands (success/fail/hard/extreme) are the canonical outcome classification. The band is already computed and stored. |

## Failure Modes and Risks

- **Over-correction**: If the spiral threshold is too low, the system floods the player with opportunity beats and removes tension. Mitigation: threshold config knobs default conservatively (3 consecutive hard, 3/5 ratio). Spiral flag decays on a single non-hard roll.
- **LLM ignores the restricted beat set**: The LLM can still emit any beat type via `gm_beat.type`. The constraint is a prompt instruction + the "allowed beat types" line in the user prompt. If the LLM routinely ignores this, the fix must move to structured output / JSON schema enforcement. For now, trust the prompt instruction given that the existing enforce_relief mechanism works the same way.
- **Conflict with enforce_relief**: If both Scene Imperative and enforce_relief fire (possible in CRISIS), Scene Imperative wins (priority 1 in the function). enforce_relief only matters when no directive overrides it. This is correct: a scene that must end should not be held in breathing_room.
- **Spiral + Scene Pressure**: Scene Pressure (age >= 3) does not restrict beats. If spiral fires at the same time, the spiral flag restricts beats. This is fine — Scene Pressure is a soft warning, spiral is a hard signal.
- **Roll band history storage**: Need to add a field to state meta or turn context for the rolling window. Existing `recent_beats` is a good model. A `recent_rolls: list[dict]` field, capped at 5 entries, storing `{"turn": N, "band": "hard"}` per turn where a roll happened. Turns without rolls don't add entries.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| (nothing removed — only additions) | | |

## What Is Unchanged

- Scene phase definitions and transition logic (SETUP → RISING → CRISIS → RESOLUTION, BREATHER)
- The three directives (Breathe, Scene Pressure, Scene Imperative) and their priority stack
- The three outcome hints (hold, advance, transition) and their narrative guidance in prompt templates
- The 9 beat types and their taxonomy
- The `enforce_relief` mechanism in CRISIS (still works, just lower priority than directive/spiral)
- All thread logic, arc logic, NPC logic, inventory logic
- Config fields: `scene_pressure_threshold`, `scene_imperative_threshold`, `consecutive_pressure_threshold`, `crisis_turn_limit`, all scene phase thresholds
- The narrate pipeline entirely
- The storytell output schema and action generation

## New Model Shapes

```python
# In _pacing.py or a new models sub-module

@dataclass
class RollRecord:
    """A single roll outcome for spiral detection."""
    turn: int
    band: str  # "crit_success" | "success" | "partial" | "fail" | "hard" | "extreme"
    skill: str  # which stat was rolled
```

```python
# In config.py additions

# Spiral detection
spiral_consecutive_hard: int = 3        # N consecutive hard+ rolls triggers spiral
spiral_hard_ratio: tuple[int, int] = (3, 5)  # M of last N hard+ triggers spiral
spiral_decay_turns: int = 2             # non-hard rolls to clear spiral flag
```

```python
# In PacingContext (models.py or turn.py)

@dataclass
class PacingContext:
    directive: str
    outcome_hint: str | None
    spiral_detected: bool = False
    summary: str
```

## Context for Implementing LLMs

- `ccya/engine/_pacing.py` — Current `BEAT_PHASE_MAP`, `derive_allowed_beat_types()`, `derive_enforce_relief()`. Entry point for all beat constraint logic.
- `ccya/engine/turn.py:409-490` — `_compute_narration_directive()` and `_compute_pacing_context()`. How directives and outcome hints are produced.
- `ccya/engine/turn.py:99-109` — `PacingContext` dataclass. The structure that carries directive + outcome_hint through the pipeline.
- `ccya/engine/config.py:140-170` — Existing pacing threshold config. Where new spiral config fields go.
- `ccya/engine/extraction.py:260-290` — Call site for `derive_allowed_beat_types()`. Where directive and spiral flag get wired in.
- `ccya/prompts/storytell_system.j2:49-76` — Phase→beat constraint table, Scene age backstop guidance. Needs directive/spiral awareness added.
- `ccya/prompts/storytell_user.j2:30-31` — Renders `allowed_beat_types`. No change needed here — it auto-adopts the filtered list.
- `ccya/models.py:168-176` — `IntentEnvelope` with `scene_motion`. Reference only (no change).
