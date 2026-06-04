"""Dynamic seed generation for new-game flow."""

from __future__ import annotations

import logging
import uuid
from typing import Any, cast
from hashlib import sha256
from jinja2 import Environment
from pathlib import Path

import re

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.names import generate_name_pool, generate_npc_names
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.models import WorldStateFact
from ccya.pack import Pack, PlayerOverrides, SeedEnvelope

from ccya.errors import ErrorKind, LlmcTimeout, LlmcError

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
    envelope.seed_state.scene.tagline = _strip_non_ascii(envelope.seed_state.scene.tagline)
    for evt in envelope.seed_state.scene.world_state:
        if isinstance(evt, str):
            envelope.seed_state.scene.world_state[envelope.seed_state.scene.world_state.index(evt)] = _strip_non_ascii(evt)
        elif isinstance(evt, dict):
            evt["text"] = _strip_non_ascii(evt.get("text", ""))
    for npc_id, npc_data in envelope.seed_state.compendium.npcs.items():
        if npc_data.name is not None:
            npc_data.name = _strip_non_ascii(npc_data.name)
            name_parts = npc_data.name.split()
            if len(name_parts) == 1 and name_parts[0]:
                surname_hash = sha256(f"{npc_data.name}-{npc_id}".encode()).hexdigest()[:4]
                surnames_pool = ["Smith", "Jones", "Black", "Stone", "Fox", "Wolf", "Hawk", "Knight"]
                npc_data.name = f'{name_parts[0]} {surnames_pool[int(surname_hash, 16) % len(surnames_pool)]}'
        npc_data.title = _strip_non_ascii(npc_data.title or "")
        npc_data.bio = _strip_non_ascii(npc_data.bio or "")

    envelope.actions = [_strip_non_ascii(a) for a in envelope.actions]
    return envelope


def _validate_seed_envelope(envelope: SeedEnvelope) -> None:
    """Raise ValueError if seed envelope violates hard constraints."""
    name_parts = envelope.seed_state.pc.name.strip().split()
    if len(name_parts) < 2:
        _log.warning(
            "PC name '%s' has only one part; seed will be used as-is",
            envelope.seed_state.pc.name,
        )





def _select_from_pool(pool_items: list[Any], seed: int, field_name: str) -> dict[str, Any]:
    """Select ONE entry from a pool using hash-based deterministic selection."""
    if not pool_items:
        raise ValueError(
            f"{field_name} pool is empty — pack must define at least one {field_name} "
            "entry for this genre"
        )

    idx = int(sha256(f"{seed}:{field_name}".encode()).hexdigest(), 16) % len(pool_items)
    selected = pool_items[idx]

    return cast(dict[str, Any], selected.model_dump())


def _build_synthesis_context(
    situation: dict[str, Any],
    arc: dict[str, Any],
    character_dynamic: dict[str, Any],
    moral_pressure: dict[str, Any],
    npc_bond: dict[str, Any] | None = None,
    scene_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a context dictionary with the six selected entries' ids and tags."""
    ctx: dict[str, Any] = {
        "situation": situation,
        "arc": arc,
        "character_dynamic": character_dynamic,
        "moral_pressure": moral_pressure,
    }
    if npc_bond:
        ctx["npc_bond"] = npc_bond
    if scene_bundle:
        ctx["scene_bundle"] = scene_bundle
    return ctx


def _preselect_pools(scenario: Any, name_seed: int) -> dict[str, Any]:
    """Pre-select from archetype pools deterministically per name_seed."""
    situation = _select_from_pool(
        scenario.situation_archetypes, name_seed, "situation_archetype"
    )
    arc = _select_from_pool(scenario.arc_categories, name_seed, "arc_category")
    character_dynamic = _select_from_pool(
        scenario.character_dynamics, name_seed, "character_dynamic"
    )
    moral_pressure = _select_from_pool(
        scenario.moral_pressures, name_seed, "moral_pressure"
    )

    npc_bond = _select_from_pool(
        scenario.npc_bonds, name_seed, "npc_bond"
    )
    scene_bundle = _select_from_pool(
        scenario.scene_detail_bundles, name_seed, "scene_detail_bundle"
    )

    return _build_synthesis_context(situation, arc, character_dynamic, moral_pressure, npc_bond, scene_bundle)


_log = logging.getLogger(__name__)


def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    import random
    scenario = pack.scenario
    locales = scenario.name_locales if scenario else pack.manifest.name_locales
    name_pool = generate_name_pool(locales)
    # Male-only name pool for historical combat genres via manifest config
    use_male = pack.manifest.use_male_only_names
    male_npc_pool = generate_npc_names(locales, count=10, gender="male") if use_male else None
    if male_npc_pool:
        # Replace the mixed npc and pc pools with male-only names
        name_pool = {
            "pc": male_npc_pool,
            "npc": male_npc_pool,
            "location": name_pool["location"],
            "inventory": name_pool["inventory"],
        }
    # Randomize name_seed if not set
    name_seed = (scenario.name_seed if scenario and scenario.name_seed else 0) or random.randint(10_000_000, 99_999_999)

    pool_selection: dict[str, Any] | None = None
    if scenario is not None:
        try:
            pool_selection = _preselect_pools(scenario, name_seed)
        except Exception as exc:
            _log.warning("pool pre-selection failed (continuing without pools): %s", exc)

    ctx = {
        "scenario": scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count
        if (overrides and overrides.npc_count > 0)
        else 0,
        "name_pool": name_pool,
        "name_seed": name_seed,
        "pool_selection": pool_selection,
    }
    system_text = _render(env, "generate_seed_system.j2", ctx)
    user_text = _render(env, "generate_seed_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ], pool_selection


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

    return warnings


async def generate_seed(
    pack: Pack,
    config: EngineConfig,
    *,
    overrides: PlayerOverrides | None = None,
    seed: int | None = None,
    template_dir: str | None = None,
) -> tuple[SeedEnvelope, dict[str, Any] | None]:
    if pack.seed is not None and pack.scenario is None:
        raise ValueError("generate_seed() requires a generated pack (scenario.yaml), got static seed pack")

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    _log.debug(
        "generate_seed start pack=%s timeout=%s overrides=%s",
        pack.manifest.id, config.request_timeout_s,
        overrides.model_dump() if overrides else "none",
        extra={"trace_id": trace_id},
    )

    messages, pool_selection = _build_generate_seed_messages(env, pack, overrides)
    messages, _, _ = trim_messages(messages, config.context_window)

    if config.log_prompts:
        _log_prompts(0, "generate_seed", messages)

    for attempt in range(1 + config.max_llm_retries):
        # Source world_facts from scenario (new) or fall back to manifest baseline_facts / world.md parsing (legacy)

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
                top_p=config.generate_seed_top_p,
                timeout=float(config.request_timeout_s),
            )
        except LlmcTimeout:
            _log.error(
                "generate_seed: LLM timeout",
                extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
            )
            raise
        except LlmcError as exc:
            _log.error(
                "generate_seed: LLM error: %s",
                exc,
                extra={"error_kind": exc.kind, "trace_id": trace_id},
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
            if attempt < config.max_llm_retries:
                fb = f"Your output failed to parse: {parse_error}. Common issues: actions must be exactly 4 items; opening_narrative must be at least 50 characters. Re-emit a valid SeedEnvelope JSON only."
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
            _validate_seed_envelope(envelope)
        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "generate_seed validation failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_llm_retries:
                fb = (
                    f"SeedEnvelope validation failed: {parse_error[:300]}. "
                    "Check field types, required fields, and array length constraints. "
                    "Re-emit corrected JSON matching the schema."
                )
                messages.append({"role": "user", "content": fb})
            continue

        # Copy arc from envelope top-level into seed_state; enforce hard limits on active threads and urgency
        if envelope.arc:
            envelope.seed_state.arc = envelope.arc
            arc = envelope.seed_state.arc
            if arc and hasattr(arc, "threads"):
                active_threads = [t for t in (arc.threads or []) if getattr(t, "active", True)]
                non_active_threads = [t for t in (arc.threads or []) if not getattr(t, "active", False)]

                # Hard limit: at most 2 threads can be active at game start
                max_active = min(2, len(active_threads)) if active_threads else 0
                excess_active = active_threads[max_active:]

                for t in excess_active:
                    object.__setattr__(t, "active", False)
                    object.__setattr__(t, "urgency", "background")

                # Force all non-active threads to background/normal urgency (never urgent)
                for t in non_active_threads + excess_active:
                    current_urgency = getattr(t, "urgency", "normal") or "normal"
                    if current_urgency == "urgent":
                        object.__setattr__(t, "urgency", "background")

                _log.info(
                    "enforce_thread_limits active=%d non_active=%d excess_capped=%d pack=%s",
                    max_active, len(non_active_threads), len(excess_active),
                    pack.manifest.id,
                    extra={"trace_id": trace_id},
                )

        # Inject baseline_facts (hardcoded genre canon) into world_state
        # LLM generates 3 global facts into world_state; prepend baseline_facts
        if (scenario := pack.scenario) and scenario.world_facts:
            existing_ws = list(envelope.seed_state.scene.world_state)

            def _normalize_for_match(text: str) -> str:
                return _strip_non_ascii(text).strip().rstrip(".")

            baseline_texts_set = {_normalize_for_match(t) for t in scenario.world_facts}
            baseline_ws = [WorldStateFact(id=f"baseline_{i}", text=text, tier="permanent") for i, text in enumerate(scenario.world_facts)]
            merged_ws = cast(
                list[WorldStateFact | str],
                baseline_ws + [f for f in existing_ws if _normalize_for_match(f.text if isinstance(f, WorldStateFact) else f) not in baseline_texts_set],
            )
            envelope.seed_state.scene.world_state = merged_ws

        # Keep seeded compendium NPCs; clear engine-managed touch_order
        if "compendium_touch_order" in envelope.seed_state.meta:
            del envelope.seed_state.meta["compendium_touch_order"]

        soft_warnings = _soft_validate_seed(envelope, pack, overrides)
        for w in soft_warnings:
            _log.warning(
                "generate_seed soft-check: %s", w, extra={"trace_id": trace_id}
            )

        opening_len = len(envelope.opening_narrative) if envelope.opening_narrative else 0
        _log.info(
            "generate_seed complete opening_len=%d pack=%s pool_selection=%s",
            opening_len, pack.manifest.id, bool(pool_selection),
            extra={"trace_id": trace_id},
        )
        return envelope, pool_selection

    raise RuntimeError(
        f"generate_seed failed after {1 + config.max_llm_retries} attempts — trace {trace_id}"
    )
