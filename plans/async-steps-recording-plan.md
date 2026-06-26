# Plan — Async Steps (World + Sanitizer) Full Event/Prompt Recording

**Design Reference:** [roadmap/features/async-steps-recording.md](../roadmap/features/async-steps-recording.md)

**Slug:** async-steps-recording

**Plan status:** ready

## Deviation from Design

The design doc says world should be a separate event with `type: "world"` in events.jsonl. I'm embedding world data in the main turn event under `extraction.world` instead.

**Reason:** This matches the existing pattern for scene/state/record extraction steps (all under `extraction.*`), keeps the turn viewer pipeline unified (single row per turn with world as a stage alongside ruling/narrate/scene/state/record), and avoids creating a new event type that would complicate `find_turn`, `filter_turn_events`, and checker logic. The design also says "World needs a regular step with output/prompts same as the other all-turns steps" — embedding in the main event is the cleanest way to achieve that.

Sanitizer recording already exists (separate event with `kind: "sanitizer"`). No changes needed there.

## Phase Summary

One phase covering all changes: modify `_run_world_step` to return prompts/raw response, capture world data in `turn.py` async window and write to events/prompts, add world as a pipeline stage in `tv_mirror.py` and `tv.py`, update the turn viewer template to include world in the stages array. All changes are tightly coupled — they touch the same data shape (`extraction.world`), same files (turn.py, world.py, tv_mirror.py, tv.py, _turn_viewer.html), and same context block (event structure).

## Tasks

### 01. Modify `_run_world_step` to return prompts and raw response

**File:** `ccya/engine/world.py`

**What:** Change `_run_world_step` return type from `list[dict]` to `tuple[list[dict[str, Any]], str, str, str]` — `(beat_candidates, system_text, user_text, raw_response)`. The caller already has `env` and can render templates itself, but we need the rendered text and raw LLM response for event recording.

**Why:** The design requires capturing `world_system.j2` and `world_user.j2` rendered templates, plus the raw LLM response. Currently `_run_world_step` renders templates internally and discards the rendered text after the LLM call.

**Validation:** `_run_world_step` returns a 4-tuple. Existing callers (only `turn.py:522`) will need unpacking adjustment (covered in next task).

### 02. Restructure `turn.py` to delay event append, then capture world data

**File:** `ccya/engine/turn.py`

**What:** Two changes:

**A. Delay `append_event` and `save_state`** (lines 480-482): Move `append_event(save_dir, event)` and `save_state(save_dir, state)` from after line 482 to after line 529 (end of async window). Also move `event["last_turn_state"] = state` to after the async window so it captures the post-sanitizer/post-world state.

**Why:** The event is currently appended at line 481, BEFORE the async window (lines 505-529). `extraction_event` is still in scope during the async window, so we need the event to be unwritten when we add `extraction_event["world"]`.

**B. In the async window** (lines 518-529), after `_run_world_step` returns:
1. Unpack the new 4-tuple: `beat_candidates, world_system_text, world_user_text, world_raw_response = await _run_world_step(...)`
2. Build a world event dict matching the extraction pattern:
    ```
    extraction_event["world"] = {
        "output": beat_candidates,
        "skipped": False,
        "tokens_in": ...,
        "tokens_out": ...,
        "ms": ...,
    }
    ```
3. Write prompts to `prompts.jsonl` via `append_prompts(save_dir, [...])` with entries containing `stream: "world"`, `rendered_system`, `rendered_user`, `turn`, `trace_id`
4. Include world timing and token counts in the event

**Validation:** After a turn completes, `events.jsonl` contains the main turn event with `extraction.world` key containing output/tokens/ms. `prompts.jsonl` contains a `stream: "world"` entry with rendered templates.

### 03. Add world as a pipeline stage in `tv_mirror.py`

**File:** `ccya/server/tv_mirror.py`

**What:** Add a new `StreamDescriptor` to `_STREAMS`:
```python
StreamDescriptor(
    key="world",
    label="World",
    stage_css="world",
    metrics_path="extraction.world",
    prompt_path="extraction.world",
    output_subkey="output",
    is_text_output=False,
    ms_key="ms",
    inputs=["narrate"],
    skip_token_display=False,
)
```

**Why:** `tv.py` iterates `_STREAMS` to build pipeline stage data. Adding world here automatically wires it into the turn viewer pipeline view with metrics extraction, output display, and connector generation.

**Validation:** `STREAM_BY_KEY["world"]` exists. `_STREAMS` has 6 entries (ruling, narrate, scene, state, record, world).

### 04. Add world stage CSS in `tv.py`, `tokens.css`, and `turn-viewer.css`

**Files:** `ccya/server/tv.py`, `ccya/static/tokens.css`, `ccya/static/turn-viewer.css`

**What:** Three changes:

**A.** Add `"world": "tv-stage-world"` to `_STAGE_CSS` dict in `tv.py` (line ~30).

**B.** Add `--stage-world: #6366f1;` to `tokens.css` (after line 43, `--stage-storytell`).

**C.** Add two CSS rules to `turn-viewer.css`:
- After line 391: `.tv-wf-segment.tv-stage-world { background: var(--stage-world); }`
- After line 860: `.tv-stage-world .tv-stage-accent { background: var(--stage-world); }`

**Why:** `_STAGE_CSS` maps the stage key to CSS class. The CSS variable provides the color. The CSS rules apply the accent color to the stage bar and waterfall segment. Without all three, the world stage will render without proper styling.

**Validation:** `_STAGE_CSS` includes world key. `tokens.css` has `--stage-world`. `turn-viewer.css` has both CSS rules.

### 05. Add "world" to stages array in turn viewer template

**File:** `ccya/templates/_turn_viewer.html`

**What:** Change line 415 from:
```javascript
stages: ['ruling', 'narrate', 'scene', 'state', 'storytell'],
```
to:
```javascript
stages: ['ruling', 'narrate', 'scene', 'state', 'storytell', 'world'],
```

**Why:** The Alpine.js `stages` array drives the pipeline stage rendering loop. Adding "world" makes the template render a world stage alongside the others.

**Validation:** Turn viewer shows world stage in pipeline view for each turn.

### 06. Update `turn_viewer_prompts` route to include world prompts

**File:** `ccya/server/routes.py` (line ~822)

**What:** No changes needed. The existing `turn_viewer_prompts` route reads all prompts with matching `turn` number from `prompts.jsonl`. Since task 02 writes world prompts with `stream: "world"` and the correct `turn`, the route will automatically include them. The template's `loadPrompts` function (line 513-532) caches by turn and keys by `stream`, so world prompts will be served automatically.

**Why:** Confirming no changes needed — the existing infrastructure handles new stream types.

**Validation:** `GET /turn_viewer/prompts?turn=N` returns world prompts alongside other prompts for turn N.

### 07. Update documentation

**Files:**
- `docs/architecture/OVERVIEW.md` — Add world to pipeline quick reference table (it's already there as Step 2d, but add recording details)
- `docs/architecture/step2d-world.md` — Add section on event/prompt recording
- `docs/repomap.md` — Update `ccya/server/tv_mirror.py` entry to mention world stream descriptor
- `AGENTS.md` — No changes needed (no new commands or signposts)

**Why:** Design mandates documentation updates. Any code change touching a module requires corresponding updates to architecture docs and repomap.

**Validation:** Repomap mentions world in tv_mirror.py. Step 2d doc mentions event recording.

## Dependencies

All tasks are in one phase with sequential dependencies:
- 01 → 02 (turn.py unpacking depends on new return type)
- 02 → 03, 04, 05 (event structure must exist before viewer reads it)
- 03 → 04 (CSS class needed for stage)
- 04 → 05 (template stage array)
- 06 is independent (no changes needed)
- 07 is independent (documentation)

## Done When

- [ ] `_run_world_step` returns 4-tuple (beat_candidates, system_text, user_text, raw_response)
- [ ] `turn.py` async window writes `extraction.world` to main turn event
- [ ] `prompts.jsonl` contains world prompts with `stream: "world"`
- [ ] `tv_mirror.py` has world `StreamDescriptor`
- [ ] `tv.py` has world in `_STAGE_CSS`
- [ ] Template `stages` array includes "world"
- [ ] `turn_viewer_prompts` route returns world prompts
- [ ] Documentation updated (repomap, step2d-world.md, OVERVIEW.md)
- [ ] `make check` passes
