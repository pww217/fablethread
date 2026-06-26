---
title: "Async Steps (World + Sanitizer) — Full Event/Prompt Recording"
status: done
created: 2026-06-26
labels:
  - engine
  - eval
  - turn-viewer
  - observability
---

## Problem

The two async end-of-turn steps (sanitizer and World) produce no event-level trace. Unlike all other pipeline steps (ruling, narrate, extract), there is no:

- Event entry in `events.jsonl` with inputs/outputs
- Prompt entry in `prompts.jsonl` with rendered templates
- LLM response capture (raw text)
- Error/failure logging visible to eval or turn viewer

This means:
- `ev check` cannot validate World output (beat_candidates never appear in events)
- `ev play --eval` cannot detect World step failures
- Turn viewer cannot show World step prompts or responses
- Debugging World step issues requires manually reading `state.yaml`
- Same blind spot exists for sanitizer (thread sanitization)

## Current State

### Ruling / Narrate / Extract (synchronous steps)
Each step produces:
- Event entry in `events.jsonl` with inputs, outputs, metrics
- Prompt entries in `prompts.jsonl` with rendered system + user templates
- LLM response captured (raw text, trimmed text, token counts)
- Errors/failures recorded in event

### Sanitizer / World (async end-of-turn steps)
No event entries. Only final state is saved to `state.yaml`.

The async window runs at `turn.py:505-529` after `yield ("complete", ...)` and before the generator returns. It:
1. Runs sanitizer (thread sanitization)
2. Runs World (beat candidate generation)
3. Saves state after each

But nothing is written to events.jsonl or prompts.jsonl.

## Requirements

### 1. Sanitizer event recording
When sanitizer runs (turn.py:507-516), capture:
- Input state (threads before sanitization)
- Output state (threads after sanitization)
- Deltas applied (which threads were modified/removed)
- Any errors
- Timing metrics

Write to `events.jsonl` as a new event entry with `type: "sanitize"`.

### 2. World step event recording
When World runs (turn.py:518-529), capture:
- Rendered `world_system.j2` template
- Rendered `world_user.j2` template (with all context variables)
- LLM raw response (before parsing)
- Parsed output (beat candidates list)
- Any errors/failures
- Timing metrics

Write to `events.jsonl` as a new event entry with `type: "world"`.
Write rendered templates to `prompts.jsonl`.

### 3. Event format
Same pattern as existing steps. Each event entry should include:
- `type`: step name ("sanitize" or "world")
- `turn`: turn number
- `trace_id`: trace ID
- `input`: step inputs (state, narration, etc.)
- `output`: step outputs (modified state, beat candidates, etc.)
- `metrics`: timing, token counts if applicable
- `errors`: any errors encountered

### 4. Prompts format
Same pattern as existing prompts. Each prompt entry should include:
- `type`: step name
- `turn`: turn number
- `trace_id`: trace ID
- `system`: rendered system template
- `user`: rendered user template
- `messages`: full message array (for LLM call reproduction)

### 5. Ev compatibility
- `ev check` checkers should be able to read sanitizer/world events
- `ev play --eval` should detect and report World step failures
- `ev.py prompt-eval` should work for World templates

### 6. Turn viewer compatibility
- Turn viewer should display sanitizer and World steps alongside other steps
- Prompts should be viewable (system + user templates)
- Outputs should be viewable (modified state, beat candidates)
- Errors should be visible

## Implementation Notes

### Where to add recording
In `turn.py`, within the async window (lines 507-529), after each step completes:
1. Capture the data
2. Write to events.jsonl via `append_event()`
3. Write to prompts.jsonl via `append_prompts()` (for World step)

### Event structure
```json
{
  "type": "world",
  "turn": 5,
  "trace_id": "abc123",
  "ts": "2026-06-26T...",
  "input": {
    "state": { ... },
    "narration": "...",
    "candidate_npcs": [...],
    "pacing_context": { ... }
  },
  "output": {
    "beat_candidates": [
      {"type": "pressure", "effect": "...", "driver": "fear"}
    ]
  },
  "prompts": {
    "system": "rendered template...",
    "user": "rendered template..."
  },
  "llm_response": "raw LLM text...",
  "metrics": {
    "ms": 4500,
    "tokens_in": 3200,
    "tokens_out": 450
  },
  "errors": []
}
```

### No backward compatibility needed
This is new data. No existing code reads these event types. Clean implementation only.

### No new files needed
Use existing `append_event()` and `append_prompts()` functions. Same files as other steps.

## Done When

- [ ] Sanitizer event written to events.jsonl with full input/output
- [ ] World event written to events.jsonl with full input/output
- [ ] World prompts written to prompts.jsonl
- [ ] `ev check` can read sanitizer/world events
- [ ] `ev play --eval` reports World step failures
- [ ] Turn viewer displays sanitizer and World steps
- [ ] Prompts are viewable in turn viewer
- [ ] All event formats match existing step patterns
- [ ] No antipatterns, no tech debt, no backward compat

## Files to Touch

- `ccya/engine/turn.py` — add recording in async window
- `ccya/state/io.py` — may need updates to `append_event`/`append_prompts` if new formats required
- `ccya/ev/checkers/` — may need new checkers for sanitizer/world validation
- `ccya/ev/events.py` — may need new extraction helpers for sanitizer/world events
- `ccya/server/` — turn viewer may need updates to display new event types
