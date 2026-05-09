"""Dynamic seed generation for new-game flow."""

from __future__ import annotations

import logging
import uuid
from jinja2 import Environment
from pathlib import Path

import re

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.names import generate_name_pool
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.pack import Pack, PlayerOverrides, SeedEnvelope, parse_world_facts

_NAME_RE = re.compile(r"[^\x00-\x7F]")


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    result = _NAME_RE.sub("", text).strip()
    return result


def _sanitize_envelope(envelope: SeedEnvelope) -> SeedEnvelope:
    """Strip non-ASCII from all name fields as a safety net."""
    envelope.seed_state.pc.name = _strip_non_ascii(envelope.seed_state.pc.name)
    envelope.seed_state.location.name = _strip_non_ascii(envelope.seed_state.location.name)
    for item in envelope.seed_state.inventory:
        item.name = _strip_non_ascii(item.name)
    for quest in envelope.seed_state.quests:
        quest.title = _strip_non_ascii(quest.title)
        for obj in quest.objectives:
            obj.description = _strip_non_ascii(obj.description)
    envelope.seed_state.scene.tagline = _strip_non_ascii(envelope.seed_state.scene.tagline)
    for evt in envelope.seed_state.scene.world_state:
        envelope.seed_state.scene.world_state[envelope.seed_state.scene.world_state.index(evt)] = _strip_non_ascii(evt)
    for evt in envelope.seed_state.scene.recent_events:
        envelope.seed_state.scene.recent_events[envelope.seed_state.scene.recent_events.index(evt)] = _strip_non_ascii(evt)
    for npc in envelope.seed_state.scene.present_npcs:
        npc["name"] = _strip_non_ascii(npc["name"])
        npc["title"] = _strip_non_ascii(npc.get("title", ""))
        npc["bio"] = _strip_non_ascii(npc.get("bio", ""))
        npc["notes"] = _strip_non_ascii(npc.get("notes", ""))
    for npc_id, npc_data in envelope.seed_state.compendium.npcs.items():
        npc_data.name = _strip_non_ascii(npc_data.name)
        npc_data.title = _strip_non_ascii(npc_data.title or "")
        npc_data.bio = _strip_non_ascii(npc_data.bio or "")
    envelope.opening_narrative = _strip_non_ascii(envelope.opening_narrative)
    envelope.actions = [_strip_non_ascii(a) for a in envelope.actions]
    return envelope


_log = logging.getLogger("ccya.engine")


def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[dict[str, str]]:
    import random
    scenario = pack.scenario
    locales = scenario.name_locales if scenario else pack.manifest.name_locales
    name_pool = generate_name_pool(locales)
    # Randomize name_seed if not set
    name_seed = (scenario.name_seed if scenario and scenario.name_seed else 0) or random.randint(10_000_000, 99_999_999)
    ctx = {
        "scenario": scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count
        if (overrides and overrides.npc_count > 0)
        else 0,
        "name_pool": name_pool,
        "name_seed": name_seed,
        # Legacy fallbacks for old packs without scenario
        "world_text": pack.world_text,
        "style_text": pack.style_text,
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
    if pack.seed is not None and pack.scenario is None:
        raise ValueError("generate_seed() requires a generated pack (scenario.yaml), got static seed pack")

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    messages = _build_generate_seed_messages(env, pack, overrides)
    messages, _, _ = trim_messages(messages, config.prompt_token_budget)
    if config.log_prompts:
        _log_prompts(0, "generate_seed", messages)
    # Source world_facts from scenario (new) or fall back to manifest baseline_facts / world.md parsing (legacy)
    world_facts: list[str] = (
        list(pack.scenario.world_facts)
        if pack.scenario and pack.scenario.world_facts
        else list(pack.manifest.baseline_facts)
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
            envelope = _sanitize_envelope(envelope)
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
