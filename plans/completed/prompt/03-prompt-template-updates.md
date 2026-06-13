# Plan 3: Prompt Template Updates

## Purpose

Update all 5 prompt templates to reflect the new phase-driven pacing system: replace the old directive→beat mapping table with phase→beat constraints, remove `pacing_gate`/`pacing directive` references, and surface `scene_phase` and `allowed_beat_types` context to the storyteller.

## Problem Statement

The storyteller prompt still has a directive→beat mapping table (Breathe→`breathing_room`, Pressure→`complication`/`pressure`, Overwhelm→`pressure`/`escalation`, etc.) that references directives that no longer exist (Pressure, Overwhelm) and doesn't know about `scene_phase` at all. The narrator prompt references "pacing directive" as a priority concept that has been replaced by `outcome_hint`. The thread list template renders `gate == "block_escalate"` which is being deleted. All prompts need to surface `scene_phase` and phase-derived beat constraints.

## Constraints

- No new LLM calls — prompt context variables must come from existing pipeline state.
- `scene_phase` is already available in `narrate_user.j2` via `state.scene` (set at `narrate.py:89`). No Python changes needed for narrator context.
- `scene_phase` and `allowed_beat_types` are passed to storytell context by Plan 2 step 2.10 (`extraction.py`). Plan 3 assumes those context variables exist.
- All `gate` references can be removed from templates now (the field still exists on `PacingContext` but is always `"allow"` after Plan 2. Templates should stop rendering it.)

## Non-goals

- No Python-side changes — all prompt context wiring is done by Plan 2.
- No deletion of old prompt sections that reference old directive names if they're harmless (the LLM will ignore undefined directive names). But actively misleading references (Pressure/Overwhelm in the mapping table) must be replaced.
- No changes to `ruling_system.j2` — that was Plan 1.
- No changes to EV tools or server templates (`index.html`, `_turn_viewer.html`).

## Solution

Replace the directive→beat mapping table in `storytell_system.j2` with a phase→allowed beat types table driven by `scene_phase` and `allowed_beat_types` context variables. Remove `pacing_gate` display from `storytell_user.j2` and `_thread_list.j2`. Remove "pacing directive" priority reference from `narrate_system.j2`. Add `scene_phase` display to `narrate_user.j2` for narrator awareness.

## Firm decisions

1. **The old directive→beat table** (Breathe, Pressure, Overwhelm, Tension, Scene Imperative) is replaced by a phase→allowed beat types table (SETUP, RISING, CRISIS, RESOLUTION, BREATHER). The Scene Imperative row is subsumed by CRISIS + RESOLUTION phase logic.
2. **The roll-band table** (lines 59-66) is unchanged — it still governs beat selection when no phase overrides are active. It becomes the secondary beat constraint after the phase table.
3. **`pending_gm_beat` section** in `storytell_user.j2` is unchanged — beat lifecycle is already correct per the design doc.
4. **`recent_beats` section** in `storytell_user.j2` is unchanged — already renders correct beat history.
5. **`pacing_gate`** is removed from `_thread_list.j2` and `storytell_user.j2`. The `gate` field on `PacingContext` still exists (Plan 4) but is always `"allow"` — rendering it is misleading.

## Risks, Ambiguities, and Blockers

- The `allowed_beat_types` context variable passed from Plan 2 step 2.10 is a list of strings. The template renders it as a comma-separated list or bullet list. The storyteller system prompt must reference it clearly.
- The `scene_phase` context variable is a string ("SETUP", "RISING", "CRISIS", "RESOLUTION", "BREATHER"). Both storytell templates and the narrator should display it.

## Status

`completed`

## Phases

Single phase — all 5 templates are independent enough to edit in parallel, but they share the same `scene_phase` / `allowed_beat_types` / phase concept, so editing them together ensures consistency.

## Implementation — Prompt Template Updates

### Context files to load

- `ccya/prompts/storytell_system.j2` (93 lines) — directive→beat table (49-57), roll-band table (59-66), diversity guidance (72-74)
- `ccya/prompts/storytell_user.j2` (62 lines) — pacing_context rendering (25-29), thread gate (implicit via _thread_list.j2 include), pending_beat (30-44), recent_beats (40-43)
- `ccya/prompts/narrate_system.j2` (108 lines) — "pacing directive" reference (line 7), "Outcome directive" reference (line 83), "Pacing" section (79-83)
- `ccya/prompts/narrate_user.j2` (102 lines) — outcome_hint rendering (98-101), `state.scene` already available
- `ccya/prompts/sections/_thread_list.j2` (7 lines) — `gate == "block_escalate"` rendering (line 2)

### Detailed steps

#### Step 3.1 — Replace directive→beat table with phase→allowed beat types in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2` — lines 49-57

**What:** Replace the entire "Pacing directive takes precedence" section and its mapping table:

Old (lines 49-57):
```
**Pacing directive takes precedence** (from `pacing_context` in user turn):

| Directive | Beat |
|---|---|
| Breathe | `breathing_room` or `null` — do not add threads |
| Pressure | `complication` or `pressure` — update threads, don't add |
| Overwhelm | `pressure` or `escalation` — may add threads if gate allows |
| Tension | Follow roll band; no new threads unless concrete threat |
| Scene Imperative | Break the loop — force a decisive outcome (victory/defeat/retreat) or transition to a new scene. Follow the outcome_hint below. Do NOT add pressure/complication beats. |
```

New:
```
## Scene phase: `{{ scene_phase }}` — allowed: `{{ allowed_beat_types | join(", ") }}`

| Phase | Beat constraint |
|---|---|
| `SETUP` | All beat types available |
| `RISING` | pressure/complication/escalation/revelation/twist only |
| `CRISIS` | pressure/escalation/complication only — `enforce_relief` forces `breathing_room` |
| `RESOLUTION` | breathing_room/callback/revelation only |
| `BREATHER` | opportunity/revelation/callback/breathing_room/hazard only |

**Phase overrides roll band.** When `outcome_hint` is `"transition"`, prefer decisive, scene-ending beats.
```

**Why:** The old table referenced directives (Pressure, Overwhelm, Tension) that no longer exist after Plan 2. The new table is driven by `scene_phase`, which is the authoritative pacing primitive. The `allowed_beat_types` context variable gives the LLM the exact list of permissible types for this turn.

**Validation:** Render the template with `scene_phase="CRISIS"` and `allowed_beat_types=["pressure", "escalation", "complication"]` — the phase table shows CRISIS row, the allowed types list shows the three types.

#### Step 3.2 — Update "Stale scenes" paragraph in storytell_system.j2

**File:** `ccya/prompts/storytell_system.j2` — line 70

**What:** Update the Scene Imperative stale-scene guidance to reflect phase-driven logic:

Old:
```
**Stale scenes:** Scene Imperative fires when a scene has been stale for 5+ turns (7+ for combat). It means break the loop — force a decisive outcome or transition. Not more pressure beats. If outcome_hint is "transition", move to a new scene/location.
```

New:
```
**Scene age backstop:** When `effective_scene_age` exceeds the threshold, `Scene Imperative` fires. It means break the loop — force a decisive outcome or transition. Not more pressure beats. If outcome_hint is "transition", move to a new scene/location.
```

**Why:** Scene Imperative is no longer the primary pacing mechanism — it's a backstop when phase transitions stall. The guidance should reflect that phase is primary; Scene Imperative is the safety net.

**Validation:** Render with empty context — the new text is clear about Scene Imperative as backstop.

#### Step 3.3 — Update storytell_user.j2: add scene_phase, replace gate

**File:** `ccya/prompts/storytell_user.j2` — lines 25-29

**What:** Replace the `pacing_context` section:

Old (lines 25-29):
```
{% if pacing_context and (pacing_context.directive or pacing_context.gate or pacing_context.outcome_hint) %}
## pacing_context
Directive: {{ pacing_context.directive or "none" }}
Outcome: {{ pacing_context.outcome_hint or "hold" }}
Gate: {{ pacing_context.gate }}
{% endif %}
```

New:
```
{% if pacing_context and (pacing_context.directive or pacing_context.outcome_hint) %}
## pacing_context
Directive: {{ pacing_context.directive or "none" }}
Outcome: {{ pacing_context.outcome_hint or "hold" }}
{% endif %}
{% if scene_phase %}
## Scene phase: {{ scene_phase }} — allowed beat types: {{ allowed_beat_types | join(", ") }}
{% endif %}
```

`scene_phase` and `allowed_beat_types` are passed by Plan 2 step 2.10 in `_storytell_messages()`.

**Why:** The `Gate` field is always `"allow"` after Plan 2 — rendering it is misleading. `scene_phase` and `allowed_beat_types` are the new authoritative signals.

**Validation:** Render with `scene_phase="RISING"` and `allowed_beat_types=["pressure"]` (enforce_relief) — "Scene phase: RISING" line appears. Render with `scene_phase=None` — no phase line appears.

#### Step 3.4 — Remove `pacing_gate` from `_thread_list.j2`

**File:** `ccya/prompts/sections/_thread_list.j2` — line 2

**What:** Remove the gate block from the thread list header:

Old:
```
{% if threads %}
### Active Threads ({{ threads | length }} active — target: 3-4, ~5 total){% if gate and gate == "block_escalate" %} **Gate: blocked** — new threads will not be added this turn{% endif %}
```

New:
```
{% if threads %}
### Active Threads ({{ threads | length }} active — target: 3-4, ~5 total)
```

**Why:** `gate` no longer blocks thread adds — phase-derived `allowed_beat_types` in the storyteller system prompt is the gating mechanism. Rendering a gate that is always `"allow"` is noise.

**Validation:** Render with 3 threads — no "Gate:" text appears.

#### Step 3.5 — Update narrate_system.j2 "pacing directive" reference

**File:** `ccya/prompts/narrate_system.j2` — line 7

**What:** Replace "pacing directive" with "outcome hint" in the priority ordering:

Old:
```
**Priority ordering: player input > GM beat > pacing directive.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts. If no GM beat is present, narrate purely from the pacing directive and player input — no added pressure or relief beyond what the scene demands.
```

New:
```
**Priority ordering: player input > GM beat > outcome hint.** When a `pending_gm_beat` is present, integrate it as environmental pressure, NPC attitude, or scene atmosphere — NEVER as a replacement for the player's stated action. The player's action dictates what happens; the GM beat dictates how the world reacts. If no GM beat is present, narrate purely from the outcome hint and player input — no added pressure or relief beyond what the scene demands.
```

**Why:** "Pacing directive" is an obsolete concept. The narrator's authoritative scene signal is `outcome_hint` (rendered in narrate_user.j2).

**Validation:** grep for "pacing directive" in narrate_system.j2 — returns 0 matches after change.

#### Step 3.6 — Update narrate_system.j2 "Pacing" section

**File:** `ccya/prompts/narrate_system.j2` — lines 79-83

**What:** Minor update to the pacing section to remove "directive" language:

Old:
```
## Pacing

Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes.

Override rule: The Outcome directive and pending GM beat are authoritative scene signals. Do not override them because the prose feels like it should go a different direction.
```

New:
```
## Pacing

Each beat must advance the plot meaningfully. No holding patterns, no extended descriptions of static scenes.

Override rule: The outcome hint and pending GM beat are authoritative scene signals. Do not override them because the prose feels like it should go a different direction.
```

**Why:** Terminology consistency — "Outcome directive" → "outcome hint". This matches the rendered context variable name in narrate_user.j2.

**Validation:** grep for "Outcome directive" in narrate_system.j2 — returns 0 matches after change.

#### Step 3.7 — Add `scene_phase` display in narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2` — after the Scene Context section (~line 47), before Prior History

**What:** Add a one-line display of the current scene phase so the narrator has scene-state awareness:

```
{% if state and state.scene and state.scene.scene_phase %}
## Scene phase: {{ state.scene.scene_phase }}
{% endif %}
```

Insert after the `{% endif %}` on line 47 (end of Current Threads block) and before `## Prior History` on line 50.

`state.scene` is already passed to the narrate user context at `narrate.py:89`. No Python change needed.

**Why:** The narrator reads scene phase to calibrate tone and pacing. A CRISIS-phase narration should feel urgent; a BREATHER-phase narration should feel exploratory.

**Validation:** Render with `state.scene.scene_phase="CRISIS"` — "Scene phase: CRISIS" appears. Render with no scene key — no phase line appears.

### Tests to write or update

No automated tests. Manual verification:

1. **Template rendering test:** Render each changed `.j2` file with sample context dicts. Verify output contains the new sections and omits the old ones.
2. **Consistency scan:** grep all `.j2` files for `pacing directive`, `Pressure`, `Overwhelm`, `block_escalate`, `gate` — confirm no remaining references to obsolete concepts. Specifically verify zero `{{ gate }}` or `pacing_context.gate` references remain in `storytell_user.j2` and zero `gate == "block_escalate"` in `_thread_list.j2`.
3. **Pipeline integration:** Run one turn via `ev.py play`, inspect raw rendered prompts in the events log — both storytell and narrate prompts contain `scene_phase`.

### Documentation updates (mandatory per AGENTS.md)

4. **`docs/repomap.md`:** Update the prompt template section to reflect the new phase-driven structure — replace directive→beat table references with phase→beat constraints, note that `scene_phase` and `allowed_beat_types` are now passed to storytell context.
5. **`docs/architecture/step2c-storytell.md`:** Update the storyteller prompt docs to reflect the new phase table replacing the old directive table. Note removal of `gate` rendering from templates.
6. **`docs/architecture/step1-narrate.md`:** Update narrator prompt docs to reflect "outcome hint" terminology replacing "pacing directive" / "Outcome directive".
