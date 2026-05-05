# Plan: Condition System Overhaul

Two related problems addressed here:

1. Engine-side TTL auto-expiry is invisible and gameable.
2. The extractor adds conditions based only on narration text, with no signal about *which skill just failed* — so it often adds the wrong condition or misses the right one.

---

## Part 1: Remove Condition TTL

### Problem

`CONDITION_TTL_TURNS = 4` in `engine.py` auto-removes any condition that's been on the PC
for 4 turns, regardless of what's happened in the fiction. A `wounded` condition disappears
on turn 5 with no narrative cause. This is:

- **Invisible to the player** — no narration, no explanation
- **Gameable** — wait 4 turns and any condition evaporates
- **Incorrect** — conditions should last as long as the fiction says they last

### Fix

Delete the TTL loop entirely from `engine.py`. The relevant block to remove:

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

Also remove:
- `condition_ttl_turns` from `EngineConfig`
- `CONDITION_TTL_TURNS` constant
- `engine_expired_conditions` parameter from `_extract_state_messages()` and
  `_run_extraction_pipeline()`
- `engine_expired_conditions` stays as an always-empty `[]` at the call site during
  transition to avoid breaking the pipeline signature; remove the parameter entirely
  once callers are updated

### Extractor guidance

Add to `extract_state_system.j2`:

> Remove a condition only when the narration contains a clear in-fiction cause: rest that
> would heal a wound, treatment by a medic, resolution of the fear that caused fright, a
> stimulant clearing exhaustion, etc. Do not remove conditions because time has passed or
> the scene changed. Conditions persist until the fiction resolves them.

---

## Part 2: Condition → Skill Feedback Loop

### Problem

The state extractor decides whether to add a condition by reading narration text alone.
It has no information about which skill was just checked, what the roll outcome was, or
whether the failure was physical, mental, or social. Result: wrong conditions added, right
ones missed.

### Fix

**`ccya/prompts/extract_state_user.j2`** — ensure `rules_outcome.skill` and
`rules_outcome.band` are explicitly surfaced near the condition section:

```jinja
{% if rules_outcome and rules_outcome.rolled %}
ROLL CONTEXT:
  skill checked: {{ rules_outcome.skill }}
  outcome band:  {{ rules_outcome.band }}
  directive:     {{ rules_outcome.directive }}
{% endif %}
```

**`ccya/prompts/extract_state_system.j2`** — add skill→condition guidance:

> When deciding whether to add a condition, use the roll context as the primary signal:
> - A failed/setback `strength` or `dexterity` check during a combat verb → consider
>   `wounded` or `bleeding`
> - A failed/setback `resolve` check → consider `shaken`
> - A failed/setback `wits` check under pressure → consider `frightened` or `drugged`
>   (if substance involved)
> - A failed/setback `strength`/`dexterity`/`resolve` check → consider `exhausted` if
>   the narration implies sustained effort
>
> The narration text is the confirmation, but the roll context is the trigger.
> Do not add conditions on a clean success.

### Condition→Skill map (source of truth)

This is already in `rules.py` as `CONDITION_MODS`. The system prompt guidance mirrors it —
conditions that penalize a skill should be triggered by failures *on that skill*.

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

---

## Migration Notes

- Existing saves with `added_turn` on condition objects are fine — that field can remain
  for debugging, it just won't be acted on.
- Remove `condition_ttl_turns` from `config.yaml` defaults and `EngineConfig` after the
  engine code is cleaned.
- Add a test: inject a condition with `added_turn = 1` on turn 10 and assert it is NOT
  auto-removed by the engine.
