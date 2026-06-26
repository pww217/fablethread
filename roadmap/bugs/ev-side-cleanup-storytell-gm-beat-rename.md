---
title: "EV-side cleanup: rename storytell stream to record + migrate gm_beat readers"
status: validated
urgency: 3
size: medium
created: 2026-06-26
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

## Current state

94 references to `storytell` and `gm_beat` across `ccya/ev/`. Sample breakage:

- `ccya/ev/__init__.py:24-25` — `STAGE_PROGRESS` and `STAGE_LABELS` map `"storytell"` → `"storytell"`, used by `ev.py` progress display
- `ccya/ev/events.py:12` — `STREAMS = ("ruling", "narrate", "scene", "state", "storytell")` — missing `record`
- `ccya/ev/events.py:239` — extraction prompt lookup `("storytell", "extraction.storytell")` — key changed
- `ccya/ev/deltas.py:37, 168-191, 228-241` — `compact_delta()` reads `extraction.storytell` for thread/inventory/condition/gm_beat display; `gm_beat` field no longer exists in record output
- `ccya/ev/deltas.py:228` — `extract_prompt(ev, "storytell")` — stream key changed
- `ccya/ev/checkers/gm_beat.py` — reads `gm_beat` from extraction event JSON, but `gm_beat` is no longer a field anywhere in the extraction pipeline. This checker now produces no signal.
- `ccya/ev/checkers/beat_phase_validity.py` — likely depends on `gm_beat` from extraction too
- `ccya/ev/checkers/pacing.py:53, 76` — `_render(env, "storytell_user.j2", ctx)` — template deleted
- `ccya/ev/checkers/llm_checkers.py` — list imports for `extraction_retry_rates`, `thread_resolution_validity`, `goal_update_validity`, `threads`, `new_thread_validity`, `arc_goals`, `arc_resolution_validity` — internal stream references
- `ccya/ev/prompt_context.py:117` — `if stream == "storytell":` — stream key changed
- `ccya/ev/prompt_eval.py:38, 50, 75` — stream → template mapping
- `ccya/ev/prompt_sizes.py:51` — `for stage in ("scene", "state", "storytell"):`
- `ccya/ev/warnings.py:19` — `for stream in ("scene", "state", "storytell"):`
- `ccya/ev/state_tools.py:346, 479, 860` — `extraction.get("storytell")` and `gm_beat` reads
- `ccya/ev/audit.py:300` — `storyteller` audit looks at the (now-renamed) record stream
- `ccya/ev/eval.py` — extraction stream references in eval scenario YAML loading

**Files to touch (23):**
- `ccya/ev/__init__.py`
- `ccya/ev/events.py`
- `ccya/ev/deltas.py`
- `ccya/ev/audit.py`
- `ccya/ev/check.py`
- `ccya/ev/state_tools.py`
- `ccya/ev/warnings.py`
- `ccya/ev/prompt_sizes.py`
- `ccya/ev/__init__.py` (stage maps)
- `ccya/ev/prompt_context.py`
- `ccya/ev/prompt_eval.py`
- `ccya/ev/eval.py`
- `ccya/ev/checkers/__init__.py`
- `ccya/ev/checkers/extraction_retry_rates.py`
- `ccya/ev/checkers/thread_resolution_validity.py`
- `ccya/ev/checkers/goal_update_validity.py`
- `ccya/ev/checkers/threads.py`
- `ccya/ev/checkers/new_thread_validity.py`
- `ccya/ev/checkers/arc_goals.py`
- `ccya/ev/checkers/llm_checkers.py`
- `ccya/ev/checkers/beat_phase_validity.py`
- `ccya/ev/checkers/pacing.py`
- `ccya/ev/checkers/arc_resolution_validity.py`
- `ccya/ev/checkers/gm_beat.py`

## Proposed change

Three coordinated passes:

### Pass 1 — Stream key rename (`storytell` → `record`)

Mechanical find/replace of `"storytell"` string literal in EV code paths. Applies to:
- `STREAMS` tuple
- Stage maps (`STAGE_PROGRESS`, `STAGE_LABELS`)
- `extraction.storytell` paths → `extraction.record`
- Template name `storytell_user.j2` → `record_user.j2` (the corresponding system template is also `record_system.j2`; `prompt_eval.py` handles both)
- CLI command `storyteller-audit` and `cmd_storyteller_audit` — keep the CLI name (already a user-facing command) but update its internal stream reference to `record`
- `deltas.py:compact_delta()` — `extraction.get("storytell")` → `extraction.get("record")`

### Pass 2 — gm_beat field readers

Two options depending on the reader's purpose:

(a) **Display-only readers** (compact_delta, audit storyteller) — drop the gm_beat row entirely from the display. Beats are no longer in extraction output. Show a note: "Beats flow through Ruling → state.meta.pending_gm_beat; see `ev.py beats` for the new audit view."

(b) **Validation checkers** (`ccya/ev/checkers/gm_beat.py`, possibly `beat_phase_validity.py`) — rewrite to read beats from `state.meta.pending_gm_beat` (post-apply state) and `state.meta.beat_candidates` (next-turn candidates) instead of extraction output. The new `ev.py beats` command (or extended `audit.py`) should be the source of truth.

This is the most consequential pass — the checker output semantics change. Two sub-options:
- (b1) Rewrite the checker in place to read from the new state fields
- (b2) Replace the checker with a new one (`selected_beat_validity.py`) that operates on the new lifecycle

Recommend (b2) — a fresh checker is clearer than threading state-field access into a checker designed for extraction output.

### Pass 3 — Audit command update

`ccya/ev/audit.py:cmd_storyteller_audit` — rename to `cmd_record_audit` (or keep the user-facing name `storyteller-audit` and just update its internals). Internal: read from `extraction.record` for thread/arc display, source `pending_gm_beat` and `beat_candidates` from `state.meta` for the beat sections.

## Files to touch

See list above (23 files in `ccya/ev/`).

## Validation

- `make check` passes
- `ev.py prompt-eval dump <save-dir> --turn N --stream record` renders without error
- `ev.py summary` reports correct per-stream timing including `record` (not `storytell`)
- `ev.py deltas` shows thread/arc/condition deltas from `record` stream output
- `ev.py beats` (or equivalent new audit) reads `state.meta.pending_gm_beat` correctly
- `ev.py storyteller-audit` (CLI name kept) shows no broken extraction paths
- A 25-turn eval run produces non-vacuous output for all stream checkers

## Related

- Design doc: [`docs/design/beat-generation-split-design.md`](../../docs/design/beat-generation-split-design.md)
- Plan: [`plans/completed/gm-beats/beat-generation-split-plan.md`](../../plans/completed/gm-beats/beat-generation-split-plan.md) — "Phase 6 / OQ9" defers this work
- Execution commit: `dfdabe7` on `beat-generation-split` branch
