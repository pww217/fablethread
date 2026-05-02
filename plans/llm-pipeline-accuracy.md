# CCYA LLM Pipeline — Accuracy Improvement Plans

## Architecture Overview (Current → Target)

**Current turn loop:**
```
player input → rules (intent + skill check) → narrate → extract → game state
```

**Target turn loop:**
```
player input → rules (intent + skill check) [ENHANCED: +scope boundaries]
                    ↓ intent envelope (with scope)
             → narrate [with labeled context blocks]
                    ↓ narration
             → extract [scope-constrained, reasoning-first schema]
                    ↓ state delta
             → game state update [_failed handling, token-threshold compaction]
```

The rules call already parses intent (`intent`, `intent_verb`, `target`, `stakes`). All plans below extend the existing architecture rather than adding new calls, except Plan F (compaction) which adds two new prompt files.

---

## Plan A: Context Block Labeling

### Problem
`narrate_system.j2` includes `_chronicle.j2` and `_recent.j2` as unlabeled context blocks. The narrator and extractor cannot distinguish between "established background" and "what just happened this turn." This causes:
- Narrator treating historical facts as still-active current scene details
- Extractor picking up old narrative details as new `established_facts_add`
- Occasional narration discrepancies from history bleeding into current-scene reasoning

### Implementation

**In `_chronicle.j2`** — wrap content in a labeled block:
```
## PRIOR HISTORY (summarized — treat as background, not current scene)
[existing chronicle content]
## END PRIOR HISTORY
```

**In `_recent.j2`** — add a section header:
```
## RECENT TURNS (most recent last — these are done, not current)
[existing recent turn content]
## END RECENT TURNS
```

**In `extract_user.j2`** — label the narration input:
```
## CURRENT TURN NARRATION (what just happened this turn — extract state changes from this)
[narration output]
## END CURRENT TURN NARRATION
```

### Notes
- Pure template changes — no Python logic required
- Zero latency impact
- Fastest win; implement first

---

## Plan B: Reasoning Field in Extractor Schema

### Problem
`extract_system.j2` emits enumerated deltas directly. The model commits to `quest_updates` and `inventory_add/remove` values before it has reasoned about what actually changed. LLMs generate left-to-right — whatever comes first in the output shapes what follows. Putting judgment-heavy enumerated fields first causes premature commitment errors on quests and inventory specifically.

### Implementation

Add `_reasoning` as the **first key** in the output schema in `extract_system.j2`, before `state_delta`:

```json
{
  "_reasoning": "string — free-form analysis before emitting any delta",
  "_failed": ["optional — precondition failures (see Plan C)"],
  "state_delta": { ... },
  "actions": [ ... ]
}
```

Add to the schema field guidance section:
```
- `_reasoning`: Before emitting any delta, write 2-4 sentences analyzing: what the
  player did, what the narrative resolved, which domains changed and why, and whether
  any quest objectives were completed or failed. Cross-check against the Established
  facts and quest lists already provided — do not add facts that are already listed.
  This field is stripped by the engine before state is applied — use it freely.
```

Verify `actions` is the **last** key in the schema definition (after all `state_delta` fields). Actions is a generative task; it should come after all analytical extraction.

**In Python engine** — strip before applying:
```python
response = llm_output  # parsed JSON
response.pop("_reasoning", None)  # discard — never reaches game state
failed = response.pop("_failed", [])  # handle separately (see Plan C)
delta = response.get("state_delta", {})
```

### Notes
- Adds ~30–60 output tokens per turn (small latency cost)
- The existing `Consolidation rule` in `extract_system.j2` becomes more effective once the model has a scratch space to apply it before committing
- The `_failed` field defined here is populated by scope logic in Plan C

---

## Plan C: Scope Boundaries via Rules Call Enhancement

### Problem
The extractor evaluates all domains every turn regardless of what the player did. A pure dialogue turn still triggers full quest/inventory/location reasoning. This causes:
- Spurious `established_facts_add` on low-information turns
- Phantom quest objective completions on unrelated turns
- Unmet-precondition actions being silently applied (e.g. grabbing keys when guard is still alive)

### Implementation

**Extend `rules_system.j2` output schema** with a `scope` field:

```json
{
  "intent": "...",
  "intent_verb": "...",
  "target": "...",
  "stakes": "...",
  "check": { ... },
  "scope": {
    "active_domains": ["scene", "present_npcs", "inventory", "quest_updates"],
    "skip_domains": ["location_change", "established_facts", "pc_condition"],
    "implicit_preconditions": ["guard must be incapacitated for key grab to succeed"],
    "ambiguities": ["'the chest' — which chest? resolve against location description"]
  }
}
```

**Domain values** (map to extractor field groups):
- `inventory` → `inventory_add`, `inventory_remove`, `inventory_update`
- `quest_updates` → quest status and objectives
- `location_change` → physical movement only
- `established_facts` → `established_facts_add/update/remove`
- `pc_condition` → `pc_condition_add/remove`
- `present_npcs` → NPC list replacement (include almost always)
- `scene` → always active: `scene_tags`, `scene_tagline`, `location_description`

**Add scope guidance to `rules_system.j2`:**
```
## Scope — active domains this turn
Emit `scope.active_domains` listing only the state domains that COULD change based on
the player's action. `scene` and `present_npcs` are always active.

Common mappings:
- Movement            → location_change, scene, present_npcs
- Combat              → inventory (ammo), pc_condition, present_npcs, quest_updates (if objective), scene
- Dialogue            → established_facts (if info revealed), quest_updates (if info revealed), present_npcs, scene
- Item interaction    → inventory, established_facts, scene
- Idle / observation  → scene, established_facts only

Emit `scope.skip_domains` for domains that definitely cannot change this turn.
Emit `scope.implicit_preconditions` for things the player assumes are true that may not be.
Emit `scope.ambiguities` for references that need world-state to resolve ("the chest", "him").
```

**In `extract_user.j2`** — inject scope block at the top, from `rules_outcome.scope`:

```jinja
## THIS TURN SCOPE
Active domains: {{ rules_outcome.scope.active_domains | join(", ") }}
Skip domains: {{ rules_outcome.scope.skip_domains | join(", ") }}
{% if rules_outcome.scope.implicit_preconditions %}
Preconditions assumed: {{ rules_outcome.scope.implicit_preconditions | join("; ") }}
{% endif %}
{% if rules_outcome.scope.ambiguities %}
Ambiguities to resolve: {{ rules_outcome.scope.ambiguities | join("; ") }}
{% endif %}

[rest of existing extract_user content]
```

**Add SKIP enforcement to `extract_system.j2`** (after the schema block, before field guidance):
```
## Domain scope (provided each turn in user message)
- For domains listed in **Active domains**: extract changes normally.
- For domains listed in **Skip domains**: emit null / empty / omit entirely.
  Do NOT reason about skip domains even if narratively adjacent.
- Use **Preconditions assumed** to validate downstream effects.
  If a precondition was not met, emit `_failed` with a description.
- Use **Ambiguities** to resolve references before emitting IDs.
```

**In Python engine** — handle `_failed`:
```python
failed = response.pop("_failed", [])
if failed:
    # Log for debugging
    logger.debug(f"Turn {turn}: failed preconditions: {failed}")
    # Optionally: store in turn record to pass as context to next narration
    turn_record["failed_preconditions"] = failed
```

To pass failures into the next narration turn (optional), add to `narrate_system.j2`:
```jinja
{% if last_turn_failed %}
## Previous turn — failed actions
The following player actions did not succeed due to unmet conditions:
{% for f in last_turn_failed %}— {{ f }}
{% endfor %}The narrator already resolved these in prose. Do not retry them.
{% endif %}
```

### Notes
- Rules call already does intent parsing — scope is a ~5 token addition to an existing call
- `scene` and `present_npcs` should be in `active_domains` almost every turn
- `skip_domains` is most useful for `quest_updates` and `location_change` on dialogue/idle turns

---

## Plan D: Active-Domain State Slicing (Extractor Only)

### Problem
`extract_user.j2` injects full game state every turn — full inventory, all quests, all established facts, all NPCs — even on turns where only 1-2 domains are active. This adds input tokens and model attention load for state the extractor doesn't need.

### Implementation

**In Python engine**, build a `state_slice` from `scope.active_domains` before rendering `extract_user.j2`:

```python
def build_state_slice(game_state: dict, active_domains: list[str]) -> dict:
    slice = {}
    if "inventory" in active_domains:
        slice["inventory"] = game_state["inventory"]
    if "quest_updates" in active_domains:
        slice["quests"] = game_state["quests"]
    if "established_facts" in active_domains:
        slice["established_facts"] = game_state["established_facts"]
    if "pc_condition" in active_domains:
        slice["conditions"] = game_state["pc"]["conditions"]
    # Always include:
    slice["present_npcs"] = game_state["present_npcs"]
    slice["location"] = game_state["location"]
    slice["pc_core"] = {"name": game_state["pc"]["name"], "stats": game_state["pc"]["stats"]}
    return slice
```

Pass `state_slice` into the extractor template instead of full game state.

**Keep full state in `narrate_system.j2`** — the narrator needs all context to write coherent prose. Slicing is extractor-only.

### Notes
- Implement after Plan C is stable (scope boundaries must exist before slicing is safe)
- Always include `present_npcs`, `location`, and `pc_core` regardless of active_domains
- Greatest token savings on combat turns (skip quests, established_facts) and dialogue turns (skip inventory, location_change)

---

## Plan E: `actions` Generation Placement

### Problem
`actions` (4 player choices) is generated in the same extractor call as state delta. These are fundamentally different tasks — state extraction is analytical (parse + classify), action generation is creative (invent + weight by stats). The creative task can cause the model to drift into generative mode mid-extraction.

### Options

**Option 1 — Recommended: Move `actions` to narrate call**
The narrator already has full context and is in generative mode. Append actions as a structured JSON block after the prose.

Narrate output format:
```
[prose narration]

ACTIONS_JSON: {"actions": ["...", "...", "...", "..."]}
```

Parse in Python:
```python
if "ACTIONS_JSON:" in narrate_output:
    prose, actions_raw = narrate_output.split("ACTIONS_JSON:", 1)
    actions = json.loads(actions_raw.strip())["actions"]
else:
    prose = narrate_output
    actions = []  # fallback
```

Add to `narrate_system.j2`:
```
## Actions
After the narration prose, emit exactly one line:
ACTIONS_JSON: {"actions": ["choice 1", "choice 2", "choice 3", "choice 4"]}

Actions rules (same as current extract rules):
- Exactly 4 distinct, meaningful choices valid in the current scene, 7-10 words each
- Weight toward character's stronger stats through what the options *are*, not labels
- One fallback/cautious option regardless of stats
- Never offer all four as the same flavor
```

Remove `actions` from `extract_system.j2` schema entirely.

**Option 2 — Minimal change: Verify key order in extract**
Ensure `actions` is the last key in the schema definition in `extract_system.j2` (after all `state_delta` fields). No other change needed.

### Notes
- Try Option 2 first (free) after Plan B; if action quality or extraction quality improves, done
- Option 1 if extraction errors persist and action quality is a factor

---

## Plan F: Context Compaction Redesign

### Problem
Compaction currently fires on a fixed turn cadence. This means:
- Compaction fires on short turns that haven't grown context
- May not fire after dense multi-event turns that bloat context quickly
- Compaction blocks the turn loop (~20s)

### Token Threshold Trigger

**In Python engine**, replace fixed-cadence check with token count:

```python
COMPACTION_THRESHOLD_CHARS = 8000  # ~2000 tokens at 4 chars/token
COMPACTION_MIN_TURNS = 3

def should_compact(recent_turns: list, turn_number: int) -> bool:
    if turn_number < COMPACTION_MIN_TURNS:
        return False
    total_chars = sum(
        len(t.get("narrative", "")) + len(t.get("input", ""))
        for t in recent_turns
    )
    return total_chars > COMPACTION_THRESHOLD_CHARS
```

Tune `COMPACTION_THRESHOLD_CHARS` based on observed context growth. Start at 8000 and adjust.

### Compactor Prompt: `compact_system.j2` (new file)

```
You are a game historian. Compress recent turn history into a compact summary
for use as context in a text adventure. The summary replaces the raw turn log.

## Preserve (must survive compression)
- Named NPCs introduced: name, disposition toward player, current status (alive/dead/fled/unknown)
- Items the player gained or lost that are NOT already in the current inventory list
- Quest objectives completed or failed this period
- Locations visited and their narrative significance
- Any durable facts NOT yet in the established facts list
- Consequences still active: wounds, debts, changed relationships, outstanding threats

## Discard
- Flavor text and atmosphere with no lasting consequence
- Failed actions with no consequence
- Repeated descriptions of the same location
- Dialogue that revealed no new information and changed no relationship
- Events already captured in established_facts

## Output
Emit a single JSON object only:
{
  "summary": "2-4 paragraph prose summary of what happened, in past tense",
  "new_facts": ["net-new durable facts not already in established_facts — omit if none"],
  "turns_compressed": N
}
```

### Compactor User Message: `compact_user.j2` (new file)

```jinja
## Current inventory (for reference — do not re-list)
{% for item in inventory %}— {{ item.name }} ({{ item.amount }}){% endfor %}

## Established facts (already stored — do not duplicate)
{% for f in established_facts %}— {{ f }}
{% endfor %}

## Recent turns to compress
{% for t in recent_turns %}
Turn {{ t.turn }}: {{ t.input }}
{{ t.narrative }}
{% endfor %}
```

### Python Engine Integration

```python
def run_compaction(game_state):
    result = llm_call("compact", game_state)  # uses compact_system + compact_user
    first_turn = game_state["recent_turns"][0]["turn"]
    last_turn = game_state["recent_turns"][-1]["turn"]

    # Archive compressed turns to chronicle
    game_state["chronicle"].append({
        "turn_range": f"{first_turn}-{last_turn}",
        "summary": result["summary"]
    })

    # Clear recent turns
    game_state["recent_turns"] = []

    # Merge new facts with dedup
    existing = set(game_state["established_facts"])
    for fact in result.get("new_facts", []):
        if fact not in existing:
            game_state["established_facts"].append(fact)
            existing.add(fact)
```

**Ensure `_chronicle.j2`** renders `chronicle` entries (compressed summaries, labeled `PRIOR HISTORY`) separately from `_recent.j2` (raw recent turns). They are different data structures and should have different section headers per Plan A.

### Notes
- Run compaction at end of turn, before returning to player — or async if architecture supports it
- Inventory is passed to compactor for reference so it doesn't re-surface already-tracked items as "new facts"
- `turns_compressed` field is for logging/debugging only

---

## Summary: Changes by File

| File | Change | Plan |
|------|--------|------|
| `ccya/prompts/sections/_chronicle.j2` | Add `PRIOR HISTORY` label wrapper | A |
| `ccya/prompts/sections/_recent.j2` | Add `RECENT TURNS` label wrapper | A |
| `ccya/prompts/extract_user.j2` | Add `CURRENT TURN NARRATION` label; inject scope block at top | A, C |
| `ccya/prompts/extract_system.j2` | Add `_reasoning` first in schema; add `_failed`; add SKIP DOMAINS instruction; verify `actions` is last | B, C, E |
| `ccya/prompts/rules_system.j2` | Add `scope` object to output schema + domain-mapping guidance | C |
| `ccya/prompts/narrate_system.j2` | Add `last_turn_failed` block (optional); add `actions` output if Option 1 chosen | C, E |
| Python engine | Strip `_reasoning`/`_failed`; `build_state_slice()`; token-threshold compaction trigger; `_failed` logging | B, C, D, F |
| `ccya/prompts/compact_system.j2` | New file | F |
| `ccya/prompts/compact_user.j2` | New file | F |

## Recommended Implementation Order

1. **A** — labels (template only, zero risk, immediate signal)
2. **B** — reasoning field (schema change + 2-line Python strip)
3. **C** — scope boundaries (extends rules call + extractor)
4. **D** — state slicing (depends on C being stable)
5. **E** — actions placement (evaluate after B; implement if needed)
6. **F** — compaction redesign (current cadence is functional; do last)
