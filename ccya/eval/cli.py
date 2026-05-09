"""ccya.eval CLI — `python -m ccya.eval`.

Subcommands:
  run [scenario]      Run scenario end-to-end (runner → judge → report).
  judge-only <run>    Re-run the judge against a prior run's events.jsonl.
  pack                Print effective eval config (debug aid).
  list                List discovered scenarios.

Flags applicable to `run`:
  --pack <id>         Override the scenario's pack (must be static).
  --temp <float>      Set temperature override on every LLM call.
  --no-judge          Skip the judge call.
  --packs-dir <dir>   Where packs live; defaults to evals/packs.

Always exits 0 unless the runner itself crashes with an unhandled exception.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from dataclasses import asdict, replace
from pathlib import Path

from ccya.eval.config import EvalConfig, InferenceConfig, load_eval_config
from ccya.eval.judge import run_judge, run_judge_streaming
from ccya.eval.report import generate_report, write_report_skeleton, finalize_report, append_judge_chunk
from ccya.eval.runner import (
    REPO_ROOT,
    RunResult,
    find_previous_run,
    load_run_result,
    run_scenario,
)
from ccya.eval.scenario import discover_scenarios, load_scenario

_log = logging.getLogger("ccya.eval")


def _resolve_packs_dirs(arg: str | None, eval_cfg: EvalConfig) -> list[Path]:
    """Returns the ordered list of packs-dirs to search. --packs-dir overrides config."""
    if arg:
        return [Path(arg).resolve()]
    return [
        (REPO_ROOT / d).resolve() if not Path(d).is_absolute() else Path(d).resolve()
        for d in eval_cfg.pack_dirs
    ]


def _resolve_scenario_path(arg: str | None, eval_cfg: EvalConfig) -> Path:
    """Resolve a scenario name to its file path.

    arg=None → use eval_cfg.default_scenario.
    arg=<id> → look up evals/scenarios/<id>.py.
    arg=<path> → resolve as filesystem path.
    """
    name = arg or eval_cfg.default_scenario
    p = Path(name)
    if p.suffix == ".py" and p.exists():
        return p.resolve()
    candidate = REPO_ROOT / "evals" / "scenarios" / f"{name}.py"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"scenario {name!r} not found at {candidate}")


async def _run_one_scenario(
    scenario_path: Path,
    args: argparse.Namespace,
    eval_cfg: EvalConfig,
    packs_dirs: list[Path],
) -> Path:
    """Run a single scenario end-to-end. Returns the REPORT.md path."""
    scenario = load_scenario(scenario_path)
    if args.pack:
        scenario = replace(scenario, pack=args.pack)

    num_turns = args.turns if args.turns is not None else eval_cfg.num_turns
    if num_turns < len(scenario.turns):
        scenario = replace(scenario, turns=scenario.turns[:num_turns])

    cfg_lines = [
        f"[eval] scenario={scenario.id} pack={scenario.pack} temp={eval_cfg.inference.temperature_override}",
        f"[eval] scenario_file={scenario_path}",
        f"[eval] model={eval_cfg.judge.model or '(engine default)'} num_turns={num_turns} rubric={eval_cfg.judge.rubric_path}",
    ]
    for line in cfg_lines:
        print(line, file=sys.stderr)

    _log.debug("scenario=%s pack=%s turns=%d", scenario.id, scenario.pack, num_turns)
    _log.debug("judge_model=%s rubric=%s", eval_cfg.judge.model or "(engine default)", eval_cfg.judge.rubric_path)

    rr: RunResult = await run_scenario(
        scenario,
        eval_cfg=eval_cfg,
        packs_dirs=packs_dirs,
    )
    _log.debug("runner done: turns=%d errors=%d output_dir=%s", len(rr.turns), rr.total_errors, rr.output_dir)
    print(f"[eval] runner done: {len(rr.turns)} turns (of {num_turns}), {rr.total_errors} errors → {rr.output_dir}", file=sys.stderr)

    report_path = write_report_skeleton(rr, eval_cfg=eval_cfg)
    print(f"[eval] skeleton written: {report_path}", file=sys.stderr)

    judge_result = None
    if not args.no_judge and eval_cfg.judge.enabled:
        prev_json = find_previous_run(
            (REPO_ROOT / eval_cfg.runs_dir).resolve(),
            scenario.id,
            exclude=Path(rr.output_dir),
        )
        prev_judge_md = None
        if prev_json is not None:
            candidate = prev_json.parent / f"{scenario.id}.judge.md"
            if candidate.exists():
                prev_judge_md = candidate
        print("[eval] judge streaming…", file=sys.stderr)
        judge_result = await run_judge_streaming(
            Path(rr.events_jsonl_path),
            eval_cfg=eval_cfg,
            output_dir=Path(rr.output_dir),
            scenario_id=scenario.id,
            on_chunk=lambda c: append_judge_chunk(report_path, c),
            previous_judge_md_path=prev_judge_md,
        )
        _log.debug("judge scores=%s", judge_result.scores)
        mech = judge_result.scores.get("mechanical_score", "?")
        print(f"[eval] judge mechanical_score={mech}", file=sys.stderr)
        rr.trace_md_path = judge_result.trace_md_path
        rr.judge_md_path = judge_result.judge_md_path
        artifacts_dir = Path(rr.output_dir) / "artifacts"
        (artifacts_dir / f"{scenario.id}.run.json").write_text(
            json.dumps(asdict(rr), indent=2, default=str)
        )
        finalize_report(report_path, rr, eval_cfg=eval_cfg, judge_result=judge_result)
        print(f"[eval] report finalized: {report_path}", file=sys.stderr)

    return report_path


async def _cmd_run(args: argparse.Namespace) -> int:
    eval_cfg = load_eval_config()
    log_level = eval_cfg.logging.level
    if log_level != "WARNING":
        logger = logging.getLogger("ccya.eval")
        logger.setLevel(getattr(logging, log_level, logging.WARNING))
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(handler)
    if args.temp is not None:
        eval_cfg = replace(eval_cfg, inference=InferenceConfig(
            temperature_override=float(args.temp),
            cache=eval_cfg.inference.cache,
        ))

    packs_dirs = _resolve_packs_dirs(args.packs_dir, eval_cfg)

    if args.all:
        scenario_paths = discover_scenarios(REPO_ROOT / "evals" / "scenarios")
        if not scenario_paths:
            print("[eval] no scenarios discovered", file=sys.stderr)
            return 1
    else:
        scenario_paths = [_resolve_scenario_path(args.scenario, eval_cfg)]

    print(f"[eval] running {len(scenario_paths)} scenario(s)", file=sys.stderr)
    last_report: Path | None = None
    for sp in scenario_paths:
        report = await _run_one_scenario(sp, args, eval_cfg, packs_dirs)
        last_report = report
        print(f"[eval] {sp.stem} → {report}", file=sys.stderr)

    if last_report is not None:
        print(str(last_report))
    return 0


async def _cmd_judge_only(args: argparse.Namespace) -> int:
    eval_cfg = load_eval_config()
    log_level = eval_cfg.logging.level
    if log_level != "WARNING":
        logger = logging.getLogger("ccya.eval")
        logger.setLevel(getattr(logging, log_level, logging.WARNING))
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
            logger.addHandler(handler)
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"[eval] not a directory: {run_dir}", file=sys.stderr)
        return 1

    run_jsons = sorted((run_dir / "artifacts").glob("*.run.json")) if (run_dir / "artifacts").is_dir() else sorted(run_dir.glob("*.run.json"))
    if not run_jsons:
        print(f"[eval] no *.run.json found in {run_dir}/artifacts/", file=sys.stderr)
        return 1
    rr = load_run_result(run_jsons[0])

    events_path = Path(rr.events_jsonl_path)
    if not events_path.exists():
        print(f"[eval] events not found: {events_path}", file=sys.stderr)
        return 1

    runs_dir = run_dir.parent
    prev_json = find_previous_run(runs_dir, rr.scenario_id, exclude=run_dir)
    prev_judge_md = None
    if prev_json is not None:
        candidate = prev_json.parent / f"{rr.scenario_id}.judge.md"
        if candidate.exists():
            prev_judge_md = candidate

    judge_result = await run_judge(
        Path(rr.events_jsonl_path),
        eval_cfg=eval_cfg,
        output_dir=Path(rr.output_dir),
        scenario_id=rr.scenario_id,
        previous_judge_md_path=prev_judge_md,
    )
    report_path = generate_report(rr, eval_cfg=eval_cfg, judge_result=judge_result)
    mech = judge_result.scores.get("mechanical_score", "?")
    print(f"[eval] re-judged: mechanical_score={mech}", file=sys.stderr)
    print(str(report_path))
    return 0


def _cmd_pack(args: argparse.Namespace) -> int:
    cfg = load_eval_config()
    print("Eval config:")
    for k in (
        "default_pack",
        "default_scenario",
        "pack_dirs",
        "default_save_root",
        "runs_dir",
        "num_turns",
    ):
        print(f"  {k}: {getattr(cfg, k)}")
    print(f"  logging.level: {cfg.logging.level}")
    print(f"  inference.temperature_override: {cfg.inference.temperature_override}")
    print(f"  inference.cache: {cfg.inference.cache}")
    print(f"  judge.enabled: {cfg.judge.enabled}")
    print(f"  judge.model: {cfg.judge.model}")
    print(f"  judge.rubric_path: {cfg.judge.rubric_path}")
    print(f"  judge.temperature: {cfg.judge.temperature}")
    print(f"  report.token_warn_pct: {cfg.report.token_warn_pct}")
    print(f"  report.token_fail_pct: {cfg.report.token_fail_pct}")
    print(f"  report.flag_at_top: {cfg.report.flag_at_top}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    scenarios = discover_scenarios(REPO_ROOT / "evals" / "scenarios")
    if not scenarios:
        print("(no scenarios)")
        return 0
    for p in scenarios:
        try:
            sc = load_scenario(p)
            print(f"  {sc.id:20s} pack={sc.pack:14s} turns={len(sc.turns)}  ({p.name})")
        except Exception as exc:
            print(f"  {p.name}  ERROR: {exc}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ccya.eval",
        description="ccya eval harness: scenario → in-process runner → judge → report",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run a scenario end-to-end")
    run.add_argument("scenario", nargs="?", default=None,
                     help="Scenario id, file path, or filename. Defaults to first found.")
    run.add_argument("--pack", default=None, help="Override scenario's pack")
    run.add_argument("--temp", type=float, default=None,
                     help="Temperature override applied to ALL LLM calls (rules/narrate/extract).")
    run.add_argument("--no-judge", action="store_true",
                     help="Skip the judge call (still writes REPORT.md without judge block).")
    run.add_argument("--packs-dir", default=None,
                     help="Override packs directory (defaults to evals/packs).")
    run.add_argument("--turns", type=int, default=None,
                     help="Run only the first N turns (default: from config, 10).")
    run.add_argument("--all", action="store_true",
                     help="Run every discovered scenario in serial (default: just default_scenario).")
    run.set_defaults(func=_cmd_run, _is_async=True)

    j = sub.add_parser("judge-only", help="Re-run the judge against a prior run dir")
    j.add_argument("run_dir", help="Path to a prior evals/runs/<ts>/ directory")
    j.set_defaults(func=_cmd_judge_only, _is_async=True)

    sub.add_parser("pack", help="Print effective eval config").set_defaults(
        func=_cmd_pack, _is_async=False
    )
    sub.add_parser("list", help="List discovered scenarios").set_defaults(
        func=_cmd_list, _is_async=False
    )

    args = parser.parse_args(argv)
    if getattr(args, "_is_async", False):
        return asyncio.run(args.func(args))  # type: ignore[no-any-return]
    return args.func(args)  # type: ignore[no-any-return]


if __name__ == "__main__":
    raise SystemExit(main())
