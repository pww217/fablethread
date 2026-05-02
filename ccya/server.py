"""FastAPI server: SSE /turn (GET), HTMX panels, errors store."""

from __future__ import annotations

import json
import os
from collections import deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from sse_starlette.sse import EventSourceResponse

from ccya.engine import EngineConfig, format_change_lines, generate_seed, is_turn_in_progress, run_turn, warmup
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
    request_timeout_s=config["llm"]["request_timeout_s"],
    narrate_temperature=config["llm"]["narrate_temperature"],
    extract_temperature=config["llm"]["extract_temperature"],
    max_extract_retries=config["llm"]["max_extract_retries"],
    window_turns=config["game"]["window_turns"],
    chronicle_prefix_budget_tokens=config["game"]["chronicle_prefix_budget_tokens"],
    established_facts_max=config["game"]["established_facts_max"],
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

# ---------------------------------------------------------------------------
# Pack loading — active pack is mutable (changed via New Game picker)
# ---------------------------------------------------------------------------

_pack_id: str = config.get("game", {}).get("setting_pack", "expanse-belter")
try:
    _active_pack: Pack = load_pack(_pack_id, PACKS_DIR)
    logger.info("Loaded pack: %s (mode=%s)", _pack_id, _active_pack.manifest.mode)
except Exception as exc:
    logger.error("Failed to load pack %r: %s", _pack_id, exc)
    raise

# Cache for the opening text of dynamic packs (written on New Game / re-roll, read on GET /)
_dynamic_opening: str = ""
_dynamic_opening_actions: list[str] = []

app = FastAPI(title="ccya")
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

# In-process errors store — last 50 entries, survives turn boundaries.
_ERRORS_LOG: deque[dict[str, Any]] = deque(maxlen=50)


def _render(template_name: str, context: dict) -> HTMLResponse:
    template = _jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_current_state() -> dict:
    return load_state(SAVE_DIR)


def _load_recent_history(save_dir: Path, n: int = 8) -> list[dict]:
    """Return the last n turns from chronicle.md for page-reload continuity (full narrative)."""
    turns = load_recent_chronicle_turns(save_dir, n)
    return [
        {"turn": t["turn"], "input": t["input"], "narrative": t["narrative"]}
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
    """Return opening prose: dynamic packs use the cached LLM-generated text; static use pack file."""
    global _dynamic_opening
    if _active_pack.manifest.mode == "dynamic":
        return _dynamic_opening
    return _active_pack.opening_text


def _get_opening_actions() -> list[str]:
    """Return opening actions: dynamic packs use the cached list; static use pack file."""
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
        rej = ev.get("rejected") or []
        tid = str(ev.get("trace_id") or "")
        n_in, n_out = narr.get("tokens_in"), narr.get("tokens_out")
        tin, tout = ext.get("tokens_in"), ext.get("tokens_out")
        parts: list[str] = []
        if n_in is not None and n_out is not None:
            parts.append(f"N{n_in}/{n_out}")
        if tin is not None and tout is not None:
            parts.append(f"E{tin}/{tout}")
        tok = "\n".join(parts) if parts else "—"
        rows.append({
            "turn": ev.get("turn", 0),
            "trace_id": tid[:8] if len(tid) >= 8 else tid,
            "trace_id_full": tid,
            "first_s": _fmt_ms_seconds(narr.get("first_token_ms")),
            "narrate_s": _fmt_ms_seconds(narr.get("total_ms")),
            "extract_s": _fmt_ms_seconds(ext.get("total_ms")),
            "retries": int(ext.get("retries", 0) or 0),
            "tokens": tok,
            "has_rejections": bool(rej),
        })
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
        entries.append({"turn": int(ev.get("turn") or 0), "lines": disp})
    return entries


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = _load_recent_history(SAVE_DIR)
    last_actions = _load_last_actions(SAVE_DIR) if history else []
    state = _load_current_state()
    opening = _get_opening() if not history and state.get("location", {}).get("id") else ""
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
    css_path = BASE_DIR / "static" / "app.css"
    ctx["css_v"] = int(css_path.stat().st_mtime) if css_path.exists() else 0
    return _render("index.html", ctx)


@app.get("/turn")
async def get_turn(input: str = ""):
    """GET /turn?input=... -> SSE stream.

    SSE event types:
      narrative_token  data: {"chunk": "..."}
      phase            data: {phase, expected_ms?, attempt?}
      turn_complete    data: {turn, trace_id, narrative, actions, scene_tags,
                              rejected, errors, diff, state, metrics}
      turn_error       data: {"error": "...", "trace_id": "..."}
    """
    user_input = input.strip()
    if not user_input:
        async def _empty():
            yield {"event": "turn_error", "data": json.dumps({"error": "Empty input"})}
        return EventSourceResponse(_empty())

    if is_turn_in_progress(str(SAVE_DIR)):
        async def _busy():
            yield {"event": "turn_error", "data": json.dumps({"error": "Turn already in progress"})}
        return EventSourceResponse(_busy())

    async def event_stream():
        try:
            async for kind, payload in run_turn(
                SAVE_DIR, user_input,
                config=engine_config,
                template_dir=str(PROMPTS_DIR),
                pack_style=_active_pack.style_text,
                pack_examples=_active_pack.extract_examples,
            ):
                if kind == "token":
                    yield {"event": "narrative_token", "data": json.dumps({"chunk": payload})}
                elif kind == "phase":
                    yield {"event": "phase", "data": json.dumps(payload)}
                elif kind == "complete":
                    result = payload
                    for err in result.errors:
                        _ERRORS_LOG.appendleft(err)
                    ch = result.changes if isinstance(result.changes, dict) else {}
                    yield {"event": "turn_complete", "data": json.dumps({
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
                    })}
        except Exception as e:
            logger.exception("Turn failed")
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@app.post("/new-game")
async def new_game(request: Request):
    """Reset save: static packs load seed directly; dynamic packs call generate_seed.
    Accepts optional form field `pack_id` to switch the active pack."""
    global _dynamic_opening, _dynamic_opening_actions, _active_pack, _pack_id
    _ERRORS_LOG.clear()

    form = await request.form()
    requested_pack = str(form.get("pack_id", "")).strip()
    if requested_pack and requested_pack != _pack_id:
        try:
            _active_pack = load_pack(requested_pack, PACKS_DIR)
            _pack_id = requested_pack
            logger.info("Switched pack to %s (mode=%s)", _pack_id, _active_pack.manifest.mode)
        except Exception as exc:
            logger.error("Failed to switch pack %r: %s", requested_pack, exc)
            _ERRORS_LOG.appendleft({"message": f"Unknown pack: {requested_pack}"})

    if _active_pack.manifest.mode == "static":
        seed = _active_pack.seed.model_dump()
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
    """Re-roll the seed for a dynamic pack (before turn 1) without changing pack mode."""
    global _dynamic_opening, _dynamic_opening_actions
    if _active_pack.manifest.mode != "dynamic":
        return HTMLResponse("<p>Re-roll only available for dynamic packs.</p>", status_code=400)

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
    """Legacy combined fragment (left + right)."""
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


def _debug_context() -> dict:
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
    """Return HTML fragment: pack picker cards for the New Game modal."""
    packs = list_packs(PACKS_DIR)
    return _render("_pack_picker.html", {"packs": packs, "active_pack_id": _pack_id})


@app.get("/panels/turn-log", response_class=HTMLResponse)
def panel_turn_log(limit: int = 50):
    """HTMX fragment: human-readable turn summaries from events.jsonl."""
    lim = max(1, min(limit, 200))
    return _render("_turn_log.html", {"entries": _turn_log_entries(SAVE_DIR, lim)})


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


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event():
    import asyncio

    logger.info("ccya starting — pack: %s (mode=%s)", _pack_id, _active_pack.manifest.mode)
    if config.get("game", {}).get("warmup_on_start", True):
        async def _warmup_bg() -> None:
            logger.info("Warming up LLM model (background)…")
            await warmup(engine_config)
            logger.info("Model warmup complete")
        asyncio.create_task(_warmup_bg())


# ---------------------------------------------------------------------------
# CLI entry (used by uvicorn directly, not __main__)
# ---------------------------------------------------------------------------


def main() -> None:
    import uvicorn
    host = config["server"]["bind_host"]
    port = config["server"]["bind_port"]
    uvicorn.run("ccya.server:app", host=host, port=port, reload=False)
