# Plan: Extraction Pipeline DRY

**Status: scoping**

**Ticket:** I-23 (Engine core tech debt consolidation)

## Design Reference

I-23 plan: `roadmap/improvements/I-23-engine-core-tech-debt-consolidation.md`

## Purpose

Extract the common stream execution pattern from the 3 near-identical extraction streams (scene, state, record) in `pipeline.py` (352 lines). Each stream follows the same flow: build messages → trim → call_stream with retry → yield phase_done + panel_update → handle exceptions → build extraction_event. Only the message builder, result type, and preview/panel data differ.

**Goal:** Reduce pipeline.py from 352 lines to ~110 lines by removing ~240 lines of duplicated stream execution logic. The 3 message builder functions and 3 variant definitions stay as-is (they are the actual differences).

## Constraints

- No behavioral change — extraction results, event structure, and error handling must be identical
- Each stream must still yield the same events in the same order: `phase_start` → (LLM calls + yields) → `phase_done` → `panel_update`
- The post-stream shared logic (dedup, capitalize, merge) stays in `_run_extraction_pipeline`
- `_ExtractionVariant` dataclass is the only new public type added to pipeline.py
- The 3 wrapper functions (`_scene_stream`, `_state_stream`, `_record_stream`) become 5-8 line thin wrappers

## Phase 1: Extract common stream execution

**Files:** `ccya/engine/extraction/pipeline.py`

**Dependencies:** None

### Step 1.1 — Add `_ExtractionVariant` dataclass

**File:** `ccya/engine/extraction/pipeline.py`

**What:**
- Add `_ExtractionVariant` dataclass after imports, before `_run_extraction_pipeline`
- Fields:
  ```python
  @dataclass
  class _ExtractionVariant:
      name: str
      result_type: type
      build_messages: Callable[..., list[dict[str, str]]]
      build_messages_kwargs: dict[str, Any]
      strip_keys: tuple[str, ...]
      preview_builder: Callable[[WorldState, Any], WorldState]
      panel_builder: Callable[[WorldState], dict[str, Any]]
  ```
- Import `dataclass` from `dataclasses`
- Import `Callable` from `collections.abc`

**Why:** The variant dataclass captures all per-stream differences in one place. The generic function takes a single variant parameter instead of 10+ individual parameters.

### Step 1.2 — Write `_run_extraction_stream` generic function

**File:** `ccya/engine/extraction/pipeline.py`

**What:**
- Add `_run_extraction_stream` async generator function after the variant dataclass
- Signature:
  ```python
  async def _run_extraction_stream(
      state: WorldState,
      variant: _ExtractionVariant,
      config: EngineConfig,
      trace_id: str,
      turn_no: int,
  ) -> AsyncIterator[tuple[str, Any]]:
  ```
- Body implements the common flow:
  1. Call `variant.build_messages(state, **variant.build_messages_kwargs)` to get messages
  2. Capture pre-trim content for context_meta (first system msg, last user msg)
  3. Call `trim_messages(msgs, config.context_window)`
  4. Initialize timing, usage, attempts, retry_errors
  5. Try block: call `_call_stream(msgs, config, trace_id, variant.name, variant.result_type, strip_keys=variant.strip_keys)`
  6. Build `extraction_event` dict with output, skipped, attempts, retry_errors, tokens, ms, context_meta
  7. Log results (debug line with result type, relevant field counts)
  8. Yield `("phase", {"phase": "extract_stream_done", "stream": variant.name})`
  9. Build preview state via `copy.deepcopy(state)` + `apply_delta` using variant's result fields
  10. Yield `("panel_update", {"panel": variant.name, "data": variant.panel_builder(preview_state)})`
  11. Except LlmcTimeout: log warning, set extraction_event with skipped + error
  12. Except Exception: log error (scene) or warning (state/record), set extraction_event with skipped + error
  13. Return `(result, extraction_event)` via `raise StopAsyncIteration((result, extraction_event))`

**Why:** This is the common flow shared by all 3 streams. It handles timing, trimming, LLM calls, retries, exception handling, event yields, preview state building, and panel updates. The variant dataclass parameterizes all differences.

### Step 1.3 — Refactor 3 stream functions to thin wrappers

**File:** `ccya/engine/extraction/pipeline.py`

**What:**
- Replace the inline stream blocks in `_run_extraction_pipeline` with calls to the 3 thin wrapper functions
- Each wrapper:
  ```python
  async def _scene_stream(state, context, turn_no, config, trace_id):
      variant = _ExtractionVariant(
          name="scene",
          result_type=SceneExtractResult,
          build_messages=_extract_scene_messages,
          build_messages_kwargs={"narration": context.user_input, "state": state, "turn_no": turn_no},
          strip_keys=(),
          preview_builder=_build_scene_preview,
          panel_builder=_build_scene_panel,
      )
      async for event in _run_extraction_stream(state, variant, config, trace_id, turn_no):
          yield event
  ```
- Similarly for `_state_stream` and `_record_stream`
- The `_build_scene_preview`, `_build_state_preview`, `_build_scene_panel`, `_build_state_panel` are extracted from the inline blocks as private helper functions

**Why:** The 3 wrappers become self-documenting references showing exactly what differs per stream. The actual stream execution logic is in the generic function.

### Step 1.4 — Update `_run_extraction_pipeline` to use wrappers

**File:** `ccya/engine/extraction/pipeline.py`

**What:**
- Replace the 3 inline stream blocks (scene, state, record) with:
  ```python
  async for event in _scene_stream(state, context, turn_no, config, trace_id):
      yield event
  ```
- The post-stream shared logic (dedup, capitalize, merge) stays unchanged
- The return 7-tuple stays unchanged
- The `scene_result` and `state_result` variables are captured from the `StopAsyncIteration.value` of the wrapper calls

**Why:** The pipeline function becomes a clean sequence of 3 wrapper calls plus the post-stream logic. The inline duplication is gone.

## Verification

- `make typecheck` passes
- `make lint` passes
- `ev.py turn 3 --save-dir evals/runs/latest` produces identical extraction events (scene, state, record streams all yield correctly)
- No behavioral change: extraction results, event structure, error handling identical to before

## Files changed

| File | Before | After | Delta |
|------|--------|-------|-------|
| `pipeline.py` | 352 lines | ~110 lines | -242 |
| `scene.py` | 40 lines | 40 lines | 0 |
| `state.py` | 46 lines | 46 lines | 0 |
| `record.py` | 100 lines | 100 lines | 0 |

## Done when

- `_ExtractionVariant` dataclass added
- `_run_extraction_stream` generic function implemented
- 3 stream functions refactored to thin wrappers
- `_run_extraction_pipeline` updated to use wrappers
- `make check` passes
- `docs/repomap.md` updated if module boundaries change
