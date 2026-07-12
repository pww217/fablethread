# PLAN: GM Beat Type Alignment with Roll Bands

## Status
completed

## Problem

The progress extractor generates `escalation` beats on fail/setback roll results (T3 fail → escalation, T5 setback → escalation). This compounds player punishment — a failed check already has narrative consequences from the band directive, and an escalation beat makes the next turn harder. Beat types should align with roll outcomes:

- **crit_success / success** → `opportunity`, `escalation` (the world reacts to PC momentum)
- **partial** → `complication`, `pressure` (success at a cost)
- **setback / fail** → `breathing_room`, `complication`, or `null` — never escalation

## Root Cause

The prompt guidance in `extract_progress_system.j2` lines 67-81 ties beat type to `deescalate > 0.5` and the narration directive, but doesn't explicitly constrain beat types by roll band. The LLM sees an active pressure and generates escalation regardless of whether the player just failed — it's responding to pressure context rather than outcome signal.

The `rules_stakes` section (lines 51-60) only gives guidance for crit_fail/fail/crit_success bands, not setback or partial. And the "Guidance per non-pressure type" section doesn't mention which band each beat type is appropriate for.

## Scope

Single file: `ccya/prompts/extract_progress_system.j2`. No code changes.

## Phases

### Phase 1 — Band-to-beat-type mapping (1 change)

Add explicit guidance to the GM Beat section that maps roll bands to appropriate beat types, overriding pressure-context bias. Insert after line 74 ("Crisis-aware beat selection"):

```
**Band-aligned beat selection:** The roll band determines what kind of beat is narratively appropriate — do not ignore this signal even when scene pressures are active:

- **crit_success / success**: `opportunity`, `escalation` (the world reacts to PC momentum), or `breathing_room` if deescalate > 0.5
- **partial**: `complication`, `pressure` — the player succeeded but at a cost; the beat should reflect that cost
- **setback / fail**: `breathing_room`, `null`, or rarely `complication`. Do NOT emit escalation or pressure beats on failed checks — the failure itself is the consequence. Escalation compounds punishment and breaks pacing.
- **No roll (pure approach/sit)**: `null` unless there's an independent narrative reason for a beat

When deescalate > 0.5, always prefer `breathing_room` or `null` regardless of band.
```

### Phase 2 — Strengthen rules_stakes guidance (1 change)

In the `rules_stakes` section (`extract_progress_user.j2`, lines 54-58), add setback/partial guidance:

After line 57, insert:
```jinja2
{% elif band == "setback" -%}
On a setback, prefer `breathing_room`, `null`, or `complication` beats. Do NOT emit escalation — the resource loss IS the consequence.
{% elif band == "partial" -%}
A partial means success at a cost. Emit `complication` or `pressure` beats that name what was lost or compromised.

```

### Phase 3 — Verify with eval (testing)

Run the existing test suite to confirm no regressions:
```bash
make check && make test
```

Then manually inspect turns from the current save after a fresh run to verify beat types align with bands.

## Success criteria

- T1-T6 mechanics output shows correct beat-type-to-band alignment (setback/fail → breathing_room/complication/null, never escalation)
- All existing tests pass
- Beat diversity rules still function — non-pressure beats appear at least every third turn during pressure cascades
