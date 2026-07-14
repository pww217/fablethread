---
title: "Stale storytell→record stream name cruft across ev.py, static assets, and CSS"
status: done
urgency: 2
size: medium
created: 2026-07-12
ticket_id: I-40
labels:
  - ev
  - cleanup
  - naming
plan: plans/i-40-storytell-clean-plan.md
---

## Problem

The extraction stream was renamed from `storytell` → `record` via the `beat-generation-split` branch (B-7). The engine and prompts are updated, but several code paths still reference the old stream name. This produces **vacuous output** (reading from paths that don't exist) in active ev.py commands, not just legacy debug output.

B-7 was marked "done" and lists deltas.py as fixed in "Fix results" §4, but only the `compact_delta()` path was fixed. The `cmd_mechanics()` function in full delta mode still reads from the wrong extraction path.

## Broken code paths (ev.py commands produce vacuous output)

### `ccya/ev/deltas.py` — `cmd_mechanics()` (full mode, lines 221-276)

All the "mechanics" sub-sections (GM Beat, Rules Outcome, Pacing Context, Active Threads) read from a variable named `storytell_event` which is obtained from `extract_prompt(ev, "storytell")`. This extraction path no longer exists in current events (it's `record` now).

Lines affected:
- **226**: `extract_prompt(ev, "storytell")["user"]` → `extract_prompt(ev, "record")["user"]`
- **235**: `extract_prompt(ev, "storytell")["output"]` → `extract_prompt(ev, "record")["output"]`
- Variable `storytell_event` → `record_event`
- Variable `storytell_output_raw` → `record_output_raw`
- **250, 259**: `extract_section_by_pattern(storytell_event, ...)` → `extract_section_by_pattern(record_event, ...)`
- **263**: Print header `(from storytell)` → `(from record)`
- **264**: `extract_section_by_pattern(storytell_event, ...)` → `extract_section_by_pattern(record_event, ...)`
- **37**: `_extract_connectors()` stream_inputs `"storytell": ...` → `"record": ...`

### `ccya/ev/events.py` — `_build_state_diff_changes()` (line 240)

The state diff lookup reads `("storytell", "extraction.storytell")`. For new events, the extraction path is `extraction.record`, so this line produces no diff entries.

- **240**: `"storytell", "extraction.storytell"` → `"record", "extraction.record"`

### `ccya/static/game-utils.js` — turn metrics display (line 165)

`streams.storytell` key doesn't exist in the current stream model (STREAMS tuple has `record`). The record metrics bar in the turn progress display won't show for new events.

- **165**: `streams.storytell` → `streams.record`

### `ccya/ev/prompt_eval.py` — crash on `--stream storytell` without `--from-events` (lines 82, 435)

`_get_template_name("storytell")` falls through to `extract_storytell_user.j2` (line 46) which doesn't exist. `_get_system_template_name("storytell")` returns `extract_storytell_system.j2` which also doesn't exist. This means `ev.py prompt-eval dump <dir> --turn N --stream storytell` (in non-`--from-events` mode) crashes with file-not-found.

- **82**: `"storytell"` in default streams list should be `"record"`
- **435**: Help text lists `"storytell"` as valid stream name — should say `"record"`

### `ccya/ev/prompt_context.py` — stale branch and stale comments (lines 92, 130, 153-218)

- **Line 92**: Comment `post-storytell state (close to pre-storytell)` — stale, says `post-record state`.
- **Line 130**: Comment `like _storytell_messages does` — function `_storytell_messages` no longer exists.
- **Lines 153-211**: The `if stream == "storytell":` branch is legacy code. It's not truly dead (reachable when `stream: storytell` is passed in a YAML/CLI), but it serves as the old extraction context format. The `record` branch at line 127 is the streamlined canonical version for the current `record` extraction. If this branch were truly needed, it would live as `if stream in ("record", "storytell"):` — but since the `record` branch is the current canonical path (streamlined for the new extraction prompt), the `storytell` branch should be removed. Users should use `stream: record` instead.
- **Lines 158, 153-218**: Comments reference `_storytell_messages` which no longer exists and `storytell` naming throughout.

## Misleading strings (low priority but should be corrected)

- **`ccya/models/extraction.py:273`**: `RecordResult._warn_empty_actions()` error/message says `storytell.actions is empty`. Model class is `RecordResult` — should say `record.actions`.

- **`ccya/ev/state_tools.py:330`**: Comment `from storytell extraction` — stale.

- **`ccya/ev/state_tools.py:391`**: Comment `prefer storytell gm_beat` — stale.

- **`ccya/engine/_pacing.py:261`**: Comment `not in-flight storyteller_result` — `StorytellerResult` class was removed when stream was renamed. Should say `record_result`.

- **`ccya/engine/hints.py:4`**: Comment `narrator and storyteller paths` — `storyteller` is now `record` (prompts are `record_system.j2` / `record_user.j2`, no `*storyteller*` prompts exist). Should say `narrator and record`.

- **`ccya/prompts/sanitize_thread.j2:51`**: Word "storyteller" in prose — acceptable (describes the LLM's narrative role, not the stream name).

## CSS naming (cosmetic)

Current CSS uses `--stage-storytell` (#ec4899 pink) as the color variable even for the record stream. Renaming to `--stage-record` would remove the mismatch, but the current variable works. Files:

- `ccya/static/tokens.css:43` — `--stage-storytell`
- `ccya/static/app-shell.css:412-414` — references `var(--stage-storytell)` for `.extraction-bar--record` (record bar uses storytell CSS var)
- `ccya/static/app.src.css:43,3165,3634` — definition and CSS rules
- `ccya/static/turn-viewer.css:391,870` — `.tv-stage-storytell`
- `ccya/server/tv.py:30` — `"record": "tv-stage-storytell"` mapping

## Backward-compat aliases (keep as-is)

- **`ccya/ev/__init__.py:25`**: `"storytell": "record"` alias — intentionally kept for backward compat with old saved prompts and events.
- **`ccya/ev/__init__.py:274`**: `storyteller-audit` CLI command name — rename in UI/help is optional.
- **`ccya/ev/__init__.py:22`**: `"rules": "ruling"` alias — similarly kept.
- **`ccya/ev/__init__.py:24`**: `"progress": "record"` alias — similarly kept.

## Test references (tests are suspended; revisit when tests return)

- `tests/test_alignment.py:248-250` — references `storytell_user.j2` (no longer exists)
- `tests/test_render.py:123-177` — references `storytell_user.j2`
- `tests/test_schema.py:374` — `test_storyteller_boundary_model_dump` (class removed)

## Related

- Parent: [B-7](../bugs/B-7-ev-side-cleanup-rename-storytell-stream-to-record.md) — the cleanup ticket that was marked done prematurely
- Original split: [beat-generation-split-design](../../docs/design/beat-generation-split-design.md)
