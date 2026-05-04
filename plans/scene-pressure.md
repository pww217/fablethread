# Plan: `scene_pressure` — Active Threat Tracking

## Problem

`world_state` is a flat list of strings that mixes two fundamentally different kinds of facts:

1. **Lore / canon**: "The Merchant Guild controls the eastern docks." — permanent, world-level, slow to change.
2. **Active pressure**: "Guards are converging on your position." — immediate, scene-level, resolves within a few turns.

Because they share the same list, the LLM treats both with equal weight. A ticking-clock threat like "the building is on fire" sits next to "the king has been dead for 10 years" and gets the same narrative attention as background worldbuilding. Active threats get forgotten; lore gets over-applied to urgent scenes.

## Design

### New field: `scene.scene_pressure`

Add a list of pressure objects alongside `world_state`:

```python
# models.py
class ScenePressure(BaseModel):
    id: str             # stable snake_case ID
    text: str           # "Guards are converging on your position."
    urgency: str        # "immediate" | "building" | "background"
    turn_added: int
    max_turns: int | None = None  # optional hard expiry; None = fiction-driven only
```

State schema:

```yaml
scene:
  world_state:
    - "The Merchant Guild controls the eastern docks."
  scene_pressure:
    - id: guards_converging
      text: "Guards are converging on your position."
      urgency: immediate
      turn_added: 7
      max_turns: 3
```

### Urgency levels

| Urgency | Meaning | Narrator instruction |
|---|---|---|
| `immediate` | Resolves this turn or the situation changes dramatically | "This must be addressed or it escalates NOW." |
| `building` | Escalates over 2–4 turns if ignored | "This is getting worse. The player should feel it." |
| `background` | Ambient threat, doesn't expire soon | Mention periodically; don't dominate every turn. |

### Narrator prompt changes

**`narrate_user.j2`** — add a dedicated `SCENE PRESSURE` block rendered before the player input:

```jinja
{% if state.scene.scene_pressure %}
ACTIVE THREATS (must be reflected in narration):
{% for p in state.scene.scene_pressure %}
- [{{ p.urgency | upper }}] {{ p.text }}
{% endfor %}
{% endif %}
```

The urgency label tells the narrator how urgently to weave it in. An `immediate` pressure should be front-and-center. A `background` pressure can be a single atmospheric sentence.

### Extractor changes

**`ProgressExtractResult`** (stream 3) — add:

```python
scene_pressure_add: list[ScenePressure] = []
scene_pressure_remove: list[str] = []  # IDs to clear
scene_pressure_update: list[ScenePressure] = []  # text/urgency changes
```

Extractor prompt guidance:
> Add a `scene_pressure` entry when the narration introduces a time-sensitive threat, pursuit, hazard, or countdown. Set urgency based on immediacy. Remove a pressure when the narration resolves it — the fire is out, the guards were evaded, the bomb was defused. Do NOT add lore or permanent world facts to `scene_pressure`; those go in `world_state`.

### Engine-side expiry (optional safety net)

Unlike the condition TTL (which is being removed), `max_turns` on pressure objects is an *explicit, fiction-grounded* expiry set by the extractor at creation time. The engine can honor it:

```python
# In run_turn(), after extraction, before apply_delta:
pressures = list((state.get("scene") or {}).get("scene_pressure") or [])
current_turn = state.get("meta", {}).get("turn", 0)
state["scene"]["scene_pressure"] = [
    p for p in pressures
    if not (isinstance(p, dict) and p.get("max_turns")
            and (current_turn - p.get("turn_added", 0)) >= p["max_turns"])
]
```

This is not a blanket TTL — it only fires when the extractor itself said the pressure should expire by then.

## Migration

- Add `scene_pressure: []` to the default state schema. Existing saves without it load fine (default empty list).
- No retroactive migration needed — old saves simply start with no pressure entries.

## Relationship to `world_state`

After this change, `world_state` should be treated as append-only lore. Consider adding a prompt rule:
> Do not add time-sensitive or scene-specific threats to `world_state`. Use `scene_pressure` for anything that might resolve within a few turns.
