# Phase 3 — In-process runner

**Goal:** Build `ccya/eval/runner.py`. The runner takes an eval-pack + scenario,
seeds an isolated save-dir, drives the engine via `run_turn()` for each scenario
turn, and copies `events.jsonl` into `evals/runs/<ts>/`. After this phase you can
manually drive a scenario end-to-end (judge + report come in later phases).

**Prerequisites:** Phase 1 + Phase 2 complete.

**Estimated context:** ~45K tokens.

---

## Files to read first

Only these. Do NOT load `ccya/engine.py` in full.

- `ccya/plans/p3-inference/eval-harness.md` — overview
- `ccya/plans/p3-inference/eval-harness/02-eval-pack.md` — handoff state
- `ccya/REPOMAP/engine.md` — engine surface area
- `ccya/REPOMAP/state.md` — state I/O surface
- `ccya/ccya/engine.py` lines 1-120 — imports + `EngineConfig` dataclass (read once, do not re-read)
- `ccya/ccya/engine.py` lines 1474-1495 — `run_turn()` signature + first 20 body lines
- `ccya/ccya/engine.py` lines 1820-1910 — events.jsonl write + `TurnResult` construction (so you understand what the runner observes)
- `ccya/ccya/server.py` lines 26-58 — how the server builds `EngineConfig` from `config.yaml` (you'll mirror this)
- `ccya/ccya/models.py` lines 321-344 — `TurnResult` dataclass
- `ccya/ccya/state.py` lines 19-26, 134-180, 192-200, 260-265 — `load_state`, `save_state`, `_default_state`, `append_event`, `init_save_dir`
- `ccya/ccya/pack.py` lines 207-300 — `Pack` + `load_pack` (already read in phase 2; refresh if needed)
- `ccya/tests/test_engine_smoke.py` lines 263-291 — `_run` and `_run_with_tokens` helpers (mirror this pattern)
- `ccya/config.yaml` — game config that the runner reads to mirror engine setup

That's it. Skip everything else in engine.py.

---

## Design

The runner is a single async function `run_scenario(scenario, *, eval_cfg, pack_dir_root, packs_dir, output_dir, save_dir)` returning a `RunResult`. It:

1. Loads the pack via `load_pack(scenario.pack, packs_dir)`.
2. Creates the run dir `evals/runs/<ts>/` and a save-dir at `<save_dir>` (default `/tmp/ccya-eval/<ts>/save`). Both are isolated from `saves/default/`.
3. Calls `init_save_dir(save_dir, seed)` with the pack's seed.
4. Patches in the two starting conditions (`bruised_ribs` added_turn=8, `low_morale` added_turn=10) directly on `state.yaml` after seed load — phase 2 deferred this here intentionally because `SeedPC.conditions` only accepts `list[str]` but the rich `Condition` object with `added_turn` is what the engine uses at runtime.
5. Builds an `EngineConfig` by loading `ccya/config.yaml` (mirroring `ccya/server.py`), and applies any `eval_cfg.inference.temperature_override`.
6. For each `Turn` in the scenario:
    - Calls `run_turn(save_dir, turn.input, config=engine_config, template_dir=str(BASE_DIR/'ccya'/'prompts'), pack_style=pack.style_text, pack_examples=pack.extract_examples, pack_name_locales=pack.manifest.name_locales)` and drains the async generator.
    - Captures `TurnResult` from the `("complete", ...)` yield.
    - Captures errors from the `("error", ...)` yield (if any).
    - Records wall-clock duration per turn.
7. After all turns complete:
    - Copies `<save_dir>/events.jsonl` to `<output_dir>/<scenario.id>.events.jsonl`.
    - Copies `<save_dir>/state.yaml` to `<output_dir>/<scenario.id>.state.yaml`.
    - Writes `<output_dir>/<scenario.id>.run.json` (RunResult metadata: scenario id, pack, started/finished timestamps, per-turn durations, model, temperature_override, total error count).
    - Updates `evals/runs/latest` symlink to point at `<ts>/`.
8. Returns the `RunResult`.

The runner does NOT call the judge or generate the report. Those are phases 4 and 5. The runner exposes enough metadata via `RunResult` for the judge (phase 5) and report (phase 4) to consume.

---

## Files to create

### 1. `ccya/eval/runner.py`

```python
"""In-process eval runner.

Drives a scenario end-to-end against an isolated save-dir. Calls run_turn()
directly — no FastAPI, no SSE. Copies events.jsonl to the run directory as the
canonical eval data source. Does not invoke the judge or generate the report.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ccya.engine import EngineConfig, run_turn
from ccya.eval.config import EvalConfig
from ccya.eval.scenario import Scenario, Turn
from ccya.models import TurnResult, load_config
from ccya.pack import Pack, load_pack
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
    pack: Pack = load_pack(scenario.pack, packs_dir)
    if pack.seed is None:
        raise ValueError(
            f"scenario.pack={scenario.pack!r} is not static (no seed). "
            "Eval harness only supports static packs."
        )

    ts = _utc_ts()
    runs_dir = (runs_dir or (REPO_ROOT / eval_cfg.runs_dir)).resolve()
    output_dir = runs_dir / ts
    _ensure_runs_dir(runs_dir)
    output_dir.mkdir(parents=True, exist_ok=False)

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
                pack_name_locales=pack.manifest.name_locales,
            ):
                if kind == "complete":
                    result_obj = payload
        except Exception as exc:
            record.error = f"runner exception: {exc!r}"
            total_errors += 1
        record.duration_s = time.monotonic() - t0

        if result_obj is not None:
            record.engine_turn_number = result_obj.turn
            record.outcome_summary = result_obj.outcome_summary
            record.narrative_chars = len(result_obj.narrative or "")
            if result_obj.errors:
                record.error = json.dumps(result_obj.errors[:3])
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
```

### 2. Update `ccya/eval/__init__.py`

Replace the file from phase 1 with this expanded version:

```python
"""ccya eval harness.

Tier 2 of the eval system: live-LLM in-process driver, single judge, single scenario.
See ccya/plans/p3-inference/eval-harness.md.
"""

from ccya.eval.config import EvalConfig, load_eval_config
from ccya.eval.runner import (
    RunResult,
    TurnRecord,
    find_previous_run,
    load_run_result,
    run_scenario,
)
from ccya.eval.scenario import Scenario, Turn, discover_scenarios, load_scenario

__all__ = [
    "EvalConfig",
    "RunResult",
    "Scenario",
    "Turn",
    "TurnRecord",
    "discover_scenarios",
    "find_previous_run",
    "load_eval_config",
    "load_run_result",
    "load_scenario",
    "run_scenario",
]
```

---

## Verification

The runner can be exercised end-to-end without a real LLM by setting `MOCK_MODE=1`,
which `ccya/llm_client.py` honors. The mock returns canned responses so a 6-turn
run completes in <2 seconds.

```bash
# 1. Module imports cleanly
uv run python -c "
from ccya.eval import run_scenario, RunResult, TurnRecord, find_previous_run
print('runner imports OK')
"

# 2. _build_engine_config mirrors server.py
uv run python -c "
from ccya.eval.config import load_eval_config
from ccya.eval.runner import _build_engine_config
cfg = load_eval_config()
ec = _build_engine_config(cfg)
print('engine config built:', ec.model, 'narrate_t=', ec.narrate_temperature)
assert ec.model, 'model should be non-empty from config.yaml'
"

# 3. Temperature override applies uniformly
uv run python -c "
from dataclasses import replace
from ccya.eval.config import load_eval_config, InferenceConfig
from ccya.eval.runner import _build_engine_config
cfg = load_eval_config()
cfg.inference = InferenceConfig(temperature_override=0.0)
ec = _build_engine_config(cfg)
assert ec.narrate_temperature == 0.0
assert ec.extract_temperature == 0.0
assert ec.rules_temperature == 0.0
assert ec.generate_seed_temperature == 0.0
print('override OK: all temps = 0.0')
"

# 4. Smoke a single-turn scenario in MOCK_MODE
mkdir -p evals/scenarios
cat > evals/scenarios/_smoke.py <<'PY'
from ccya.eval.scenario import Scenario, Turn

scenario = Scenario(
    id="_smoke",
    pack="eval-pack",
    description="One-turn smoke test for the runner.",
    turns=[Turn(input="Look around the inn.", phase="dialogue")],
)
PY

MOCK_MODE=1 uv run python -c "
import asyncio
from pathlib import Path
from ccya.eval.config import load_eval_config
from ccya.eval.scenario import load_scenario
from ccya.eval.runner import run_scenario, REPO_ROOT

async def main():
    sc = load_scenario('evals/scenarios/_smoke.py')
    cfg = load_eval_config()
    rr = await run_scenario(
        sc,
        eval_cfg=cfg,
        packs_dir=REPO_ROOT / 'evals' / 'packs',
    )
    print('runner result:')
    print('  output_dir:', rr.output_dir)
    print('  events:', rr.events_jsonl_path)
    print('  turns:', len(rr.turns))
    print('  errors:', rr.total_errors)
    for t in rr.turns:
        print(f'    turn {t.turn_number}: engine_turn={t.engine_turn_number} '
              f'duration={t.duration_s:.2f}s error={t.error}')

asyncio.run(main())
"

# 5. Verify the run dir got created with expected files + symlink
ls -la evals/runs/
ls evals/runs/latest/
test -f evals/runs/latest/_smoke.events.jsonl
test -f evals/runs/latest/_smoke.state.yaml
test -f evals/runs/latest/_smoke.run.json

# 6. Verify events.jsonl actually contains 1 event
wc -l evals/runs/latest/_smoke.events.jsonl
uv run python -c "
import json
from pathlib import Path
events = [json.loads(line) for line in Path('evals/runs/latest/_smoke.events.jsonl').read_text().splitlines() if line.strip()]
assert len(events) == 1, f'expected 1 event, got {len(events)}'
e = events[0]
assert e['turn'] == 13, f'expected turn=13 (seed turn=12 + 1), got {e[\"turn\"]}'
assert e['input'] == 'Look around the inn.'
assert 'extraction' in e
assert 'rules_prompt' in e
assert 'narrate_prompt' in e
print('events.jsonl smoke check OK')
"

# 7. find_previous_run returns None when only one run exists
uv run python -c "
from pathlib import Path
from ccya.eval.runner import find_previous_run, REPO_ROOT
prev = find_previous_run(REPO_ROOT / 'evals' / 'runs', '_smoke')
print('previous run (should be None on first run, then a path on subsequent):', prev)
"

# 8. Run again to confirm find_previous_run starts returning the prior dir
MOCK_MODE=1 uv run python -c "
import asyncio
from pathlib import Path
from ccya.eval.config import load_eval_config
from ccya.eval.scenario import load_scenario
from ccya.eval.runner import run_scenario, find_previous_run, REPO_ROOT

async def main():
    sc = load_scenario('evals/scenarios/_smoke.py')
    cfg = load_eval_config()
    rr = await run_scenario(sc, eval_cfg=cfg, packs_dir=REPO_ROOT / 'evals' / 'packs')
    runs_dir = REPO_ROOT / 'evals' / 'runs'
    prev = find_previous_run(runs_dir, '_smoke', exclude=Path(rr.output_dir))
    print('previous run after second run:', prev)
    assert prev is not None and prev.exists(), 'should find a previous run now'

asyncio.run(main())
"

# 9. saves/default/ is untouched (CRITICAL — runner must never write there)
git status saves/default/

# 10. Cleanup the smoke scenario file (leave runs/ alone — it's gitignored)
rm evals/scenarios/_smoke.py

# 11. Existing tests still pass
uv run pytest -q tests/test_engine_smoke.py
```

If `git status saves/default/` shows changes to `state.yaml`, `events.jsonl`, or
`chronicle.md`, the runner has a bug — it wrote to the user's real save. Stop
and fix before proceeding.

---

## STOP HERE

Phase 3 is complete. Verify all checks pass, then stop and start a new chat with
`eval-harness/04-report.md`.

### Handoff to phase 4

State after this phase:

- `ccya/eval/runner.py` exists and exposes `run_scenario`, `RunResult`, `TurnRecord`, `find_previous_run`, `load_run_result`.
- A scenario can be driven end-to-end against the eval-pack in MOCK_MODE in <2 seconds.
- Each run writes `<scenario_id>.events.jsonl`, `<scenario_id>.state.yaml`, `<scenario_id>.run.json` to `evals/runs/<ts>/`, plus updates `evals/runs/latest`.
- The runner does NOT call the judge and does NOT generate REPORT.md.
- `saves/default/` is never touched by the runner.
- The smoke scenario file `evals/scenarios/_smoke.py` was deleted in step 10.

Phase 4 builds `ccya/eval/report.py` which consumes `RunResult` + `events.jsonl` + the previous `RunResult` (via `find_previous_run`) and produces `REPORT.md` with token-regression flags at the top.
