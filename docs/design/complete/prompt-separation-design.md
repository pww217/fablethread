# Prompt Separation Design

## Purpose

This document defines the split of rendered prompt strings out of `events.jsonl` into a separate `prompts.jsonl` file. It is the design authority for plans implementing this storage separation across the engine, EV tooling, and Turn Viewer. It is a prerequisite to the eval system design at `docs/design/eval-system-design.md`.

## Problem Statement

Rendered prompt strings (`rendered_system`, `rendered_user`) account for ~75% of `events.jsonl` file size (~2.5 MB of ~3.3 MB for a 30-turn session). After stripping, `events.jsonl` drops to ~846 KB (25% of original). The EV tooling and LLM agents analyzing game state must read the entire file, but these prompt strings are never needed for game logic, checkers, or state analysis. Prompts are a historical artifact useful only for debugging "what did the LLM actually see?" — a rare, explicitly requested operation.

Additionally, narrate prompt strings are stored **twice**: once in `extraction_event.narrate.rendered_system`/`rendered_user` and once in `narrate_prompt.rendered_system`/`rendered_user`. This doubles the bloat for narrate prompts.

## Constraints

- Existing `events.jsonl` readers (checkers, EV tooling, turn viewer) must continue to work — the schema changes must be backward-compatible for readers that access non-prompt fields.
- `prompts.jsonl` must be loadable on demand without reading `events.jsonl`.
- The engine must write both files with minimal performance overhead (single JSON dump per entry).
- No new external dependencies. The Jinja2 environment already exists in the engine.

## Non-goals

- This does not change the content of prompt templates. Templates remain in `ccya/prompts/`.
- This does not change the prompt rendering pipeline (Jinja2 context construction, template selection). Only the storage of rendered output changes.
- This does not change `state.yaml` format or content.
- This does not change how checkers fundamentally work — only `pacing_directives` and `gm_beat_lifecycle` need internal refactors.
- This does not change the chronicle (`chronicle.md`) or save state format.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Remove `rendered_system` and `rendered_user` from all prompt fields in `events.jsonl` | Strip stored rendered prompt strings from `ruling_prompt`, `narrate_prompt`, `extraction.narrate`, `extraction.scene`, `extraction.state`, `extraction.storytell` | 79% file bloat. Prompts are not game state. |
| Write prompts to `prompts.jsonl` | One JSON line per turn per stream containing `ts`, `trace_id`, `turn`, `stream`, `rendered_system`, `rendered_user`, `context_meta` | On-demand loading for turn viewer, `ev prompt`, and `prompt-eval`. Keeps prompts accessible without bloating `events.jsonl`. |
| `prompt-eval --from-events` reads from `prompts.jsonl` | Flag now reads from `prompts.jsonl` instead of extracting from `events.jsonl`. Could rename to `--historical` or `--from-prompts` to reflect the new data source. | The flag still serves its original purpose: use stored historical prompts rather than re-rendering from codebase. Data source changes from `events.jsonl` to `prompts.jsonl`. |
| `ev prompt` reads from `prompts.jsonl` | Change data source from `events.jsonl` to `prompts.jsonl` | Prompt inspection still works on demand without bloating the default load path. |
| Turn viewer reads prompts from `prompts.jsonl` | Change the prompt tab data source | Prompt display in the UI still works but loads a separate file. |
| `pacing_directives` re-renders narrate/storytell prompts | Instead of reading `narrate_prompt.rendered_user`, construct Jinja2 env and re-render | Verifies the template renders the directive — the original intent of the check. No `prompts.jsonl` needed. |
| `gm_beat_lifecycle` re-renders narrate prompt | Instead of reading `narrate_prompt.rendered_user` for BINDING block check, re-render from template | Verifies the template includes rules outcome. No `prompts.jsonl` needed. |
| Remove duplicate prompt storage in `extraction.narrate` | `extraction_event.narrate` already stores `rendered_system`/`rendered_user` which duplicates `narrate_prompt`. Strip them from `extraction_event.narrate`, keep only `output` + metrics. | Eliminates the double-stored narrate prompts. |
| Keep `output`, `parse_error`, metrics, `context_meta` in `events.jsonl` prompt fields | `ruling_prompt.output`, `narrate_prompt.output`, `extraction.*.output`, `ruling_prompt.parse_error`, token counts, ms | The LLM output and error info are part of game history. `context_meta` provides trimming info without storing verbose strings. |

## Open Questions

- [OPEN: Should `prompts.jsonl` be written in the same `append_event` call (engine turn.py writes both files atomically), or should it be a post-hoc extraction step?]
- [OPEN: For Turn Viewer 2, should the prompt tab load `prompts.jsonl` on demand via a separate HTTP endpoint, or should the existing `/api/turns` endpoint include a `load_prompts=true` flag?]
- [OPEN: Should `prompts.jsonl` use the same event schema as `events.jsonl` (same `turn`/`trace_id`/`ts` fields) or a different schema focused on prompt structure?]

## Current State — What Exists

### Write Paths

Rendered prompts are written to `events.jsonl` at three points in the engine:

**1. `engine/turn.py` lines 409-421** — Ruling and narrate prompt blobs:

```python
"ruling_prompt": {
    "rendered_system": rendered_ruling_system,   # ~5 KB
    "rendered_user": rendered_ruling_user,        # ~3.6 KB
    "output": ruling_raw_response,               # ~400 B
    "parse_error": ruling_parse_error,
    "context_meta": {...},
},
"narrate_prompt": {
    "rendered_system": rendered_narr_system,     # ~14 KB
    "rendered_user": rendered_narr_user,          # ~6 KB
    "output": narrative,                          # ~1.4 KB
    "context_meta": {...},
},
```

**2. `engine/turn.py` lines 215-222** — Narrate prompt stored a second time in extraction_event:

```python
extraction_event["narrate"] = {
    "rendered_system": rendered_narr_system,     # duplicate of narrate_prompt
    "rendered_user": rendered_narr_user,          # duplicate of narrate_prompt
    "output": narrative,
    "tokens_in": ...,
    "tokens_out": ...,
    "ms": ...,
},
```

**3. `engine/extraction/pipeline.py` lines 88-261** — Scene, state, storytell prompt blobs (each ~10-20 KB of rendered strings + ~2-8 KB output):

```python
extraction_event[stream] = {
    "rendered_system": ...,    # stream-specific system prompt
    "rendered_user": ...,      # stream-specific user prompt
    "output": parsed_output,
    "skipped": False,
    "attempts": 1,
    "retry_errors": [],
    "tokens_in": ...,
    "tokens_out": ...,
    "ms": ...,
}
```

### Read Paths

| Reader | File | Fields Read | Purpose |
|---|---|---|---|
| `pacing_directives` (checker) | `events.jsonl` | `narrate_prompt.rendered_user`, `storytell.rendered_user` | Verify directive/BINDING text in prompt |
| `gm_beat_lifecycle` (checker) | `events.jsonl` | `narrate_prompt.rendered_user` | Verify BINDING block presence |
| `ev prompt` (inspect) | `events.jsonl` | `rendered_system`, `rendered_user` per stream | Display prompt for a specific turn |
| Turn Viewer (tv.py) | `events.jsonl` | `rendered_system`, `rendered_user` per stream | Display prompt tab in UI |
| `prompt-eval --from-events` | `events.jsonl` | `rendered_system`, `rendered_user`, `output` | Re-use historical prompt for LLM call |

### Problems with Current State

1. **~79% of `events.jsonl` is rendered prompt text.** For a 30-turn session: ~2.6 MB of prompts, ~700 KB of actual game state/events.
2. **Narrate prompts stored twice.** `extraction_event.narrate.rendered_system`/`rendered_user` duplicates `narrate_prompt.rendered_system`/`rendered_user`.
3. **EV tooling must load all prompt data even when it only needs game state.** Checkers, summary, timing, and state-inspection commands all read the full file.
4. **LLM agents analyzing game state consume context budget on prompt text.** 10k+ lines of rendered prompts vs ~2k lines of actual state.
5. **No lazy loading.** There is no mechanism to load only non-prompt fields from `events.jsonl`.

## Proposed Solution

### Core Changes

**1. New file: `prompts.jsonl`**

One JSON line per LLM call. Written by the engine alongside `events.jsonl`.

Schema:

```
{
    "ts": float,          # timestamp
    "trace_id": str,      # correlation ID
    "turn": int,          # turn number
    "stream": str,        # "ruling" | "narrate" | "scene" | "state" | "storytell"
    "rendered_system": str,
    "rendered_user": str,
    "context_meta": {     # same structure as today
        "system_chars": int,
        "user_chars": int,
        "total_chars": int,
        "est_tokens": int,
        "trimmed": bool,
        "trimmed_chars": int
    }
}
```

5 entries per turn (ruling, narrate, scene, state, storytell) × 30 turns = 150 lines for a standard session.

**2. Stripped `events.jsonl` per-stream structure**

`ruling_prompt`:
```python
"ruling_prompt": {
    "output": str | dict,
    "parse_error": str,
    "context_meta": {...},
}
```

`narrate_prompt`:
```python
"narrate_prompt": {
    "output": str,
    "context_meta": {...},
}
```

`extraction_event.narrate`:
```python
"narrate": {
    "output": str,
    "tokens_in": int,
    "tokens_out": int,
    "ms": float,
}
```

`extraction_event.scene` / `extraction_event.state` / `extraction_event.storytell`:
```python
stream: {
    "output": dict,
    "skipped": bool,
    "attempts": int,
    "retry_errors": list,
    "tokens_in": int,
    "tokens_out": int,
    "ms": float,
}
```

**3. Checker refactors**

`pacing_directives` — Replace `narrate_prompt.rendered_user` reads with on-the-fly Jinja2 re-rendering. The checker will `_render(env, template_name, ctx)` using the same Jinja2 environment and context variables the engine uses. This verifies the prompt template renders the directive correctly, which is the actual intent of the check.

`gm_beat_lifecycle` — Same approach: re-render the narrate user prompt and check for `rules_outcome (BINDING` in the re-rendered output.

Both checkers will need access to the Jinja2 environment. This can be done by importing `_build_jinja_env` / `_render` from `engine/config.py` and constructing the context from event data.

**4. Prompt reader refactors**

| Reader | Before | After |
|---|---|---|
| `ev prompt` | Reads from `events.jsonl` event dict | Loads `prompts.jsonl` lines filtered by `turn` and `stream` |
| Turn Viewer | Reads from `events.jsonl` event dict | Loads `prompts.jsonl` lines filtered by `turn` and `stream` |
| `prompt-eval --from-events` | Reads from `events.jsonl` event dict | Reads from `prompts.jsonl` instead (same behavior, new data source) |

**Data flow diagram:**

```
Engine (turn.py + pipeline.py)
      │
      └── append_event(save_dir, event, prompts=None)
          │
          ├── writes event to events.jsonl  (no rendered prompts)
          │
          └── if prompts is not None:
              writes prompt_entry to prompts.jsonl

EV Tooling / Checkers
      │
      ├── load_events("events.jsonl") ──► filtered turn events  (lean, ~700 KB)
      │
      └── (on demand) load_prompts("prompts.jsonl") ──► prompt entries

Turn Viewer
      │
      ├── GET /api/turns ──► reads events.jsonl, returns turn list
      │
      └── GET /api/prompts?turn=N&stream=S ──► reads prompts.jsonl, returns prompt text
```

### Alternatives Considered and Rejected

| Alternative | Why Rejected |
|---|---|
| Keep prompts in `events.jsonl` but gzip the file | Adds decompression step to all readers. Does not solve the agent context-bloat problem. |
| Store prompts only in memory (never persist) | Turn viewer and historical inspection lose prompt display entirely. |
| Post-hoc extraction script to separate prompts | Requires running an extra step after each session. Engine should write correctly the first time. |
| Add `?fields=...` query to `load_events` to skip prompt fields | More complex data access pattern. Every reader must know to exclude prompts. Separate file is simpler. |

## Failure Modes and Risks

1. **`prompts.jsonl` and `events.jsonl` get out of sync.** If the engine crashes between writing `events.jsonl` and `prompts.jsonl`, the prompt file could be missing entries for the last turn. Mitigation: write `events.jsonl` first, then `prompts.jsonl`. The EV tool can detect missing prompt entries by comparing turn counts across files.

2. **Turn Viewer loads `prompts.jsonl` synchronously on every page load.** If the file is large (e.g., 500-turn session), this degrades UI performance. Mitigation: load prompts on demand per-turn-per-stream via a separate API call, not in the batch turns endpoint.

3. **`pacing_directives` and `gm_beat_lifecycle` re-rendering produces different output than the original prompt.** If the Jinja2 context reconstruction is not perfectly faithful, the checker might report false positives. Mitigation: the context reconstruction should use the same data sources as `build_prompt_context()` in `prompt_eval.py`, which already works correctly.

4. **Existing saved `events.jsonl` files lose prompt display in turn viewer.** After the change, old game saves will show blank prompt tabs. Mitigation: document this as a breaking change. Old files can still be inspected via `prompt-eval` re-rendering.

5. **Checkers fail if `_render` import changes or template paths shift.** Mitigation: `pacing_directives` and `gm_beat_lifecycle` should catch import/render errors and skip the check gracefully.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `rendered_system` field | All prompt blobs in `events.jsonl` | Moved to `prompts.jsonl` |
| `rendered_user` field | All prompt blobs in `events.jsonl` | Moved to `prompts.jsonl` |
| `rendered_system`/`rendered_user` from `extraction_event.narrate` | `engine/turn.py` line 216-217 | Stripped — only output + metrics remain |
| `--from-events` behavior | `ev.py prompt-eval dump` and `call` | Flag now reads from `prompts.jsonl` instead of `events.jsonl`. Could rename to `--from-prompts` or `--historical`. |

## What Is Unchanged

- `events.jsonl` file path and overall JSONL format.
- `state.yaml` format and content.
- `chronicle.md` format.
- `context_meta` field — stays in events for trimming info without verbose strings.
- `output`, `parse_error`, `skipped`, `attempts`, `retry_errors`, `tokens_in`, `tokens_out`, `ms` fields — stay in `events.jsonl`.
- Checker framework (`@register_checker`, `CheckerResult`, `run_checker`) — unchanged.
- `ev.py` CLI command structure — unchanged.
- `ev.py play` — unchanged.
- `ev.py eval run` — unchanged.
- All LLM checkers (`directive_tone_match`, `beat_narrative_chain`, `state_fidelity`) — unchanged.
- `ev.py prompt-eval` CLI interface — the `--from-events` flag reads from `prompts.jsonl` instead of `events.jsonl`.
- Prompt templates in `ccya/prompts/` — unchanged.
- Prompt context construction (`build_prompt_context` in `prompt_eval.py`) — unchanged.

## New Model Shapes

**`events.jsonl` prompt field shapes** (per-stream, reduced):

```python
# ruling_prompt
{
    "output": str | dict,         # LLM raw response (JSON string or parsed)
    "parse_error": str,            # empty if no error
    "context_meta": dict,          # {"system_chars", "user_chars", "total_chars", "est_tokens", "trimmed", "trimmed_chars"}
}

# narrate_prompt
{
    "output": str,                # narration prose
    "context_meta": dict,
}

# extraction_event.narrate
{
    "output": str,                # narration prose
    "tokens_in": int,
    "tokens_out": int,
    "ms": float,
}

# extraction_event.scene / .state / .storytell
{
    "output": dict,               # parsed extraction output
    "skipped": bool,
    "attempts": int,
    "retry_errors": list,
    "tokens_in": int,
    "tokens_out": int,
    "ms": float,
}
```

**`prompts.jsonl` entry:**

```python
{
    "ts": float,                  # timestamp, matches events.jsonl
    "trace_id": str,              # correlation ID
    "turn": int,                  # turn number
    "stream": str,                # "ruling" | "narrate" | "scene" | "state" | "storytell"
    "rendered_system": str,       # the full rendered system prompt
    "rendered_user": str,         # the full rendered user prompt
    "context_meta": dict,         # {"system_chars", "user_chars", "total_chars", "est_tokens", "trimmed", "trimmed_chars"}
}
```

## Context for Implementation

- `ccya/engine/turn.py` — Lines 215-222 (extraction_event narrate with rendered_system/rendered_user), 409-421 (ruling_prompt at 409-415, narrate_prompt at 416-421). Primary write path for ruling and narrate prompts, plus duplicate narrate storage in extraction_event.
- `ccya/engine/extraction/pipeline.py` — Lines 88-89 (scene rendered_system/rendered_user), 133-134 (state rendered_system/rendered_user), 258-259 (storytell rendered_system/rendered_user). Write paths for scene/state/storytell prompts in extraction_event.
- `ccya/state/chronicle.py` — `append_event()` function. Add an optional `prompts: list[dict] | None` parameter. When provided, write prompt entries to `prompts.jsonl` in the same file-handle session.
- `ccya/ev/prompt_eval.py` — Lines 332-343 (`cmd_prompt_eval_dump`), 396-405 (`cmd_prompt_eval_call`). Reads `rendered_system`/`rendered_user` from events when `--from-events` is set. Needs to be changed to read from `prompts.jsonl` instead.
- `ccya/ev/inspect.py` — Lines 36-37. `extract_prompt()` reads `rendered_system`/`rendered_user` from event blobs. Needs a `prompts.jsonl` load path.
- `ccya/server/tv.py` — Lines 525-526. Turn Viewer reads `rendered_system`/`rendered_user` from event prompt blobs. Needs a `prompts.jsonl` load path.
- `ccya/ev/checkers/pacing.py` — Lines 28, 41, 58-59. Reads `narrate_prompt.rendered_user` and `storytell.rendered_user`. Needs re-render refactor.
- `ccya/ev/checkers/gm_beat.py` — Line 64. Reads `narrate_prompt.rendered_user`. Needs re-render refactor.
- `ccya/engine/config.py` — `_build_jinja_env()` and `_render()` functions. Already available for import by checkers.
- `ccya/ev/events.py` — `extract_field()`, `load_events()`, `filter_turn_events()`. New `load_prompts()` function needed.
