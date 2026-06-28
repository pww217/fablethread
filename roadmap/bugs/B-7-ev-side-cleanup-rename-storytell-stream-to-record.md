---
title: "EV-side cleanup: rename storytell stream to record + migrate gm_beat readers"
status: done
urgency: 3
size: medium
created: 2026-06-26
ticket_id: B-7
labels:
  - ev
  - extraction
  - gm-beats
  - refactor
---

## Review findings (2026-06-26)

Review of the `beat-generation-split` branch surfaced additional in-scope changes that the original execution missed. These are tracked separately as part of the same review pass:

- `ccya/server/tv.py` — `_EXTRACTION_STREAMS` and `_STAGE_CSS` were using `"storytell"` key (no `"record"` entry). Result: turn viewer's diff panel silently dropped the record-stage entries. **Fixed in review.**
- `ccya/server/tv_mirror.py` — `StreamDescriptor(key="storytell", ...)` references the old stream name. **Fixed in review.**
- `ccya/server/metrics.py` — Metrics formatter iterated `("scene", "state", "storytell")` and read `raw_streams["storytell"]` to populate `So_tt`/`So_tok` (storytell time/tokens) cells. **Fixed in review** (renamed to `Re_tt`/`Re_tok`).
- `ccya/templates/_debug.html` — Template references `t.streams.So_tt` / `So_tok`. **Fixed in review.**

The other 13 doc files referenced in this ticket (state-models, prompts-architecture, persist, prompt-variable-contracts, step0/1, step2a, step2c-record body, cross-pipeline, cross-module-contracts, delta-validate, out-of-band, turn-viewer-ui, pacing-systems, markers.py) are tracked here as a follow-up sweep if they weren't already updated in the same review pass.

## Problem

The beat generation split ([design doc](../../docs/design/beat-generation-split-design.md), executed in `beat-generation-split` branch) renamed the extraction stream from `storytell` to `record` and removed the `gm_beat` field from `StorytellerResult` / `TurnResult`. Beat flow moved: World step writes `state.meta.beat_candidates`, Ruling selects `selected_beat`, `state.meta.pending_gm_beat` is set/popped per turn.

The live turn pipeline is updated. The EV tooling (`ccya/ev/`) still references `storytell` and `gm_beat` in 23 files. The result: most EV commands produce vacuous output (looking for a key that no longer exists), some are silently wrong, and any new eval run will mix pre/post-split data without the user knowing.

## Actual event schema (verified 2026-06-27)

Events contain **both** `extraction.record` and `extraction.world`:

- `extraction.record.output` — structured extraction: `actions`, `outcome_summary`, `thread_resolve`, `thread_update` (replaces old storytell's structured output)
- `extraction.world.output` — list of `{type, effect}` beat objects (replaces old storytell's `gm_beat`)

Old `extraction.storytell` had: `gm_beat`, `thread_add`, `thread_resolve`, `thread_update`, `goal_update`, `actions`, etc.

New pipeline split:
- `record` = structured extraction (threads, goals, actions)
- `world` = beat generation (list of {type, effect})

## Current state (tested against saves/the-outer-rim--after-unification-2026-06-27)

### Crashes
1. **`ev.py convergence`** — `KeyError: 'dice'` at `state_tools.py:692`. Row dict has key `"roll"` but format function references `"dice"`.

### Silent failures / vacuous output
2. **`ev.py storyteller-audit`** — reads `extraction.storytell` (now `extraction.world`/`record`). Reports "No storyteller format violations found" vacuously.
3. **`ev.py beats`** — reads `extraction.storytell.output.gm_beat`. All beat types show empty. Only shows `recent_beats` from `last_turn_state.meta`.
4. **`ev.py deltas`** — GM Beat display reads `extraction.storytell`. No GM Beat shown.
5. **`ev.py goals`** — fallback reads `extraction.storytell`. Reports "(no goal changes found)".
6. **`ev.py trace`** — thread_resolve from `extraction.storytell`. Shows "(same)" or "(no data)" for thread fields.
7. **`ev.py trace pc.location`** — reports "Field not tracked per-turn" (search doesn't support `pacing_context` dot-paths).
8. **`ev.py search scene_phase:CLIMAX`** — returns "(no matches)" (search doesn't support `pacing_context` fields).
9. **`ev.py trace`** — doesn't filter compaction events. Shows duplicate turn 5 entries (turn event + sanitizer event).

### Silent logic errors
10. **`beat_phase_validity` checker** — reads `ruling.get("selected_beat")` which is now an int index (0-based), not a dict with `.type`. Checker silently passes because `isinstance(gm_beat, dict)` is False.
11. **`pacing_directives` checker** — reads `storytell_user.j2` template which no longer exists. Checker passes vacuously.

### Missing features
12. **`ev.py thread-audit`** — listed in help text but no command case implemented. Returns "Unknown command: thread-audit".

### Minor issues
13. **`ev.py eval list`** — error on `thread-fix-v1.yaml`: "missing required field 'pack'".
14. **`ev.py effective-age`** — "(no effective_scene_age data found)" — field not in record output.
15. **`ev.py beat-ttl`** — "(no beat TTL data found)" — TTL field not in expected location.

## Files to touch (23)

- `ccya/ev/__init__.py` — STREAMS tuple, stage maps, stream aliases
- `ccya/ev/events.py` — STREAMS tuple, extraction path references
- `ccya/ev/deltas.py` — extraction.storytell → extraction.record/world
- `ccya/ev/audit.py` — storyteller audit reads record stream
- `ccya/ev/state_tools.py` — extraction.storytell → record/world, convergence KeyError, thread_resolve, goals fallback, trace compaction filtering
- `ccya/ev/warnings.py` — stream iteration
- `ccya/ev/prompt_sizes.py` — stream iteration
- `ccya/ev/prompt_context.py` — stream key check
- `ccya/ev/prompt_eval.py` — stream → template mapping
- `ccya/ev/checkers/beat_phase_validity.py` — reads int index, not dict
- `ccya/ev/checkers/pacing.py` — references deleted storytell_user.j2 template
- `ccya/ev/checkers/extraction_retry_rates.py` — extraction.storytell → record
- `ccya/ev/checkers/thread_resolution_validity.py` — extraction.storytell → record
- `ccya/ev/checkers/goal_update_validity.py` — extraction.storytell → record
- `ccya/ev/checkers/threads.py` — extraction.storytell → record
- `ccya/ev/checkers/new_thread_validity.py` — extraction.storytell → record
- `ccya/ev/checkers/arc_goals.py` — extraction.storytell → record
- `ccya/ev/checkers/arc_resolution_validity.py` — extraction.storytell → record
- `ccya/ev/checkers/gm_beat.py` — reads gm_beat field that no longer exists
- `ccya/ev/checkers/__init__.py` — checker imports (internal stream refs)
- `ccya/ev/eval.py` — scenario loading

## Proposed change

### Pass 1 — Stream key rename (`storytell` → `record`)

Mechanical find/replace of `"storytell"` string literal in EV code paths. Applies to:
- `STREAMS` tuple: add `"record"` (keep `"storytell"` as alias for backward compat)
- Stage maps (`STAGE_PROGRESS`, `STAGE_LABELS`)
- `extraction.storytell` paths → `extraction.record`
- Template name `storytell_user.j2` → `record_user.j2`
- CLI command `storyteller-audit` — keep CLI name but update internal stream reference to `record`
- `deltas.py:compact_delta()` — `extraction.get("storytell")` → `extraction.get("record")`

### Pass 2 — gm_beat field readers

Beats are no longer in extraction output. Two approaches:

(a) **Display-only readers** (compact_delta, audit storyteller) — drop the gm_beat row. Show note: "Beats flow through Ruling → state.meta.pending_gm_beat; see `ev.py beats` for the audit view."

(b) **Validation checkers** (`gm_beat.py`, `beat_phase_validity.py`) — rewrite to read from `state.meta.pending_gm_beat` and `state.meta.beat_candidates`. The `ev.py beats` command should be the source of truth.

### Pass 3 — World stream handling

`extraction.world` contains beat candidates as a list of `{type, effect}`. Commands that need beat type/effect data should read from:
- `state.meta.pending_gm_beat` — the selected beat for this turn
- `state.meta.beat_candidates` — the beat candidates the ruling system chose from
- `extraction.world.output` — the world step's beat suggestions (list of {type, effect})

### Pass 4 — Search and trace improvements

- Add `pacing_context` field support to `_match_single_query` in `state_tools.py`
- Filter compaction events in `cmd_trace` (use `is_compaction_event`)
- Support dot-path traversal on `pacing_context` for trace/search

### Pass 5 — Implement thread-audit

Add `thread-audit` command case in `__init__.py` and implement in `audit.py`. Should track thread lifecycle: created by record's thread_add (or state.arc.threads), updated by record's thread_update, resolved by record's thread_resolve.

## Fix results (2026-06-27)

### Crashes — Fixed
1. **`ev.py convergence`** — `KeyError: 'dice'` → Changed `r['dice']` to `r['roll']` in state_tools.py:692.

### Silent failures — Fixed
2. **`ev.py storyteller-audit`** — Updated to read from `extraction.record` instead of `extraction.storytell`. Now checks thread_update, thread_resolve, and actions fields.
3. **`ev.py beats`** — Updated to read beat type/effect from `state.meta.pending_gm_beat` instead of `extraction.storytell.output.gm_beat`.
4. **`ev.py deltas`** — GM Beat display now reads from `state.meta.pending_gm_beat`.
5. **`ev.py goals`** — Removed extraction fallback (goal_update no longer exists in record output). Sanitizer events are the source of truth.
6. **`ev.py trace`** — Added explicit handling for thread_resolve, thread_update, and actions fields. Filters compaction events by default.
7. **`ev.py search scene_phase:CLIMAX`** — Added explicit handling for scene_phase and pacing_context.* fields in _match_single_query.

### Silent logic errors — Fixed
8. **`beat_phase_validity` checker** — Updated to read selected_beat as int index and look up beat type from state.meta.beat_candidates.

### Missing features — Implemented
9. **`ev.py thread-audit`** — New command that audits thread lifecycle: creation, updates, resolution, and orphan detection.

### Minor issues — Fixed
10. **`ev.py eval list`** — Updated to handle both Scenario and PromptEvalScenario YAML formats.
11. **`ev.py warnings`** — Updated stream iteration from `("scene", "state", "storytell")` to `("scene", "state", "record")`.
12. **`ev.py prompt-sizes`** — Updated stream iteration and display from "storytell" to "record".

### Files modified (10)
- `ccya/ev/__init__.py` — STREAM_ALIASES, thread-audit command routing
- `ccya/ev/audit.py` — storyteller audit rewrite, thread-audit implementation
- `ccya/ev/checkers/beat_phase_validity.py` — int index beat lookup
- `ccya/ev/deltas.py` — GM Beat from state.meta
- `ccya/ev/eval.py` — eval list dual-format support
- `ccya/ev/events.py` — STREAMS tuple, extract_field_from_event thread_resolve/thread_update/actions
- `ccya/ev/prompt_eval.py` — template name mapping record_user.j2/record_system.j2
- `ccya/ev/prompt_sizes.py` — record stream display
- `ccya/ev/state_tools.py` — convergence KeyError, beats from state.meta, trace compaction filtering, search pacing_context
- `ccya/ev/warnings.py` — record stream iteration

## Validation

- `make check` passes
- `ev.py prompt-eval dump <save-dir> --turn N --stream record` renders without error
- `ev.py summary` reports correct per-stream timing including `record` (not `storytell`)
- `ev.py deltas` shows thread/arc/condition deltas from record stream output
- `ev.py beats` reads `state.meta.pending_gm_beat` correctly
- `ev.py storyteller-audit` (CLI name kept) reads from record stream
- `ev.py convergence` runs without crash
- `ev.py check --all` produces non-vacuous output for all checkers
- `ev.py thread-audit` works (new command)
- `ev.py search scene_phase:CLIMAX` returns matching turns
- A 25-turn eval run produces non-vacuous output for all stream checkers

## Related

- Design doc: [`docs/design/beat-generation-split-design.md`](../../docs/design/beat-generation-split-design.md)
- Plan: [`plans/completed/gm-beats/beat-generation-split-plan.md`](../../plans/completed/gm-beats/beat-generation-split-plan.md) — "Phase 6 / OQ9" defers this work
- Execution commit: `dfdabe7` on `beat-generation-split` branch
