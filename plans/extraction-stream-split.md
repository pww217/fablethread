# Plan G — Split Extraction Into Three Focused Streams

## Status: Pending

---

## Why We're Doing This

The current extractor runs one LLM call that is asked to do many different things at once:
- Classify scene cosmetics (tags, tagline, who is present)
- Calculate mechanical deltas (inventory changes, condition changes)
- Track long-horizon progress (quests, established facts, NPC compendium)

These are fundamentally different tasks. When they compete for the model's attention in one call, the model makes tradeoffs. The most common failure modes:

- **Conditions accumulate and never resolve.** The model sees a long list of other fields to fill and takes the easy path: add a condition, skip the removal check.
- **Quests don't start.** The model is mid-stream filling inventory and condition fields when it reaches quest_updates. It under-invests attention on quest reasoning because the "hard part" feels done.
- **Facts duplicate.** established_facts_add gets items already in the list because the model's working memory is spread thin.

The fix is to break the single extraction call into three smaller calls, each with a narrow, well-defined job. Each call gets its own system prompt focused only on its concern. The model cannot "run out of attention" on the most important fields because there are fewer fields per call.

**Total tokens per turn stays approximately the same.** Each stream's system prompt is smaller. Each stream's state slice is smaller. The sum is close to what the current single call costs — but accuracy improves because focus is higher per call.

---

## The Three Streams

### Stream 1 — Scene
**Job:** What does the scene look like right now? Who is in it? Did location change?

Fields owned:
- `scene_tags`
- `scene_tagline`
- `location_change` (boolean + new location id if true)
- `location_description` (updated description if location changed)
- `present_npcs` (full replacement list)

This stream runs first because the other two streams may need NPC presence to reason correctly (e.g. quest stream needs to know if a quest NPC is present).

### Stream 2 — State
**Job:** What physically changed for the player right now?

Fields owned:
- `inventory_add`
- `inventory_remove`
- `inventory_update`
- `pc_condition_add`
- `pc_condition_remove`

Inventory and conditions are grouped together because they are both immediate mechanical deltas — things that changed *this turn* with concrete cause in the narration. They are **not** grouped with quests/facts because those require longer-horizon reasoning.

### Stream 3 — Progress
**Job:** What did the player learn or accomplish that persists beyond this scene?

Fields owned:
- `quest_updates` (new quests, objective progress, completions)
- `established_facts_add`
- `established_facts_update`
- `established_facts_remove`
- `compendium_npc_update`

This stream runs last because it benefits from knowing the scene result (stream 1) and any mechanical outcomes (stream 2) before reasoning about long-term consequences.

---

## Execution Order

```
narration
    → stream 1 (scene)      ← runs first, no dependencies
    → stream 2 (state)      ← runs second; receives stream 1 output (present_npcs, location)
    → stream 3 (progress)   ← runs last; receives stream 1 + 2 outputs
    → merge all three into single state delta
    → apply to game state
```

Streams 2 and 3 could theoretically run in parallel (they don't depend on each other), but **do not implement parallel execution yet**. On a local GPU, parallel calls compete for the same hardware and the coordination overhead is not worth it at this scale. Run sequentially for MVP. Parallel can be revisited if latency becomes a problem after the split.

---

## Scope Integration (Plan C)

Plan C already has the rules call emitting `scope.active_domains` and `scope.skip_domains`. This integrates with the stream split as follows:

- If a stream's entire domain is in `skip_domains`, **skip that stream entirely** (do not call the LLM at all).
- Example: pure dialogue turn with `skip_domains: ["inventory", "pc_condition", "location_change"]` → skip stream 2 entirely, run only streams 1 and 3.
- This is the primary latency win from the split: on simple turns, one or two streams don't run.

```python
# In engine, before calling streams:
active = rules_outcome.scope.active_domains
skip = rules_outcome.scope.skip_domains

run_stream_1 = True  # scene always runs
run_stream_2 = not all(d in skip for d in ["inventory", "pc_condition"])
run_stream_3 = not all(d in skip for d in ["quest_updates", "established_facts", "compendium_npc"])
```

---

## New Files Required

| File | Purpose |
|------|---------|
| `ccya/prompts/extract_scene_system.j2` | System prompt for stream 1 |
| `ccya/prompts/extract_scene_user.j2` | User message for stream 1 |
| `ccya/prompts/extract_state_system.j2` | System prompt for stream 2 |
| `ccya/prompts/extract_state_user.j2` | User message for stream 2 |
| `ccya/prompts/extract_progress_system.j2` | System prompt for stream 3 |
| `ccya/prompts/extract_progress_user.j2` | User message for stream 3 |

The existing `extract_system.j2` and `extract_user.j2` are **not deleted** until all three streams are tested and confirmed stable. Keep them as fallback.

---

## Step-by-Step Implementation

### Step 1 — Create `extract_scene_system.j2`

Create a new file at `ccya/prompts/extract_scene_system.j2`. This is the system prompt for the scene stream.

Content:

```
You are the scene extractor. Your only job is to extract scene and location changes from a narration.
Do not reason about inventory, conditions, quests, or facts. Those are handled separately.

## Output schema
Emit a single JSON object with exactly these keys:

{
  "scene_tags": ["tag1", "tag2"],
  "scene_tagline": "one sentence describing the current scene mood and setting",
  "location_change": false,
  "location_id": null,
  "location_description": null,
  "present_npcs": []
}

## Field rules

`scene_tags`: 2-5 lowercase single-word or hyphenated tags describing the current mood and environment.
Examples: "tense", "crowded", "night", "underground", "hostile". Always emit at least 2.

`scene_tagline`: One sentence, present tense, describing what the scene feels like right now.
Example: "The market stalls empty quickly as tension rises between the guards."

`location_change`: true only if the player physically moved to a new location this turn. False for all other cases,
including if location was described but player did not move.

`location_id`: If location_change is true, emit the location id string from the known locations list.
If the new location is not in the known locations list, emit a snake_case id derived from its name.
If location_change is false, emit null.

`location_description`: If location_change is true, emit a 1-2 sentence description of the new location.
If location_change is false, emit null.

`present_npcs`: Full replacement list of named NPCs currently present in the scene after this turn.
This replaces the previous list entirely — include everyone present, not just newcomers.
Use the NPC's id from the known characters list. If an NPC is new, use a snake_case id from their name.
Emit an empty array [] if no named NPCs are present.

## Rules
- Emit null for any field that does not apply. Never omit a key.
- Do not add commentary or explanation outside the JSON object.
- Do not emit fields for other domains (inventory, conditions, quests, facts).
```

### Step 2 — Create `extract_scene_user.j2`

Create a new file at `ccya/prompts/extract_scene_user.j2`.

Content:

```jinja
## THIS TURN SCOPE
Active domains: {{ rules_outcome.scope.active_domains | join(", ") }}

## Player
{{ pc.name }} — {{ pc.tagline }}

## Current location
ID: {{ location.id }}
Name: {{ location.name }}
Description: {{ location.description }}

## Known locations
{% for loc in known_locations %}— {{ loc.id }}: {{ loc.name }}{% endfor %}

## Known characters
{% for npc in compendium %}— {{ npc.id }}: {{ npc.name }}{% endfor %}

## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

### Step 3 — Create `extract_state_system.j2`

Create a new file at `ccya/prompts/extract_state_system.j2`.

Content:

```
You are the state extractor. Your only job is to extract inventory changes and condition changes
from a narration. Do not reason about scene, quests, facts, or NPCs. Those are handled separately.

## Hard caps
- inventory_add: maximum 2 items per turn. If more than 2 seem to apply, pick the 2 most significant.
- pc_condition_add: maximum 2 per turn. Total active conditions must not exceed 5.

## Output schema
Emit a single JSON object with exactly these keys:

{
  "inventory_add": [],
  "inventory_remove": [],
  "inventory_update": [],
  "pc_condition_add": [],
  "pc_condition_remove": [],
  "_reasoning": ""
}

## Field rules

`inventory_add`: Items the player gained this turn. Each entry: {"id": "snake_case", "name": "Display Name", "amount": 1}.
Only add items explicitly received in the narration. Do not infer items from scene description.

`inventory_remove`: Items the player lost, used, or spent this turn. Each entry: {"id": "existing_item_id", "amount": 1}.
Use the exact id from the current inventory list.

`inventory_update`: Quantity or description changes to existing items. Each entry: {"id": "existing_item_id", "amount": new_total}.
Use this for ammo counts, partial consumption, etc. Use the exact id from the current inventory list.

`pc_condition_add`: New conditions affecting the player. Each entry: {"id": "snake_case", "label": "Short Label", "description": "one sentence"}.
Only add conditions with a clear cause in the narration. Do not duplicate existing conditions.

`pc_condition_remove`: Conditions that resolved this turn. Each entry: {"id": "existing_condition_id"}.
Prefer removing a resolved condition over adding a new similar one.
If the narration implies a condition resolved (healed, sobered, cleaned up), remove it even if not stated explicitly.

`_reasoning`: After filling all fields above, write 2-3 sentences checking your work.
Ask yourself: Did I miss a removal? Did I add a condition that already exists under a different name?
Did I add inventory that was described in scene but not actually given to the player?
This field is stripped by the engine before state is applied — write freely.

## Rules
- Emit empty arrays [] for fields with no changes. Never omit a key.
- Do not add commentary outside the JSON object.
- Do not emit fields for other domains (scene, quests, facts).
```

### Step 4 — Create `extract_state_user.j2`

Create a new file at `ccya/prompts/extract_state_user.j2`.

Content:

```jinja
## THIS TURN SCOPE
Active domains: {{ rules_outcome.scope.active_domains | join(", ") }}
{% if rules_outcome.scope.implicit_preconditions %}
Preconditions assumed: {{ rules_outcome.scope.implicit_preconditions | join("; ") }}
{% endif %}

## Player
{{ pc.name }} — {{ pc.tagline }}

## Active conditions
{% if pc.conditions %}
{% for c in pc.conditions %}— {{ c.id }}: {{ c.label }} ({{ c.description }}){% endfor %}
{% else %}
None.
{% endif %}

## Current inventory
{% if inventory %}
{% for item in inventory %}— {{ item.id }}: {{ item.name }} x{{ item.amount }}{% endfor %}
{% else %}
Empty.
{% endif %}

## Scene result (from scene stream)
Location: {{ scene_result.location_id if scene_result.location_change else location.id }}
Present NPCs: {{ scene_result.present_npcs | join(", ") if scene_result.present_npcs else "none" }}

## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

### Step 5 — Create `extract_progress_system.j2`

Create a new file at `ccya/prompts/extract_progress_system.j2`.

Content:

```
You are the progress extractor. Your only job is to extract quest updates, established facts,
and NPC compendium changes from a narration.
Do not reason about inventory, conditions, or scene cosmetics. Those are handled separately.

## Output schema
Emit a single JSON object with exactly these keys:

{
  "quest_updates": [],
  "established_facts_add": [],
  "established_facts_update": [],
  "established_facts_remove": [],
  "compendium_npc_update": [],
  "_reasoning": ""
}

## Field rules

`quest_updates`: Changes to quest state this turn.
Each entry: {"id": "quest_id", "status": "active|completed|failed", "objective": "updated objective string"}.
For new quests: {"id": "snake_case_new_id", "title": "Quest Title", "status": "active", "objective": "first objective"}.

QUEST THRESHOLD — read carefully:
{% if active_quests | length == 0 %}
No active quests exist. The bar for starting a new quest is LOW.
Any goal that will take more than one turn to resolve qualifies: a journey, an errand, finding someone,
resolving a conflict, delivering something, learning something specific. If the player is pursuing anything,
start a quest for it.
{% elif active_quests | length >= 3 %}
{{ active_quests | length }} quests are already active. The bar for starting a new quest is HIGH.
Only start a new quest if the narration introduces a major new obligation clearly distinct from all existing quests.
Do not fragment an existing quest into sub-quests.
{% else %}
Start a new quest if the narration introduces a clear new goal that will take multiple turns to resolve.
{% endif %}

`established_facts_add`: Durable facts learned this turn that are not already in the fact list.
Each entry is a plain string. Target 0-2 new facts per turn. Do not add facts already present under any wording.

`established_facts_update`: Facts in the list whose content changed this turn.
Each entry: {"old": "exact existing fact string", "new": "replacement string"}.

`established_facts_remove`: Facts that are now false or superseded.
Each entry is the exact existing fact string to remove.

`compendium_npc_update`: NPC records to create or update.
Each entry: {"id": "npc_id", "name": "Name", "bio": "one sentence", "disposition": "friendly|neutral|hostile|unknown", "status": "alive|dead|fled|unknown"}.
Only emit if the narration revealed new information about an NPC. Do not re-emit unchanged NPCs.

`_reasoning`: After filling all fields above, write 2-3 sentences checking your work.
Ask yourself: Is this new quest actually distinct from an existing one? Did I add a fact that's already in the list
with different wording? Did I miss a quest completion that the narration implied?
This field is stripped by the engine before state is applied — write freely.

## Rules
- Emit empty arrays [] for fields with no changes. Never omit a key.
- Do not add commentary outside the JSON object.
- Do not emit fields for other domains (inventory, conditions, scene).
```

### Step 6 — Create `extract_progress_user.j2`

Create a new file at `ccya/prompts/extract_progress_user.j2`.

Content:

```jinja
## THIS TURN SCOPE
Active domains: {{ rules_outcome.scope.active_domains | join(", ") }}
{% if rules_outcome.scope.ambiguities %}
Ambiguities to resolve: {{ rules_outcome.scope.ambiguities | join("; ") }}
{% endif %}

## Player
{{ pc.name }} — {{ pc.tagline }}

## Active quests
{% if active_quests %}
{% for q in active_quests %}— {{ q.id }}: {{ q.title }} | Objective: {{ q.objective }}{% endfor %}
{% else %}
None.
{% endif %}

## Established facts
{% if established_facts %}
{% for f in established_facts %}— {{ f }}{% endfor %}
{% else %}
None recorded yet.
{% endif %}

## Known characters
{% for npc in compendium %}— {{ npc.id }}: {{ npc.name }} — {{ npc.bio }} ({{ npc.disposition }}, {{ npc.status }}){% endfor %}

## Scene result (from scene stream)
Present NPCs this turn: {{ scene_result.present_npcs | join(", ") if scene_result.present_npcs else "none" }}

## State result (from state stream)
Inventory changes this turn: {{ state_result.inventory_add | length }} added, {{ state_result.inventory_remove | length }} removed

## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```

### Step 7 — Update Python engine to run three streams

Find the function in the engine that calls the extractor (currently calls `extract_system.j2` + `extract_user.j2`). Replace it with a new function:

```python
async def run_extraction(game_state: dict, narration: str, rules_outcome: dict) -> dict:
    """
    Runs the three extraction streams in sequence.
    Returns a merged state delta.
    """
    scope = rules_outcome.get("scope", {})
    active = scope.get("active_domains", ["scene", "inventory", "pc_condition", "quest_updates", "established_facts"])
    skip = scope.get("skip_domains", [])

    scene_result = {"scene_tags": [], "scene_tagline": "", "location_change": False,
                    "location_id": None, "location_description": None, "present_npcs": []}
    state_result = {"inventory_add": [], "inventory_remove": [], "inventory_update": [],
                    "pc_condition_add": [], "pc_condition_remove": []}
    progress_result = {"quest_updates": [], "established_facts_add": [],
                       "established_facts_update": [], "established_facts_remove": [],
                       "compendium_npc_update": []}

    # Stream 1 — scene (always runs)
    scene_ctx = build_scene_context(game_state, narration, rules_outcome)
    scene_raw = await llm_call("extract_scene", scene_ctx)
    scene_result = parse_and_strip(scene_raw)  # strips _reasoning if present

    # Stream 2 — state (skip if all state domains are skipped)
    state_domains = ["inventory", "pc_condition"]
    if not all(d in skip for d in state_domains):
        state_ctx = build_state_context(game_state, narration, rules_outcome, scene_result)
        state_raw = await llm_call("extract_state", state_ctx)
        state_result = parse_and_strip(state_raw)
    else:
        logger.debug("Skipping state stream — all state domains in skip_domains")

    # Stream 3 — progress (skip if all progress domains are skipped)
    progress_domains = ["quest_updates", "established_facts", "compendium_npc"]
    if not all(d in skip for d in progress_domains):
        progress_ctx = build_progress_context(game_state, narration, rules_outcome, scene_result, state_result)
        progress_raw = await llm_call("extract_progress", progress_ctx)
        progress_result = parse_and_strip(progress_raw)
    else:
        logger.debug("Skipping progress stream — all progress domains in skip_domains")

    # Merge all three into one delta dict
    return {
        **scene_result,
        **state_result,
        **progress_result
    }
```

The `parse_and_strip` helper:
```python
def parse_and_strip(raw: str) -> dict:
    """Parse JSON response, remove _reasoning before returning."""
    result = json.loads(raw)  # add error handling as needed
    result.pop("_reasoning", None)
    return result
```

The three `build_*_context` functions simply render the corresponding template pair with the right subset of game_state. Follow the same pattern as the existing context builder.

### Step 8 — Update `llm_call` to recognize new template names

Make sure `llm_call("extract_scene", ...)` knows to load `extract_scene_system.j2` + `extract_scene_user.j2`. Follow the same naming convention the engine already uses for `rules`, `narrate`, etc.

### Step 9 — Log all three stream outputs to events.jsonl

In the turn event log, record each stream separately:

```python
turn_event["extraction"] = {
    "scene": {
        "rendered_system": rendered_extract_scene_system,
        "rendered_user": rendered_extract_scene_user,
        "output": scene_result,
        "skipped": False
    },
    "state": {
        "rendered_system": rendered_extract_state_system,
        "rendered_user": rendered_extract_state_user,
        "output": state_result,
        "skipped": all(d in skip for d in state_domains)
    },
    "progress": {
        "rendered_system": rendered_extract_progress_system,
        "rendered_user": rendered_extract_progress_user,
        "output": progress_result,
        "skipped": all(d in skip for d in progress_domains)
    }
}
```

This is required by Plan H (debug UI) to render the pipeline view.

### Step 10 — Condition TTL via engine (do not add to prompts)

Track condition age in the engine, not in prompts. This keeps condition tokens out of the system prompt.

When a condition is added, stamp it:
```python
# When applying pc_condition_add:
condition["added_turn"] = current_turn_number
```

At the start of each turn, before running extraction, check for expired conditions:
```python
CONDITION_TTL_TURNS = 4  # adjust based on playtesting

expired = []
for c in game_state["pc"]["conditions"]:
    age = current_turn - c.get("added_turn", 0)
    if age >= CONDITION_TTL_TURNS:
        expired.append(c)

for c in expired:
    game_state["pc"]["conditions"].remove(c)
    logger.debug(f"Auto-expired condition: {c['id']} (age {age} turns)")
```

If any conditions were auto-expired, inject a block into `extract_state_user.j2` so the state stream doesn't re-add them:

```jinja
{% if engine_expired_conditions %}
## Auto-expired conditions (engine removed — do NOT re-add)
{% for c in engine_expired_conditions %}— {{ c.id }}: {{ c.label }}{% endfor %}
{% endif %}
```

---

## Rollback Plan

If the split introduces new problems, the original `extract_system.j2` and `extract_user.j2` are still in place. Add a feature flag:

```python
USE_SPLIT_EXTRACTION = True  # set False to revert to single call

if USE_SPLIT_EXTRACTION:
    delta = await run_extraction(game_state, narration, rules_outcome)
else:
    delta = await run_extraction_legacy(game_state, narration, rules_outcome)
```

Remove the flag and legacy path once the split is confirmed stable over 20+ turns.

---

## Checklist

- [ ] Create `extract_scene_system.j2`
- [ ] Create `extract_scene_user.j2`
- [ ] Create `extract_state_system.j2`
- [ ] Create `extract_state_user.j2`
- [ ] Create `extract_progress_system.j2`
- [ ] Create `extract_progress_user.j2`
- [ ] Add `build_scene_context()`, `build_state_context()`, `build_progress_context()` to engine
- [ ] Add `run_extraction()` to engine (replaces single extraction call)
- [ ] Register `extract_scene`, `extract_state`, `extract_progress` in `llm_call` dispatch
- [ ] Add `USE_SPLIT_EXTRACTION` feature flag
- [ ] Log all three stream outputs under `turn_event["extraction"]` in events.jsonl
- [ ] Add condition TTL stamping on `pc_condition_add`
- [ ] Add condition TTL check at turn start
- [ ] Add `engine_expired_conditions` injection to `extract_state_user.j2`
