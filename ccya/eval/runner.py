"""In-process eval runner.

Drives a scenario end-to-end against an isolated save-dir. Calls run_turn()
directly — no FastAPI, no SSE. Copies events.jsonl to the run directory as the
canonical eval data source. Does not invoke the judge or generate the report.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from ccya.engine import EngineConfig, build_engine_config, run_turn
from ccya.engine.config import _validate_compactor_config
from ccya.eval.config import EvalConfig
from ccya.eval.engine_mirror import (
    MOMENTUM_DELTA,
    MOMENTUM_MAX,
    MOMENTUM_MIN,
    THREAD_ARC_DEMOTE_AGE,
    URGENCY_LEVELS,
)
from ccya.eval.scenario import Scenario, TurnAssert
from ccya.models import TurnResult, load_config
from ccya.pack import load_pack
from ccya.state import init_save_dir, load_state, save_state
from ccya.state.chronicle import append_event
from ccya.eval.universal_asserts import run_all_universal_asserts

_log = logging.getLogger(__name__)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
"""Absolute path to the ccya repo root (the dir containing pyproject.toml)."""

PROMPTS_DIR = REPO_ROOT / "ccya" / "prompts"
"""Jinja prompt templates directory — passed to run_turn() so engine can find them."""


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class TurnRecord:
    """Per-turn observations the runner captured.

    The bulky stuff (rendered prompts, raw extractor outputs, applied deltas) is
    in events.jsonl; this record just tracks runner-level metadata.
    """

    turn_number: int
    """1-indexed position in the scenario (NOT the engine's state.meta.turn)."""
    input: str
    phase: str = ""
    expects: list[str] = field(default_factory=list)
    duration_s: float = 0.0
    error: str | None = None
    """If the engine yielded `("error", ...)` we capture it here. None on success."""
    engine_turn_number: int = 0
    """state.meta.turn AFTER this turn ran."""
    outcome_summary: str = ""
    narrative_chars: int = 0
    rules_parse_failures: int = 0
    """Number of rules parse failures (model returned invalid IntentEnvelope)."""
    extract_parse_failures: int = 0
    """Number of extract parse failures (model returned invalid JSON for a stream)."""
    assert_results: list[dict[str, Any]] = field(default_factory=list)
    """Auto-checker results: [{assertion, passed, detail}]."""


@dataclass
class RunResult:
    scenario_id: str
    pack: str
    model: str
    temperature_override: float | None
    started_at: str
    finished_at: str
    save_dir: str
    output_dir: str
    events_jsonl_path: str
    state_yaml_path: str
    trace_md_path: str = ""
    judge_md_path: str = ""
    turns: list[TurnRecord] = field(default_factory=list)
    total_errors: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _build_engine_config(
    eval_cfg: EvalConfig, game_config_path: Path | None = None
) -> EngineConfig:
    """Build EngineConfig from config.yaml, applying temperature override."""
    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    if not cfg_path.exists():
        raise FileNotFoundError(f"game config not found: {cfg_path}")
    cfg = load_config(cfg_path)
    return build_engine_config(
        cfg,
        temperature_override=eval_cfg.inference.temperature_override,
    )


_EVAL_PACK_STARTING_CONDITIONS = [
    {
        "id": "bruised_ribs",
        "label": "bruised ribs",
        "description": "A hard fall on the bridge two days ago left a deep, aching bruise along the right ribcage.",
        "added_turn": 8,
    },
    {
        "id": "low_morale",
        "label": "low morale",
        "description": "Twelve days on the road, two days behind schedule, and an old debt waiting at the end of it.",
        "added_turn": 10,
    },
]


def _patch_eval_pack_starting_state(
    save_dir: Path, pack_id: str, seed_overrides: dict[str, Any] | None = None
) -> None:
    """Apply runtime-only seed adjustments that SeedState's schema can't express.

    Currently only affects eval-pack: adds two structured Condition objects with
    explicit `added_turn` that SeedPC.conditions (list[str]) cannot represent.
    No-op for any other pack.

    If `seed_overrides` is provided, applies dotpath overrides on top of the
    pack seed state (e.g. {"meta.momentum": 3, "arc.threads": [...]}).
    """
    if pack_id == "eval-pack" or seed_overrides:
        state = load_state(save_dir)
        if pack_id == "eval-pack":
            state["pc"]["conditions"] = list(_EVAL_PACK_STARTING_CONDITIONS)
        if seed_overrides:
            for dotpath, value in seed_overrides.items():
                _apply_dotpath(state, dotpath, value)
        save_state(save_dir, state)


def _apply_dotpath(obj: dict[str, Any], path: str, value: Any) -> None:
    """Set obj[a][b][c] = value for dotpath 'a.b.c'."""
    parts = path.split(".")
    for part in parts[:-1]:
        obj = obj.setdefault(part, {})
    obj[parts[-1]] = value


def _ensure_runs_dir(runs_dir: Path) -> None:
    runs_dir.mkdir(parents=True, exist_ok=True)


def _update_latest_symlink(runs_dir: Path, target: Path) -> None:
    """Point evals/runs/latest at target/. Replace any existing symlink atomically."""
    link = runs_dir / "latest"
    rel_target = os.path.relpath(target, start=runs_dir)
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(rel_target, target_is_directory=True)


# ---------------------------------------------------------------------------
# Auto-checker: verify structured asserts against events.jsonl
# ---------------------------------------------------------------------------


def _check_asserts(
    asserts: list[TurnAssert],
    event: dict[str, Any],
) -> list[dict[str, Any]]:
    """Check structured assertions against a single event from events.jsonl.

    Returns a list of dicts: [{assertion, passed, detail}].
    """
    _VALID_STREAMS = frozenset(("ruling", "extract.state", "extract.scene", "storytell.extract", "extract", "state_yaml"))
    results: list[dict[str, Any]] = []
    for a in asserts:
        passed = False
        detail = ""

        if a.stream not in _VALID_STREAMS:
            results.append({
                "assertion": f"{a.stream}.{a.field}",
                "passed": False,
                "detail": f"unknown stream '{a.stream}' (valid: {', '.join(sorted(_VALID_STREAMS))})",
            })
            continue

        if a.stream == "ruling":
            ruling = event.get("ruling") or {}
            if a.field == "rolled":
                val = ruling.get("rolled", False)
                passed = (val == (a.expected == "true"))
                detail = f"rolled={val}"
            elif a.field == "skill":
                val = ruling.get("skill", "")
                passed = val == a.expected
                detail = f"skill={val!r} (expected {a.expected!r})"
            elif a.field == "difficulty":
                val = ruling.get("difficulty", "")
                passed = val == a.expected
                detail = f"difficulty={val!r} (expected {a.expected!r})"
            elif a.field == "band":
                val = ruling.get("band", "")
                passed = val == a.expected
                detail = f"band={val!r} (expected {a.expected!r})"
            elif a.field == "intent_verb":
                val = ruling.get("intent_verb", "")
                passed = val == a.expected
                detail = f"intent_verb={val!r} (expected {a.expected!r})"

        elif a.stream == "extract.state":
            applied = event.get("applied") or {}
            if a.field == "inventory_remove":
                removes = applied.get("inventory_remove") or []
                found = None
                for item in removes:
                    if isinstance(item, dict) and item.get("id") == a.expected:
                        found = item
                        break
                if found:
                    amt = found.get("amount", 0)
                    passed = amt >= (a.min_amount or 1)
                    detail = f"inventory_remove[{a.expected}] amount={amt}"
                else:
                    passed = False
                    detail = f"inventory_remove[{a.expected}] not found"

            elif a.field == "inventory_add":
                adds = applied.get("inventory_add") or []
                found = None
                for item in adds:
                    if isinstance(item, dict) and item.get("id") == a.expected:
                        found = item
                        break
                passed = found is not None
                detail = f"inventory_add[{a.expected}] {'found' if found else 'not found'}"

            elif a.field == "pc_condition_add":
                conds = applied.get("pc_condition_add") or []
                found = None
                for c in conds:
                    if isinstance(c, dict) and c.get("id") == a.expected:
                        found = c
                        break
                passed = found is not None
                detail = f"pc_condition_add[{a.expected}] {'found' if found else 'not found'}"

            elif a.field == "pc_condition_remove":
                conds = applied.get("pc_condition_remove") or []
                ids = [c.get("id") for c in conds if isinstance(c, dict)]
                passed = a.expected in ids
                detail = f"pc_condition_remove[{a.expected}] {'found' if passed else 'not found'}"

        elif a.stream == "extract.scene":
            applied = event.get("applied") or {}
            if a.field == "scene_tags":
                tags = applied.get("scene_tags") or []
                passed = a.expected in tags
                detail = f"scene_tags[{a.expected}] {'found' if passed else 'not found'}"

        elif a.stream == "storytell.extract":
            applied = event.get("applied") or {}
            output = ((event.get("extraction") or {}).get("storytell") or {}).get("output") or {}
            if a.field == "thread_advance":
                threads = output.get("thread_advance") or []
                passed = a.expected in threads
                detail = f"thread_advance[{a.expected}] {'found' if passed else 'not found'}"

            elif a.field == "thread_resolve":
                resolutions = output.get("thread_resolve") or []
                resolved_ids = [r.get("id", "") for r in resolutions if isinstance(r, dict)]
                passed = a.expected in resolved_ids
                detail = f"thread_resolve[{a.expected}] {'found' if passed else 'not found'} (resolved: {resolved_ids[:5]})"

            elif a.field == "thread_add":
                thread = output.get("thread_add") or {}
                tid = thread.get("id", "") if isinstance(thread, dict) else ""
                passed = a.expected == tid
                detail = f"thread_add[{a.expected}] {'found' if passed else 'not found'} (actual: {tid})"

        elif a.stream == "extract":
            extraction = event.get("extraction") or {}
            if a.field.startswith("attempts:"):
                stream_name = a.field.split(":", 1)[1]
                ex = extraction.get(stream_name) or {}
                attempts = ex.get("attempts", 0)
                passed = attempts >= (a.min_amount or 1)
                detail = f"{stream_name} attempts={attempts}"
            elif a.field == "skipped:scene":
                ex = extraction.get("scene") or {}
                passed = bool(ex.get("skipped"))
                detail = f"scene skipped={passed}"
            elif a.field == "skipped:state":
                ex = extraction.get("state") or {}
                passed = bool(ex.get("skipped"))
                detail = f"state skipped={passed}"

        elif a.stream == "state_yaml":
            state_snap = event.get("state_snapshot") or {}
            if a.field == "pending_gm_beat.present":
                beat = (state_snap.get("meta") or {}).get("pending_gm_beat")
                passed = beat is not None
                detail = f"pending_gm_beat={'present' if passed else 'absent'}"
            elif a.field == "pending_gm_beat.absent":
                beat = (state_snap.get("meta") or {}).get("pending_gm_beat")
                passed = beat is None
                detail = f"pending_gm_beat={'present' if beat else 'absent'}"

        results.append({
            "assertion": f"{a.stream}.{a.field}",
            "passed": passed,
            "detail": detail,
        })

    return results


def _extract_parse_failures(events: list[dict[str, Any]]) -> list[tuple[int, int, int]]:
    """Extract per-turn parse failure counts from events.

    Returns list of (turn_number, rules_parse_failures, extract_parse_failures).
    """
    results: list[tuple[int, int, int]] = []
    for ev in events:
        turn = int(ev.get("turn", 0))
        ruling = ev.get("ruling") or {}

        # Rules parse failures: if rolled=False but the event has a rules key,
        # it means the rules call defaulted to no-roll after parse failures.
        # We can't directly know how many failures occurred, but we know at
        # least one happened if rolled=False and there's a rules key.
        rules_failures = 0
        if not ruling.get("rolled") and "ruling_prompt" in ev:
            # Check if the ruling_prompt output contains validation errors
            output = ev.get("ruling_prompt", {}).get("output", "")
            if "check.skill" in output or "check.difficulty" in output:
                rules_failures = 2  # max retries = 2

        # Extract parse failures: count retry_errors across all streams
        extract_failures = 0
        extraction = ev.get("extraction") or {}
        for sub in ("scene", "state", "storytell"):
            ex = extraction.get(sub) or {}
            retry_errors = ex.get("retry_errors") or []
            extract_failures += len(retry_errors)

        results.append((turn, rules_failures, extract_failures))

    return results


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def run_scenario(
    scenario: Scenario,
    *,
    eval_cfg: EvalConfig,
    packs_dirs: list[Path],
    runs_dir: Path | None = None,
    save_dir: Path | None = None,
    gate: bool = False,
) -> RunResult:
    """Execute scenario end-to-end. Returns a RunResult; writes artifacts to disk.

    Args:
      scenario: parsed Scenario (from load_scenario()).
      eval_cfg: parsed EvalConfig (from load_eval_config()).
      packs_dirs: ordered list of directories to search for the pack.
      runs_dir: where to create the timestamped run dir. Defaults to
        eval_cfg.runs_dir resolved relative to REPO_ROOT.
      save_dir: isolated save-dir for this run. Defaults to a fresh subdir under
        eval_cfg.default_save_root.

    Side effects:
      - Creates <runs_dir>/<ts>/ with REPORT.md, <scenario>.trace.md,
        <scenario>.judge.md, and artifacts/<scenario>.events.jsonl,
        artifacts/<scenario>.run.json.
      - Updates <runs_dir>/latest symlink.
      - Reads/writes <save_dir>/.

    Does NOT invoke judge or generate report.
    """
    from ccya.eval.pack_utils import resolve_pack_path
    pack_path = resolve_pack_path(scenario.pack, packs_dirs)
    pack = load_pack(scenario.pack, pack_path.parent)
    if pack.seed is None:
        raise ValueError(
            f"scenario.pack={scenario.pack!r} is not static (no seed). "
            "Eval harness only supports static packs."
        )

    ts = _utc_ts()
    runs_dir = (runs_dir or (REPO_ROOT / eval_cfg.runs_dir)).resolve()
    _ensure_runs_dir(runs_dir)
    output_dir = Path(tempfile.mkdtemp(dir=str(runs_dir), prefix=f"{ts}_"))

    save_root = Path(eval_cfg.default_save_root).expanduser()
    save_dir = (save_dir or (save_root / ts / "save")).resolve()
    if save_dir.exists():
        shutil.rmtree(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    seed = pack.seed.model_dump(mode="json")
    init_save_dir(save_dir, seed)
    _patch_eval_pack_starting_state(save_dir, pack.manifest.id, scenario.seed_overrides)

    metadata_event = {
        "__metadata__": True,
        "pack_id": pack.manifest.id,
        "pack_name": pack.manifest.name,
        "pack_style": pack.style_text,
        "narrator_rules": pack.scenario.narrator_rules if pack.scenario else [],
        "world_factions": [f.model_dump() for f in (pack.scenario.factions if pack.scenario else [])],
        "world_locations": [loc.model_dump() for loc in (pack.scenario.locations if pack.scenario else [])],
        "seed_state": seed,
        "engine_constants": {
            "thread_arc_demote_age": THREAD_ARC_DEMOTE_AGE,
            "urgency_levels": list(URGENCY_LEVELS),
            "momentum_min": MOMENTUM_MIN,
            "momentum_max": MOMENTUM_MAX,
            "momentum_delta": dict(MOMENTUM_DELTA),
        },
        "scenario_id": scenario.id,
        "scenario_description": scenario.description,
    }
    append_event(save_dir, metadata_event)

    engine_config = _build_engine_config(eval_cfg)
    _validate_compactor_config(engine_config)

    started_at = datetime.now(timezone.utc).isoformat()
    turn_records: list[TurnRecord] = []
    state_snapshots: list[dict[str, Any]] = []
    total_errors = 0

    _log.debug("starting run: scenario=%s pack=%s model=%s turns=%d", scenario.id, scenario.pack, engine_config.model, len(scenario.turns))

    for idx, turn in enumerate(scenario.turns, start=1):
        record = TurnRecord(
            turn_number=idx,
            input=turn.input,
            phase=turn.phase,
            expects=list(turn.expects),
        )
        _log.debug("turn %d/%d: %s", idx, len(scenario.turns), turn.input[:120])
        t0 = time.monotonic()
        result_obj: TurnResult | None = None
        try:
            async for kind, payload in run_turn(
                save_dir,
                turn.input,
                config=engine_config,
                template_dir=str(PROMPTS_DIR),
                pack_style=pack.style_text,
                pack_name_locales=pack.manifest.name_locales or [],
                pack_narrator_rules=pack.scenario.narrator_rules if pack.scenario else [],
                pack_world_rules=pack.scenario.world_rules if pack.scenario else [],
                pack_factions=[f.model_dump() for f in (pack.scenario.factions if pack.scenario else [])],
                pack_locations=[loc.model_dump() for loc in (pack.scenario.locations if pack.scenario else [])],
            ):
                if kind == "complete":
                    result_obj = payload
        except Exception as exc:
            record.error = f"exception: {exc!r}"
            total_errors += 1
            _log.debug("turn %d: exception: %s", idx, exc)
        record.duration_s = time.monotonic() - t0
        if result_obj is None:
            record.error = "no complete event from engine"
            total_errors += 1

        if result_obj is not None:
            record.engine_turn_number = result_obj.turn
            record.outcome_summary = result_obj.outcome_summary
            record.narrative_chars = len(result_obj.narrative or "")
            if result_obj.errors:
                record.error = f"engine_errors: {json.dumps(result_obj.errors[:3])}"
                total_errors += 1
            _log.debug("turn %d: engine_turn=%d narrative=%d chars errors=%d", idx, record.engine_turn_number, record.narrative_chars, len(result_obj.errors or []))

        turn_records.append(record)

        # Capture state snapshot after each turn for state_yaml assertions
        state_snap: dict[str, Any] = {}
        try:
            state_snap = load_state(save_dir)
        except Exception as err:
            _log.warning("turn readback failed for turn %d in %s: %s", idx, save_dir, err)
        state_snapshots.append(state_snap)

    src_events = save_dir / "events.jsonl"

    # Run auto-checker and extract parse failures from events.jsonl
    if src_events.exists():
        events_lines = src_events.read_text().splitlines()
        all_events = [json.loads(ln) for ln in events_lines if ln.strip()]
        turn_events = [e for e in all_events if not e.get("__metadata__")]

        parse_failures = _extract_parse_failures(turn_events)
        for i, record in enumerate(turn_records):
            if i < len(parse_failures):
                _, rules_f, extract_f = parse_failures[i]
                record.rules_parse_failures = rules_f
                record.extract_parse_failures = extract_f

        # Merge state snapshots into turn_events for state_yaml assertions
        for i, snap in enumerate(state_snapshots):
            if i < len(turn_events):
                turn_events[i]["state_snapshot"] = snap

        # Run structured asserts
        for i, turn in enumerate(scenario.turns):
            if i >= len(turn_records):
                break
            record = turn_records[i]
            if i < len(turn_events) and turn.asserts:
                record.assert_results = _check_asserts(turn.asserts, turn_events[i])

        # Run universal asserts for every turn
        all_assert_results: list[dict[str, Any]] = []
        prev_ev: dict[str, Any] | None = None
        for i, ev in enumerate(turn_events):
            if i >= len(turn_records):
                break
            record = turn_records[i]
            window = turn_events[max(0, i-2):i+1] if i >= 2 else turn_events[:i+1]
            universal_results = run_all_universal_asserts(ev, prev_ev, event_window=window)
            record.assert_results.extend(universal_results)
            all_assert_results.extend(universal_results)
            prev_ev = ev

        if gate:
            red_failures = [r for r in all_assert_results if not r.get("passed") and r.get("severity") == "red"]
            if red_failures:
                for f in red_failures:
                    print(f"GATE FAIL [{f['assertion']}]: {f['detail']}", file=sys.stderr)
                sys.exit(1)

    finished_at = datetime.now(timezone.utc).isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    dst_events = artifacts_dir / f"{scenario.id}.events.jsonl"
    if src_events.exists():
        enriched = list(turn_events)
        if all_events and all_events[0].get("__metadata__"):
            enriched.insert(0, all_events[0])
        dst_events.write_text("\n".join(json.dumps(e, default=str) for e in enriched) + "\n")
    else:
        dst_events.write_text("")

    # NOTE: state.yaml is intentionally NOT copied — its content is fully
    # reproduced inside <scenario>.trace.md as the last turn's "State After
    # Turn" snapshot. See Phase 04 of eval-system-hardening.

    run_result = RunResult(
        scenario_id=scenario.id,
        pack=scenario.pack,
        model=engine_config.model,
        temperature_override=eval_cfg.inference.temperature_override,
        started_at=started_at,
        finished_at=finished_at,
        save_dir=str(save_dir),
        output_dir=str(output_dir),
        events_jsonl_path=str(dst_events),
        state_yaml_path="",
        turns=turn_records,
        total_errors=total_errors,
    )

    (artifacts_dir / f"{scenario.id}.run.json").write_text(
        json.dumps(asdict(run_result), indent=2, default=str)
    )

    _update_latest_symlink(runs_dir, output_dir)

    _log.debug("run complete: scenario=%s turns=%d errors=%d output_dir=%s", scenario.id, len(turn_records), total_errors, output_dir)

    return run_result


def load_run_result(run_json_path: Path) -> RunResult:
    """Reverse of the writer: rehydrate RunResult from <scenario_id>.run.json."""
    raw = json.loads(Path(run_json_path).read_text())
    turns = [TurnRecord(**t) for t in raw.pop("turns", [])]
    known_fields = {f.name for f in RunResult.__dataclass_fields__.values()}
    raw = {k: v for k, v in raw.items() if k in known_fields}
    return RunResult(turns=turns, **raw)


def find_previous_run(
    runs_dir: Path, scenario_id: str, exclude: Path | None = None
) -> Path | None:
    """Find the most recent prior run for the given scenario, excluding `exclude`.

    Returns the path to the previous <run_dir>/artifacts/<scenario_id>.run.json,
    or falls back to <run_dir>/<scenario_id>.run.json for pre-restructure runs.
    """
    if not runs_dir.is_dir():
        return None
    candidates: list[Path] = []
    for child in sorted(runs_dir.iterdir(), reverse=True):
        if child.name == "latest":
            continue
        if exclude is not None and child.resolve() == exclude.resolve():
            continue
        # New layout: artifacts/<scenario>.run.json
        run_json = child / "artifacts" / f"{scenario_id}.run.json"
        if not run_json.exists():
            # Back-compat: pre-restructure runs had it at the top level
            run_json = child / f"{scenario_id}.run.json"
        if run_json.exists():
            candidates.append(run_json)
    return candidates[0] if candidates else None
