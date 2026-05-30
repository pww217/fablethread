# Impossible Action Gating + Pacing Outcome Hints

## Status
`completed`

## Phases

2 phases: Phase 1 adds impossible action detection to the ruling LLM and synthesizes a failure outcome when actions are impossible. Phase 2 adds scene motion judgment to the ruling LLM and replaces PacingContext.directive with outcome_hint as the narrator's primary scene-motion signal.

## Issue

Two structural problems cause the majority of narrative quality failures in the CCYA engine. First, the narrator permits impossible actions — a player fires a gun with no ammo, attempts actions they lack resources for, or targets things not present in the scene. The narrator prompt already instructs the LLM to verify inventory before narrating item usage (`narrate_system.j2:24`), but the LLM ignores this self-supervision instruction because it has too many competing concerns and no hard pre-established fact blocking the action. Second, the narrator defaults to preparation prose and repetitive scene continuity. PacingContext sends tone directives (`"Breathe"`, `"Pressure"`, `"Overwhelm"`) but never an outcome — "Pressure" tells the narrator how the scene *feels* but not what should *happen*. The LLM mimics the style of its recent turns, so three turns of setup beget a fourth.

## Solution

Add fields to `IntentEnvelope` (`impossible`, `impossible_reason`, `scene_motion`) that the ruling LLM populates alongside its existing intent classification. When `impossible=true`, Python skips `resolve_check()` and synthesizes a `RulesOutcome` with `band="fail"` or `"crit_fail"`. The narrator receives this as a hard fact it cannot ignore. Separately, add `outcome_hint` to `PacingContext` — computed from the ruling LLM's `scene_motion` and PacingContext escalation signals — replacing `directive` as the narrator's primary scene-motion instruction. The narrator receives a concrete outcome to narrate toward (`"hold"`, `"advance"`, or `"transition"`) rather than a tone word it can treat as optional flavor.

## Firm decisions

1. Ruling LLM judges impossibility — not Python. The LLM has context Python lacks (conditions, scene, intent). Avoids unreliable fuzzy-matching of `target` against inventory IDs.
2. Ruling LLM judges scene motion — not Python inferred from `intent_verb`. `intent_verb` is free-text, unreliable for Python logic.
3. No separate impossibility validation stage. Ruling already has the context; a separate call adds latency and scope creep.
4. Impossible actions get `band="fail"` or `"crit_fail"` — ruling LLM distinguishes honest mistake (fail) from absurd attempt (crit_fail). Python gates: only `{fail, crit_fail}` allowed for impossible actions, default to `fail`.
5. No `resource_costs` (pre-applying inventory costs). Reconciliation with extraction is fragile; extraction handles inventory well.
6. No `pre_rendered_constraints`. Reformatting conditions to prose doesn't solve the obedience problem.
7. No `contract_summary`. Redundant with `outcome_summary` and `recent_turns`.
8. `outcome_hint` replaces `directive` for the narrator. Narrator sees `outcome_hint`, not `directive`. Eliminates conflicting signals.
9. `directive` retained for storytell. Storytell needs tone vocabulary for beat selection and thread management.
10. Skip `resolve_check()` when `impossible=true`. No dice roll for impossible actions.
11. Momentum still applied on impossible actions. Band `fail` → -1, `crit_fail` → -2.
12. Existing `narrate_system.j2:24` inventory instruction retained (belt and suspenders).

## Non-goals

- Moving all inventory management to Python (extraction handles inventory well)
- Replacing storytell or extraction for narrative discoveries
- Pre-applying resource costs before narration
- Pre-rendering conditions as prose sentences
- Persisting contract summaries across turns
- Making Python a storyteller
- Changing how storytell uses PacingContext (gate, beat_locked, thread urgency signals remain unchanged)
- Adding narrator emotional texture tone words alongside outcome_hint (deferred to post-rollout evaluation)

## Risks, Ambiguities, and Blockers

- **Ruling LLM may omit `scene_motion` from JSON output.** The field defaults to `"hold"` via Pydantic. This is safe — the narrator continues at natural pace, and PacingContext escalation signals can still push `hold` → `advance` when pressure warrants it. No special fallback needed.
- **Narrator emotional texture loss.** The narrator no longer receives PacingContext tone words (`Pressure`, `Breathe`, etc.) — only `outcome_hint`. If post-rollout evaluation shows the narrator losing emotional nuance, a brief tone word can be added alongside `outcome_hint`. This is explicitly deferred.
- **`_compute_pacing_context()` signature change.** Adding `scene_motion` and `impossible` as inputs changes the function signature. All callers must be updated. Currently called once in `_narrate_setup()` (turn.py:983-988).
- **`apply_momentum()` is called in `_ruling_phase()` only when `outcome.rolled=True`** (turn.py:867-868). When `impossible=true` and `rolled=False`, momentum is NOT applied by the current code. This plan adds momentum application for impossible actions — the existing `apply_momentum()` call needs to be moved or an additional call added.

## Implementation — Phase 1: Impossible Action Gating

### Context files to load

- `ccya/models.py:155-176` — `IntentEnvelope` and `RulesOutcome` shapes
- `ccya/models.py:17-19` — `Band` type alias
- `ccya/engine/turn.py:776-870` — `_ruling_phase()` — where impossible detection and synthetic outcome go
- `ccya/engine/turn.py:970-1007` — `_narrate_setup()` — where PacingContext is computed and passed to narration
- `ccya/engine/ruling.py:16-47` — `_ruling_messages()` — prompt building for ruling
- `ccya/engine/ruling.py:50-127` — `_call_ruling()` — retry logic
- `ccya/rules.py:148-169` — `build_directive()` — used for synthesized impossible outcomes
- `ccya/rules.py:80-87` — `MOMENTUM_DELTA` — band-to-momentum mapping
- `ccya/state/momentum.py` — `apply_momentum()` — how momentum is applied
- `ccya/prompts/ruling_system.j2` — ruling prompt — adding impossibility check instruction + schema fields
- `ccya/prompts/narrate_user.j2:70-94` — rules_outcome rendering section (impossible block replaces elif branch)
- `ccya/prompts/narrate_system.j2:107-118` — static directive descriptions (unchanged in Phase 1; replaced in Phase 2)

### Detailed steps

#### Step 1.1 — Add `impossible` and `impossible_reason` to `IntentEnvelope` and `RulesOutcome`

**File:** `ccya/models.py`

**What:** Add two fields to `IntentEnvelope` (line 155-159):

```python
class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    impossible: bool = False          # NEW
    impossible_reason: str = ""       # NEW
```

Also add the same two fields to `RulesOutcome` (line 162-176):

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
    impossible: bool = False          # NEW
    impossible_reason: str = ""       # NEW
```

**Why:** `IntentEnvelope` carries the ruling LLM's impossibility judgment. `RulesOutcome` needs the same fields so the narrator prompt can access them via its existing `rules_outcome` context variable — no new context variable needed. Defaults ensure backward compatibility.

**Validation:** `python -c "from ccya.models import IntentEnvelope, RulesOutcome; e = IntentEnvelope(); r = RulesOutcome(); print(e.impossible, r.impossible)"` should print `False False`.

#### Step 1.2 — Add impossibility check instruction to ruling system prompt

**File:** `ccya/prompts/ruling_system.j2`

**What:** Insert a new section after the "Anti-declare-outcome rule" section (line 60), before the "Output schema" section (line 62):

```
## Impossibility check

After classifying intent, evaluate whether the described action is impossible given the character's state, inventory, and scene. An action is impossible when:

- It requires an item the character does not have (firing a gun with no ammo, using a key they never acquired)
- It requires a capability contradicted by active conditions (climbing with a broken leg, sneaking while armored and noisy)
- It acts on something not present in the scene (targeting an NPC who is not here, opening a door that doesn't exist)

If the action is merely difficult, risky, or unlikely — but not physically impossible — do NOT mark it impossible. Set `impossible=false` and classify the check normally.

If impossible: set `impossible=true`, write a brief reason in `impossible_reason`, and set `check.required=false`. The narrator will handle the failure — you do not need to determine the band.
```

Update the output schema JSON (line 62-72) to include the new fields:

```json
{
  "intent": "",
  "intent_verb": "",
  "target": "",
  "impossible": false,
  "impossible_reason": "",
  "check": {
    "required": boolean,
    "skill": "",
    "difficulty": ""
  }
}
```

**Why:** The ruling LLM needs explicit instructions and schema fields to judge impossibility. The instruction distinguishes impossible from merely difficult, and tells the LLM to set `check.required=false` when impossible.

**Validation:** Render the ruling prompt and verify the new sections appear. `python -c "from ccya.engine.config import _build_jinja_env; env = _build_jinja_env('ccya/prompts'); from ccya.engine.config import _render; print(_render(env, 'ruling_system.j2', {}))"` — check for "Impossibility check" section.

#### Step 1.3 — Synthesize `RulesOutcome` when `impossible=true`

**File:** `ccya/engine/turn.py`

**What:** Modify `_ruling_phase()` (line 776). After `intent` is returned from `_call_ruling()` (line 824-826) and before the existing `if intent.check.required` block (line 834), add an `if intent.impossible:` branch that:

1. Forces `intent.check.required = False` (ensures the existing roll block is skipped)
2. Calls `build_directive()` with `band="fail"` (or `"crit_fail"` if the ruling LLM signals absurdity)
3. Synthesizes a `RulesOutcome` with `rolled=False`, the chosen band, the directive, `impossible=True`, and `impossible_reason=intent.impossible_reason`
4. Calls `apply_momentum(state, band)` (normally only called when `outcome.rolled=True`)
5. Logs at INFO level with `trace_id`, `turn`, `pack`, `kind` context keys

The existing `if intent.check.required and intent.check.skill:` block (line 834-847) will not execute because `intent.check.required` is forced to `False`.

**Why:** When an action is impossible, there's nothing to roll. Python synthesizes a `RulesOutcome` with `rolled=False` and `band="fail"` so downstream systems (momentum, PacingContext, narrator) receive a valid outcome. Momentum is applied because an impossible action has consequences.

**Validation:** When `impossible=true`, `resolve_check()` should not be called, `outcome.rolled` should be `False`, `outcome.band` should be `"fail"`, and `apply_momentum()` should have been called. Log line should appear in output.

#### Step 1.4 — Add impossible action block to narrator system prompt

**File:** `ccya/prompts/narrate_user.j2`

**What:** Add a Jinja2 block before the "This Turn's Result" section (before line 70). Also modify the existing `elif rules_outcome and not rules_outcome.rolled` block (lines 75-77) to exclude impossible actions:

Replace lines 70-82:

```jinja2
## This Turn's (Turn {{ meta.get('turn', '?') if meta is mapping else '?' }}) Result
{% if rules_outcome and rules_outcome.impossible %}

**IMPOSSIBLE:** This action cannot succeed — {{ rules_outcome.impossible_reason }}.
Narrate the attempt and its natural failure. Do NOT write a version where the action succeeds.
{% elif rules_outcome and rules_outcome.rolled %}

**Band:** {{ rules_outcome.band | upper | replace('_', ' ') }} → {{ rules_outcome.directive }}

{% elif rules_outcome and not rules_outcome.rolled %}

**No roll required.** Describe what happens with appropriate weight for the moment.
{% endif %}
{% if rules_outcome and rules_outcome.rolled -%}

**rules_outcome (BINDING)** — This turn had a mechanical outcome. Do not ignore, override, or undermine the resolved band and directive above. The band result is authoritative for what happens next.
{%- endif %}
```

**Why:** `rules_outcome` is only available in the user prompt context (`narrate_user.j2`), not the system prompt. The system prompt is rendered with only `{pack_style, narrator_rules, world_rules, current_arc}` (see `narrate.py:104-109`). Adding the impossible block to `narrate_system.j2` would silently fail — the `{% if %}` would always be False. Additionally, when `impossible=True` and `rolled=False`, the existing `elif` block would show "No roll required" which is incorrect for impossible actions. The new `if rules_outcome.impossible` branch takes priority over the `elif not rules_outcome.rolled` branch, ensuring the narrator sees the IMPOSSIBLE fact instead of the generic "No roll required" message.

**Validation:** Render the narrator user prompt with `rules_outcome.impossible=True, rules_outcome.impossible_reason="no ammo"` and verify the IMPOSSIBLE block appears with the reason. Render with `impossible=False` and verify it does not appear. Verify `narrate_system.j2` is NOT modified in Phase 1.

### Tests to write or update

Tests are temporarily removed during refactor. No tests to write per AGENTS.md.

### REPOMAP updates required

- `docs/repomap.md` — Update `IntentEnvelope` and `RulesOutcome` field lists to include `impossible` and `impossible_reason`. Update ruling pipeline description to note impossibility gating. Update narrator prompt section to note impossible action block.

---

## Implementation — Phase 2: Pacing Outcome Hints

**Dependency:** Phase 1 must be completed first. Phase 2 builds on the `impossible` field and the modified `_ruling_phase()` from Phase 1.

### Context files to load

- `ccya/models.py:155-159` — `IntentEnvelope` shape (Phase 1 already added `impossible`)
- `ccya/engine/turn.py:129-139` — `PacingContext` dataclass — field being added
- `ccya/engine/turn.py:659-711` — `_compute_pacing_context()` — where `outcome_hint` logic goes
- `ccya/engine/turn.py:970-1007` — `_narrate_setup()` — where PacingContext is passed to narration
- `ccya/engine/narrate.py:19-43` — `_narrate_messages()` — where `pacing_context` enters narration
- `ccya/prompts/ruling_system.j2` — ruling prompt — adding scene motion instruction + schema field
- `ccya/prompts/narrate_system.j2:107-118` — static directive descriptions (to be removed)
- `ccya/prompts/narrate_user.j2:91-94` — PacingContext directive rendering (to be replaced with outcome_hint)
- `ccya/prompts/storytell_system.j2:64-74` — Storytell PacingContext guidance (unchanged, read for context)
- `ccya/prompts/storytell_user.j2:35-38` — Storytell PacingContext rendering (unchanged)

### Detailed steps

#### Step 2.1 — Add `scene_motion` to `IntentEnvelope`

**File:** `ccya/models.py`

**What:** Add `scene_motion` field to `IntentEnvelope`:

```python
class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    impossible: bool = False
    impossible_reason: str = ""
    scene_motion: Literal["hold", "advance", "transition"] = "hold"  # NEW
```

**Why:** The ruling LLM judges scene motion (`hold`, `advance`, `transition`) alongside impossibility. This is more reliable than Python inferring from `intent_verb` (free-text). Default `"hold"` is safe — if the LLM omits it, the narrator continues at natural pace.

**Validation:** `python -c "from ccya.models import IntentEnvelope; e = IntentEnvelope(); print(e.scene_motion)"` should print `hold`.

#### Step 2.2 — Add scene motion instruction to ruling system prompt

**File:** `ccya/prompts/ruling_system.j2`

**What:** Add scene motion section after the impossibility check section (added in Phase 1), before the output schema:

```
## Scene motion

After classifying intent, determine how the scene should progress this turn:

- "hold" — the action doesn't move the story to a new situation. The scene continues at its current pace. Most routine actions are "hold".
- "advance" — something significant is happening or resolving this turn. The narrator should narrate through to the outcome, not dwell on setup or preparation. Key signals: a decisive action, a confrontation reaching its climax, a discovery that changes the situation.
- "transition" — the player is leaving this location or situation entirely. The narrator should write the arrival at the new place, not the departure from the old one. Key signals: travel, escape, entering a new area, scene change.

Set `scene_motion` based on the player's intent and the current scene dynamics, not based on dice outcomes (those are resolved separately).
```

Update the output schema to include `scene_motion`:

```json
{
  "intent": "",
  "intent_verb": "",
  "target": "",
  "impossible": false,
  "impossible_reason": "",
  "scene_motion": "hold",
  "check": {
    "required": boolean,
    "skill": "",
    "difficulty": ""
  }
}
```

**Why:** The ruling LLM needs explicit instructions and a schema field to judge scene motion. The instruction distinguishes the three motion types and tells the LLM to base its judgment on intent and scene dynamics, not dice outcomes.

**Validation:** Render the ruling prompt and verify the scene motion section appears. Check that the output schema includes `scene_motion`.

#### Step 2.3 — Add `outcome_hint` to `PacingContext` and compute it

**File:** `ccya/engine/turn.py`

**What:** Three changes:

**A. Add `outcome_hint` to `PacingContext` dataclass** (line 129-139):

```python
@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str  # Retained for storytell
    outcome_hint: str | None  # NEW — narrator's primary scene motion instruction
    beat_locked: bool
    gate: Literal["block_escalate", "allow"]
    summary: str

    @staticmethod
    def neutral() -> PacingContext:
        return PacingContext(directive="", outcome_hint="hold", beat_locked=False, gate="allow", summary="neutral")
```

**B. Modify `_compute_pacing_context()`** (line 659-711) to accept `scene_motion` and `impossible` as inputs and compute `outcome_hint`:

New signature:
```python
def _compute_pacing_context(
    deescalate: float,
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
    threat_ages: list[dict[str, Any]] | None,
    momentum: int,
    config: "EngineConfig",
    consecutive_pressure_turns: int = 0,
    scene_motion: str = "hold",       # NEW
    impossible: bool = False,          # NEW
) -> PacingContext:
```

Compute `outcome_hint` after computing `directive` and `beat_locked` (move `beat_locked` computation before `outcome_hint`), then compute `outcome_hint` using this priority:

1. `scene_motion="transition"` → `"transition"`
2. `scene_motion="advance"` → `"advance"`
3. `impossible=true` → `"advance"`
4. Scene Imperative (effective_age >= config.threat_imperative_at) → `"advance"`
5. `beat_locked=True` → `"advance"`
6. directive in ("Overwhelm", "Pressure") with 1+ urgent threads → `"advance"`
7. Default → `"hold"`

Update the `return PacingContext(...)` call to include `outcome_hint`.

**C. Update the caller** at `_narrate_setup()` (line 983-988) to pass `scene_motion` and `impossible`:

```python
_pc = _compute_pacing_context(
    deescalate=ctx._deescalate, narrative_velocity=narrative_velocity,
    scope_scene_threads=_scope_scene_threads, ages=ctx._ages,
    threat_ages=ctx._threat_ages, momentum=(state.get("pc") or {}).get("momentum", 0), config=config,
    consecutive_pressure_turns=(state.get("meta") or {}).get("consecutive_pressure_turns", 0),
    scene_motion=ctx.intent.scene_motion,       # NEW
    impossible=ctx.intent.impossible,           # NEW
)
```

**Why:** `outcome_hint` is computed from the ruling LLM's `scene_motion` and PacingContext escalation signals. The ruling LLM's judgment is primary; PacingContext can escalate `hold` to `advance` but cannot override `transition` or `advance` from the ruling LLM.

**Validation:** `_compute_pacing_context()` should return a `PacingContext` with `outcome_hint` set. When `scene_motion="transition"`, `outcome_hint` should be `"transition"`. When `scene_motion="hold"` and no escalation signals, `outcome_hint` should be `"hold"`.

#### Step 2.4 — Replace narrator directive rendering with outcome_hint

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace lines 91-94:

```jinja2
{%- if pacing_context and pacing_context.directive -%}

**Directive:** {{ pacing_context.directive }}
{% endif %}
```

With:

```jinja2
{%- if pacing_context and pacing_context.outcome_hint -%}

**Outcome:** {{ pacing_context.outcome_hint }}
{% if pacing_context.outcome_hint == "advance" %}Narrate through to the resolution. Do not linger on preparation or setup. Something significant happens this turn.{% elif pacing_context.outcome_hint == "transition" %}Write the arrival at the new location, not the departure from this one. The scene moves forward.{% elif pacing_context.outcome_hint == "hold" %}Continue the current scene at its natural pace.{% endif %}
{% endif %}
```

**Why:** The narrator receives `outcome_hint` instead of `directive`. `outcome_hint` is a concrete scene-motion instruction rather than a tone word. This eliminates the conflicting signals problem.

**Validation:** Render the narrator user prompt with `outcome_hint="advance"` and verify the Outcome block appears with the advance guidance. Render with `outcome_hint="hold"` and verify the hold guidance appears. Verify `directive` no longer appears.

#### Step 2.5 — Remove static directive descriptions from narrator system prompt

**File:** `ccya/prompts/narrate_system.j2`

**What:** Remove lines 107-118 (the "## Narration directives" section with descriptions of Breathe, Overwhelm, Pressure, Tension, Scene Pressure, Scene Imperative, Threat Pressure, Resolve a Threat).

Replace with a brief note:

```
## Scene outcome

The user prompt provides a single Outcome instruction for this turn: "hold" (continue at natural pace), "advance" (something significant happens, narrate through to resolution), or "transition" (the player is leaving, write the arrival). Follow it.
```

**Why:** The narrator no longer needs to know about the PacingContext tone vocabulary. It receives a concrete outcome instruction instead. The static directive descriptions are dead weight — they describe values the narrator no longer receives.

**Validation:** Render the narrator system prompt and verify the old directive descriptions are gone and the new "Scene outcome" section appears. Verify the prompt is shorter (fewer tokens).

### Tests to write or update

Tests are temporarily removed during refactor. No tests to write per AGENTS.md.

### Eval assertion updates required

- `ccya/eval/universal_asserts.py:565-610` — `directive_rendered` assertion checks that `pacing_context.directive` value appears in the narrate user prompt AND storytell user prompt. After this phase, the narrator no longer renders `directive` — it renders `outcome_hint` instead. This assertion must be updated:
  - For **narrator**: check for `outcome_hint` value (`hold`/`advance`/`transition`) rendered as `**Outcome:**` instead of `**Directive:**`.
  - For **storytell**: no change needed (`directive` is still rendered there unchanged).
  - Suggested: add a new assertion `universal.narrate.outcome_hint_rendered` that checks narrator prompt contains the outcome_hint value, and modify the existing `directive_rendered` assertion to only check storytell (or skip narrator check when outcome_hint is present).

### REPOMAP updates required

- `docs/repomap.md` — Update `IntentEnvelope` field list to include `scene_motion`. Update `PacingContext` to include `outcome_hint`. Update narrator prompt section to note `outcome_hint` replaces `directive`. Update `_compute_pacing_context()` signature to include new parameters.
