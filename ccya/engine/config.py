"""Engine configuration and per-save turn in-flight guard."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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

_cancel_requested: dict[str, asyncio.Event] = {}
_turn_done: dict[str, asyncio.Event] = {}

def is_turn_in_progress(save_dir: str) -> bool:
    lock = _inflight._locks.get(save_dir)
    return lock is not None and lock.locked()


def request_cancel(save_dir: str) -> None:
    event = _cancel_requested.get(save_dir)
    if event is not None:
        event.set()


def is_cancel_requested(save_dir: str) -> bool:
    event = _cancel_requested.get(save_dir)
    return event is not None and event.is_set()



def clear_cancel(save_dir: str) -> None:
    _cancel_requested.pop(save_dir, None)


def register_turn(save_dir: str) -> None:
    _turn_done[save_dir] = asyncio.Event()


def signal_turn_done(save_dir: str) -> None:
    event = _turn_done.pop(save_dir, None)
    if event is not None:
        event.set()
    clear_cancel(save_dir)


def clear_all_turn_locks(save_dir: str) -> None:
    """Clear all turn-related locks/state for a save directory.

    Called before switching to a save to ensure no stale locks
    from a previous turn in that directory block execution.
    """
    _inflight._locks.pop(save_dir, None)
    _cancel_requested.pop(save_dir, None)
    _turn_done.pop(save_dir, None)


async def await_turn_done(save_dir: str, timeout: float = 30.0) -> bool:
    event = _turn_done.get(save_dir)
    if event is None:
        return False
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False


@dataclass
class CheckerConfig:
    min_reason_words: int = 5
    max_reason_words: int = 10
    band_skew_ratio: float = 0.8
    location_min_sentences: int = 1
    location_min_words: int = 15
    world_state_fact_min_chars: int = 10


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
    model: str = "mlx-community/gemma-4-26b-a4b-it-mxfp8"
    request_timeout_s: int = 1200
    ruling_temperature: float = 0.2
    extract_temperature: float = 0.4
    narrate_temperature: float = 0.9
    generate_seed_temperature: float = 0.7

    # ruling
    ruling_top_p: float = 0.8

    # extract  
    extract_top_p: float = 0.85
    extract_frequency_penalty: float = 0.15

    # narrate
    narrate_top_p: float = 0.95
    narrate_frequency_penalty: float = 0.5

    # generate_seed
    generate_seed_top_p: float = 0.95

    # pack_generation (stub)
    pack_generation_temperature: float = 0.8
    pack_generation_top_p: float = 0.95

    max_llm_retries: int = 1
    context_window: int = 32768
    log_llm_io: bool = False
    log_llm_io_max_chars: int = 4000
    log_prompts: bool = False
    # Avoidance-based pressure decay: keywords that trigger de-escalation detection
    avoidance_keywords: list[str] = field(default_factory=lambda: ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])

    # Max entries in recent_beats history list
    recent_beats_max: int = 5
    # Gate for de-escalation flag on successful rolls
    thread_deescalate_on_success: bool = True
    # TTL (in turns) for resolved arcs and completed threads kept in prompt context

    # Difficulty curve preset (forgiving/balanced/demanding)
    difficulty_curve: str = "balanced"
    # Scene pacing thresholds (turns before directive triggers)
    scene_pressure_threshold: int = 3
    scene_imperative_threshold: int = 5
    # Scene phase thresholds
    climax_turn_limit: int = 4          # max turns in CLIMAX before forced RESOLUTION
    breather_max_turns: int = 3         # max turns in BREATHER before forced RISING transition
    convergence_threshold: int = 2
    # Near-miss softening: whether near-fails get softer narration directive text
    near_miss_softening: bool = True
    # TTL for completed threads and resolved arcs in narration context (turns)
    thread_memory_ttl: int = 3
    arc_memory_ttl: int = 3
    # Max active threads before eviction of oldest
    thread_max_active: int = 5

    # Death spiral detection
    spiral_consecutive_hard: int = 3        # N consecutive hard+ rolls triggers spiral flag
    spiral_hard_ratio: tuple[int, int] = (3, 5)  # M of last N hard+ triggers spiral flag

    # Urgency decay: demote urgent→normal→background after N turns at same urgency level
    thread_urgency_max_age: int = 8
    # Thread creation cooldown (minimum turns between new thread additions)
    thread_creation_cooldown: int = 3

    # Thread sanitizer: batch arc/thread cleanup every N turns
    sanitize_every: int = 5       # 0 = disabled
    sanitize_temperature: float = 0.3

    # NPC lifecycle TTLs
    nearby_decay_ttl: int = 2       # turns before nearby → known auto-decay
    departed_archive_ttl: int = 3  # turns as "departed" before → archived
    # Condition TTL
    condition_default_ttl: int = 10  # turns assigned when LLM omits turns_remaining

    debug_mode: bool = False

    # Checker thresholds
    checkers: CheckerConfig = field(default_factory=CheckerConfig)

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

    ruling_cfg = llm.get("ruling", {})
    ruling_t = float(ruling_cfg.get("temperature", 0.2))
    ruling_top_p = float(ruling_cfg.get("top_p", 0.8))

    extract_cfg = llm.get("extract", {})
    extract_t = float(extract_cfg.get("temperature", 0.4))
    extract_top_p = float(extract_cfg.get("top_p", 0.85))
    extract_freq_penalty = float(extract_cfg.get("frequency_penalty") or 0)

    narrate_cfg = llm.get("narrate", {})
    narrate_t = float(narrate_cfg.get("temperature", 0.9))
    narrate_top_p = float(narrate_cfg.get("top_p", 0.95))
    narrate_freq_penalty = float(narrate_cfg.get("frequency_penalty") or 0)

    seed_cfg = llm.get("generate_seed", {})
    seed_t = float(seed_cfg.get("temperature", 0.9))
    seed_top_p = float(seed_cfg.get("top_p", 0.95))

    pack_cfg = llm.get("pack_generation", {})
    pack_temp = float(pack_cfg.get("temperature") or 0.8)
    pack_top_p = float(pack_cfg.get("top_p") or 0.95)

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
        request_timeout_s=int(llm.get("request_timeout_s", 1200)),
        narrate_temperature=narrate_t,
        extract_temperature=extract_t,
        ruling_temperature=ruling_t,
        generate_seed_temperature=seed_t,
        ruling_top_p=ruling_top_p,
        extract_top_p=extract_top_p,
        extract_frequency_penalty=extract_freq_penalty,
        narrate_top_p=narrate_top_p,
        narrate_frequency_penalty=narrate_freq_penalty,
        generate_seed_top_p=seed_top_p,
        pack_generation_temperature=pack_temp,
        pack_generation_top_p=pack_top_p,
        max_llm_retries=int(llm.get("max_llm_retries", 1)),
        log_llm_io=bool(logging_cfg.get("log_llm_io", False)),
        log_llm_io_max_chars=int(logging_cfg.get("log_llm_io_max_chars", 4000)),
        log_prompts=bool(logging_cfg.get("log_prompts", False)),

        thread_deescalate_on_success=bool(
            game.get("thread_deescalate_on_success", True)
        ),

        avoidance_keywords=[str(kw) for kw in game.get("avoidance_keywords", ["retreat", "run", "flee", "hide", "rest", "escape", "back away", "disengage", "withdraw", "surrender", "concede", "leave", "get out"])],

        recent_beats_max=int(game.get("recent_beats_max", 5)),

        difficulty_curve=game.get("difficulty_curve", "balanced"),
        scene_pressure_threshold=int(game.get("scene_pressure_threshold", 3)),
        scene_imperative_threshold=int(game.get("scene_imperative_threshold", 5)),
        climax_turn_limit=int(game.get("climax_turn_limit", 4)),
        breather_max_turns=int(game.get("breather_max_turns", 3)),
        convergence_threshold=int(game.get("convergence_threshold", 2)),
        near_miss_softening=bool(game.get("near_miss_softening", True)),
        thread_memory_ttl=int(game.get("thread_memory_ttl", 3)),
        arc_memory_ttl=int(game.get("arc_memory_ttl", 3)),
        thread_max_active=int(game.get("thread_max_active", 5)),

        # Thread lifecycle enforcement
        thread_urgency_max_age=int(game.get("thread_urgency_max_age", 8)),
        thread_creation_cooldown=int(game.get("thread_creation_cooldown", 3)),

        sanitize_every=int(game.get("sanitize_every", 5)),   # 0 = disabled
        sanitize_temperature=float(
            llm.get("sanitize", {}).get("temperature", 0.3)
        ),

        debug_mode=bool(game.get("debug", {}).get("enabled", False)),

        checkers=_build_checkers_config(cfg),

        condition_default_ttl=int(game.get("condition_default_ttl", 10)),
    )


def _build_checkers_config(cfg: dict[str, Any]) -> CheckerConfig:
    checkers_raw = cfg.get("checkers") or {}
    if not isinstance(checkers_raw, dict):
        checkers_raw = {}
    return CheckerConfig(
        min_reason_words=int(checkers_raw.get("min_reason_words", 3)),
        band_skew_ratio=float(checkers_raw.get("band_skew_ratio", 0.8)),
        location_min_sentences=int(checkers_raw.get("location_min_sentences", 1)),
        location_min_words=int(checkers_raw.get("location_min_words", 15)),
        world_state_fact_min_chars=int(checkers_raw.get("world_state_fact_min_chars", 10)),
    )



def _build_jinja_env(template_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        keep_trailing_newline=True,
    )
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
