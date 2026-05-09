"""FastAPI app bootstrap, config, Jinja env, pack loading, startup."""

from __future__ import annotations

import asyncio
from collections import deque
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, pass_context

from ccya.engine import build_engine_config, warmup
from ccya.engine.config import _validate_compactor_config
from ccya.logging_setup import setup_logging
from ccya.models import load_config as _load_config
from ccya.pack import Pack, load_pack

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
TEMPLATES_DIR = BASE_DIR.parent / "templates"
PROMPTS_DIR = BASE_DIR.parent / "prompts"
PACKS_DIR = REPO_ROOT / "packs"
SAVE_DIR = Path("saves") / "default"

config: dict[str, Any] = _load_config(REPO_ROOT / "config.yaml")
engine_config = build_engine_config(config)
_validate_compactor_config(engine_config)

logger = setup_logging(config)

_pack_id: str = config.get("game", {}).get("setting_pack", "expanse-belter")
try:
    _active_pack: Pack = load_pack(_pack_id, PACKS_DIR)
    logger.info("Loaded pack: %s (mode=%s)", _pack_id, _active_pack.mode)
except Exception as exc:
    logger.error("Failed to load pack %r: %s", _pack_id, exc)
    raise

_dynamic_opening: str = ""
_dynamic_opening_actions: list[str] = []

app = FastAPI(title="ccya")

# Import routes so @app.get/@app.post decorators register handlers.
# Must be after `app` is created to avoid circular import.
import ccya.server.routes  # noqa: F401, E402
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


app.mount("/static", StaticFiles(directory=str(BASE_DIR.parent / "static")), name="static")


def _validate_stats(stats: dict[str, int]) -> bool:
    SKILLS = {"strength", "dexterity", "wits", "lore", "charisma", "resolve"}
    if set(stats.keys()) != SKILLS:
        return False
    if not all(isinstance(v, int) and 1 <= v <= 4 for v in stats.values()):
        return False
    total = sum(stats.values())
    return 12 <= total <= 16


@app.on_event("startup")
async def startup_event():
    logger.info(
        "pack: %s (mode=%s) | LLM: %s",
        _pack_id,
        _active_pack.mode,
        engine_config.model,
    )
    if config.get("game", {}).get("warmup_on_start", True):

        async def _warmup_bg() -> None:
            logger.info("warming up LLM model (background)…")
            await warmup(engine_config)
            logger.info("model warmup complete")

        asyncio.create_task(_warmup_bg())


def main() -> None:
    """Run the server (entry point for uvicorn)."""
    import uvicorn

    host = config["server"]["bind_host"]
    port = config["server"]["bind_port"]
    uvicorn.run(app, host=host, port=port, reload=False)
