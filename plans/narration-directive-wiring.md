# Narration Directive Wiring and Pacing

## Status
`open`

## Part of
standalone

## Dependencies
- none (does not depend on Plan 1, can run in parallel)

## Objective
Two separate but related failures degrade narration quality: (1) the `Breathe`/`Overwhelm`/`Pressure`/`Tension` directives in `narrate_user.j2` are never rendered because the bare `scene_pressure` variable is not passed to `_narrate_messages()` — only `state.scene.scene_pressure` is accessible, but the Jinja block at lines 96-111 references `scene_pressure` as a standalone variable; (2) even when they do render, the momentum floor directive ("Consider offering an opportunity") is too vague to be honored consistently, and there is no mechanic-grounded instruction telling the narrator how to reward player de-escalation choices. The result is a death spiral with no exit and narration that ignores momentum state entirely.

## Non-goals
- Does not change dice resolution or band logic.
- Does not add new Pydantic fields to `ProgressExtractResult` or state.
- Does not change the pressure expiry/escalation logic in `pressure.py` (that is a mechanics plan).
- Does not address narration imagery repetition (separate prompt concern).
- Does not touch quest or scene extraction prompts.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/engine/narrate.py` | modify | Add `scene_pressure` kwarg to `_narrate_messages()` signature; add to Jinja `user_ctx` dict |
| `ccya/engine/turn.py` | modify | Pass `scene_pressure` kwarg at both `_narrate_messages()` call sites (`run_turn` and `run_turn_retry`) |
| `ccya/prompts/narrate_user.j2` | modify | Strengthen momentum floor directive; add de-escalation reward instruction tied to `deescalate` flag and momentum band |
| `ccya/prompts/narrate_system.j2` | modify | Add repeat-imagery prohibition rule; add quantified-NPC rule |
| `docs/REPOMAP/engine.md` | update | Document `scene_pressure` kwarg addition to `_narrate_messages()` |
| `docs/REPOMAP/prompts.md` | update | Document new narrator rules |

## Firm decisions

1. The directive rendering bug is an engine fix, not a prompt fix — `scene_pressure` must be passed explicitly. The template already has the correct Jinja logic; the variable just isn't arriving.
2. The momentum floor directive must reference the numeric value and give a concrete narrative instruction, not a soft suggestion.
3. De-escalation reward (retreat, rest, disengagement) must be expressed as a **narrative permission**, not a mechanical override — the narrator is told it is allowed to make the moment feel like progress even on a bad band, not that the band is overridden. This avoids the "critical fail but escaped anyway" weirdness.
4. Repeat-imagery prohibition is a system prompt rule with a negative example, not just a suggestion.
5. NPC quantity rule applies to groups — named individuals are exempt.

## Implementation — Phase 1: Fix scene_pressure Wiring

### Context files to load
- `ccya/engine/narrate.py`
- `ccya/engine/turn.py`
- `ccya/prompts/narrate_user.j2`

### Overview
Pass `scene_pressure` as an explicit list to `_narrate_messages()`, sourced from `state.get("scene", {}).get("scene_pressure") or []`. This makes the existing Jinja directive blocks (`Breathe`, `Overwhelm`, `Pressure`, `Tension`) at lines 93-111 of `narrate_user.j2` actually render.

### Detailed steps

#### Step 1.1 — Add scene_pressure kwarg to _narrate_messages signature

**File:** `ccya/engine/narrate.py`

**What:** Add `scene_pressure: list | None = None` to the `_narrate_messages()` function signature (after `pc_allegiance` at line 33). Add `"scene_pressure": scene_pressure or []` to the `user_ctx` dict (after `"pc_allegiance"` at line 53).

**Why:** The template at `narrate_user.j2:96-111` references `scene_pressure` as a bare variable in `{% elif scene_pressure %}`, `{% set immediate_count = scene_pressure | selectattr(...) %}`, and `{% set building_count = scene_pressure | selectattr(...) %}`. It is currently never in the Jinja context, so every block silently evaluates to false/empty. The `user_ctx` dict already passes `"scene": state.get("scene", {})` at line 47, but the template uses bare `scene_pressure` (not `state.scene.scene_pressure`) in the directive blocks.

**Code Snippet:**
```python
# In _narrate_messages() signature, add after pc_allegiance:
    scene_pressure: list | None = None,

# In the user_ctx dict, add after pc_allegiance:
        "scene_pressure": scene_pressure or [],
```

**Validation:** Render `narrate_user.j2` with a state that has one immediate pressure and `scene_pressure=[{"urgency": "immediate", "text": "test"}]`. Confirm `**Pressure:** Active immediate threat(s).` appears in the rendered output.

***

#### Step 1.2 — Pass scene_pressure at the call sites in run_turn and run_turn_retry

**File:** `ccya/engine/turn.py`

**What:** At both `_narrate_messages()` call sites, add `scene_pressure=(state.get("scene") or {}).get("scene_pressure") or []`.

**Why:** The kwarg added in 1.1 has no effect unless the call site provides the value. There are two call sites:
- `run_turn()` at lines 460-482
- `run_turn_retry()` at lines 1007-1031

**Code Snippet:**
```python
# In run_turn() _narrate_messages() call (around line 481), add:
            scene_pressure=(state.get("scene") or {}).get("scene_pressure") or [],

# In run_turn_retry() _narrate_messages() call (around line 1030), add:
            scene_pressure=(state.get("scene") or {}).get("scene_pressure") or [],
```

**Validation:** Run a full turn with an active immediate pressure. Check `events.jsonl` → `narrate_prompt.rendered_user` — confirm the `Pressure` or `Overwhelm` block is present.

***

## Implementation — Phase 2: Strengthen Momentum and De-escalation Directives

### Context files to load
- `ccya/prompts/narrate_user.j2`

### Overview
Replace the vague momentum floor and de-escalation directives with concrete, mechanic-grounded instructions. The goal is to give the narrator a clear permission structure: when momentum is at floor and/or the player chooses a de-escalation action, the narrator is explicitly permitted (and directed) to give a beat of narrative relief.

### Detailed steps

#### Step 2.1 — Strengthen momentum LOW directive

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace the current low-momentum block at lines 89-92:

```jinja2
{% elif m <= -2 %}

**Momentum:** LOW ({{ m }}). The player has been struggling. Consider offering an opportunity or escape path to progress the story.
{% endif %}
```

With a stronger, concrete version:

```jinja2
{% elif m <= -3 %}

**Momentum FLOOR ({{ m }}):** The player is at the lowest possible momentum. You MUST give them a visible out this turn. If the player attempts any de-escalation action (retreat, hide, run, rest, ask for help, surrender, concede), narrate a partial success — they get some distance, some relief, some breath. Do not pile on. One pressure should feel like it eases even if not removed. The story cannot sustain another pure failure here.
{% elif m <= -2 %}

**Momentum LOW ({{ m }}):** The player is struggling. Look for the one thing going slightly in their favor and name it. If the player attempts retreat, disengagement, or rest, allow the attempt to feel like it matters narratively.
{% endif %}
```

**Why:** The old single-threshold directive (`<= -2`) never fired with sufficient force. Splitting floor from low gives the narrator a clear escalation: at -2 it softens, at -3 it's mandatory relief.

**Validation:** Render `narrate_user.j2` with `momentum=-3`. Confirm `Momentum FLOOR` text appears. Render with `momentum=-2`. Confirm `Momentum LOW` appears. Render with `momentum=-1`. Confirm neither appears.

***

#### Step 2.2 — Add de-escalation reward note to Breathe block

**File:** `ccya/prompts/narrate_user.j2`

**What:** Replace the existing Breathe block at line 95:

```jinja2
**Breathe:** A pressure has resolved. Pull back. Let the scene have a moment of relief. No new hook this turn.
```

With:

```jinja2
**Breathe:** A pressure has resolved — the player earned this. Pull back. Describe what quiet or relief feels like in this moment. No new hook, no new threat this turn. If the player retreated or disengaged to earn this, acknowledge it — they made a smart call and the world reflects it.
```

**Why:** The current text pulls narration back but doesn't reward the player's choice. Making the beat feel earned closes the loop between player agency and narrative outcome.

**Validation:** Render with `deescalate=1.0`. Confirm updated Breathe text appears.

***

## Implementation — Phase 3: Narrator System Prompt Rules

### Context files to load
- `ccya/prompts/narrate_system.j2`

### Overview
Add two missing narrator rules: prohibition on repeating previous-turn imagery, and quantification requirement for NPC groups.

### Detailed steps

#### Step 3.1 — Add repeat-imagery prohibition

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add the following rule in the "Output discipline" section (after line 88, before "Active scope tail"):

```
**NO REPETITION RULE:** Do not reuse sensory details, metaphors, descriptive phrases, or imagery from the immediately preceding turn's narration. If the previous turn described "the rain hammering the cobblestones," this turn must find a different image. The world changes with each turn; the narration must reflect that.
```

**Why:** The model's recency bias causes it to echo the previous narration's most salient phrases. An explicit negative prohibition is more effective than a positive instruction to "be varied."

**Validation:** In a multi-turn eval, check turns 2–5 for repeated phrases from the prior turn. If the rule is working, cross-turn phrase repetition should be rare.

***

#### Step 3.2 — Add quantified NPC group rule

**File:** `ccya/prompts/narrate_system.j2`

**What:** Add the following rule in the "NPCs in scene" section (after line 46):

```
**NPC QUANTITY RULE:** When introducing or describing a group of unnamed NPCs, always give a specific number or a tight qualifier: "four guards," "a dozen soldiers," "three dock workers." Never use vague collective nouns alone: not "guards" or "some soldiers" or "a group of men." Named individuals are exempt. Vague groups make state tracking impossible.
```

**Why:** Vague groups produce NPC tracking failures downstream — the scene extractor can't emit a `npc_add` for "guards." Named or counted groups allow correct extraction and coherent state.

**Validation:** Check narration output in eval runs for vague group mentions. The pattern "a group of" or standalone "guards entered" without a number should disappear.

***

### Tests to write or update
- **New file `tests/test_narrate.py`:** Call `_narrate_messages()` with `scene_pressure=[{"urgency": "immediate", "text": "test"}]` → assert rendered user prompt contains `Pressure` directive.
- **New file `tests/test_prompts.py`:** Render `narrate_user.j2` with `momentum=-3` and `scene_pressure=[{"urgency": "immediate", "text": "test"}]` → assert `Momentum FLOOR` and `Pressure` both appear.
- **New file `tests/test_prompts.py`:** Render `narrate_user.j2` with `deescalate=1.0` → assert updated `Breathe` text appears.
- **New file `tests/test_prompts.py`:** Render `narrate_system.j2` → assert `NO REPETITION RULE` appears.

### REPOMAP updates required
- `docs/REPOMAP/engine.md`: in `_narrate_messages()` signature entry (line 72), add `scene_pressure: list | None = None` kwarg.
- `docs/REPOMAP/prompts.md`: under `narrate_user.j2`, add: "scene_pressure wire fix (bare variable now passed from engine); momentum floor two-tier directive (-2 softens, -3 mandatory relief); de-escalation reward on Breathe block."
- `docs/REPOMAP/prompts.md`: under `narrate_system.j2`, add: "NO REPETITION RULE; NPC QUANTITY RULE."

### Risks
1. **scene_pressure kwarg name collision** — if another variable named `scene_pressure` is already in the Jinja context via `state` rendering, the explicit kwarg could shadow or conflict. Mitigation: the `user_ctx` dict already has `"scene": state.get("scene", {})` at line 47 of `narrate.py`. Adding `"scene_pressure"` as a top-level key is safe — Jinja resolves bare `scene_pressure` before `state.scene_pressure`. No conflict.
2. **Momentum FLOOR directive conflicts with crit_fail band** — a crit_fail band says "things go badly" while the floor directive says "give them a visible out." These can coexist: the band describes the outcome of the specific action, the floor directive describes the environmental/narrative relief available. The executor should add a note in the floor directive text: "This is a narrative permission for environmental relief, not a band override — the action outcome still follows the band."
3. **Breathe block now longer** — small token cost increase. Acceptable.

## Ambiguities requiring resolution before execution
1. **Call site location — resolved:** `_narrate_messages()` is called from `turn.py` at two locations: `run_turn()` (lines 460-482) and `run_turn_retry()` (lines 1007-1031). Both call sites must be updated. The function is defined in `narrate.py` but never called from within `narrate.py` itself.
2. **deescalate type — resolved:** `deescalate` is typed as `float = 0.0` in `_narrate_messages()` signature (`narrate.py:28`). The template uses `{% if deescalate %}` which is truthy for any non-zero float. The call sites in `turn.py` pass `deescalate=deescalate` (a float) at line 475 and `deescalate=False` at line 1025 (bool, which is truthy in Jinja). This is consistent — no change needed.

## TODO.md update
Add under **P2 — Stability / Fidelity**:
```
- [ ] [Narration Directive Wiring and Pacing](plans/narration-directive-wiring.md)
```

--- END PLAN ---
