# UI: Thread progress strings, debug metadata display, thread ordering, TV delta expansion

## Purpose

Add inline thread progress strings after turn completion, conditional debug-mode metadata (momentum/narrative_velocity/gm_beat/outcome_hint) during streaming, reverse thread ordering in the sidebar, and expand TV delta with pacing fields.

## Problem Statement

After each turn completes, users see narrative text but no explicit display of which threads were advanced or what progress was made on them — only change-lines in a separate panel. Additionally, there's no way to inspect pacing metadata (momentum, narrative velocity, GM beat, outcome hint) during streaming except via the Turn Viewer post-hoc. Active/completed thread lists are ordered oldest-first, making it hard to see recent activity at a glance.

## Constraints

- Use existing `game.debug.enabled` config key from config.yaml — do not add duplicate debug flags.
- Tests temporarily removed; skip test changes.
- No commented-out code, no dead code.
- Debug metadata only displayed when `debug.enabled: true`.
- Thread progress strings appear inline below narrative text (not in streaming phase labels).

## Non-goals

- Do not add a UI toggle for debug mode — purely config-driven.
- Do not change streaming phase label behavior during extraction phases.
- Do not modify the Turn Viewer's existing data structure beyond adding fields.
- Do not reorder threads client-side; do it in Jinja templates only.

## Solution

1. Wire `game.debug.enabled` into EngineConfig so turn_complete payload can carry it to UI.
2. Add streaming metadata (narrative_velocity, gm_beat dict with type+surface_as, outcome_hint) to TurnResult and the turn_complete SSE event.
3. In index.html's turn_complete handler: render thread progress strings as emoji-prefixed lines below narrative text; conditionally render debug metadata row when debug_mode is true.
4. Reverse active threads and completed_threads lists in `_state_left.html` via Jinja `|reverse`.
5. Add narrative_velocity, gm_beat, outcome_hint to TV delta rows in tv.py's `_turn_viewer_data()`.

## Firm decisions

1. Use existing config key: `game.debug.enabled` (currently set to `true`).
2. Thread progress strings displayed as emoji-prefixed lines: `🧵 [KIND] text`, matching existing change-line style.
3. Debug metadata printed inline with other results/deltas — no collapsible panel, just a formatted row.
4. gm_beat displayed as "type (surface_as)" format.
5. Narrative velocity included in TV delta alongside momentum_before/after/outcome_hint.

## Risks, Ambiguities, and Blockers

- [AMBIGUOUS] Thread progress strings: should we show ALL thread changes from `changes["threads"]`, or only the "progress" sub-field updates? Plan assumes all thread change lines that mention progress (🧵 prefix with advancement/setback/shift text). NOTE: Current `summarize_changes()` in changes.py only records "progress added"/"progress updated" as detail strings — it does NOT include actual progress text. Phase 2 must add new progress text to the summary data, or read from state.
- The turn_complete handler already inserts roll badges, outcome summaries, and `_buildTurnChanges()` — need to ensure new elements integrate cleanly without layout breakage.

## Status

`completed`

## Phases

5 phases: config wiring → streaming metadata in pipeline/UI → thread progress display → sidebar ordering → TV delta expansion.

---

# Implementation — Phase 1: Wire debug.enabled into EngineConfig and turn_complete payload

### Context files to load
- `ccya/engine/config.py` (EngineConfig dataclass, `_build_engine_config()` function)
- `ccya/models.py` (TurnResult class definition)
- `ccya/server/routes.py` (`get_turn`, turn_complete event construction at lines 201-223)

### Detailed steps

#### Step 1.1 — Add debug_mode field to EngineConfig

**File:** `ccya/engine/config.py`

**What:** Add `debug_mode: bool = False` to the EngineConfig dataclass (around line ~165, after thread_urgency_max_age). Read it in `_build_engine_config()` from `game.get("debug", {}).get("enabled", False)`.

**Why:** The existing config.yaml already has `game.debug.enabled: true`, but this value is never read into EngineConfig. UI needs access to this flag via the turn_complete payload.

**Validation:**
```bash
source .venv/bin/activate && python -c "from ccya.engine.config import build_engine_config, _load_config; c = build_engine_config(_load_config('config.yaml')); print(c.debug_mode)"
# Expected: True (since config.yaml has debug.enabled: true)
```

#### Step 1.2 — Add streaming metadata fields to TurnResult

**File:** `ccya/models.py`

**What:** Add three new optional fields to the TurnResult dataclass (after line ~528, before ts):
- `narrative_velocity: float | None = None`
- `gm_beat: dict[str, str] | None = None` — stores `{type, surface_as}` from storyteller_result.gm_beat
- `outcome_hint: str | None = None`

**Why:** These fields carry streaming metadata that the UI needs to display during/after turn completion. gm_beat is a dict (not GMBeat model) because it's serialized for JSON transport and may be null.

**Validation:** No command needed — verify by reading the dataclass definition after edit.

#### Step 1.3 — Populate streaming metadata in run_turn() TurnResult construction

**File:** `ccya/engine/turn.py` (around line ~1454, where result_obj = TurnResult(...) is constructed)

**What:** Add to the TurnResult constructor call:
- `narrative_velocity=narrative_velocity` — use the local variable computed at line 854 (always available)
- `gm_beat={"type": storyteller_result.gm_beat.type, "surface_as": storyteller_result.gm_beat.surface_as} if (storyteller_result and storyteller_result.gm_beat) else None` — note: variable is `storyteller_result`, not "storytell_result". Guard with null check since extraction pipeline may fail.
- `outcome_hint=_pc.outcome_hint if _pc else None` — use the local PacingContext variable (always available)

**Why:** These values are already computed during turn execution but not passed to TurnResult. The UI needs them for display.

**Validation:** Read back lines ~1454-1470 to verify all three fields present in constructor call.

#### Step 1.4 — Include streaming metadata and debug_mode in turn_complete SSE event payload

**File:** `ccya/server/routes.py` (lines 203-222, the JSON dict inside the "complete" yield)

**What:** Add to the turn_complete payload dict:
- `"debug_mode": _app_mod.engine_config.debug_mode`
- `"narrative_velocity": result.narrative_velocity`
- `"gm_beat": result.gm_beat`
- `"outcome_hint": result.outcome_hint`

**Why:** The UI's `turn_complete` event handler (index.html line ~1696) parses this JSON. These fields must be present for streaming metadata display and debug-mode conditional rendering.

**Validation:** Read lines 203-225 to verify all four new keys in the payload dict.

---

# Implementation — Phase 2: Display thread progress strings inline after narrative text

### Context files to load
- `ccya/templates/index.html` (turn_complete handler at ~line 1696, `_buildTurnChanges()` function)
- `ccya/engine/changes.py` (`format_change_lines`, how 🧵 lines are constructed from thread changes)

### Detailed steps

#### Step 2.0 — Add actual new progress strings to thread change summaries (prerequisite for 2.1)

**File:** `ccya/engine/changes.py` (`summarize_changes()` function, lines ~285-299 where "progress added" is recorded)

**What:** In the thread update block (~line 285), when progress changes are detected (new entries in post_progress vs pre_progress), capture the actual new progress text. Store it as a `new_progress` field on the threads entry:
```python
new_entries = post_progress[len(pre_progress):] if len(post_progress) > len(pre_progress) else []
if new_entries:
    progress_texts = [f"[{p.get('kind', 'advancement').upper()}] {p.text or p}" if isinstance(p, dict) else str(p) for p in new_entries]
    threads[-1]["new_progress"] = "; ".join(progress_texts)
```

**Why:** Current `summarize_changes()` only records "progress added" as a detail string — it does NOT include the actual progress text (e.g., "[ADVANCEMENT] Rescuing the prisoner"). The UI needs this data to display inline.

**Validation:** After a test turn, verify that thread change entries in `changes["threads"]` contain `"new_progress"` field with formatted progress strings when progress was added/updated.

#### Step 2.1 — Build inline progress strings in turn_complete handler

**File:** `ccya/templates/index.html` (inside the `turn_complete` event listener, after `_buildTurnChanges()` call at ~line 1733-1734)

**What:** After inserting change-lines via `_buildTurnChanges()`, build and insert thread progress lines. Extract from `result.changes["threads"]` — for each entry with a `"new_progress"` field (added in Step 2.0), create an inline div with class `thread-progress-line`, emoji prefix 🧵, and text like `[ADVANCEMENT] Rescuing the prisoner`. Only show entries that have new progress strings (not all thread changes).

**Why:** Users need to see which threads were advanced during this turn, displayed inline below narrative text (same visual treatment as change-lines but thread-specific). Step 2.0 ensures actual progress text is available in the data.

**Validation:** Visually verify after a test turn that progress lines appear between roll badge/outcome and action pills.

---

# Implementation — Phase 3: Debug-mode metadata display in streaming UI

### Context files to load
- `ccya/templates/index.html` (turn_complete handler, `_buildRollBadge`, `_formatMetricsRow`)

### Detailed steps

#### Step 3.1 — Render debug metadata row when debug_mode is enabled

**File:** `ccya/templates/index.html` (inside the turn_complete event listener)

**What:** After inserting change-lines (after step 2.1), check if `result.debug_mode` is true. If so, insert a formatted metadata div with:
- Momentum: value from ruling.momentum_delta or state.pc.momentum
- Narrative velocity: result.narrative_velocity (formatted to 2 decimal places)
- GM beat: "type (surface_as)" format from result.gm_beat, or "—" if null
- Outcome hint: result.outcome_hint

Style with appropriate color matching existing delta/result styling in the UI.

**Why:** When debug mode is enabled, users want to see pacing metadata inline during streaming — same treatment as roll badges and outcome summaries.

**Validation:** With `debug.enabled: true` in config.yaml, verify metadata row appears after turn completion. Toggle to false and verify it disappears.

---

# Implementation — Phase 4: Reverse thread ordering in sidebar template

### Context files to load
- `ccya/templates/_state_left.html` (active threads loop at ~line 78, completed_threads at ~line 115)

### Detailed steps

#### Step 4.1 — Reverse active threads list

**File:** `ccya/templates/_state_left.html` (line ~74)

**What:** Change the Jinja expression from:
```jinja
{% set _active = (_arc.get('threads') | selectattr('active', 'equalto', true) | list) if _arc.get('threads') else [] %}
```
to:
```jinja
{% set _active = (_arc.get('threads') | selectattr('active', 'equalto', true) | list | reverse) if _arc.get('threads') else [] %}
```

**Why:** Users want to see the most recently active threads at the top of the sidebar.

#### Step 4.2 — Reverse completed_threads list

**File:** `ccya/templates/_state_left.html` (line ~75)

**What:** Change from:
```jinja
{% set _completed = (_arc.get('completed_threads', [])[:20]) if _arc else [] %}
```
to:
```jinja
{% set _completed = (_arc.get('completed_threads', [])[:20] | reverse) if _arc else [] %}
```

**Why:** Same reasoning — newest completed threads should appear first.

**Validation:** After a few turns, verify active/completed thread lists show most recent entries at the top in the sidebar panel.

---

# Implementation — Phase 5: Expand TV delta with pacing metadata fields

### Context files to load
- `ccya/server/tv.py` (`_turn_viewer_data()` function, lines ~566-612 where pacing_context and momentum are extracted)

### Detailed steps

#### Step 5.1 — Write narrative_velocity to events.jsonl event dict (prerequisite for TV delta)

**File:** `ccya/engine/turn.py` (around line ~1394-1400, where pacing_context is written to event dict)

**What:** Add `"narrative_velocity": round(narrative_velocity, 2)` to the event dict that gets appended to events.jsonl.

**Why:** TV delta reads from events.jsonl via `_turn_viewer_data()`. Narrative velocity must be persisted there for post-hoc inspection.

**Validation:** Check that `events.jsonl` entries contain `"narrative_velocity": <float>` after a turn completes.

#### Step 5.2 — Add narrative_velocity, gm_beat to TV delta row data

**File:** `ccya/server/tv.py` (in `_turn_viewer_data()`, after the existing pacing_ctx extraction at ~line 567-570)

**What:** After extracting `pacing_context` and momentum values from event data:
1. Read `narrative_velocity` from events.jsonl via `ev.get("narrative_velocity")`. Written there in Step 5.1 above.
2. Read gm_beat type/surface_as from the storytell extraction output: `_get_nested(ev, "extraction.storytell").get("output")` → parse JSON blob → look for `gm_beat.type` and `gm_beat.surface_as`. Use `_tv_parse_json_blob()` to safely extract.
3. outcome_hint is already available via `pacing_ctx.get("outcome_hint")` (already in TV delta at line ~598-602).

Add to the row dict (around line ~604-612):
```python
"narrative_velocity": ev.get("narrative_velocity"),
"gm_beat_type": gm_beat_dict.get("type") if gm_beat_dict else None,
"gm_beat_surface_as": gm_beat_dict.get("surface_as") if gm_beat_dict else None,
```

**Why:** TV delta should show all pacing metadata for debugging. Narrative velocity is computed in turn.py and persisted to events.jsonl (Step 5.1). gm_beat data comes from storytell extraction output (extraction_event["storytell"]["output"] contains `storytell_result.model_dump()` which includes gm_beat as `{type, surface_as}`).

**Validation:** After a test turn, verify TV panel shows narrative_velocity and gm_beat fields in the ruling/pacing section of the delta row.

---

### Tests to write or update

Tests are temporarily removed during refactor — skip test changes per AGENTS.md.

## Documentation updates required (mandatory)

- `docs/repomap.md`: Update TurnResult section with new fields (`narrative_velocity`, `gm_beat`, `outcome_hint`). Update TV delta row data structure to include new pacing metadata keys.
- `docs/architecture/OVERVIEW.md` or relevant step subdoc: Note that narrative_velocity is now persisted in events.jsonl event dict (for TV delta consumption).
