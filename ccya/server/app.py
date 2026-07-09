"""FastAPI app bootstrap, config, Jinja env, pack loading, startup."""

from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, pass_context

from ccya.engine import build_engine_config, warmup
from ccya.engine.npc_roster import generate_npc_color
from ccya.errors import ErrorKind, LlmcApiError, LlmcRateLimit, LlmcTimeout
from ccya.logging_setup import setup_logging, setup_server_logging
from ccya.models import load_config as _load_config
from ccya.pack import Pack, load_pack

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
TEMPLATES_DIR = BASE_DIR.parent / "templates"
PROMPTS_DIR = BASE_DIR.parent / "prompts"
PACKS_DIR = REPO_ROOT / "packs"
SAVE_DIR: Path | None = None
_turn_lock: asyncio.Lock | None = None
_cancel_event: asyncio.Event | None = None
_turn_done_event: asyncio.Event | None = None


def _start_turn() -> tuple[asyncio.Lock, asyncio.Event, asyncio.Event]:
    global _turn_lock, _cancel_event, _turn_done_event
    _turn_lock = asyncio.Lock()
    _cancel_event = asyncio.Event()
    _turn_done_event = asyncio.Event()
    return _turn_lock, _cancel_event, _turn_done_event


def _signal_turn_done() -> None:
    global _turn_lock, _cancel_event, _turn_done_event
    if _turn_done_event:
        _turn_done_event.set()
    if _cancel_event:
        _cancel_event.set()
    if _turn_lock:
        _turn_lock.release()
    _turn_lock = _cancel_event = _turn_done_event = None


def _is_cancel_requested() -> bool:
    return _cancel_event is not None and _cancel_event.is_set()


def _is_turn_in_progress() -> bool:
    return _turn_lock is not None and _turn_lock.locked()


async def _await_turn_done(timeout: float = 30.0) -> bool:
    if _turn_done_event is None:
        return False
    try:
        await asyncio.wait_for(_turn_done_event.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False


def _find_all_save_dirs(limit: int | None = None) -> list[Path]:
    """Find save directories in both saves/ and evals/runs/, optionally limited to most recent."""
    all_dirs: dict[str, Path] = {}
    for root in [Path("saves"), Path("evals/runs")]:
        if root.exists():
            for entry in root.iterdir():
                if not entry.is_dir() or entry.name == "default":
                    continue
                if (entry / "state.yaml").exists():
                    r = entry.resolve()
                    all_dirs.setdefault(str(r), r)
                else:
                    for sub in entry.iterdir():
                        if sub.is_dir() and (sub / "state.yaml").exists():
                            r = sub.resolve()
                            all_dirs.setdefault(str(r), r)
    result = list(all_dirs.values())
    if limit is not None:
        result.sort(key=lambda d: d.stat().st_mtime, reverse=True)
        result = result[:limit]
    return result


def _has_game_progress(save_dir: Path) -> bool:
    """Check if a save directory has actual game progress (not just a fresh init)."""
    events = save_dir / "events.jsonl"
    if events.exists() and events.stat().st_size > 0:
        return True
    chronicle = save_dir / "chronicle.md"
    if chronicle.exists() and chronicle.stat().st_size > 0:
        content = chronicle.read_text()
        if "## Turn 1" in content or "## Turn 2" in content:
            return True
    return False


def _find_latest_save() -> Path | None:
    """Return the most recently modified save directory with actual game progress."""
    candidates = _find_all_save_dirs()
    progress = [d for d in candidates if _has_game_progress(d)]
    return max(progress, key=lambda d: d.stat().st_mtime) if progress else None


_latest = _find_latest_save()
if _latest is not None:
    SAVE_DIR = _latest


config: dict[str, Any] = _load_config(REPO_ROOT / "config.yaml")
engine_config = build_engine_config(config)

logger = setup_logging(config)
server_logger = setup_server_logging()

if SAVE_DIR is not None:
    logger.info("Resumed save: %s", SAVE_DIR)
else:
    logger.info("No existing save found — select or create a save to begin")

_pack_id: str = config.get("game", {}).get("setting_pack", "zombie-survival")
try:
    _active_pack: Pack = load_pack(_pack_id, PACKS_DIR)
    logger.info("Loaded pack: %s", _pack_id)
except Exception as exc:
    logger.error("Failed to load pack %r: %s", _pack_id, exc)
    raise

_dynamic_opening: str = ""
_dynamic_opening_outcome: str = ""

@asynccontextmanager
async def lifespan(app):
    logger.info(
        "pack: %s | LLM: %s",
        _pack_id,
        engine_config.model,
    )
    if config.get("game", {}).get("warmup_on_start", False):

        async def _warmup_bg() -> None:
            logger.info("warming up LLM model (background)…")
            await warmup(engine_config)
            logger.info("model warmup complete")

        asyncio.create_task(_warmup_bg())
    yield


app = FastAPI(title="ccya", lifespan=lifespan)
logger.debug("App startup: pack=%s save_dir=%s", _pack_id, SAVE_DIR)


# Server error persistence
_errors_file_path: Path | None = None


def _ensure_errors_file(data_dir: str) -> Path:
    global _errors_file_path
    if _errors_file_path is None:
        path = Path(data_dir) / "server_errors.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        _errors_file_path = path
    return _errors_file_path


def _persist_server_error(exc: Exception, *, kind: str | None = ErrorKind.SERVER_ERROR, **extra_fields):
    """Persist a server-level error to server_errors.jsonl for turn viewer enrichment."""
    data_dir = config.get("server", {}).get("data_dir", "saves")
    errors_file = _ensure_errors_file(data_dir)

    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR",
        "error_kind": kind,
        "message": str(exc),
        **extra_fields,
    }

    with open(errors_file, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    server_logger.error(
        "server_error %s", str(exc),
        extra={"error_kind": kind, **extra_fields},
    )


@app.middleware("http")
async def server_exception_middleware(request: Request, call_next):
    """Catch any unhandled exception in route handlers and persist to server_errors.jsonl."""
    try:
        response = await call_next(request)
        return response
    except LlmcTimeout as exc:
        _persist_server_error(exc, kind=ErrorKind.LLM_TIMEOUT, path=str(request.url.path))
        return JSONResponse(status_code=504, content={"error": "LLM timeout"})
    except LlmcRateLimit as exc:
        _persist_server_error(exc, kind=ErrorKind.LLM_RATE_LIMIT, path=str(request.url.path))
        return JSONResponse(status_code=429, content={"error": "Rate limited by LLM provider"})
    except LlmcApiError as exc:
        status = 502 if exc.status_code else 500
        _persist_server_error(exc, kind=ErrorKind.LLM_API_ERROR, path=str(request.url.path), status_code=exc.status_code)
        return JSONResponse(status_code=status, content={"error": str(exc)})
    except Exception as exc:
        _persist_server_error(
            exc, kind=ErrorKind.SERVER_ERROR, path=str(request.url.path), exception_type=type(exc).__name__,
        )
        return JSONResponse(status_code=500, content={"error": "Internal server error"})


# Import routes so @app.get/@app.post decorators register handlers.
# Must be after `app` is created to avoid circular import.
import ccya.server.routes  # noqa: F401, E402  # late import required by FastAPI route registration (circular if done earlier)
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=True,
)
_jinja_env.filters["tojson"] = pass_context(lambda ctx, obj: __import__("json").dumps(obj))

_jinja_env.filters["npc_color"] = generate_npc_color


def _render(template_name: str, context: dict[str, Any]) -> HTMLResponse:
    template = _jinja_env.get_template(template_name)
    return HTMLResponse(template.render(**context))


app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "static")), name="static")


def _validate_stats(stats: dict[str, int]) -> bool:
    SKILLS = {"strength", "dexterity", "wits", "charisma"}
    if set(stats.keys()) != SKILLS:
        return False
    if not all(isinstance(v, int) and 1 <= v <= 4 for v in stats.values()):
        return False
    total = sum(stats.values())
    return 8 <= total <= 12


def main() -> None:
    """Run the server (entry point for uvicorn)."""
    import uvicorn

    host = config["server"]["bind_host"]
    port = config["server"]["bind_port"]
    uvicorn.run(app, host=host, port=port, reload=False)
