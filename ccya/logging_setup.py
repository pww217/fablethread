"""Logging: JSONL RotatingFileHandler + SSE error push helper."""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any

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
    ch.setLevel(os.getenv("CCYA_LOG_LEVEL", "INFO"))
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
        for attr in dir(record):
            if not attr.startswith("_"):
                val = getattr(record, attr)
                if isinstance(val, (str, int, float, bool)):
                    log_data[attr] = val
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data, default=str)

