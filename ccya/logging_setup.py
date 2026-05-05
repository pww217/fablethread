"""Logging: JSONL RotatingFileHandler + SSE error push helper."""

from __future__ import annotations

import json
import logging
import logging.handlers
from pathlib import Path
from typing import Any, Callable

from ccya.models import load_config


def setup_logging(config: dict[str, Any] | None = None) -> logging.Logger:
    if config is None:
        config = load_config()

    log_cfg = config.get("logging", {})
    log_file = log_cfg.get("file", "logs/llm-g.log")
    level_str = log_cfg.get("level", "INFO")
    level = getattr(logging, level_str, logging.INFO)

    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("ccya")
    logger.setLevel(level)

    fh = logging.handlers.RotatingFileHandler(
        str(log_path), maxBytes=5 * 1024 * 1024, backupCount=3
    )
    fh.setLevel(level)
    fh.setFormatter(_JsonFormatter())
    logger.addHandler(fh)

    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

    return logger


class _JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)


class _SseErrorHandler:

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []
        self._callbacks: list[Callable[[dict[str, Any]], None]] = []

    def register(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._callbacks.append(callback)

    def push(self, error: dict[str, Any]) -> None:
        self._events.append(error)
        for cb in self._callbacks:
            try:
                cb(error)
            except Exception:
                pass

    def get_events(self) -> list[dict[str, Any]]:
        return self._events

    def clear(self) -> None:
        self._events.clear()
