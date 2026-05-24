"""Metrics formatting helpers for the debug panel."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ccya.engine import format_change_lines

_log = logging.getLogger(__name__)


def _fmt_ms_seconds(ms: Any) -> str:
    if ms is None:
        return "\u2014"
    try:
        return f"{float(ms) / 1000.0:.1f}s"
    except (TypeError, ValueError):
        _log.debug("_fmt_ms_seconds non-numeric ms=%r", ms)
        return "\u2014"


def _fmt_tokens(n: Any) -> str:
    if n is None:
        return "\u2014"
    try:
        n = int(n)
    except (TypeError, ValueError):
        _log.debug("_fmt_tokens non-numeric n=%r", n)
        return "\u2014"
    if n < 1000:
        return str(n)
    return f"{n / 1000:.2f}".rstrip("0").rstrip(".") + "k"


def _fmt_tokens_exact(n: Any) -> str:
    """Format token count as exact integer string."""
    if n is None:
        return "\u2014"
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        _log.debug("_fmt_tokens_exact non-numeric n=%r", n)
        return "\u2014"


def _recent_turn_metrics(save_dir: Path, n: int = 10) -> list[dict[str, Any]]:
    """Last n turns from events.jsonl, newest first, for the Debug panel."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    raw = path.read_text().strip()
    if not raw:
        return []
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return []
    chunk = lines[-n:]
    rows: list[dict[str, Any]] = []
    for line in chunk:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            _log.warning("Skipping malformed events.jsonl line in _recent_turn_metrics: %s", e)
            continue
        if ev.get("kind") == "compaction":
            compact_start = int(ev.get("compact_start") or 0)
            compact_end = int(ev.get("compact_end") or 0)
            range_label = f"turn {compact_start}" if compact_start == compact_end else f"turns {compact_start}-{compact_end}"
            compact_ms = ev.get("ms")
            c_tin = ev.get("tokens_in")
            c_tout = ev.get("tokens_out")
            rows.append({
                "turn": ev.get("turn", 0),
                "is_compaction": True,
                "pipe_label": f"Compaction ({range_label})",
                "time": _fmt_ms_seconds(compact_ms) if compact_ms else "\u2014",
                "tok": f"{_fmt_tokens(c_tin)}/{_fmt_tokens(c_tout)}" if (c_tin and c_tout) else "\u2014",
            })
            continue
        narr = ev.get("narrate") or {}
        ext = ev.get("extract") or {}
        extraction = ev.get("extraction") or {}
        rej = ev.get("rejected") or []
        tid = str(ev.get("trace_id") or "")
        n_in, n_out = narr.get("tokens_in"), narr.get("tokens_out")
        tin, tout = ext.get("tokens_in"), ext.get("tokens_out")
        raw_streams: dict[str, dict[str, Any]] = {}
        for s in ("scene", "state", "storytell"):
            sev = extraction.get(s) or {}
            raw_streams[s] = {
                "ms": sev.get("ms"),
                "tokens_in": sev.get("tokens_in"),
                "tokens_out": sev.get("tokens_out"),
                "skipped": sev.get("skipped", False),
            }
        tok_parts: list[str] = []
        if n_in is not None and n_out is not None:
            tok_parts.append(f"N{_fmt_tokens(n_in)}/{_fmt_tokens(n_out)}")
        if tin is not None and tout is not None:
            tok_parts.append(f"E{_fmt_tokens(tin)}/{_fmt_tokens(tout)}")
        tok = "\n".join(tok_parts) if tok_parts else "\u2014"
        ruling_ev = ev.get("ruling") or {}

        def _tok(ti: Any = None, to: Any = None) -> str:
            if ti is None or to is None:
                return "\u2014"
            return f"{_fmt_tokens(ti)}/{_fmt_tokens(to)}"

        rows.append(
            {
                "turn": ev.get("turn", 0),
                "trace_id": tid[:8] if len(tid) >= 8 else tid,
                "trace_id_full": tid,
                "narrate_s": _fmt_ms_seconds(narr.get("total_ms")),
                "extract_s": _fmt_ms_seconds(ext.get("total_ms")),
                "retries": int(ext.get("retries", 0) or 0),
                "tokens": tok,
                "has_rejections": bool(rej),
                "streams": {
                    "R_tt": _fmt_ms_seconds(ruling_ev.get("total_ms")),
                    "R_tok": _tok(ruling_ev.get("tokens_in"), ruling_ev.get("tokens_out")),
                    "N_ttft": _fmt_ms_seconds(narr.get("first_token_ms")),
                    "N_tt": _fmt_ms_seconds(narr.get("total_ms")),
                    "N_tok": _tok(n_in, n_out),
                    "Sc_tt": _fmt_ms_seconds(raw_streams["scene"]["ms"]) if not raw_streams["scene"]["skipped"] else "\u2014",
                    "Sc_tok": _tok(raw_streams["scene"]["tokens_in"], raw_streams["scene"]["tokens_out"]) if not raw_streams["scene"]["skipped"] else "\u2014",
                    "St_tt": _fmt_ms_seconds(raw_streams["state"]["ms"]) if not raw_streams["state"]["skipped"] else "\u2014",
                    "St_tok": _tok(raw_streams["state"]["tokens_in"], raw_streams["state"]["tokens_out"]) if not raw_streams["state"]["skipped"] else "\u2014",
                    "P_tt": _fmt_ms_seconds(raw_streams["storytell"]["ms"]) if not raw_streams["storytell"]["skipped"] else "\u2014",
                    "P_tok": _tok(raw_streams["storytell"]["tokens_in"], raw_streams["storytell"]["tokens_out"]) if not raw_streams["storytell"]["skipped"] else "\u2014",
                },
                "total_ms": (
                    (ruling_ev.get("total_ms") or 0)
                    + (narr.get("total_ms") or 0)
                    + (ext.get("total_ms") or 0)
                ),
                "total_tokens_in": (
                    (ruling_ev.get("tokens_in") or 0)
                    + (n_in or 0)
                    + (tin or 0)
                ),
                "total_tokens_out": (
                    (ruling_ev.get("tokens_out") or 0)
                    + (n_out or 0)
                    + (tout or 0)
                ),
                "total_tt": _fmt_ms_seconds(
                    (ruling_ev.get("total_ms") or 0)
                    + (narr.get("total_ms") or 0)
                    + (ext.get("total_ms") or 0)
                ),
                "total_tok": f"{_fmt_tokens((ruling_ev.get('tokens_in') or 0) + (n_in or 0) + (tin or 0))}/{_fmt_tokens((ruling_ev.get('tokens_out') or 0) + (n_out or 0) + (tout or 0))}",
            }
        )
    rows.reverse()
    return rows


def _turn_log_entries(save_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Build rows for _turn_log.html from events.jsonl (newest first)."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    raw = path.read_text().strip()
    if not raw:
        return []
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return []
    tail = lines[-limit:]
    entries: list[dict[str, Any]] = []
    for line in reversed(tail):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            _log.warning("Skipping malformed events.jsonl line in _turn_log_entries: %s", e)
            continue
        if ev.get("kind") == "compaction":
            continue
        ch = ev.get("changes")
        if isinstance(ch, dict):
            disp = format_change_lines(ch)
        else:
            disp = ["(no structured summary — older save)"]
        if not disp:
            disp = ["(no changes this turn)"]
        ruling = ev.get("ruling")
        entries.append(
            {
                "turn": int(ev.get("turn") or 0),
                "lines": disp,
                "ruling": ruling if isinstance(ruling, dict) else None,
            }
        )
    return entries
