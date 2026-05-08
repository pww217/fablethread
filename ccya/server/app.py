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

from ccya.engine import EngineConfig, warmup
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
    compact_every=config["game"].get("compact_every", 0),
    compact_temperature=config["game"].get("compact_temperature", 0.1),
)
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
