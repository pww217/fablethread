from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from ccya.ev.checkers import CheckerResult, list_checkers, run_checkers
from ccya.ev.events import find_turn

_log = logging.getLogger(__name__)

# Checker domain groupings for summary output
_CHECKER_DOMAINS: dict[str, list[str]] = {
    "Pacing": ["pacing_directives", "phase_transition", "climax_turn_counting", "breather_enforcement", "roll_band_consistency", "phase_transition_signals", "convergence_recompute", "curtain_call", "directive_beat_alignment"],
    "Threads": ["thread_lifecycle", "sanitizer_lifecycle", "thread_resolution_validity", "new_thread_validity", "arc_resolution_validity"],
    "Beats": ["gm_beat_lifecycle", "beat_phase_validity"],
    "Goals": ["arc_goal_updates", "goal_update_validity"],
    "State": ["location_change", "inventory_integrity", "conditions_lifecycle", "npc_presence", "compendium_lifecycle", "location_description_consistency", "world_state_facts"],
    "Ruling": ["ruling_reason_quality", "ruling_band_distribution", "ruling_intent_match"],
}

def _get_domain(checker_id: str) -> str:
    for domain, ids in _CHECKER_DOMAINS.items():
        if checker_id in ids:
            return domain
    return "Other"


def cmd_check(
    events: list[dict[str, Any]],
    turn: int | None = None,
    checker_ids: list[str] | None = None,
    all_checkers: bool = False,
    include_llm: bool = False,
    save_dir: Path | None = None,
    checker_model: str | None = None,
    list_only: bool = False,
    verbose: bool = False,
    pack_dir: Path | None = None,
) -> None:
    if list_only:
        _print_checker_list()
        return

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
        if pack_dir is not None:
            from ccya.pack import load_pack
            pack = load_pack(str(pack_dir.name), pack_dir.parent)
            if pack.manifest.checkers:
                raw_cfg.setdefault("checkers", {}).update(pack.manifest.checkers)
        config = build_engine_config(raw_cfg)
    else:
        config = None

    _log.info("check: %d checkers, turn=%s", len(checker_list), turn)

    if turn is not None:
        turn_ev = find_turn(events, turn)
        if turn_ev is None:
            print(f"Turn {turn} not found", file=sys.stderr)
            sys.exit(1)
        results = run_checkers(checker_list, events, config=config, save_dir=save_dir)
        _print_results({turn: results}, verbose=verbose)
    else:
        # Run checkers ONCE against full events list (not per-turn)
        results = run_checkers(checker_list, events, config=config, save_dir=save_dir)
        _print_all_summary(results, verbose=verbose)


def _print_checker_list() -> None:
    print("Registered checkers:")
    for meta in list_checkers():
        print(f"  {meta['id']} ({meta['type']}): {meta['description']}")


def _print_all_summary(results: dict[str, CheckerResult], verbose: bool = False) -> None:
    pass_count = sum(1 for r in results.values() if r.passed)
    total = len(results)
    avg_score = sum(r.score or 0.0 for r in results.values()) / total if total else 0.0
    fail_ids = [cid for cid, r in results.items() if not r.passed]

    print(f"Checkers: {pass_count}/{total} PASS ({pass_count/total*100:.1f}%)  |  Average score: {avg_score:.2f}")
    if fail_ids:
        print(f"FAIL: {', '.join(fail_ids)}")

    # Domain breakdown
    domains: dict[str, tuple[int, int, list[str]]] = {}
    for cid, result in results.items():
        domain = _get_domain(cid)
        passed, total_d, fails = domains.get(domain, (0, 0, []))
        if result.passed:
            passed += 1
        else:
            fails.append(cid)
        total_d += 1
        domains[domain] = (passed, total_d, fails)

    for domain in sorted(domains):
        passed, total_d, fails = domains[domain]
        if fails:
            print(f"  {domain:<12}: {passed}/{total_d} FAIL ({', '.join(fails)})")
        else:
            print(f"  {domain:<12}: {passed}/{total_d} PASS")

    if verbose:
        print()
        for cid in sorted(results):
            result = results[cid]
            status = "PASS" if result.passed else "FAIL"
            score = result.score or 0.0
            print(f"## {cid}: {status} (score: {score})")
            if result.findings:
                for f in result.findings:
                    f_id = f.get("finding", f.get("id", ""))
                    f_detail = f.get("detail", "")
                    f_turn = f.get("turn", "")
                    print(f"  T{f_turn}: {f_id} — {f_detail}")


def _print_results(per_turn: dict[int, dict[str, Any]], verbose: bool = False) -> None:
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
                    f_turn = f.get("turn", turn_num)
                    print(f"| {f_turn} | {f_id} | {f_detail} |")
            print()

        if not first:
            print()
        first = False
