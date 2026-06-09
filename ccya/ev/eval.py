from __future__ import annotations

import logging
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
