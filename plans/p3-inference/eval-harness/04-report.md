# Phase 4 — Report generator

**Goal:** Build `ccya/eval/report.py`. It consumes the current `RunResult` and the
previous run's `RunResult` (via `find_previous_run` from phase 3), reads
`events.jsonl` for both, computes per-stream token regressions, and writes a
markdown `REPORT.md` to the run dir. Critical regressions are flagged at the top.

The judge integration is wired in here as a placeholder — phase 5 fills in the
actual judge call. The report should accept an optional `judge_result: JudgeResult | None`
and render its findings if present.

**Prerequisites:** Phase 1, 2, 3 complete.

**Estimated context:** ~30K tokens.

---

## Files to read first

Only these.

- `ccya/plans/p3-inference/eval-harness.md` — overview
- `ccya/plans/p3-inference/eval-harness/03-runner.md` — handoff state, especially the structure of `RunResult` and `TurnRecord`
- `ccya/ccya/engine.py` lines 1820-1890 — the `event = {...}` dict written to events.jsonl. This is the canonical schema you'll parse.
- `ccya/REPOMAP/state.md` — events.jsonl shape reference

That's it. You don't need engine.py beyond those lines; you do NOT need the runner code (you import it, you don't re-read it).

---

## events.jsonl event schema reference (do not look elsewhere)

Each line is one turn's event dict, written by `engine.append_event()`:

```python
{
  "ts": "2026-05-05T...Z",
  "trace_id": "55152111",
  "turn": 13,
  "input": "Look around the inn.",
  "applied": {<dict — applied StateDelta fields>},
  "rejected": [<list of rejected delta entries>],
  "actions": [<list of suggested next-action strings>],
  "scene_tags": ["dialogue"],
  "rules": {                    # only present if rolled or non-trivial intent
    "intent_verb": "look",
    "intent": "...",
    "rolled": True,
    "skill": "wits",
    "difficulty": "...",
    "band": "success",
    "outcome_summary": "...",
    "total_ms": 234,
    "tokens_in": 30,
    "tokens_out": 12,
  } | None,
  "narrate": {                  # narrate stream metrics
    "total_ms": 1234,
    "tokens_in": 4200,
    "tokens_out": 320,
  },
  "extract": {                  # aggregate extract metrics across all 3 sub-calls
    "total_ms": 800,
    "tokens_in": 3000,
    "tokens_out": 600,
  },
  "extraction": {               # per-stream — THE KEY OBJECT FOR EVALS
    "scene": {
      "rendered_system": "<full system prompt as sent>",
      "rendered_user": "<full user prompt as sent>",
      "output": "<raw LLM response>",
      "skipped": False,         # True if this stream was skipped via scope.skip_domains
      "attempts": 1,            # 1 = first try succeeded; 2 = retry once; etc.
      "tokens_in": 1200,
      "tokens_out": 240,
      "ms": 320,
    },
    "state":    { ... same shape ... },
    "progress": { ... same shape ... },
  },
  "changes": {<dict — pre/post diff>},
  "failed": [<list of failed precondition strings>],
  "rules_prompt":   { "rendered_system": "...", "rendered_user": "...", "output": "..." },
  "narrate_prompt": { "rendered_system": "...", "rendered_user": "...", "output": "..." },
}
```

Streams to track for token regression: `rules`, `narrate`, `extraction.scene`, `extraction.state`, `extraction.progress`. Use `tokens_in` for budget tracking (input prompt size — the thing that grows with context rot). Use `attempts > 1` as the retry signal. Use `skipped` to know when a stream was skipped (do not flag a skipped stream as a regression).

---

## Files to create

### `ccya/eval/report.py`

```python
"""Markdown report generator for eval runs.

Consumes the current RunResult + the previous run's events.jsonl and produces
REPORT.md in the current run directory. Critical regressions surface at the top.
Always exits successfully — the report is a notification, not a CI gate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ccya.eval.config import EvalConfig
from ccya.eval.runner import RunResult, find_previous_run, load_run_result


# ---------------------------------------------------------------------------
# Stream extraction from events.jsonl
# ---------------------------------------------------------------------------


_STREAM_KEYS = ("rules", "narrate", "extraction.scene", "extraction.state", "extraction.progress")


@dataclass
class StreamMetrics:
    tokens_in: int = 0
    tokens_out: int = 0
    ms: int = 0
    attempts: int = 1
    skipped: bool = False


@dataclass
class TurnMetrics:
    turn: int
    """state.meta.turn (engine's turn number after this event)."""
    input: str
    streams: dict[str, StreamMetrics] = field(default_factory=dict)
    rejected_count: int = 0
    failed: list[str] = field(default_factory=list)
    """failed-preconditions list."""


def _read_events(events_path: Path) -> list[dict[str, Any]]:
    if not events_path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in events_path.read_text().splitlines():
        s = line.strip()
        if not s:
            continue
        try:
            out.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return out


def _extract_stream_metrics(event: dict[str, Any]) -> dict[str, StreamMetrics]:
    streams: dict[str, StreamMetrics] = {}

    rules = event.get("rules") or {}
    if rules:
        streams["rules"] = StreamMetrics(
            tokens_in=int(rules.get("tokens_in") or 0),
            tokens_out=int(rules.get("tokens_out") or 0),
            ms=int(rules.get("total_ms") or 0),
            attempts=1,
            skipped=False,
        )
    else:
        streams["rules"] = StreamMetrics(skipped=True)

    narrate = event.get("narrate") or {}
    streams["narrate"] = StreamMetrics(
        tokens_in=int(narrate.get("tokens_in") or 0),
        tokens_out=int(narrate.get("tokens_out") or 0),
        ms=int(narrate.get("total_ms") or 0),
        attempts=1,
        skipped=not narrate,
    )

    extraction = event.get("extraction") or {}
    for sub in ("scene", "state", "progress"):
        ex = extraction.get(sub) or {}
        streams[f"extraction.{sub}"] = StreamMetrics(
            tokens_in=int(ex.get("tokens_in") or 0),
            tokens_out=int(ex.get("tokens_out") or 0),
            ms=int(ex.get("ms") or 0),
            attempts=int(ex.get("attempts") or 1),
            skipped=bool(ex.get("skipped", False)),
        )

    return streams


def _summarize_events(events: list[dict[str, Any]]) -> list[TurnMetrics]:
    out: list[TurnMetrics] = []
    for ev in events:
        rejected = ev.get("rejected") or []
        failed = ev.get("failed") or []
        out.append(
            TurnMetrics(
                turn=int(ev.get("turn") or 0),
                input=str(ev.get("input") or ""),
                streams=_extract_stream_metrics(ev),
                rejected_count=len(rejected) if isinstance(rejected, list) else 0,
                failed=list(failed) if isinstance(failed, list) else [],
            )
        )
    return out


# ---------------------------------------------------------------------------
# Regression analysis
# ---------------------------------------------------------------------------


@dataclass
class StreamRegression:
    stream: str
    turn: int
    prev_tokens_in: int
    cur_tokens_in: int
    pct_change: float
    severity: str
    """One of: 'warn' (>= warn_pct) or 'flag' (>= fail_pct)."""


@dataclass
class Flag:
    kind: str
    """One of: tokens_regression | extraction_retries | extraction_failures |
    judge_score_drop | rejected_deltas | runner_errors."""
    summary: str
    detail: str = ""


def _compute_regressions(
    cur: list[TurnMetrics],
    prev: list[TurnMetrics],
    *,
    warn_pct: float,
    fail_pct: float,
) -> list[StreamRegression]:
    """Per-turn, per-stream tokens_in regression vs the prior run's same turn index."""
    out: list[StreamRegression] = []
    n = min(len(cur), len(prev))
    for i in range(n):
        cur_t = cur[i]
        prev_t = prev[i]
        for stream in _STREAM_KEYS:
            cur_s = cur_t.streams.get(stream)
            prev_s = prev_t.streams.get(stream)
            if cur_s is None or prev_s is None:
                continue
            if cur_s.skipped or prev_s.skipped:
                continue
            if prev_s.tokens_in <= 0:
                continue
            pct = (cur_s.tokens_in - prev_s.tokens_in) / prev_s.tokens_in * 100.0
            if pct >= fail_pct:
                sev = "flag"
            elif pct >= warn_pct:
                sev = "warn"
            else:
                continue
            out.append(
                StreamRegression(
                    stream=stream,
                    turn=cur_t.turn,
                    prev_tokens_in=prev_s.tokens_in,
                    cur_tokens_in=cur_s.tokens_in,
                    pct_change=pct,
                    severity=sev,
                ),
            )
    return out


def _collect_flags(
    cur: list[TurnMetrics],
    regressions: list[StreamRegression],
    run_result: RunResult,
    judge: "Any | None",
) -> list[Flag]:
    flags: list[Flag] = []

    flagged_regs = [r for r in regressions if r.severity == "flag"]
    if flagged_regs:
        worst = max(flagged_regs, key=lambda r: r.pct_change)
        flags.append(
            Flag(
                kind="tokens_regression",
                summary=f"{len(flagged_regs)} stream(s) over the fail threshold "
                f"(worst: {worst.stream} turn {worst.turn} +{worst.pct_change:.1f}%)",
                detail="\n".join(
                    f"- `{r.stream}` turn {r.turn}: {r.prev_tokens_in} → {r.cur_tokens_in} (+{r.pct_change:.1f}%)"
                    for r in flagged_regs
                ),
            ),
        )

    retries = []
    failures = []
    for t in cur:
        for stream, sm in t.streams.items():
            if sm.skipped:
                continue
            if sm.attempts > 1:
                retries.append((t.turn, stream, sm.attempts))
            if stream.startswith("extraction.") and sm.tokens_out == 0 and not sm.skipped:
                failures.append((t.turn, stream))
    if retries:
        flags.append(
            Flag(
                kind="extraction_retries",
                summary=f"{len(retries)} retried extraction stream(s)",
                detail="\n".join(f"- turn {t} `{s}` attempts={a}" for t, s, a in retries),
            ),
        )
    if failures:
        flags.append(
            Flag(
                kind="extraction_failures",
                summary=f"{len(failures)} extraction stream(s) returned no tokens",
                detail="\n".join(f"- turn {t} `{s}`" for t, s in failures),
            ),
        )

    rejected_total = sum(t.rejected_count for t in cur)
    if rejected_total:
        flags.append(
            Flag(
                kind="rejected_deltas",
                summary=f"{rejected_total} rejected delta(s) across the run",
                detail="\n".join(
                    f"- turn {t.turn}: {t.rejected_count} rejected"
                    for t in cur
                    if t.rejected_count
                ),
            ),
        )

    if run_result.total_errors:
        flags.append(
            Flag(
                kind="runner_errors",
                summary=f"{run_result.total_errors} turn(s) errored",
                detail="\n".join(
                    f"- turn {t.turn_number}: {t.error}"
                    for t in run_result.turns
                    if t.error
                ),
            ),
        )

    if judge is not None:
        prev_score = getattr(judge, "previous_overall", None)
        cur_score = getattr(judge, "overall_score", None)
        if (
            prev_score is not None
            and cur_score is not None
            and (prev_score - cur_score) >= 1
        ):
            flags.append(
                Flag(
                    kind="judge_score_drop",
                    summary=f"judge overall {prev_score} → {cur_score} (-{prev_score - cur_score})",
                    detail=getattr(judge, "comments", ""),
                ),
            )

    return flags


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _render_flag_block(flags: list[Flag], flag_at_top: list[str]) -> str:
    if not flags:
        return "## ✅ No flags\n\nNo regressions, retries, failures, or judge score drops detected.\n"

    top = [f for f in flags if f.kind in flag_at_top]
    other = [f for f in flags if f.kind not in flag_at_top]

    lines: list[str] = []
    if top:
        lines.append("## ⚠️  Flagged\n")
        for f in top:
            lines.append(f"### `{f.kind}` — {f.summary}\n")
            if f.detail:
                lines.append(f.detail)
                lines.append("")
    if other:
        lines.append("## Other observations\n")
        for f in other:
            lines.append(f"- **`{f.kind}`**: {f.summary}")
            if f.detail:
                lines.append(f.detail)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_per_turn_table(cur: list[TurnMetrics], prev: list[TurnMetrics]) -> str:
    if not cur:
        return "_(no turns)_\n"
    rows: list[str] = []
    rows.append("| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | rejected |")
    rows.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")

    def _delta(cur_v: int, prev_v: int | None) -> str:
        if prev_v is None or prev_v == 0:
            return str(cur_v)
        diff = cur_v - prev_v
        sign = "+" if diff >= 0 else "−"
        return f"{cur_v} ({sign}{abs(diff)})"

    for i, t in enumerate(cur):
        p = prev[i] if i < len(prev) else None
        def _gv(stream: str, src: TurnMetrics | None) -> int | None:
            if src is None:
                return None
            sm = src.streams.get(stream)
            if sm is None or sm.skipped:
                return None
            return sm.tokens_in

        cells = [
            str(t.turn),
            (t.input[:48] + "…") if len(t.input) > 48 else t.input,
        ]
        for stream in _STREAM_KEYS:
            cur_v = _gv(stream, t)
            prev_v = _gv(stream, p)
            if cur_v is None:
                cells.append("—")
            else:
                cells.append(_delta(cur_v, prev_v))

        retries_in_turn = sum(
            sm.attempts - 1
            for sm in t.streams.values()
            if not sm.skipped and sm.attempts > 1
        )
        cells.append(str(retries_in_turn) if retries_in_turn else "0")
        cells.append(str(t.rejected_count) if t.rejected_count else "0")

        rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows) + "\n"


def _render_judge_block(judge: "Any | None") -> str:
    if judge is None:
        return "_Judge was not run._\n"
    overall = getattr(judge, "overall_score", "?")
    rubric = getattr(judge, "rubric_path", "?")
    raw = getattr(judge, "raw_response", "")
    parts = [f"**Overall:** {overall}/5  ", f"**Rubric:** `{rubric}`", ""]
    findings = getattr(judge, "findings", []) or []
    if findings:
        parts.append("### Per-criterion findings\n")
        for f in findings:
            name = f.get("criterion", "?")
            score = f.get("score", "?")
            note = f.get("note", "")
            parts.append(f"- **{name}** ({score}/5): {note}")
        parts.append("")
    comments = getattr(judge, "comments", "") or ""
    if comments:
        parts.append("### Judge summary\n")
        parts.append(comments)
        parts.append("")
    if raw:
        parts.append("<details><summary>Raw judge response</summary>\n\n```json\n"
                     + raw[:6000]
                     + "\n```\n</details>\n")
    return "\n".join(parts)


def generate_report(
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    judge_result: "Any | None" = None,
    runs_dir: Path | None = None,
) -> Path:
    """Write REPORT.md to the run directory and return its path.

    Args:
      run_result: result from runner.run_scenario.
      eval_cfg: needed for token thresholds + flag_at_top list.
      judge_result: optional JudgeResult-like object (phase 5 fills this in).
        Should expose: overall_score: int, findings: list[dict],
        comments: str, raw_response: str, rubric_path: str, previous_overall: int | None.
      runs_dir: where prior runs live; defaults to dirname(run_result.output_dir).

    Always returns the report path; never raises on regression.
    """
    output_dir = Path(run_result.output_dir)
    runs_dir = runs_dir or output_dir.parent
    cur_events = _read_events(Path(run_result.events_jsonl_path))
    cur_metrics = _summarize_events(cur_events)

    prev_metrics: list[TurnMetrics] = []
    prev_run_path: Path | None = None
    prev_json = find_previous_run(runs_dir, run_result.scenario_id, exclude=output_dir)
    if prev_json is not None:
        prev_run_path = prev_json.parent
        prev_run = load_run_result(prev_json)
        prev_events = _read_events(Path(prev_run.events_jsonl_path))
        prev_metrics = _summarize_events(prev_events)

    regressions = _compute_regressions(
        cur_metrics,
        prev_metrics,
        warn_pct=eval_cfg.report.token_warn_pct,
        fail_pct=eval_cfg.report.token_fail_pct,
    )
    flags = _collect_flags(cur_metrics, regressions, run_result, judge_result)

    parts: list[str] = []
    parts.append(f"# Eval Report — `{run_result.scenario_id}`\n")
    parts.append(
        f"**Pack:** `{run_result.pack}` · **Model:** `{run_result.model}` · "
        f"**Temp override:** `{run_result.temperature_override}`  "
    )
    parts.append(
        f"**Started:** {run_result.started_at} · **Finished:** {run_result.finished_at}  "
    )
    parts.append(f"**Output dir:** `{run_result.output_dir}`  ")
    if prev_run_path is not None:
        parts.append(f"**Compared against:** `{prev_run_path}`")
    else:
        parts.append("**Compared against:** _(no prior run found)_")
    parts.append("")

    parts.append(_render_flag_block(flags, eval_cfg.report.flag_at_top))
    parts.append("")

    parts.append("## Per-turn metrics\n")
    parts.append(_render_per_turn_table(cur_metrics, prev_metrics))

    if regressions:
        warns = [r for r in regressions if r.severity == "warn"]
        if warns:
            parts.append("\n## Warnings (≥ warn threshold but < fail threshold)\n")
            for r in warns:
                parts.append(
                    f"- `{r.stream}` turn {r.turn}: "
                    f"{r.prev_tokens_in} → {r.cur_tokens_in} (+{r.pct_change:.1f}%)"
                )

    parts.append("\n## Judge\n")
    parts.append(_render_judge_block(judge_result))

    parts.append("\n## Runner turn timing\n")
    parts.append("| # | engine_turn | duration_s | error |")
    parts.append("|---|---:|---:|---|")
    for t in run_result.turns:
        parts.append(
            f"| {t.turn_number} | {t.engine_turn_number} | "
            f"{t.duration_s:.2f} | {t.error or '—'} |"
        )

    out_path = output_dir / "REPORT.md"
    out_path.write_text("\n".join(parts) + "\n")
    return out_path
```

### Update `ccya/eval/__init__.py`

Add report exports. Replace the file with:

```python
"""ccya eval harness.

Tier 2 of the eval system: live-LLM in-process driver, single judge, single scenario.
See ccya/plans/p3-inference/eval-harness.md.
"""

from ccya.eval.config import EvalConfig, load_eval_config
from ccya.eval.report import generate_report
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
    "generate_report",
    "load_eval_config",
    "load_run_result",
    "load_scenario",
    "run_scenario",
]
```

---

## Verification

```bash
# 1. Imports clean
uv run python -c "from ccya.eval import generate_report; print('report imports OK')"

# 2. End-to-end smoke: run scenario twice, generate report after second run
mkdir -p evals/scenarios
cat > evals/scenarios/_smoke.py <<'PY'
from ccya.eval.scenario import Scenario, Turn

scenario = Scenario(
    id="_smoke",
    pack="eval-pack",
    description="Two-turn smoke for report.",
    turns=[
        Turn(input="Look around the inn.", phase="dialogue"),
        Turn(input="Walk toward the merchant.", phase="dialogue"),
    ],
)
PY

MOCK_MODE=1 uv run python -c "
import asyncio
from pathlib import Path
from ccya.eval.config import load_eval_config
from ccya.eval.scenario import load_scenario
from ccya.eval.runner import run_scenario, REPO_ROOT
from ccya.eval.report import generate_report

async def main():
    sc = load_scenario('evals/scenarios/_smoke.py')
    cfg = load_eval_config()
    rr1 = await run_scenario(sc, eval_cfg=cfg, packs_dir=REPO_ROOT / 'evals' / 'packs')
    rr2 = await run_scenario(sc, eval_cfg=cfg, packs_dir=REPO_ROOT / 'evals' / 'packs')
    report_path = generate_report(rr2, eval_cfg=cfg)
    print('report written:', report_path)
    print(report_path.read_text()[:1500])

asyncio.run(main())
"

# 3. Inspect the generated report
test -f evals/runs/latest/REPORT.md
head -40 evals/runs/latest/REPORT.md

# 4. Cleanup
rm evals/scenarios/_smoke.py

# 5. Existing tests still pass
uv run pytest -q tests/test_engine_smoke.py
```

The report should contain:

- Header with scenario id, pack, model, temp, started/finished
- "Compared against" pointing at the first run's dir
- A flag block (likely "✅ No flags" since MOCK_MODE produces identical outputs)
- Per-turn metrics table with `(+0)` deltas for each stream
- Empty Judge block (`_Judge was not run._`)
- Runner timing table

If the per-turn table doesn't show columns for rules / narrate / scene / state /
progress, double-check `_extract_stream_metrics` and `_render_per_turn_table`.

---

## STOP HERE

Phase 4 is complete. Verify all checks pass, then stop and start a new chat with
`eval-harness/05-judge.md`.

### Handoff to phase 5

State after this phase:

- `ccya/eval/report.py` exists. `generate_report(run_result, eval_cfg=..., judge_result=...)` writes `REPORT.md` and returns its path.
- The report renders correctly even with `judge_result=None`.
- The report compares against the prior run via `find_previous_run` and shows token regression deltas.
- Critical regressions surface in a "⚠️ Flagged" block at the top per `eval_cfg.report.flag_at_top`.
- Always exits successfully — never raises.

Phase 5 builds the judge: an LLM call over `events.jsonl` using `evals/rubrics/default.md`. The judge returns a structured `JudgeResult` that `generate_report` already knows how to render via duck-typing (`overall_score`, `findings`, `comments`, `raw_response`, `rubric_path`, `previous_overall`).
