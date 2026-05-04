# Plan: Condition System Overhaul

Two related problems addressed here:

1. Engine-side TTL auto-expiry is invisible and gameable.
2. The extractor adds conditions based only on narration text, with no signal about *which skill just failed* — so it often adds the wrong condition or misses the right one.

---

## Part 1: Remove Condition TTL

### Problem

`CONDITION_TTL_TURNS = 4` in `engine.py` auto-removes any condition that's been on the PC for 4 turns, regardless of what's happened in the fiction. A `wounded` condition disappears on turn 5 with no narrative cause. This is:

- **Invisible to the player** — no narration, no explanation
- **Gameable** — wait 4 turns and any condition evaporates
- **Incorrect** — conditions should last as long as the fiction says they last

### Fix

Delete the TTL loop entirely from `engine.py`. The relevant block is:

```python
# === Pre-extraction: condition TTL tick ===
engine_expired_conditions: list[dict[str, Any]] = []
pc_conds = list((state.get("pc") or {}).get("conditions") or [])
surviving: list[dict] = []
for c in pc_conds:
    ...
    age = (state.get("meta", {}).get("turn", 0)) - c.get("added_turn", 0)
    if age >= config.condition_ttl_turns:
        engine_expired_conditions.append(c)
    else:
        surviving.append(c)
```

Remove this block and remove `engine_expired_conditions` from the call to `_run_extraction_pipeline()`. Conditions are now only removed by the extractor.

Also remove:
- `condition_ttl_turns` from `EngineConfig`
- `CONDITION_TTL_TURNS` constant
- `engine_expired_conditions` parameter from `_extract_state_messages()` and `_run_extraction_pipeline()`

### Extractor guidance

The state extractor system prompt (`extract_state_system.j2`) needs explicit guidance on condition removal. Add a rule along the lines of:

> Remove a condition only when the narration contains a clear in-fiction cause: rest that would heal a wound, treatment by a medic, resolution of the fear that caused fright, a stimulant clearing exhaustion, etc. Do not remove conditions because time has passed or the scene changed. Conditions persist until the fiction resolves them.

---

## Part 2: Condition → Skill Feedback Loop

### Problem

Right now the state extractor decides whether to add a condition by reading the narration text alone. It has no information about:

- Which skill was just checked
- What the roll outcome was
- Whether the failure was physical, mental, or social

This means the extractor will sometimes add `frightened` after a failed `strength` check (wrong), or miss adding `wounded` after a failed `fight` action because the narration was vague.

### Fix

Pass `RulesOutcome` context into the state extraction user prompt. The extractor already receives `rules_outcome` but the template may not be surfacing the `skill` field. Ensure the `extract_state_user.j2` template renders:

```jinja
{% if rules_outcome and rules_outcome.rolled %}
ROLL CONTEXT:
  skill checked: {{ rules_outcome.skill }}
  outcome band:  {{ rules_outcome.band }}
  directive:     {{ rules_outcome.directive }}
{% endif %}
```

Then add a rule in `extract_state_system.j2`:

> When deciding whether to add a condition, use the roll context as the primary signal:
> - A failed/setback `strength` or `dexterity` check during a combat verb → consider `wounded` or `bleeding`
> - A failed/setback `resolve` check → consider `shaken`
> - A failed/setback `wits` check under pressure → consider `frightened` or `drugged` (if substance involved)
> - A failed/setback `strength`/`dexterity`/`resolve` check → consider `exhausted` if the narration implies sustained effort
> The narration text is the confirmation, but the roll context is the trigger. Do not add conditions on a clean success.

### Condition→Skill map (source of truth)

This is already in `rules.py` as `CONDITION_MODS`. The system prompt guidance should mirror it — conditions that penalize a skill should be triggered by failures *on that skill*. Keep them in sync.

```python
CONDITION_MODS: dict[str, dict[str, int]] = {
    "wounded":   {"strength": -1, "dexterity": -1},
    "exhausted": {"strength": -1, "dexterity": -1, "resolve": -1},
    "drugged":   {"wits": -1, "resolve": -1},
    "frightened":{"resolve": -1, "charisma": -1},
    "shaken":    {"resolve": -1},
    "bleeding":  {"strength": -1},
}
```

When writing the extractor prompt guidance, frame it as: *"add a condition that penalizes the skill that just failed."*

---

## Migration Notes

- Existing saves with `added_turn` on condition objects are fine — that field can remain for debugging, it just won't be acted on.
- Remove `condition_ttl_turns` from `config.yaml` defaults and `EngineConfig` after the engine code is cleaned.
- Add a test: inject a condition with `added_turn = 1` on turn 10 and assert it is NOT auto-removed by the engine.
