"""Engine configuration and per-save turn in-flight guard."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import re

from jinja2 import Environment, FileSystemLoader

_log = logging.getLogger(__name__)


class _EventLock:
    def __init__(self) -> None:
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(self, key: str) -> None:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        await self._locks[key].acquire()

    async def release(self, key: str) -> None:
        lock = self._locks.get(key)
        if lock and lock.locked():
            lock.release()


_inflight: _EventLock = _EventLock()


def is_turn_in_progress(save_dir: str) -> bool:
    lock = _inflight._locks.get(save_dir)
    return lock is not None and lock.locked()


@dataclass
class EngineConfig:
    # DURABILITY PATTERNS — how each field is consumed at runtime:
    #
    #   module constant:   Fields defined as module-level variables imported
    #                      at startup (e.g., _MOMENTUM_MIN in rules.py).
    #                      Require server restart to change.
    #   startup only:      Fields read once at EngineConfig construction and
    #                      never re-read (e.g., model, host, temperatures).
    #                      Require server restart to change.
    #   runtime mutable:   Fields that can be changed mid-session via UI
    #                      config panels (future use). Currently none.
    #
    host: str = "http://localhost:8080/v1"
    model: str = "mlx-community/Qwen3.6-27B-4bit"
    request_timeout_s: int = 180
    ruling_temperature: float = 0.2
    extract_temperature: float = 0.4
    narrate_temperature: float = 0.9
    generate_seed_temperature: float = 0.9
    max_llm_retries: int = 1
    context_window: int = 32768
    log_llm_io: bool = False
    log_llm_io_max_chars: int = 4000
    log_prompts: bool = False
    # Avoidance-based pressure decay: keywords that trigger de-escalation detection
    avoidance_keywords: list[str] = field(default_factory=lambda: ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])
    # Momentum floor value and relief trigger threshold
    momentum_floor: int = -3
    momentum_ceiling: int = 3
    # Consecutive pressure threshold for relief trigger
    consecutive_pressure_threshold: int = 3
    # Gate for de-escalation flag on successful rolls
    thread_deescalate_on_success: bool = True
    # TTL (in turns) for resolved arcs and completed threads kept in prompt context

    # Difficulty curve preset (forgiving/balanced/demanding)
    difficulty_curve: str = "balanced"
    # Scene pacing thresholds (turns before directive triggers)
    scene_pressure_threshold: int = 3
    scene_imperative_threshold: int = 5
    # Momentum influence on narrative direction (scaling factor, capped at ±factor)
    momentum_pacing_factor: float = 0.5
    # Near-miss softening: whether near-fails get softer narration directive text
    near_miss_softening: bool = True
    # TTL for completed threads and resolved arcs in narration context (turns)
    thread_memory_ttl: int = 3
    arc_memory_ttl: int = 3

    def _resolve_difficulty_modifiers(self) -> dict[str, int]:
        curves = {
            "forgiving": {"trivial": 3, "easy": 1, "normal": 0, "hard": -1, "extreme": -2},
            "balanced": {"trivial": 2, "easy": 1, "normal": 0, "hard": -1, "extreme": -2},
            "demanding": {"trivial": 1, "easy": 0, "normal": 0, "hard": -1, "extreme": -3},
        }
        return curves.get(self.difficulty_curve or "balanced", curves["balanced"])


def build_engine_config(
    cfg: dict[str, Any],
    temperature_override: float | None = None,
) -> EngineConfig:
    """Build EngineConfig from a raw config dict.

    Single source of truth for all field mappings. Both the server
    and the eval harness call this function.

    Args:
        cfg: Raw config dict (output of ``load_config``).
        temperature_override: If set, uniformly override all temperature
            knobs (rules, narrate, extract, generate_seed).
    """
    llm = cfg.get("llm", {})
    game = cfg.get("game", {})
    logging_cfg = cfg.get("server", {}).get("logging", {})

    narrate_t = float(llm.get("narrate_temperature", 0.9))
    extract_t = float(llm.get("extract_temperature", 0.4))
    ruling_t = float(llm.get("ruling_temperature", 0.2))
    seed_t = float(llm.get("generate_seed_temperature", 0.9))

    if temperature_override is not None:
        t = float(temperature_override)
        narrate_t = extract_t = ruling_t = seed_t = t
        _log.debug("build_engine_config temperature_override=%.2f applied", t)

    if not llm.get("host"):
        _log.warning("build_engine_config: llm.host not configured, using default")
    if not llm.get("model"):
        _log.warning("build_engine_config: llm.model not configured, using default")

    return EngineConfig(
        host=str(llm.get("host", "http://localhost:8080/v1")),
        model=str(llm.get("model", "")),
        context_window=int(llm.get("context_window", 32768)),
        request_timeout_s=int(llm.get("request_timeout_s", 180)),
        narrate_temperature=narrate_t,
        extract_temperature=extract_t,
        ruling_temperature=ruling_t,
        generate_seed_temperature=seed_t,
        max_llm_retries=int(llm.get("max_llm_retries", 1)),
        log_llm_io=bool(logging_cfg.get("log_llm_io", False)),
        log_llm_io_max_chars=int(logging_cfg.get("log_llm_io_max_chars", 4000)),
        log_prompts=bool(logging_cfg.get("log_prompts", False)),

        thread_deescalate_on_success=bool(
            game.get("thread_deescalate_on_success", True)
        ),

        avoidance_keywords=[str(kw) for kw in game.get("avoidance_keywords", ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])],

        momentum_floor=int(game.get("momentum_floor", -3)),
        consecutive_pressure_threshold=int(game.get("consecutive_pressure_threshold", 3)),

        difficulty_curve=game.get("difficulty_curve", "balanced"),
        scene_pressure_threshold=int(game.get("scene_pressure_threshold", 3)),
        scene_imperative_threshold=int(game.get("scene_imperative_threshold", 5)),
        momentum_pacing_factor=float(game.get("momentum_pacing_factor", 0.5)),
        near_miss_softening=bool(game.get("near_miss_softening", True)),
        thread_memory_ttl=int(game.get("thread_memory_ttl", 3)),
        arc_memory_ttl=int(game.get("arc_memory_ttl", 3)),
    )



def _strip_turn_prefix(s: str) -> str:
    if not s:
        return s
    return re.sub(r'^- \[T\d+\] ', '', s).lstrip('- ').strip()


def _build_jinja_env(template_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )
    env.filters["strip_turn_prefix"] = _strip_turn_prefix
    return env


def _render(env: Environment, template_name: str, ctx: dict[str, Any]) -> str:
    return str(env.get_template(template_name).render(**ctx))


# ---------------------------------------------------------------------------
# Shared utilities (moved here to avoid circular imports between rules.py
# and extraction.py)
# ---------------------------------------------------------------------------

_PROMPTS_LOG_PATH = Path("logs/prompts.log")


def _find_json(text: str) -> dict[str, Any] | None:
    text = text.strip()

    def _try(t: str) -> dict[str, Any] | None:
        try:
            result = json.loads(t)
            if isinstance(result, dict):
                return result
            return None
        except (json.JSONDecodeError, ValueError):
            return None

    # 1. Try parsing the entire text as JSON first
    j = _try(text)
    if j is not None:
        return j

    # 2. Extract from code blocks — most reliable when LLM uses markdown fences
    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            r = _try(p)
            if r is not None:
                return r

    # 3. Brace fallback — try multiple closing positions to handle thinking content
    # that may contain braces or malformed fragments between first { and last }
    b = text.find("{")
    if b >= 0:
        # Try from opening brace, find the matching close by counting nesting depth
        depth = 0
        for i in range(b, len(text)):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[b : i + 1]
                    r = _try(candidate)
                    if r is not None:
                        return r

    # 4. Last resort: try from first { to last } (original behavior, least reliable)
    b = text.find("{")
    if b >= 0:
        r_idx = text.rfind("}")
        if r_idx > b:
            r = _try(text[b : r_idx + 1])
            if r is not None:
                return r

    return None


def _truncate(s: str, n: int) -> str:
    if not isinstance(s, str):
        s = str(s)
    if len(s) <= n:
        return s
    return s[:n] + f"…[truncated, {len(s) - n} more chars]"


def _log_llm_io(
    *,
    trace_id: str,
    phase: str,
    messages: list[dict[str, Any]] | None = None,
    response: str | None = None,
    extra: dict[str, Any] | None = None,
    max_chars: int = 4000,
) -> None:
    payload: dict[str, Any] = {"phase": phase, "trace_id": trace_id}
    if messages is not None:
        payload["messages"] = [
            {
                "role": m.get("role"),
                "content": _truncate(m.get("content", ""), max_chars),
            }
            for m in messages
        ]
    if response is not None:
        payload["response"] = _truncate(response, max_chars)
    if extra:
        payload.update(extra)
    _log.debug(
        "llm_io %s", json.dumps(payload, default=str), extra={"trace_id": trace_id}
    )


def _log_prompts(turn: int, call: str, messages: list[dict[str, str]]) -> None:
    lines: list[str] = []
    lines.append(f"## Turn {turn} — {call}")
    lines.append("")
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"--- [{role}] ---")
        lines.append(content)
        lines.append("")
    lines.append("---")
    lines.append("")

    try:
        _PROMPTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(_PROMPTS_LOG_PATH, "a") as f:
            f.write("\n".join(lines))
    except OSError:
        _log.warning("failed to write prompts.log", exc_info=True)
