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

import logging

from ccya.eval.config import EvalConfig
from ccya.eval.judge import JudgeResult, merge_judge_scores
from ccya.eval.runner import RunResult, find_previous_run, load_run_result

_log = logging.getLogger("ccya.eval")


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
            ev = json.loads(s)
        except json.JSONDecodeError:
            continue
        if ev.get("__metadata__"):
            continue
        out.append(ev)
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
    judge: JudgeResult | list[JudgeResult] | None,
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
        if isinstance(judge, list):
            merged = merge_judge_scores(judge)
            representative = next((j for j in judge if j.judge_id == "meta"), judge[-1])
            prev_scores = representative.previous_scores or {}
        else:
            merged = judge.scores or {}
            prev_scores = judge.previous_scores or {}

        prev_score = prev_scores.get("mechanical_score")
        cur_score = merged.get("mechanical_score")
        if prev_score is not None and cur_score is not None and (prev_score - cur_score) >= 1:
            flags.append(
                Flag(
                    kind="judge_score_drop",
                    summary=f"judge mechanical {prev_score} → {cur_score} (-{prev_score - cur_score})",
                    detail="See judge verdict files for analysis.",
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


def _fmt_score(v: int | None) -> str:
    return str(v) if v is not None else "—"


def _fmt_rate(v: float | None) -> str:
    return f"{v*100:.1f}%" if v is not None else "—"


def _render_judge_summary(
    judges: list[JudgeResult] | JudgeResult | None,
) -> str:
    if judges is None:
        return ""
    if isinstance(judges, JudgeResult):
        judges = [judges]
    if not judges:
        return ""

    merged = merge_judge_scores(judges)
    meta = next((j for j in judges if j.judge_id == "meta"), judges[-1])

    parts: list[str] = []

    # Merged scores block
    parts.append(f"**Mechanical:** {_fmt_score(merged.get('mechanical_score'))}/5  ")
    parts.append(f"**Narrative:** {_fmt_score(merged.get('narrative_score'))}/5  ")
    parts.append(f"**System Cohesion:** {_fmt_score(merged.get('system_cohesion_score'))}/5  ")
    parts.append(f"**Prompt Quality:** {_fmt_score(merged.get('prompt_quality_score'))}/5  ")
    parts.append(f"**Compaction:** {_fmt_score(merged.get('compaction_score'))}/5  ")
    parts.append(f"**State Fidelity:** {_fmt_rate(merged.get('state_fidelity_rate'))}  ")
    parts.append(f"**Prompt Adherence:** {_fmt_rate(merged.get('prompt_adherence_rate'))}")
    parts.append(f"**Judge model:** `{meta.model}`")
    ps = merged.get("pipeline_scores") or {}
    if ps:
        parts.append("")
        parts.append("**Pipeline scores:**")
        for k in ("rules", "narrate", "extract_scene", "extract_state", "extract_progress"):
            parts.append(f"- {k}: {_fmt_score(ps.get(k))}/5")
    parts.append("")

    # Domain judge breakdown table
    domain_judges = [j for j in judges if j.judge_id != "meta"]
    if len(domain_judges) > 1:
        parts.append("**Domain judge breakdown:**")
        parts.append("")
        parts.append("| Judge | Scores |")
        parts.append("|---|---|")
        for jr in domain_judges:
            score_items = []
            for k, v in (jr.scores or {}).items():
                if k == "pipeline_scores":
                    continue
                if isinstance(v, float):
                    score_items.append(f"{k}={_fmt_rate(v)}")
                else:
                    score_items.append(f"{k}={_fmt_score(v)}")
            parts.append(f"| `{jr.judge_id}` | {', '.join(score_items)} |")
        parts.append("")

    # Previous scores comparison (use meta or last judge)
    if meta.previous_scores:
        prev_mech = meta.previous_scores.get("mechanical_score")
        prev_narr = meta.previous_scores.get("narrative_score")
        if prev_mech is not None:
            parts.append(f"**Previous mechanical:** {prev_mech}/5")
        if prev_narr is not None:
            parts.append(f"**Previous narrative:** {prev_narr}/5")
        parts.append("")

    # Artifact links for all judges
    for jr in judges:
        label = jr.judge_id
        parts.append(
            f"**[{label} trace]({Path(jr.trace_md_path).name})** · "
            f"**[{label} verdict]({Path(jr.judge_md_path).name})**  "
        )
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
    stream_tok_in: dict[str, int] = {s: 0 for s in _STREAM_KEYS}

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
                stream_tok_in[stream] += sm.tokens_in

        rows.append("| " + " | ".join(cells) + " |")

    # Totals row
    total_cells = ["", "TOTALS"]
    for stream in _STREAM_KEYS:
        total_cells.append(str(stream_tok_in[stream]))
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
    """Render structured auto-checker results with engine turn numbers."""
    if not run_result.turns:
        return ""

    passed = sum(1 for t in run_result.turns for r in t.assert_results if r["passed"])
    failed = sum(1 for t in run_result.turns for r in t.assert_results if not r["passed"])

    parts: list[str] = [f"**{passed} passed, {failed} failed**", ""]
    parts.append("| Turn | Assertion | Result | Detail |")
    parts.append("|---|---|---|---|")
    for t in run_result.turns:
        for r in t.assert_results:
            status = "✅" if r["passed"] else "❌"
            parts.append(f"| {t.engine_turn_number} | `{r['assertion']}` | {status} | {r['detail']} |")
    parts.append("")
    return "\n".join(parts)


def _render_assert_summary_table(run_result: RunResult) -> str:
    """Render a summary table of universal assert results across all turns."""
    if not run_result.turns:
        return ""

    # Collect per-assertion stats
    assertion_stats: dict[str, dict[str, Any]] = {}
    for t in run_result.turns:
        for r in t.assert_results:
            name = r["assertion"]
            if name not in assertion_stats:
                assertion_stats[name] = {
                    "total": 0,
                    "failed": 0,
                    "first_failure": None,
                    "severity": r.get("severity", "red"),
                }
            assertion_stats[name]["total"] += 1
            if not r["passed"]:
                assertion_stats[name]["failed"] += 1
                if assertion_stats[name]["first_failure"] is None:
                    assertion_stats[name]["first_failure"] = t.engine_turn_number

    if not assertion_stats:
        return ""

    lines: list[str] = ["## Universal Assert Results", ""]
    lines.append("| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |")
    lines.append("|---|---|---:|---:|---:|")

    for name, stats in sorted(assertion_stats.items()):
        sev = stats["severity"]
        sev_mark = "🔴" if sev == "red" else "🟡"
        failed = stats["failed"]
        total = stats["total"]
        first_fail = f"T{stats['first_failure']}" if stats["first_failure"] is not None else "—"
        lines.append(f"| `{name}` | {sev_mark} | {failed} | {total} | {first_fail} |")

    lines.append("")
    return "\n".join(lines)


def _compute_pacing_metrics(events: list[dict[str, Any]]) -> str:
    """Compute pacing metrics from events. Returns markdown string."""
    if not events:
        return ""

    lines: list[str] = ["## Pacing Metrics", ""]

    # Pressure duration table
    pressure_first: dict[str, int] = {}
    pressure_last: dict[str, int] = {}
    for ev in events:
        pressures = ((ev.get("state_snapshot") or {}).get("scene") or {}).get("scene_pressure") or []
        meta = (ev.get("state_snapshot") or {}).get("meta") or {}
        cur_turn = int(meta.get("turn") or 0) if isinstance(meta, dict) else 0
        for p in pressures:
            if not isinstance(p, dict):
                continue
            pid = p.get("id", "?")
            if pid not in pressure_first:
                pressure_first[pid] = cur_turn
            pressure_last[pid] = cur_turn

    if pressure_first:
        lines.append("### Pressure Duration")
        lines.append("")
        lines.append("| Pressure ID | First Turn | Last Turn | Duration (turns) | Flagged |")
        lines.append("|---|---|---:|---:|---|")
        for pid in sorted(pressure_first.keys()):
            first = pressure_first[pid]
            last = pressure_last[pid]
            duration = last - first + 1
            flagged = "⚠️ >8 turns" if duration > 8 else ""
            lines.append(f"| `{pid}` | T{first} | T{last} | {duration} | {flagged} |")
        lines.append("")

    # Location dwell table
    location_dwell: dict[str, dict[str, Any]] = {}
    for ev in events:
        meta = (ev.get("state_snapshot") or {}).get("meta") or {}
        cur_turn = int(meta.get("turn") or 0) if isinstance(meta, dict) else 0
        loc = ((ev.get("state_snapshot") or {}).get("location") or {}).get("id")
        if not loc:
            continue
        if loc not in location_dwell:
            location_dwell[loc] = {"first": cur_turn, "last": cur_turn, "turns": [cur_turn]}
        else:
            location_dwell[loc]["last"] = cur_turn
            location_dwell[loc]["turns"].append(cur_turn)

    if location_dwell:
        lines.append("### Location Dwell")
        lines.append("")
        lines.append("| Location ID | Turns Active | Flagged |")
        lines.append("|---|---:|---|")
        for loc_id in sorted(location_dwell.keys()):
            info = location_dwell[loc_id]
            dwell = info["last"] - info["first"] + 1
            flagged = "⚠️ >4 turns" if dwell > 4 else ""
            lines.append(f"| `{loc_id}` | {dwell} | {flagged} |")
        lines.append("")

    # Momentum floor runs
    floor_runs: list[tuple[int, int]] = []
    current_run_start: int | None = None
    for ev in events:
        meta = (ev.get("state_snapshot") or {}).get("meta") or {}
        cur_turn = int(meta.get("turn") or 0) if isinstance(meta, dict) else 0
        m = ((ev.get("state_snapshot") or {}).get("meta") or {}).get("momentum")
        if m is not None and m <= -3:
            if current_run_start is None:
                current_run_start = cur_turn
        else:
            if current_run_start is not None:
                floor_runs.append((current_run_start, cur_turn - 1))
                current_run_start = None
    if current_run_start is not None:
        floor_runs.append((current_run_start, events[-1].get("turn", 0) if events else 0))

    if floor_runs:
        lines.append("### Momentum Floor Runs")
        lines.append("")
        lines.append("| Run Start | Run End | Duration (turns) |")
        lines.append("|---|---|---:|")
        for start, end in floor_runs:
            duration = end - start + 1
            lines.append(f"| T{start} | T{end} | {duration} |")
        lines.append("")

    # Condition duration
    condition_first: dict[str, int] = {}
    condition_last: dict[str, int] = {}
    for ev in events:
        meta = (ev.get("state_snapshot") or {}).get("meta") or {}
        cur_turn = int(meta.get("turn") or 0) if isinstance(meta, dict) else 0
        conds = ((ev.get("state_snapshot") or {}).get("pc") or {}).get("conditions") or []
        for c in conds:
            if not isinstance(c, dict):
                continue
            cid = c.get("id", "?")
            if cid not in condition_first:
                condition_first[cid] = cur_turn
            condition_last[cid] = cur_turn

    if condition_first:
        lines.append("### Condition Duration")
        lines.append("")
        lines.append("| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |")
        lines.append("|---|---|---:|---:|---|")
        for cid in sorted(condition_first.keys()):
            first = condition_first[cid]
            last = condition_last[cid]
            duration = last - first + 1
            flagged = "⚠️ >6 turns" if duration > 6 else ""
            lines.append(f"| `{cid}` | T{first} | T{last} | {duration} | {flagged} |")
        lines.append("")

    return "\n".join(lines)


_JUDGE_STREAM_SENTINEL_OPEN = "<!-- JUDGE_STREAM_OPEN -->\n"
_JUDGE_STREAM_SENTINEL_CLOSE = "<!-- JUDGE_STREAM_CLOSE -->\n"


def write_report_skeleton(
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    runs_dir: Path | None = None,
) -> Path:
    """Write REPORT.md with everything except the judge body. Returns the path.

    The judge section contains a placeholder: '## Judge (streaming…)' followed by
    a single empty fenced code block. Phase 05.2's appender writes into the
    fence; Phase 05.3's finalizer rewrites the whole file with the judge body
    hoisted into a normal section.
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
        cur_metrics, prev_metrics,
        warn_pct=eval_cfg.report.token_warn_pct,
        fail_pct=eval_cfg.report.token_fail_pct,
    )
    flags = _collect_flags(cur_metrics, regressions, run_result, judge=None)

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
    parts.append(
        f"**Compared against:** `{prev_run_path}`" if prev_run_path is not None
        else "**Compared against:** _(no prior run found)_"
    )
    parts.append("")
    parts.append("## Judge (streaming…)\n")
    parts.append("_Judge response is streaming live below. This block will be replaced with the parsed verdict once the call completes._\n")
    parts.append("```\n")
    parts.append(_JUDGE_STREAM_SENTINEL_OPEN)
    parts.append(_JUDGE_STREAM_SENTINEL_CLOSE)
    parts.append("```\n")
    parts.append(_render_flag_block(flags, eval_cfg.report.flag_at_top))
    parts.append("")
    auto_block = _render_auto_checker_block(run_result)
    if auto_block:
        parts.append("## Auto-Checker\n")
        parts.append(auto_block)
    assert_table = _render_assert_summary_table(run_result)
    if assert_table:
        parts.append(assert_table)
    pacing = _compute_pacing_metrics(cur_events)
    if pacing:
        parts.append(pacing)
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


def append_judge_chunk(report_path: Path, chunk: str) -> None:
    """Append a streamed-judge token-or-chunk to REPORT.md atomically.

    Reads the file, inserts `chunk` immediately before _SENTINEL_CLOSE, writes
    back. Cheap because the file is small until the judge produces real volume.
    For very long judge outputs this becomes O(n^2) over chunks — acceptable
    because chunks are coarse (full sentences) and total judge output is
    bounded at ~64K tokens.
    """
    text = report_path.read_text()
    if _JUDGE_STREAM_SENTINEL_CLOSE not in text:
        return                          # finalize already ran or skeleton missing
    new_text = text.replace(
        _JUDGE_STREAM_SENTINEL_CLOSE,
        chunk + _JUDGE_STREAM_SENTINEL_CLOSE,
        1,
    )
    report_path.write_text(new_text)


def finalize_report(
    report_path: Path,
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    judge_result: JudgeResult | list[JudgeResult],
    runs_dir: Path | None = None,
) -> None:
    """Rewrite REPORT.md with the judge summary hoisted to the top.

    The streaming sentinel block is removed; a proper judge summary block is
    inserted after the metadata header; the parsed scores update the flag
    computation (judge_score_drop) so the flag block reflects them.
    """
    judges = judge_result if isinstance(judge_result, list) else [judge_result]

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
        cur_metrics, prev_metrics,
        warn_pct=eval_cfg.report.token_warn_pct,
        fail_pct=eval_cfg.report.token_fail_pct,
    )
    flags = _collect_flags(cur_metrics, regressions, run_result, judges)

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
    parts.append(
        f"**Compared against:** `{prev_run_path}`" if prev_run_path is not None
        else "**Compared against:** _(no prior run found)_"
    )
    parts.append("")
    parts.append("## Judge Summary\n")
    parts.append(_render_judge_summary(judges))
    parts.append(_render_flag_block(flags, eval_cfg.report.flag_at_top))
    parts.append("")

    # One verdict section per judge, meta last
    domain_judges = [j for j in judges if j.judge_id != "meta"]
    meta_judge = next((j for j in judges if j.judge_id == "meta"), None)
    for jr in domain_judges:
        parts.append(f"## Judge Verdict — `{jr.judge_id}`\n")
        parts.append(jr.body_md)
        parts.append("")
    if meta_judge:
        parts.append("## Meta Judge Verdict\n")
        parts.append(meta_judge.body_md)
        parts.append("")

    auto_block = _render_auto_checker_block(run_result)
    if auto_block:
        parts.append("## Auto-Checker\n")
        parts.append(auto_block)
    assert_table = _render_assert_summary_table(run_result)
    if assert_table:
        parts.append(assert_table)
    pacing = _compute_pacing_metrics(cur_events)
    if pacing:
        parts.append(pacing)
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

    tmp = report_path.with_suffix(".md.tmp")
    tmp.write_text("\n".join(parts) + "\n")
    tmp.replace(report_path)


def generate_report(
    run_result: RunResult,
    *,
    eval_cfg: EvalConfig,
    judge_result: JudgeResult | list[JudgeResult] | None = None,
    runs_dir: Path | None = None,
) -> Path:
    """Back-compat entry point. New code should call write_report_skeleton/finalize_report directly."""
    if judge_result is not None:
        path = write_report_skeleton(run_result, eval_cfg=eval_cfg, runs_dir=runs_dir)
        finalize_report(path, run_result, eval_cfg=eval_cfg, judge_result=judge_result, runs_dir=runs_dir)
    else:
        path = write_report_skeleton(run_result, eval_cfg=eval_cfg, runs_dir=runs_dir)
    return path


if __name__ == "__main__":
    pass
