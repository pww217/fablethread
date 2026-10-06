"""Logging: JSONL RotatingFileHandler + SSE error push helper."""

from __future__ import annotations

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Any

from fablethread.models import load_config


def setup_logging(config: dict[str, Any] | None = None) -> logging.Logger:
    if getattr(setup_logging, "_done", False):
        return logging.getLogger("fablethread")

    if config is None:
        config = load_config()

    log_cfg = config.get("server", {}).get("logging", {})
    level_str = log_cfg.get("level", "INFO")
    level = getattr(logging, level_str, logging.INFO)

    console_level_str = log_cfg.get("console_level", "INFO")
    console_level = getattr(logging, console_level_str, logging.INFO)

    log_path = Path("logs/game.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("fablethread")
    logger.setLevel(level)

    fh = logging.handlers.RotatingFileHandler(
        str(log_path), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setLevel(level)
    fh.setFormatter(_JsonFormatter())
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(console_level)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    setup_logging._done = True  # type: ignore[attr-defined]
    return logger


class _JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for attr in dir(record):
            if not attr.startswith("_"):
                val = getattr(record, attr)
                if isinstance(val, (str, int, float, bool)):
                    log_data[attr] = val
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


def setup_server_logging() -> logging.Logger:
    """Set up a dedicated RotatingFileHandler for server errors (logs/server.log).

    Returns a logger named 'fablethread.server' that writes to logs/server.log.
    This is separate from the main 'fablethread' logger so server errors can be
    tracked independently.
    """
    server_logger = logging.getLogger("fablethread.server")
    server_logger.setLevel(logging.ERROR)

    server_log_path = Path("logs/server.log")
    server_log_path.parent.mkdir(parents=True, exist_ok=True)

    fh = logging.handlers.RotatingFileHandler(
        str(server_log_path), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setLevel(logging.ERROR)
    fh.setFormatter(_JsonFormatter())
    server_logger.addHandler(fh)

    return server_logger
