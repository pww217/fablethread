# Compactor Plan: Context Token Reduction

Goal: periodically compact game state context so prompt size stays bounded over
long playthroughs without losing mechanically or narratively important information.

The compactor runs every N turns (configurable, default 4). It operates in two
modes:
- **Rendering-time** — filters/truncates what gets passed to the Jinja template.
  State on disk is untouched.
- **State mutation** — writes back to `state.yaml` / `chronicle.md`. Used sparingly,
  only when data has genuinely expired.

All compaction logic must apply dynamic relevance judgment: "does this information
affect current game mechanics or story continuity?" is the test. Recency alone is
not enough reason to purge — a plot thread from 20 turns ago may still matter.
Freshness of items that are no longer mechanically relevant is the target.

---

## Compaction Targets

### 1. Narrative history (`recent_turns` + chronicle tail)
**Mode:** State mutation + rendering filter
**Trigger:** Every N turns, for turns older than `window_turns`

The `window_turns` config controls how many full-prose turns appear in `## Recent Turns`.
Turns that age out of that window are currently appended verbatim to `chronicle.md`,
which is then fed back via `chronicle_tail` with a token budget cap.

The compactor replaces verbatim prose with a bullet-list summary **before** it lands
in the chronicle, or re-summarizes existing verbose chronicle sections. Each summary
bullet must prioritize:
- Named NPCs who were present or affected
- Location where the turn took place
- Quest-relevant outcomes (objective resolved, objective failed, new info gained)
- Mechanical consequences (conditions gained/lost, key items gained/lost)
- Tone-setting moments that inform ongoing plot

The compactor prompt must explicitly instruct the LLM:
> Preserve everything that has mechanical weight or forward story consequence.
> Cull flavor detail, atmospheric description, and dialogue that does not
> introduce named characters, change relationships, or alter quest/item state.
> Do not summarize away named NPC introductions, death/departure events, or
> any moment where the player character made an irreversible choice.

Format: one bullet per turn, 1-2 lines max:
```
- [T12] Docked at Ilus Station; met Drummer (dockworker, hostile). Lost access card.
- [T13] Persuaded Naomi to vouch for entry. Quest: Find Holden → new lead: cargo bay 7.
```

---

### 2. `recent_events` list
**Mode:** State mutation (prune `state.scene.recent_events`)
**Trigger:** Every N turns (same compaction pass)

`recent_events` caps at 15 entries and accumulates full-text strings.
Entries older than ~5 turns are candidates for removal **unless** they satisfy
at least one of:
- Mentions a name matching a current `present_npc.name` (or compendium alias)
- Mentions a word overlapping with an active quest `id` or `description`
- Mentions a word overlapping with an active `scene_pressure.text`
- The event is the most recent mention of a location the player may return to

Removal is by list position + keyword scan — purely mechanical, no LLM call needed.
This is a purge, not a summarize: if the event fails relevance, it's gone.

The compactor function signature:
```python
def _prune_recent_events(
    events: list[str],
    current_turn: int,
    present_npc_names: set[str],
    active_quest_ids: set[str],
    active_pressure_texts: list[str],
    max_age: int = 5,
) -> list[str]:
    ...
```

---

### 3. Completed/failed quests
**Mode:** Rendering-time filter only
**Trigger:** Every turn (no compaction pass needed — just fix the Jinja template)

Completed and failed quests are injected into every narrate/extract prompt via
`_quests.j2`. They have zero prompt value once resolved — the narrator does not
need to know what the PC used to want.

Fix: update `_quests.j2` to filter:
```jinja
{% for q in state.pc.quests if q.status == 'active' %}
```

Keep completed/failed quests in `state.yaml` for player-facing UI — this is a
rendering filter only, no state change.

Also applies to extract prompts: `extract_progress_user.j2` should only show
active quests when listing current state for the extractor to compare against.

---

### 4. NPC `bio` in `present_npcs`
**Mode:** Rendering-time filter
**Trigger:** Every turn (conditional on `in_scene`)

NPC fields are now delta-based: only `notes` updates each turn; `bio`, `name`,
`title`, etc. default to null and are set once. `bio` can be multi-sentence and
represents personality/backstory.

Rule:
- If NPC is `in_scene = true` (currently present): include full `bio`
- If NPC is in `recently_left`: omit `bio`, keep `name` + `title` only
- Never-present NPCs are never in `present_npcs` at all

Old NPCs can return — when they re-enter `in_scene = true`, bio is restored.
This is already structurally handled since bio lives in the compendium and is
looked up at render time, not stored in `present_npcs` directly.

Implementation: in the narrate context builder, when hydrating `present_npcs`
from compendium for NPCs in `recently_left`, emit only `{name, title}` and
omit `bio` and `notes`.

---

### 5. `location.description` update discipline
**Mode:** Prompt tightening (extract_scene instruction change)
**Trigger:** No code change — update `extract_scene_system.j2`

The location description delta should only be written when a notable environmental
or tonal change has occurred in the narration — not as a routine re-description
of the same space.

Add to `extract_scene_system.j2`:
> `location.description`: Only emit this field if the narration describes a
> meaningful environmental or atmospheric change to the current location — a
> shift in lighting, weather, crowd density, physical damage, or emotional
> register of the space. Do not re-describe unchanged surroundings. If the
> scene looks and feels the same as before, omit `description` entirely.

This prevents the model from re-filling the description field every turn with
slight paraphrases of the same text, which inflates every subsequent prompt
after the first few turns in a location.

---

## What Is NOT Compacted

| Field | Reason |
|---|---|
| `world_state` | Immutable, small, foundational to setting |
| PC stats, skills | Always mechanically required |
| PC conditions | Actively affect rolls |
| Active quest objectives | Narrator needs these to push story |
| `scene_pressure` (active) | Binding constraint on narration |
| NPC compendium data | Not injected into prompts — only `present_npcs` is |
| `inventory` (active items) | Mechanically required each turn |

---

## Compaction Architecture

### New file: `ccya/engine/compactor.py`

```python
async def maybe_compact(
    save_dir: Path,
    state: dict,
    config: EngineConfig,
    llm: LLMClient,
) -> dict:
    """Run compaction pass if turn count is a multiple of config.compact_every.
    Returns (possibly mutated) state. Writes chronicle.md side-effects.
    """
```

The function:
1. Checks `state.meta.turn % config.compact_every == 0`
2. Calls `_compact_chronicle(...)` — LLM call to summarize aged turns
3. Calls `_prune_recent_events(...)` — mechanical keyword purge, no LLM
4. Writes updated state + chronicle back to disk
5. Returns updated state for use in the current turn's context build

### Call site
`run_turn()` in `engine/turn.py`, after state load and before context build:
```python
state = await maybe_compact(save_dir, state, config, llm)
```

### Config additions (`config.yaml`)
```yaml
game:
  compact_every: 4          # run compactor every N turns (0 = disabled)
  compact_max_event_age: 5  # prune recent_events older than N turns
```

### New prompt: `prompts/compact_system.j2`
System prompt for the chronicle summarization LLM call. See checkpoint 2 below.

---

## Execution Checkpoints

The plan is split into discrete checkpoints. Each checkpoint is self-contained
and leaves the codebase in a working state. A small model should implement one
checkpoint at a time.

---

### CHECKPOINT A — Quest filter (Jinja only, no logic change)

**Files to change:**
- `ccya/prompts/sections/_quests.j2`
- `ccya/prompts/extract_progress_user.j2`

**What to do:**
1. In `_quests.j2`, wrap the quest loop: only render quests where `q.status == 'active'`.
   Add a fallback: if no active quests, emit `(no active quests)`.
2. In `extract_progress_user.j2`, find where current quests are listed and apply
   the same active-only filter so the extractor isn't comparing against dead quests.

**Test:** Start a game, complete a quest via debug or direct state edit,
confirm it disappears from the narrate prompt but remains in `state.yaml`.

**No state changes. No new functions. Purely template edits.**

---

### CHECKPOINT B — Location description discipline (prompt only)

**Files to change:**
- `ccya/prompts/extract_scene_system.j2`

**What to do:**
Find the `location` field description in the output schema section and add the
constraint:
> Only emit `description` if the narration describes a meaningful environmental
> or atmospheric change — a shift in lighting, weather, crowd density, physical
> damage, or tone. Do not re-describe unchanged surroundings. If the space
> looks and feels the same as before, omit `description` entirely.

**Test:** Run 3 turns in the same location with no dramatic events. Inspect
`events.jsonl` — the `scene.location.description` field should be absent or
unchanged on turns 2 and 3.

**No code changes. One prompt file only.**

---

### CHECKPOINT C — NPC bio suppression for `recently_left`

**Files to change:**
- `ccya/engine.py` (or `engine/narrate.py` after refactor) — the function that
  builds `present_npcs` and `recently_left` context dicts
- `ccya/prompts/narrate_user.j2` — already renders `recently_left` separately;
  confirm it only emits `name` + `title` for that block (not bio/notes)

**What to do:**
1. Find where `recently_left` is hydrated from compendium data before being passed
   to the Jinja context.
2. For `recently_left` entries, strip all fields except `name` and `title`.
   Bio and notes are not relevant for characters who just exited.
3. For `present_npcs` (in_scene = true), continue passing full bio + notes as-is.

**Test:** Have an NPC leave the scene. Confirm `recently_left` in the rendered
narrate prompt shows only name/title, not bio. Have the NPC re-enter; confirm
bio reappears.

**One logic file + minor template audit. No state changes.**

---

### CHECKPOINT D — `recent_events` pruner (mechanical, no LLM)

**Files to change:**
- New function in `ccya/state.py` (or `state/chronicle.py` after refactor)
- `ccya/engine.py` (or `engine/turn.py`) — call site
- `config.yaml` — new `compact_max_event_age` key

**What to do:**
1. Implement `prune_recent_events(events, current_turn, state, max_age) -> list[str]`:
   - For each event, extract the turn number from the event text or metadata
   - If `current_turn - event_turn > max_age`, check relevance:
     - Does the event text contain any name from `state.scene.compendium.npcs`
       (check aliases too)?
     - Does it contain any word from active quest ids/descriptions?
     - Does it contain any word from active `scene_pressure` texts?
   - If none match: remove. If any match: keep.
   - Always keep the most recent `max_age` events regardless of relevance.
2. Call `prune_recent_events` in `run_turn()` after state load, before context build.
   Write the pruned list back to state before saving (state mutation).
3. Add `compact_max_event_age: 5` to `config.yaml` under `game:`.

**Test:** Manually add 12 events to `state.yaml`, advance 6 turns, confirm stale
non-relevant events are removed and quest/NPC-relevant ones are preserved.

**One new function + one call site + config. No LLM calls.**

---

### CHECKPOINT E — Chronicle summarizer (LLM call, new prompt)

**Files to change:**
- New file: `ccya/prompts/compact_system.j2`
- New file: `ccya/prompts/compact_user.j2`
- New file: `ccya/engine/compactor.py` (or add to `engine.py` pre-refactor)
- `ccya/engine.py` / `engine/turn.py` — call site
- `config.yaml` — new `compact_every` key

**What to do:**
1. Write `compact_system.j2`:
   - Role: you are a game historian compressing an TTRPG session log
   - Task: take a list of full-turn narratives and produce one bullet per turn
   - Instruction: preserve named NPCs (first mention + role), location, quest
     outcomes, item gains/losses, condition changes, irreversible player choices.
     Cull: atmospheric flavor, repeated setting descriptions, dialogue that
     doesn't introduce someone or resolve something, combat blow-by-blow.
   - Format: `- [T{n}] {1-2 line summary}`
   - Hard rule: do not invent, infer, or embellish. Only compress what is given.

2. Write `compact_user.j2`:
   - Renders the list of full narratives to be compacted (turns older than window)
   - Includes active quest ids, active NPC names, active pressures as relevance
     anchors so the LLM knows what to protect

3. Implement `compact_chronicle(turns, state, config, llm) -> str`:
   - Builds messages from the two new prompts
   - Makes a single non-streaming LLM call (low temp, e.g. 0.1)
   - Returns the bullet-list string
   - Appends it to `chronicle.md` **before** the verbatim turns it replaces
   - Does NOT delete the verbatim turns from chronicle — they stay as archive.
     The token-budget loader (`load_chronicle_tail`) will naturally prefer
     recent content, so the verbatim old content falls off the budget cap.
     (Optional future step: truncate chronicle.md to last M characters to
     prevent unbounded file growth — out of scope for this checkpoint.)

4. Implement `maybe_compact(save_dir, state, config, llm) -> dict`:
   - Check `state.meta.turn % config.compact_every == 0` (skip turn 0)
   - Identify turns older than `window_turns` that haven't been compacted yet
     (track in `state.meta.last_compacted_turn: int`)
   - Call `compact_chronicle` on those turns
   - Call `prune_recent_events` (from checkpoint D) as part of the same pass
   - Update `state.meta.last_compacted_turn`
   - Return updated state

5. Call `maybe_compact` in `run_turn()` after state load, before context build.

6. Add to `config.yaml`:
   ```yaml
   game:
     compact_every: 4
   ```

7. Add to `EngineConfig`:
   ```python
   compact_every: int = 0       # 0 = disabled
   compact_temperature: float = 0.1
   ```

**Test:** Play 8 turns. At turn 4 and 8, confirm:
- `chronicle.md` contains bullet summaries for turns outside `window_turns`
- The narrate prompt's `## Prior History` section is shorter than without compaction
- Full verbatim prose still exists below the bullets in `chronicle.md`
- `state.meta.last_compacted_turn` is updated

**This is the highest-risk checkpoint. Test thoroughly before merging.**

---

### CHECKPOINT F — chronicle.md size management (optional, post-E)

**Files to change:**
- `ccya/state.py` / `state/chronicle.py`

**What to do:**
After compaction runs, trim `chronicle.md` so the verbatim archive doesn't grow
unboundedly. Keep:
- All bullet-summary lines (compact format)
- Last `window_turns` verbatim turn blocks
- Everything else: truncate from the top

This is cosmetic — the token-budget loader already caps what gets injected into
prompts. But it prevents chronicle.md from becoming a 500KB file after a very
long campaign.

**Implement only after checkpoint E is stable.**

---

## Summary Table

| Checkpoint | Files Changed | LLM Call? | State Mutation? | Risk |
|---|---|---|---|---|
| A | 2 Jinja templates | No | No | Very low |
| B | 1 prompt file | No | No | Very low |
| C | 1 logic file + template audit | No | No | Low |
| D | 1 new function + 1 call site | No | Yes (events list) | Low |
| E | 2 prompts + 1 new module + call site | Yes | Yes (chronicle) | Medium |
| F | 1 state file | No | Yes (chronicle trim) | Low |
