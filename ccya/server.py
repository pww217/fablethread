"""FastAPI server: SSE /turn (GET), HTMX panels, errors store."""

from __future__ import annotations

import asyncio
import json
import os
from collections import deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, pass_context
from sse_starlette.sse import EventSourceResponse

from ccya.engine import (
    EngineConfig,
    format_change_lines,
    generate_seed,
    is_turn_in_progress,
    run_turn,
    warmup,
)
from ccya.logging_setup import setup_logging
from ccya.models import load_config as _load_config
from ccya.pack import Pack, load_pack, list_packs
from ccya.state import init_save_dir, load_recent_chronicle_turns, load_state

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
PROMPTS_DIR = BASE_DIR / "prompts"
PACKS_DIR = BASE_DIR.parent / "packs"
SAVE_DIR = Path("saves") / "default"

config: dict[str, Any] = _load_config(BASE_DIR.parent / "config.yaml")
engine_config = EngineConfig(
    host=config["llm"]["host"],
    model=config["llm"]["model"],
    prompt_token_budget=config["llm"].get("prompt_token_budget", 28672),
    request_timeout_s=config["llm"]["request_timeout_s"],
    narrate_temperature=config["llm"]["narrate_temperature"],
    extract_temperature=config["llm"]["extract_temperature"],
    max_extract_retries=config["llm"]["max_extract_retries"],
    window_turns=config["game"]["window_turns"],
    chronicle_prefix_budget_tokens=config["game"]["chronicle_prefix_budget_tokens"],
    recent_events_max=config["game"]["recent_events_max"],
    enable_extract_thinking=config["llm"].get("enable_extract_thinking", False),
    enable_narrate_thinking=config["llm"].get("enable_narrate_thinking", False),
    generate_seed_temperature=config["llm"].get("generate_seed_temperature", 0.9),
    generate_seed_max_retries=config["llm"].get("generate_seed_max_retries", 1),
    log_llm_io=config.get("logging", {}).get("log_llm_io", False),
    log_llm_io_max_chars=config.get("logging", {}).get("log_llm_io_max_chars", 4000),
    log_prompts=config.get("logging", {}).get("log_prompts", False),
    rules_temperature=config.get("rules", {}).get("temperature", 0.2),
    max_rules_retries=config.get("rules", {}).get("max_retries", 1),
)

logger = setup_logging(config)

_pack_id: str = config.get("game", {}).get("setting_pack", "expanse-belter")
try:
    _active_pack: Pack = load_pack(_pack_id, PACKS_DIR)
    logger.info("Loaded pack: %s (mode=%s)", _pack_id, _active_pack.manifest.mode)
except Exception as exc:
    logger.error("Failed to load pack %r: %s", _pack_id, exc)
    raise

_dynamic_opening: str = ""
_dynamic_opening_actions: list[str] = []

app = FastAPI(title="ccya")
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)
_jinja_env.filters["tojson"] = pass_context(lambda ctx, obj: __import__("json").dumps(obj))

# In-process errors store — last 50 entries, survives turn boundaries.
_ERRORS_LOG: deque[dict[str, Any]] = deque(maxlen=50)


def _render(template_name: str, context: dict[str, Any]) -> HTMLResponse:
    template = _jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _validate_stats(stats: dict[str, int]) -> bool:
    SKILLS = {"strength", "dexterity", "wits", "lore", "charisma", "resolve"}
    if set(stats.keys()) != SKILLS:
        return False
    if not all(isinstance(v, int) and 1 <= v <= 4 for v in stats.values()):
        return False
    total = sum(stats.values())
    return 12 <= total <= 16


def _load_current_state() -> dict[str, Any]:
    return load_state(SAVE_DIR)


def _load_rules_map(save_dir: Path) -> dict[int, dict[str, Any]]:
    """Build a turn→rules map from events.jsonl."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return {}
    raw = path.read_text().strip()
    if not raw:
        return {}
    rules_map: dict[int, dict[str, Any]] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        turn = int(ev.get("turn") or 0)
        rules = ev.get("rules")
        if rules and isinstance(rules, dict):
            rules_map[turn] = rules
    return rules_map


def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict[str, Any]]:
    """Return the last n turns from chronicle.md for page-reload continuity (full narrative)."""
    turns = load_recent_chronicle_turns(save_dir, n)
    rules_map = _load_rules_map(save_dir)
    return [
        {
            "turn": t["turn"],
            "input": t["input"],
            "narrative": t["narrative"],
            "rules": rules_map.get(t["turn"]),
        }
        for t in turns
    ]


def _load_last_actions(save_dir: Path) -> list[str]:
    """Return the actions list from the most recent turn event."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = [ln for ln in path.read_text().strip().splitlines() if ln.strip()]
    if not lines:
        return []
    try:
        ev = json.loads(lines[-1])
        return ev.get("actions") or []
    except (json.JSONDecodeError, KeyError):
        return []


def _get_opening() -> str:
    global _dynamic_opening
    if _active_pack.manifest.mode == "dynamic":
        return _dynamic_opening
    return _active_pack.opening_text


def _get_opening_actions() -> list[str]:
    if _active_pack.manifest.mode == "dynamic":
        return _dynamic_opening_actions
    return _active_pack.opening_actions


def _fmt_ms_seconds(ms: Any) -> str:
    if ms is None:
        return "—"
    try:
        return f"{float(ms) / 1000.0:.1f}s"
    except (TypeError, ValueError):
        return "—"


def _fmt_tokens(n: Any) -> str:
    if n is None:
        return "—"
    try:
        n = int(n)
    except (TypeError, ValueError):
        return "—"
    if n < 1000:
        return str(n)
    return f"{n / 1000:.2f}".rstrip("0").rstrip(".") + "k"


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
        except json.JSONDecodeError:
            continue
        narr = ev.get("narrate") or {}
        ext = ev.get("extract") or {}
        extraction = ev.get("extraction") or {}
        rej = ev.get("rejected") or []
        tid = str(ev.get("trace_id") or "")
        n_in, n_out = narr.get("tokens_in"), narr.get("tokens_out")
        tin, tout = ext.get("tokens_in"), ext.get("tokens_out")
        raw_streams: dict[str, dict[str, Any]] = {}
        # Per-stream data from extraction event
        for s in ("scene", "state", "progress"):
            sev = extraction.get(s) or {}
            raw_streams[s] = {
                "ms": sev.get("ms"),
                "tokens_in": sev.get("tokens_in"),
                "tokens_out": sev.get("tokens_out"),
                "skipped": sev.get("skipped", False),
            }
        # Build token display
        tok_parts: list[str] = []
        if n_in is not None and n_out is not None:
            tok_parts.append(f"N{_fmt_tokens(n_in)}/{_fmt_tokens(n_out)}")
        if tin is not None and tout is not None:
            tok_parts.append(f"E{_fmt_tokens(tin)}/{_fmt_tokens(tout)}")
        tok = "\n".join(tok_parts) if tok_parts else "—"
        rules_ev = ev.get("rules") or {}
        def _tok(ti: Any = None, to: Any = None) -> str:
            if ti is None or to is None:
                return "—"
            return f"{_fmt_tokens(ti)}/{_fmt_tokens(to)}"
        def _ttft(ms: Any, first_token_ms: Any = None) -> str:
            if first_token_ms is not None and first_token_ms > 0:
                return _fmt_ms_seconds(first_token_ms)
            return _fmt_ms_seconds(ms)
        rows.append(
            {
                "turn": ev.get("turn", 0),
                "trace_id": tid[:8] if len(tid) >= 8 else tid,
                "trace_id_full": tid,
                "first_s": _fmt_ms_seconds(narr.get("first_token_ms")),
                "narrate_s": _fmt_ms_seconds(narr.get("total_ms")),
                "extract_s": _fmt_ms_seconds(ext.get("total_ms")),
                "retries": int(ext.get("retries", 0) or 0),
                "tokens": tok,
                "has_rejections": bool(rej),
                "streams": {
                    "R_ttft": _ttft(rules_ev.get("total_ms")),
                    "R_tt": _fmt_ms_seconds(rules_ev.get("total_ms")),
                    "R_tok": _tok(rules_ev.get("tokens_in"), rules_ev.get("tokens_out")),
                    "N_ttft": _fmt_ms_seconds(narr.get("first_token_ms")),
                    "N_tt": _fmt_ms_seconds(narr.get("total_ms")),
                    "N_tok": _tok(n_in, n_out),
                    "Sc_ttft": _fmt_ms_seconds(raw_streams["scene"]["ms"]) if not raw_streams["scene"]["skipped"] else "—",
                    "Sc_tt": _fmt_ms_seconds(raw_streams["scene"]["ms"]) if not raw_streams["scene"]["skipped"] else "—",
                    "Sc_tok": _tok(raw_streams["scene"]["tokens_in"], raw_streams["scene"]["tokens_out"]) if not raw_streams["scene"]["skipped"] else "—",
                    "St_ttft": _fmt_ms_seconds(raw_streams["state"]["ms"]) if not raw_streams["state"]["skipped"] else "—",
                    "St_tt": _fmt_ms_seconds(raw_streams["state"]["ms"]) if not raw_streams["state"]["skipped"] else "—",
                    "St_tok": _tok(raw_streams["state"]["tokens_in"], raw_streams["state"]["tokens_out"]) if not raw_streams["state"]["skipped"] else "—",
                    "P_ttft": _fmt_ms_seconds(raw_streams["progress"]["ms"]) if not raw_streams["progress"]["skipped"] else "—",
                    "P_tt": _fmt_ms_seconds(raw_streams["progress"]["ms"]) if not raw_streams["progress"]["skipped"] else "—",
                    "P_tok": _tok(raw_streams["progress"]["tokens_in"], raw_streams["progress"]["tokens_out"]) if not raw_streams["progress"]["skipped"] else "—",
                },
                "total_ms": (
                    (rules_ev.get("total_ms") or 0)
                    + (narr.get("total_ms") or 0)
                    + (ext.get("total_ms") or 0)
                ),
                "total_ttft_ms": (
                    (rules_ev.get("total_ms") or 0)
                    + (narr.get("first_token_ms") or 0)
                    + (raw_streams["scene"]["ms"] or 0)
                    + (raw_streams["state"]["ms"] or 0)
                    + (raw_streams["progress"]["ms"] or 0)
                ),
                "total_tokens_in": (
                    (rules_ev.get("tokens_in") or 0)
                    + (n_in or 0)
                    + (tin or 0)
                ),
                "total_tokens_out": (
                    (rules_ev.get("tokens_out") or 0)
                    + (n_out or 0)
                    + (tout or 0)
                ),
                "total_tt": _fmt_ms_seconds(
                    (rules_ev.get("total_ms") or 0)
                    + (narr.get("total_ms") or 0)
                    + (ext.get("total_ms") or 0)
                ),
                "total_ttft": _fmt_ms_seconds(
                    (rules_ev.get("total_ms") or 0)
                    + (narr.get("first_token_ms") or 0)
                    + (raw_streams["scene"]["ms"] or 0)
                    + (raw_streams["state"]["ms"] or 0)
                    + (raw_streams["progress"]["ms"] or 0)
                ),
                "total_tok": f"{_fmt_tokens((rules_ev.get('tokens_in') or 0) + (n_in or 0) + (tin or 0))}/{_fmt_tokens((rules_ev.get('tokens_out') or 0) + (n_out or 0) + (tout or 0))}",
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
        except json.JSONDecodeError:
            continue
        ch = ev.get("changes")
        if isinstance(ch, dict):
            disp = format_change_lines(ch)
        else:
            disp = ["(no structured summary — older save)"]
        if not disp:
            disp = ["(no changes this turn)"]
        rules = ev.get("rules")
        entries.append(
            {
                "turn": int(ev.get("turn") or 0),
                "lines": disp,
                "rules": rules if isinstance(rules, dict) else None,
            }
        )
    return entries


def _fmt_tokens_exact(n: Any) -> str:
    """Format token count as exact integer string."""
    if n is None:
        return "—"
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return "—"


_STATUS_CSS: dict[str, str] = {
    "ok": "tv-sts-ok",
    "skipped": "tv-sts-skipped",
    "retried": "tv-sts-retried",
    "rejected": "tv-sts-rejected",
    "error": "tv-sts-error",
    "neutral": "tv-sts-neutral",
}

_STAGE_CSS: dict[str, str] = {
    "rules": "tv-stage-rules",
    "narrate": "tv-stage-narrate",
    "scene": "tv-stage-scene",
    "state": "tv-stage-state",
    "progress": "tv-stage-progress",
}


def _tv_parse_json_blob(raw: Any) -> dict[str, Any] | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    try:
        out = json.loads(s)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = json.loads(s[i : j + 1])
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
                return None
        return None


def _tv_dict_to_lines(
    d: dict[str, Any],
    skip_keys: tuple[str, ...] = (),
    max_str: int = 150,
) -> list[dict[str, Any]]:
    """Generic: render every top-level key of a dict as a KV line.

    Values are stringified with enough context to be useful:
    - empty list/None/empty string → "∅", dim=True
    - list of primitives (≤4) → comma-joined
    - list of dicts → "[N] id1, id2, …" using id/name/text heuristics
    - longer list → "[N items] first_item_summary"
    - dict → flat inline JSON (truncated)
    - bool → "true"/"false"
    - string → truncated to max_str
    """
    lines: list[dict[str, Any]] = []
    for k, v in d.items():
        if k in skip_keys:
            continue
        if v is None:
            lines.append({"k": k, "v": "null", "dim": True})
        elif isinstance(v, bool):
            lines.append({"k": k, "v": str(v).lower(), "dim": not v})
        elif isinstance(v, list):
            if not v:
                lines.append({"k": k, "v": "∅", "dim": True})
            elif all(isinstance(x, (str, int, float)) for x in v):
                joined = ", ".join(str(x) for x in v)
                if len(joined) > max_str:
                    joined = joined[:max_str] + "…"
                lines.append({"k": k, "v": joined, "dim": False})
            elif all(isinstance(x, dict) for x in v):
                def _label(x: dict[str, Any]) -> str:
                    for key in ("id", "name", "text", "label"):
                        val = x.get(key)
                        if val and isinstance(val, str):
                            return val[:60]
                    return str(list(x.values())[0])[:60] if x else ""
                labels = [_label(x) for x in v if x]
                summary = ", ".join(l for l in labels if l)
                if len(summary) > max_str:
                    summary = summary[:max_str] + "…"
                display = f"[{len(v)}] {summary}" if summary else f"[{len(v)}]"
                lines.append({"k": k, "v": display, "dim": False})
            else:
                lines.append({"k": k, "v": f"[{len(v)} items]", "dim": False})
        elif isinstance(v, dict):
            if not v:
                lines.append({"k": k, "v": "{}", "dim": True})
            else:
                raw = json.dumps(v, ensure_ascii=False)
                if len(raw) > max_str:
                    raw = raw[:max_str] + "…"
                lines.append({"k": k, "v": raw, "dim": False})
        elif isinstance(v, str):
            if not v:
                lines.append({"k": k, "v": "∅", "dim": True})
            else:
                display = v[:max_str] + ("…" if len(v) > max_str else "")
                lines.append({"k": k, "v": display, "dim": False})
        else:
            lines.append({"k": k, "v": str(v), "dim": not v})
    return lines


def _tv_extract_stream_status(
    name: str,
    *,
    skipped: bool,
    error: str | None,
    attempts: int,
    rejected: list[Any],
) -> str:
    if skipped:
        return "skipped"
    if error:
        return "error"
    if name == "state" and any(
        isinstance(r, dict) and r.get("field") == "inventory_remove" for r in rejected
    ):
        return "rejected"
    if int(attempts or 1) > 1:
        return "retried"
    return "ok"


def _tv_rules_status(rules_ev: Any) -> str:
    if not rules_ev or not isinstance(rules_ev, dict):
        return "neutral"
    return "ok"


def _tv_narration_lines(narr: str) -> list[dict[str, Any]]:
    s = narr or ""
    lines: list[dict[str, Any]] = [
        {"k": "chars", "v": str(len(s)), "dim": not s, "full_width": False}
    ]
    if s:
        prev = s[:100] + ("…" if len(s) > 100 else "")
        lines.append({"k": "text", "v": prev, "dim": False, "full_width": True})
    return lines


def _turn_viewer_data(save_dir: Path) -> tuple[list[dict[str, Any]], bool]:
    path = save_dir / "events.jsonl"
    if not path.exists():
        return [], True
    raw = path.read_text().strip()
    if not raw:
        return [], True
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if not lines:
        return [], True
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        narr = ev.get("narrate") or {}
        ext = ev.get("extract") or {}
        extraction = ev.get("extraction") or {}
        rej = ev.get("rejected") or []
        tid = str(ev.get("trace_id") or "")
        rules_ev = ev.get("rules") or {}

        rules_prompt = ev.get("rules_prompt") or {}
        narr_prompt = ev.get("narrate_prompt") or {}

        def _fmt_ms(ms: Any) -> str:
            if ms is None:
                return "—"
            try:
                return f"{float(ms) / 1000.0:.1f}s"
            except (TypeError, ValueError):
                return "—"

        rules_ev_d = rules_ev if isinstance(rules_ev, dict) else {}
        scene_blk = extraction.get("scene") or {}
        state_blk = extraction.get("state") or {}
        prog_blk = extraction.get("progress") or {}

        scene_out: dict[str, Any] = scene_blk.get("output") or {}
        state_out: dict[str, Any] = state_blk.get("output") or {}
        prog_out: dict[str, Any] = prog_blk.get("output") or {}

        raw_streams: dict[str, dict[str, Any]] = {}
        for s in ("scene", "state", "progress"):
            sev = extraction.get(s) or {}
            raw_streams[s] = {
                "ms": sev.get("ms"),
                "tokens_in": sev.get("tokens_in"),
                "tokens_out": sev.get("tokens_out"),
                "skipped": bool(sev.get("skipped", False)),
                "error": sev.get("error"),
                "attempts": int(sev.get("attempts") or 1),
                "retry_errors": sev.get("retry_errors") or [],
            }

        streams: dict[str, dict[str, Any]] = {}

        r_in = rules_ev_d.get("tokens_in")
        r_out = rules_ev_d.get("tokens_out")
        r_ms = rules_ev_d.get("total_ms")
        rules_status = _tv_rules_status(rules_ev_d)
        streams["rules"] = {
            "tt": _fmt_ms(r_ms),
            "tokens_in": r_in,
            "tokens_out": r_out,
            "tokens_in_display": _fmt_tokens_exact(r_in),
            "tokens_out_display": _fmt_tokens_exact(r_out),
            "skipped": False,
            "error": None,
            "attempts": 1,
            "status": rules_status,
            "status_class": _STATUS_CSS.get(rules_status, "tv-sts-ok"),
            "stage_class": _STAGE_CSS["rules"],
        }

        n_in = narr.get("tokens_in")
        n_out = narr.get("tokens_out")
        n_ms = narr.get("total_ms")
        streams["narrate"] = {
            "tt": _fmt_ms(n_ms),
            "tokens_in": n_in,
            "tokens_out": n_out,
            "tokens_in_display": _fmt_tokens_exact(n_in),
            "tokens_out_display": _fmt_tokens_exact(n_out),
            "skipped": False,
            "error": None,
            "attempts": 1,
            "status": "ok",
            "status_class": _STATUS_CSS["ok"],
            "stage_class": _STAGE_CSS["narrate"],
        }

        for key in ("scene", "state", "progress"):
            s_data = raw_streams[key]
            s_in = s_data["tokens_in"]
            s_out = s_data["tokens_out"]
            s_ms = s_data["ms"]
            s_skip = s_data["skipped"]
            err = s_data.get("error")
            err_s = str(err) if err else None
            attempts = int(s_data.get("attempts") or 1)
            st = _tv_extract_stream_status(
                key,
                skipped=s_skip,
                error=err_s,
                attempts=attempts,
                rejected=rej if isinstance(rej, list) else [],
            )
            streams[key] = {
                "tt": "—" if s_skip else _fmt_ms(s_ms),
                "tokens_in": s_in,
                "tokens_out": s_out,
                "tokens_in_display": "—" if s_skip else _fmt_tokens_exact(s_in),
                "tokens_out_display": "—" if s_skip else _fmt_tokens_exact(s_out),
                "skipped": s_skip,
                "error": err_s,
                "attempts": attempts,
                "retry_errors": s_data.get("retry_errors") or [],
                "status": st,
                "status_class": _STATUS_CSS.get(st, "tv-sts-ok"),
                "stage_class": _STAGE_CSS[key],
            }

        token_sums: list[int] = []
        for stg in ("rules", "narrate", "scene", "state", "progress"):
            tin = streams[stg].get("tokens_in") or 0
            tout = streams[stg].get("tokens_out") or 0
            sm = int(tin) + int(tout)
            token_sums.append(sm)
            streams[stg]["token_sum"] = sm
        max_sum = max(token_sums) if token_sums else 1
        if max_sum < 1:
            max_sum = 1
        for stg in ("rules", "narrate", "scene", "state", "progress"):
            sm = int(streams[stg]["token_sum"])
            streams[stg]["token_bar_pct"] = round(100.0 * sm / float(max_sum), 1)

        total_in = (
            (r_in or 0)
            + (n_in or 0)
            + (raw_streams["scene"]["tokens_in"] or 0)
            + (raw_streams["state"]["tokens_in"] or 0)
            + (raw_streams["progress"]["tokens_in"] or 0)
        )
        total_out = (
            (r_out or 0)
            + (n_out or 0)
            + (raw_streams["scene"]["tokens_out"] or 0)
            + (raw_streams["state"]["tokens_out"] or 0)
            + (raw_streams["progress"]["tokens_out"] or 0)
        )
        total_tt_ms = (r_ms or 0) + (n_ms or 0) + (ext.get("total_ms") or 0)

        narr_text = str(narr_prompt.get("output") or "")
        connectors: list[dict[str, Any]] = []
        if rules_ev_d:
            connectors.append(
                {
                    "before_stage": "narrate",
                    "segments": [
                        {
                            "from": "rules",
                            "label": "rules → narrate",
                            "lines": _tv_dict_to_lines(
                                rules_ev_d,
                                skip_keys=("tokens_in", "tokens_out", "total_ms"),
                            ),
                            "anchor": "rules",
                            "upstream_status": streams["rules"]["status"],
                            "upstream_status_class": streams["rules"]["status_class"],
                        }
                    ],
                }
            )
        connectors.append(
            {
                "before_stage": "scene",
                "segments": [
                    {
                        "from": "narrate",
                        "label": "narrate → scene",
                        "lines": _tv_narration_lines(narr_text),
                        "anchor": "narrate",
                        "upstream_status": streams["narrate"]["status"],
                        "upstream_status_class": streams["narrate"]["status_class"],
                    }
                ],
            }
        )
        connectors.append(
            {
                "before_stage": "state",
                "segments": [
                    {
                        "from": "narrate",
                        "label": "narrate → state",
                        "lines": _tv_narration_lines(narr_text),
                        "anchor": "narrate",
                        "upstream_status": streams["narrate"]["status"],
                        "upstream_status_class": streams["narrate"]["status_class"],
                    },
                    {
                        "from": "scene",
                        "label": "scene → state",
                        "lines": _tv_dict_to_lines(scene_out),
                        "anchor": "scene",
                        "upstream_status": streams["scene"]["status"],
                        "upstream_status_class": streams["scene"]["status_class"],
                    },
                ],
            }
        )
        connectors.append(
            {
                "before_stage": "progress",
                "segments": [
                    {
                        "from": "narrate",
                        "label": "narrate → progress",
                        "lines": _tv_narration_lines(narr_text),
                        "anchor": "narrate",
                        "upstream_status": streams["narrate"]["status"],
                        "upstream_status_class": streams["narrate"]["status_class"],
                    },
                    {
                        "from": "scene",
                        "label": "scene → progress",
                        "lines": _tv_dict_to_lines(scene_out),
                        "anchor": "scene",
                        "upstream_status": streams["scene"]["status"],
                        "upstream_status_class": streams["scene"]["status_class"],
                    },
                    {
                        "from": "state",
                        "label": "state → progress",
                        "lines": _tv_dict_to_lines(state_out),
                        "anchor": "state",
                        "upstream_status": streams["state"]["status"],
                        "upstream_status_class": streams["state"]["status_class"],
                    },
                ],
            }
        )

        state_rej = [
            r
            for r in (rej if isinstance(rej, list) else [])
            if isinstance(r, dict) and r.get("field") == "inventory_remove"
        ]
        has_retries = any(
            int((extraction.get(s) or {}).get("attempts") or 1) > 1
            for s in ("scene", "state", "progress")
        )
        has_errors = any(
            bool(streams[s].get("error"))
            for s in ("scene", "state", "progress")
        )
        has_skipped = any(
            streams[s].get("skipped")
            for s in ("scene", "state", "progress")
        )

        rules_intent = _tv_parse_json_blob(rules_prompt.get("output"))

        rows.append(
            {
                "turn": ev.get("turn", 0),
                "trace_id": tid[:8] if len(tid) >= 8 else tid,
                "trace_id_full": tid,
                "has_rejections": bool(rej),
                "has_retries": has_retries,
                "has_errors": has_errors,
                "has_skipped": has_skipped,
                "streams": streams,
                "connectors": connectors,
                "rules_event": rules_ev_d,
                "rules_intent": rules_intent,
                "state_rejections": state_rej,
                "total_tt": _fmt_ms(total_tt_ms),
                "total_tokens_in": total_in,
                "total_tokens_out": total_out,
                "total_tokens_in_display": _fmt_tokens_exact(total_in),
                "total_tokens_out_display": _fmt_tokens_exact(total_out),
                "user_input": ev.get("input", ""),
                "rules_prompt": {
                    "system": rules_prompt.get("rendered_system", ""),
                    "user": rules_prompt.get("rendered_user", ""),
                    "output": rules_prompt.get("output", ""),
                },
                "narrate_prompt": {
                    "system": narr_prompt.get("rendered_system", ""),
                    "user": narr_prompt.get("rendered_user", ""),
                    "output": narr_text,
                },
                "scene_prompt": {
                    "system": extraction.get("scene", {}).get("rendered_system", ""),
                    "user": extraction.get("scene", {}).get("rendered_user", ""),
                    "output": json.dumps(scene_out, indent=2)
                    if extraction.get("scene")
                    and not extraction.get("scene", {}).get("skipped", False)
                    else "",
                },
                "state_prompt": {
                    "system": extraction.get("state", {}).get("rendered_system", ""),
                    "user": extraction.get("state", {}).get("rendered_user", ""),
                    "output": json.dumps(state_out, indent=2)
                    if extraction.get("state")
                    and not extraction.get("state", {}).get("skipped", False)
                    else "",
                },
                "progress_prompt": {
                    "system": extraction.get("progress", {}).get("rendered_system", ""),
                    "user": extraction.get("progress", {}).get("rendered_user", ""),
                    "output": json.dumps(prog_out, indent=2)
                    if extraction.get("progress")
                    and not extraction.get("progress", {}).get("skipped", False)
                    else "",
                },
            }
        )
    rows.reverse()
    return rows, False


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = _load_recent_history(SAVE_DIR)
    last_actions = _load_last_actions(SAVE_DIR) if history else []
    state = _load_current_state()
    opening = (
        _get_opening() if not history and state.get("location", {}).get("id") else ""
    )
    opening_actions = _get_opening_actions() if not history and opening else []
    ctx = _debug_context()
    ctx["state"] = state
    ctx["history"] = history
    ctx["last_actions"] = last_actions
    ctx["opening"] = opening
    ctx["opening_actions"] = opening_actions
    ctx["has_narrative"] = bool(opening or history)
    ctx["pack_mode"] = _active_pack.manifest.mode
    ctx["pack_name"] = _active_pack.manifest.name
    ctx["character_creation_enabled"] = config.get("game", {}).get(
        "character_creation_enabled", True
    )
    css_path = BASE_DIR / "static" / "app.css"
    ctx["css_v"] = int(css_path.stat().st_mtime) if css_path.exists() else 0
    return _render("index.html", ctx)


@app.get("/turn")
async def get_turn(input: str = ""):
    user_input = input.strip()
    if not user_input:

        async def _empty():
            yield {"event": "turn_error", "data": json.dumps({"error": "Empty input"})}

        return EventSourceResponse(_empty())

    if is_turn_in_progress(str(SAVE_DIR)):

        async def _busy():
            yield {
                "event": "turn_error",
                "data": json.dumps({"error": "Turn already in progress"}),
            }

        return EventSourceResponse(_busy())

    async def event_stream():
        try:
            async for kind, payload in run_turn(
                SAVE_DIR,
                user_input,
                config=engine_config,
                template_dir=str(PROMPTS_DIR),
                pack_style=_active_pack.style_text,
                pack_examples=_active_pack.extract_examples,
                pack_name_locales=_active_pack.manifest.name_locales,
            ):
                if kind == "token":
                    yield {
                        "event": "narrative_token",
                        "data": json.dumps({"chunk": payload}),
                    }
                elif kind == "phase":
                    yield {"event": "phase", "data": json.dumps(payload)}
                elif kind == "complete":
                    result = payload
                    for err in result.errors:
                        _ERRORS_LOG.appendleft(err)
                    ch = result.changes if isinstance(result.changes, dict) else {}
                    yield {
                        "event": "turn_complete",
                        "data": json.dumps(
                            {
                                "turn": result.turn,
                                "trace_id": result.trace_id,
                                "narrative": result.narrative,
                                "actions": result.actions,
                                "scene_tags": result.scene_tags,
                                "game_over": "game_over" in (result.scene_tags or []),
                                "rejected": result.rejected,
                                "errors": result.errors,
                                "diff": result.diff,
                                "changes": ch,
                                "change_lines": format_change_lines(ch),
                                "state": _load_current_state(),
                                "metrics": result.metrics,
                                "rules": result.rules,
                            }
                        ),
                    }
        except Exception as e:
            logger.exception("Turn failed")
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@app.post("/new-game")
async def new_game(request: Request):
    global _dynamic_opening, _dynamic_opening_actions, _active_pack, _pack_id
    _ERRORS_LOG.clear()

    form = await request.form()
    requested_pack = str(form.get("pack_id", "")).strip()
    if requested_pack and requested_pack != _pack_id:
        try:
            _active_pack = load_pack(requested_pack, PACKS_DIR)
            _pack_id = requested_pack
            logger.info(
                "Switched pack to %s (mode=%s)", _pack_id, _active_pack.manifest.mode
            )
        except Exception as exc:
            logger.error("Failed to switch pack %r: %s", requested_pack, exc)
            _ERRORS_LOG.appendleft({"message": f"Unknown pack: {requested_pack}"})

    # Character creation form fields
    pc_name = str(form.get("pc_name", "")).strip()
    pc_tagline = str(form.get("pc_tagline", "")).strip()
    pc_stats_raw = str(form.get("pc_stats", "")).strip()
    pc_hints = str(form.get("pc_hints", "")).strip()
    npc_hints = str(form.get("npc_hints", "")).strip()
    location_hints = str(form.get("location_hints", "")).strip()
    quest_hints = str(form.get("quest_hints", "")).strip()
    free_form = str(form.get("free_form", "")).strip()

    npc_count_raw = str(form.get("npc_count", "")).strip()
    try:
        npc_count = max(0, int(npc_count_raw)) if npc_count_raw else 0
    except ValueError:
        npc_count = 0

    from ccya.pack import PlayerOverrides

    overrides = PlayerOverrides(
        pc_hints=pc_hints,
        npc_hints=npc_hints,
        location_hints=location_hints,
        quest_hints=quest_hints,
        free_form=free_form,
        npc_count=npc_count,
    )

    if (pc_name or pc_tagline or pc_stats_raw) and overrides:
        hint_parts = []
        if pc_name:
            hint_parts.append(f"Name the PC '{pc_name}'.")
        if pc_tagline:
            hint_parts.append(f"Tagline: '{pc_tagline}'.")
        if pc_stats_raw:
            hint_parts.append(f"Use these exact stats: {pc_stats_raw}.")
        if hint_parts:
            overrides = overrides.model_copy(
                update={"pc_hints": " ".join(hint_parts) + " " + overrides.pc_hints}
            )

    if _active_pack.manifest.mode == "static":
        assert _active_pack.seed is not None
        seed = _active_pack.seed.model_dump()
        if pc_name:
            seed["pc"]["name"] = pc_name
        if pc_tagline:
            seed["pc"]["tagline"] = pc_tagline
        if pc_stats_raw:
            try:
                stats = json.loads(pc_stats_raw)
                if _validate_stats(stats):
                    seed["pc"]["stats"] = stats
            except (json.JSONDecodeError, TypeError):
                pass  # invalid JSON — leave seed stats unchanged
        seed.setdefault("meta", {})["model"] = config["llm"]["model"]
        init_save_dir(SAVE_DIR, seed)
        _dynamic_opening = ""
        _dynamic_opening_actions = []
    else:
        # dynamic: LLM-generated seed
        try:
            envelope = await generate_seed(
                _active_pack,
                engine_config,
                template_dir=str(PROMPTS_DIR),
                overrides=overrides if not overrides.is_empty() else None,
            )
            seed = envelope.seed_state.model_dump()
            seed.setdefault("meta", {})["model"] = config["llm"]["model"]
            seed["meta"]["setting_pack"] = _pack_id
            init_save_dir(SAVE_DIR, seed)
            _dynamic_opening = envelope.opening_narrative
            _dynamic_opening_actions = envelope.actions
        except Exception as exc:
            logger.exception("generate_seed failed")
            _ERRORS_LOG.appendleft({"message": f"New game generation failed: {exc}"})

    ctx = _debug_context()
    ctx["pack_mode"] = _active_pack.manifest.mode
    return _render("_state.html", ctx)


@app.post("/new-game/reroll")
async def new_game_reroll(request: Request):
    global _dynamic_opening, _dynamic_opening_actions
    if _active_pack.manifest.mode != "dynamic":
        return HTMLResponse(
            "<p>Re-roll only available for dynamic packs.</p>", status_code=400
        )

    try:
        envelope = await generate_seed(
            _active_pack,
            engine_config,
            template_dir=str(PROMPTS_DIR),
        )
        seed = envelope.seed_state.model_dump()
        seed.setdefault("meta", {})["model"] = config["llm"]["model"]
        seed["meta"]["setting_pack"] = _pack_id
        init_save_dir(SAVE_DIR, seed)
        _dynamic_opening = envelope.opening_narrative
        _dynamic_opening_actions = envelope.actions
    except Exception as exc:
        logger.exception("generate_seed reroll failed")
        _ERRORS_LOG.appendleft({"message": f"Re-roll failed: {exc}"})
        return HTMLResponse(f"<p class='text-red-400'>Re-roll failed: {exc}</p>")

    actions_html = "".join(
        f'<button class="action-pill" onclick="window._gameInstance && window._gameInstance.fillFromChoice(this.textContent)">{a}</button>'
        for a in _dynamic_opening_actions
    )
    return HTMLResponse(
        f'<div id="actions-zone" hx-swap-oob="outerHTML:true">{actions_html}</div>'
        + _dynamic_opening
    )


@app.get("/panels/state")
def panel_state(request: Request):
    return _render("_state.html", _debug_context())


@app.get("/panels/state-left")
def panel_state_left(request: Request):
    return _render("_state_left.html", {"state": _load_current_state()})


@app.get("/panels/state-right")
def panel_state_right(request: Request):
    return _render("_state_right.html", _debug_context())


@app.get("/panels/actions")
def panel_actions(request: Request):
    return _render("_actions.html", {"state": _load_current_state()})


def _debug_context() -> dict[str, Any]:
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    return {
        "errors": list(_ERRORS_LOG),
        "turns": _recent_turn_metrics(SAVE_DIR, 10),
        "mock_mode": mock_mode,
        "state": _load_current_state(),
        "log_llm_io": engine_config.log_llm_io,
        "log_prompts": engine_config.log_prompts,
        "log_file": config.get("logging", {}).get("file", "logs/llm-g.log"),
    }


@app.post("/panels/debug/clear-errors")
def debug_clear_errors():
    _ERRORS_LOG.clear()
    return _render("_debug.html", _debug_context())


@app.get("/panels/debug")
def panel_debug():
    return _render("_debug.html", _debug_context())


@app.get("/panels/pack-picker", response_class=HTMLResponse)
def panel_pack_picker():
    packs = list_packs(PACKS_DIR)
    return _render("_pack_picker.html", {"packs": packs, "active_pack_id": _pack_id})


@app.get("/panels/char-creation", response_class=HTMLResponse)
def panel_char_creation():
    return _render("_char_creation.html", {})


@app.get("/panels/turn-log", response_class=HTMLResponse)
def panel_turn_log(limit: int = 50):
    lim = max(1, min(limit, 200))
    return _render("_turn_log.html", {"entries": _turn_log_entries(SAVE_DIR, lim)})


@app.get("/turn_viewer", response_class=HTMLResponse)
def turn_viewer():
    css_path = BASE_DIR / "static" / "app.css"
    css_v = int(css_path.stat().st_mtime) if css_path.exists() else 0
    turns, no_events = _turn_viewer_data(SAVE_DIR)
    return _render(
        "_turn_viewer.html",
        {
            "turns": turns,
            "turn_count": len(turns),
            "no_events": no_events,
            "css_v": css_v,
        },
    )


@app.get("/turn_viewer/data")
def turn_viewer_data():
    turns, no_events = _turn_viewer_data(SAVE_DIR)
    latest = turns[0] if turns else None
    return JSONResponse(
        {
            "turns": turns,
            "no_events": no_events,
            "turn_count": len(turns),
            "latest_turn": latest.get("turn") if latest else None,
            "latest_trace_id_full": latest.get("trace_id_full") if latest else None,
        }
    )


@app.get("/turn_viewer/stream")
async def turn_viewer_stream():
    path = SAVE_DIR / "events.jsonl"

    async def gen():
        last_mtime: float | None = None
        while True:
            await asyncio.sleep(1.0)
            if not path.exists():
                continue
            m = path.stat().st_mtime
            if last_mtime is None:
                last_mtime = m
            elif m != last_mtime:
                last_mtime = m
                yield {"event": "updated", "data": "{}"}

    return EventSourceResponse(gen())


@app.get("/opening")
def opening():
    return HTMLResponse(_get_opening())


@app.get("/healthz")
def healthz():
    import httpx

    host = str(config["llm"]["host"]).rstrip("/")
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    if mock_mode:
        return {
            "llm": "mock",
            "model": config["llm"]["model"],
            "available": True,
            "mock": True,
            "llm_version": "",
        }
    llm_version = ""
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{host}/models")
            resp.raise_for_status()
            body = resp.json()
            models = [m["id"] for m in body.get("data", [])]
            model = config["llm"]["model"]
            return {
                "llm": "ok",
                "model": model,
                "available": model in models,
                "llm_version": llm_version,
            }
    except Exception:
        return {
            "llm": "fail",
            "model": config["llm"]["model"],
            "available": False,
            "llm_version": llm_version,
        }


@app.on_event("startup")
async def startup_event():
    import asyncio

    logger.info(
        "ccya starting — pack: %s (mode=%s)", _pack_id, _active_pack.manifest.mode
    )
    if config.get("game", {}).get("warmup_on_start", True):

        async def _warmup_bg() -> None:
            logger.info("Warming up LLM model (background)…")
            await warmup(engine_config)
            logger.info("Model warmup complete")

        asyncio.create_task(_warmup_bg())


def main() -> None:
    import uvicorn

    host = config["server"]["bind_host"]
    port = config["server"]["bind_port"]
    uvicorn.run("ccya.server:app", host=host, port=port, reload=False)
