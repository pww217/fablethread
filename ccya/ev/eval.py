from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from ccya.engine.config import EngineConfig, build_engine_config
from ccya.ev.checkers import CheckerResult, list_checkers, run_checkers
from ccya.ev.checkers.turn_assert import turn_assert as turn_assert_checker
from ccya.ev.events import find_turn, load_events
from ccya.ev.play import EV_SAVES_DIR, play_turn
from ccya.ev.scenario import Scenario, discover_scenarios, load_scenario
from ccya.models import load_config
from ccya.state.io import _default_state, init_save_dir, load_state

_log = logging.getLogger(__name__)


def _apply_seed_overrides(state: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    for path, value in overrides.items():
        parts = path.split(".")
        target = state
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
    return state


def _build_eval_config(model: str | None = None, temp: float | None = None) -> EngineConfig:
    raw_cfg = load_config()
    if model:
        raw_cfg.setdefault("llm", {})["model"] = model
    if temp is not None:
        for section in ("ruling", "extract", "narrate", "generate_seed"):
            raw_cfg.setdefault("llm", {}).setdefault(section, {})["temperature"] = temp
    config = build_engine_config(raw_cfg)
    config.sanitize_every = 0
    return config


def _create_eval_session(scenario: Scenario) -> Path:
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    rand = uuid.uuid4().hex[:6]
    session_name = f"eval_{scenario.id}_{ts}_{rand}"
    session_dir = EV_SAVES_DIR / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    state = _default_state()
    state["meta"]["game_name"] = scenario.id
    if scenario.seed_overrides:
        _apply_seed_overrides(state, scenario.seed_overrides)

    init_save_dir(session_dir, state)
    return session_dir


def cmd_eval_run(
    scenario_path: Path,
    model: str | None = None,
    temp: float | None = None,
    checkers: list[str] | None = None,
    report: Path | None = None,
) -> None:
    scenario = load_scenario(scenario_path)
    _log.info("eval: loading scenario %s (%d turns)", scenario.id, len(scenario.turns))
    config = _build_eval_config(model=model, temp=temp)
    session_dir = _create_eval_session(scenario)
    _log.info("eval: session dir %s", session_dir)

    per_turn_asserts: list[tuple[int, list[Any]]] = []

    for i, turn_data in enumerate(scenario.turns):
        state = load_state(session_dir)
        _log.info("eval: playing turn %d/%d", i + 1, len(scenario.turns))
        result = play_turn(
            turn_data.input,
            state,
            config,
            session_dir,
        )
        turn_num = result.get("turn", 0)
        if turn_data.asserts:
            per_turn_asserts.append((turn_num, turn_data.asserts))

    events = load_events(session_dir / "events.jsonl")

    outputs: list[str] = []
    outputs.append(f"# Eval Report: {scenario.id}")
    outputs.append(f"- Scenario: {scenario.id}")
    outputs.append(f"- Pack: {scenario.pack}")
    outputs.append(f"- Description: {scenario.description}")
    outputs.append(f"- Turns: {len(scenario.turns)}")
    outputs.append(f"- Session: {session_dir}")
    outputs.append("")

    runner_checkers = checkers or [m["id"] for m in list_checkers(checker_type="deterministic")]
    checker_results: dict[str, CheckerResult] = run_checkers(runner_checkers, events, save_dir=session_dir)

    if checker_results:
        outputs.append("## Checker Results")
        for cid, result in checker_results.items():  # type: ignore[assignment]
            cr = cast(CheckerResult, result)
            status = "PASS" if cr.passed else "FAIL"
            score = cr.score or 0.0
            outputs.append(f"- **{cid}**: {status} (score: {score})")
        outputs.append("")

    if per_turn_asserts:
        outputs.append("## Turn Assertions")
        has_table = False
        for turn_num, asserts in per_turn_asserts:
            turn_ev = find_turn(events, turn_num)
            if turn_ev is None:
                continue
            result = turn_assert_checker([turn_ev], asserts)
            for finding in result.findings:
                if not has_table:
                    outputs.append("| Turn | Assertion | Detail |")
                    outputs.append("|------|-----------|--------|")
                    has_table = True
                a_id = finding.get("finding", "")
                a_detail = finding.get("detail", "")
                outputs.append(f"| {turn_num} | {a_id} | {a_detail} |")
        if not has_table:
            outputs.append("(all passed)")
        outputs.append("")

    report_text = "\n".join(outputs)

    if report:
        report.write_text(report_text)
        _log.info("eval: report written to %s", report)
        print(f"Report written to {report}")
    else:
        print(report_text)


def _load_run_events(run_dir: Path) -> list[dict[str, Any]]:
    events_path = run_dir / "events.jsonl"
    if events_path.exists():
        return load_events(events_path)

    # Multi-pack run: merge events from subdirectories
    subdirs = sorted(d for d in run_dir.iterdir() if d.is_dir())
    if not subdirs:
        print(f"Error: no events.jsonl found in {run_dir}", file=sys.stderr)
        sys.exit(1)

    all_events: list[dict[str, Any]] = []
    for subdir in subdirs:
        sub_events_path = subdir / "events.jsonl"
        if sub_events_path.exists():
            all_events.extend(load_events(sub_events_path))

    if not all_events:
        print(f"Error: no events.jsonl found in any subdirectory of {run_dir}", file=sys.stderr)
        sys.exit(1)

    return all_events


def _run_eval_checkers(events: list[dict[str, Any]], checkers: list[str] | None = None) -> dict[str, CheckerResult]:
    runner_checkers = checkers or [m["id"] for m in list_checkers(checker_type="deterministic")]
    return run_checkers(runner_checkers, events)


def cmd_eval_compare(
    baseline_dir: Path,
    current_dir: Path,
    checkers: list[str] | None = None,
) -> None:
    baseline_dir = baseline_dir.resolve()
    current_dir = current_dir.resolve()

    print(f"=== Eval Compare: {baseline_dir.name} → {current_dir.name} ===")
    print()

    baseline_events = _load_run_events(baseline_dir)
    current_events = _load_run_events(current_dir)

    baseline_results = _run_eval_checkers(baseline_events, checkers)
    current_results = _run_eval_checkers(current_events, checkers)

    all_ids = sorted(set(list(baseline_results.keys()) + list(current_results.keys())))

    # Column widths
    id_w = max(len(cid) for cid in all_ids) + 2
    base_w = 8
    curr_w = 8
    diff_w = 12

    header = f"{'Checker':<{id_w}} | {'Baseline':^{base_w}} | {'Current':^{curr_w}} | {'Change':^{diff_w}}"
    sep = f"{'─' * id_w}┼{'─' * (base_w + 2)}┼{'─' * (curr_w + 2)}┼{'─' * (diff_w + 2)}"

    print(header)
    print(sep)

    improvements = 0
    regressions = 0
    unchanged = 0

    for cid in all_ids:
        b = baseline_results.get(cid)
        c = current_results.get(cid)

        b_status = f"{'PASS' if b and b.passed else 'FAIL'}" if b else "N/A"
        c_status = f"{'PASS' if c and c.passed else 'FAIL'}" if c else "N/A"

        b_score = f"{b.score:.2f}" if b and b.score is not None else "—"
        c_score = f"{c.score:.2f}" if c and c.score is not None else "—"

        b_str = f"{b_status} ({b_score})"
        c_str = f"{c_status} ({c_score})"

        if b and c:
            if b.passed and not c.passed:
                change = "REGRESSION"
                regressions += 1
            elif not b.passed and c.passed:
                change = "IMPROVED"
                improvements += 1
            else:
                change = "unchanged"
                unchanged += 1
        elif b and not c:
            change = "removed"
        elif c and not b:
            change = "added"
        else:
            change = "—"

        print(f"{cid:<{id_w}} | {b_str:^{base_w}} | {c_str:^{curr_w}} | {change}")

    print()
    print(f"Summary: {improvements} improved, {regressions} regressions, {unchanged} unchanged")

    if regressions > 0:
        print()
        print("=== Regressions ===")
        for cid in all_ids:
            b = baseline_results.get(cid)
            c = current_results.get(cid)
            if b and c and b.passed and not c.passed:
                b_score = f"{b.score:.2f}" if b.score is not None else "—"
                c_score = f"{c.score:.2f}" if c.score is not None else "—"
                print(f"  {cid}: {b_score} → {c_score}")
                if c.findings:
                    for f in c.findings[:3]:
                        f_turn = f.get("turn", "?")
                        f_detail = f.get("detail", f.get("finding", ""))
                        print(f"    T{f_turn}: {f_detail}")

    if improvements > 0:
        print()
        print("=== Improvements ===")
        for cid in all_ids:
            b = baseline_results.get(cid)
            c = current_results.get(cid)
            if b and c and not b.passed and c.passed:
                b_score = f"{b.score:.2f}" if b.score is not None else "—"
                c_score = f"{c.score:.2f}" if c.score is not None else "—"
                print(f"  {cid}: {b_score} → {c_score}")

    # Per-pack comparison if multi-pack runs detected
    baseline_packs = set()
    current_packs = set()
    for ev in baseline_events:
        pack = ev.get("pack") or (ev.get("meta") or {}).get("pack")
        if pack:
            baseline_packs.add(pack)
    for ev in current_events:
        pack = ev.get("pack") or (ev.get("meta") or {}).get("pack")
        if pack:
            current_packs.add(pack)

    if baseline_packs or current_packs:
        print()
        print(f"=== Packs ===")
        print(f"  Baseline: {', '.join(sorted(baseline_packs)) if baseline_packs else '(none)'}")
        print(f"  Current:  {', '.join(sorted(current_packs)) if current_packs else '(none)'}")


def cmd_eval_list() -> None:
    scenarios = discover_scenarios()
    if not scenarios:
        print("No YAML scenarios found in packs/")
        return
    print("Available scenarios:")
    print()
    for sp in scenarios:
        try:
            sc = load_scenario(sp)
            print(f"  {sp.name}")
            print(f"    id: {sc.id}")
            print(f"    pack: {sc.pack}")
            print(f"    description: {sc.description}")
            print(f"    turns: {len(sc.turns)}")
            print()
        except Exception as e:
            print(f"  {sp.name}: error: {e}")
            print()
