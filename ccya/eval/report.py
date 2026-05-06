"""Markdown report generator for eval runs.

Consumes the current RunResult + the previous run's events.jsonl and produces
REPORT.md in the run directory. Critical regressions surface at the top.
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
    judge: Any | None,
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
            if stream.startswith("extraction.") and sm.tokens_out == 0 and sm.tokens_in > 0 and not sm.skipped:
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

    # Parse failure flags
    rules_parse_total = sum(t.rules_parse_failures for t in run_result.turns)
    extract_parse_total = sum(t.extract_parse_failures for t in run_result.turns)
    if rules_parse_total:
        flags.append(
            Flag(
                kind="rules_parse_failures",
                summary=f"{rules_parse_total} rules parse failure(s) across the run",
                detail="\n".join(
                    f"- turn {t.turn_number}: {t.rules_parse_failures} failure(s)"
                    for t in run_result.turns
                    if t.rules_parse_failures
                ),
            ),
        )
    if extract_parse_total:
        flags.append(
            Flag(
                kind="extract_parse_failures",
                summary=f"{extract_parse_total} extract parse failure(s) across the run",
                detail="\n".join(
                    f"- turn {t.turn_number}: {t.extract_parse_failures} failure(s)"
                    for t in run_result.turns
                    if t.extract_parse_failures
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


def _render_judge_summary(judge: Any | None) -> str:
    """Render a single combined judge summary at the top of the report."""
    if judge is None:
        return ""
    overall = getattr(judge, "overall_score", "?")
    rubric = getattr(judge, "rubric_path", "?")
    findings = getattr(judge, "findings", []) or []
    comments = getattr(judge, "comments", "") or ""
    narrative_recap = getattr(judge, "narrative_recap", "") or ""
    remediation = getattr(judge, "remediation", "") or ""

    parts = [f"**Overall:** {overall}/5  ", f"**Rubric:** `{rubric}`", ""]
    if findings:
        for f in findings:
            name = f.get("criterion", "?")
            score = f.get("score", "?")
            note = f.get("note", "")
            parts.append(f"- **{name}** ({score}/5): {note}")
        parts.append("")
    if comments:
        parts.append(f"**Verdict:** {comments}")
        parts.append("")
    if narrative_recap:
        parts.append(f"**Narrative recap:** {narrative_recap}")
        parts.append("")
    if remediation:
        parts.append(f"**Remediation:** {remediation}")
        parts.append("")
    return "\n".join(parts)


def _render_combined_table(
    cur_metrics: list[TurnMetrics],
    prev_metrics: list[TurnMetrics],
    run_result: RunResult,
) -> str:
    """Render a combined table with tokens, timing, parse failures, and totals."""
    if not cur_metrics:
        return "_(no turns)_\n"

    rows: list[str] = []
    rows.append("| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |")
    rows.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    total_tok_in = 0
    total_tok_out = 0
    total_ms = 0
    total_duration = 0.0
    total_retries = 0
    total_parse_failures = 0

    def _delta(cur_v: int, prev_v: int | None) -> str:
        if prev_v is None or prev_v == 0:
            return str(cur_v)
        diff = cur_v - prev_v
        sign = "+" if diff >= 0 else "-"
        return f"{cur_v} ({sign}{abs(diff)})"

    for i, t in enumerate(cur_metrics):
        p = prev_metrics[i] if i < len(prev_metrics) else None

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
        total_retries += retries_in_turn
        cells.append(str(retries_in_turn) if retries_in_turn else "0")

        # Parse failures from TurnRecord
        parse_fails = 0
        if i < len(run_result.turns):
            parse_fails = (
                run_result.turns[i].rules_parse_failures
                + run_result.turns[i].extract_parse_failures
            )
        total_parse_failures += parse_fails
        cells.append(str(parse_fails) if parse_fails else "0")

        # Duration from TurnRecord
        duration = 0.0
        if i < len(run_result.turns):
            duration = run_result.turns[i].duration_s
        total_duration += duration
        cells.append(f"{duration:.2f}")

        # Accumulate totals
        for stream in _STREAM_KEYS:
            sm = t.streams.get(stream)
            if sm and not sm.skipped:
                total_tok_in += sm.tokens_in
                total_tok_out += sm.tokens_out
                total_ms += sm.ms

        rows.append("| " + " | ".join(cells) + " |")

    # Totals row
    total_cells = ["", "TOTALS"]
    for stream in _STREAM_KEYS:
        total_cells.append(str(total_tok_in))
    total_cells.extend([str(total_retries), str(total_parse_failures), f"{total_duration:.2f}"])
    rows.append("| " + " | ".join(total_cells) + " |")

    # Summary stats
    parts = [
        "",
        f"**Total turns:** {len(cur_metrics)} · **Total duration:** {total_duration:.2f}s · **Avg/turn:** {total_duration/len(cur_metrics):.2f}s",
        f"**Total tokens in:** {total_tok_in:,} · **Total tokens out:** {total_tok_out:,} · **Total LLM time:** {total_ms/1000:.1f}s",
        f"**Total retries:** {total_retries} · **Total parse failures:** {total_parse_failures}",
    ]

    return "\n".join(rows) + "\n" + "\n".join(parts) + "\n"


def _render_auto_checker_block(run_result: RunResult) -> str:
    """Render structured auto-checker results."""
    all_results: list[dict] = []
    for t in run_result.turns:
        for r in t.assert_results:
            all_results.append({"turn": t.turn_number, **r})

    if not all_results:
        return ""

    passed = sum(1 for r in all_results if r["passed"])
    failed = sum(1 for r in all_results if not r["passed"])

    parts = [f"**{passed} passed, {failed} failed**", ""]
    parts.append("| Turn | Assertion | Result | Detail |")
    parts.append("|---|---|---|---|")
    for r in all_results:
        status = "✅" if r["passed"] else "❌"
        parts.append(f"| {r['turn']} | `{r['assertion']}` | {status} | {r['detail']} |")
    parts.append("")
    return "\n".join(parts)


def generate_report(
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    judge_result: Any | None = None,
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

    # Judge summary at top
    judge_summary = _render_judge_summary(judge_result)
    if judge_summary:
        parts.append("## Judge Summary\n")
        parts.append(judge_summary)

    parts.append(_render_flag_block(flags, eval_cfg.report.flag_at_top))
    parts.append("")

    # Auto-checker results
    auto_block = _render_auto_checker_block(run_result)
    if auto_block:
        parts.append("## Auto-Checker\n")
        parts.append(auto_block)

    # Combined table at bottom
    parts.append("## Turn Metrics\n")
    parts.append(_render_combined_table(cur_metrics, prev_metrics, run_result))

    if regressions:
        warns = [r for r in regressions if r.severity == "warn"]
        if warns:
            parts.append("\n## Warnings (≥ warn threshold but < fail threshold)\n")
            for r in warns:
                parts.append(
                    f"- `{r.stream}` turn {r.turn}: "
                    f"{r.prev_tokens_in} → {r.cur_tokens_in} (+{r.pct_change:.1f}%)"
                )

    out_path = output_dir / "REPORT.md"
    out_path.write_text("\n".join(parts) + "\n")
    return out_path


if __name__ == "__main__":
    pass
