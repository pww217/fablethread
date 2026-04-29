"""FastAPI server: SSE /turn (GET), HTMX panels, errors store."""

from __future__ import annotations

import json
import os
import time
from collections import deque
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from sse_starlette.sse import EventSourceResponse

from ccya.engine import EngineConfig, is_turn_in_progress, run_turn, warmup
from ccya.logging_setup import setup_logging
from ccya.models import load_config as _load_config
from ccya.state import init_save_dir, load_state

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
PROMPTS_DIR = BASE_DIR / "prompts"
SAVE_DIR = Path("saves") / "default"

config: dict[str, Any] = _load_config(BASE_DIR.parent / "config.yaml")
engine_config = EngineConfig(
    ollama_host=config["ollama"]["host"],
    model=config["ollama"]["model"],
    keep_alive=config["ollama"]["keep_alive"],
    num_ctx=config["ollama"]["num_ctx"],
    extract_num_ctx=config["ollama"].get("extract_num_ctx", 4096),
    request_timeout_s=config["ollama"]["request_timeout_s"],
    narrate_temperature=config["ollama"]["narrate_temperature"],
    extract_temperature=config["ollama"]["extract_temperature"],
    max_extract_retries=config["ollama"]["max_extract_retries"],
    window_turns=config["game"]["window_turns"],
    chronicle_prefix_budget_tokens=config["game"]["chronicle_prefix_budget_tokens"],
    established_facts_max=config["game"]["established_facts_max"],
    enforce_extract_schema=config["ollama"].get("enforce_extract_schema", True),
    log_llm_io=config.get("logging", {}).get("log_llm_io", False),
    log_llm_io_max_chars=config.get("logging", {}).get("log_llm_io_max_chars", 4000),
)

logger = setup_logging(config)

app = FastAPI(title="ccya")
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

# In-process errors store — last 50 entries, survives turn boundaries.
_ERRORS_LOG: deque[dict[str, Any]] = deque(maxlen=50)

# Request timing for debug panel
_REQUEST_LOG: list[dict[str, Any]] = []


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
    """Return the last n turn events from events.jsonl for page-reload continuity."""
    path = save_dir / "events.jsonl"
    if not path.exists():
        return []
    lines = path.read_text().strip().splitlines()
    recent = lines[-n:] if len(lines) > n else lines
    result = []
    for line in recent:
        try:
            ev = json.loads(line)
            result.append({
                "turn": ev.get("turn", 0),
                "input": ev.get("input", ""),
                "narrative": ev.get("narrative", "").strip(),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return result


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


def _load_opening() -> str:
    pack = config.get("game", {}).get("setting_pack", "hard-scifi-demo")
    path = BASE_DIR.parent / "packs" / pack / "opening_scene.md"
    if path.exists():
        return path.read_text()
    return ""


def _add_timing(entry: dict, start: float) -> None:
    entry["elapsed_ms"] = round((time.time() - start) * 1000, 1)


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
        tin, tout = ext.get("tokens_in"), ext.get("tokens_out")
        if tin is not None and tout is not None:
            tok = f"{tin}/{tout}"
        elif tin is not None:
            tok = str(tin)
        else:
            tok = "—"
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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = _load_recent_history(SAVE_DIR)
    last_actions = _load_last_actions(SAVE_DIR) if history else []
    state = _load_current_state()
    # Show opening scene text server-side when there's no history yet (turn 0 or fresh game)
    opening = _load_opening() if not history and state.get("location", {}).get("id") else ""
    ctx = _debug_context()
    ctx["state"] = state
    ctx["history"] = history
    ctx["last_actions"] = last_actions
    ctx["opening"] = opening
    return _render("index.html", ctx)


@app.get("/turn")
async def get_turn(input: str = ""):
    """GET /turn?input=... -> SSE stream.

    Uses GET so the browser's native EventSource API can connect without CORS
    pre-flight or custom headers. Appropriate for a local-only single-player tool.

    SSE event types:
      narrative_token  data: {"chunk": "..."}
      phase              data: {phase, expected_ms?, attempt?}
      turn_complete    data: {turn, trace_id, narrative, actions, scene_tags,
                              rejected, errors, state, metrics}
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

    start = time.time()

    async def event_stream():
        timing = {"event": "turn_start", "input": user_input[:100]}
        _REQUEST_LOG.append(timing)

        try:
            async for kind, payload in run_turn(
                SAVE_DIR, user_input,
                config=engine_config,
                template_dir=str(PROMPTS_DIR),
            ):
                if kind == "token":
                    yield {"event": "narrative_token", "data": json.dumps({"chunk": payload})}
                elif kind == "phase":
                    yield {"event": "phase", "data": json.dumps(payload)}
                elif kind == "complete":
                    result = payload
                    for err in result.errors:
                        _ERRORS_LOG.appendleft(err)
                    _add_timing(timing, start)
                    yield {"event": "turn_complete", "data": json.dumps({
                        "turn": result.turn,
                        "trace_id": result.trace_id,
                        "narrative": result.narrative,
                        "actions": result.actions,
                        "scene_tags": result.scene_tags,
                        "rejected": result.rejected,
                        "errors": result.errors,
                        "state": _load_current_state(),
                        "metrics": result.metrics,
                    })}
        except Exception as e:
            _add_timing(timing, start)
            logger.exception("Turn failed")
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@app.post("/new-game")
async def new_game(request: Request):
    """Reset save from starter pack seed state."""
    seed = _load_seed()
    seed.setdefault("meta", {})
    seed["meta"]["model"] = config["ollama"]["model"]
    init_save_dir(SAVE_DIR, seed)
    _ERRORS_LOG.clear()
    return _render("_state.html", _debug_context())


def _load_seed() -> dict:
    pack = config.get("game", {}).get("setting_pack", "hard-scifi-demo")
    seed_path = BASE_DIR.parent / "packs" / pack / "seed_state.yaml"
    if seed_path.exists():
        with open(seed_path) as f:
            return yaml.safe_load(f) or {}
    return {}


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
        "enforce_extract_schema": engine_config.enforce_extract_schema,
        "log_llm_io": engine_config.log_llm_io,
        "log_file": config.get("logging", {}).get("file", "logs/llm-g.log"),
        "num_ctx": config["ollama"].get("num_ctx", ""),
    }


@app.post("/panels/debug/clear-errors")
def debug_clear_errors():
    _ERRORS_LOG.clear()
    return _render("_debug.html", _debug_context())


@app.get("/panels/debug")
def panel_debug():
    return _render("_debug.html", _debug_context())


@app.get("/opening")
def opening():
    return HTMLResponse(_load_opening())


@app.get("/healthz")
def healthz():
    import httpx

    host = str(config["ollama"]["host"]).rstrip("/")
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    if mock_mode:
        return {
            "ollama": "mock",
            "model": config["ollama"]["model"],
            "available": True,
            "mock": True,
            "ollama_version": "",
        }
    ollama_version = ""
    try:
        with httpx.Client(timeout=5) as client:
            try:
                vr = client.get(f"{host}/api/version")
                if vr.status_code == 200:
                    body = vr.json()
                    if isinstance(body, dict) and body.get("version"):
                        ollama_version = str(body["version"])
            except Exception:
                pass
            resp = client.get(f"{host}/api/tags")
            resp.raise_for_status()
            tags = resp.json()
            models = [m["name"] for m in tags.get("models", [])]
            model = config["ollama"]["model"]
            return {
                "ollama": "ok",
                "model": model,
                "available": model in models,
                "ollama_version": ollama_version,
            }
    except Exception:
        return {
            "ollama": "fail",
            "model": config["ollama"]["model"],
            "available": False,
            "ollama_version": ollama_version,
        }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event():
    import asyncio

    logger.info("ccya starting")
    if config.get("game", {}).get("warmup_on_start", True):
        async def _warmup_bg() -> None:
            logger.info("Warming up Ollama model (background)…")
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
