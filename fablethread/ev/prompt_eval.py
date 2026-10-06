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
import os
import sys
from pathlib import Path
from typing import Any

from fablethread.engine.config import build_engine_config, _build_jinja_env, _render
from fablethread.models import load_config
from fablethread.pack import load_pack
from fablethread.ev.checkers import CheckerResult
from fablethread.ev.events import find_turn, load_events, load_prompts
from fablethread.ev.prompt_context import build_prompt_context
from fablethread.ev.scenario import PromptEvalScenario, load_prompt_scenario
from fablethread.engine.seed import _build_prepare_seed_messages, _build_narrate_seed_messages
from fablethread.pack import SeedState
from fablethread.engine.names import generate_npc_names_split
from fablethread.engine.npc_roster import build_pending_roster_entries

PROMPTS_DIR = str(Path(__file__).parent.parent / "prompts")

_log = logging.getLogger(__name__)


def _inject_pending_names(ctx: dict[str, Any], save_dir: Path, turn_no: int) -> None:
    """Inject pending name pool entries into the narrate roster and set pending_new_character_name."""
    try:
        state_path = save_dir / "state.yaml"
        if not state_path.exists():
            return
        import yaml
        with open(state_path) as f:
            state = yaml.safe_load(f)
        pack_id = state.get("meta", {}).get("setting_pack", "")
        if not pack_id:
            return
        pack = load_pack(pack_id, Path(__file__).parent.parent.parent / "packs")
        locales = pack.manifest.name_locales
        if not locales:
            return
        pool = generate_npc_names_split(locales, male_count=3, female_count=3, seed=turn_no)
        pending = build_pending_roster_entries(pool, turn_no=turn_no)
        if pending and "npc_roster" in ctx:
            ctx["npc_roster"] = ctx["npc_roster"] + pending
        # Inject the pending new character name (rotated by pending_names_used)
        used = state.get("meta", {}).get("pending_names_used", 0)
        all_pool_names = []
        for gender in ("male", "female"):
            all_pool_names.extend(pool.get(gender, []))
        if all_pool_names and "npc_roster" in ctx:
            ctx["pending_new_character_name"] = all_pool_names[used % len(all_pool_names)]
    except Exception as e:
        _log.debug("Failed to inject pending names: %s", e)


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

    streams = ["ruling", "narrate", "scene", "state", "record"] if all_streams else [stream]

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

    # Support both old format (rendered_user/rendered_system) and new format (context_meta)
    meta = blob.get("context_meta") or {}
    system = blob.get("rendered_system") or meta.get("system_text") or ""
    user = blob.get("rendered_user") or meta.get("user_text") or ""

    return {
        "system": system,
        "user": user,
        "output": output,
    }


def cmd_prompt_eval_seed(
    pack_id: str,
    model: str | None = None,
    temp: float | None = None,
) -> None:
    """Render seed prompt, call LLM, check JSON output."""
    raw_cfg = load_config()
    config = build_engine_config(raw_cfg)
    model = model or config.model
    temp = temp if temp is not None else config.prepare_seed_temperature

    packs_dir = Path(__file__).parent.parent.parent / "packs"
    pack = load_pack(pack_id, packs_dir)

    env = _build_jinja_env(PROMPTS_DIR)
    messages, _, pool = _build_prepare_seed_messages(env, pack)

    from fablethread.llm_client import chat_with_config as llm_chat

    try:
        llm_result = asyncio.run(llm_chat(
            config,
            messages=messages,
            temperature=temp,
            timeout=180.0,
            num_ctx=config.num_ctx,
        ))
        output = llm_result.content
    except Exception as exc:
        print(f"Error: LLM call failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Seed Generation — {pack.manifest.id} ===\n")
    print("--- SYSTEM ---")
    print(messages[0]["content"])
    print()
    print("--- USER ---")
    print(messages[1]["content"])
    print()
    print("--- OUTPUT ---")
    print(output)
    print()

    # Check JSON format
    from fablethread.engine.config import _find_json
    parsed = _find_json(output)
    if parsed is None:
        print("## JSON format: FAIL")
        print("  Could not extract valid JSON from output")
        # Save full response for debugging
        failed_dir = Path("saves") / "prepare_seed_failures"
        failed_dir.mkdir(parents=True, exist_ok=True)
        failed_file = failed_dir / f"prompt-eval_{pack.manifest.id}_{temp}_{os.urandom(4).hex()}.txt"
        failed_file.write_text(output)
        print(f"  Full response saved to: {failed_file}")
    else:
        print("## JSON format: PASS")
        print(f"  Extracted JSON with keys: {', '.join(parsed.keys())}")
        if "seed_state" in parsed:
            ss = parsed["seed_state"]
            print(f"  seed_state keys: {', '.join(ss.keys())}")
        # Save seed state for narrate-seed testing
        seed_dir = Path(f"saves/prompt-eval-seed-{pack.manifest.id}-{temp}")
        seed_dir.mkdir(parents=True, exist_ok=True)
        with open(seed_dir / "seed.json", "w") as f:
            json.dump(ss, f, indent=2)
        print(f"  Seed state saved to: {seed_dir / 'seed.json'}")


def cmd_prompt_eval_narrate_seed(
    save_dir: Path,
    model: str | None = None,
    temp: float | None = None,
    pack: str | None = None,
) -> None:
    """Render narrate_seed prompt from a saved seed state, call LLM, check output.

    Accepts either:
    - A directory containing seed.json (from prepare_seed output)
    - A directory with state.yaml (extracts seed fields)
    """
    raw_cfg = load_config()
    config = build_engine_config(raw_cfg)
    model = model or config.model
    temp = temp if temp is not None else 0.7

    # Try seed.json first (cleanest source)
    seed_path = save_dir / "seed.json"
    if seed_path.exists():
        import yaml as _yaml
        with open(seed_path) as f:
            seed_data = json.load(f)
        seed_state = SeedState.model_validate(seed_data)
    else:
        # Fall back to state.yaml — extract only SeedState fields
        state_path = save_dir / "state.yaml"
        if not state_path.exists():
            print(f"Error: no seed.json or state.yaml at {save_dir}", file=sys.stderr)
            sys.exit(1)

        with open(state_path) as f:
            state_data = _yaml.safe_load(f)

        # Extract only the fields SeedState needs, stripping turn-added data
        import yaml
        seed_data = {
            "meta": state_data.get("meta", {}),
            "pc": state_data.get("pc", {}),
            "location": state_data.get("location", {}),
            "inventory": state_data.get("inventory", []),
            "scene": state_data.get("scene", {}),
            "compendium": state_data.get("compendium", {}),
            "long_term_objective": state_data.get("long_term_objective"),
            "arc_origin": state_data.get("arc_origin", ""),
            "actions": state_data.get("actions", []),
            "world": state_data.get("world", {}),
        }
        seed_state = SeedState.model_validate(seed_data)

    # Load pack for setting_info
    pack_id = pack or seed_state.meta.get("setting_pack", "") or seed_state.meta.get("pack_source", "")
    if not pack_id:
        print("Error: could not determine pack_id from seed state or --pack flag", file=sys.stderr)
        sys.exit(1)

    packs_dir = Path(__file__).parent.parent.parent / "packs"
    pack = load_pack(pack_id, packs_dir)

    # Build narrate_seed messages
    env = _build_jinja_env(PROMPTS_DIR)
    messages, ctx = _build_narrate_seed_messages(env, seed_state, pack=pack)

    from fablethread.llm_client import chat_with_config as llm_chat

    try:
        llm_result = asyncio.run(llm_chat(
            config,
            messages=messages,
            temperature=temp,
            timeout=180.0,
            num_ctx=config.num_ctx,
        ))
        output = llm_result.content
    except Exception as exc:
        print(f"Error: LLM call failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"=== Narrate Seed — {pack.manifest.id} ===\n")
    print("--- SYSTEM ---")
    print(messages[0]["content"])
    print()
    print("--- OUTPUT ---")
    print(output)
    print()

    # Check JSON format
    from fablethread.engine.config import _find_json
    parsed = _find_json(output)
    if parsed is None:
        print("## JSON format: FAIL")
        print("  Could not extract valid JSON from output")
        failed_dir = Path("saves") / "narrate_seed_failures"
        failed_dir.mkdir(parents=True, exist_ok=True)
        failed_file = failed_dir / f"prompt-eval_{save_dir.name}_{os.urandom(4).hex()}.txt"
        failed_file.write_text(output)
        print(f"  Full response saved to: {failed_file}")
    else:
        print("## JSON format: PASS")
        print(f"  Extracted JSON with keys: {', '.join(parsed.keys())}")
        # Check opening narrative length
        opening = parsed.get("opening_narrative", "")
        if opening:
            print(f"  opening_narrative length: {len(opening)} chars")
            if len(opening) < 1500:
                print(f"  WARNING: opening_narrative below 1500 chars (got {len(opening)})")
        else:
            print("  WARNING: no opening_narrative in output")
        actions = parsed.get("actions", [])
        print(f"  actions count: {len(actions)}")
        outcome = parsed.get("outcome_summary", "")
        print(f"  outcome_summary: {outcome[:80]}..." if len(outcome) > 80 else f"  outcome_summary: {outcome}")


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
        # Inject pending name pool entries into the roster for narrate streams
        if scenario.stream == "narrate":
            _inject_pending_names(ctx, save_dir, scenario.turn)
        system_template = _get_system_template_name(scenario.stream)
        user_template = _get_template_name(scenario.stream)
        rendered_system = _render(env, system_template, ctx)
        rendered_user = _render(env, user_template, ctx)

    # Call LLM
    raw_cfg = load_config()
    config = build_engine_config(raw_cfg)
    temp = scenario.temp if scenario.temp is not None else 0.7

    from fablethread.llm_client import chat_with_config as llm_chat

    try:
        llm_result = asyncio.run(llm_chat(
            config,
            messages=[
                {"role": "system", "content": rendered_system},
                {"role": "user", "content": rendered_user},
            ],
            temperature=temp,
            timeout=180.0,
            num_ctx=config.num_ctx,
        ))
        output = llm_result.content
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
        print("Usage: ev.py prompt-eval <seed|dump|call> [args...]")
        print()
        print("Subcommands:")
        print("  seed <pack> [--model MODEL] [--temp TEMP]")
        print("    Render seed prompt, call LLM, check JSON output.")
        print()
        print("    Flags:")
        print("      --model MODEL   Override model")
        print("      --temp TEMP     Override temperature")
        print()
        print("  dump <save-dir> --turn N --stream STREAM [--from-events]")
        print("    Re-render a prompt from a saved session for inspection.")
        print()
        print("    Flags:")
        print("      --turn N          Turn number to render")
        print("      --stream STREAM   Stream name: ruling, narrate, scene, state, record")
        print("      --from-events     Render from events.jsonl (no LLM call)")
        print("      --all             Render all streams")
        print("      --user-only       Show only user prompts")
        print()
        print("  seed <pack> [--model MODEL] [--temp TEMP]")
        print("    Render prepare_seed prompt, call LLM, check JSON output.")
        print()
        print("    Flags:")
        print("      --model MODEL     Override model")
        print("      --temp TEMP       Override temperature")
        print()
        print("  narrate-seed <save-dir> [--model MODEL] [--temp TEMP]")
        print("    Render narrate_seed prompt from saved state, call LLM, check output.")
        print()
        print("    Flags:")
        print("      --model MODEL     Override model")
        print("      --temp TEMP       Override temperature")
        print()
        print("  call <scenario.yaml> [--from-events]")
        print("    Render prompts from a scenario, optionally call LLM and check results.")
        print()
        print("    Flags:")
        print("      --from-events     Use stored output instead of calling LLM")
        sys.exit(0)

    if len(args) < 2:
        print("Usage: ev.py prompt-eval <seed|narrate-seed|dump|call> [args...]", file=sys.stderr)
        print("\nSubcommands:")
        print("  seed <pack> [--model MODEL] [--temp TEMP]")
        print("  narrate-seed <save-dir> [--model MODEL] [--temp TEMP]")
        print("  dump <save-dir> --turn N [--stream STREAM] [--all] [--user-only] [--from-events]")
        print("  call <scenario.yaml> [--from-events]")
        sys.exit(1)

    subcmd = args[0]
    from_events = "from-events" in flags

    if subcmd == "seed":
        if len(args) < 2:
            print("Usage: ev.py prompt-eval seed <pack> [--model MODEL] [--temp TEMP]", file=sys.stderr)
            sys.exit(1)
        pack_id = args[1]
        model = flags.get("model")
        temp = float(flags["temp"]) if "temp" in flags else None
        cmd_prompt_eval_seed(pack_id, model, temp)

    elif subcmd == "narrate-seed":
        if len(args) < 2:
            print("Usage: ev.py prompt-eval narrate-seed <save-dir> [--model MODEL] [--temp TEMP] [--pack PACK]", file=sys.stderr)
            sys.exit(1)
        save_dir = Path(args[1])
        model = flags.get("model")
        temp = float(flags["temp"]) if "temp" in flags else None
        pack = flags.get("pack")
        cmd_prompt_eval_narrate_seed(save_dir, model, temp, pack)

    elif subcmd == "dump":
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
