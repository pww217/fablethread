from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from ccya.ev.checkers import list_checkers, run_checkers
from ccya.ev.checkers._llm import _load_checker_model, _unload_checker_model
from ccya.ev.checkers.llm_checkers import set_checker_config
from ccya.ev.events import find_turn

_log = logging.getLogger(__name__)


def cmd_check(
    events: list[dict[str, Any]],
    turn: int | None = None,
    checker_ids: list[str] | None = None,
    all_checkers: bool = False,
    include_llm: bool = False,
    save_dir: Path | None = None,
    checker_model: str | None = None,
) -> None:
    if checker_ids:
        checker_list = checker_ids
    elif all_checkers:
        checker_list = [m["id"] for m in list_checkers(checker_type="deterministic")]
        if include_llm:
            checker_list.extend(m["id"] for m in list_checkers(checker_type="llm"))
    else:
        print("Error: specify checkers or --all", file=sys.stderr)
        sys.exit(1)

    # Load checker model if running LLM checkers
    if include_llm:
        from ccya.engine.config import build_engine_config
        from ccya.models import load_config
        raw_cfg = load_config()
        if checker_model:
            raw_cfg.setdefault("llm", {})["model"] = checker_model
        config = build_engine_config(raw_cfg)
        set_checker_config(config)
        try:
            _load_checker_model(config)
        except Exception as exc:
            print(f"Warning: Failed to load checker model: {exc}", file=sys.stderr)
            # Continue without LLM checkers
            checker_list = [cid for cid in checker_list if not any(
                m["id"] == cid and m["type"] == "llm"
                for m in list_checkers()
            )]
            _log.warning("LLM checkers removed from list due to model load failure")

    _log.info("check: %d checkers, turn=%s", len(checker_list), turn)

    try:
        if turn is not None:
            turn_ev = find_turn(events, turn)
            if turn_ev is None:
                print(f"Turn {turn} not found", file=sys.stderr)
                sys.exit(1)
            results = run_checkers(checker_list, [turn_ev], save_dir=save_dir)
            _print_results({turn: results})
        else:
            per_turn: dict[int, dict[str, Any]] = {}
            seen: set[int] = set()
            for ev in events:
                t = ev.get("turn")
                if t is not None and t not in seen:
                    seen.add(t)
                    turn_ev = find_turn(events, t)
                    if turn_ev is not None:
                        per_turn[t] = run_checkers(checker_list, [turn_ev], save_dir=save_dir)
            _print_results(per_turn)
    finally:
        if include_llm:
            _unload_checker_model()


def _print_results(per_turn: dict[int, dict[str, Any]]) -> None:
    first = True
    for turn_num in sorted(per_turn):
        results = per_turn[turn_num]
        for cid, result in results.items():
            status = "PASS" if result.passed else "FAIL"
            score = result.score or 0.0
            print(f"## {cid}: {status} (score: {score})")

        has_findings = any(r.findings for r in results.values())
        if has_findings:
            print()
            print("| Turn | Finding | Detail |")
            print("|------|---------|--------|")
            for cid, result in results.items():
                for f in result.findings:
                    f_id = f.get("finding", f.get("id", ""))
                    f_detail = f.get("detail", "")
                    print(f"| {turn_num} | {f_id} | {f_detail} |")
            print()

        if not first:
            print()
        first = False
