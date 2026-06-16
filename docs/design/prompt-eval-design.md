# Prompt Eval Design

## Purpose

A `prompt-eval` command for `ev.py` that renders individual pipeline prompts with live data from a save, optionally calls the LLM, and evaluates the output. This is for testing and iterating on prompt templates in isolation from the full turn pipeline.

Reference: "This document is the design authority for plans implementing `ev.py prompt-eval`."

## Problem Statement

Prompt templates (`ccya/prompts/*.j2`) are currently tested only through the full turn pipeline (`ev.py play`), which is slow (~1 min/turn, 5 LLM calls) and hard to isolate. There is no fast path to:

1. Render a single prompt (system + user) with live data from an existing save.
2. Send it to the LLM and evaluate the output.
3. Iterate on the prompt template and re-test immediately.

The existing `ev.py prompt N stream user` dumps rendered prompts from events.jsonl but does not call the LLM. The existing `ev.py eval run` runs the full pipeline. Neither supports the fast prompt-test loop.

## Constraints

- Minimal new code. One new command module (`ccya/ev/prompt_eval.py`), maybe 3-4 new checkers.
- Reuse existing infrastructure: `_render()`, `llm_client.chat()`, `CheckerResult`, checker registry.
- Use rendered prompts from events.jsonl as the source of truth (what actually went to the LLM).
- Same output format as `ev.py check` for consistency.
- Python 3.13+ only (ev.py requirement).
- No new configuration files. Scenarios live alongside existing YAML scenarios.

## Non-goals

- Full turn pipeline testing (already covered by `ev.py eval run`).
- Prompt rendering from scratch (reuses stored rendered prompts).
- Multi-turn prompt testing (single turn at a time).
- Prompt diffing or versioning.
- Web UI for prompt testing.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Command name | `ev.py prompt-eval` | Follows `ev.py` naming convention. Distinguishes from `ev.py prompt` (dump only) and `ev.py eval` (full pipeline). |
| Subcommands | `dump` and `call` | `dump` renders and prints (no LLM). `call` renders + LLM + check. Separates inspection from evaluation. |
| Data source | Rendered prompts from events.jsonl | Source of truth — what actually went to the LLM. Avoids re-rendering which could differ. |
| LLM call | `llm_client.chat()` | Same client the engine uses. No new LLM abstraction. |
| Output format | Same as `ev.py check` | Consistency. Users already know how to read checker results. |
| Scenario format | YAML, extends existing `ev/scenario.py` pattern | Reuses `Scenario` dataclass pattern. Minimal new types. |
| New checkers | `golden_match`, `prose_quality`, `directive_adherence`, `extraction_format` | Prompt-specific checks. Deterministic where possible, LLM-based where needed. |
| Stream selection | Single stream per run | Keeps scope simple. Users run multiple invocations for multi-stream testing. |

## Open Questions

- `[OPEN: Should `prompt-eval call` support testing multiple streams in one invocation, or is single-stream sufficient for the iteration loop?]`
- `[OPEN: Should `prompt-eval` support re-rendering prompts from scratch (bypassing events.jsonl) for cases where no save exists?]`

## Current State — What Exists

### `ev.py prompt` (ccya/ev/inspect.py)

Reads events.jsonl, extracts `*_prompt.rendered_system` and `*_prompt.rendered_user` for a given turn and stream. Prints them. No LLM call.

**Data flow:** events.jsonl → `find_turn()` → `extract_prompt()` → print

**Streams:** ruling, narrate, scene, state, storytell (aliases: rules, progress)

**Event structure for prompts:**
```
ruling_prompt: { rendered_system, rendered_user, output, parse_error, context_meta }
narrate_prompt: { rendered_system, rendered_user, output, context_meta }
extraction.{stream}: { rendered_system, rendered_user, output, context_meta }
```

### `ev.py eval run` (ccya/ev/eval.py)

Loads a YAML scenario, runs the full turn pipeline for each turn via `play_turn()`, runs checkers on all turns, generates a report.

**Data flow:** scenario.yaml → `play_turn()` (full 5-call pipeline) → events.jsonl → checkers → report

**Problem:** Each turn costs ~1 minute and 5 LLM calls. Cannot isolate a single prompt.

### `_render()` (ccya/engine/config.py:308)

Renders a Jinja2 template with a context dict. Used by all pipeline stages to build prompts.

### `llm_client.chat()` (ccya/llm_client.py:151)

Async OpenAI-compatible chat client. Takes `host`, `model`, `messages` (list of `{role, content}`), optional `temperature`, `max_tokens`, `timeout`. Returns `{response, done, usage}`.

### Checker infrastructure (ccya/ev/checkers/__init__.py)

`CheckerResult` dataclass with `checker_id`, `passed`, `score`, `detail`, `findings`, `ms`. Registered via `@register_checker(id, type, requires_fields, description)`. Run via `run_checkers()`.

### Problems with Current State

- **No fast prompt testing path.** Must run full pipeline to test a single prompt.
- **No LLM call from ev.py for prompt testing.** `ev.py prompt` dumps but does not call.
- **No prompt-specific checkers.** Existing checkers validate turn pipeline mechanics, not prompt output quality.
- **No golden output comparison.** Cannot assert "this prompt should produce X output."

## Proposed Solution

### Core Changes

**New file: `ccya/ev/prompt_eval.py`** (~150 lines)

Implements two subcommands:

#### `prompt-eval dump`

Reads events.jsonl, extracts rendered prompts for a single turn/stream, prints them.

```
ev.py prompt-eval dump saves/my-game/events.jsonl --turn 5 --stream narrate
```

Uses `extract_prompt()` from `ccya/ev/inspect.py` (same as `ev.py prompt`). No new logic.

#### `prompt-eval call`

Reads events.jsonl, extracts rendered prompts for a single turn/stream, sends to LLM, runs checks, prints results.

```
ev.py prompt-eval call scenarios/prompts/narrate-turn5.yaml
```

**Data flow:**
```
events.jsonl → find_turn() → extract_prompt() → LLM call → checkers → output
```

**Steps:**
1. Load events.jsonl from `--save-dir` or path argument.
2. Find the turn (`--turn` or from scenario YAML).
3. Extract rendered prompts for the stream (`extract_prompt()`).
4. Build messages: `[{"role": "system", "content": rendered_system}, {"role": "user", "content": rendered_user}]`.
5. Call `llm_client.chat()` with model/temp from scenario or flags.
6. Run configured checkers on the output.
7. Print results in `ev.py check` format.

**Scenario YAML format** (extends `ccya/ev/scenario.py`):

```yaml
id: narrate-turn5
description: Test narrate prompt at turn 5
save: saves/my-game/events.jsonl
turn: 5
stream: narrate
model: gemma-4-26b
temp: 0.7
checks:
  - golden_match: scenarios/prompts/golden/narrate-turn5.txt
  - prose_quality
  - directive_adherence
```

**New types in `ccya/ev/scenario.py`:**

```python
@dataclass
class PromptEvalScenario:
    id: str
    description: str
    save: str
    turn: int
    stream: str = "narrate"
    model: str | None = None
    temp: float | None = None
    checks: list[PromptCheck] = field(default_factory=list)

@dataclass
class PromptCheck:
    type: str  # "golden_match", "prose_quality", "directive_adherence", "extraction_format"
    path: str | None = None  # for golden_match: path to golden output file
    expected_directive: str | None = None  # for directive_adherence
```

**New checkers in `ccya/ev/checkers/`:**

| Checker | Type | Input | What it validates |
|---|---|---|---|
| `golden_match` | deterministic | LLM output + golden file | Exact match (line-by-line diff) |
| `prose_quality` | deterministic | LLM output | No repeated sentences, proper prose structure |
| `directive_adherence` | deterministic | LLM output + ruling directive | Output does not contradict the ruling directive |
| `extraction_format` | deterministic | LLM output | Valid JSON, required fields present |

**`golden_match` checker** (`ccya/ev/checkers/golden_match.py`):

```python
@register_checker("golden_match", "deterministic", requires_fields=[], description="Compare LLM output against a golden reference file")
def golden_match(events: list[dict[str, Any]], golden_path: str | None = None) -> CheckerResult:
```

Takes `golden_path` from the check config. Reads the golden file. Compares line-by-line. Reports diff on failure.

**`prose_quality` checker** (`ccya/ev/checkers/prose_quality.py`):

```python
@register_checker("prose_quality", "deterministic", requires_fields=[], description="Validate narrative prose quality heuristics")
def prose_quality(events: list[dict[str, Any]]) -> CheckerResult:
```

Checks:
- Output is non-empty prose (not JSON, not code)
- No repeated sentences (same sentence appears twice)
- No single-paragraph output (at least 2 paragraphs for multi-turn context)

**`directive_adherence` checker** (`ccya/ev/checkers/directive_adherence.py`):

```python
@register_checker("directive_adherence", "deterministic", requires_fields=[], description="Verify output does not contradict the ruling directive")
def directive_adherence(events: list[dict[str, Any]], expected_directive: str | None = None) -> CheckerResult:
```

Takes `expected_directive` from check config. Checks that the output does not contain text contradicting the directive (e.g., if directive is "fail", output should not describe the PC succeeding).

**`extraction_format` checker** (`ccya/ev/checkers/extraction_format.py`):

```python
@register_checker("extraction_format", "deterministic", requires_fields=[], description="Validate extraction output is valid JSON with required fields")
def extraction_format(events: list[dict[str, Any]], stream: str = "scene") -> CheckerResult:
```

Takes `stream` from check config (scene or state). Validates:
- Output is valid JSON
- Required fields present (scene: `npcs`, `location`; state: `inventory`, `conditions`)

### Integration with `ccya/ev/__init__.py`

Add routing for `prompt-eval` command:

```python
case "prompt-eval":
    from ccya.ev.prompt_eval import cmd_prompt_eval
    cmd_prompt_eval(flags, args)
```

Add to help text and command list.

### Alternatives Considered and Rejected

| Alternative | Why Rejected | Trade-off |
|---|---|---|
| Re-render prompts from scratch | Events.jsonl is source of truth. Re-rendering could differ due to context changes. | Simpler for cases with no save, but less accurate. |
| Single `prompt-eval` command with flags | `dump` and `call` have different UX. Separate subcommands are clearer. | Slightly more commands, but cleaner. |
| LLM-based prompt quality checkers | Deterministic checkers are fast and reproducible. LLM checkers add latency and variance. | Less nuanced quality assessment, but fast and consistent. |
| Extend `ev.py eval run` with `--prompt-only` flag | `eval run` is designed for full pipeline. Mixing concerns makes both harder to use. | Fewer commands, but conflates two distinct workflows. |

## Failure Modes and Risks

- **events.jsonl missing rendered prompts.** Older saves may not have `*_prompt` fields. `prompt-eval` should fail gracefully with a clear error.
- **LLM call fails.** Same error handling as `ev.py play` — report the error, continue to next check if multiple.
- **Golden file missing.** `golden_match` should fail with a clear error if the golden file does not exist.
- **Prompt too large for LLM.** `llm_client.chat()` does not trim prompts. Users may need to test with earlier turns or smaller saves.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| Nothing | — | No existing code is removed. |

## What Is Unchanged

- `ev.py play` — full turn pipeline, unchanged.
- `ev.py eval run` — full pipeline eval, unchanged.
- `ev.py prompt` — prompt dump, unchanged.
- `ev.py check` — checker infrastructure, unchanged.
- `ccya/engine/config.py` — `_render()`, `_build_jinja_env()`, unchanged.
- `ccya/llm_client.py` — `chat()`, `chat_stream()`, unchanged.
- `ccya/prompts/*.j2` — prompt templates, unchanged.
- `ccya/engine/turn.py` — turn pipeline, unchanged.
- `ccya/engine/extraction.py` — extraction pipeline, unchanged.
- `ccya/engine/narrate.py` — narrate pipeline, unchanged.
- `ccya/engine/ruling.py` — ruling pipeline, unchanged.
- `ccya/state/` — state management, unchanged.
- `ccya/packs/` — pack loading, unchanged.

## New Model Shapes

```python
@dataclass
class PromptEvalScenario:
    id: str
    description: str
    save: str
    turn: int
    stream: str = "narrate"
    model: str | None = None
    temp: float | None = None
    checks: list[PromptCheck] = field(default_factory=list)

@dataclass
class PromptCheck:
    type: str  # "golden_match", "prose_quality", "directive_adherence", "extraction_format"
    path: str | None = None
    expected_directive: str | None = None
```

## Context for Implementing LLMs

- `ccya/ev/__init__.py` — command routing, add `prompt-eval` case (~line 315)
- `ccya/ev/inspect.py` — `extract_prompt()` function, reused for prompt extraction
- `ccya/ev/scenario.py` — `Scenario` dataclass pattern, extend with `PromptEvalScenario`
- `ccya/ev/checkers/__init__.py` — `CheckerResult`, `@register_checker`, `run_checkers()`
- `ccya/llm_client.py` — `chat()` function signature for LLM calls
- `ccya/engine/config.py` — `_render()` signature (for reference, not used directly)
- `ccya/ev/events.py` — `find_turn()`, `load_events()` for event loading
- `ccya/ev/play.py` — `play_turn()` signature (for reference, not used)
