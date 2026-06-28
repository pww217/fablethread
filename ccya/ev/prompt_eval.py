"""prompt_eval.py — Fast prompt testing for CCYA.

Subcommands:
  dump  — renders and prints prompts (no LLM)
  call  — renders + LLM + check

`prompt-eval call` has a 180s timeout on the LLM request. Use `prompt-eval
dump` to validate prompt rendering without hitting the LLM.
"""

from __future__ import annotations

import asyncio
import difflib
import json
import logging
import sys
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, _build_jinja_env, _render
from ccya.ev.checkers import CheckerResult
from ccya.ev.events import find_turn, load_events, load_prompts
from ccya.ev.prompt_context import build_prompt_context
from ccya.ev.scenario import PromptEvalScenario, load_prompt_scenario

PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")

_log = logging.getLogger(__name__)


def _get_template_name(stream: str) -> str:
    """Map stream name to Jinja2 template filename."""
    if stream == "narrate":
        return "narrate_user.j2"
    elif stream == "ruling":
        return "ruling_user.j2"
    elif stream == "record":
        return "record_user.j2"
    elif stream == "world":
        return "world_user.j2"
    else:
        return f"extract_{stream}_user.j2"


def _get_system_template_name(stream: str) -> str:
    """Map stream name to Jinja2 system template filename."""
    if stream == "narrate":
        return "narrate_system.j2"
    elif stream == "ruling":
        return "ruling_system.j2"
    elif stream == "record":
        return "record_system.j2"
    elif stream == "world":
        return "world_system.j2"
    else:
        return f"extract_{stream}_system.j2"


def cmd_prompt_eval_dump(
    events: list[dict[str, Any]],
    save_dir: Path,
    turn: int,
    stream: str,
    from_events: bool = False,
    user_only: bool = False,
    all_streams: bool = False,
) -> None:
    """Dump rendered prompts for a single turn/stream.

    If all_streams is True, dump all 5 streams sequentially.
    If user_only is True, skip the system prompt.
    """
    turn_ev = find_turn(events, turn)
    if turn_ev is None:
        print(f"Error: turn {turn} not found", file=sys.stderr)
        sys.exit(1)

    streams = ["ruling", "narrate", "scene", "state", "storytell"] if all_streams else [stream]

    for s in streams:
        if all_streams:
            print(f"===== Turn {turn} — {s} =====")
        else:
            print(f"=== Turn {turn} — {s} (re-rendered) ===\n")

        if from_events:
            p = _extract_prompt_from_event(turn_ev, save_dir, s)
            if not user_only:
                print("--- SYSTEM ---")
                print(p["system"])
                print()
            print("--- USER ---")
            print(p["user"])
            print()
            if not user_only:
                print("--- OUTPUT ---")
                print(p["output"])
        else:
            env = _build_jinja_env(PROMPTS_DIR)
            ctx = build_prompt_context(events, turn, s)
            system_template = _get_system_template_name(s)
            user_template = _get_template_name(s)
            rendered_system = _render(env, system_template, ctx)
            rendered_user = _render(env, user_template, ctx)
            if not user_only:
                print("--- SYSTEM ---")
                print(rendered_system)
                print()
            print("--- USER ---")
            print(rendered_user)
        print()


def _extract_prompt_from_event(
    ev: dict[str, Any],
    save_dir: Path,
    stream: str,
) -> dict[str, str]:
    """Extract stored rendered prompts from events or prompts.jsonl.

    Loads from prompts.jsonl first; falls back to reading from event blob.
    """
    prompts = load_prompts(save_dir)
    turn = ev.get("turn")
    if prompts is not None and turn is not None:
        for p in prompts:
            if p.get("turn") == turn and p.get("stream") == stream:
                return {
                    "system": p.get("rendered_system") or "",
                    "user": p.get("rendered_user") or "",
                    "output": "",
                }

    # Fallback: read from event blob
    if stream == "ruling":
        blob = ev.get("ruling_prompt") or {}
    elif stream == "narrate":
        blob = ev.get("narrate_prompt") or {}
    else:
        blob = (ev.get("extraction") or {}).get(stream) or {}

    output = blob.get("output") or ""
    if isinstance(output, dict):
        output = json.dumps(output, indent=2)

    return {
        "system": blob.get("rendered_system") or "",
        "user": blob.get("rendered_user") or "",
        "output": output,
    }


def cmd_prompt_eval_call(
    events: list[dict[str, Any]],
    save_dir: Path,
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
        p = _extract_prompt_from_event(turn_ev, save_dir, scenario.stream)
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
        llm_result = asyncio.run(llm_chat(
            host=config.host,
            model=model,
            messages=[
                {"role": "system", "content": rendered_system},
                {"role": "user", "content": rendered_user},
            ],
            temperature=temp,
            timeout=180.0,
            num_ctx=config.num_ctx,
        ))
        output = llm_result.get("response", "")
    except Exception as exc:
        print(f"Error: LLM call failed: {exc}", file=sys.stderr)
        sys.exit(1)

    # Print rendered prompts and LLM output
    print(f"=== Turn {scenario.turn} — {scenario.stream} ===\n")
    print("--- SYSTEM ---")
    print(rendered_system)
    print()
    print("--- USER ---")
    print(rendered_user)
    print()
    print("--- OUTPUT ---")
    try:
        parsed = json.loads(output)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError:
        print(output)
    print()

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
    # Strip JSON code block markers that LLMs often add
    cleaned = output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        parsed = json.loads(cleaned)
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
        "state": [],
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
    if "help" in flags or len(args) < 1:
        print("Usage: ev.py prompt-eval <dump|call> [args...]")
        print()
        print("Subcommands:")
        print("  dump <save-dir> --turn N --stream STREAM [--from-events]")
        print("    Re-render a prompt from a saved session for inspection.")
        print()
        print("    Flags:")
        print("      --turn N          Turn number to render")
        print("      --stream STREAM   Stream name: ruling, narrate, scene, state, storytell")
        print("      --from-events     Render from events.jsonl (no LLM call)")
        print("      --all             Render all streams")
        print("      --user-only       Show only user prompts")
        print()
        print("  call <scenario.yaml> [--from-events]")
        print("    Render prompts from a scenario, optionally call LLM and check results.")
        print()
        print("    Flags:")
        print("      --from-events     Use stored output instead of calling LLM")
        sys.exit(0)

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
            print("Usage: ev.py prompt-eval dump <save-dir> --turn N [--stream STREAM] [--all] [--user-only] [--from-events]", file=sys.stderr)
            sys.exit(1)
        save_dir = args[1]
        turn = int(flags["turn"]) if "turn" in flags else None
        stream = flags.get("stream", "scene")
        user_only = "user-only" in flags
        all_streams = "all" in flags

        if turn is None:
            print("Error: --turn is required for dump", file=sys.stderr)
            sys.exit(1)

        events = load_events(Path(save_dir) / "events.jsonl")
        cmd_prompt_eval_dump(events, Path(save_dir), turn, stream, from_events=from_events, user_only=user_only, all_streams=all_streams)

    elif subcmd == "call":
        if len(args) < 2:
            print("Usage: ev.py prompt-eval call <scenario.yaml> [--from-events]", file=sys.stderr)
            sys.exit(1)
        scenario_path = Path(args[1])
        scenario = load_prompt_scenario(scenario_path)

        events = load_events(Path(scenario.save) / "events.jsonl")
        cmd_prompt_eval_call(events, Path(scenario.save), scenario, from_events=from_events)

    else:
        print(f"Error: unknown subcommand '{subcmd}'", file=sys.stderr)
        sys.exit(1)
