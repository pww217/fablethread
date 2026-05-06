# Compactor Plan: Context Token Reduction (Refined)

Goal: periodically compact game state context so prompt size stays bounded over
long playthroughs without losing mechanically or narratively important information.

---

## Key Design Decisions

- **Timing**: Compactor runs at the END of the current turn, after persist
  (append_chronicle + save_state). The compacted state takes effect when the
  NEXT turn loads. On turn 4, compaction runs and compacts turns 1-3. On turn 5,
  the narrate prompt sees 2 recent turns in full prose + compacted bullets as
  prior history.
- **Frequency**: Every `compact_every` turns (default 4).
- **Window**: `window_turns` remains 3 for recent turns loading. After compaction,
  the first of those 3 will be a compacted bullet (from chronicle.md), effectively
  giving 2 full prose turns + compacted prior history.
- **Single LLM call**: One compaction call handles BOTH chronicle summarization
  AND recent_events compaction. The events are included in the same prompt.
- **UI**: Shows a phase moodlet ("Compacting history…") during the turn it runs,
  same pattern as existing phases. No output displayed — result visible when
  next turn begins.
- **No truncation**: We do NOT delete verbatim turns from chronicle.md. The
  token-budget loader (`load_chronicle_tail`) naturally caps what gets injected
  into prompts. Compaction just lowers the token count so we're less likely to
  hit the budget.

## Current state discrepancies (corrected from original plan)

| Item | Plan said | Actual | Decision |
|---|---|---|---|
| Checkpoint A (quest filter) | Needs implementation | **Already done** — `_quests.j2` filters active | Skip |
| Checkpoint C (NPC bio suppression) | Needs implementation | **Already done** — `delta.py` only stores name/title in recently_left | Skip |
| recent_events cap | 15 | **20** | Correct plan to 20 |
| `last_compacted_turn` | Not mentioned | Doesn't exist yet | Add to state.meta |
| Compactor timing | "before context build" | **After persist, end-of-turn** | Runs after save, affects next turn |

---

## Compaction Flow (detailed)

### When it runs
At the end of `run_turn()`, after `append_chronicle()` and `save_state()`.
Triggered when `state.meta.turn % compact_every == 0` and `turn > 0`.

### What it does
1. Reads `chronicle.md` — finds all `## Turn N` headers
2. Identifies turns to compact: from `last_compacted_turn + 1` to
   `current_turn - window_turns` (i.e. turns that are outside the recent window)
3. Extracts full prose for those turns from chronicle.md
4. Gathers recent_events from state (the ones being compacted)
5. Makes ONE LLM call with both the turn narratives AND the events
6. LLM returns: bullet summaries for each turn + compacted events list
7. Writes COMPACTED block to chronicle.md (prepends before the verbatim turns)
8. Updates state: prunes recent_events, updates `last_compacted_turn`
9. Saves state back to disk

### What the next turn sees
- `load_recent_chronicle_turns(save_dir, 3)` — returns last 3 turns from chronicle.
  The most recent 2 are full prose. The 3rd (if compacted) will be a bullet line
  that doesn't match the `## Turn N` header pattern → **problem**.

**Solution**: The compacted bullets get their OWN header format in chronicle.md:
```
## COMPACTED
- [T1] Docked at Ilus Station; met Drummer (dockworker, hostile). Lost access card.
- [T2] Persuaded Naomi to vouch for entry.
- [T3] Found Holden in cargo bay 7. Quest complete.
```
This is a single block, not individual turn headers. `load_recent_chronicle_turns`
will skip it (no `## Turn N` match). The bullets appear in `chronicle_tail`
(which reads everything before the last N turns).

So the narrate prompt on turn 5 will see:
- `## Prior History` — the COMPACTED block with bullets (from chronicle_tail)
- `## Recent Turns` — turns 4 and 5 in full prose (from load_recent_chronicle_turns)

This gives exactly 2 full prose turns + all prior history as bullets.

### Incremental compaction
On subsequent compaction passes (e.g. turn 8), the compactor appends new bullets
to the existing COMPACTED block rather than rebuilding from scratch. This preserves
the accumulated history without re-processing already-compacted turns.

---

## Compaction Targets

### 1. Narrative history (chronicle turns outside window)
**Mode**: State mutation — writes to chronicle.md
**Trigger**: Every `compact_every` turns, end-of-turn

The compactor takes full prose from aged turns and produces bullet summaries.
Each bullet preserves:
- Named NPCs (first mention + role, death/departure)
- Location
- Quest outcomes (resolved, failed, new leads)
- Mechanical consequences (conditions, key items)
- Irreversible player choices

Culls: atmospheric flavor, repeated descriptions, dialogue without consequence,
combat blow-by-blow.

Format:
```
- [T1] Docked at Ilus Station; met Drummer (dockworker, hostile). Lost access card.
- [T2] Persuaded Naomi to vouch for entry. Quest: Find Holden → new lead: cargo bay 7.
```

### 2. Recent events (now 20 cap)
**Mode**: State mutation — same LLM call as chronicle
**Trigger**: Same compaction pass

The events from the compacted turns are included in the LLM prompt. The LLM
produces a compacted events list — only events with mechanical or narrative weight.
The pruned list replaces `state.scene.recent_events`. The most recent 5 events
are always preserved regardless of relevance.

### 3. Location description discipline
**Mode**: Prompt tightening
**Trigger**: Every turn (no compaction pass needed)

Strengthen `extract_scene_system.j2` instruction for `location_description`:
> Only emit if the narration describes a meaningful environmental or atmospheric
> change — a shift in lighting, weather, crowd density, physical damage, or tone.
> Do not re-describe unchanged surroundings. If the scene looks and feels the
> same as before, omit `description` entirely.

---

## Architecture

### New file: `ccya/engine/compactor.py`

```python
async def maybe_compact(
    save_dir: Path,
    state: dict,
    config: EngineConfig,
) -> dict:
    """Run compaction pass if turn count triggers it.
    Mutates chronicle.md and state. Returns updated state.
    """
```

Called from `run_turn()` after persist (append_chronicle + save_state).
Yields a phase event for UI visibility.

### Compaction LLM call
Single non-streaming call (`llm_client.chat`), low temperature (0.1).
System prompt: `compact_system.j2`
User prompt: `compact_user.j2` — renders turn narratives + events + relevance anchors

### State tracking
New field in `state.meta`: `last_compacted_turn` (int, default 0).
Updated after each successful compaction pass.

### Config additions
```yaml
game:
  compact_every: 4          # run compactor every N turns (0 = disabled)
```
```python
compact_every: int = 0       # 0 = disabled
compact_temperature: float = 0.1
```

---

## Execution Checkpoints

### CHECKPOINT 1 — Location description discipline (prompt only) ✅ DONE

**Files to change:**
- `ccya/prompts/extract_scene_system.j2`

**What to do:**
Replace the `location_description` field rule (line 28) with stronger language:
```
`location_description`: Only emit this field if the narration describes a
meaningful environmental or atmospheric change to the current location — a
shift in lighting, weather, crowd density, physical damage, or emotional
register of the space. Do not re-describe unchanged surroundings. If the
scene looks and feels the same as before, omit `description` entirely.
```

**Test:** Run 3 turns in same location with no dramatic events. Check events.jsonl
— `location_description` should be absent on turns 2-3.

**No code changes. One prompt file only. Very low risk.**

---

### CHECKPOINT 2 — Config + meta fields ✅ DONE

**Files to change:**
- `ccya/engine/config.py` — add `compact_every` and `compact_temperature` to EngineConfig
- `config.yaml` — add `compact_every: 4` under `game:`
- `ccya/server/app.py` — wire new config keys into EngineConfig construction
- `ccya/state/io.py` — add `last_compacted_turn: 0` to `_default_state()` meta

**What to do:**
1. Add to EngineConfig:
   ```python
   compact_every: int = 0           # 0 = disabled
   compact_temperature: float = 0.1
   ```
2. Add to config.yaml under `game:`:
   ```yaml
   compact_every: 4
   ```
3. Wire in app.py:
   ```python
   compact_every=config["game"].get("compact_every", 0),
   compact_temperature=config["game"].get("compact_temperature", 0.1),
   ```
4. Add `last_compacted_turn: 0` to the meta dict in `_default_state()`

**Test:** Start a new game — confirm `last_compacted_turn: 0` appears in state.yaml meta.

**No behavior change yet. Very low risk.**

---

### CHECKPOINT 3 — Compactor module + prompts ✅ DONE

**Files to create:**
- `ccya/engine/compactor.py` — `maybe_compact()`, `_compact_chronicle()`, `_build_compact_messages()`, `_parse_compact_response()`, `_extract_turns_for_compact()`, `_write_compacted_block()`
- `ccya/prompts/compact_system.j2` — system prompt
- `ccya/prompts/compact_user.j2` — user prompt template

**Files to change:**
- `ccya/engine/__init__.py` — export `maybe_compact`

**What to do:**

1. **`compact_system.j2`**:
   - Role: game historian compressing a TTRPG session log
   - Task: produce one bullet per turn + compacted events list
   - Preserve: named NPCs (first mention + role), location, quest outcomes,
     item gains/losses, condition changes, irreversible player choices,
     death/departure events
   - Cull: atmospheric flavor, repeated setting descriptions, dialogue without
     consequence, combat blow-by-blow
   - Format: `- [T{n}] {1-2 line summary}` for turns
   - Events: emit as a JSON array of compacted event strings
   - Hard rule: do not invent, infer, or embellish. Only compress what is given.
   - Output format: first the bullets (one per line), then a blank line, then
     a JSON array of compacted event strings

2. **`compact_user.j2`**:
   - Renders the turn narratives to compact (full prose, with turn numbers)
   - Renders the recent_events to compact (with turn numbers)
   - Includes relevance anchors: active quest IDs/descriptions, present NPC names,
     active pressure texts
   - Template receives: `turns` (list of {turn, input, narrative}), `events`
     (list of {turn, text}), `active_quests`, `npc_names`, `pressures`

3. **`_build_compact_messages(env, state, turns, events)`**:
   - Renders system + user prompts
   - Returns messages list for `llm_client.chat()`

4. **`_parse_compact_response(response_text)`**:
   - Parses LLM output: extracts bullet lines and JSON events array
   - Returns `(bullets_text: str, compacted_events: list[str])`
   - Bullet lines: any line matching `- [T\d+]` pattern
   - JSON events: last JSON array in the response

5. **`_extract_turns_for_compact(save_dir, start_turn, end_turn)`**:
   - Reads chronicle.md
   - Extracts full prose for turns in range [start_turn, end_turn]
   - Returns list of {turn, input, narrative} dicts

6. **`_write_compacted_block(save_dir, bullets_text)`**:
   - Prepends a `## COMPACTED` block to chronicle.md
   - If a COMPACTED block already exists, appends new bullets after it
   - Format:
     ```
     ## COMPACTED
     - [T1] ...
     - [T2] ...
     ```

7. **`async def maybe_compact(save_dir, state, config)`**:
   - Check `config.compact_every > 0` and `state.meta.turn % config.compact_every == 0`
   - Skip if `state.meta.turn == 0`
   - Read chronicle.md, find turns from `last_compacted_turn + 1` to
     `turn - window_turns` (these are the turns outside the recent window)
   - If no turns to compact, return state unchanged
   - Extract full prose for each identified turn
   - Gather events from state (all events, we'll let the LLM decide what to keep)
   - Build messages, call `llm_client.chat()`
   - Parse response
   - Write COMPACTED block to chronicle.md
   - Update `state.scene.recent_events` with compacted events
   - Update `state.meta.last_compacted_turn = state.meta.turn`
   - Save state
   - Return state

**Test:** Play 4 turns. After turn 4 completes, check chronicle.md for COMPACTED
block with bullets for turns 1-3. Check state.yaml for updated `last_compacted_turn`.

**Medium risk — first LLM integration. Test thoroughly.**

**Bug fixes applied during implementation:**
- `_parse_compact_response`: regex `[\s\S]*` → `[\s\S]*?` (non-greedy) to avoid
  matching bracket pairs in bullet lines like `- [T1] ...`
- `_write_compacted_block`: on incremental compaction, find end of entire COMPACTED
  block (next `## Turn` header) instead of just the header line, so new bullets
  append after existing ones rather than re-inserting after the header
- `config.yaml`: added `compact_temperature: 0.1` for consistency

---

### CHECKPOINT 4 — Wire into run_turn

**Status: DONE** ✅

**Files changed:**
- `ccya/engine/turn.py` — added `from ccya.engine.compactor import maybe_compact` import
- `ccya/engine/turn.py` — added compactor call after persist in `run_turn()` (line ~469)
- `ccya/engine/turn.py` — added compactor call after persist in `run_turn_retry()` (line ~875)

**Test:** All 249 tests pass.

**Low risk — wiring only, logic tested in checkpoint 3.**

---

### CHECKPOINT 5 — UI phase handling

**Status: DONE** ✅

**Files changed:**
- `ccya/templates/index.html` — added `compact_start`/`compact_done` to `_setProgressFromPhase()` (line ~486)

**Test:** All 249 tests pass.

**Very low risk.**

---

## Summary Table

| Checkpoint | Files Changed | LLM Call? | State Mutation? | Risk |
|---|---|---|---|---|
| 1 | 1 prompt file | No | No | Very low |
| 2 | config.py, config.yaml, app.py, io.py | No | No (new field) | Very low |
| 3 | compactor.py (new), 2 prompts (new), __init__.py | Yes | Yes (chronicle) | Medium |
| 4 | turn.py | No (calls compactor) | Yes (via compactor) | Low |
| 5 | index.html | No | No | Very low |

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
