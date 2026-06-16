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
- Default path re-renders prompts using current templates and reconstructed context. events.jsonl forensics path available via `--from-events` flag.
- Same output format as `ev.py check` for consistency.
- Python 3.13+ only (ev.py requirement).
- No new configuration files. Scenarios live alongside existing YAML scenarios.

## Non-goals

- Full turn pipeline testing (already covered by `ev.py eval run`).
- Multi-turn prompt testing (single turn at a time).
- Prompt diffing or versioning.
- Web UI for prompt testing.
- Exact historical replay (use `--from-events` for that).

## Decision Table

| Decision | What | Why |
|---|---|---|
| Command name | `ev.py prompt-eval` | Follows `ev.py` naming convention. Distinguishes from `ev.py prompt` (dump only) and `ev.py eval` (full pipeline). |
| Subcommands | `dump` and `call` | `dump` renders and prints (no LLM). `call` renders + LLM + check. Separates inspection from evaluation. |
| Default data source | Re-render from reconstructed context + current template on disk | Tests what the template produces now. Edits to .j2 files are reflected immediately. |
| Forensics path | `--from-events` flag | Replays stored rendered_system/rendered_user exactly. Use for regression against known-bad turns. |
| Pre-turn state | Use event["state_snapshot"] (post-turn) directly | Delta reversal is not feasible — all delta types are lossy. Pre-turn reconstruction would require engine changes. Post-turn state is accurate for all fields except items mutated in the turn being tested, which is acceptable for the prompt iteration use case. |
| Golden fixtures | Committed save dirs under `ev/fixtures/` | No tooling needed. prompt-eval reads --save as a directory already. Golden output files live at `ev/fixtures/<name>/golden/`. |
| LLM call | `llm_client.chat()` | Same client the engine uses. No new LLM abstraction. |
| Output format | Same as `ev.py check` | Consistency. Users already know how to read checker results. Format: `## {checker_id}: {status} (score: {score})` with optional table of findings. |
| Scenario format | YAML, new `PromptEvalScenario` type | Reuses `yaml.safe_load()` + dataclass pattern from `ccya/ev/scenario.py`. New type, not an extension of `Scenario` (which has `pack` field for full pipeline). |
| New checkers | `golden_match`, `prose_quality`, `extraction_format` | Prompt-specific checks. Deterministic where possible. `directive_adherence` requires LLM judge; deferred to future design. |
| Stream selection | Single stream per run | Keeps scope simple. Users run multiple invocations for multi-stream testing. |
| Checker parameter passing | Each new checker reads its config from `PromptCheck.extra` dict at invocation time (not via `run_checkers` registry) | `run_checkers` only passes `events` and `save_dir` to checkers. Check-specific params go in `extra` dict. The plan phase will invoke checkers directly (not via `run_checkers`) so it can pass `extra` params. |
| `needs_state` for new checkers | `False` for all three new checkers | None of the new checkers need access to `load_current_state()`. They only need the LLM output and scenario config. |
| `needs_non_turn_events` for new checkers | `False` for all three new checkers | New checkers only need the single turn's event data. |

## Open Questions

- Delta reversibility: "No. All delta types are lossy. Pre-turn state reconstruction is not feasible without engine changes. `build_prompt_context()` uses post-turn `state_snapshot` instead."
- Which streams for v1: "Inventory only. Additional streams added as needed."

## Current State — What Exists

### `ev.py prompt` (ccya/ev/inspect.py)

**File:** `ccya/ev/inspect.py`

**Key function:** `extract_prompt(ev: dict[str, Any], stream: str) -> dict[str, str]` at line 17.

Takes a **single event dict** (not a list) and a stream name. Returns `{"system": ..., "user": ..., "output": ...}`.

**Command handler:** `cmd_prompt(ev, stream, field=None, include_system=False)` at line 106.

**Subcommand registration:** `case "prompt":` at `ccya/ev/__init__.py:138`.

**Data flow:** events.jsonl → `find_turn()` → single event dict → `extract_prompt(ev, stream)` → print

**Streams:** ruling, narrate, scene, state, storytell

**Aliases (defined at `ccya/ev/__init__.py:24`):** `rules` → `ruling`, `progress` → `storytell`

**Event structure for prompts (field names confirmed in source):**
```
ruling_prompt: { rendered_system, rendered_user, output, parse_error, context_meta }
narrate_prompt: { rendered_system, rendered_user, output, context_meta }
extraction.{stream}: { rendered_system, rendered_user, output, context_meta }
```

**Note on extraction events:** `extract_prompt()` accesses extraction events via `ev.get("extraction", {}).get(stream)` (inspect.py:23). The top-level key is `extraction`, not `extraction.{stream}`.

### `ev.py eval run` (ccya/ev/eval.py)

**File:** `ccya/ev/eval.py`

**Key function:** `cmd_eval_run(scenario_path, model=None, temp=None, checkers=None, report=None)` at line 62.

**Subcommand registration:** `case "eval":` at `ccya/ev/__init__.py:330`, subcommand `run` at line 339.

Uses `play_turn()` imported from `ccya.ev.play` (play.py:37), called at eval.py:80.

**Data flow:** scenario.yaml → `play_turn()` (full 5-call pipeline) → events.jsonl → checkers → report

**Problem:** Each turn costs ~1 minute and 5 LLM calls. Cannot isolate a single prompt.

### `_render()` (ccya/engine/config.py:308)

**File:** `ccya/engine/config.py`

**Signature:** `_render(env: Environment, template_name: str, ctx: dict[str, Any]) -> str` at line 308.

Takes a Jinja2 `Environment`, a template name (string matching a `.j2` filename in `ccya/prompts/`), and a context dict. Returns the rendered string.

**Note:** There is also a second `_render()` at `ccya/server/app.py:169` with a different signature (returns `HTMLResponse` for UI templates). Do not confuse the two.

### `llm_client.chat()` (ccya/llm_client.py:151)

**File:** `ccya/llm_client.py`

**Signature:** `async def chat(host: str, model: str, messages: list[dict[str, str]], *, temperature: float | None = None, max_tokens: int | None = None, timeout: float = 180.0, top_p: float | None = None, frequency_penalty: float | None = None, seed: int | None = None) -> dict[str, Any]` at line 151.

**Return value:** `{"response": content, "done": True, "usage": {"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...}}` (llm_client.py:195-203).

**Error handling:** Raises `LlmcTimeout` on timeout, `LlmcRateLimit` on 429, `LlmcApiError` on other HTTP errors.

**Mock mode:** Supported via `MOCK_MODE` env var (llm_client.py:25).

### Checker infrastructure (ccya/ev/checkers/__init__.py)

**File:** `ccya/ev/checkers/__init__.py`

**`CheckerResult` dataclass** at line 15:
```python
@dataclass
class CheckerResult:
    checker_id: str
    passed: bool | None
    score: float | None
    detail: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    ms: float = 0.0
```

**`@register_checker` decorator** at line 39:
```python
def register_checker(
    id: str,
    type: Literal["deterministic", "llm"],
    requires_fields: list[str],
    description: str,
    needs_non_turn_events: bool = False,
    needs_state: bool = False,
) -> Callable[..., Any]:
```

**Note:** Two extra optional parameters beyond what the design doc originally stated: `needs_non_turn_events` and `needs_state`. These control whether `run_checker` filters to turn events only and whether it passes `state` to the checker.

**`run_checker(checker_id, events, save_dir=None)`** at line 61. Invokes a single checker. Passes `events` (and optionally `state` if `needs_state=True`) to the checker function.

**`run_checkers(checker_ids, events, save_dir=None)`** at line 108. Batch wrapper around `run_checker`.

**`list_checkers(checker_type=None)`** at line 112. Returns `list[CheckerMeta]`.

**Checker invocation pattern:** Checkers are registered as module-level functions decorated with `@register_checker`. They are imported at the bottom of `__init__.py` (line 124) via `from . import gm_beat, inventory, ...`. Each checker function receives `(events, state)` or `(events)` depending on `needs_state`.

**Existing checkers (25 total):** gm_beat, inventory, conditions, threads, arc_goals, npc_presence, pacing, sanitizer, llm_checkers, phase_transition, recent_beats, phase_persistence, scene_age_tracking, climax_turn_counting, breather_enforcement, roll_band_consistency, thread_resolution_validity, new_thread_validity, compendium_lifecycle, beat_phase_validity, arc_resolution_validity, goal_update_validity.

### `ccya/ev/__init__.py` command routing

**File:** `ccya/ev/__init__.py`

**Pattern:** Python 3.10+ `match/case` statement at line 111 (`match cmd:`).

**Command registration pattern:** `case "commandname":` blocks throughout lines 112-355. Each imports its handler lazily and calls it.

**Flag parsing:** `_strip_flags(args)` at line 43. Returns `(flags: dict[str, str], positional: list[str])`. Boolean flags (e.g., `--all`, `--llm`) set `flags[name] = "true"`. Value flags (e.g., `--model foo`) set `flags[name] = "foo"`.

**Event loading:** Events are auto-loaded from `--save-dir/events.jsonl` or `saves/default/events.jsonl` for all commands except `play`, `init`, `status`, `help`, and `check --list`.

**`STREAM_ALIASES`** at line 24: `{"rules": "ruling", "ruling": "ruling", "progress": "storytell", "storytell": "storytell", "narrate": "narrate", "scene": "scene", "state": "state"}`.

**`_resolve_stream(name)`** at line 35: Resolves alias to canonical name. Exits with error for unknown streams.

### `ccya/ev/scenario.py` — Scenario dataclass

**File:** `ccya/ev/scenario.py`

**`Scenario` dataclass** at line 29:
```python
@dataclass
class Scenario:
    id: str
    pack: str
    description: str
    turns: list[ScenarioTurn]
    seed_overrides: dict[str, Any] = field(default_factory=dict)
```

**`ScenarioTurn`** at line 22: `input: str`, `expects: list[str]`, `asserts: list[TurnAssert]`.

**`TurnAssert`** at line 14: `stream: str`, `field: str`, `expected: str | None`, `min_amount: int | None`.

**`load_scenario(path: Path) -> Scenario`** at line 37. Uses `yaml.safe_load()`.

**`discover_scenarios(scenarios_dir="packs") -> list[Path]`** at line 88. Defaults to `packs/` at repo root (not `ccya/packs/`).

**Note:** `Scenario` is for the full pipeline (`ev.py eval run`). `PromptEvalScenario` is a new type for single-turn prompt testing. They share the YAML loading pattern but have different fields.

### `ccya/ev/events.py` — Event loading

**File:** `ccya/ev/events.py`

**`load_events(path: Path) -> list[dict[str, Any]]`** at line 17. Loads JSONL file.

**`find_turn(events: list[dict[str, Any]], turn: int) -> dict[str, Any] | None`** at line 39. Returns a single event dict for the given turn number.

**`STREAMS`** at line 14: `("ruling", "narrate", "scene", "state", "storytell")`.

**`filter_turn_events(events)`** at line 35. Filters to events where `kind == "turn"`.

**`extract_field(event, dotpath)`** at line 49. Dot-notation traversal on event dict.

**`load_current_state(save_dir: Path) -> dict[str, Any]`** at line 63. Delegates to `ccya.state.io.load_state`.

### `ev.py play` (ccya/ev/play.py)

**File:** `ccya/ev/play.py`

**Key function:** `play_turn(input_text, state, config, save_dir, ...)` at line 37.

**Command handler:** `cmd_play(flags, args)` at line 538.

**Subcommand registration:** `case "play":` at `ccya/ev/__init__.py:282`.

### `ev.py check` (ccya/ev/check.py)

**File:** `ccya/ev/check.py`

**Key function:** `cmd_check(events, turn=None, checker_ids=None, all_checkers=False, include_llm=False, save_dir=None, checker_model=None, list_only=False, verbose=False)` at line 31.

**Subcommand registration:** `case "check":` at `ccya/ev/__init__.py:285`.

**Output format:** `## {checker_id}: {status} (score: {score})` per checker. Optional table of findings. Domain breakdown summary.

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
ev.py prompt-eval dump saves/my-game --turn 5 --stream narrate
```

Uses `extract_prompt()` from `ccya/ev/inspect.py` (same as `ev.py prompt`). No new logic.

**Implementation note:** `dump` follows the same pattern as `ev.py prompt`: parse `--turn` and `--stream` flags, call `find_turn()`, call `extract_prompt()`, print.

#### `prompt-eval call`

Reads events.jsonl, extracts rendered prompts for a single turn/stream, sends to LLM, runs checks, prints results.

```
ev.py prompt-eval call scenarios/prompts/narrate-turn5.yaml
```

**Data flow:**

Default (re-render):
```
events.jsonl[turn N] → state_snapshot, narration, intent
state_snapshot + narration + intent → build_prompt_context(stream) → _render() → LLM → checkers → output
```

Forensics (`--from-events`):
```
events.jsonl[turn N] → rendered_system, rendered_user → LLM → checkers → output
```

**Steps:**
1. Load events via `load_events(save_dir)`, find turn N via `find_turn()`.
2. Load state from `event["state_snapshot"]`. Note: this is post-turn state. Inventory and conditions reflect the end of turn N, not the start. This is a known limitation — see Failure Modes.
3. Extract `narration` from `event["narrate"]["output"]` and `intent` from `event["ruling"]["intent"]`.
4. Assemble context dict matching the engine's exact shape for the requested stream.

#### `build_prompt_context(save_dir, turn_no, stream)` — new function in `prompt_eval.py`

Reconstructs the context dict the engine would have passed to `_render()` for the given stream and turn. This is the core of the re-render path.

Steps:
1. Load events via `load_events(save_dir)`, find turn N via `find_turn()`.
2. Load state from `event["state_snapshot"]`. Note: this is post-turn state. Inventory and conditions reflect the end of turn N, not the start. This is a known limitation — see Failure Modes.
3. Extract `narration` from `event["narrate"]["output"]` and `intent` from `event["ruling"]["intent"]`.
4. Assemble context dict matching the engine's exact shape for the requested stream.

For the inventory stream, the context dict is:
```python
{
    "narration": str,        # from event["narrate"]["output"]
    "conditions": list,      # from state_snapshot["pc"]["conditions"] (post-turn)
    "inventory": list,       # from state_snapshot["inventory"] (post-turn)
    "intent": dict | None,   # from event["ruling"]["intent"]
    "turn_no": int,
}
```

**Parity contract:** this dict must be identical in shape to what `extraction.py` passes to `_render()` for each stream. If the engine's context shape changes, `build_prompt_context()` must be updated. Divergence should fail loudly.

**Scenario YAML format** (new `PromptEvalScenario` type, not an extension of `Scenario`):

```yaml
id: narrate-turn5
description: Test narrate prompt at turn 5
save: saves/my-game
turn: 5
stream: narrate
model: gemma-4-26b
temp: 0.7
checks:
  - golden_match: ev/fixtures/narrate-turn5/golden/output.txt
  - prose_quality
```

**YAML parsing note:** The `checks` list supports two formats:
- Shorthand: `"prose_quality"` (string, maps to checker with no extra params)
- Full: `golden_match: path/to/golden.txt` (mapping with checker type as key and config as value)

The plan phase will define the exact YAML parsing logic.

**New types in `ccya/ev/scenario.py`:**

```python
@dataclass
class PromptEvalScenario:
    id: str
    description: str
    save: str
    turn: int
    stream: str = "inventory"
    model: str | None = None
    temp: float | None = None
    checks: list[PromptCheck] = field(default_factory=list)

@dataclass
class PromptCheck:
    type: str  # "golden_match", "prose_quality", "extraction_format"
    extra: dict = field(default_factory=dict)
```

**Note on `PromptEvalScenario.save`:** This is a save directory (consistent with every other `ev.py` command). The plan phase will add `load_prompt_scenario()` to `ccya/ev/scenario.py`.

**New checkers in `ccya/ev/checkers/`:**

| Checker | Type | Input | What it validates |
|---|---|---|---|
| `golden_match` | deterministic | LLM output + golden file | For extraction streams: JSON field-level comparison against golden file. For prose streams: line-by-line diff. Branches on stream type. |
| `prose_quality` | deterministic | LLM output | No repeated sentences, proper prose structure |
| `extraction_format` | deterministic | LLM output | Valid JSON, required fields present |

**`golden_match` checker** (`ccya/ev/checkers/golden_match.py`):

```python
@register_checker("golden_match", "deterministic", requires_fields=[], description="Compare LLM output against a golden reference file", needs_non_turn_events=False, needs_state=False)
def golden_match(events: list[dict[str, Any]], golden_path: str | None = None) -> CheckerResult:
```

Takes `golden_path` from `PromptCheck.extra`. Reads the golden file. For extraction streams: parses both outputs as JSON and does field-level comparison. For prose streams: line-by-line diff. Reports diff on failure.

**Implementation note:** This checker will NOT be invoked via `run_checkers()` (which doesn't support passing `golden_path`). Instead, `prompt_eval.py` will invoke it directly: `golden_match(events, golden_path=scenario.checks[0].extra["golden_path"])`.

**`prose_quality` checker** (`ccya/ev/checkers/prose_quality.py`):

```python
@register_checker("prose_quality", "deterministic", requires_fields=[], description="Validate narrative prose quality heuristics", needs_non_turn_events=False, needs_state=False)
def prose_quality(events: list[dict[str, Any]]) -> CheckerResult:
```

Checks:
- Output is non-empty prose (not JSON, not code)
- No repeated sentences (same sentence appears twice)
- No single-paragraph output (at least 2 paragraphs for multi-turn context)

**`extraction_format` checker** (`ccya/ev/checkers/extraction_format.py`):

```python
@register_checker("extraction_format", "deterministic", requires_fields=[], description="Validate extraction output is valid JSON with required fields", needs_non_turn_events=False, needs_state=False)
def extraction_format(events: list[dict[str, Any]], stream: str = "scene") -> CheckerResult:
```

Takes `stream` from `PromptCheck.extra` (scene or state). Validates:
- Output is valid JSON
- Required fields present (scene: `npcs`, `location`; state: `inventory`, `conditions`)

**Implementation note:** Will be invoked directly by `prompt_eval.py`, not via `run_checkers()`, to pass `stream` from `extra`.

### Integration with `ccya/ev/__init__.py`

Add routing for `prompt-eval` command:

```python
case "prompt-eval":
    from ccya.ev.prompt_eval import cmd_prompt_eval
    cmd_prompt_eval(flags, args)
```

Add to help text and command list (at `ccya/ev/__init__.py:78` and `:114`).

**Placement:** Insert before `case "prompt":` (line 138) to keep alphabetical-ish ordering.

### Alternatives Considered and Rejected

| Alternative | Why Rejected | Trade-off |
|---|---|---|
| Re-render prompts from scratch | Now the default path. See Decision Table. | Re-render tests current template; forensics tests exact historical replay. Both supported. |
| Single `prompt-eval` command with flags | `dump` and `call` have different UX. Separate subcommands are clearer. | Slightly more commands, but cleaner. |
| LLM-based prompt quality checkers | Deterministic checkers are fast and reproducible. LLM checkers add latency and variance. | Less nuanced quality assessment, but fast and consistent. |
| Extend `ev.py eval run` with `--prompt-only` flag | `eval run` is designed for full pipeline. Mixing concerns makes both harder to use. | Fewer commands, but conflates two distinct workflows. |
| Use `run_checkers()` for all checker invocation | `run_checkers()` doesn't support passing check-specific parameters (golden_path, expected_directive, stream). | Simpler integration, but requires modifying `run_checkers` signature or adding a new registry mechanism. Direct invocation is simpler for this scope. |

## Failure Modes and Risks

- **events.jsonl missing rendered prompts.** Older saves may not have `*_prompt` fields. `prompt-eval` should fail gracefully with a clear error.
- **LLM call fails.** Same error handling as `ev.py play` — report the error, continue to next check if multiple.
- **Golden file missing.** `golden_match` should fail with a clear error if the golden file does not exist.
- **Prompt too large for LLM.** `llm_client.chat()` does not trim prompts. Users may need to test with earlier turns or smaller saves.
- **State snapshot is post-turn.** `build_prompt_context()` uses `event["state_snapshot"]`, which reflects state after turn N completed. For turns where inventory or conditions changed, the re-rendered prompt will see the post-delta state rather than what the engine saw. This is acceptable for iterating on prompt logic but means re-rendered output is not bit-for-bit identical to the original engine call. Use `--from-events` when exact historical replay is required.

## Future Work

- **Additional stream support** — `build_prompt_context()` currently implements inventory only. Other extraction streams (scene, state, storytell) follow the same pattern and can be added as needed.
- **LLM judge checker** — `directive_adherence` and rubric-based output quality assessment require an LLM judge. Deferred pending a separate design for structured rubric evaluation.
- **Fixture generation tooling** — Golden saves are currently committed manually. A future `ev.py fixture record` or similar command could automate capturing a controlled game run as a fixture.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| Nothing | — | No existing code is removed. |

## What Is Unchanged

- `ev.py play` (`ccya/ev/play.py`) — full turn pipeline, unchanged.
- `ev.py eval run` (`ccya/ev/eval.py`) — full pipeline eval, unchanged.
- `ev.py prompt` (`ccya/ev/inspect.py`) — prompt dump, unchanged.
- `ev.py check` (`ccya/ev/check.py`) — checker infrastructure, unchanged.
- `ccya/engine/config.py` — `_render()`, `_build_jinja_env()`, unchanged.
- `ccya/llm_client.py` — `chat()`, `chat_stream()`, unchanged.
- `ccya/prompts/*.j2` — prompt templates, unchanged.
- `ccya/engine/turn.py` — turn pipeline, unchanged.
- `ccya/engine/extraction.py` — extraction pipeline, unchanged.
- `ccya/engine/narrate.py` — narrate pipeline, unchanged.
- `ccya/engine/ruling.py` — ruling pipeline, unchanged.
- `ccya/state/` — state management, unchanged.
- `ccya/state/delta.py` — delta application logic, unchanged. Not used by `build_prompt_context()`.
- `ccya/ev/events.py` — `find_turn()`, `load_events()`, unchanged.
- `ccya/ev/scenario.py` — `Scenario` dataclass, `load_scenario()`, unchanged (new types added alongside).
- `ccya/ev/checkers/__init__.py` — `CheckerResult`, `@register_checker`, `run_checkers()`, unchanged (new checkers added alongside).

## New Model Shapes

```python
@dataclass
class PromptEvalScenario:
    id: str
    description: str
    save: str
    turn: int
    stream: str = "inventory"
    model: str | None = None
    temp: float | None = None
    checks: list[PromptCheck] = field(default_factory=list)

@dataclass
class PromptCheck:
    type: str  # "golden_match", "prose_quality", "extraction_format"
    extra: dict = field(default_factory=dict)
```

## Context for Implementing LLMs

- `ccya/ev/__init__.py` — command routing (match/case at line 111), add `prompt-eval` case. Help text at line 78. (~359 lines total)
- `ccya/ev/inspect.py` — `extract_prompt()` function at line 17, reused for prompt extraction. `cmd_prompt()` at line 106 for reference on dump UX. (~130 lines total)
- `ccya/ev/scenario.py` — `Scenario` dataclass pattern at line 29, extend with `PromptEvalScenario` and `PromptCheck`. `load_scenario()` at line 37 for reference on YAML loading. (~103 lines total)
- `ccya/ev/checkers/__init__.py` — `CheckerResult` at line 15, `@register_checker` at line 39 (note: includes `needs_non_turn_events` and `needs_state` params), `run_checkers()` at line 108. (~124 lines total)
- `ccya/llm_client.py` — `chat()` at line 151 for LLM calls. Return type is `dict[str, Any]` with keys `response`, `done`, `usage`. (~228 lines total)
- `ccya/engine/config.py` — `_render()` at line 308 (for reference, not used directly by prompt-eval). Signature: `_render(env: Environment, template_name: str, ctx: dict[str, Any]) -> str`. (~430 lines total)
- `ccya/ev/events.py` — `find_turn()` at line 39, `load_events()` at line 17 for event loading. `STREAMS` tuple at line 14. (~431 lines total)
- `ccya/ev/play.py` — `play_turn()` at line 37 (for reference, not used by prompt-eval). (~538+ lines total)
- `ccya/ev/check.py` — `cmd_check()` at line 31 (for reference on output format). (~169 lines total)
- `ccya/state/delta.py` — delta application logic; not used by `build_prompt_context()`, which uses `event["state_snapshot"]` directly.
