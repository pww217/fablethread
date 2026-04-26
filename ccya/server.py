"""FastAPI server with SSE turn endpoint and HTMX panels."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import FileSystemLoader, Environment
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
    request_timeout_s=config["ollama"]["request_timeout_s"],
    narrate_temperature=config["ollama"]["narrate_temperature"],
    extract_temperature=config["ollama"]["extract_temperature"],
    max_extract_retries=config["ollama"]["max_extract_retries"],
    window_turns=config["game"]["window_turns"],
    chronicle_prefix_budget_tokens=config["game"]["chronicle_prefix_budget_tokens"],
    established_facts_max=config["game"]["established_facts_max"],
)

logger = setup_logging(config)

app = FastAPI(title="ccya")
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)

# Track request timing for debug panel
_REQUEST_LOG: list[dict[str, Any]] = []


def _render(template_name: str, context: dict) -> HTMLResponse:
    template = _jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


# Mount static files (vendored JS, compiled CSS)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_current_state() -> dict:
    return load_state(SAVE_DIR)


def _load_opening() -> str:
    """Load the opening scene from the setting pack."""
    pack = config.get("game", {}).get("setting_pack", "hard-scifi-demo")
    path = BASE_DIR.parent / "packs" / pack / "opening_scene.md"
    if path.exists():
        return path.read_text()
    return ""


def _add_timing(entry: dict, start: float) -> None:
    """Add elapsed_ms to a timing entry."""
    entry["elapsed_ms"] = round((time.time() - start) * 1000, 1)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    state = _load_current_state()
    return _render("index.html", {"state": state})


@app.post("/turn")
async def post_turn(request: Request):
    """POST /turn {input: str} -> SSE stream of narrative tokens + final event."""
    form = await request.form()
    user_input = form.get("input", "").strip()
    if not user_input:
        return {"error": "Empty input"}

    if is_turn_in_progress(str(SAVE_DIR)):
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail="Turn already in progress")

    start = time.time()

    async def event_stream():
        timing = {"event": "turn_start", "input": user_input[:100]}
        _add_timing(timing, start)
        _REQUEST_LOG.append(timing)
        yield {"event": "turn_start", "data": json.dumps(timing)}

        try:
            result = await run_turn(
                SAVE_DIR, user_input,
                config=engine_config,
                template_dir=str(PROMPTS_DIR),
            )
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
            timing["error"] = str(e)
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@app.post("/new-game")
async def new_game(request: Request):
    """Reset save from starter pack seed state."""
    seed = _load_seed()
    seed.setdefault("meta", {})
    seed["meta"]["model"] = config["ollama"]["model"]
    init_save_dir(SAVE_DIR, seed)
    return _render("_state.html", {"state": load_state(SAVE_DIR)})


def _load_seed() -> dict:
    pack = config.get("game", {}).get("setting_pack", "hard-scifi-demo")
    seed_path = BASE_DIR.parent / "packs" / pack / "seed_state.yaml"
    if seed_path.exists():
        with open(seed_path) as f:
            return yaml.safe_load(f) or {}
    return {}


@app.get("/panels/state")
def panel_state(request: Request):
    return _render("_state.html", {"state": _load_current_state()})


@app.get("/panels/actions")
def panel_actions(request: Request):
    state = _load_current_state()
    return _render("_actions.html", {"state": state})


@app.get("/panels/errors")
def panel_errors(request: Request):
    return _render("_errors.html", {"state": _load_current_state(), "errors": []})


@app.get("/panels/debug")
def panel_debug():
    """Return debug info: request log and mock mode status."""
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    return _render("_debug.html", {
        "requests": _REQUEST_LOG[-20:],
        "mock_mode": mock_mode,
        "state": _load_current_state(),
    })


@app.get("/opening")
def opening():
    """Return the opening scene text for a new game."""
    return HTMLResponse(_load_opening())


@app.get("/healthz")
def healthz():
    import httpx
    host = config["ollama"]["host"]
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    if mock_mode:
        return {
            "ollama": "mock",
            "model": config["ollama"]["model"],
            "available": True,
            "mock": True,
        }
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{host}/api/tags")
            resp.raise_for_status()
            tags = resp.json()
            models = [m["name"] for m in tags.get("models", [])]
            model = config["ollama"]["model"]
            return {"ollama": "ok", "model": model, "available": model in models}
    except Exception:
        return {"ollama": "fail", "model": config["ollama"]["model"], "available": False}


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info("ccya starting")
    if config.get("game", {}).get("warmup_on_start", True):
        logger.info("Warming up Ollama model...")
        await warmup(engine_config)
        logger.info("Model warmup complete")


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def main() -> None:
    import uvicorn
    host = config["server"]["bind_host"]
    port = config["server"]["bind_port"]
    uvicorn.run("ccya.server:app", host=host, port=port, reload=False)
