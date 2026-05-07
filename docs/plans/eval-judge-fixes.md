# eval-judge-fixes — Judge reliability, logging, and trace structure

## Problem

The eval harness has three issues:

1. **Pydantic validation error**: `GMBeat.type` rejects `'ambient'` as a value. The LLM confuses `type` with `surface_as` and outputs `type: "ambient"`.
2. **Judge timeout**: The judge call uses a 180s timeout. The judge sends a very large trace (all prompts + outputs for 10 turns). The model times out before responding.
3. **No visibility**: The eval process has almost no logging during the judge phase. No progress indicators, no timing info.
4. **Truncation**: The judge trace builder truncates narration and extraction outputs, and falls back to a compact trace. The judge should see everything.
5. **System prompts duplicated**: The trace includes system prompts once (static context) AND per-turn. System prompts are immutable — they should appear only once.

## Changes

### 1. Fix `gm_beat.type` validation error

**`ccya/models.py:378`** — Add `'ambient'` to `GMBeat.type` Literal:
```python
type: Literal["complication", "revelation", "opportunity", "breathing_room", "pressure", "ambient"] | None = None
```

**`ccya/prompts/extract_progress_system.j2`** — Clarify the distinction between `type` and `surface_as`:
- Add a note near the GM Beat section explaining that `type` describes the beat category and `surface_as` describes how it's presented
- Explicitly state that `ambient` is a `surface_as` value, not a `type` value
- Add a "Common mistake" callout

### 2. Remove judge timeout

**`ccya/eval/config.py`** — Remove `max_input_chars` from `JudgeConfig`:
- Remove the field entirely
- Update `load_eval_config()` to not read it
- Update `cli.py _cmd_pack()` to not print it

**`ccya/eval/judge.py:517-522`** — Pass `timeout=600.0` to `chat()` for the judge call

### 3. Remove all truncation from judge trace

**`ccya/eval/judge.py`** — Remove:
- `_NARRATE_TRUNC = 800` and `_EXTRACT_TRUNC = 300` constants
- `_compact_trace()` function entirely (lines 118-174)
- The fallback to `_compact_trace()` in `build_trace()` (lines 360-361)
- The greedy middle-fill truncation logic in `build_trace()` (lines 371-401)
- The truncation marker at lines 398-400
- The `_TRUNC_MARKER` constant

**`ccya/eval/judge.py`** — Simplify `build_trace()`:
- Render static context
- Render ALL turn blocks (no truncation)
- Concatenate and return

### 4. System prompts appear only once

**`ccya/eval/judge.py`** — Restructure the trace:

**Static context** (`_render_static_context`):
- Pack style, seed state, engine constants
- 5 system prompts (rules, narrate, extract scene, extract state, extract progress)

**Per-turn** (`_render_turn_context`):
- Remove per-turn system prompts entirely
- Keep: user prompts (rules, narrate, extract scene, extract state, extract progress)
- Keep: engine outputs, applied/rejected deltas, actions, telemetry, state snapshot

This means the judge sees each system prompt exactly once at the top, and each user prompt exactly once per turn.

### 5. Add progress logging

**`ccya/eval/__init__.py`** — Set up a dedicated logger:
```python
import logging
logger = logging.getLogger("ccya.eval")
```

**`ccya/eval/judge.py`** — Add structured logging:
- `logger.info("building trace: %d turns, static context %d chars", ...)`
- `logger.info("judge request sent, waiting for response...")`
- `logger.info("judge response received in %.1fs", ...)`
- `logger.info("judge parsed: overall_score=%d", ...)`

**`ccya/eval/runner.py`** — Add structured logging:
- `logger.info("starting scenario: id=%s pack=%s turns=%d", ...)`
- `logger.info("turn %d/%d: %s (%.1fs)", ...)`
- `logger.info("scenario complete: %d turns, %d errors", ...)`

**`ccya/eval/cli.py`** — Add stderr progress messages:
- `[eval] runner done: N turns (of M), E errors → path`
- `[eval] building judge trace: N turns, S chars`
- `[eval] sending judge request (timeout=600s)…`
- `[eval] judge response received in X.Xs`
- `[eval] judge overall_score=N`
- `[eval] report: path`

### 6. Update config loading

**`ccya/eval/config.py`** — Remove `max_input_chars` from `JudgeConfig` and `load_eval_config()`.

**`evals/config.yaml`** — Remove `max_input_chars` line.

### 7. Update report generation

**`ccya/eval/report.py`** — Check if `max_input_chars` is referenced in report generation and remove those references.

## Files changed

| File | Change |
|------|--------|
| `ccya/models.py` | Add `'ambient'` to `GMBeat.type` |
| `ccya/prompts/extract_progress_system.j2` | Clarify type vs surface_as |
| `ccya/eval/__init__.py` | Add dedicated logger |
| `ccya/eval/config.py` | Remove `max_input_chars` |
| `ccya/eval/judge.py` | Remove truncation, restructure trace, add logging, set timeout=600 |
| `ccya/eval/runner.py` | Add structured logging |
| `ccya/eval/cli.py` | Add stderr progress, remove max_input_chars from pack output |
| `ccya/eval/report.py` | Remove max_input_chars references |
| `evals/config.yaml` | Remove max_input_chars line |

## Testing

- Run `make eval` and verify:
  - No Pydantic validation errors for `gm_beat.type`
  - Judge completes without timeout
  - Report is generated
  - Progress messages appear on stderr
- Check `evals/runs/<ts>/` artifacts for full trace (no truncation markers)
