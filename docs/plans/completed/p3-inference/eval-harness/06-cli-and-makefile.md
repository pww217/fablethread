# Phase 6 — CLI, Makefile targets, and full_cycle scenario

**Goal:** Wire `ccya/eval/cli.py` so `python -m ccya.eval` runs scenarios
end-to-end (runner → judge → report). Add Makefile targets. Hand-author the
production `full_cycle.py` scenario.

After this phase, `make eval` runs the full pipeline against the live mlx_lm
server and produces a `REPORT.md`.

**Prerequisites:** Phase 1 through 5 complete.

**Estimated context:** ~25K tokens.

---

## Files to read first

- `ccya/plans/p3-inference/eval-harness.md` — overview
- `ccya/plans/p3-inference/eval-harness/05-judge.md` — handoff state
- `ccya/Makefile` — current targets (read in full; only ~50 lines)
- `ccya/ccya/__main__.py` — argparse pattern used elsewhere

That's it.

---

## Files to create

### 1. `evals/scenarios/full_cycle.py`

Hand-authored 6-turn scenario. Each turn is chosen to exercise a specific
mechanic. The `phase` tag is informational. The `expects` list is shown in the
report as an annotation — NOT enforced as a test failure.

```python
"""full_cycle — exercises dialogue, combat, quest progression in one run.

Designed against eval-pack's mid-game seed (turn=12). The arc:
  1. dialogue with Halden (no roll, no inventory change)
  2. attempt to bandage Halden — partial success — uses 2 bandages
  3. confront the toughs — combat, strength check
  4. take a hit — likely setback — adds a condition
  5. pay them off — charisma + credits — quest objective progresses
  6. hand the ledger to Halden — completes deliver_the_ledger objective

Expected emergent observations the judge / report should surface:
  - rules call should fire on turns 2, 3, 4, 5 (skill checks)
  - extract.state should remove inventory on turns 2 and 5
  - extract.progress should mark quest objectives done on turns 5 and 6
  - context_economy: by turn 6, recent_events shouldn't have ballooned
"""

from ccya.eval.scenario import Scenario, Turn


scenario = Scenario(
    id="full_cycle",
    pack="eval-pack",
    description="Six-turn arc: dialogue → bandage → confront → take hit → pay off → deliver.",
    turns=[
        Turn(
            input="Walk over to Halden's table and sit down across from him.",
            phase="dialogue",
            expects=[
                "rules.required=false (pure social, no obstacle)",
                "scope skips inventory and pc_condition",
                "extract.state should be near-empty",
            ],
        ),
        Turn(
            input="Tear open two bandages and wrap the gash on Halden's forearm before the bleeding gets worse.",
            phase="first_aid",
            expects=[
                "rules.required=true skill=wits|dexterity",
                "extract.state.inventory_remove includes bandages amount=2",
                "extract.scene.present_npcs still includes halden",
            ],
        ),
        Turn(
            input="Stand up, square my shoulders, and walk straight toward the bald tough at the door.",
            phase="combat_engage",
            expects=[
                "rules.required=true skill=strength|charisma",
                "scope active_domains includes pc_condition",
                "narration honors the rules band",
            ],
        ),
        Turn(
            input="Take the punch on the ribs and grab the bald tough's wrist before he can pull a knife.",
            phase="combat_take_hit",
            expects=[
                "rules.required=true skill=strength",
                "extract.state likely adds a pc_condition (cracked_ribs, winded, or similar)",
                "extract.state should NOT add bruised_ribs again (it already exists)",
            ],
        ),
        Turn(
            input="Drop a stack of 200 credits onto the table by the door and tell the toughs Caron's coin is paid; they can leave now.",
            phase="payoff",
            expects=[
                "rules.required=true skill=charisma",
                "extract.state.inventory_remove includes credits amount=200",
                "extract.progress.quest_updates marks 'Convince, pay, or remove the toughs' done",
            ],
        ),
        Turn(
            input="Sit back down across from Halden, slide the merchant seal across the table, and hand him the ledger from my coat.",
            phase="quest_complete",
            expects=[
                "extract.progress marks deliver_the_ledger objectives done",
                "auto_complete should fire — quest status should become completed",
                "extract.scene mentions both halden and the seal/ledger",
            ],
        ),
    ],
)
```

Note: the eval-pack's seed does NOT actually contain a "bandage Halden" hook in
its current narration — that's fine. The narrator should improvise from "Halden
sits at the corner table" + the player's chosen input. The judge will score
narrative quality and consistency from there.

### 2. `evals/scenarios/__init__.py`

Empty file so Python can treat the directory as a package if needed:

```python
```

### 3. `ccya/eval/cli.py`

```python
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
import sys
from dataclasses import replace
from pathlib import Path

from ccya.eval.config import InferenceConfig, load_eval_config
from ccya.eval.judge import run_judge
from ccya.eval.report import generate_report
from ccya.eval.runner import (
    REPO_ROOT,
    RunResult,
    find_previous_run,
    load_run_result,
    run_scenario,
)
from ccya.eval.scenario import discover_scenarios, load_scenario


def _resolve_packs_dir(arg: str | None) -> Path:
    if arg:
        return Path(arg).resolve()
    return REPO_ROOT / "evals" / "packs"


def _resolve_scenario_path(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        if not p.exists() and (REPO_ROOT / "evals" / "scenarios" / arg).exists():
            return REPO_ROOT / "evals" / "scenarios" / arg
        if not p.exists() and (REPO_ROOT / "evals" / "scenarios" / f"{arg}.py").exists():
            return REPO_ROOT / "evals" / "scenarios" / f"{arg}.py"
        return p.resolve()
    candidates = discover_scenarios(REPO_ROOT / "evals" / "scenarios")
    if not candidates:
        raise FileNotFoundError("no scenarios found in evals/scenarios/")
    return candidates[0]


async def _cmd_run(args: argparse.Namespace) -> int:
    eval_cfg = load_eval_config()
    if args.temp is not None:
        eval_cfg.inference = InferenceConfig(
            temperature_override=float(args.temp),
            cache=eval_cfg.inference.cache,
        )

    scenario_path = _resolve_scenario_path(args.scenario)
    scenario = load_scenario(scenario_path)
    if args.pack:
        scenario = replace(scenario, pack=args.pack)

    print(f"[eval] scenario={scenario.id} pack={scenario.pack} temp={eval_cfg.inference.temperature_override}", file=sys.stderr)
    print(f"[eval] scenario_file={scenario_path}", file=sys.stderr)

    rr: RunResult = await run_scenario(
        scenario,
        eval_cfg=eval_cfg,
        packs_dir=_resolve_packs_dir(args.packs_dir),
    )
    print(f"[eval] runner done: {len(rr.turns)} turns, {rr.total_errors} errors → {rr.output_dir}", file=sys.stderr)

    judge_result = None
    if not args.no_judge and eval_cfg.judge.enabled:
        prev_json = find_previous_run(
            (REPO_ROOT / eval_cfg.runs_dir).resolve(),
            scenario.id,
            exclude=Path(rr.output_dir),
        )
        prev_report = prev_json.parent / "REPORT.md" if prev_json else None
        print(f"[eval] running judge (model defaults to engine model)…", file=sys.stderr)
        judge_result = await run_judge(
            Path(rr.events_jsonl_path),
            eval_cfg=eval_cfg,
            previous_report_path=prev_report,
        )
        print(f"[eval] judge overall_score={judge_result.overall_score}", file=sys.stderr)

    report_path = generate_report(rr, eval_cfg=eval_cfg, judge_result=judge_result)
    print(f"[eval] report: {report_path}", file=sys.stderr)
    print(str(report_path))
    return 0


async def _cmd_judge_only(args: argparse.Namespace) -> int:
    eval_cfg = load_eval_config()
    run_dir = Path(args.run_dir).resolve()
    if not run_dir.is_dir():
        print(f"[eval] not a directory: {run_dir}", file=sys.stderr)
        return 1

    run_jsons = sorted(run_dir.glob("*.run.json"))
    if not run_jsons:
        print(f"[eval] no *.run.json found in {run_dir}", file=sys.stderr)
        return 1
    rr = load_run_result(run_jsons[0])

    runs_dir = run_dir.parent
    prev_json = find_previous_run(runs_dir, rr.scenario_id, exclude=run_dir)
    prev_report = prev_json.parent / "REPORT.md" if prev_json else None

    judge_result = await run_judge(
        Path(rr.events_jsonl_path),
        eval_cfg=eval_cfg,
        previous_report_path=prev_report,
    )
    report_path = generate_report(rr, eval_cfg=eval_cfg, judge_result=judge_result)
    print(f"[eval] re-judged: overall={judge_result.overall_score}", file=sys.stderr)
    print(str(report_path))
    return 0


def _cmd_pack(args: argparse.Namespace) -> int:
    cfg = load_eval_config()
    print("Eval config:")
    for k in (
        "default_pack",
        "default_save_root",
        "runs_dir",
    ):
        print(f"  {k}: {getattr(cfg, k)}")
    print(f"  inference.temperature_override: {cfg.inference.temperature_override}")
    print(f"  inference.cache: {cfg.inference.cache}")
    print(f"  judge.enabled: {cfg.judge.enabled}")
    print(f"  judge.model: {cfg.judge.model}")
    print(f"  judge.rubric_path: {cfg.judge.rubric_path}")
    print(f"  judge.temperature: {cfg.judge.temperature}")
    print(f"  judge.max_input_chars: {cfg.judge.max_input_chars}")
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
        return asyncio.run(args.func(args))
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
```

### 4. Add `ccya/eval/__main__.py`

So `python -m ccya.eval` works:

```python
from ccya.eval.cli import main

raise SystemExit(main())
```

### 5. Update `Makefile`

Add the four eval targets at the bottom (preserve existing targets — do not
delete or reorder them). Update the `.PHONY` line to include the new targets.

Replace the first line of the Makefile:

```makefile
.PHONY: install run dev fmt lint test test-v test-x typecheck check css clean new-game vendor llama-swap
```

with:

```makefile
.PHONY: install run dev fmt lint test test-v test-x typecheck check css clean new-game vendor llama-swap eval eval-fast eval-judge-only eval-pack
```

Append these targets to the end of the file (after `clean:`):

```makefile

eval: llama-swap
	uv run python -m ccya.eval run

eval-fast: llama-swap
	uv run python -m ccya.eval run --temp 0

eval-judge-only:
	@if [ -z "$(RUN)" ]; then echo 'Usage: make eval-judge-only RUN=evals/runs/<ts>'; exit 2; fi
	uv run python -m ccya.eval judge-only $(RUN)

eval-pack:
	uv run python -m ccya.eval pack
```

The `llama-swap` dependency on `eval` and `eval-fast` ensures the model server
is up before the runner starts dialing it.

---

## Verification

```bash
# 1. CLI imports + help works
uv run python -m ccya.eval --help
uv run python -m ccya.eval run --help

# 2. List scenarios discovers full_cycle
uv run python -m ccya.eval list

# 3. Print effective config
make eval-pack

# 4. MOCK_MODE end-to-end via CLI
MOCK_MODE=1 uv run python -m ccya.eval run full_cycle --no-judge

# 5. The CLI emits the report path on stdout
MOCK_MODE=1 uv run python -m ccya.eval run full_cycle --no-judge | tail -1
# → should print path to evals/runs/<ts>/REPORT.md

# 6. Verify REPORT.md exists and full_cycle ran 6 turns
test -f evals/runs/latest/REPORT.md
uv run python -c "
import json
from pathlib import Path
events = [json.loads(line) for line in Path('evals/runs/latest/full_cycle.events.jsonl').read_text().splitlines() if line.strip()]
print('events:', len(events))
assert len(events) == 6, f'expected 6 events, got {len(events)}'
print('first input:', events[0]['input'])
print('last input:', events[-1]['input'])
"

# 7. judge-only against the latest run
MOCK_MODE=1 make eval-judge-only RUN=evals/runs/latest

# 8. Confirm the existing tests still pass
uv run pytest -q tests/test_engine_smoke.py

# 9. saves/default/ STILL untouched
git status saves/default/
```

If `make eval` is run without `MOCK_MODE` and a live mlx_lm server is up at the
configured host, it will run the full 6-turn scenario against the real model
(~3 minutes per the user's machine). Do NOT try the live run as part of phase 6
verification — leave that for the user to invoke manually after phase 7 is done.

---

## STOP HERE

Phase 6 is complete. Verify all checks pass, then stop and start a new chat with
`eval-harness/07-engine-pipeline-tests.md`.

### Handoff to phase 7

State after this phase:

- `python -m ccya.eval run [scenario]` runs the full pipeline (runner → judge → report) and emits the report path on stdout.
- `make eval` is the user-facing entry point (production temps, real model).
- `make eval-fast` runs the same scenario at temperature 0 for deterministic structural diffs.
- `make eval-judge-only RUN=evals/runs/<ts>` re-runs the judge against a prior run.
- `make eval-pack` prints the effective eval config.
- `evals/scenarios/full_cycle.py` is the production scenario.
- `evals/scenarios/__init__.py` exists (empty).

Phase 7 adds the engine integration tests (token ceilings, multi-turn invariants, rules/scope correctness) under `tests/test_engine_pipeline.py`. These run under `make test` and stay strictly mocked. They do NOT touch any eval-harness file from phases 1-6.
