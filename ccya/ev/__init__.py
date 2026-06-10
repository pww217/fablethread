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

DEFAULT_SAVE_DIR = Path("saves/default")
DEFAULT_FILE = DEFAULT_SAVE_DIR / "events.jsonl"

STREAM_ALIASES: dict[str, str] = {
    "rules": "ruling",
    "ruling": "ruling",
    "progress": "storytell",
    "storytell": "storytell",
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
    flags: dict[str, str] = {}
    positional: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name = a[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                flags[name] = args[i + 1]
                i += 2
            else:
                flags[name] = "true"
                i += 1
        else:
            positional.append(a)
            i += 1
    return flags, positional


def _stub_command(name: str, phase: int) -> None:
    print(f"'{name}' not yet implemented — planned for phase {phase}")
    sys.exit(0)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip() if __doc__ else "ev.py — Debug CLI for CCYA events.jsonl")
        sys.exit(0)

    flags, args = _strip_flags(args)
    if not args:
        print("Error: no command specified.", file=sys.stderr)
        print("Commands: summary, timing, turn, prompt, outputs, deltas, mechanics, state, diff, trace, search, play, check, eval", file=sys.stderr)
        print("\nUsage: .venv/bin/python scripts/debug/ev.py <command> [args...]", file=sys.stderr)
        sys.exit(1)

    cmd = args[0]

    from ccya.ev.events import load_events, find_turn

    if len(args) > 1 and args[-1].startswith("saves/"):
        turn_file = Path(args[-1])
        args = args[:-1]
    else:
        turn_file = DEFAULT_FILE

    events = load_events(turn_file)

    match cmd:
        case "help":
            print(__doc__.strip() if __doc__ else "ev.py — Debug CLI for CCYA events.jsonl")
            print("\nCommands: summary, timing, turn, prompt, outputs, deltas, mechanics, state, diff, trace, search, play, check, eval")
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
        case "prompt":
            if len(args) < 3:
                print("Usage: ev.py prompt TURN STREAM [--field FIELD] [--system]", file=sys.stderr)
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
            cmd_prompt(ev, stream, field=field, include_system=include_system)
        case "deltas":
            if len(args) < 2:
                print("Usage: ev.py deltas TURN", file=sys.stderr)
                sys.exit(1)
            turn = int(args[1])
            ev = find_turn(events, turn)
            if not ev:
                print(f"Turn {turn} not found")
                sys.exit(1)
            from ccya.ev.deltas import cmd_deltas
            cmd_deltas(ev, events)
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
            save_dir_path = Path(flags["save-dir"]) if "save-dir" in flags else DEFAULT_SAVE_DIR
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
        case "play":
            from ccya.ev.play import cmd_play
            cmd_play(flags, args)
        case "check":
            from ccya.ev.check import cmd_check
            from ccya.ev.checkers import list_checkers

            if "help" in flags:
                print("Usage: ev.py check TURN [CHECKER_ID ...] [--all] [--llm] [--checker-model MODEL] [--save-dir PATH]")
                print("\nRun checkers against existing events.")
                print("\nFlags:")
                print("  --all              Run all registered checkers")
                print("  --llm              Include LLM-based checkers")
                print("  --checker-model    Override checker model name")
                print("  --save-dir         Path to save directory (needed for sanitizer_lifecycle)")
                print("\nRegistered checkers:")
                for meta in list_checkers():
                    print(f"  {meta['id']} ({meta['type']}): {meta['description']}")
                sys.exit(0)

            check_turn: int | None = None
            check_ids: list[str] | None = None
            check_all = "all" in flags
            check_llm = "llm" in flags

            if len(args) > 1:
                check_turn = int(args[1])
            if len(args) > 2:
                check_ids = args[2:]

            if not check_all and not check_ids:
                print("Error: specify --all or provide checker IDs", file=sys.stderr)
                sys.exit(1)

            check_save_dir: Path | None = Path(flags["save-dir"]) if "save-dir" in flags else None
            checker_model = flags.get("checker-model")
            cmd_check(events, turn=check_turn, checker_ids=check_ids, all_checkers=check_all, include_llm=check_llm, save_dir=check_save_dir, checker_model=checker_model)
        case "eval":
            from ccya.ev.eval import cmd_eval_run, cmd_eval_list

            if len(args) < 2:
                print("Usage: ev.py eval run <scenario.yaml> [--model] [--temp] [--checkers] [--report]", file=sys.stderr)
                print("       ev.py eval list", file=sys.stderr)
                sys.exit(1)

            subcmd = args[1]
            if subcmd == "run":
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
                cmd_eval_run(scenario_path, model=model, temp=temp, checkers=checker_list, report=report_path)
            elif subcmd == "list":
                cmd_eval_list()
            else:
                print(f"Unknown eval subcommand: {subcmd}", file=sys.stderr)
                sys.exit(1)
        case _:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            print(__doc__.strip())
            sys.exit(1)
