# Plan 02: Narrative Velocity

## Status
completed

**Replaces:** `deescalate` float + `momentum` integer as separate inputs

---

## Problem

`deescalate` and `momentum` are both inputs to `narrate_user.j2` that answer the same question: *how fast and in what emotional direction should the narration be moving right now?*

`momentum` is an integer (range roughly -5 to +3) representing the player's recent streak. It drives two distinct behaviors:
- High positive: "raise the stakes"
- Low negative: "give them a visible out" (with a hard floor at -3)

`deescalate` is a float (0.0–1.0) representing "a pressure just resolved, calm down". It's the only way the system currently says "the narrator should breathe."

In `narrate_user.j2`, these two inputs are rendered in separate blocks with separate Jinja logic, and they can conflict: a player at momentum -3 with `deescalate=0.8` gets both "give them an out" and "breathe" — redundant signals with no priority rule between them. In `extract_progress_user.j2`, `deescalate` is used to gate beat generation. In `narrate_user.j2`, it's the primary driver of the `Breathe` directive.

They need to be one thing.

---

## Solution

Replace both with a single signed float: **`narrative_velocity`**.

```
 narrative_velocity: float, range -1.0 to +1.0

  +1.0  = full escalation (multiple immediate threats, player on a run)
   0.0  = neutral (hold pace, normal narration)
  -1.0  = full deescalation (pressure just resolved, give them air)
```

This is a **computed value**, not a model output — the engine calculates it from the same inputs that previously produced `momentum` and `deescalate` separately.

### Computation

```python
def compute_narrative_velocity(
    momentum: int,
    deescalate: float,
    scene_pressure: list[ScenePressure],
) -> float:
    """
    Returns narrative_velocity in [-1.0, +1.0].
    deescalate dominates when >= 0.5 (a meaningful resolution happened).
    """
    if deescalate >= 0.5:
        # Strong deescalation — clamp to negative range
        # 0.5 → -0.3, 1.0 → -1.0
        return -deescalate

    immediate_count = sum(
        1 for p in scene_pressure if p.urgency == PressureUrgency.IMMEDIATE
    )

    # Normalize momentum: clamp to [-5, +3], map to [-0.6, +0.4]
    mom_norm = max(-5, min(3, momentum)) / 5.0  # [-1.0, +0.6]

    # Pressure contribution: each immediate pressure adds +0.15, capped at +0.4
    pressure_contrib = min(immediate_count * 0.15, 0.4)

    # Partial deescalate (< 0.5) softens velocity
    deesc_dampener = deescalate * 0.5  # 0.0–0.25

    raw = mom_norm + pressure_contrib - deesc_dampener
    return max(-1.0, min(1.0, raw))
```

---

## Template changes

### `narrate_user.j2` — replace two blocks with one

**Remove** the existing momentum block:
```jinja2
{# REMOVE #}
{% set m = momentum | default(0) %}
{% if m >= 2 %}
**Momentum:** HIGH (+{{ m }}). ...
{% elif m <= -3 %}
**Momentum FLOOR ({{ m }}):** ...
{% elif m <= -2 %}
**Momentum LOW ({{ m }}):** ...
{% endif %}
```

**Remove** the existing deescalate block that produces `Breathe`:
```jinja2
{# REMOVE — this is now handled by narrative_velocity #}
{% if deescalate %}
**Narration Directive:** Breathe
{% elif scene_pressure and not deescalate %}
...
```

**Replace both** with a single section. Extract to `sections/_velocity.j2`:

```jinja2
{# sections/_velocity.j2 #}
{# narrative_velocity: -1.0 (full deescalate) to +1.0 (full escalate) #}
{% if narrative_velocity is defined %}
{% set v = narrative_velocity %}
{% if v <= -0.5 %}
**Narration Directive: Breathe** — A pressure resolved. Pull back. Quiet and relief. No new hook.
{% elif v <= -0.1 %}
**Narration Directive: Ease** — Things are settling. Slightly lower the temperature. A moment of pause is fine.
{% elif v >= 0.8 %}
**Narration Directive: Overwhelm** — Multiple immediate threats. Focus on the most pressing. Don't address everything.
{% elif v >= 0.4 %}
**Narration Directive: Pressure** — Active threat(s) present. Keep them felt. Don't resolve prematurely.
{% elif v >= 0.1 %}
**Narration Directive: Tension** — Danger building. Show it in environment and NPC behavior, not explicit new threats.
{% endif %}
{% if v <= -0.6 %}
{# At velocity floor: guarantee a visible out #}
**Velocity floor:** The player has been struggling. If they attempt retreat, rest, or de-escalation, give it to them — 
not as a full resolution, but as breathing room. One thing should ease.
{% endif %}
{% endif %}
```

In `narrate_user.j2`, replace the two removed blocks with:
```jinja2
{% include "sections/_velocity.j2" %}
```

Note: `Breathe` is now a threshold on `narrative_velocity`, not a separate Jinja variable. `Overwhelm` is now also driven by this scalar rather than the manual immediate-count logic that was scattered in the pressure block. The `scene_pressure` urgency block (from Plan 01) still renders the threat list — this section handles *only* the pacing directive.

---

## Extractor changes (`extract_progress_user.j2` and system)

The extractor currently uses `deescalate` to gate beat generation. Replace that with `narrative_velocity`:

```jinja2
{# In extract_progress_user.j2, replace: #}
{% if deescalate > 0 -%}
## deescalate
A pressure resolved this turn (magnitude: {{ "%.1f"|format(deescalate) }}).
...
{% endif -%}

{# With: #}
{% if narrative_velocity is defined and narrative_velocity < -0.1 -%}
## narrative_velocity
Velocity: {{ "%.2f"|format(narrative_velocity) }} (de-escalating). 
{% if narrative_velocity <= -0.5 -%}
Strong deescalation. Prefer `breathing_room` beat type or no beat. Do not add new immediate pressures.
{% else -%}
Partial deescalation. Prefer low-urgency beat or no beat.
{% endif %}
{% endif -%}
```

In `extract_progress_system.j2`, update the `gm_beat` guidance:

```
`gm_beat`:
- `narrative_velocity <= -0.5` → prefer `breathing_room` or null (no beat)
- `narrative_velocity` between -0.5 and 0.0 → low-urgency beat acceptable
- `narrative_velocity >= 0.4` with active pressure → `pressure` or `escalation`
- Recent `twist` or `callback` beats should not repeat within 2 turns
```

(Previously referenced `deescalate > 0.5` — replace all such references with `narrative_velocity <= -0.5`.)

---

## Python payload changes

In `build_narrate_payload()` and `build_extract_progress_payload()`:

```python
# Before
payload["momentum"]   = state.meta.momentum
payload["deescalate"] = deescalate_value

# After
payload["narrative_velocity"] = compute_narrative_velocity(
    momentum=state.meta.momentum,
    deescalate=deescalate_value,
    scene_pressure=state.scene.scene_pressure,
)
# momentum and deescalate are no longer passed to templates
# (they can remain on state for internal use / display)
```

`momentum` and `deescalate` stay on the state object — they're still useful internally for tracking and computing future velocity. They just stop being passed to LLM templates as separate inputs.

---

## System prompt changes (`narrate_system.j2`)

Update the `## Narration directives` section:

- Remove `Breathe` as a standalone entry — it's now emitted by the velocity template section
- Remove `Overwhelm` — same
- Remove `Tension` and `Pressure` from the static list — these are now emitted dynamically
- Keep `Combat Fatigue`, `Threat Pressure`, `Resolve a Threat` — those are still separately managed and unaffected by this plan
- Add a single preamble note:

```
## Narration directives

The user prompt provides zero or one Narration Directive per turn. Follow it exactly.
Directives are set by the engine — do not infer or substitute a different directive.

- **Breathe** — A pressure resolved. Pull back. Quiet and relief. No new hook or threat.
- **Ease** — Things settling. Lower the temperature slightly. A moment of pause is acceptable.
- **Tension** — Danger building. Show it in environment and NPC behavior — no new explicit threats yet.
- **Pressure** — Active immediate threat(s). Keep them present and felt.
- **Overwhelm** — Multiple immediate threats. Focus on the most pressing. Don't address everything.
- **Combat Fatigue** — Fight has run long. Bring to decisive close — one side prevails, flees, or is incapacitated.
- **[PACING]** — (from scene pressure list) Structural demand. The story must move. See pressure list for specifics.
- **Threat Pressure** — A background threat has been lingering. Acknowledge it in the scene. No need to resolve.
- **Resolve a Threat** — The oldest threat has been active too long. Resolve it naturally. Do NOT introduce a new threat.
```

Note: `Velocity floor` instruction is emitted inline by `_velocity.j2` when triggered — it does not need a definition in the system prompt.

---

## What gets deleted

- `momentum` as a template variable (stays on state, removed from payload)
- `deescalate` as a template variable (stays on state, removed from payload)
- Inline momentum Jinja block in `narrate_user.j2`
- Inline deescalate/Breathe Jinja block in `narrate_user.j2`
- Inline deescalate block in `extract_progress_user.j2`
- `Breathe`, `Overwhelm`, `Tension`, `Pressure` as static definitions in `narrate_system.j2` directives section (replaced by velocity-driven dynamic emission)

---

## New section file summary

| File | Purpose |
|------|---------|
| `sections/_velocity.j2` | Renders the single velocity-derived narration directive |
| `sections/_scene_pressure.j2` | (From Plan 01) Renders the threat list — kept separate |

The directive and the threat list are different things and stay in different sections. `_velocity.j2` says *how fast*; `_scene_pressure.j2` says *what threats*.

---

## Migration

No saved-game state migration needed. `momentum` and `deescalate` remain on the state object — they're still computed as before, just not passed through to templates. The velocity computation wraps them transparently. Old saves that load into the new code will have `narrative_velocity` computed fresh on the next tick.
