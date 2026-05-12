"""Engine configuration and per-save turn in-flight guard."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

_log = logging.getLogger("ccya.engine")


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
    host: str = "http://localhost:8080/v1"
    model: str = "mlx-community/Qwen3.6-27B-4bit"
    # Local prompt-token budget for trim_messages (NOT sent to the LLM API —
    # mlx_lm.server has no equivalent of Ollama's num_ctx knob; this just
    # caps how much we pack into a single request).
    prompt_token_budget: int = 32768
    request_timeout_s: int = 180
    narrate_temperature: float = 0.9
    extract_temperature: float = 0.4
    max_extract_retries: int = 1
    window_turns: int = 3
    chronicle_prefix_budget_tokens: int = 1500
    recent_events_max: int = 20
    enable_extract_thinking: bool = False
    enable_narrate_thinking: bool = False
    # generate_seed settings (used by POST /new-game on dynamic packs)
    generate_seed_temperature: float = 0.9
    generate_seed_max_retries: int = 1
    log_llm_io: bool = False
    log_llm_io_max_chars: int = 4000
    rules_temperature: float = 0.2
    max_rules_retries: int = 1
    max_generate_pack_retries: int = 1
    log_prompts: bool = False
    # Scene pressure urgency escalation thresholds (turns)
    scene_pressure_building_at: int = 6
    scene_pressure_immediate_at: int = 10
    # Scene pressure hard age cap (turns) — auto-remove pressures older than this
    scene_pressure_max_age: int = 15
    # Scene pressure immediate TTL (turns) — how long an immediate pressure lasts
    # from the turn it became immediate (not from turn_added).
    scene_pressure_immediate_ttl: int = 8
    # Avoidance-based pressure decay: keywords that trigger de-escalation detection
    avoidance_keywords: list[str] = field(default_factory=lambda: ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])
    # Avoidance decay: extra age increment per turn for non-immediate pressures
    avoidance_decay_per_turn: int = 1
    # Momentum floor value and relief trigger threshold
    momentum_floor: int = -3
    momentum_floor_relief_turns: int = 2
    # Gate for de-escalation flag on successful rolls
    scene_pressure_deescalate_on_success: bool = True
    # Compaction: periodically compress narrative history + events
    compact_every: int = 0
    compact_temperature: float = 0.1
    recent_turns_min: int = 2


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
    rules = cfg.get("rules", {})
    logging_cfg = cfg.get("logging", {})

    narrate_t = float(llm.get("narrate_temperature", 0.9))
    extract_t = float(llm.get("extract_temperature", 0.4))
    rules_t = float(rules.get("temperature", 0.2))
    seed_t = float(llm.get("generate_seed_temperature", 0.9))

    if temperature_override is not None:
        t = float(temperature_override)
        narrate_t = extract_t = rules_t = seed_t = t

    return EngineConfig(
        host=str(llm.get("host", "http://localhost:8080/v1")),
        model=str(llm.get("model", "")),
        prompt_token_budget=int(llm.get("prompt_token_budget", 28672)),
        request_timeout_s=int(llm.get("request_timeout_s", 180)),
        narrate_temperature=narrate_t,
        extract_temperature=extract_t,
        max_extract_retries=int(llm.get("max_extract_retries", 1)),
        window_turns=int(game.get("window_turns", 3)),
        chronicle_prefix_budget_tokens=int(
            game.get("chronicle_prefix_budget_tokens", 1500)
        ),
        recent_events_max=int(game.get("recent_events_max", 20)),
        enable_extract_thinking=bool(llm.get("enable_extract_thinking", False)),
        enable_narrate_thinking=bool(llm.get("enable_narrate_thinking", False)),
        generate_seed_temperature=seed_t,
        generate_seed_max_retries=int(llm.get("generate_seed_max_retries", 1)),
        log_llm_io=bool(logging_cfg.get("log_llm_io", False)),
        log_llm_io_max_chars=int(logging_cfg.get("log_llm_io_max_chars", 4000)),
        log_prompts=bool(logging_cfg.get("log_prompts", False)),
        rules_temperature=rules_t,
        max_rules_retries=int(rules.get("max_retries", 1)),
        max_generate_pack_retries=int(llm.get("max_generate_pack_retries", 1)),
        scene_pressure_building_at=int(game.get("scene_pressure_building_at", 6)),
        scene_pressure_immediate_at=int(
            game.get("scene_pressure_immediate_at", 10)
        ),
        scene_pressure_max_age=int(game.get("scene_pressure_max_age", 15)),
        scene_pressure_deescalate_on_success=bool(
            game.get("scene_pressure_deescalate_on_success", True)
        ),
        scene_pressure_immediate_ttl=int(game.get("scene_pressure_immediate_ttl", 8)),
        avoidance_keywords=[str(kw) for kw in game.get("avoidance_keywords", ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])],
        avoidance_decay_per_turn=int(game.get("avoidance_decay_per_turn", 1)),
        momentum_floor=int(game.get("momentum_floor", -3)),
        momentum_floor_relief_turns=int(game.get("momentum_floor_relief_turns", 2)),
        compact_every=int(game.get("compact_every", 0)),
        compact_temperature=float(game.get("compact_temperature", 0.1)),
        recent_turns_min=int(game.get("recent_turns_min", 2)),
    )


def _validate_compactor_config(config: EngineConfig) -> None:
    if config.window_turns < 1:
        raise ValueError(f"window_turns must be >= 1, got {config.window_turns}")
    if config.compact_every < 0:
        raise ValueError(
            f"compact_every must be >= 0, got {config.compact_every}"
        )
    if 0 < config.compact_every <= config.window_turns:
        raise ValueError(
            f"compact_every ({config.compact_every}) must be > window_turns ({config.window_turns})"
        )
    if config.recent_turns_min < 0:
        raise ValueError(f"recent_turns_min must be >= 0, got {config.recent_turns_min}")
    if config.recent_turns_min > config.window_turns:
        raise ValueError(
            f"recent_turns_min ({config.recent_turns_min}) must be <= window_turns ({config.window_turns})"
        )


def _build_jinja_env(template_dir: str) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )


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

    j = _try(text)
    if j is not None:
        return j

    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            r = _try(p)
            if r is not None:
                return r

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
