# Plan: I-40 — Stale storytell→record stream name cruft cleanup

## Design Reference

- Ticket: `roadmap/improvements/I-40-stale-storytell-stream-name-cruft.md`
- Parent bug: `roadmap/bugs/B-7` — original stream rename (done, but `deltas.py` fix was incomplete)

## Problem Statement

The extraction stream was renamed from `storytell` → `record` via B-7, but several code paths still reference the old stream name. This produces **vacuous output** (reading from extraction paths that no longer exist) in active ev.py commands, crashes in `prompt-eval dump --stream storytell` mode, and leaves stale naming across comments, error messages, and CSS class names.

## Firm decisions (from design)

1. **Rename `storytell` → `record`** everywhere in engine/tooling code (not optional per-phase).
2. **Keep backward-compat aliases** in `ccya/ev/__init__.py` `STREAM_ALIASES` for old saved events/prompts.
3. **Remove the dead `if stream == "storytell":` branch** in `prompt_context.py` — the `record` branch is the canonical version.
4. **Keep `storyteller-audit` CLI command name** (rename optional, not in scope).
5. **Keep `"storyteller"` in prose** in `sanitize_thread.j2:51` (describes LLM narrative role, not stream).
6. **Defer frozen eval scenarios** (YAML files using `stream: storytell` — no active evals).
7. **Defer suspended tests** (tests referencing `storytell_user.j2`).
8. **CSS renaming** (`--stage-storytell`, `.tv-stage-storytell`) are cosmetic — in scope but lowest priority. Keep working.

## Scope

- **Phase 01:** ev.py engine (deltas.py + events.py) — critical vacuous output fixes
- **Phase 02:** Static assets (game-utils.js) — turn metrics display fix
- **Phase 03:** ev.py tooling (prompt_eval.py + prompt_context.py) — crash + dead code fixes
- **Phase 04:** Strings/comments + CSS cleanup (extraction.py, state_tools.py, _pacing.py, hints.py, 5 CSS files) — cosmetic only

## Status

`completed`

---

## Phase 01: ev.py engine fixes (critical)

### Depends on

None

### Context files to load

- `ccya/ev/deltas.py:33-38` — `_extract_connectors()` stream_inputs dict
- `ccya/ev/deltas.py:221-276` — `cmd_mechanics()` full delta mode output
- `ccya/ev/events.py:224-276` — `_build_state_diff()` state diff lookup

### What changes

Rename `storytell` to `record` in two engine files that govern ev.py command output and state diffs.

### Where to change

**`ccya/ev/deltas.py`**

- `:37` — `_extract_connectors()` stream_inputs dict: `"storytell": ["ruling", "narrate", "scene", "state"]` → `"record": ["ruling", "narrate", "scene", "state"]`
- `:226` — `extract_prompt(ev, "storytell")["user"]` → `extract_prompt(ev, "record")["user"]`
- `:235` — `extract_prompt(ev, "storytell")["output"]` → `extract_prompt(ev, "record")["output"]`
- `:226` — rename variable `storytell_event` → `record_event`
- `:235` — rename variable `storytell_output_raw` → `record_output_raw`
- `:250` — `extract_section_by_pattern(storytell_event, ...)` → `extract_section_by_pattern(record_event, ...)`
- `:259` — `extract_section_by_pattern(storytell_event, ...)` → `extract_section_by_pattern(record_event, ...)`
- `:263` — Print header `--- Active Threads (from storytell) ---` → `--- Active Threads (from record) ---`
- `:264` — `extract_section_by_pattern(storytell_event, ...)` → `extract_section_by_pattern(record_event, ...)`

**`ccya/ev/events.py`**

- `:240` — tuple in `_build_state_diff()`: `("storytell", "extraction.storytell")` → `("record", "extraction.record")`. This affects the `_add_event` list entries that process event JSON.

### Why

Both files still reference `"storytell"` instead of `"record"` when reading extraction data from turn events. Since events now store extraction under the `"record"` key, all reads return `(none)`/empty values. This makes the `ev mechanics` command (full mode) and state diff commands silently produce empty output for new events.

### Validation

- Run `ev.py mechanics --save-dir <dir> --turn N` on a recent save (post-B-7) — should show GM Beat, Rules Outcome, Pacing Context, Active Threads populated instead of `(none)`/`(empty)`.
- Run `ev.py diff --save-dir <dir> --turn N` — should show state diff entries for the record extraction domain.
- `make check` passes.

---

## Phase 02: Static assets (turn metrics display)

### Depends on

None

### Context files to load

- `ccya/static/game-utils.js:145-172` — `_formatMetricsRow()` function rendering turn progress bars

### What changes

Rename `streams.storytell` → `streams.record` in the record metrics bar.

### Where to change

**`ccya/static/game-utils.js`**

- `:165` — `const pg = streams.storytell;` → `const pg = streams.record;`
  - The label `'Rec '` on line 166 is already correct.

### Why

The `streams` object keys match the `STREAMS` tuple (`("ruling", "narrate", "scene", "state", "record", "world")`). There is no `"storytell"` key — this null-reference means the record step's metrics bar never renders in `game-utils.js`, so the UI shows missing progress data for the extraction step.

### Validation

- Open the frontend in a browser and watch a new turn complete — the record step metrics bar (`Rec`) should appear alongside Rul, Nar, Scn, Ste.
- `make check` passes.

---

## Phase 03: ev.py tooling (prompt-eval + prompt-context)

### Depends on

Phase 01 (optional — they're independent but useful together for CLI verification)

### Context files to load

- `ccya/ev/prompt_eval.py:78-87` — `cmd_prompt_eval_dump()` stream list and iteration
- `ccya/ev/prompt_eval.py:430-439` — help text for `prompt-eval dump` command
- `ccya/ev/prompt_context.py:89-93, 127-218` — `build_prompt_context()` record and storytell branches

### What changes

Fix the `"storytell"` → `"record"` references in prompt_eval and remove the stale `storytell` branch from prompt_context.

### Where to change

**`ccya/ev/prompt_eval.py`**

- `:82` — `"storytell"` in the `all_streams` list: `["ruling", "narrate", "scene", "state", "storytell"]` → `["ruling", "narrate", "scene", "state", "record"]`. This ensures `--all` iterates over `record` instead of a non-existent template file.
- `:435` — help text: `--stream STREAM   Stream name: ruling, narrate, scene, state, storytell` → `--stream STREAM   Stream name: ruling, narrate, scene, state, record`. This is visible in `ev.py --help`.

**`ccya/ev/prompt_context.py`**

- `:92` — docstring comment: `post-storytell state` → `post-record state`, `pre-storytell` → `pre-record`
- `:130` — comment: `like _storytell_messages does` → `like record context building does` (or similar wording)
- `:153-218` — **Delete the entire `if stream == "storytell":` branch**. The `record` branch at `:127` is the canonical version for the current extraction prompt. Users should use `stream: record` (alias `storytell: record` back-compat is already in `__init__.py`).

### Why

`prompt_eval.py:82` excludes `"record"` from the `all_streams` list while including `"storytell"`, which crashes in non-`--from-events` mode (template `extract_storytell_user.j2` doesn't exist). The help text at `:435` mirrors this error by listing `storytell` as valid. The `storytell` branch in `prompt_context.py` is legacy code — when `STREAM_ALIASES` aliases `storytell→record` is applied in `__init__.py`. This makes this branch unreachable/functionally unreachable, even though `key in `ev/__init__.py` maps it to record. In other words, `build_prompt_context` if reachability depends on bypassing the alias layer entirely.

### Validation

- `ev.py prompt-eval dump <dir> --turn N --stream record --from-events` works without error.
- `ev.py prompt-eval dump <dir> --turn N --all` includes `record` in output.
- `ev.py --help prompt-eval dump` lists `record` as valid stream.
- `make check` passes.

---

## Phase 04: Strings, comments, and CSS cleanup (cosmetic)

### Depends on

Phase 03 (optional — no functional dependency, bundle just for convenience).

### Context files to load

- `ccya/models/extraction.py:273`
- `ccya/ev/state_tools.py:330,391`
- `ccya/engine/_pacing.py:261`
- `ccya/engine/hints.py:4`
- `ccya/static/tokens.css:43`
- `ccya/static/app-shell.css:412-414`
- `ccya/static/app.src.css:43,3165,3634`
- `ccya/static/turn-viewer.css:391,870`
- `ccya/server/tv.py:30`

### What changes

Update stale strings, comments, and CSS class names.

### Where to change

**`ccya/models/extraction.py`**

- `:273` — `"storytell.actions is empty"` → `"record.actions is empty"`

**`ccya/ev/state_tools.py`**

- `:330` — `"from storytell extraction"` → `"from record extraction"`
- `:391` — `"prefer storytell gm_beat"` → `"prefer record gm_beat"`

**`ccya/engine/_pacing.py`**

- `:261` — `"not in-flight storyteller_result"` → `"not in-flight record result"`

**`ccya/engine/hints.py`**

- `:4` — `"narrator and storyteller paths"` → `"narrator and record paths"`

**CSS files (cosmetic)**

- `ccya/static/tokens.css:43` — `--stage-storytell` → `--stage-record`
- `ccya/static/app-shell.css:412-414` — `var(--stage-storytell)` → `var(--stage-record)`
- `ccya/static/app.src.css:43` — `--stage-storytell` → `--stage-record`
- `ccya/static/app.src.css:3165` — `.tv-stage-storytell` → `.tv-stage-record`
- `ccya/static/app.src.css:3634` — `.tv-stage-storytell` → `.tv-stage-record`
- `ccya/static/turn-viewer.css:391` — `.tv-stage-storytell` → `.tv-stage-record`
- `ccya/static/turn-viewer.css:870` — `.tv-stage-storytell` → `.tv-stage-record`
- `ccya/server/tv.py:30` — `"record": "tv-stage-storytell"` → `"record": "tv-stage-record"`

### Why

These are all stale naming from the original `storytell` → `record` rename. They don't affect runtime behavior but cause confusion for developers and don't update helpers, which makes the stale naming the naming inconsistent. Updated to match the current `record` convention for clarity. The CSS rename (`--stage-storytell` → `--stage-record`, `.tv-stage-storytell` → `.tv-stage-record`) may cascade updates via CSS minification (app.src.css → app.css) — the minified `app.css` file should also be updated, or it will be regenerated when the source is re-compiled.

### Validation

- `make check` passes (CSS changes won't affect lint/typecheck).
- UI renders extraction bars and turn viewer stages with correct styling.
- No runtime errors with `ev.py` commands on sample data.
- If `app.css` (minified) was not manually updated, run `make css` to regenerate it from `app.src.css`.

---

## Documentation updates

- `docs/architecture/step2c-record.md` — 6 stale `storyteller_result` references need `record_result` (lines 109, 209, 230, 241, 251) + `_storytell_messages` → `_record_context` (line 267).
- `docs/architecture/pacing-systems.md` — `extraction.storytell.gm_beat` → `extraction.record.gm_beat` (line 431).
- `docs/repomap.md` — no stream renaming needed across 2 entries (line 55 `storyteller` is agent name, line 133 `storyteller proposes` is agent role). No changes required.
- `AGENTS.md` — no changes needed (no `storytell` references).
