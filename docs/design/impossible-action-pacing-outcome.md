# Impossible Action Gating + Pacing Outcome Hints

## Motivation

Two structural problems cause the majority of narrative quality failures:

1. **The narrator permits the impossible.** A player fires a gun with no ammo, attempts actions they lack the resources for, or tries things the scene doesn't support. The narrator prompt already instructs: "Before narrating any item usage, verify the item appears in the inventory list" (`narrate_system.j2:24`). The LLM ignores this instruction — it has too many competing concerns and no hard pre-established fact blocking the action. Post-hoc extraction then tries to reconcile the impossible with state, producing phantom inventory deltas.

2. **Narrative inertia.** The narrator defaults to preparation prose and repetitive scene continuity. PacingContext sends tone directives (`"Breathe"`, `"Pressure"`, `"Overwhelm"`) but never an outcome. "Pressure" tells the narrator how the scene *feels* but not what should *happen*. The LLM mimics the style of its recent turns — three turns of setup beget a fourth. Providing a concrete outcome to narrate toward is a stronger signal than a tone directive, because LLMs comply with concrete facts more reliably than abstract instructions.

The root cause for both: the narrator currently holds both *creative authority* (what the scene feels like) and *outcome authority* (what actually happened). These should be separated. Python and the ruling LLM decide what is true; the narrator dramatizes it.

***

## Goals

- Prevent the narrator from permitting actions that are impossible given current state and scene
- Give the narrator an unambiguous outcome directive so scenes advance rather than linger
- Offload mechanical narrative structure from storytell to ruling, reducing storytell's burden
- Keep extraction doing what it's good at: location changes, NPC notes, bios, arc signals, emergent discoveries
- Minimal new code surface — two field additions to existing structs, prompt changes, one PacingContext refactor

## Non-Goals

- Moving all inventory management to Python (extraction handles inventory well)
- Replacing storytell or extraction for narrative discoveries
- Pre-applying resource costs before narration (cut — reconciliation with extraction is fragile)
- Pre-rendering conditions as prose sentences (cut — narrator already receives conditions as structured data; reformatting doesn't solve the obedience problem)
- Persisting contract summaries across turns (cut — redundant with `outcome_summary` and `recent_turns`)
- Making Python a storyteller
- Changing how storytell uses PacingContext (gate, beat_locked, thread urgency signals remain unchanged)

***

## Design

### 1. Impossible Action Gating

Add two fields to `IntentEnvelope` (`ccya/models.py:155-159`):

```python
class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    impossible: bool = False
    impossible_reason: str = ""
    scene_motion: Literal["hold", "advance", "transition"] = "hold"
```

**Ruling LLM judges impossibility and scene motion.** The ruling system prompt (`ruling_system.j2`) gains two instructions: after classifying intent, evaluate whether the action is physically or logically impossible, and determine how the scene should move this turn.

The ruling LLM is better suited for this than Python because:
- `intent_verb` and `target` are LLM outputs — fuzzy matching against inventory IDs in Python would be unreliable
- The LLM can judge context-dependent impossibility (broken leg preventing climbing) that Python can't detect
- The LLM can judge scene progression intent (is the player trying to leave? is this a turning point?) more reliably than Python inferring from `intent_verb`
- Ruling already receives `pc.conditions` and full `inventory` in its prompt (`ruling_user.j2:6,15-19`)

**Prompt instruction for ruling — impossibility.** Add to `ruling_system.j2`:

```
## Impossibility check

After classifying intent, evaluate whether the described action is impossible given the character's state, inventory, and scene. An action is impossible when:

- It requires an item the character does not have (firing a gun with no ammo, using a key they never acquired)
- It requires a capability contradicted by active conditions (climbing with a broken leg, sneaking while armored and noisy)
- It acts on something not present in the scene (targeting an NPC who is not here, opening a door that doesn't exist)

If the action is merely difficult, risky, or unlikely — but not physically impossible — do NOT mark it impossible. Set `impossible=false` and classify the check normally.

If impossible: set `impossible=true`, write a brief reason in `impossible_reason`, and set `check.required=false`. The narrator will handle the failure — you do not need to determine the band.
```

**Prompt instruction for ruling — scene motion.** Add to `ruling_system.j2`:

```
## Scene motion

After classifying intent, determine how the scene should progress this turn:

- "hold" — the action doesn't move the story to a new situation. The scene continues at its current pace. Most routine actions are "hold".
- "advance" — something significant is happening or resolving this turn. The narrator should narrate through to the outcome, not dwell on setup or preparation. Key signals: a decisive action, a confrontation reaching its climax, a discovery that changes the situation.
- "transition" — the player is leaving this location or situation entirely. The narrator should write the arrival at the new place, not the departure from the old one. Key signals: travel, escape, entering a new area, scene change.

Set `scene_motion` based on the player's intent and the current scene dynamics, not based on dice outcomes (those are resolved separately).
```

**When `impossible=true`, Python overrides the band.** No dice roll. `_ruling_phase()` in `turn.py` sets `outcome.band` to a value determined by the ruling LLM's context assessment:

The ruling LLM emits a normal `check` (with `required=false` when impossible). Python then synthesizes the `RulesOutcome` as if a roll occurred, but without actually rolling. The ruling LLM's `intent_verb` and existing context determine the band:

| Impossibility character | Default band | Rationale |
|---|---|---|
| Honest mistake (wrong item, out of ammo) | `fail` | Player tried something reasonable that just doesn't work |
| Absurd or reckless (punching a dragon, walking through walls) | `crit_fail` | Player attempted something obviously beyond reason |

Python gates this: if the ruling LLM emits `impossible=true` with `check.required=true` (contradiction), Python forces `check.required=false`. If the LLM emits a band outside `{fail, crit_fail}` for an impossible action, Python clamps it to `fail` as a safe default.

**No new LLM call.** Impossibility and scene motion are judged by the existing ruling call, in the same JSON response. Two additional fields for the smallest pipeline stage.

#### Routing through the pipeline

When `_ruling_phase()` returns with `impossible=true`:

1. `_ruling_phase()` skips `resolve_check()` — no dice roll
2. Python synthesizes `RulesOutcome` with `rolled=false`, `band=fail` or `crit_fail`, and an appropriate `directive` from `build_directive()`
3. Momentum is still applied — a `fail` band gives -1, a `crit_fail` gives -3 (per existing momentum rules in `ccya/state/momentum.py`)
4. PacingContext computation proceeds normally using the synthesized band
5. The narrator receives `impossible=true` and `impossible_reason` as hard facts, alongside the normal `RulesOutcome` and `outcome_hint`
6. Extraction and storytell are unaffected

#### Narrator prompt block for impossible actions

Added to `narrate_system.j2`:

```jinja2
{% if rules_outcome.impossible %}
FACT: This action cannot succeed — {{ rules_outcome.impossible_reason }}.
Narrate the attempt and its natural failure. Do NOT write a version where the action succeeds.
{% endif %}
```

This is placed as a hard fact, not a suggestion. The narrator retains creative authority over *how* the failure plays out — embarrassment, danger, revelation — but cannot invent a success.

#### Why this works better than the existing `narrate_system.j2:24` instruction

The current instruction at line 24 is a general prohibition: "verify the item appears in the inventory list." The LLM must actively check inventory against every item it mentions — a self-supervision task it consistently fails. The new `impossible` flag inverts this: instead of asking the LLM to self-supervise (which it doesn't), Python + ruling pre-supervise and deliver a concrete fact the LLM must incorporate. LLMs comply with explicit facts more reliably than with self-check instructions.

### 2. Pacing Outcome Hints

**Replace PacingContext.directive as the narrator's primary scene motion signal with `outcome_hint`.**

Currently, `PacingContext` (defined in `ccya/engine/turn.py:129-139`) has four fields:

```python
@dataclass
class PacingContext:
    directive: str       # Tone: "Breathe" | "Scene Imperative" | "Overwhelm" | ...
    beat_locked: bool
    gate: Literal["block_escalate", "allow"]
    summary: str         # Never sent to LLM
```

The change adds one field and restructures the narrator's relationship to directive:

```python
@dataclass
class PacingContext:
    directive: str           # Retained for storytell (becat selection + thread guidance)
    outcome_hint: str | None # New. Narrator's primary scene motion instruction
    beat_locked: bool
    gate: Literal["block_escalate", "allow"]
    summary: str
```

**`outcome_hint` values:**

| Value | Meaning | When computed |
|---|---|---|
| `"hold"` | Scene continues at its natural pace. No forced advancement. | Default — no urgency signals and `scene_motion="hold"` |
| `"advance"` | Something significant is happening or resolving. Narrate through to the outcome, not more setup. | Scene Imperative conditions, beat_locked, `impossible=true`, consecutive pressure, or `scene_motion="advance"` |
| `"transition"` | The player is leaving this location. Write arrival at the new location, not departure. | `scene_motion="transition"` |

**Computation logic.** `outcome_hint` is computed inside `_compute_pacing_context()` from two sources: the ruling LLM's `scene_motion` field and PacingContext signals. The ruling LLM's `scene_motion` is the primary input; PacingContext signals can escalate `hold` to `advance` but cannot override `transition` or `advance` from the ruling LLM.

Priority (highest to lowest):
1. `scene_motion="transition"` from ruling → `"transition"` (PacingContext cannot override a ruling that the player is leaving)
2. `scene_motion="advance"` from ruling → `"advance"` (ruling says this is a turning point)
3. `impossible=true` → `"advance"` (a failed attempt is still scene motion)
4. Scene Imperative (effective_age ≥ 5) → `"advance"` (scene has overstayed)
5. beat_locked → `"advance"` (force resolution)
6. "Overwhelm" or "Pressure" with 1+ urgent threads → `"advance"` (escalation)
7. `scene_motion="hold"` + no pressure signals → `"hold"`
8. Default → `"hold"`

"Breathe" no longer produces `"hold"` explicitly — `"hold"` is simply the absence of escalation signals. Breathing/relief is conveyed by storytell's beat selection, not by narrator pacing.

`outcome_hint` never conflicts with `directive` because they serve different consumers:
- **`outcome_hint`** → narrator (what happens)
- **`directive`** → storytell (how to manage threads and beats, tone for beat selection)
- **`gate`** and **`beat_locked`** → storytell only (unchanged)

The narrator no longer receives `directive` at all. `outcome_hint` replaces it as the narrator's single authoritative scene-motion signal.

#### Narrator prompt change

**Remove** from `narrate_user.j2:91-94`:
```jinja2
{%- if pacing_context and pacing_context.directive -%}
**Directive:** {{ pacing_context.directive }}
{% endif %}
```

**Replace with**:
```jinja2
{%- if pacing_context and pacing_context.outcome_hint -%}
**Outcome:** {{ pacing_context.outcome_hint }}
{% if pacing_context.outcome_hint == "advance" %}Narrate through to the resolution. Do not linger on preparation or setup. Something significant happens this turn.{% elif pacing_context.outcome_hint == "transition" %}Write the arrival at the new location, not the departure from this one. The scene moves forward.{% elif pacing_context.outcome_hint == "hold" %}Continue the current scene at its natural pace.{% endif %}
{% endif %}
```

The static directive descriptions currently in `narrate_system.j2` (lines 107-118: Breathe, Overwhelm, Pressure, etc.) should also be removed or replaced. The narrator no longer needs to know about the PacingContext tone vocabulary — it receives a concrete outcome instruction instead.

#### Storytell: unchanged

Storytell continues to receive the full `PacingContext` struct (directive, gate, beat_locked) via `storytell_user.j2:35-38`. No changes to storytell prompts or behavior. The `directive` field retains its current values and semantics for beat selection and thread guidance.

#### Why this fixes inertia

PacingContext's `directive` tells the narrator *how to feel*: "Pressure", "Overwhelm", "Breathe". These are tone instructions that the narrator treats as optional flavor. "Advance" tells the narrator *what happens*: something significant resolves this turn. This is a structural instruction — a fact about the scene's progression, not a suggestion about its mood. The narrator can still determine the emotional texture from context, prose history, and storytell beats, but the scene no longer has the option of not moving.

***

## Decision Table

| Decision | What | Why |
|---|---|---|
| Ruling LLM judges impossibility | Add `impossible` + `impossible_reason` to `IntentEnvelope` | LLM has context Python lacks (conditions, scene, intent). Avoids unreliable fuzzy-matching of `target` against inventory IDs. |
| Ruling LLM judges scene motion | Add `scene_motion` to `IntentEnvelope` | LLM can determine whether the player is trying to leave, advance, or stay better than Python inferring from `intent_verb`. `intent_verb` is free-text — unreliable for Python logic. |
| No separate impossibility validation stage | Ruling already has the context; a separate call adds latency and scope creep | Keep ruling focused; one inference task (is this possible?) is within its capacity |
| Impossible → `fail` or `crit_fail` (ruling LLM chooses) | Ruling LLM emits `check` normally; Python synthesize band from context | LLM can distinguish "honest mistake" (fail) from "absurd attempt" (crit_fail). Python gates: only `{fail, crit_fail}` allowed for impossible actions, default to `fail` |
| No `resource_costs` | Cut from original design | Pre-applying inventory costs creates reconciliation problem with extraction LLM. Extraction handles inventory well — the problem is narration, not state application |
| No `pre_rendered_constraints` | Cut from original design | Narrator already receives conditions and tags as structured data. Reformatting to prose doesn't solve the obedience problem; `impossible` flag does |
| No `contract_summary` | Cut from original design | Redundant with `outcome_summary` (already persisted in events) and `recent_turns` |
| No `TurnContract` dataclass | Fields merge into existing types | This is two field additions, not a new architecture. `impossible` on `IntentEnvelope`, `outcome_hint` on `PacingContext` |
| `outcome_hint` replaces `directive` for narrator | Narrator sees `outcome_hint`, not `directive` | Eliminates conflicting signals. Narrator gets one instruction about scene motion, not a tone it can ignore |
| `directive` retained for storytell | `PacingContext.directive` unchanged for storytell | Storytell needs tone vocabulary for beat selection and thread management. This is its correct consumer |
| Skip `resolve_check()` when `impossible=true` | No dice roll for impossible actions | The outcome is predetermined; rolling adds no information |
| Momentum still applied on impossible | Band `fail` → -1, `crit_fail` → -3 | Impossible actions should have consequences. A player who wastes a turn on an impossible attempt loses momentum |
| Existing `narrate_system.j2:24` inventory instruction | Retained, not removed | The `impossible` flag covers the common failure mode; the general instruction still covers edge cases the ruling LLM might miss. Belt and suspenders |

***

## What Changes

| Component | Change |
|---|---|
| `ccya/models.py` `IntentEnvelope` | Add `impossible: bool = False`, `impossible_reason: str = ""`, `scene_motion: Literal["hold", "advance", "transition"] = "hold"` |
| `ccya/engine/turn.py` `_ruling_phase()` | When `intent.impossible=true`: skip `resolve_check()`, synthesize `RulesOutcome` with `rolled=false`, `band=fail` or `crit_fail`, compute `directive` from `build_directive()` |
| `ccya/engine/turn.py` `_compute_pacing_context()` | Add `outcome_hint` computation from `scene_motion` (ruling) + PacingContext signals; accept `scene_motion` and `impossible` as inputs |
| `ccya/engine/turn.py` `PacingContext` dataclass | Add `outcome_hint: str \| None = None` |
| `ccya/engine/turn.py` `_narrate_setup()` | Pass `outcome_hint` instead of `directive` to narrator |
| `ccya/prompts/ruling_system.j2` | Add impossibility check instruction, scene motion instruction, and `impossible`/`impossible_reason`/`scene_motion` to output schema |
| `ccya/prompts/ruling_user.j2` | No change (already sends inventory, conditions, scene) |
| `ccya/prompts/narrate_system.j2` | Add `{% if rules_outcome.impossible %}` block; remove or replace static directive descriptions (lines 107-118) |
| `ccya/prompts/narrate_user.j2` | Replace `pacing_context.directive` rendering (lines 91-94) with `pacing_context.outcome_hint` |
| `ccya/engine/narrate.py` `_narrate_messages()` | Accept `outcome_hint` parameter or extract from `pacing_context.outcome_hint`; pass to template context |

## What Is Unchanged

| Component | Why unchanged |
|---|---|
| Extraction pipeline (`extraction.py`, `StateExtractResult`, `SceneExtractResult`) | Inventory extraction works well; the problem is narration permitting the impossible, not extraction misapplying deltas |
| Storytell pipeline (`storytell_system.j2`, `storytell_user.j2`) | Storytell continues to receive `directive`, `gate`, `beat_locked` — these are its correct inputs for beat selection and thread management |
| `ccya/state/delta.py` `apply_delta()` / `reconcile_delta()` | No new delta fields; impossible actions produce no inventory deltas that need reconciliation |
| `ccya/rules.py` `resolve_check()` / `build_directive()` | Still used for non-impossible actions. `build_directive()` is called for synthesized impossible outcomes |
| `ccya/state/momentum.py` `apply_momentum()` | Applied normally; band `fail` gives -1, `crit_fail` gives -3 |
| GM beat lifecycle | No changes. Storytell beats remain the same |
| Thread lifecycle | No changes |
| `TurnResult` | No structural changes (impossible and outcome_hint flow through existing channels) |
| `events.jsonl` format | Ruling event gains `impossible` and `impossible_reason` fields; no structural change |
| PacingContext for storytell | `directive`, `gate`, `beat_locked` passed unchanged |

***

## Model Shapes

### IntentEnvelope (after change)

```python
class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    impossible: bool = False          # NEW
    impossible_reason: str = ""       # NEW
    scene_motion: Literal["hold", "advance", "transition"] = "hold"  # NEW
```

`impossible` defaults to `False` and `scene_motion` defaults to `"hold"` so existing prompt outputs without these fields parse normally.

### PacingContext (after change)

```python
@dataclass
class PacingContext:
    directive: str            # Retained for storytell
    outcome_hint: str | None # NEW — narrator's primary scene motion instruction
    beat_locked: bool
    gate: Literal["block_escalate", "allow"]
    summary: str
```

### RulesOutcome (unchanged)

```python
class RulesOutcome(BaseModel):
    rolled: bool = False
    skill: str = ""
    stat_value: int = 0
    difficulty: str = "normal"
    stat_mod: int = 0
    diff_mod: int = 0
    cond_mod: int = 0
    dice: list[int] = Field(default_factory=list)
    raw_total: int = 0
    final_total: int = 0
    band: Band = "success"
    directive: str = ""
    intent_verb: str = ""
    intent: str = ""
```

When `impossible=true`, Python synthesizes: `rolled=False`, `band="fail"` or `"crit_fail"`, `directive` from `build_directive()`, remaining fields zeroed.

### Band values (existing, unchanged)

```python
Band = Literal["crit_fail", "fail", "setback", "partial", "success", "crit_success"]
```

Python gates impossible actions to `{fail, crit_fail}` only.

***

## Rollout Order

1. **`impossible` + `impossible_reason` on `IntentEnvelope`** — highest value, lowest risk. Add fields, update ruling prompt, add synthesization in `_ruling_phase()`, add narrator prompt block. No changes to storytell or extraction. Test: attempt actions with missing inventory items and verify narrator writes failure.
2. **`scene_motion` on `IntentEnvelope` + `outcome_hint` on `PacingContext`** — moderate implementation, highest narrative impact. Add `scene_motion` field to ruling, update ruling prompt, add `outcome_hint` computation in `_compute_pacing_context()`, replace narrator `directive` rendering with `outcome_hint`, remove static directive descriptions from `narrate_system.j2`. Test: observe whether scenes advance more reliably under `"advance"` and `"transition"` hints.
3. **Storytell optimization** (future) — once ruling provides outcome authority, evaluate whether storytell's beat disposition logic can be simplified. No changes in this rollout.

***

## Open Questions

- **Narrator emotional texture without tone directive.** The narrator no longer receives PacingContext tone words (`Pressure`, `Breathe`, etc.) — only `outcome_hint`. The narrator infers emotional texture from context, recent turns, and storytell beats. If post-rollout evaluation shows the narrator losing emotional nuance, a brief tone word can be added alongside `outcome_hint` (e.g., `**Outcome:** advance (high pressure)`). This is explicitly deferred to post-rollout evaluation — not included in the initial implementation.

- **`outcome_hint` default when ruling LLM doesn't emit `scene_motion`.** The field defaults to `"hold"`. If the ruling LLM occasionally omits `scene_motion` from its JSON output (which is possible — LLMs sometimes drop fields), the default is safe: the narrator continues at natural pace, and PacingContext escalation signals can still push `hold` → `advance` when pressure warrants it. No special fallback logic needed beyond the Pydantic default.

***

## Core Principle

LLMs are writers. Python is the GM. The ruling LLM is the GM's assistant — it decides what is possible. The narrator dramatizes what the GM decided. The contract between them is two fields: *is this possible?* and *what should happen this turn?* Everything else the narrator should figure out on its own.

***

## Context for Implementing LLMs

Files to read before starting:

| File | Why |
|---|---|
| `ccya/models.py:155-176` | `IntentEnvelope` and `RulesOutcome` shapes — fields being modified |
| `ccya/models.py:17-19` | `Band` type alias — impossible actions gated to `{fail, crit_fail}` |
| `ccya/engine/turn.py:129-139` | `PacingContext` dataclass — field being added |
| `ccya/engine/turn.py:659-711` | `_compute_pacing_context()` — where `outcome_hint` logic goes |
| `ccya/engine/turn.py:776-850` | `_ruling_phase()` — where impossible detection and synthetic outcome go |
| `ccya/engine/turn.py:983-1004` | Where PacingContext is computed and passed to narration |
| `ccya/engine/ruling.py:16-47` | `_ruling_messages()` — prompt building for ruling |
| `ccya/engine/ruling.py:50-127` | `_call_ruling()` — retry logic, will need to validate `impossible` field |
| `ccya/rules.py:148-169` | `build_directive()` — used for synthesized impossible outcomes |
| `ccya/engine/narrate.py:19-43` | `_narrate_messages()` — where `pacing_context` enters narration |
| `ccya/prompts/ruling_system.j2` | Ruling prompt — adding impossibility check instruction + schema fields |
| `ccya/prompts/narrate_system.j2:24,107-118` | Inventory instruction (retained) + static directive descriptions (to be removed/replaced) |
| `ccya/prompts/narrate_user.j2:91-94` | PacingContext directive rendering (to be replaced with outcome_hint) |
| `ccya/prompts/storytell_system.j2:64-74` | Storytell PacingContext guidance (unchanged, but read for context) |
| `ccya/prompts/storytell_user.j2:35-38` | Storytell PacingContext rendering (unchanged) |