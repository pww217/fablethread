# Plan: Active DM Storytelling in the Progress Module

## Problem

The progress extractor (`extract_progress_system.j2`) is purely reactive — it reads the narration and records what happened. It does not influence story direction. A human GM does something the progress module currently doesn't: **between turns, they decide what happens next.** They look at the quest state, the faction landscape, what the player just did, and they make an active choice about where to push the story.

The momentum track (see `plans/momentum-track.md`) gives a pacing signal. This plan makes the progress extractor act on it — and on quest state, NPC allegiances, and scene pressure — to emit **forward-facing story beats** alongside the normal extraction output.

---

## Concept: The GM Move Block

After extracting what happened this turn, the progress extractor emits one additional field: `gm_beat`. This is a short, structured directive the narrator receives at the top of the *next* turn's user prompt — before the player acts.

It is not narrated directly. It's a backstage instruction: *"this is what the world is doing right now, whether the player notices it or not."*

```json
{
  "gm_beat": {
    "type": "complication" | "revelation" | "opportunity" | "breathing_room" | "pressure" | null,
    "instruction": "A rival faction has noticed the player's recent activity and dispatched a watcher.",
    "surface_as": "ambient" | "event" | "npc_behavior"
  }
}
```

`null` means the extractor has nothing to add this turn. That's fine — not every turn needs a GM beat.

---

## Beat Types

| Type | When to emit | What it does |
|---|---|---|
| `complication` | After `success` or `crit_success` streak (momentum >= +2) | Something new goes wrong or gets harder. The world reacts to the player winning. |
| `pressure` | After a quiet turn with no roll or low stakes | A ticking threat or faction move arrives to raise urgency. |
| `revelation` | Any time a significant NPC or quest detail hasn't been surfaced yet | A fact the player doesn't know yet becomes available to the narrator. |
| `opportunity` | After `fail` or `setback` streak (momentum <= -2) | A small door opens — a resource found, a friendly NPC appears, a lucky detail. |
| `breathing_room` | After `crit_fail` or sustained punishment (momentum == -3) | No threat this turn. Give the player a moment to stabilize. |

The extractor decides the type based on:
1. `momentum` from PC state
2. Quest status (any quest near completion? any near failure?)
3. `scene_pressure` entries (any already escalating?)
4. Unresolved NPC compendium entries (any NPCs with unknown allegiance or pending motivation?)

---

## How `surface_as` Works

The narrator receives the `gm_beat` and uses `surface_as` to decide presentation:

- `ambient` — weave it into background description. A shadow at the window. A distant horn. Not an event, just texture.
- `event` — something actually happens this turn that the player can interact with.
- `npc_behavior` — an NPC present in the scene changes their behavior in a way that reflects the beat.

This keeps GM beats from feeling like interruptions. An `ambient` beat adds atmosphere without derailing the player's action. An `event` beat is used when the story genuinely needs a redirect.

---

## Implementation

### Schema

**`ccya/models.py`** — add:

```python
class GMBeat(BaseModel):
    type: Literal["complication", "revelation", "opportunity", "breathing_room", "pressure"] | None = None
    instruction: str = ""
    surface_as: Literal["ambient", "event", "npc_behavior"] = "ambient"

class ProgressExtractResult(BaseModel):
    # ... existing fields ...
    gm_beat: GMBeat | None = None
```

### Progress extractor system prompt

**`ccya/prompts/extract_progress_system.j2`** — add a new section after the existing field rules:

```
## GM Beat (gm_beat)

After extracting this turn's changes, decide whether to emit a forward-facing story beat for the NEXT turn.

Emit `null` if:
- The current scene already has active `scene_pressure` entries (don't pile on)
- The player is in a critical resolution moment (final quest objective in reach)
- Nothing meaningful has changed in faction, NPC, or quest state to react to

Emit a beat when:
- momentum >= +2: the player is winning; emit `complication` to raise stakes
- momentum <= -2: the player is struggling; emit `opportunity` or `breathing_room`
- A quest has been stalled (same objective for 3+ turns): emit `pressure` or `revelation`
- An NPC with unknown or shifting allegiance is present: emit `revelation`

Beat instruction rules:
- 1-2 sentences. Concrete, not vague.
- BAD: "Something bad happens to the player."
- GOOD: "A contact the player trusted has been seen meeting with the opposing faction at the dockside inn."
- BAD: "Give the player a break."
- GOOD: "The player spots a satchel left behind by a fleeing guard — it contains a vial and a partial map."

`surface_as` guidance:
- `ambient`: low-stakes background texture. Used for `breathing_room` and most `revelation` beats.
- `event`: something the player can directly interact with. Used for `opportunity` and `pressure`.
- `npc_behavior`: a present NPC shifts their demeanor, loyalty signal, or body language. Best for `revelation` and `complication`.
```

### Narrator user prompt

**`ccya/prompts/narrate_user.j2`** — add a block that surfaces the previous turn's `gm_beat` (stored in turn state or passed from engine):

```jinja
{% if gm_beat and gm_beat.type %}
GM DIRECTION ({{ gm_beat.type | upper }}, surface as {{ gm_beat.surface_as }}):
{{ gm_beat.instruction }}
This is a backstage instruction, not player-visible narration. Integrate it naturally.
{% endif %}
```

### Engine integration

**`ccya/engine.py`** — after `_run_progress_pipeline()` resolves:

```python
gm_beat = progress_result.gm_beat  # may be None
# Store on turn state or pass directly into next narrate call
state.setdefault("meta", {})["pending_gm_beat"] = gm_beat.dict() if gm_beat else None
```

On the *next* turn, `_narrate_messages()` reads `state["meta"]["pending_gm_beat"]` and injects it into the user prompt. After narration completes, clear `pending_gm_beat`.

---

## Notes

- The GM beat is advisory to the narrator, not binding. The narrator is told to integrate it naturally — it should never override a clear player intention or produce a non-sequitur.
- If `scene_pressure` (see `plans/scene-pressure.md`) is already high, the extractor should prefer emitting `null` rather than stacking a second beat.
- The beat should feel like a human GM's offhand thought between turns: *"Actually, let me have this faction notice what's happening..."* — quiet, purposeful, and grounded in the existing fiction rather than invented from nothing.
- Long-term: `gm_beat` history could be stored in the compaction chronicle to give future turns a sense of which beats were played and which threads are still live.
