"""ev.py — CCYA event debug CLI.

See scripts/debug/README.md for full docs, especially the Play command
section for running game turns into existing saves.

Quick start — play a turn:
    .venv/bin/python scripts/debug/ev.py play "my action" \\
        --no-sanitize --save-dir saves/my-save saves/my-save/events.jsonl
"""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info < (3, 13):
    print(f"Error: ev.py requires Python 3.13+. You are using {sys.version.split()[0]}.", file=sys.stderr)
    print("Use: .venv/bin/python scripts/debug/ev.py <command>", file=sys.stderr)
    sys.exit(1)

STREAM_ALIASES: dict[str, str] = {
    "rules": "ruling",
    "ruling": "ruling",
    "progress": "record",
    "storytell": "record",
    "record": "record",
    "world": "world",
    "narrate": "narrate",
    "scene": "scene",
    "state": "state",
}


def _resolve_stream(name: str) -> str:
    canonical = STREAM_ALIASES.get(name)
    if not canonical:
        print(f"Unknown stream: {name}. Valid: {', '.join(sorted(STREAM_ALIASES))}", file=sys.stderr)
        sys.exit(1)
    return canonical


def _strip_flags(args: list[str]) -> tuple[dict[str, str], list[str]]:
    # Boolean flags that don't take values
    _BOOL_FLAGS = {"pacing", "dice", "sanitize", "all", "llm", "show-unchanged", "system", "compact", "list", "verbose", "summary", "estimate", "include-compaction", "user-only", "auto-report", "llm-checkers", "eval", "help", "from-events"}
    flags: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a[2:]
            if name in _BOOL_FLAGS:
                flags[name] = "true"
                i += 1
            elif i + 1 < len(args) and not args[i + 1].startswith("--"):
                flags[name] = args[i + 1]
                i += 2
            else:
                flags[name] = "true"
                i += 1
        else:
            positional.append(a)
            i += 1
    return flags, positional



def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip() if __doc__ else "ev.py — Debug CLI for CCYA events.jsonl")
        sys.exit(0)

    # Set up logging for CLI commands
    from ccya.logging_setup import setup_logging
    setup_logging()

    flags, args = _strip_flags(args)
    if not args:
       print("Error: no command specified.", file=sys.stderr)
       print("Commands: summary, timing, turn, prompt, deltas, mechanics, state, diff, trace, search, play, check, eval, init, status, state-history, active-conditions, npc-ghosting, storyteller-audit, sanitizer, thread-audit, ruling-audit, compat, beats, rolls, convergence, phase-transitions, curtain-call, warnings, prompt-sizes, prompt-eval", file=sys.stderr)
       print("\nUsage: .venv/bin/python scripts/debug/ev.py <command> [args...]", file=sys.stderr)
       sys.exit(1)

    cmd = args[0]

    from ccya.ev.events import load_events, find_turn

    # Initialize turn_file for commands that need it
    turn_file: Path | None = None

    # Auto-detect events.jsonl from --save-dir when no positional events path given
    if cmd not in ("play", "prompt-eval", "init", "eval", "status", "check") and "save-dir" in flags and not (len(args) > 1 and (args[-1].endswith(".jsonl") or args[-1].startswith("saves/"))):
        turn_file = Path(str(flags["save-dir"])) / "events.jsonl"

    # Skip events path extraction for commands that don't need pre-loaded events
    elif cmd not in ("play", "prompt-eval", "init", "eval", "status", "check") and len(args) > 1 and args[-1].startswith("saves/"):
        candidate = Path(args[-1])
        if candidate.is_dir():
            turn_file = candidate / "events.jsonl"
        else:
            turn_file = candidate
        args = args[:-1]
    elif cmd not in ("play", "prompt-eval", "init", "eval", "status", "check") and "save-dir" in flags:
        turn_file = Path(str(flags["save-dir"])) / "events.jsonl"
    elif cmd in ("play", "prompt-eval", "init", "eval", "status"):
        # play writes events; prompt-eval renders/calls; eval subcommands load events themselves; init creates new sessions; status reads state directly
        pass
    elif cmd == "check":
        # check loads events from --save-dir if provided
        if "save-dir" in flags:
            turn_file = Path(str(flags["save-dir"])) / "events.jsonl"
        elif len(args) > 1 and (args[-1].endswith(".jsonl") or args[-1].startswith("saves/")):
            candidate = Path(args[-1])
            if candidate.is_dir():
                turn_file = candidate / "events.jsonl"
            else:
                turn_file = candidate
            args = args[:-1]
        else:
            # check without --save-dir or events path — will load empty list
            pass
    else:
        print("Error: no events file specified. Use --save-dir <path> or pass events.jsonl path as argument.", file=sys.stderr)
        sys.exit(1)

    # Skip loading events for commands that don't need them
    skip_events = cmd in ("play", "init", "status", "help", "prompt-eval", "eval")
    # Also skip for check --list (checker list doesn't need data)
    if cmd == "check" and "list" in flags:
        skip_events = True

    events = load_events(turn_file) if not skip_events and turn_file else []

    match cmd:
        case "help":
            print(__doc__.strip() if __doc__ else "ev.py — Debug CLI for CCYA events.jsonl")
            print("\nCommands: summary, timing, turn, prompt, deltas, mechanics, state, diff, trace, search, play, check, eval, state-history, active-conditions, npc-ghosting, storyteller-audit, sanitizer, thread-audit, ruling-audit, compat, beats, rolls, convergence, phase-transitions, curtain-call, warnings, prompt-sizes, prompt-eval")
            sys.exit(0)
        case "summary":
            from ccya.ev.inspect import cmd_summary
            fmt = flags.get("format", "text")
            cmd_summary(events, format=fmt)
        case "timing":
            from ccya.ev.inspect import cmd_timing
            cmd_timing(events)
        case "turn":
            if len(args) < 2:
                print("Usage: ev.py turn TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found (or is a compaction entry)")
                sys.exit(1)
            if "json" in flags:
                import json
                print(json.dumps(ev, indent=2))
            else:
                from ccya.ev.inspect import cmd_turn
                cmd_turn(ev)
        case "prompt-eval":
            from ccya.ev.prompt_eval import cmd_prompt_eval
            cmd_prompt_eval(flags, args[1:])
        case "prompt":
            if len(args) < 3:
                print("Usage: ev.py prompt TURN STREAM [--field FIELD] [--system] [--from-events] --save-dir DIR", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            stream = args[2]
            stream = _resolve_stream(stream)
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            from ccya.ev.inspect import cmd_prompt
            field = flags.get("field")
            include_system = "system" in flags
            from_events = "from-events" in flags
            save_dir = Path(flags["save-dir"]) if "save-dir" in flags else None
            cmd_prompt(ev, stream, field=field, include_system=include_system, from_events=from_events, save_dir=save_dir)
        case "deltas":
            if len(args) < 2:
                print("Usage: ev.py deltas TURN [--compact]", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found (or is a compaction entry)")
                sys.exit(1)
            from ccya.ev.deltas import cmd_deltas
            compact = "compact" in flags
            cmd_deltas(ev, events, compact=compact)
        case "mechanics":
            if len(args) < 2:
                print("Usage: ev.py mechanics TURN [--pacing] [--dice] [--sanitize]", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            from ccya.ev.deltas import cmd_mechanics
            show_pacing = "pacing" in flags
            show_dice = "dice" in flags
            show_sanitize = "sanitize" in flags
            cmd_mechanics(ev, events=events, show_pacing=show_pacing, show_dice=show_dice, show_sanitize=show_sanitize)
        case "state":
            if "save-dir" not in flags:
                print("Error: --save-dir is required for state command", file=sys.stderr)
                sys.exit(1)
            save_dir_path = Path(flags["save-dir"])
            fmt = flags.get("format", "full")
            valid_formats = ("full", "compact", "pc", "inventory", "location", "scene", "arc", "npcs", "compidx")
            if fmt not in valid_formats:
                print(f"Error: unknown format '{fmt}'. Valid formats: {', '.join(valid_formats)}", file=sys.stderr)
                sys.exit(1)
            from ccya.ev.state_tools import cmd_state
            cmd_state(fmt, save_dir_path)
        case "diff":
            turn_a = int(args[1]) if len(args) > 1 else None
            turn_b = int(args[2]) if len(args) > 2 else None
            section = flags.get("section")
            valid_sections = ("npcs", "inventory", "conditions", "location", "tags", "applied")
            if section is not None and section not in valid_sections:
                print(f"Error: unknown section '{section}'. Valid sections: {', '.join(valid_sections)}", file=sys.stderr)
                sys.exit(1)
            from ccya.ev.state_tools import cmd_diff
            cmd_diff(events, turn_a, turn_b, section_filter=section)
        case "trace":
            if len(args) < 2:
                print("Error: trace requires a field name", file=sys.stderr)
                sys.exit(1)
            field = args[1]
            from_turn = int(flags["from"]) if "from" in flags else None
            to_turn = int(flags["to"]) if "to" in flags else None
            show_unchanged = "show-unchanged" in flags
            from ccya.ev.state_tools import cmd_trace
            cmd_trace(events, field, from_turn=from_turn, to_turn=to_turn, show_unchanged=show_unchanged)
        case "search":
            if len(args) < 2:
                print("Error: search requires at least one expression", file=sys.stderr)
                sys.exit(1)
            exprs = args[1:]
            from ccya.ev.state_tools import cmd_search
            cmd_search(events, exprs)
        case "threads":
            from ccya.ev.state_tools import cmd_threads
            cmd_threads(events, summary="summary" in flags, include_compaction="include-compaction" in flags)
        case "beats":
            from ccya.ev.state_tools import cmd_beats
            cmd_beats(events, include_compaction="include-compaction" in flags)
        case "goals":
            from ccya.ev.state_tools import cmd_goals
            cmd_goals(events, include_compaction="include-compaction" in flags)
        case "effective-age":
            from ccya.ev.state_tools import cmd_effective_age
            cmd_effective_age(events, include_compaction="include-compaction" in flags)
        case "beat-ttl":
            from ccya.ev.state_tools import cmd_beat_ttl
            cmd_beat_ttl(events, include_compaction="include-compaction" in flags)
        case "rolls":
            from ccya.ev.state_tools import cmd_rolls
            cmd_rolls(events, summary="summary" in flags, include_compaction="include-compaction" in flags)
        case "state-history":
            from ccya.ev.audit import cmd_state_history
            cmd_state_history(events)
        case "active-conditions":
            from ccya.ev.audit import cmd_active_conditions
            cmd_active_conditions(events)
        case "npc-ghosting":
            from ccya.ev.audit import cmd_npc_ghosting
            cmd_npc_ghosting(events)
        case "storyteller-audit":
            from ccya.ev.audit import cmd_storyteller_audit
            cmd_storyteller_audit(events)
        case "sanitizer":
            if len(args) < 2:
                print("Usage: ev.py sanitizer TURN --save-dir DIR", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            from ccya.ev.audit import cmd_sanitizer
            cmd_sanitizer(events, turn)
        case "thread-audit":
            from ccya.ev.audit import cmd_thread_audit
            cmd_thread_audit(events)
        case "ruling-audit":
            from ccya.ev.audit import cmd_ruling_audit
            cmd_ruling_audit(events)
        case "compat":
            from ccya.ev.compat import cmd_compat
            cmd_compat(events)
        case "convergence":
            from ccya.ev.state_tools import cmd_convergence
            cmd_convergence(events, estimate="estimate" in flags, include_compaction="include-compaction" in flags, by_scene="by-scene" in flags)
        case "phase-transitions":
            from ccya.ev.state_tools import cmd_phase_transitions
            cmd_phase_transitions(events, include_compaction="include-compaction" in flags, by_scene="by-scene" in flags)
        case "curtain-call":
            from ccya.ev.state_tools import cmd_curtain_call
            cmd_curtain_call(events, include_compaction="include-compaction" in flags, by_scene="by-scene" in flags)
        case "warnings":
            from ccya.ev.warnings import cmd_warnings
            cmd_warnings(events)
        case "personas":
            from ccya.ev.persona import PERSONA_PROMPTS
            print("Available personas:")
            for name, prompt in PERSONA_PROMPTS.items():
                print(f"\n  {name}:")
                print(f"    {prompt[:100]}...")
        case "prompt-sizes":
            from ccya.ev.prompt_sizes import cmd_prompt_sizes
            cmd_prompt_sizes(events, include_compaction="include-compaction" in flags)
        case "play":
            from ccya.ev.play import cmd_play
            cmd_play(flags, args)
        case "check":
            from ccya.ev.check import cmd_check
            from ccya.ev.checkers import list_checkers

            if "help" in flags:
                print("Usage: ev.py check TURN [CHECKER_ID ...] [--all] [--llm] [--checker-model MODEL] [--save-dir PATH] [--pack PATH]")
                print("       ev.py check --list")
                print("\nRun checkers against existing events.")
                print("\nFlags:")
                print("  --all              Run all registered checkers")
                print("  --llm              Include LLM-based checkers")
                print("  --checker-model    Override checker model name")
                print("  --save-dir         Path to save directory (needed for sanitizer_lifecycle)")
                print("  --pack             Path to pack directory for checker config overrides")
                print("  --list             List all registered checkers (no events loaded)")
                print("  --verbose          Show per-checker detail in summary mode")
                print("\nRegistered checkers:")
                for meta in list_checkers():
                    print(f"  {meta['id']} ({meta['type']}): {meta['description']}")
                sys.exit(0)

            check_turn: int | None = None
            check_ids: list[str] | None = None
            check_all = "all" in flags
            check_llm = "llm" in flags
            check_list = "list" in flags
            check_verbose = "verbose" in flags

            if not check_list and len(args) > 1:
                check_turn = int(args[1])
            if not check_list and len(args) > 2:
                check_ids = args[2:]

            if not check_all and not check_ids and not check_list:
                print("Error: specify --all, --list, or provide checker IDs", file=sys.stderr)
                sys.exit(1)

            check_save_dir: Path | None = Path(flags["save-dir"]) if "save-dir" in flags else None
            checker_model = flags.get("checker-model")
            pack_dir: Path | None = Path(flags["pack"]) if "pack" in flags else None
            cmd_check(events, turn=check_turn, checker_ids=check_ids, all_checkers=check_all, include_llm=check_llm, save_dir=check_save_dir, checker_model=checker_model, list_only=check_list, verbose=check_verbose, pack_dir=pack_dir)
        case "init":
            from ccya.ev.init import cmd_init
            cmd_init(flags, args)
        case "status":
            from ccya.ev.status import cmd_status
            cmd_status(flags)
        case "eval":
            from ccya.ev.eval import cmd_eval_run, cmd_eval_list, cmd_eval_compare
            from ccya.ev.session_config import resolve_auto_report

            if len(args) < 2:
                print("Usage: ev.py eval run <scenario.yaml> [--model] [--temp] [--checkers] [--report] [--auto-report] [--llm-checkers]", file=sys.stderr)
                print("       ev.py eval list", file=sys.stderr)
                print("       ev.py eval compare <baseline> <current> [--checkers]", file=sys.stderr)
                sys.exit(1)

            subcmd = args[1]
            if subcmd == "run":
                if "help" in flags:
                    print("Usage: ev.py eval run <scenario.yaml> [--model] [--temp] [--checkers] [--report] [--auto-report] [--llm-checkers]")
                    print()
                    print("Run a scenario against the game engine and check results.")
                    print()
                    print("Flags:")
                    print("  --model NAME          Override LLM model")
                    print("  --temp N              Override temperature")
                    print("  --checkers            Comma-separated checker IDs to run")
                    print("  --report PATH         Write report to PATH")
                    print("  --auto-report         Write report.md in session directory")
                    print("  --llm-checkers        Include LLM-based checkers")
                    sys.exit(0)
                if len(args) < 3:
                    print("Usage: ev.py eval run <scenario.yaml> ...", file=sys.stderr)
                    sys.exit(1)
                scenario_path = Path(args[2])
                model = flags.get("model")
                temp = float(flags["temp"]) if "temp" in flags else None
                checker_list = flags.get("checkers", "").split(",") if flags.get("checkers") else None
                if checker_list is not None:
                    checker_list = [c.strip() for c in checker_list if c.strip()]
                report_path = Path(flags["report"]) if "report" in flags else None
                auto_report = resolve_auto_report(flags, {})
                cmd_eval_run(
                    scenario_path,
                    model=model,
                    temp=temp,
                    checkers=checker_list,
                    report=report_path,
                    auto_report=auto_report,
                    llm_checkers="llm-checkers" in flags,
                )
            elif subcmd == "list":
                cmd_eval_list()
            elif subcmd == "compare":
                if "help" in flags:
                    print("Usage: ev.py eval compare <baseline_dir> <current_dir> [--checkers]")
                    print()
                    print("Compare two eval runs side-by-side. Shows IMPROVED, REGRESSION, unchanged, added, or removed checkers.")
                    print()
                    print("Flags:")
                    print("  --checkers          Comma-separated checker IDs to compare")
                    sys.exit(0)
                if len(args) < 4:
                    print("Usage: ev.py eval compare <baseline_dir> <current_dir> [--checkers]", file=sys.stderr)
                    sys.exit(1)
                baseline_path = Path(args[2])
                current_path = Path(args[3])
                checker_list = flags.get("checkers", "").split(",") if flags.get("checkers") else None
                if checker_list is not None:
                    checker_list = [c.strip() for c in checker_list if c.strip()]
                cmd_eval_compare(baseline_path, current_path, checkers=checker_list)
            else:
                print(f"Unknown eval subcommand: {subcmd}", file=sys.stderr)
                sys.exit(1)
        case _:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__.strip())
            sys.exit(1)
