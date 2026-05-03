# Plan G — Split Extraction Into Three Focused Streams

## Status: Done (implemented 2026-05-03)

---

## Why We're Doing This

The current extractor runs one LLM call that is asked to do many different things at once:
- Classify scene cosmetics (tags, tagline, who is present, suggested actions, outcome flavor)
- Calculate mechanical deltas (inventory changes, condition changes)
- Track long-horizon progress (quests, recent events, NPC compendium)

These are fundamentally different tasks. When they compete for the model's attention in one call, the model makes tradeoffs. The most common failure modes:

- **Conditions accumulate and never resolve.** The model sees a long list of other fields to fill and takes the easy path: add a condition, skip the removal check.
- **Quests don't start.** The model is mid-stream filling inventory and condition fields when it reaches `quest_updates`. It under-invests attention on quest reasoning because the "hard part" feels done.
- **Recent events duplicate.** `recent_events_add` gets items already in the list because the model's working memory is spread thin.

The fix is to break the single extraction call into three smaller calls, each with a narrow, well-defined job. Each call gets its own system prompt focused only on its concern.

**Token cost is roughly flat per turn**, but the *budget allocation* is the point: each stream's input is sliced down to only the state it actually needs. See the **Token Efficiency** section below — this is non-negotiable for the split to be worth it.

---

## Concurrent schema changes

Two breaking schema changes ride along with this split. No backward compatibility — old saves are not migrated.

### 1. `pc.conditions` becomes structured

Today: `list[str]` (e.g. `["bruised ribs", "shaken"]`).
After: `list[Condition]`:

```python
class Condition(BaseModel):
    id: str            # snake_case dedup key, e.g. "bruised_ribs"
    label: str         # short tag for prompts, 1-4 words, e.g. "bruised ribs"
    description: str = ""  # one sentence; optional, used in narrate context
    added_turn: int    # set by engine on add — drives TTL
```

This:
- Eliminates fragile string-normalization dedup (`_normalize_condition` goes away).
- Gives TTL a place to live (`added_turn`).
- Lets `extract_state_user.j2` show only `id` + `label` to streams 2 and 3 (saves tokens vs. full strings with markdown noise).

`pc_condition_add` delta items become `{id, label, description?}`. `pc_condition_remove` becomes `{id}` (id-only, no string match). `apply_delta` stamps `added_turn = state.meta.turn` on every add.

### 2. Recent events are the only mutable fact list

The plan originally said `established_facts_*` — that field no longer exists. The codebase has:
- `scene.recent_events`: mutable, owned by stream 3.
- `scene.world_state`: immutable genre canon, never touched by extractor.

Stream 3 emits `recent_events_add / recent_events_update / recent_events_remove` only. `world_state` is read-only context (and only included where genuinely useful — see Token Efficiency).

---

## The Three Streams

### Stream 1 — Scene + UI hints
**Job:** What does the scene look like right now? Who's in it? What can the player do next?

Fields owned:
- `scene_tags` (list of short tags)
- `scene_tagline` (3–6 word UI header)
- `location_change` (`LocationRef | null`)
- `location_description` (in-place description refresh when no move)
- `present_npcs` (full `list[NpcRef]` — same shape as today)
- `actions` (4 player choices for the UI pills)
- `outcome_summary` (one-sentence flavor of what just happened, drawn from narration)

Why `actions` + `outcome_summary` live here: they're cosmetic, derive purely from the narration, and don't depend on inventory/quest reasoning. Folding them into stream 1 avoids a 4th round-trip while keeping streams 2 and 3 laser-focused on state.

This stream runs first because the other two need its `present_npcs` and `location_change`.

### Stream 2 — State
**Job:** What physically changed for the player right now?

Fields owned:
- `inventory_add` (capped at 2/turn)
- `inventory_remove`
- `inventory_update`
- `pc_condition_add` (capped at 2/turn; structured)
- `pc_condition_remove` (id-only)

Conditions and inventory are grouped because they're both immediate mechanical deltas — things that changed *this turn* with concrete cause in the narration.

### Stream 3 — Progress
**Job:** What did the player learn or accomplish that persists beyond this scene?

Fields owned:
- `quest_updates`
- `recent_events_add`
- `recent_events_update`
- `recent_events_remove`
- `compendium_npc_update` (current shape: `id, name?, title?, bio?` — no `disposition`/`status`)

This stream runs last so it can connect items gained (stream 2) to quest objectives, and reason about NPCs whose presence was just established (stream 1).

---

## Cross-Stream Dependencies

| Stream | Receives from prior streams | Why |
|--------|-----------------------------|-----|
| Scene (1) | nothing | Runs first; observational + UI |
| State (2) | `scene.present_npcs` (id + name only), `scene.location_change` (id only) | Knows who's present for cause/effect on conditions; knows if scene moved (affects what loot is in reach) |
| Progress (3) | `scene.present_npcs` (id + name), `state.inventory_add[*].name`, `state.inventory_remove[*].id` | NPC presence for compendium upserts; item deltas for quest objective resolution |

### The inventory question — two different things

Progress receives **two separate things** related to inventory:

1. **The full inventory list** (from game state, included only when needed) — the *before* picture. Used to avoid starting a quest for something the player already owns.
2. **Item names gained/lost this turn** (from `state_result`, passed as cross-stream context) — the *delta*. Lets progress connect "iron key gained" → resolve "find the key" objective.

These are not redundant.

### What streams do NOT receive

- Scene gets no inventory, no quests, no recent_events, no conditions.
- State gets no quests, no recent_events, no compendium summary.
- Progress gets no full inventory mutations (just item names), no condition deltas.

---

## Execution Order

```
narration
    → stream 1 (scene)      ← runs first, no dependencies
    → stream 2 (state)      ← receives scene_result
    → stream 3 (progress)   ← receives scene_result + state_result
    → merge into single StateDelta + ExtractResult
    → validate + apply_delta
```

Streams 2 and 3 don't depend on each other and *could* run in parallel. **Do not implement parallel execution yet.** On a local GPU they'd compete for the same hardware. Sequential for MVP.

---

## Scope Integration (Plan C)

The rules call already emits `scope.active_domains` and `scope.skip_domains`. Integration:

- If a stream's *entire* domain set is in `skip_domains`, skip the LLM call for that stream entirely.
- Stream 1 (scene): always runs — UI needs `actions` and `scene_tagline` every turn.
- Stream 2 (state): skip if `{"inventory", "pc_condition"} ⊆ skip_domains`.
- Stream 3 (progress): skip if `{"quest_updates", "recent_events", "compendium_npc"} ⊆ skip_domains`.

This is the primary latency win: pure-dialogue turns skip streams 2 and/or 3 entirely.

---

## Token Efficiency — the hard requirement

Three calls instead of one means more *prompt overhead*. The split only pays off if each stream's input is aggressively scoped down. The rules below are non-negotiable.

### Per-stream input matrix

Legend: ✅ included; ⛔ never included; 🔶 conditional (see notes).

| Section | Scene | State | Progress |
|---|:-:|:-:|:-:|
| `pc.name` + `pc.tagline` | ✅ | ✅ | ✅ |
| `pc.bio` | ⛔ | ⛔ | ⛔ |
| `pc.stats` | 🔶 (only for `actions` flavoring) | ⛔ | ⛔ |
| `pc.conditions` (id + label only) | 🔶 (only for `actions` flavoring) | ✅ (full: id, label, description) | ⛔ |
| Current location | ✅ (id, name, description) | 🔶 (id only, from scene_result) | ⛔ |
| Known locations | 🔶 (omit if scope says no movement plausible) | ⛔ | ⛔ |
| Compendium summary (top-N LRU) | ✅ (id + name only) | ⛔ | ✅ (id, name, title, bio_preview) |
| `present_npcs` (current state) | ⛔ (narration is source of truth) | 🔶 (id + name only, from scene_result) | 🔶 (id + name only, from scene_result) |
| Inventory (full list) | ⛔ | ✅ (id, name, amount) | 🔶 (id, name only — only if quest active or new quest plausible) |
| Active quests | ⛔ | ⛔ | ✅ (id, title, objectives with index) |
| Recent events list | ⛔ | ⛔ | ✅ |
| World state | ⛔ | ⛔ | 🔶 (only when stream 3 needs to reason about a new quest — gate behind `active_quests | length == 0`) |
| Rules outcome | 🔶 (band only, for `outcome_summary` flavoring) | ✅ (full — directive drives harm/loss application) | 🔶 (band only — only successful bands resolve objectives) |
| Scope.active_domains | ✅ | ✅ | ✅ |
| Scope.implicit_preconditions | ⛔ | ✅ | ⛔ |
| Scope.ambiguities | ⛔ | ⛔ | ✅ (NPC + quest reference resolution) |
| Engine-expired conditions | ⛔ | ✅ | ⛔ |
| Cross-stream: scene_result | — | ✅ (subset) | ✅ (subset) |
| Cross-stream: state_result | — | — | ✅ (item names only) |
| Narration | ✅ | ✅ | ✅ |

### Conditional rendering rules (use Jinja `{% if %}` liberally)

The current `extract_user.j2` uses a `__HIDDEN__` sentinel to tell the model "this section exists but isn't relevant." **Drop that pattern in the new templates.** When a section isn't relevant to a stream, don't render it at all — no header, no placeholder. The model can't be distracted by tokens that don't exist.

Mandatory conditional gates per template:

- `extract_scene_user.j2`:
  - `Known locations` block: render only if `rules_outcome.scope.active_domains | select("eq", "location_change") | list | length > 0`.
  - `Player stats + conditions` block: render only if scope contains intent verbs that affect action options (always true for combat/social/exploration; could be omitted for pure observation turns — for MVP, always include).
  - `Rules outcome` line: render only if `rules_outcome.rolled` (only one line: band + skill + directive — keep tight).

- `extract_state_user.j2`:
  - `Active conditions` block: render only if `"pc_condition" in active_domains`.
  - `Auto-expired conditions` block: render only if `engine_expired_conditions` is non-empty.
  - `Current inventory` block: render only if `"inventory" in active_domains`.
  - `Scene result` block: render only if `scene_result.location_change` or `scene_result.present_npcs`.

- `extract_progress_user.j2`:
  - `Active quests` block: render only if quests exist.
  - `Recent events` block: render only if recent_events exist.
  - `World state` block: render only if `active_quests | length == 0` (low-bar new-quest reasoning needs world canon; established-quest turns don't).
  - `Known characters` block: render only if compendium is non-empty.
  - `Inventory delta` block: render only if `state_result.inventory_add` or `state_result.inventory_remove` is non-empty.
  - `Quest threshold` block in system prompt: keep the existing `{% if active_quests | length == 0 / >= 3 %}` ladder — it's already conditional.

### Shared compendium slice — build once

`_known_characters_for_extract` already builds a top-10 LRU compendium summary. The split needs:
- Scene: `id` + `name` only (compact, used for `present_npcs` id matching).
- Progress: `id` + `name` + `title` + `bio_preview` (richer, used for compendium upsert decisions).

Add a `compact: bool = False` flag to the helper rather than building two lists. Stream 1 calls with `compact=True`.

### Cross-stream payload — minimum surface

When passing scene_result to streams 2/3, pass only:

```python
{
    "location_id": scene_result.location_change.id if scene_result.location_change else current_location_id,
    "location_changed": bool(scene_result.location_change),
    "present_npcs": [{"id": n.id, "name": n.name} for n in scene_result.present_npcs],
}
```

When passing state_result to stream 3, pass only:

```python
{
    "items_gained": [it.name for it in state_result.inventory_add],
    "items_lost": [it.id for it in state_result.inventory_remove],
}
```

No full StateDelta passing between streams. No JSON dumping. Render these as plain prose lines in the user template.

### What to delete from the current `extract_user.j2` for the new templates

Don't carry over: the `__HIDDEN__` placeholder branches, the long markdown rules section (move to per-stream system prompts only where relevant), the `Previous turn NPCs` block in any stream other than scene (only scene reasons about who's there now; state/progress get the post-extraction set from scene_result).

### Measurement gate

After implementation, log per-stream prompt + response token counts to `events.jsonl`. The acceptance bar:

- Sum of three streams' input tokens ≤ 1.4× current single-call input tokens (the 40% headroom covers the per-call schema overhead).
- On turns where stream 2 or 3 is skipped, total tokens should drop below the current baseline.

If the sum exceeds 1.4×, the conditional gates above aren't aggressive enough — tighten them before merging.

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

`extract_system.j2` and `extract_user.j2` are **deleted** — no fallback. The new pipeline replaces the old call directly.

---

## Step-by-Step Implementation

### Step 1 — Schema changes (`models.py`)

Add structured condition models:

```python
class Condition(BaseModel):
    id: str
    label: str
    description: str = ""
    added_turn: int = 0  # stamped by engine

class ConditionAdd(BaseModel):
    id: str
    label: str
    description: str = ""

class ConditionRemove(BaseModel):
    id: str
```

Update `StateDelta`:
- `pc_condition_add: list[ConditionAdd]` (max 2)
- `pc_condition_remove: list[ConditionRemove]`

`pc.conditions` in state.yaml becomes `list[Condition]`. `_normalize_condition` is deleted.

### Step 2 — `apply_delta` updates (`state.py`)

- Stamp `added_turn = state.meta.turn` on every condition added.
- Dedup by `id` (not normalized string).
- Removal matches by `id`.
- TTL eviction lives in the engine's per-turn pre-extraction step (Step 8), not in `apply_delta`.

Delete `_normalize_condition`. Update `summarize_changes` and `format_change_lines` to read structured conditions (use `c.label` for display).

### Step 3 — Create `extract_scene_system.j2`

System prompt covers: `scene_tags`, `scene_tagline`, `location_change`, `location_description`, `present_npcs`, `actions`, `outcome_summary`. Output schema is one JSON object. Includes the existing `present_npcs` hydration rules (id-only when known to compendium) and the `actions` weighting guidance from the current extract prompt.

### Step 4 — Create `extract_scene_user.j2`

Render only the sections in the Per-stream input matrix marked ✅ for Scene. Apply conditional gates from the Token Efficiency section.

### Step 5 — Create `extract_state_system.j2`

System prompt covers: inventory ops + structured conditions. Includes inventory hard caps, weapons-need-ammo rule, condition cap (5 active), `_reasoning` field for self-check.

### Step 6 — Create `extract_state_user.j2`

Render only ✅ sections. Include `engine_expired_conditions` block conditionally. Cross-stream `scene_result` block at the bottom.

### Step 7 — Create `extract_progress_system.j2`

System prompt covers: `quest_updates`, `recent_events_*`, `compendium_npc_update`. Includes the quest threshold ladder (`length == 0` → low bar, `length >= 3` → high bar). `_reasoning` field for self-check.

### Step 8 — Create `extract_progress_user.j2`

Render only ✅ sections. Include `state_result` inventory delta as plain text lines. Conditional `world_state` only when no active quests.

### Step 9 — Engine changes (`engine.py`)

Replace `_extract_messages` + the single extract call in `run_turn` with:

```python
async def _run_extraction_pipeline(
    env, state, narration, *, rules_outcome, intent, config, trace_id, log_prompts, turn_no
) -> tuple[StateDelta, list[str], str, dict]:  # returns (delta, actions, outcome_summary, per_stream_metrics)
```

Internally:
1. Tick condition TTL: drop `pc.conditions` whose `state.meta.turn - added_turn >= CONDITION_TTL_TURNS`. Collect them as `engine_expired_conditions` for stream 2.
2. Build scene messages → call → parse → `scene_result`.
3. Decide stream 2 skip; if not skipped, build state messages with `scene_result` → call → parse → `state_result`.
4. Decide stream 3 skip; if not skipped, build progress messages with both prior results → call → parse → `progress_result`.
5. Merge into one `StateDelta`. Return `(delta, scene_result.actions, scene_result.outcome_summary, metrics)`.

Per-stream parse helper strips `_reasoning` before Pydantic validation (same as current).

### Step 10 — `events.jsonl` logging

Replace the single `extract` event field with:

```python
event["extraction"] = {
    "scene":    {"rendered_system": ..., "rendered_user": ..., "output": scene_result, "skipped": False, "tokens_in": ..., "tokens_out": ..., "ms": ...},
    "state":    {... or {"skipped": True}},
    "progress": {... or {"skipped": True}},
}
```

Sum the three for the rolled-up `metrics.extract` (keep the same TurnResult shape so the UI doesn't break).

### Step 11 — Condition TTL constant

```python
CONDITION_TTL_TURNS = 4  # tunable; expose via EngineConfig
```

Add `condition_ttl_turns: int = 4` to `EngineConfig`. The engine's pre-extraction tick uses it.

### Step 12 — Tests

Add to `tests/test_engine_smoke.py`:
- Each stream's prompt renders without error from a representative state.
- Skip logic: a `skip_domains` covering all of stream 2's domains causes only streams 1 and 3 to be called (mock `llm_chat` and assert call count).
- Condition TTL: a condition with `added_turn = 0` and `state.meta.turn = 4` is removed by the pre-extraction tick.
- Structured condition round-trip: `pc_condition_add` → `apply_delta` → state has `Condition` with `added_turn` stamped.

---

## Checklist

- [ ] `Condition`, `ConditionAdd`, `ConditionRemove` in `models.py`; `StateDelta.pc_condition_*` updated
- [ ] `apply_delta` handles structured conditions + stamps `added_turn`; `_normalize_condition` deleted
- [ ] `summarize_changes` / `format_change_lines` read `c.label`
- [ ] UI renderers (`index.html`, `_summarize_applied`) updated for structured conditions
- [ ] `extract_scene_system.j2` + `extract_scene_user.j2` created (with conditional gates)
- [ ] `extract_state_system.j2` + `extract_state_user.j2` created (with conditional gates)
- [ ] `extract_progress_system.j2` + `extract_progress_user.j2` created (with conditional gates)
- [ ] `_known_characters_for_extract` gains `compact` flag
- [ ] `_run_extraction_pipeline` in engine; old `_extract_messages` deleted
- [ ] `extract_system.j2` + `extract_user.j2` deleted
- [ ] Per-stream entries in `events.jsonl` under `extraction`; rolled-up `metrics.extract` preserved
- [ ] `CONDITION_TTL_TURNS` + `EngineConfig.condition_ttl_turns`; pre-extraction TTL tick
- [ ] Tests: per-stream render, skip logic, condition TTL, structured condition round-trip
- [ ] Token measurement gate verified (`sum ≤ 1.4× current single-call baseline`)
