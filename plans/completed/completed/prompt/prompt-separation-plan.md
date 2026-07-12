# Prompt Separation Plan

## Purpose

Split rendered prompt strings out of `events.jsonl` into a separate `prompts.jsonl` file, reducing event file size by ~75% (~2.5 MB → ~800 KB for a 30-turn session).

## Problem Statement

Rendered prompt strings (`rendered_system`, `rendered_user`) account for ~75% of `events.jsonl` file size. EV tooling, checkers, and the Turn Viewer must load the entire file even when only game state is needed. Additionally, narrate prompts are stored twice: once in `extraction_event.narrate` and once in `narrate_prompt`, doubling the bloat for narrate prompts.

## Constraints

- No backward compatibility or migrations — old files will show blank prompt tabs
- Deterministic checkers (`pacing_directives`, `gm_beat_lifecycle`) must re-render prompts via Jinja2 instead of reading from events
- `prompts.jsonl` written alongside `events.jsonl` in the same `append_event` call
- Turn Viewer loads prompts on-demand via separate endpoint (not merged into `/turn_viewer/data`)
- No new external dependencies

## Non-goals

- Does not change prompt templates or rendering pipeline
- Does not change `state.yaml`, `chronicle.md`, or event schema (except removing prompt fields)
- Does not change LLM checkers or checker framework
- Does not change `ev.py play` or `ev.py eval run` behavior
- Does not change how prompts are constructed or rendered — only where rendered output is stored

## Solution

Strip `rendered_system` and `rendered_user` from all prompt blobs in `events.jsonl`, write them to a new `prompts.jsonl` file with one entry per LLM call per turn. Update all readers (checkers, EV tooling, Turn Viewer) to either re-render prompts via Jinja2 or load from `prompts.jsonl`. Expected outcome: `events.jsonl` drops to ~25% of original size; prompts remain accessible on demand.

## Firm decisions

1. `prompts.jsonl` written in the same `append_event` call (not post-hoc) — atomic per turn
2. Turn Viewer uses a new endpoint `GET /turn_viewer/prompts?turn=N` for on-demand loading
3. `prompts.jsonl` schema: `{ts, trace_id, turn, stream, rendered_system, rendered_user, context_meta}`
4. Deterministic checkers re-render prompts via Jinja2 using `_build_jinja_env`/`_render` from `engine/config.py`
5. No backward compat — old files will show blank prompts; documented as breaking change
6. Narrate prompts stored once (not twice) — strip from `extraction_event.narrate`, keep only in `narrate_prompt`

## Risks, Ambiguities, and Blockers

- **Checker re-rendering context fidelity:** If Jinja2 context reconstruction in checkers is not perfectly faithful to the original prompt, false positives may occur. Mitigation: use the same context construction as `build_prompt_context()` in `prompt_eval.py`, which already works correctly.
- **Old game saves:** After the change, old `events.jsonl` files will show blank prompt tabs in Turn Viewer. Mitigation: documented as breaking change; old files can still be inspected via `prompt-eval` re-rendering.
- **File sync:** If engine crashes between writing `events.jsonl` and `prompts.jsonl`, the prompt file could be missing entries for the last turn. Mitigation: write `events.jsonl` first, then `prompts.jsonl`.

## Status

`open`

## Phases

4 phases: strip prompts from events.jsonl, refactor checkers to re-render, update EV tooling to read from prompts.jsonl, add Turn Viewer on-demand endpoint.

---

## Implementation — Phase 1: Engine Writes

### Context files to load

- `ccya/state/chronicle.py` — `append_event()` function
- `ccya/engine/turn.py` — lines 215-222 (extraction_event narrate), lines 409-421 (ruling_prompt, narrate_prompt)
- `ccya/engine/extraction/pipeline.py` — lines 87-98 (scene), lines 132-143 (state), lines 257-268 (storytell)
- `ccya/engine/config.py` — `_context_meta()` function (already exists)

### Detailed steps

#### Step 1.1 — Add `prompts.jsonl` write helper to `chronicle.py`

**File:** `ccya/state/chronicle.py`

**What:** Add `append_prompts(save_dir: Path, prompts: list[dict[str, Any]]) -> None` function. Writes each prompt entry as a JSON line to `prompts.jsonl` in the save directory. Creates directory if needed. Logs errors.

**Why:** Centralized prompt writing function, mirrors `append_event()` pattern.

**Validation:** Function exists with correct signature. No runtime test needed (will be tested via integration).

#### Step 1.2 — Strip prompts from `extraction_event.narrate` in `turn.py`

**File:** `ccya/engine/turn.py`, lines 215-222

**What:** Remove `"rendered_system"` and `"rendered_user"` keys from the `extraction_event["narrate"]` dict. Keep only `"output"`, `"tokens_in"`, `"tokens_out"`, `"ms"`.

**Why:** Eliminates duplicate narrate prompt storage (already stored in `narrate_prompt`).

**Validation:** `grep "rendered_system" ccya/engine/turn.py` returns no matches in extraction_event block.

#### Step 1.3 — Strip prompts from `ruling_prompt` and `narrate_prompt` in `turn.py`

**File:** `ccya/engine/turn.py`, lines 409-421

**What:** Remove `"rendered_system"` and `"rendered_user"` keys from both `ruling_prompt` and `narrate_prompt` dicts. Keep `"output"`, `"parse_error"` (for ruling), and `"context_meta"`.

**Why:** Prompts move to `prompts.jsonl`; events.jsonl no longer stores rendered prompt strings.

**Validation:** `grep "rendered_system" ccya/engine/turn.py` returns no matches.

#### Step 1.4 — Strip prompts from extraction streams in `pipeline.py`

**File:** `ccya/engine/extraction/pipeline.py`

**What:** Remove `"rendered_system"` and `"rendered_user"` keys from:
- `extraction_event["scene"]` (lines 87-98)
- `extraction_event["state"]` (lines 132-143)
- `extraction_event["storytell"]` (lines 257-268)

Keep `"output"`, `"skipped"`, `"attempts"`, `"retry_errors"`, `"tokens_in"`, `"tokens_out"`, `"ms"`, `"context_meta"`.

**Why:** Prompts move to `prompts.jsonl`; events.jsonl no longer stores rendered prompt strings.

**Validation:** `grep "rendered_system" ccya/engine/extraction/pipeline.py` returns no matches.

#### Step 1.5 — Collect prompts and write to `prompts.jsonl` in `turn.py`

**File:** `ccya/engine/turn.py`, around line 427 (after event dict is built, before `append_event`)

**What:** Before calling `append_event(save_dir, event)`:
1. Build a list of prompt entries from the stripped prompt data:
   ```python
   prompts_list = [
       {
           "ts": ...,           # timestamp from event or time.time()
           "trace_id": trace_id,
           "turn": turn_no,
           "stream": "ruling",
           "rendered_system": rendered_ruling_system,
           "rendered_user": rendered_ruling_user,
           "context_meta": {...},
       },
       {
           "ts": ...,
           "trace_id": trace_id,
           "turn": turn_no,
           "stream": "narrate",
           "rendered_system": rendered_narr_system,
           "rendered_user": rendered_narr_user,
           "context_meta": {...},
       },
       # ... scene, state, storytell from extraction_event context_meta
   ]
   ```
2. Call `append_event(save_dir, event)` first (events.jsonl)
3. Call `append_prompts(save_dir, prompts_list)` second (prompts.jsonl)

**Why:** Writes both files per turn. Events first, prompts second (crash safety: events always written even if prompts fails).

**Validation:** `ls saves/<dir>/prompts.jsonl` exists after a run. File has 5 lines per turn.

### Tests to write or update

None (tests temporarily removed during refactor).

---

## Implementation — Phase 2: Checker Refactors

### Context files to load

- `ccya/ev/checkers/pacing.py` — `pacing_directives` function
- `ccya/ev/checkers/gm_beat.py` — `gm_beat_lifecycle` function
- `ccya/engine/config.py` — `_build_jinja_env()`, `_render()` functions
- `ccya/ev/prompt_eval.py` — `build_prompt_context()` function (for context reconstruction)

### Detailed steps

#### Step 2.1 — Refactor `pacing_directives` to re-render prompts

**File:** `ccya/ev/checkers/pacing.py`

**What:** Replace all reads of `rendered_user` from event blobs with on-the-fly Jinja2 re-rendering:
1. Import `_build_jinja_env` and `_render` from `ccya.engine.config`
2. Import `build_prompt_context` from `ccya.ev.prompt_eval`
3. For each turn event, call `build_prompt_context(events, turn, stream)` to get context dict
4. Call `_render(env, template_name, ctx)` to get rendered prompt
5. Check for directive/outcome_hint in re-rendered output

**Why:** Checkers verify template renders correctly, not that stored prompts contain expected text. Re-rendering is the actual intent of the check.

**Validation:** `ev.py check <save-dir> pacing_directives` passes/fails on known test data.

#### Step 2.2 — Refactor `gm_beat_lifecycle` to re-render prompts

**File:** `ccya/ev/checkers/gm_beat.py`

**What:** Replace the read of `narrate_prompt.rendered_user` (line 64) with Jinja2 re-rendering:
1. Import `_build_jinja_env` and `_render` from `ccya.engine.config`
2. Import `build_prompt_context` from `ccya.ev.prompt_eval`
3. For turns where `ruling.rolled` is true, re-render narrate user prompt
4. Check for `"rules_outcome (BINDING"` in re-rendered output

**Why:** Same as pacing_directives — verifies template includes BINDING block when rolled.

**Validation:** `ev.py check <save-dir> gm_beat_lifecycle` passes/fails on known test data.

### Tests to write or update

None (tests temporarily removed during refactor).

---

## Implementation — Phase 3: EV Tooling

### Context files to load

- `ccya/ev/events.py` — `load_events()`, `extract_field()` functions
- `ccya/ev/inspect.py` — `extract_prompt()`, `cmd_turn()`, `cmd_prompt()` functions
- `ccya/ev/prompt_eval.py` — `_extract_prompt_from_event()`, `cmd_prompt_eval_dump()`, `cmd_prompt_eval_call()` functions

### Detailed steps

#### Step 3.1 — Add `load_prompts()` to `events.py`

**File:** `ccya/ev/events.py`

**What:** Add `load_prompts(save_dir: Path) -> list[dict[str, Any]]` function. Loads `prompts.jsonl` from save directory, returns list of prompt entries. Mirrors `load_events()` pattern.

**Why:** EV tooling needs a way to load prompts from the new file.

**Validation:** Function exists with correct signature. Returns empty list if file doesn't exist.

#### Step 3.2 — Update `extract_prompt()` in `inspect.py`

**File:** `ccya/ev/inspect.py`

**What:** Modify `extract_prompt(ev, stream)` to accept an optional `prompts: list[dict] | None` parameter. When provided, load `rendered_system`/`rendered_user` from the matching prompt entry in `prompts` list (filtered by `turn` and `stream`). When not provided, fall back to reading from event blob (for backward compat with old files or callers that don't have prompts).

**Why:** `ev prompt` command needs to load prompts from `prompts.jsonl`. Fallback ensures old files still work (showing empty prompts).

**Validation:** `ev.py prompt <save-dir> --turn N --stream STREAM` displays prompts when `prompts.jsonl` exists.

#### Step 3.3 — Update `_extract_prompt_from_event()` in `prompt_eval.py`

**File:** `ccya/ev/prompt_eval.py`

**What:** Replace `_extract_prompt_from_event()` to load from `prompts.jsonl` when `--from-events` flag is set:
1. Accept `save_dir: Path` parameter (in addition to event and stream)
2. Load prompts via `load_prompts(save_dir)`
3. Filter by `turn` and `stream` to find matching entry
4. Return `{system, user, output}` dict from prompt entry

**Why:** `prompt-eval --from-events` should read from `prompts.jsonl` (new data source), not `events.jsonl`.

**Validation:** `ev.py prompt-eval dump <save-dir> --turn N --stream STREAM --from-events` displays prompts from `prompts.jsonl`.

### Tests to write or update

None (tests temporarily removed during refactor).

---

## Implementation — Phase 4: Turn Viewer On-Demand Endpoint

### Context files to load

- `ccya/server/tv.py` — `_turn_viewer_data()` function, lines 499-528 (prompts dict construction)
- `ccya/server/routes.py` — turn viewer routes
- `ccya/server/tv_mirror.py` — `_STREAMS`, `_get_nested()` (read-only, no changes)

### Detailed steps

#### Step 4.1 — Strip prompts from `_turn_viewer_data()` in `tv.py`

**File:** `ccya/server/tv.py`, lines 499-528

**What:** Remove the prompts dict construction loop (lines 499-528). The `prompts` key will no longer be included in turn row dicts. The frontend will load prompts on demand via the new endpoint.

**Why:** Turn Viewer no longer loads prompts with turn data. Prompts loaded separately when user opens prompt tab.

**Validation:** `/turn_viewer/data` endpoint no longer includes `prompts` in turn objects.

#### Step 4.2 — Add `GET /turn_viewer/prompts?turn=N` endpoint in `routes.py`

**File:** `ccya/server/routes.py`

**What:** Add new route handler:
```python
@app.get("/turn_viewer/prompts")
def turn_viewer_prompts(turn: int):
    """Load prompts for a specific turn from prompts.jsonl."""
    if err := _require_save():
        return err
    prompts_path = _app_mod.SAVE_DIR / "prompts.jsonl"
    if not prompts_path.exists():
        return JSONResponse({"prompts": []}, status_code=200)
    # Load prompts.jsonl, filter by turn, return list of prompt entries
    ...
```

Each prompt entry: `{stream, rendered_system, rendered_user, context_meta}`.

**Why:** Turn Viewer frontend fetches prompts on demand when user opens a prompt tab. Separate endpoint keeps `/turn_viewer/data` lightweight.

**Validation:** `curl "http://localhost:8765/turn_viewer/prompts?turn=1"` returns prompt entries for turn 1.

#### Step 4.3 — Update TV frontend for on-demand prompt loading

**File:** `ccya/templates/_turn_viewer.html`

**What:** Modify the Alpine.js component to fetch prompts on demand:
1. Add a `stagePrompts` reactive map to store fetched prompts per turn/stage
2. When user clicks the "Prompt" tab (line 175), check if `stagePrompts[turn-stage]` exists; if not, fetch from `/turn_viewer/prompts?turn=N`
3. Store fetched prompts in `stagePrompts` map
4. Update template bindings to read from `stagePrompts[turn-stage]` when available, falling back to `t.prompts[stage]` for old files

Specific changes:
- Add `stagePrompts: {}` to the reactive data
- Add `async loadStagePrompts(turn, stage)` method that fetches `/turn_viewer/prompts?turn=${turn}` and stores result
- Modify the tab click handler to call `loadStagePrompts` if prompts not yet loaded
- Update template bindings: `x-show="stagePrompts[turn+'-'+stage] || t.prompts[stage]"`
- Update all `t.prompts[stage]` references to check `stagePrompts[turn+'-'+stage]` first

**Why:** Frontend needs to load prompts from the new endpoint when user clicks a prompt tab. Keeps `/turn_viewer/data` lightweight.

**Validation:** Prompt tabs load correctly when clicked. Old files still work (show "No prompt data available").

### Tests to write or update

None (tests temporarily removed during refactor).

---

## Documentation Updates

After all phases complete, update:

1. **`docs/architecture/`** — Update pipeline data shapes to reflect stripped prompt fields in events.jsonl and new prompts.jsonl schema
2. **`docs/repomap.md`** — Add `append_prompts()` to chronicle.py, update event schema descriptions, add `/turn_viewer/prompts` endpoint
3. **`docs/ev/CHECKERS.md`** — Note that `pacing_directives` and `gm_beat_lifecycle` now re-render prompts
4. **`docs/ev/COMMANDS.md`** — Update `prompt-eval --from-events` to read from `prompts.jsonl`
5. **`docs/design/eval-system-design.md`** — Note that prompts are no longer embedded in events.jsonl (affects file size calculations)
