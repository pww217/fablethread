from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from ccya.engine.config import EngineConfig, build_engine_config
from ccya.ev.checkers import CheckerResult, list_checkers, run_checkers
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


def _build_eval_config(
    model: str | None = None,
    temp: float | None = None,
    pack_dir: Path | None = None,
) -> EngineConfig:
    raw_cfg = load_config()
    if model:
        raw_cfg.setdefault("llm", {})["model"] = model
    if temp is not None:
        for section in ("ruling", "extract", "narrate", "generate_seed"):
            raw_cfg.setdefault("llm", {}).setdefault(section, {})["temperature"] = temp
    if pack_dir is not None:
        from ccya.pack import load_pack
        pack = load_pack(str(pack_dir.name), pack_dir.parent)
        if pack.manifest.checkers:
            raw_cfg.setdefault("checkers", {}).update(pack.manifest.checkers)
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
    state["meta"]["session_name"] = scenario.id
    if scenario.seed_overrides:
        _apply_seed_overrides(state, scenario.seed_overrides)

    init_save_dir(session_dir, state)
    return session_dir


def _compute_pass_rate(checker_results: dict[str, CheckerResult]) -> float:
    """Compute pass rate as percentage of passed checkers (excluding skipped)."""
    non_skipped = {cid: r for cid, r in checker_results.items() if r.passed is not None}
    if not non_skipped:
        return 0.0
    passed = sum(1 for r in non_skipped.values() if r.passed)
    return round(passed / len(non_skipped) * 100, 1)


def _build_rubric_areas(checker_results: dict[str, CheckerResult]) -> list[dict[str, Any]]:
    """Group checker results into rubric areas."""
    RUBRIC_AREAS: dict[str, list[str]] = {
        "Ruling": ["ruling_reason_quality", "ruling_band_distribution", "ruling_intent_match"],
        "Narration": ["directive_tone_match", "beat_narrative_chain", "state_fidelity"],
        "Pacing": ["pacing_directives", "phase_transition", "climax_turn_counting",
                    "breather_enforcement", "convergence_components"],
        "State": ["location_change", "inventory_integrity", "conditions_lifecycle",
                  "location_description_consistency", "world_state_facts"],
        "Threads": ["thread_lifecycle", "thread_resolution_validity", "new_thread_validity",
                    "sanitizer_lifecycle"],
        "Arcs": ["arc_goal_updates", "arc_resolution_validity", "goal_update_validity"],
        "NPCs": ["npc_presence", "compendium_lifecycle"],
        "GM Beats": ["gm_beat_lifecycle", "beat_phase_validity"],
        "Rolls": ["roll_band_consistency"],
    }

    areas: list[dict[str, Any]] = []
    for number, (area_name, checker_ids) in enumerate(RUBRIC_AREAS.items(), 1):
        area_checkers: list[dict[str, Any]] = []
        red_flags: list[str] = []
        passed_count = 0
        total_count = 0

        for checker_id in checker_ids:
            result = checker_results.get(checker_id)
            if result is None:
                area_checkers.append({
                    "name": checker_id,
                    "status": "SKIP",
                    "detail": "",
                })
                continue

            if result.passed is None:
                status = "SKIP"
            elif result.passed:
                status = "PASS"
                passed_count += 1
            else:
                status = "FAIL"

            total_count += 1
            detail = result.detail or ""

            # Collect red flags from findings with score < 0.5
            if result.findings:
                for finding in result.findings:
                    f_score = finding.get("score", 1.0)
                    if f_score is not None and f_score < 0.5:
                        red_flags.append(finding.get("detail", finding.get("finding", "")))

            area_checkers.append({
                "name": checker_id,
                "status": status,
                "detail": detail,
            })

        areas.append({
            "number": number,
            "name": area_name,
            "passed": passed_count,
            "total": total_count,
            "checkers": area_checkers,
            "red_flags": red_flags,
        })

    return areas


def _store_checker_warnings(
    checker_results: dict[str, CheckerResult],
    events: list[dict[str, Any]],
    session_dir: Path,
) -> None:
    """Store checker findings as warning events in events.jsonl."""
    from ccya.state.chronicle import append_event

    warning_checkers = {
        "ruling_reason_quality",
        "ruling_band_distribution",
        "convergence_components",
        "world_state_facts",
        "location_description_consistency",
    }
    total_warnings = 0
    for checker_id in warning_checkers:
        result = checker_results.get(checker_id)
        if result is None or not result.findings:
            continue
        for finding in result.findings:
            warning_event = {
                "kind": "warning",
                "turn": finding.get("turn", 0),
                "checker": checker_id,
                "warning": finding.get("detail", finding.get("finding", "")),
            }
            append_event(session_dir, warning_event)
            total_warnings += 1
    if total_warnings:
        _log.info("eval: stored %d checker warnings as events", total_warnings)


def _find_latest_run(scenario_pack: str) -> dict[str, Any] | None:
    """Find the most recent previous eval run for the same pack."""
    runs_dir = Path("evals/runs")
    if not runs_dir.exists():
        return None

    import yaml as yaml_lib

    meta_files: list[Path] = []
    for group in runs_dir.iterdir():
        if not group.is_dir():
            continue
        for run in group.iterdir():
            meta_path = run / "run-meta.yaml"
            if meta_path.exists():
                meta_files.append(meta_path)

    if not meta_files:
        return None

    def _meta_mtime(p: Path) -> str:
        try:
            meta = yaml_lib.safe_load(p.read_text())
            return str(meta.get("created_at", ""))
        except Exception:
            return ""

    meta_files.sort(key=_meta_mtime, reverse=True)

    for meta_path in meta_files:
        try:
            meta = yaml_lib.safe_load(meta_path.read_text())
            if meta.get("pack") == scenario_pack and meta.get("pass_rate") is not None:
                return {
                    "path": str(meta_path.parent),
                    "date": str(meta.get("created_at", "")),
                    "pass_rate": float(meta.get("pass_rate", 0)),
                }
        except Exception:
            continue

    return None


def _run_turn_asserts(
    events: list[dict[str, Any]],
    per_turn_asserts: list[tuple[int, list[Any]]],
) -> list[dict[str, Any]]:
    """Validate per-turn structured assertions (stream/field/expected)."""
    _STREAM_MAP: dict[str, str] = {
        "ruling": "ruling",
        "extract.state": "applied",
    }

    findings: list[dict[str, Any]] = []
    for turn_num, asserts in per_turn_asserts:
        turn_ev = find_turn(events, turn_num)
        if turn_ev is None:
            continue
        for a in asserts:
            if isinstance(a, dict):
                stream = a.get("stream", "")
                field = a.get("field", "")
                expected = a.get("expected")
                min_amount = a.get("min_amount")
            else:
                stream = getattr(a, "stream", "")
                field = getattr(a, "field", "")
                expected = getattr(a, "expected", None)
                min_amount = getattr(a, "min_amount", None)

            event_key = _STREAM_MAP.get(stream)
            if event_key is None:
                findings.append({
                    "finding": f"unknown_stream:{stream}",
                    "field": field,
                    "stream": stream,
                    "detail": f"Unknown stream '{stream}', expected one of: {', '.join(_STREAM_MAP)}",
                })
                continue

            section = turn_ev.get(event_key, {})
            parts = field.split(".")
            cur: Any = section
            for part in parts:
                if isinstance(cur, dict):
                    cur = cur.get(part)
                else:
                    cur = None
                    break

            actual = cur
            detail_parts: list[str] = []

            if expected is not None:
                str_actual = str(actual) if actual is not None else ""
                if str_actual != expected:
                    detail_parts.append(f"expected={expected!r}, got={str_actual!r}")

            if min_amount is not None:
                try:
                    num_actual = int(actual) if actual is not None else 0
                except (TypeError, ValueError):
                    num_actual = 0
                if num_actual < min_amount:
                    detail_parts.append(f"expected >= {min_amount}, got={num_actual}")

            detail = "; ".join(detail_parts) if detail_parts else "ok"
            findings.append({
                "turn": turn_num,
                "finding": f"{stream}.{field}",
                "stream": stream,
                "field": field,
                "expected": expected,
                "actual": actual,
                "detail": detail,
            })
    return findings


def cmd_eval_run(
    scenario_path: Path,
    model: str | None = None,
    temp: float | None = None,
    checkers: list[str] | None = None,
    report: Path | None = None,
    auto_report: bool = False,
    llm_checkers: bool = False,
) -> None:
    import subprocess
    import time

    from jinja2 import Environment, FileSystemLoader

    scenario = load_scenario(scenario_path)
    _log.info("eval: loading scenario %s (%d turns)", scenario.id, len(scenario.turns))
    config = _build_eval_config(model=model, temp=temp)
    session_dir = _create_eval_session(scenario)
    _log.info("eval: session dir %s", session_dir)

    per_turn_asserts: list[tuple[int, list[Any]]] = []

    t0 = time.perf_counter()
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
    duration_ms = round((time.perf_counter() - t0) * 1000.0)

    events = load_events(session_dir / "events.jsonl")

    runner_checkers = checkers or [m["id"] for m in list_checkers(checker_type="deterministic")]
    checker_results: dict[str, CheckerResult] = run_checkers(runner_checkers, events, save_dir=session_dir)

    if llm_checkers:
        llm_checker_ids = [m["id"] for m in list_checkers(checker_type="llm")]
        llm_results = run_checkers(llm_checker_ids, events, save_dir=session_dir)
        checker_results.update(llm_results)

    # Store warnings as events
    _store_checker_warnings(checker_results, events, session_dir)

    # Build report if auto_report or explicit report path
    if auto_report or report:
        rubric_areas = _build_rubric_areas(checker_results)

        # Git info
        try:
            git_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()[:7]
        except Exception:
            git_sha = "unknown"
        try:
            git_branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            git_branch = "unknown"

        # Previous run comparison
        prev_run = _find_latest_run(scenario.pack)
        pass_rate = _compute_pass_rate(checker_results)
        pass_rate_delta: float = 0.0
        if prev_run and prev_run.get("pass_rate") is not None:
            pass_rate_delta = round(pass_rate - prev_run["pass_rate"], 1)

        # Render template
        template_dir = Path("evals/ev-tooling/templates")
        env = Environment(loader=FileSystemLoader(str(template_dir)), keep_trailing_newline=True)
        template = env.get_template("report.md.j2")

        report_ctx = {
            "pack": scenario.pack,
            "personality": scenario.personality,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": git_sha,
            "git_branch": git_branch,
            "actual_turns": len(scenario.turns),
            "max_turns": len(scenario.turns),
            "duration_ms": duration_ms,
            "pass_rate": pass_rate,
            "rubric_areas": rubric_areas,
            "prev_run": prev_run,
            "pass_rate_delta": pass_rate_delta,
        }

        report_text = template.render(**report_ctx)

        if auto_report:
            report_path = session_dir / "report.md"
            report_path.write_text(report_text)
            _log.info("eval: auto report written to %s", report_path)
            print(f"Report written to {report_path}")
        elif report:
            report.write_text(report_text)
            _log.info("eval: report written to %s", report)
            print(f"Report written to {report}")

    # Legacy plain-text output if neither auto_report nor report
    if not auto_report and not report:
        outputs: list[str] = []
        outputs.append(f"# Eval Report: {scenario.id}")
        outputs.append(f"- Scenario: {scenario.id}")
        outputs.append(f"- Pack: {scenario.pack}")
        outputs.append(f"- Description: {scenario.description}")
        outputs.append(f"- Turns: {len(scenario.turns)}")
        outputs.append(f"- Session: {session_dir}")
        outputs.append("")

        if checker_results:
            outputs.append("## Checker Results")
            for cid, result in checker_results.items():  # type: ignore[assignment]
                cr = cast(CheckerResult, result)
                status = "PASS" if cr.passed else "FAIL"
                score = cr.score or 0.0
                outputs.append(f"- **{cid}**: {status} (score: {score})")
            outputs.append("")

        if per_turn_asserts:
            findings = _run_turn_asserts(events, per_turn_asserts)
            outputs.append("## Turn Assertions")
            has_table = False
            for finding in findings:
                if not has_table:
                    outputs.append("| Turn | Assertion | Detail |")
                    outputs.append("|------|-----------|--------|")
                    has_table = True
                turn_num = finding.get("turn", "")
                a_id = finding.get("finding", "")
                a_detail = finding.get("detail", "")
                outputs.append(f"| {turn_num} | {a_id} | {a_detail} |")
            if not has_table:
                outputs.append("(all passed)")
            outputs.append("")

        report_text = "\n".join(outputs)
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
        print("=== Packs ===")
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
