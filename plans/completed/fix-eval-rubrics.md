# Plan: Adjust Eval Rubrics & Inputs for New Mechanics

## Problem

The evaluation rubrics and scenarios were designed before the `narration_directive` system was wired through to the progress extractor. The new mechanics surface in the trace but aren't being evaluated:

1. **narration_directive** — Now computed in turn.py and passed to both narrate and progress prompts. No rubric evaluates whether the directive is being honored.
2. **Beat generation context** — Progress extractor now has narration_directive for beats/pressure decisions. No rubric evaluates whether this context improves beat generation.
3. **Pressure removal timing** — Pressures removed by progress extractor when narration shows threats resolved (turns 2, 6 in default run). No rubric evaluates this behavior.
4. **Directive→narration alignment** — The narrate template computes directives (Breathe/Pressure/Overwhelm/Tension/Combat Fatigue/Location Imperative/Location Pressure/Threat Pressure/Resolve a Threat) but no rubric checks if narration follows them.

## Current Rubric Coverage

### What's already covered
- **state_correctness**: Mechanic lifecycle tables for momentum, beats, pressures, conditions, arc threads. Auto-checker failure analysis.
- **narrative_interplay**: Momentum→directive→tone chain (but only rules directive, not narration_directive). Beat→narrative effect. Pressure→stakes→consequence chain.
- **prompt_pipeline**: Per-pipeline P1-P9 audit. Cross-pipeline I/O relevance. Extract progress section mentions deescalate/pending_beat.
- **universal_asserts**: `check_directive_rendered` checks for `**Pressure:**`/`**Overwhelm:**` in narrate user prompt when immediate pressures exist.

### What's NOT covered
- **narration_directive evaluation**: No rubric checks if the computed narration_directive (Breathe/Pressure/Overwhelm/Tension/Combat Fatigue/Location Imperative/Location Pressure/Threat Pressure/Resolve a Threat) is being honored by either the narrator or the progress extractor.
- **Directive→narration alignment**: The narrate template renders directives but no rubric checks if narration follows them.
- **Progress extractor directive usage**: The progress extractor now receives narration_directive in its prompt. No rubric evaluates whether it uses it for beats/pressure decisions.
- **Pressure removal evaluation**: Pressures removed by progress extractor when narration shows threats resolved. No rubric evaluates this behavior.
- **Beat generation improvement**: No rubric evaluates whether narration_directive context improves beat generation quality.

## Changes Required

### 1. Update `narrative_interplay` rubric — Add directive evaluation

**Section 1A — Momentum→Directive→Tone** → Extend to include narration_directive:

```markdown
### 1A — Rules Directive + Narration Directive → Tone

For each turn with a roll:

| Turn | Band | Rules Directive | Narration Directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|---------------------|-------------|---------------------------|------|

Flag: `TONE_MISMATCH` (narration tone contradicts band), `DIRECTIVE_IGNORED` (rules directive issued but prose ignores it), `NARRATION_DIRECTIVE_IGNORED` (narration_directive present but prose contradicts it).

After the table: Does band progression feel too fast, too slow, or appropriate? Was there a coherent momentum arc across the run?

### 1A.5 — Narration Directive Analysis

For each turn where narration_directive is non-empty:
- Was the directive honored in narration? (e.g., Breathe → low-urgency prose, Overwhelm → chaotic/overlapping events)
- Was the directive available to the progress extractor? (Check if it appears in extract_progress_user prompt)
- Did the progress extractor use it for beats/pressure decisions?

| Turn | Narration Directive | Honored? | Available to Extractor? | Used for Beat/Pressure? | Flag |
|------|---------------------|----------|------------------------|------------------------|------|

Flag: `DIRECTIVE_NOT_RENDERED` (computed but not in narrate prompt), `DIRECTIVE_IGNORED_BY_NARRATOR`, `DIRECTIVE_NOT_IN_PROGRESS_PROMPT`, `DIRECTIVE_AVAILABLE_BUT_UNUSED`.

Evaluate all 9 directive types: Breathe, Pressure, Overwhelm, Tension, Combat Fatigue, Location Imperative, Location Pressure, Threat Pressure, Resolve a Threat.
```

### 2. Update `narrative_interplay` rubric — Add pressure removal evaluation

**Section 1C — Pressure→Stakes→Consequence Chain** → Extend to cover removal:

```markdown
### 1C.5 — Pressure Removal Evaluation

For each `scene_pressure_remove` event:
- Was the removal justified by narration? (narration showed the threat being addressed/resolved)
- Was the removal timely? (removed within 2-3 turns of narration showing resolution — pacing should not lock a player into a threat for more than a few turns)
- Was the removal correct? (no false removals — pressure removed when it shouldn't have been)

| Pressure ID | Added (Tn) | Resolved (Tm) | Turns to Remove | Narration Justified? | Correct? | Flag |
|-------------|------------|---------------|-----------------|---------------------|----------|------|

Flag: `EARLY_REMOVAL` (removed before narration showed resolution), `LATE_REMOVAL` (persisted >3 turns after narration showed resolution), `FALSE_REMOVAL` (removed when threat was still active), `MISSING_REMOVAL` (threat resolved in narration but pressure not removed).
```

### 3. Update `narrative_interplay` rubric — Beat generation improvement

**Section 1B — GM Beat→Narrative Effect** → Extend to evaluate narration_directive context:

```markdown
### 1B.5 — Beat Generation Quality with Directive Context

For each turn where a beat was generated:
- Was the beat type appropriate given the narration_directive? (e.g., Breathe → breathing_room beat, Pressure → complication beat)
- Was the beat generation informed by the directive context available in the progress prompt?

| Turn Beat Created | Beat Type | Narration Directive | Type Matches Directive? | Flag |
|-------------------|-----------|---------------------|------------------------|------|

Assessment method:
- **Rule-based**: Breathe→breathing_room, Pressure/Overwhelm→complication, Tension→complication or revelation, Combat Fatigue→complication, Location Imperative→complication, Location Pressure→complication, Threat Pressure→complication, Resolve a Threat→revelation or complication.
- **LLM judge**: Let the judge read the beat type + directive and decide if they align. More flexible but subjective.

Flag: `TYPE_MISMATCH` (beat type contradicts directive), `DIRECTIVE_INFORMED` (beat type aligns with directive).
```

### 4. Update `state_correctness` rubric — Add pressure removal flags

**Section 1C — Scene Pressure Lifecycle Table** → Extend flags:

```markdown
Flags: `INERT` (no escalation or resolution across ≥3 turns), `OVERLONG`, `UNRESOLVED_AT_END`, `EARLY_REMOVAL` (removed before narration showed resolution), `LATE_REMOVAL` (persisted >3 turns after narration showed resolution), `FALSE_REMOVAL` (removed when threat was still active).
```

### 5. Update `prompt_pipeline` rubric — Add narration_directive to extract progress assessment

**Section 3 — Cross-Pipeline I/O Relevance** → Extend extract progress assessment:

```markdown
**Extract Progress**: ... Should receive: narrative, pc, recent_events, world_state, scene_pressure, rules_outcome, intent, recent_turns, items_gained/lost, stakes, band, deescalate, pending_beat, narration_directive, extraction_ctx (NPC/inventory/location/pressure/conditions from scene+state). ...

Assess: is narration_directive being used by the progress extractor? Flag if it appears in the prompt but the extractor's output shows no evidence of using it for beats/pressure decisions.
```

### 6. Update universal asserts — Add narration_directive check

**New assert**: `check_narration_directive_rendered` — If narration_directive is non-empty, it should appear in both narrate_user.j2 AND extract_progress_user.j2.

```python
def check_narration_directive_rendered(event: dict[str, Any]) -> dict[str, Any]:
    """If narration_directive was computed, it should appear in both narrate and progress prompts.
    
    Checks for all 9 directive types: Breathe, Pressure, Overwhelm, Tension,
    Combat Fatigue, Location Imperative, Location Pressure, Threat Pressure, Resolve a Threat.
    """
    narr_user = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    progress_user = (event.get("extraction_prompt") or {}).get("rendered_user") or ""
    
    # Check for any directive in narrate prompt (all 9 types)
    directive_markers = [
        "**Pressure:**", "**Overwhelm:**", "**Breathe:**", "**Tension:**",
        "**Combat Fatigue:**", "**Location Imperative:**", "**Location Pressure:**",
        "**Threat Pressure:**", "**Resolve a Threat:**",
    ]
    has_directive = any(m in narr_user for m in directive_markers)
    
    if not has_directive:
        return {
            "assertion": "universal.narrate.directive_rendered",
            "passed": True,
            "detail": "(no directive computed)",
            "scope": "universal",
            "severity": "red",
        }
    
    if not any(m in narr_user for m in directive_markers):
        return {
            "assertion": "universal.narrate.directive_rendered",
            "passed": False,
            "detail": "narration_directive computed but not rendered in narrate user prompt",
            "scope": "universal",
            "severity": "red",
        }
    
    if "narration_directive" not in progress_user.lower():
        return {
            "assertion": "universal.narrate.directive_rendered",
            "passed": False,
            "detail": "narration_directive computed but not rendered in extract_progress user prompt",
            "scope": "universal",
            "severity": "yellow",
        }
    
    return {
        "assertion": "universal.narrate.directive_rendered",
        "passed": True,
        "detail": "directive rendered in both prompts",
        "scope": "universal",
        "severity": "red",
    }
```

### 7. Update scenarios — Add directive-aware assertions

**full_cycle.py**: Add assertions for narration_directive presence in key turns:

```python
# Turn 5: confrontation — should have Pressure/Overwhelm directive
Turn(
    input="...",
    phase="confrontation",
    expects=[
        "narration_directive should include Pressure or Overwhelm (immediate pressures from confrontation)",
        "beat type should align with directive (complication for Pressure)",
    ],
),
```

**pressure_lifecycle.py**: Add assertions for directive changes as pressure escalates:

```python
Turn(
    input="...",
    phase="pressure_building",
    expects=[
        f"narration_directive should include Tension (building pressure at age {PRESSURE_BUILDING_AT})",
        "narration_directive should NOT include Breathe (no deescalation)",
    ],
),
```

### 8. Update meta rubric — Add cross-judge directive evaluation

**Section 2 — Inter-Judge Contradiction Check** → Extend:

```markdown
- **narrative_interplay vs prompt_pipeline**: narrative says directives are ignored but prompt_pipeline rates the narrate prompt highly — check if narration_directive is being rendered in prompts. Is the issue with prompt architecture or narrator behavior?
```

## Implementation Order

1. **Update rubrics** (narrative_interplay.md, state_correctness.md, prompt_pipeline.md, meta.md) — adds directive evaluation sections
2. **Add universal assert** (universal_asserts.py) — check_narration_directive_rendered
3. **Update scenarios** (full_cycle.py, pressure_lifecycle.py) — add directive-aware assertions
4. **Run eval** — verify rubrics work with new trace data
5. **Iterate** — adjust rubric criteria based on actual eval results

## Files to Change

| File | Change |
|------|--------|
| `evals/rubrics/narrative_interplay.md` | Add Sections 1A.5, 1B.5, 1C.5 for directive/pressure evaluation |
| `evals/rubrics/state_correctness.md` | Extend Section 1C flags to include removal timing |
| `evals/rubrics/prompt_pipeline.md` | Extend Section 3 extract progress assessment for narration_directive |
| `evals/rubrics/meta.md` | Extend Section 2 cross-judge evaluation for directive alignment |
| `ccya/eval/universal_asserts.py` | Add check_narration_directive_rendered |
| `evals/scenarios/full_cycle.py` | Add directive-aware assertions for key turns |
| `evals/scenarios/pressure_lifecycle.py` | Add directive-aware assertions for escalation turns |
