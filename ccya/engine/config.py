"""Engine configuration."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from jinja2 import Environment, FileSystemLoader

_log = logging.getLogger(__name__)


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
    host: str = "http://10.75.100.51:1234/v1"
    model: str = "google/gemma-4-26b-a4b-it"
    num_ctx: int = 16384
    request_timeout_s: int = 1200
    ruling_temperature: float = 0.2
    extract_temperature: float = 0.4
    world_temperature: float = 0.55
    narrate_temperature: float = 0.9
    prepare_seed_temperature: float = 0.4

    # ruling
    ruling_top_p: float = 0.8

    # extract  
    extract_top_p: float = 0.85
    extract_frequency_penalty: float = 0.05

    # narrate
    narrate_top_p: float = 0.95
    narrate_frequency_penalty: float = 0.3

    # prepare_seed
    prepare_seed_top_p: float = 0.95

    # pack_generation (stub)
    pack_generation_temperature: float = 0.8
    pack_generation_top_p: float = 0.95

    max_llm_retries: int = 1
    context_window: int = 32768
    fallback_host: str = ""
    fallback_cooldown_s: int = 300

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
    # EMA smoothing for convergence score
    convergence_alpha: float = 0.4
    # Hysteresis thresholds for phase transitions
    convergence_enter_threshold: int = 2
    convergence_exit_threshold: int = 1
    # Configurable phase minimums
    RISING_min: int = 3
    CLIMAX_min: int = 3
    BREATHER_min: int = 2
    # New convergence components
    roll_starvation_threshold: int = 3    # turns without a roll before +1
    threat_density_threshold: int = 3     # active threat threads before +1
    # CLIMAX extension
    extension_max: int = 2               # max additional CLIMAX turns beyond climax_turn_limit
    # Near-miss softening: whether near-fails get softer narration directive text
    near_miss_softening: bool = True
    # TTL for completed threads and resolved arcs in narration context (turns)
    thread_memory_ttl: int = 3
    arc_memory_ttl: int = 3
    # Max active threads before eviction of oldest
    thread_max_active: int = 5
    # Turns without activity before auto-dormant
    thread_dormant_threshold: int = 8

    # Urgency decay: demote urgent→normal→background after N turns at same urgency level
    thread_urgency_max_age: int = 8

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

    Defaults: host=http://10.75.100.51:1234/v1,     model=google/gemma-4-26b-a4b-it.

    Args:
        cfg: Raw config dict (output of ``load_config``).
        temperature_override: If set, uniformly override all temperature
            knobs (rules, narrate, extract). Seed steps use config defaults.
    """
    llm = cfg.get("llm", {})
    game = cfg.get("game", {})

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

    seed_cfg = llm.get("prepare_seed", {})
    seed_t = float(seed_cfg.get("temperature", 0.4))
    seed_top_p = float(seed_cfg.get("top_p", 0.95))

    pack_cfg = llm.get("pack_generation", {})
    pack_temp = float(pack_cfg.get("temperature") or 0.8)
    pack_top_p = float(pack_cfg.get("top_p") or 0.95)

    if temperature_override is not None:
        t = float(temperature_override)
        narrate_t = extract_t = ruling_t = t
        _log.debug("build_engine_config temperature_override=%.2f applied (seed uses config default)", t)

    if not llm.get("host"):
        _log.warning("build_engine_config: llm.host not configured, using default")
    if not llm.get("model"):
        _log.warning("build_engine_config: llm.model not configured, using default")

    return EngineConfig(
        host=str(llm.get("host", "http://10.75.100.51:1234/v1")),
        model=str(llm.get("model", "google/gemma-4-26b-a4b-it")),
        num_ctx=int(llm.get("num_ctx", 16384)),
        context_window=int(llm.get("context_window", 16384)),
        request_timeout_s=int(llm.get("request_timeout_s", 1200)),
        narrate_temperature=narrate_t,
        extract_temperature=extract_t,
        world_temperature=float(game.get("world_temperature", 0.55)),
        ruling_temperature=ruling_t,
        prepare_seed_temperature=seed_t,
        ruling_top_p=ruling_top_p,
        extract_top_p=extract_top_p,
        extract_frequency_penalty=extract_freq_penalty,
        narrate_top_p=narrate_top_p,
        narrate_frequency_penalty=narrate_freq_penalty,
        prepare_seed_top_p=seed_top_p,
        pack_generation_temperature=pack_temp,
        pack_generation_top_p=pack_top_p,
        max_llm_retries=int(llm.get("max_llm_retries", 1)),
        fallback_host=str(llm.get("fallback_host", "")),
        fallback_cooldown_s=int(llm.get("fallback_cooldown_s", 300)),

        thread_deescalate_on_success=bool(
            game.get("thread_deescalate_on_success", True)
        ),

        recent_beats_max=int(game.get("recent_beats_max", 5)),

        difficulty_curve=game.get("difficulty_curve", "balanced"),
        scene_pressure_threshold=int(game.get("scene_pressure_threshold", 3)),
        scene_imperative_threshold=int(game.get("scene_imperative_threshold", 5)),
        climax_turn_limit=int(game.get("climax_turn_limit", 4)),
        breather_max_turns=int(game.get("breather_max_turns", 3)),
        convergence_alpha=float(game.get("convergence_alpha", 0.4)),
        convergence_enter_threshold=int(game.get("convergence_enter_threshold", 3)),
        convergence_exit_threshold=int(game.get("convergence_exit_threshold", 1)),
        RISING_min=int(game.get("RISING_min", 3)),
        CLIMAX_min=int(game.get("CLIMAX_min", 3)),
        BREATHER_min=int(game.get("BREATHER_min", 2)),
        roll_starvation_threshold=int(game.get("roll_starvation_threshold", 3)),
        threat_density_threshold=int(game.get("threat_density_threshold", 3)),
        extension_max=int(game.get("extension_max", 2)),
        near_miss_softening=bool(game.get("near_miss_softening", True)),
        thread_memory_ttl=int(game.get("thread_memory_ttl", 3)),
        arc_memory_ttl=int(game.get("arc_memory_ttl", 3)),
        thread_max_active=int(game.get("thread_max_active", 5)),

        # Thread lifecycle enforcement
        thread_urgency_max_age=int(game.get("thread_urgency_max_age", 8)),

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



_jinja_env_cache: dict[str, Environment] = {}


def _build_jinja_env(template_dir: str) -> Environment:
    if template_dir not in _jinja_env_cache:
        _jinja_env_cache[template_dir] = Environment(
            loader=FileSystemLoader(template_dir),
            keep_trailing_newline=True,
        )
    return _jinja_env_cache[template_dir]


def _render(env: Environment, template_name: str, ctx: dict[str, Any]) -> str:
    return str(env.get_template(template_name).render(**ctx))


# ---------------------------------------------------------------------------
# Shared utilities (moved here to avoid circular imports between rules.py
# and extraction.py)
# ---------------------------------------------------------------------------


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

    # 0. Fix malformed keys like "dormant: true" -> "dormant": true
    # This handles LLMs outputting "key: value" with colon inside quotes
    # Also handles "key:=value" where colon+equals are inside the opening quote
    fixed = re.sub(r'"(\w+):="(\w+)"', r'"\1": "\2"', text)
    fixed = re.sub(
        r'"([^":]+):\s*(true|false|null|\d+|"[^"]*"|[a-zA-Z_][a-zA-Z0-9_]*)"',
        r'"\1": \2',
        fixed,
    )
    if fixed != text:
        text = fixed

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
