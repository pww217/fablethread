"""Single LLM judge over events.jsonl.

One call, one rubric, structured JSON output. Truncates input to fit the
configured judge model's window. Parses tolerantly — one bad turn shouldn't kill
the eval.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ccya.eval.config import EvalConfig
from ccya.eval.engine_mirror import constants_block
from ccya.llm_client import chat, strip_thinking
from ccya.models import load_config

_log = logging.getLogger("ccya.eval")


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class JudgeResult:
    overall_score: int
    findings: list[dict[str, Any]] = field(default_factory=list)
    comments: str = ""
    raw_response: str = ""
    rubric_path: str = ""
    model: str = ""
    previous_overall: int | None = None
    narrative_recap: str = ""
    remediation: str = ""


# ---------------------------------------------------------------------------
# Trace builder
# ---------------------------------------------------------------------------


_NARRATE_TRUNC = 800
_EXTRACT_TRUNC = 300


def _summarize_applied(applied: dict[str, Any]) -> str:
    parts: list[str] = []
    for k in ("inventory_add", "inventory_remove", "inventory_update"):
        v = applied.get(k) or []
        if v:
            parts.append(f"{k}={len(v)}")
    for k in ("pc_condition_add", "pc_condition_remove"):
        v = applied.get(k) or []
        if v:
            parts.append(f"{k}={len(v)}")
    for k in ("quest_updates", "recent_events_add", "compendium_npc_update"):
        v = applied.get(k) or []
        if v:
            parts.append(f"{k}={len(v)}")
    if applied.get("location_change"):
        parts.append("location_change")
    if applied.get("scene_tags"):
        parts.append(f"scene_tags={applied['scene_tags']}")
    return ", ".join(parts) or "(no changes)"


def _summarize_rejected(rejected: list[Any]) -> str:
    if not rejected:
        return "(none)"
    return f"{len(rejected)} rejected: " + json.dumps(rejected[:3], default=str)[:200]


def _trim(s: str, n: int) -> str:
    s = s or ""
    if len(s) <= n:
        return s
    return s[:n].rstrip() + "…"


def _context_line(event: dict[str, Any]) -> str:
    """Summarize per-stream context sizes and truncation for the judge."""
    parts = []
    narrate = event.get("narrate_prompt") or {}
    nm = narrate.get("context_meta") or {}
    if nm:
        trunc = " TRIMMED" if nm.get("trimmed") else ""
        parts.append(f"narrate={nm.get('est_tokens', '?')}t{trunc}")

    extraction = event.get("extraction") or {}
    for stream in ("scene", "state", "progress"):
        ex = extraction.get(stream) or {}
        cm = ex.get("context_meta") or {}
        if cm:
            trunc = " TRIMMED" if cm.get("trimmed") else ""
            parts.append(f"{stream}={cm.get('est_tokens', '?')}t{trunc}")

    return ", ".join(parts) if parts else "(no context telemetry)"


def _scope_summary(rules_event: dict[str, Any] | None, narrate_prompt: dict[str, Any]) -> str:
    """Scope is now in the narrator's <scope>...</scope> tail in narrate output."""
    raw = narrate_prompt.get("output", "")
    raw = strip_thinking(raw or "")
    m = re.search(r"<scope>(.*?)</scope>", raw, re.DOTALL)
    if not m:
        return "active=? (no tail)"
    try:
        data = json.loads(m.group(1).strip())
        active = data.get("active_domains", [])
        return f"active={active}"
    except (json.JSONDecodeError, AttributeError):
        return "active=? (unparseable)"


def build_trace(events: list[dict[str, Any]], *, max_chars: int) -> str:
    """Build the compact trace string sent to the judge as the user message."""
    lines: list[str] = [constants_block()]
    blocks: list[str] = []
    for ev in events:
        turn = ev.get("turn", "?")
        inp = ev.get("input", "")
        rules = ev.get("rules") or {}
        narrate_prompt = ev.get("narrate_prompt") or {}
        extraction = ev.get("extraction") or {}
        applied = ev.get("applied") or {}
        rejected = ev.get("rejected") or []

        scene = (extraction.get("scene") or {}).get("output", "")
        state = (extraction.get("state") or {}).get("output", "")
        progress = (extraction.get("progress") or {}).get("output", "")
        narration = narrate_prompt.get("output", "")

        scope_line = _scope_summary(rules, narrate_prompt)
        rules_line = (
            f"band={rules.get('band', '—')} skill={rules.get('skill', '—')} "
            f"summary={(rules.get('outcome_summary') or '')[:140]}"
            if rules and rules.get("rolled")
            else f"intent_only verb={rules.get('intent_verb', '—') if rules else '—'}"
        )

        block = (
            f"TURN {turn} — {inp}\n"
            f"[context] {_context_line(ev)}\n"
            f"[scope] {scope_line}\n"
            f"[rules] {rules_line}\n"
            f"[narrate] {_trim(narration, _NARRATE_TRUNC)}\n"
            f"[extract.scene] {_trim(scene, _EXTRACT_TRUNC)}\n"
            f"[extract.state] {_trim(state, _EXTRACT_TRUNC)}\n"
            f"[extract.progress] {_trim(progress, _EXTRACT_TRUNC)}\n"
            f"[applied] {_summarize_applied(applied)}\n"
            f"[rejected] {_summarize_rejected(rejected)}\n"
            f"---\n"
        )
        blocks.append(block)

    full = "\n".join(blocks)
    trace = "\n".join(lines) + full
    if len(trace) <= max_chars:
        return trace
    _TRUNC_MARKER = "\n\n[... trace truncated to fit judge window ...]\n\n"
    head_keep = max(int(max_chars * 0.6), len(lines[0]) + 1)
    tail_keep = max_chars - head_keep - len(_TRUNC_MARKER)
    return (
        trace[:head_keep]
        + _TRUNC_MARKER
        + trace[-tail_keep:]
    )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _find_json_object(text: str) -> str | None:
    """Find the outermost JSON object in text by counting brace depth."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_judge_response(raw: str) -> dict[str, Any]:
    """Best-effort JSON extraction from a judge response.

    Strips think tags, finds the outermost JSON object, returns the parsed dict.
    Raises ValueError on unrecoverable output.
    """
    s = strip_thinking(raw or "")
    s = s.strip()
    if s.startswith("```"):
        # markdown fence; strip first and last line
        s = "\n".join(s.splitlines()[1:-1])
    obj = _find_json_object(s)
    if obj is None:
        raise ValueError("no JSON object found in judge response")
    try:
        return json.loads(obj)  # type: ignore[no-any-return]
    except json.JSONDecodeError as exc:
        raise ValueError(f"judge JSON parse failed: {exc}") from exc


def _coerce_score(v: Any) -> int:
    try:
        n = int(round(float(v)))
    except (TypeError, ValueError):
        return 0
    return max(1, min(5, n))


# ---------------------------------------------------------------------------
# Previous-run lookup (for previous_overall)
# ---------------------------------------------------------------------------


_OVERALL_RE = re.compile(r"\*\*Overall:\*\*\s*(\d+)\s*/\s*5", re.MULTILINE)


def _lookup_previous_overall(prev_report_path: Path) -> int | None:
    if not prev_report_path.exists():
        return None
    txt = prev_report_path.read_text()
    m = _OVERALL_RE.search(txt)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def run_judge(
    events_path: Path,
    *,
    eval_cfg: EvalConfig,
    previous_report_path: Path | None = None,
    game_config_path: Path | None = None,
) -> JudgeResult:
    """Read events.jsonl, send to judge, return JudgeResult.

    Honors MOCK_MODE via llm_client (returns canned response — score will be
    parsed from the mock and JudgeResult will have overall_score=0).
    """
    rubric_path = Path(eval_cfg.judge.rubric_path)
    if not rubric_path.is_absolute():
        rubric_path = REPO_ROOT / rubric_path
    if not rubric_path.exists():
        raise FileNotFoundError(f"rubric not found: {rubric_path}")
    rubric_text = rubric_path.read_text()

    cfg_path = game_config_path or (REPO_ROOT / "config.yaml")
    game_cfg = load_config(cfg_path)
    llm = game_cfg.get("llm", {})
    host = str(llm.get("host", "http://localhost:8080/v1"))
    judge_model = eval_cfg.judge.model or str(llm.get("model", ""))
    if not judge_model:
        raise ValueError("judge model not set (eval_cfg.judge.model is null AND game config llm.model is empty)")

    events_lines = events_path.read_text().splitlines() if events_path.exists() else []
    events = [json.loads(line) for line in events_lines if line.strip()]
    trace = build_trace(events, max_chars=eval_cfg.judge.max_input_chars)
    _log.debug("judge: %d events, trace=%d chars", len(events), len(trace))

    messages = [
        {"role": "system", "content": rubric_text},
        {"role": "user", "content": trace},
    ]

    resp = await chat(
        host=host,
        model=judge_model,
        messages=messages,
        temperature=eval_cfg.judge.temperature,
    )
    raw = resp.get("response", "") or ""

    overall = 0
    findings: list[dict[str, Any]] = []
    comments = ""
    narrative_recap = ""
    remediation = ""
    try:
        parsed = parse_judge_response(raw)
        overall = _coerce_score(parsed.get("overall_score", 0))
        for f in parsed.get("findings") or []:
            if not isinstance(f, dict):
                continue
            findings.append(
                {
                    "criterion": str(f.get("criterion", "")),
                    "score": _coerce_score(f.get("score", 0)),
                    "note": str(f.get("note", "")),
                    "turns": [int(t) for t in (f.get("turns") or []) if str(t).isdigit()],
                }
            )
        comments = str(parsed.get("comments", ""))
        narrative_recap = str(parsed.get("narrative_recap", ""))
        remediation = str(parsed.get("remediation", ""))
        _log.debug("judge parsed: overall=%d findings=%d", overall, len(findings))
    except ValueError as exc:
        comments = f"(judge response could not be parsed: {exc})"
        _log.debug("judge parse failed: %s", exc)

    previous_overall = (
        _lookup_previous_overall(previous_report_path) if previous_report_path else None
    )

    return JudgeResult(
        overall_score=overall,
        findings=findings,
        comments=comments,
        raw_response=raw,
        rubric_path=str(rubric_path),
        model=judge_model,
        previous_overall=previous_overall,
        narrative_recap=narrative_recap,
        remediation=remediation,
    )
