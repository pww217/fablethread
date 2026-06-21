from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal, TypedDict, cast

from ccya.ev.events import filter_turn_events, load_current_state, extract_field

_log = logging.getLogger(__name__)


@dataclass
class CheckerResult:
    checker_id: str
    passed: bool | None
    score: float | None
    detail: str
    findings: list[dict[str, Any]] = field(default_factory=list)
    ms: float = 0.0


CHECKER_META = "__checker_meta__"


class CheckerMeta(TypedDict):
    id: str
    type: Literal["deterministic", "llm"]
    requires_fields: list[str]
    description: str
    needs_non_turn_events: bool
    needs_state: bool


_checker_registry: dict[str, Callable[..., Any]] = {}


def register_checker(
    id: str,
    type: Literal["deterministic", "llm"],
    requires_fields: list[str],
    description: str,
    needs_non_turn_events: bool = False,
    needs_state: bool = False,
) -> Callable[..., Any]:
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        setattr(fn, CHECKER_META, CheckerMeta(
            id=id,
            type=type,
            requires_fields=requires_fields,
            description=description,
            needs_non_turn_events=needs_non_turn_events,
            needs_state=needs_state,
        ))
        _checker_registry[id] = fn
        return fn
    return decorator


def run_checker(checker_id: str, events: list[dict[str, Any]], save_dir: Path | None = None) -> CheckerResult:
    fn = _checker_registry.get(checker_id)
    if fn is None:
        return CheckerResult(checker_id=checker_id, passed=None, score=None, detail=f"unknown checker: {checker_id}")

    meta: CheckerMeta | None = getattr(fn, CHECKER_META, None)
    if meta is None:
        return CheckerResult(checker_id=checker_id, passed=None, score=None, detail=f"checker '{checker_id}' has no metadata")

    filtered = events
    if not meta.get("needs_non_turn_events", False):
        filtered = filter_turn_events(events)

    for field_dotpath in meta.get("requires_fields", []):
        found = False
        for ev in filtered:
            if extract_field(ev, field_dotpath) is not None:
                found = True
                break
        if not found:
            _log.warning("required field '%s' not found in any event for checker '%s'", field_dotpath, checker_id)
            return CheckerResult(
                checker_id=checker_id, passed=None, score=None,
                detail=f"required field '{field_dotpath}' not found in any event",
            )

    state: dict[str, Any] | None = None
    if meta.get("needs_state", False):
        if save_dir is None:
            return CheckerResult(
                checker_id=checker_id, passed=None, score=None,
                detail="checker requires state but no save_dir provided",
            )
        state = load_current_state(save_dir)

    t0 = time.perf_counter()
    if meta.get("needs_state", False):
        raw = fn(filtered, state)
    else:
        raw = fn(filtered)
    result = cast(CheckerResult, raw)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    result.ms = elapsed_ms
    return result


def run_checkers(checker_ids: list[str], events: list[dict[str, Any]], save_dir: Path | None = None) -> dict[str, CheckerResult]:
    return {cid: run_checker(cid, events, save_dir=save_dir) for cid in checker_ids}


def list_checkers(checker_type: str | None = None) -> list[CheckerMeta]:
    results: list[CheckerMeta] = []
    for fn in _checker_registry.values():
        meta: CheckerMeta | None = getattr(fn, CHECKER_META, None)
        if meta is None:
            continue
        if checker_type is not None and meta.get("type") != checker_type:
            continue
        results.append(meta)
    return results


from . import gm_beat, inventory, conditions, threads, arc_goals, npc_presence, pacing, sanitizer, llm_checkers, phase_transition, climax_turn_counting, breather_enforcement, roll_band_consistency, thread_resolution_validity, new_thread_validity, compendium_lifecycle, beat_phase_validity, arc_resolution_validity, goal_update_validity  # noqa: E402, F401
