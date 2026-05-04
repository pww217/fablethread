# Plan: Scene Age Anti-Stall

## Problem

With no mechanism to nudge the story forward, the narrator can keep the player in the same room for 10+ turns — especially if the player is asking questions, examining objects, or doing low-stakes actions. There's no signal that the scene has "gone stale" and the story needs to move.

This is different from `scene_pressure` (which tracks active threats). Scene age is about *inertia* — the absence of change, not the presence of danger.

## Design

### Track `turn_entered` on scene

Add `turn_entered: int` to scene state, set when `location_change` fires:

```python
# In apply_delta, when location changes:
state["scene"]["turn_entered"] = state["meta"]["turn"]
```

Default `0` for existing saves.

### Scene age calculation

In `engine.py`, before building narrate messages:

```python
current_turn = state["meta"]["turn"]
turn_entered = (state.get("scene") or {}).get("turn_entered", 0)
scene_age = current_turn - turn_entered
```

### Narrator directive

In `narrate_user.j2`:

```jinja
{% set scene_age = (meta.turn | default(0)) - (scene.turn_entered | default(0)) %}
{% if scene_age >= 6 and not scene.scene_pressure %}
SCENE AGE: This scene has been active for {{ scene_age }} turns with no location change.
Consider advancing: a new arrival, a change in atmosphere, a time skip, or a reason for the
player to move. Do not force it if the player's action anchors them here — but look for a
natural opportunity to shift.
{% elif scene_age >= 10 %}
SCENE AGE: {{ scene_age }} turns in this location. The scene needs to move. Something should
change this turn: an NPC departs, conditions worsen, time pressure becomes visible.
{% endif %}
```

The `>= 6` threshold is advisory; `>= 10` is a stronger nudge. The `not scene.scene_pressure` check avoids stacking anti-stall with active threat pressure.

## Notes

- `scene_age` resets to 0 on any `location_change` in the delta, including sub-location moves.
- This is purely a narrator directive — it doesn't force any state change, it just makes the narrator aware.
- The threshold values (6, 10) should be configurable in `config.yaml` as `scene_stall_advisory_turns` and `scene_stall_hard_turns`.
- If the player is deliberately camping (crafting, resting, extended dialogue), the narrator can acknowledge the time passing without forcing a scene change.
