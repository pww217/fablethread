# Plan: Extraction Subpackage Split

## Purpose

Replace `ccya/engine/extraction.py` (803 lines) with a `ccya/engine/extraction/` subpackage organized by stream (scene/state/storytell) + shared utilities + pipeline orchestrator, preserving the exact same public import surface for `turn.py`.

## Problem Statement

`ccya/engine/extraction.py` bundles 3 independent LLM streams in one file with a shared orchestrator and shared utilities. An agent editing the storytell stream must load scene and state message builders too. The 280-line orchestrator is the only reason the file isn't already split — moving it to its own file (`pipeline.py`) unblocks stream-level granularity.

## Constraints

- `turn.py` imports `_run_extraction_pipeline`, `_avg_event_ms`, `_context_meta` from `ccya.engine.extraction` — this import must continue to resolve identically (subpackage `__init__.py` re-exports).
- No behavioral or import changes outside `ccya/engine/extraction/*` and `ccya/engine/turn.py`.
- No new external dependencies.

## Non-goals

- Behavioral, field, or logic changes to any extraction function.
- Changes to prompt templates (`.j2` files).
- Changes to `turn.py` import statements (they must work before and after unchanged).

## Solution

Create `ccya/engine/extraction/` subpackage with 7 files. The `__init__.py` re-exports the 3 functions that `turn.py` imports. Internal subpackage imports use full `ccya.engine.extraction.X` style (consistent with the codebase convention). The old `ccya/engine/extraction.py` is deleted after the subpackage is verified.

## Firm decisions

1. `__init__.py` re-exports exactly: `_run_extraction_pipeline`, `_avg_event_ms`, `_context_meta`.
2. No cross-stream imports between `scene.py`, `state.py`, `storytell.py` — they only import from `utils.py` and standard library.
3. `pipeline.py` imports from all 5 other subpackage files.
4. Subpackage internal imports use `ccya.engine.extraction.X` prefix (not relative imports), matching the convention of all existing engine module imports.
5. Each subpackage file uses `logging.getLogger(__name__)`.

## Risks, Ambiguities, and Blockers

- **Ordering of subpackage creation vs. old file deletion:** Must create subpackage first, then delete `extraction.py` in the same commit. If `extraction.py` is deleted before the subpackage exists, `turn.py` will fail to import between commits.
- **`_context_meta` and `_avg_event_ms` are also imported by `turn.py`** — they must be re-exported from `__init__.py` to preserve the import path.
- **Tests are temporarily removed** — validation relies on `make check` and import verification.
- **Python subpackage detection:** The `extraction/` directory needs an `__init__.py` to be treated as a package. If the directory exists but `__init__.py` is missing, imports will silently fail.

## Status
`completed`

## Phases

Single phase — atomic swap of file → subpackage.

---

## Implementation — Phase 1: Create subpackage, move functions, delete old file

### Context files to load

- `ccya/engine/extraction.py` — read the full file to understand function groupings and internal references
- `ccya/engine/turn.py` lines 17–24 — current imports from extraction.py; verify they remain valid after the swap
- `docs/design/engine-file-splitting-design.md` — design authority; "Extraction subpackage" section

### Detailed steps

#### Step 1.1 — Create `ccya/engine/extraction/__init__.py`

**File:** `ccya/engine/extraction/__init__.py` (new)

**What:** Re-export the 3 functions imported by `turn.py`:

```python
"""Three-stream extraction pipeline: scene, state, storytell."""

from ccya.engine.extraction.pipeline import _run_extraction_pipeline
from ccya.engine.extraction.utils import _avg_event_ms, _context_meta
```

All subpackage files will be created in subsequent steps before this directory is importable.

**Why:** `turn.py` imports these 3 functions from `ccya.engine.extraction`. The `__init__.py` preserves this import path.

**Validation:** (will fail until sub-files exist — expected at this point)

#### Step 1.2 — Create `ccya/engine/extraction/utils.py`

**File:** `ccya/engine/extraction/utils.py` (new)

**What:** Move these utility functions and helpers from `ccya/engine/extraction.py`:
- `_text_references_thread(text, thread_id)` → function, check thread IDs referenced in text
- `_filter_evicted_threads(texts, evicted_ids)` → function, filter thread references
- `_context_meta(rendered_system, rendered_user, was_trimmed, trimmed_chars)` → function, build context metadata dict
- `_capitalize_inventory_names(items)` → function, capitalize item names
- `_extract_group_base_type(name)` → function, strip quantity prefixes from NPC names
- `_dedup_compendium_update(cu, existing_npcs, existing_ids)` → function, dedup compendium NPC updates
- `_coerce_scene_json(j)` → function, coerce LLM JSON to match Pydantic expectations
- `_parse_stream_result(raw, model_cls, strip_keys)` → function, parse + validate LLM JSON output
- `_call_stream(messages, config, trace_id, phase, model_cls, strip_keys)` → async function, LLM call with retry
- `_avg_event_ms(save_dir, field_path, n)` → function, average event timing

Imports the same standard library + engine config + models + errors that the original functions used.

**Why:** These are shared utilities consumed by all 3 streams, the pipeline orchestrator, and `turn.py`. Grouping them in `utils.py` avoids duplication.

**Validation:** `python -c "from ccya.engine.extraction.utils import _call_stream, _parse_stream_result; print('ok')"` prints "ok".

#### Step 1.3 — Create `ccya/engine/extraction/context.py`

**File:** `ccya/engine/extraction/context.py` (new)

**What:** Move these from `ccya/engine/extraction.py`:
- `_ExtractionContext` dataclass — fields: `comp_this_turn`, `location_this_turn`, `inventory_this_turn`, `conditions_this_turn`
- `_build_extraction_context(state, scene_result, state_result)` → function, compute this-turn derived context

**Why:** The extraction context is a cross-stream concern consumed by both `storytell.py` and `pipeline.py`.

**Validation:** `python -c "from ccya.engine.extraction.context import _ExtractionContext; print('ok')"` prints "ok".

#### Step 1.4 — Create `ccya/engine/extraction/scene.py`

**File:** `ccya/engine/extraction/scene.py` (new)

**What:** Move this function from `ccya/engine/extraction.py`:
- `_extract_scene_messages(env, narration, state, *, turn_no)` → function, build [system, user] messages for scene extraction stream

**Why:** Scene message building is independent — it only consumes narration text + state and produces LLM messages.

**Validation:** `python -c "from ccya.engine.extraction.scene import _extract_scene_messages; print('ok')"` prints "ok".

#### Step 1.5 — Create `ccya/engine/extraction/state.py`

**File:** `ccya/engine/extraction/state.py` (new)

**What:** Move this function from `ccya/engine/extraction.py`:
- `_extract_state_messages(env, narration, state, *, intent, turn_no)` → function, build [system, user] messages for state extraction stream

**Why:** State message building is independent — it consumes narration + state + intent and produces LLM messages.

**Validation:** `python -c "from ccya.engine.extraction.state import _extract_state_messages; print('ok')"` prints "ok".

#### Step 1.6 — Create `ccya/engine/extraction/storytell.py`

**File:** `ccya/engine/extraction/storytell.py` (new)

**What:** Move this function from `ccya/engine/extraction.py`:
- `_storytell_messages(env, narration, state, *, extraction_ctx, intent, pacing_context, recent_turns, turn_no, band, arc_ttl, config)` → function, build [system, user] messages for storytell extraction stream

Import `_get_resolved_arcs` from `ccya.engine.narrate`, `_fmt_progress` from `ccya.prompts.context`, `derive_allowed_beat_types` from `ccya.engine._pacing`, `build_npc_roster` from `ccya.engine.npc_roster` (same imports the function already has).

**Why:** Storytell message building is the most complex stream — it consumes extraction context from the scene + state streams (via `_build_extraction_context`) plus pacing context. It imports from the same modules it currently imports from.

**Validation:** `python -c "from ccya.engine.extraction.storytell import _storytell_messages; print('ok')"` prints "ok".

#### Step 1.7 — Create `ccya/engine/extraction/pipeline.py`

**File:** `ccya/engine/extraction/pipeline.py` (new)

**What:** Move `_run_extraction_pipeline(env, state, narration, *, rules_outcome, intent, config, trace_id, turn_no, pacing_context, recent_turns)` — the async generator orchestrator (280 lines).

This function imports from all other subpackage files:
```python
from ccya.engine.extraction.scene import _extract_scene_messages
from ccya.engine.extraction.state import _extract_state_messages
from ccya.engine.extraction.storytell import _storytell_messages
from ccya.engine.extraction.context import _build_extraction_context
from ccya.engine.extraction.utils import _call_stream, _context_meta, _capitalize_inventory_names, _dedup_compendium_update
```

Also imports from `ccya.engine.config`, `ccya.engine.markers`, `ccya.models`, `ccya.errors`, and standard library — same imports as the original function.

**Why:** The pipeline orchestrator is the entry point that coordinates all 3 streams. It is the only function imported by `turn.py` (along with 2 utility functions).

**Validation:** `python -c "from ccya.engine.extraction.pipeline import _run_extraction_pipeline; print('ok')"` prints "ok".

#### Step 1.8 — Verify subpackage imports work

**What:** Test that all subpackage files are importable and the public API surface matches.

**Why:** Catch any missing imports, circular dependencies, or incorrect module references before deleting the old file.

**Validation:**
```bash
python -c "
from ccya.engine.extraction import _run_extraction_pipeline, _avg_event_ms, _context_meta
from ccya.engine.extraction.scene import _extract_scene_messages
from ccya.engine.extraction.state import _extract_state_messages
from ccya.engine.extraction.storytell import _storytell_messages
from ccya.engine.extraction.context import _ExtractionContext, _build_extraction_context
from ccya.engine.extraction.utils import _call_stream, _parse_stream_result, _coerce_scene_json, _capitalize_inventory_names, _dedup_compendium_update, _filter_evicted_threads
print('All extraction subpackage imports resolved')
"
```

#### Step 1.9 — Delete `ccya/engine/extraction.py`

**File:** `ccya/engine/extraction.py` (delete)

**What:** Remove the original flat file.

**Why:** All functions have been moved to the subpackage — the original file is now dead code.

**Validation:** `python -c "from ccya.engine.turn import run_turn; print('turn.py imports resolved')"` prints "turn.py imports resolved" (verifies the import chain through the subpackage).

#### Step 1.10 — Run `make check`

**What:** Verify lint and typecheck pass with the new subpackage structure.

**Why:** Final validation that no import paths are broken, no symbols are missing, and type annotations are consistent.

**Validation:**
```bash
make check
```
Exit code 0 expected. If typecheck fails, fix type annotation paths (e.g., `TYPE_CHECKING` imports that referenced `extraction.py`).

### Tests to write or update

No tests — tests are temporarily removed. Validation relies on `make check` and import verification.
