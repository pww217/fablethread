# Plan: `ev.py prompt-eval` — fast prompt testing CLI

## Purpose

Add a `prompt-eval` subcommand to `ev.py` that renders individual pipeline prompts with live data from a save, optionally calls the LLM, and evaluates the output — enabling fast iteration on prompt templates without running the full turn pipeline.

## Problem Statement

Prompt templates (`ccya/prompts/*.j2`) are currently tested only through the full turn pipeline (`ev.py play`), which is slow (~1 min/turn, 5 LLM calls) and hard to isolate. There is no fast path to render a single prompt with live data, send it to the LLM, and evaluate the output. The existing `ev.py prompt` dumps rendered prompts from events.jsonl but does not call the LLM. The existing `ev.py eval run` runs the full pipeline. Neither supports the fast prompt-test loop.

## Constraints

- Minimal new code. One new command module (`ccya/ev/prompt_eval.py`), maybe 3-4 new checkers.
- Reuse existing infrastructure: `_render()`, `llm_client.chat()`, `CheckerResult`, checker registry.
- Default path re-renders prompts using current templates and reconstructed context. events.jsonl forensics path available via `--from-events` flag.
- Same output format as `ev.py check` for consistency.
- Python 3.13+ only.
- No new configuration files. Scenarios live alongside existing YAML scenarios.

## Non-goals

- Full turn pipeline testing (already covered by `ev.py eval run`).
- Multi-turn prompt testing (single turn at a time).
- Prompt diffing or versioning.
- Web UI for prompt testing.
- Exact historical replay (use `--from-events` for that).

## Solution

Add `ev.py prompt-eval` with two subcommands: `dump` (renders and prints prompts, no LLM) and `call` (renders + LLM + check). The default path re-renders prompts using current templates and post-turn `state_snapshot` as context. The `--from-events` flag replays stored rendered prompts for regression testing. Three new checkers (`golden_match`, `prose_quality`, `extraction_format`) validate LLM output.

## Firm decisions

1. `dump` and `call` are separate subcommands, not flags on one command.
2. Re-render is the default path. `--from-events` is the forensics flag.
3. `build_prompt_context()` uses `event["state_snapshot"]` (post-turn) directly. Delta reversal is not feasible.
4. `PromptCheck` uses `extra: dict` for all checker-specific parameters. No nullable fields.
5. New checkers are invoked directly by `prompt_eval.py`, not via `run_checkers()`, to pass `extra` params.
6. `PromptEvalScenario.save` is a save directory (consistent with every other `ev.py` command).
7. `build_prompt_context()` implements inventory stream only in v1.
8. `directive_adherence` is deferred to a future LLM judge design.

## Risks, Ambiguities, and Blockers

- **Post-turn state limitation:** Re-rendered prompts will see post-delta inventory/conditions for the turn being tested. This is acceptable for prompt iteration but means output is not bit-for-bit identical to the original engine call. Users should use `--from-events` for exact replay.
- **Context shape parity:** `build_prompt_context()` must produce a dict identical in shape to what `extraction.py` passes to `_render()`. If the engine's context shape changes, `build_prompt_context()` must be updated. No automated parity check exists yet.
- **`--from-events` missing rendered prompts:** Older saves may not have `*_prompt` fields. The command should fail gracefully with a clear error.

## Status

`open`

## Phases

4 phases: implement `prompt_eval.py` module with `dump` and `call` subcommands and inline checkers, integration into `ev.py` command routing, and documentation updates.

---

## Implementation — Phase 1: `PromptEvalScenario`, `PromptCheck`, and `load_prompt_scenario()`

### Context files to load

- `ccya/ev/scenario.py` (103 lines) — existing `Scenario` dataclass and `load_scenario()` for reference
- `ccya/ev/events.py` (431 lines) — `find_turn()`, `load_events()`, `STREAMS`

### Detailed steps

#### Step 1.1 — Add `PromptEvalScenario` and `PromptCheck` dataclasses

**File:** `ccya/ev/scenario.py`

**What:** Add two new dataclasses after the existing `Scenario` class (after line 34):

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

**Why:** New scenario type for single-turn prompt testing. Different fields from `Scenario` (no `pack`, no `turns`). Uses `extra: dict` for checker params.

**Validation:** `rg -n "class PromptEvalScenario" ccya/ev/scenario.py` returns the new class. `rg -n "class PromptCheck" ccya/ev/scenario.py` returns the new class.

#### Step 1.2 — Add `load_prompt_scenario()` function

**File:** `ccya/ev/scenario.py`

**What:** Add a new function after `load_scenario()` (after line 85):

```python
def load_prompt_scenario(path: Path) -> PromptEvalScenario:
    text = path.read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected YAML mapping, got {type(data).__name__}")

    _require(data, "id", str, path)
    _require(data, "description", str, path)
    _require(data, "save", str, path)
    _require(data, "turn", int, path)

    stream = data.get("stream", "inventory")
    if not isinstance(stream, str):
        raise ValueError(f"{path}: field 'stream' must be str, got {type(data['stream']).__name__}")

    model = data.get("model")
    if model is not None and not isinstance(model, str):
        raise ValueError(f"{path}: field 'model' must be str or null")

    temp = data.get("temp")
    if temp is not None and not isinstance(temp, (int, float)):
        raise ValueError(f"{path}: field 'temp' must be float or null")

    checks_raw = data.get("checks", [])
    if not isinstance(checks_raw, list):
        raise ValueError(f"{path}: field 'checks' must be a list")

    checks = []
    for check_item in checks_raw:
        if isinstance(check_item, str):
            checks.append(PromptCheck(type=check_item))
        elif isinstance(check_item, dict):
            if len(check_item) != 1:
                raise ValueError(f"{path}: each check mapping must have exactly one key")
            checker_type = next(iter(check_item))
            checker_value = check_item[checker_type]
            extra = {}
            if checker_type == "golden_match":
                if not isinstance(checker_value, str):
                    raise ValueError(f"{path}: golden_match value must be a string path")
                extra["golden_path"] = checker_value
            elif checker_type == "extraction_format":
                if isinstance(checker_value, dict):
                    extra["stream"] = checker_value.get("stream", "scene")
                elif isinstance(checker_value, str):
                    extra["stream"] = checker_value
            checks.append(PromptCheck(type=checker_type, extra=extra))
        else:
            raise ValueError(f"{path}: check must be a string or mapping, got {type(check_item).__name__}")

    return PromptEvalScenario(
        id=data["id"],
        description=data["description"],
        save=data["save"],
        turn=data["turn"],
        stream=stream,
        model=model,
        temp=float(temp) if temp is not None else None,
        checks=checks,
    )
```

**Why:** YAML parsing for the new scenario type. Reuses `_require()` helper. Handles both shorthand (`"prose_quality"`) and full (`golden_match: path/to/golden.txt`) check formats.

**Validation:** `rg -n "def load_prompt_scenario" ccya/ev/scenario.py` returns the new function.

---

## Implementation — Phase 2: `build_prompt_context()` and `prompt_eval.py` module

### Context files to load

- `ccya/ev/inspect.py` (130 lines) — `extract_prompt()`, `cmd_prompt()` for reference on dump UX
- `ccya/ev/events.py` (431 lines) — `find_turn()`, `load_events()`, `STREAMS`
- `ccya/engine/extraction.py` (810 lines) — `_extract_state_messages()` at line 269, `_extract_scene_messages()` at line 239, `_storytell_messages()` at line 299 for context shape parity
- `ccya/engine/config.py` (430 lines) — `_render()` at line 308, `_build_jinja_env()` for reference
- `ccya/llm_client.py` (228 lines) — `chat()` at line 151

### Detailed steps

#### Step 2.1 — Create `ccya/ev/prompt_eval.py`

**File:** `ccya/ev/prompt_eval.py` (new file, ~200 lines)

**What:** Create the new module with two subcommand handlers and `build_prompt_context()`:

```python
"""prompt_eval.py — Fast prompt testing for CCYA.

Subcommands:
  dump  — renders and prints prompts (no LLM)
  call  — renders + LLM + check
"""

from __future__ import annotations

import asyncio
import difflib
import json
import logging
import sys
from pathlib import Path
from typing import Any

from jinja2 import Environment

from ccya.engine.config import EngineConfig, _build_jinja_env, _render
from ccya.ev.checkers import CheckerResult
from ccya.ev.events import find_turn, load_events
from ccya.ev.scenario import PromptEvalScenario, load_prompt_scenario

PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")

_log = logging.getLogger(__name__)


def build_prompt_context(
    events: list[dict[str, Any]],
    turn_no: int,
    stream: str,
) -> dict[str, Any]:
    """Build the context dict for rendering a prompt for the given stream and turn.

    Uses event["state_snapshot"] (post-turn state). This is a known limitation:
    inventory and conditions reflect the end of turn N, not the start.

    Parity contract: the returned dict must be identical in shape to what
    extraction.py passes to _render() for each stream.
    """
    turn_ev = find_turn(events, turn_no)
    if turn_ev is None:
        print(f"Error: turn {turn_no} not found", file=sys.stderr)
        sys.exit(1)

    state_snapshot = turn_ev.get("state_snapshot") or {}
    narration = (turn_ev.get("narrate") or {}).get("output", "")
    intent = (turn_ev.get("ruling") or {}).get("intent")

    if stream == "inventory":
        pc = state_snapshot.get("pc") or {}
        return {
            "narration": narration,
            "conditions": list(pc.get("conditions") or []),
            "inventory": state_snapshot.get("inventory") or [],
            "intent": intent if isinstance(intent, dict) else None,
            "turn_no": turn_no,
        }

    # Placeholder for future streams — fail loudly if used
    print(f"Error: stream '{stream}' not yet implemented in build_prompt_context()", file=sys.stderr)
    sys.exit(1)


def _get_template_name(stream: str) -> str:
    """Map stream name to Jinja2 template filename."""
    if stream == "narrate":
        return "narrate_user.j2"
    elif stream == "ruling":
        return "ruling_user.j2"
    elif stream == "storytell":
        return "storytell_user.j2"
    else:
        return f"extract_{stream}_user.j2"


def _get_system_template_name(stream: str) -> str:
    """Map stream name to Jinja2 system template filename."""
    if stream == "narrate":
        return "narrate_system.j2"
    elif stream == "ruling":
        return "ruling_system.j2"
    elif stream == "storytell":
        return "storytell_system.j2"
    else:
        return f"extract_{stream}_system.j2"


def cmd_prompt_eval_dump(
    events: list[dict[str, Any]],
    turn: int,
    stream: str,
    from_events: bool = False,
) -> None:
    """Dump rendered prompts for a single turn/stream."""
    turn_ev = find_turn(events, turn)
    if turn_ev is None:
        print(f"Error: turn {turn} not found", file=sys.stderr)
        sys.exit(1)

    if from_events:
        # Forensics path: use stored rendered prompts
        p = _extract_prompt_from_event(turn_ev, stream)
        print(f"=== Turn {turn} — {stream} (from events) ===\n")
        print("--- SYSTEM ---")
        print(p["system"])
        print()
        print("--- USER ---")
        print(p["user"])
        print()
        print("--- OUTPUT ---")
        print(p["output"])
    else:
        # Re-render path: use current templates
        env = _build_jinja_env(PROMPTS_DIR)
        ctx = build_prompt_context(events, turn, stream)
        system_template = _get_system_template_name(stream)
        user_template = _get_template_name(stream)
        rendered_system = _render(env, system_template, ctx)
        rendered_user = _render(env, user_template, ctx)
        print(f"=== Turn {turn} — {stream} (re-rendered) ===\n")
        print("--- SYSTEM ---")
        print(rendered_system)
        print()
        print("--- USER ---")
        print(rendered_user)


def _extract_prompt_from_event(ev: dict[str, Any], stream: str) -> dict[str, str]:
    """Extract stored rendered prompts from an event dict.

    Mirrors extract_prompt() from inspect.py but reads from stored
    rendered_system/rendered_user fields.
    """
    if stream == "ruling":
        blob = ev.get("ruling_prompt") or {}
    elif stream == "narrate":
        blob = ev.get("narrate_prompt") or {}
    else:
        blob = (ev.get("extraction") or {}).get(stream) or {}

    return {
        "system": blob.get("rendered_system") or "",
        "user": blob.get("rendered_user") or "",
        "output": blob.get("output") or "",
    }


def cmd_prompt_eval_call(
    events: list[dict[str, Any]],
    scenario: PromptEvalScenario,
    from_events: bool = False,
) -> None:
    """Render prompts, call LLM, run checks, print results."""
    turn_ev = find_turn(events, scenario.turn)
    if turn_ev is None:
        print(f"Error: turn {scenario.turn} not found", file=sys.stderr)
        sys.exit(1)

    # Render prompts
    if from_events:
        p = _extract_prompt_from_event(turn_ev, scenario.stream)
        rendered_system = p["system"]
        rendered_user = p["user"]
    else:
        env = _build_jinja_env(PROMPTS_DIR)
        ctx = build_prompt_context(events, scenario.turn, scenario.stream)
        system_template = _get_system_template_name(scenario.stream)
        user_template = _get_template_name(scenario.stream)
        rendered_system = _render(env, system_template, ctx)
        rendered_user = _render(env, user_template, ctx)

    # Call LLM
    config = EngineConfig()
    model = scenario.model or config.model
    temp = scenario.temp if scenario.temp is not None else 0.7

    from ccya.llm_client import chat as llm_chat

    try:
        result = asyncio.run(llm_chat(
            host=config.host,
            model=model,
            messages=[
                {"role": "system", "content": rendered_system},
                {"role": "user", "content": rendered_user},
            ],
            temperature=temp,
        ))
        output = result.get("response", "")
    except Exception as exc:
        print(f"Error: LLM call failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Run checks
    for check in scenario.checks:
        if check.type == "golden_match":
            result = _run_golden_match(output, check.extra.get("golden_path"))
        elif check.type == "prose_quality":
            result = _run_prose_quality(output)
        elif check.type == "extraction_format":
            result = _run_extraction_format(output, check.extra.get("stream", "scene"))
        else:
            print(f"Warning: unknown checker '{check.type}'", file=sys.stderr)
            continue

        status = "PASS" if result.passed else "FAIL" if result.passed is False else "SKIP"
        score_str = f"{result.score:.2f}" if result.score is not None else "N/A"
        print(f"## {result.checker_id}: {status} (score: {score_str})")
        if result.detail:
            print(f"  {result.detail}")
        for finding in result.findings:
            if "diff" in finding:
                print("  Diff:")
                for line in finding["diff"].splitlines():
                    print(f"    {line}")

    return


def _run_golden_match(output: str, golden_path: str | None) -> CheckerResult:
    """Compare output against a golden reference file."""
    if not golden_path:
        return CheckerResult(
            checker_id="golden_match", passed=None, score=None,
            detail="golden_path not provided",
        )

    golden_file = Path(golden_path)
    if not golden_file.exists():
        return CheckerResult(
            checker_id="golden_match", passed=False, score=0.0,
            detail=f"golden file not found: {golden_path}",
        )

    golden_text = golden_file.read_text().strip()

    if output.strip() == golden_text:
        return CheckerResult(
            checker_id="golden_match", passed=True, score=1.0,
            detail="exact match",
        )

    diff = list(difflib.unified_diff(
        golden_text.splitlines(keepends=True),
        output.strip().splitlines(keepends=True),
        fromfile="golden",
        tofile="output",
        lineterm="",
    ))

    return CheckerResult(
        checker_id="golden_match", passed=False, score=0.0,
        detail="output differs from golden",
        findings=[{"diff": "".join(diff)}],
    )


def _run_prose_quality(output: str) -> CheckerResult:
    """Validate narrative prose quality heuristics."""
    if not output.strip():
        return CheckerResult(
            checker_id="prose_quality", passed=False, score=0.0,
            detail="empty output",
        )

    sentences = [s.strip() for s in output.replace("\n", " ").split(".") if s.strip()]
    if len(sentences) != len(set(sentences)):
        return CheckerResult(
            checker_id="prose_quality", passed=False, score=0.0,
            detail="repeated sentences detected",
        )

    paragraphs = [p.strip() for p in output.split("\n\n") if p.strip()]
    if len(paragraphs) < 2 and len(sentences) > 3:
        return CheckerResult(
            checker_id="prose_quality", passed=False, score=0.0,
            detail="single paragraph with multiple sentences",
        )

    return CheckerResult(
        checker_id="prose_quality", passed=True, score=1.0,
        detail="prose quality OK",
    )


def _run_extraction_format(output: str, stream: str) -> CheckerResult:
    """Validate extraction output is valid JSON with required fields."""
    try:
        parsed = json.loads(output)
    except (json.JSONDecodeError, ValueError):
        return CheckerResult(
            checker_id="extraction_format", passed=False, score=0.0,
            detail="not valid JSON",
        )

    if not isinstance(parsed, dict):
        return CheckerResult(
            checker_id="extraction_format", passed=False, score=0.0,
            detail="output is not a JSON object",
        )

    required_fields = {
        "scene": ["npcs", "location"],
        "state": ["inventory", "conditions"],
    }.get(stream, [])

    missing = [f for f in required_fields if f not in parsed]
    if missing:
        return CheckerResult(
            checker_id="extraction_format", passed=False, score=0.0,
            detail=f"missing fields: {', '.join(missing)}",
        )

    return CheckerResult(
        checker_id="extraction_format", passed=True, score=1.0,
        detail="extraction format OK",
    )


def cmd_prompt_eval(flags: dict[str, str], args: list[str]) -> None:
    """Main entry point for ev.py prompt-eval command."""
    if len(args) < 2:
        print("Usage: ev.py prompt-eval <dump|call> [args...]", file=sys.stderr)
        print("\nSubcommands:")
        print("  dump <save-dir> --turn N --stream STREAM [--from-events]")
        print("  call <scenario.yaml> [--from-events]")
        sys.exit(1)

    subcmd = args[0]
    from_events = "from-events" in flags

    if subcmd == "dump":
        if len(args) < 2:
            print("Usage: ev.py prompt-eval dump <save-dir> --turn N --stream STREAM", file=sys.stderr)
            sys.exit(1)
        save_dir = args[1]
        turn = int(flags["turn"]) if "turn" in flags else None
        stream = flags.get("stream", "inventory")

        if turn is None:
            print("Error: --turn is required for dump", file=sys.stderr)
            sys.exit(1)

        events = load_events(Path(save_dir) / "events.jsonl")
        cmd_prompt_eval_dump(events, turn, stream, from_events=from_events)

    elif subcmd == "call":
        if len(args) < 2:
            print("Usage: ev.py prompt-eval call <scenario.yaml> [--from-events]", file=sys.stderr)
            sys.exit(1)
        scenario_path = Path(args[1])
        scenario = load_prompt_scenario(scenario_path)

        events = load_events(Path(scenario.save) / "events.jsonl")
        cmd_prompt_eval_call(events, scenario, from_events=from_events)

    else:
        print(f"Error: unknown subcommand '{subcmd}'", file=sys.stderr)
        sys.exit(1)
```

**Why:** Core module implementing both subcommands. `build_prompt_context()` handles inventory stream. `cmd_prompt_eval_dump` handles the dump subcommand. `cmd_prompt_eval_call` handles the call subcommand with LLM invocation and checker execution. Three inline checker functions (`_run_golden_match`, `_run_prose_quality`, `_run_extraction_format`) take `output: str` directly and return `CheckerResult` for direct invocation with `extra` params.

**Validation:** `rg -n "def build_prompt_context" ccya/ev/prompt_eval.py` returns the function. `rg -n "def cmd_prompt_eval_dump" ccya/ev/prompt_eval.py` returns the function. `rg -n "def cmd_prompt_eval_call" ccya/ev/prompt_eval.py` returns the function. `rg -n "def cmd_prompt_eval" ccya/ev/prompt_eval.py` returns the function.

---

## Implementation — Phase 3: Integration into `ev.py` command routing

### Context files to load

- `ccya/ev/__init__.py` (359 lines) — command routing, help text, flag parsing

### Detailed steps

#### Step 3.1 — Add `prompt-eval` command routing

**File:** `ccya/ev/__init__.py`

**What:** Add routing for `prompt-eval` command.

1. Add `prompt-eval` to help text at line 78 (after `prompt-sizes`, before closing paren):
   Change: `...prompt-sizes"`
   To: `...prompt-sizes, prompt-eval"`

2. Add `prompt-eval` to help text at line 114 (same pattern):
   Change: `...prompt-sizes"`
   To: `...prompt-sizes, prompt-eval"`

3. Add the command case before `case "prompt":` (line 138) to keep alphabetical-ish ordering:

```python
        case "prompt-eval":
            from ccya.ev.prompt_eval import cmd_prompt_eval
            cmd_prompt_eval(flags, args)
```

**Why:** Wires the new module into the ev.py CLI. Placement before `prompt` keeps alphabetical-ish ordering.

**Validation:** `rg -n "prompt-eval" ccya/ev/__init__.py` returns the new case and help text entries.

---

## Implementation — Phase 4: Documentation updates

### Context files to load

- `docs/architecture/OVERVIEW.md` — pipeline overview, data models
- `docs/repomap.md` — module boundaries, public APIs
- `AGENTS.md` — repo conventions

### Detailed steps

#### Step 4.1 — Update `docs/architecture/OVERVIEW.md`

**What:** Add a section documenting the `prompt-eval` command:
- Purpose: fast prompt testing without full turn pipeline
- Two subcommands: `dump` (render only), `call` (render + LLM + check)
- Data flow: events.jsonl → `build_prompt_context()` → Jinja2 templates → LLM → checkers
- Known limitation: `build_prompt_context()` uses post-turn `state_snapshot`

**Validation:** `rg -n "prompt-eval" docs/architecture/OVERVIEW.md` returns the new section.

#### Step 4.2 — Update `docs/repomap.md`

**What:** Add `ccya/ev/prompt_eval.py` to the module map:
- Module: `ccya/ev/prompt_eval.py` (~200 lines)
- Public API: `cmd_prompt_eval(flags, args)`, `build_prompt_context(events, turn, stream)`
- Depends on: `ccya/engine/config._build_jinja_env()`, `ccya/engine.config._render()`, `ccya/ev/events`, `ccya/ev/scenario`, `ccya/llm_client.chat`

**Validation:** `rg -n "prompt_eval" docs/repomap.md` returns the new entry.

#### Step 4.3 — Update `AGENTS.md`

**What:** Add `prompt-eval` to the EV section in AGENTS.md:
- `ev.py prompt-eval dump <save-dir> --turn N --stream STREAM [--from-events]` — render prompts
- `ev.py prompt-eval call <scenario.yaml> [--from-events]` — render + LLM + check

**Validation:** `rg -n "prompt-eval" AGENTS.md` returns the new entries.

---

## Tests to write or update

No tests during refactor phase. Tests will be written when test infrastructure returns.
