"""Dynamic seed generation for new-game flow."""

from __future__ import annotations

import logging
import uuid
from jinja2 import Environment
from pathlib import Path

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.names import generate_name_pool
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.pack import Pack, PlayerOverrides, SeedEnvelope, parse_world_facts

_log = logging.getLogger("ccya.engine")


def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[dict[str, str]]:
    name_pool = generate_name_pool(pack.manifest.name_locales)
    ctx = {
        "world_text": pack.world_text,
        "style_text": pack.style_text,
        "scenario": pack.scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count
        if (overrides and overrides.npc_count > 0)
        else 0,
        "name_pool": name_pool,
    }
    system_text = _render(env, "generate_seed_system.j2", ctx)
    user_text = _render(env, "generate_seed_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _soft_validate_seed(
    envelope: SeedEnvelope,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[str]:
    warnings: list[str] = []
    c = pack.scenario.constraints if pack.scenario else None
    if not c:
        return warnings

    words = len(envelope.opening_narrative.split())
    lo, hi = c.prose_word_range
    if not (lo <= words <= hi):
        warnings.append(f"Opening narrative {words} words (expected {lo}-{hi})")

    text_lower = envelope.opening_narrative.lower()
    for cliche in c.forbid_cliches:
        if cliche.lower() in text_lower:
            warnings.append(f"Opening narrative contains forbidden cliché: '{cliche}'")

    if c.forbid_player_dependents:
        dependent_words = {
            "wife",
            "husband",
            "spouse",
            "child",
            "kids",
            "son",
            "daughter",
        }
        if any(word in text_lower for word in dependent_words):
            warnings.append(
                "Opening narrative may contain player-dependent relationships"
            )

    return warnings


async def generate_seed(
    pack: Pack,
    config: EngineConfig,
    *,
    overrides: PlayerOverrides | None = None,
    seed: int | None = None,
    template_dir: str | None = None,
) -> SeedEnvelope:
    if pack.manifest.mode != "dynamic":
        raise ValueError(
            f"generate_seed() requires a dynamic pack, got mode={pack.manifest.mode!r}"
        )

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    messages = _build_generate_seed_messages(env, pack, overrides)
    messages = trim_messages(messages, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(0, "generate_seed", messages)
    # Prefer hand-curated baseline_facts on the manifest; fall back to parsing
    # world.md prose (legacy behavior) for packs that haven't been migrated.
    world_facts: list[str] = (
        list(pack.manifest.baseline_facts)
        if pack.manifest.baseline_facts
        else parse_world_facts(pack.world_text)
    )

    for attempt in range(1 + config.generate_seed_max_retries):
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_seed_request_attempt_{attempt}",
                messages=messages,
                max_chars=config.log_llm_io_max_chars,
            )
        try:
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                temperature=config.generate_seed_temperature,
                timeout=float(config.request_timeout_s),
            )
        except Exception as exc:
            _log.error(
                "generate_seed: LLM error: %s",
                exc,
                extra={"trace_id": trace_id},
            )
            raise
        raw = result.get("response", "") if isinstance(result, dict) else ""
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase=f"generate_seed_response_attempt_{attempt}",
                response=raw,
                max_chars=config.log_llm_io_max_chars,
            )

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in generate_seed response"
            _log.warning(
                "generate_seed failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.generate_seed_max_retries:
                fb = f"Your output failed to parse: {parse_error}. Re-emit a valid SeedEnvelope JSON only."
                messages.append({"role": "user", "content": fb})
            continue

        try:
            # Unwrap if nested under "seed_state" key (expected); also accept bare SeedState
            if "seed_state" not in j and "pc" in j:
                j = {
                    "seed_state": j,
                    "opening_narrative": j.pop("opening_narrative", "."),
                }
            envelope = SeedEnvelope(**j)
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "generate_seed validation failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.generate_seed_max_retries:
                fb = (
                    f"SeedEnvelope validation failed: {parse_error[:300]}. "
                    "Re-emit corrected JSON matching the schema."
                )
                messages.append({"role": "user", "content": fb})
            continue

        # Inject baseline_facts (hardcoded genre canon) into world_state
        # LLM generates 3 global facts into world_state; prepend baseline_facts
        if world_facts:
            existing_ws = list(envelope.seed_state.scene.world_state)
            merged_ws = world_facts + [f for f in existing_ws if f not in world_facts]
            envelope.seed_state.scene.world_state = merged_ws

        # Preserve compendium NPCs generated by the seed LLM; clear touch order
        if "compendium_touch_order" in envelope.seed_state.meta:
            del envelope.seed_state.meta["compendium_touch_order"]

        # Phase 5: seed world factions and locations
        seed_val = seed or hash(envelope.seed_state.meta.get("game_name", ""))
        envelope.seed_state.meta["faction_pool_seed"] = seed_val
        envelope.seed_state.meta["location_pool_seed"] = seed_val + 1

        soft_warnings = _soft_validate_seed(envelope, pack, overrides)
        for w in soft_warnings:
            _log.warning(
                "generate_seed soft-check: %s", w, extra={"trace_id": trace_id}
            )

        return envelope

    raise RuntimeError(
        f"generate_seed failed after {1 + config.generate_seed_max_retries} attempts — trace {trace_id}"
    )
