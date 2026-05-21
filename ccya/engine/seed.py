"""Dynamic seed generation for new-game flow."""

from __future__ import annotations

import logging
import uuid
from typing import Any
from hashlib import sha256
from jinja2 import Environment
from pathlib import Path

import re

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _log_llm_io, _log_prompts, _render
from ccya.engine.names import generate_name_pool, generate_npc_names
from ccya.llm_client import chat as llm_chat, strip_thinking, trim_messages
from ccya.pack import Pack, PlayerOverrides, PoolEntry, SeedEnvelope, parse_world_facts

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
        envelope.seed_state.scene.world_state[envelope.seed_state.scene.world_state.index(evt)] = _strip_non_ascii(evt)
    for evt in envelope.seed_state.scene.recent_events:
        envelope.seed_state.scene.recent_events[envelope.seed_state.scene.recent_events.index(evt)] = _strip_non_ascii(evt)
    for npc in envelope.seed_state.scene.present_npcs:
        npc["name"] = _strip_non_ascii(npc["name"])
        npc["title"] = _strip_non_ascii(npc.get("title", ""))
        npc["bio"] = _strip_non_ascii(npc.get("bio", ""))
        npc["notes"] = _strip_non_ascii(npc.get("notes", ""))
    for npc_id, npc_data in envelope.seed_state.compendium.npcs.items():
        if npc_data.name is not None:
            npc_data.name = _strip_non_ascii(npc_data.name)
        npc_data.title = _strip_non_ascii(npc_data.title or "")
        npc_data.bio = _strip_non_ascii(npc_data.bio or "")
    envelope.opening_narrative = _strip_non_ascii(envelope.opening_narrative)
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




# Genre tag whitelists for sanity validation. Each key maps to a set of allowed
# substrings; an entry passes if ANY of its tags contains at least one substring.
_GENRE_TAG_WHITELIST: dict[str, list[str]] = {
    "zombie": ["community", "leadership", "responsibility", "marginalized", "independent",
               "distrustful", "ambitious", "disruptive", "emerging_power", "fallen_status",
               "redemption_needed", "outcast", "hunted", "isolated", "connected", "secretive",
               "leverage_holding", "former_status", "loss_of_power", "adaptation_needed",
               "infrastructure", "social", "supply", "faction", "discovery", "moral",
               "survival", "community_fracture", "sabotage", "rationing", "power_struggle",
               "resource_scarcity", "collapse_conspiracy", "quarantine", "territory",
               "outside_threat", "cult", "information_warfare", "infection_evolution",
               "settlement_politics", "supply_route", "moral_decay", "defection",
               "survival_vs_humanity", "protect_the_vulnerable", "resource_allocation",
               "truth_control", "leadership_burden", "trust_dynamics"],
    "pirate": ["crew_loyalty", "working_class", "ship_identity", "ambitious", "dissident",
               "leadership_challenge", "forced_into_pirate_life", "conflicted", "inexperienced",
               "experienced", "hardened", "respected_by_crew", "independent", "unaligned",
               "self_reliant", "mutiny", "naval", "port", "cargo", "disease", "storm",
               "treasure", "crew_conflict", "blockade", "strike", "sabotage", "heist",
               "leadership_legitimacy", "faction_power_struggle", "territorial_control",
               "mutiny_escalation", "outside_betrayal", "colonial_conspiracy", "ship_rivalry",
               "pardon_scheme", "disease_quarantine", "storm_wreckage", "crew_defection",
               "slave_trade", "loyalty_vs_self_preservation", "code_of_honor",
               "power_concentration", "freedom_vs_discipline", "legitimate_governance"],
    "noir": ["institutional_access", "insider_knowledge", "system_participant",
             "external_perspective", "limited_resources", "outside_looking_in",
             "ethical_corruption", "moral_erosion", "murder", "kidnapping", "gang_war",
             "corruption", "witness_protection", "heist", "blackmail", "political_scandal",
             "media_manipulation", "judicial_rigging", "organized_crime", "institutional_corruption",
             "gang_territory_dispute", "underworld_betrayal", "evidence_tampering",
             "political_shakedown", "union_infiltration", "police_compromise",
             "witness_intimidation", "truth_vs_self_preservation", "collateral_damage",
             "evidence_vs_justice", "professional_ethics", "ends_vs_means",
             "trauma", "cooperation", "vulnerability"],
}


def _select_from_pool(pool_items: list[PoolEntry], seed: int, field_name: str) -> dict[str, Any]:
    """Select ONE entry from a pool using hash-based deterministic selection."""
    if not pool_items:
        raise ValueError(
            f"{field_name} pool is empty — pack must define at least one {field_name} "
            "entry for this genre"
        )

    idx = int(sha256(f"{seed}:{field_name}".encode()).hexdigest(), 16) % len(pool_items)
    selected = pool_items[idx]

    return selected.model_dump()


def _validate_genre_sanity(selected: dict[str, Any], genre: str) -> bool:
    """Validate that no selected entry has tags outside expected genre vocabulary."""
    allowed = _GENRE_TAG_WHITELIST.get(genre, [])
    if not allowed:
        return True

    tag = selected.get("id", "") + " " + " ".join(selected.get("tags", []))
    for substring in allowed:
        if substring.lower() in tag.lower():
            return True

    _log.warning(
        "Genre sanity check failed — entry has no matching genre tags. id=%s tags=%s genre=%s",
        selected.get("id"),
        selected.get("tags"),
        genre,
    )
    return False


def _build_synthesis_context(
    situation: dict[str, Any],
    arc: dict[str, Any],
    character_dynamic: dict[str, Any],
    moral_pressure: dict[str, Any],
) -> dict[str, Any]:
    """Build a context dictionary with the four selected entries' ids and tags."""
    return {
        "situation": situation,
        "arc": arc,
        "character_dynamic": character_dynamic,
        "moral_pressure": moral_pressure,
    }


def _normalize_genre_key(genre: str) -> str:
    """Map pack genre strings to whitelist keys."""
    if "zombie" in genre or "post-apocalyptic" in genre or "apocalypse" in genre:
        return "zombie"
    if "pirate" in genre or "naval" in genre:
        return "pirate"
    if "noir" in genre or "detective" in genre or "1930s" in genre:
        return "noir"
    return genre


def _preselect_pools(scenario: Any, name_seed: int, genre_str: str) -> dict[str, Any]:
    """Pre-select from archetype pools deterministically per name_seed."""
    raw_genre = (genre_str or "").lower()
    genre = _normalize_genre_key(raw_genre)

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

    all_selected = [situation, arc, character_dynamic, moral_pressure]
    field_names = ["situation", "arc", "character_dynamic", "moral_pressure"]

    for selected, fname in zip(all_selected, field_names):
        if not _validate_genre_sanity(selected, genre):
            pool_map = {
                "situation": scenario.situation_archetypes,
                "arc": scenario.arc_categories,
                "character_dynamic": scenario.character_dynamics,
                "moral_pressure": scenario.moral_pressures,
            }
            pool_items = pool_map[fname]
            for salt in (1, 2, 3):
                alt_idx = int(sha256(f"{name_seed + salt}:{fname}".encode()).hexdigest(), 16) % len(pool_items) if pool_items else -1
                if alt_idx < 0:
                    break
                alt_selected = pool_items[alt_idx].model_dump()
                if _validate_genre_sanity(alt_selected, genre):
                    all_selected[field_names.index(fname)] = alt_selected
                    selected = alt_selected
                    break

    return _build_synthesis_context(*all_selected)


_log = logging.getLogger(__name__)


def _build_generate_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> list[dict[str, str]]:
    import random
    scenario = pack.scenario
    locales = scenario.name_locales if scenario else pack.manifest.name_locales
    name_pool = generate_name_pool(locales)
    # Historical combat genres: male-only name pool for initial NPCs
    _HISTORICAL_COMBAT = {"ww2", "noir", "pirate", "sengoku japan"}
    genre = (pack.manifest.genre or "").lower()
    male_npc_pool = generate_npc_names(locales, count=10, gender="male") if genre in _HISTORICAL_COMBAT else None
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
            pool_selection = _preselect_pools(scenario, name_seed, genre)
        except Exception as exc:
            _log.warning("pool pre-selection failed (continuing without pools): %s", exc)

    ctx = {
        "scenario": scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count
        if (overrides and overrides.npc_count > 0)
        else 0,
        "min_named_npcs": (
            scenario.constraints.min_named_npcs
            if scenario and scenario.constraints
            else 2
        ),
        "name_pool": name_pool,
        "male_npc_pool": male_npc_pool,
        "name_seed": name_seed,
        # Pool selection (pre-selected archetype entries for synthesis guidance)
        "pool_selection": pool_selection,
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
            _validate_seed_envelope(envelope)
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

        # Copy arc from envelope top-level into seed_state; wire pc_drive into arc
        if envelope.arc:
            envelope.seed_state.arc = envelope.arc
            if envelope.pc_drive:
                envelope.seed_state.arc.pc_drive = envelope.pc_drive
            # Ensure seeded active threads start with correct state
            arc = envelope.seed_state.arc
            if arc and hasattr(arc, "threads"):
                for t in arc.threads or []:
                    if not getattr(t, "active", True):
                        object.__setattr__(t, "active", True)
        if envelope.pc_drive:
            envelope.seed_state.pc.drive = envelope.pc_drive

        # Inject baseline_facts (hardcoded genre canon) into world_state
        # LLM generates 3 global facts into world_state; prepend baseline_facts
        if world_facts:
            existing_ws = list(envelope.seed_state.scene.world_state)
            merged_ws = world_facts + [f for f in existing_ws if f not in world_facts]
            envelope.seed_state.scene.world_state = merged_ws

        # Preserve compendium NPCs generated by the seed LLM; clear touch order
        if "compendium_touch_order" in envelope.seed_state.meta:
            del envelope.seed_state.meta["compendium_touch_order"]

        soft_warnings = _soft_validate_seed(envelope, pack, overrides)
        for w in soft_warnings:
            _log.warning(
                "generate_seed soft-check: %s", w, extra={"trace_id": trace_id}
            )

        return envelope

    raise RuntimeError(
        f"generate_seed failed after {1 + config.generate_seed_max_retries} attempts — trace {trace_id}"
    )
