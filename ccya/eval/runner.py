"""In-process eval runner.

Drives a scenario end-to-end against an isolated save-dir. Calls run_turn()
directly — no FastAPI, no SSE. Copies events.jsonl to the run directory as the
canonical eval data source. Does not invoke the judge or generate the report.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from ccya.engine import EngineConfig, run_turn
from ccya.eval.config import EvalConfig
from ccya.eval.scenario import Scenario
from ccya.models import TurnResult, load_config
from ccya.pack import load_pack
from ccya.state import init_save_dir, load_state, save_state


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
    """Mirror ccya/server.py's EngineConfig assembly from ccya/config.yaml.

    Applies eval_cfg.inference.temperature_override uniformly to all temperature
    knobs (rules, narrate, extract, generate_seed) when set.
    """
    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    if not cfg_path.exists():
        raise FileNotFoundError(f"game config not found: {cfg_path}")
    cfg = load_config(cfg_path)
    llm = cfg.get("llm", {})
    game = cfg.get("game", {})
    rules = cfg.get("rules", {})
    logging_cfg = cfg.get("logging", {})

    narrate_t = float(llm.get("narrate_temperature", 0.9))
    extract_t = float(llm.get("extract_temperature", 0.4))
    rules_t = float(rules.get("temperature", 0.2))
    seed_t = float(llm.get("generate_seed_temperature", 0.9))

    if eval_cfg.inference.temperature_override is not None:
        t = float(eval_cfg.inference.temperature_override)
        narrate_t = extract_t = rules_t = seed_t = t

    return EngineConfig(
        host=str(llm.get("host", "http://localhost:8080/v1")),
        model=str(llm.get("model", "")),
        prompt_token_budget=int(llm.get("prompt_token_budget", 28672)),
        request_timeout_s=int(llm.get("request_timeout_s", 180)),
        narrate_temperature=narrate_t,
        extract_temperature=extract_t,
        max_extract_retries=int(llm.get("max_extract_retries", 1)),
        window_turns=int(game.get("window_turns", 3)),
        chronicle_prefix_budget_tokens=int(
            game.get("chronicle_prefix_budget_tokens", 1500)
        ),
        recent_events_max=int(game.get("recent_events_max", 15)),
        enable_extract_thinking=bool(llm.get("enable_extract_thinking", False)),
        enable_narrate_thinking=bool(llm.get("enable_narrate_thinking", False)),
        generate_seed_temperature=seed_t,
        generate_seed_max_retries=int(llm.get("generate_seed_max_retries", 1)),
        log_llm_io=bool(logging_cfg.get("log_llm_io", False)),
        log_llm_io_max_chars=int(logging_cfg.get("log_llm_io_max_chars", 4000)),
        log_prompts=bool(logging_cfg.get("log_prompts", False)),
        rules_temperature=rules_t,
        max_rules_retries=int(rules.get("max_retries", 1)),
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


def _patch_eval_pack_starting_state(save_dir: Path, pack_id: str) -> None:
    """Apply runtime-only seed adjustments that SeedState's schema can't express.

    Currently only affects eval-pack: adds two structured Condition objects with
    explicit `added_turn` that SeedPC.conditions (list[str]) cannot represent.
    No-op for any other pack.
    """
    if pack_id != "eval-pack":
        return
    state = load_state(save_dir)
    state["pc"]["conditions"] = list(_EVAL_PACK_STARTING_CONDITIONS)
    save_state(save_dir, state)


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
# Main entry point
# ---------------------------------------------------------------------------


async def run_scenario(
    scenario: Scenario,
    *,
    eval_cfg: EvalConfig,
    packs_dir: Path,
    runs_dir: Path | None = None,
    save_dir: Path | None = None,
) -> RunResult:
    """Execute scenario end-to-end. Returns a RunResult; writes artifacts to disk.

    Args:
      scenario: parsed Scenario (from load_scenario()).
      eval_cfg: parsed EvalConfig (from load_eval_config()).
      packs_dir: directory containing scenario.pack as a subdirectory.
      runs_dir: where to create the timestamped run dir. Defaults to
        eval_cfg.runs_dir resolved relative to REPO_ROOT.
      save_dir: isolated save-dir for this run. Defaults to a fresh subdir under
        eval_cfg.default_save_root.

    Side effects:
      - Creates <runs_dir>/<ts>/ and writes events.jsonl, state.yaml, run.json.
      - Updates <runs_dir>/latest symlink.
      - Reads/writes <save_dir>/.

    Does NOT invoke judge or generate report.
    """
    pack = load_pack(scenario.pack, packs_dir)
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

    seed = pack.seed.model_dump()
    init_save_dir(save_dir, seed)
    _patch_eval_pack_starting_state(save_dir, pack.manifest.id)

    engine_config = _build_engine_config(eval_cfg)

    started_at = datetime.now(timezone.utc).isoformat()
    turn_records: list[TurnRecord] = []
    total_errors = 0

    for idx, turn in enumerate(scenario.turns, start=1):
        record = TurnRecord(
            turn_number=idx,
            input=turn.input,
            phase=turn.phase,
            expects=list(turn.expects),
        )
        t0 = time.monotonic()
        result_obj: TurnResult | None = None
        try:
            async for kind, payload in run_turn(
                save_dir,
                turn.input,
                config=engine_config,
                template_dir=str(PROMPTS_DIR),
                pack_style=pack.style_text,
                pack_examples=pack.extract_examples,
                pack_name_locales=pack.manifest.name_locales or [],
            ):
                if kind == "complete":
                    result_obj = payload
        except Exception as exc:
            record.error = f"exception: {exc!r}"
            total_errors += 1
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

        turn_records.append(record)

    finished_at = datetime.now(timezone.utc).isoformat()

    src_events = save_dir / "events.jsonl"
    src_state = save_dir / "state.yaml"
    dst_events = output_dir / f"{scenario.id}.events.jsonl"
    dst_state = output_dir / f"{scenario.id}.state.yaml"
    if src_events.exists():
        shutil.copyfile(src_events, dst_events)
    else:
        dst_events.write_text("")
    if src_state.exists():
        shutil.copyfile(src_state, dst_state)

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
        state_yaml_path=str(dst_state),
        turns=turn_records,
        total_errors=total_errors,
    )

    (output_dir / f"{scenario.id}.run.json").write_text(
        json.dumps(asdict(run_result), indent=2, default=str)
    )

    _update_latest_symlink(runs_dir, output_dir)

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

    Returns the path to the previous <run_dir>/<scenario_id>.run.json, or None
    if no previous run exists.
    """
    if not runs_dir.is_dir():
        return None
    candidates: list[Path] = []
    for child in sorted(runs_dir.iterdir(), reverse=True):
        if child.name == "latest":
            continue
        if exclude is not None and child.resolve() == exclude.resolve():
            continue
        run_json = child / f"{scenario_id}.run.json"
        if run_json.exists():
            candidates.append(run_json)
    return candidates[0] if candidates else None
