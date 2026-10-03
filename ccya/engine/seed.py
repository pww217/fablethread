"""Dynamic seed generation for new-game flow."""

from __future__ import annotations

import logging
import uuid
from typing import Any, cast
from hashlib import sha256
from jinja2 import Environment
from pathlib import Path

import re

from ccya.engine.config import EngineConfig, _build_jinja_env, _find_json, _render
from ccya.engine.names import generate_name_pool, generate_npc_names
from ccya.engine.npc_roster import generate_npc_color, generate_pc_color, generate_item_color
from ccya.llm_client import chat_with_config as llm_chat, strip_thinking, trim_messages
from ccya.models import InventoryItem, WorldStateFact
from ccya.pack import Pack, PlayerOverrides, SeedStateEnvelope, SeedState

from ccya.errors import ErrorKind, LlmcTimeout, LlmcError

_NPC_PALETTE = [
    "#e06c75", "#c67b40", "#e5c07b", "#7eb8da",
    "#56b6c2", "#61afef", "#bb85f0", "#be5046",
    "#d19a66", "#7eb8da", "#528bff", "#c678dd",
]

_NAME_RE = re.compile(r"[^\x00-\x7F]")


def _strip_non_ascii(text: str) -> str:
    if not text:
        return text
    result = _NAME_RE.sub("", text).strip()
    return result


def _replace_names_with_pool(seed_state: SeedState, pool: dict[str, list[str]]) -> SeedState:
    """Replace LLM-generated names with names from the pool."""
    import random
    pc_names = pool.get("pc", [])
    npc_names = pool.get("npc", [])
    if pc_names and seed_state.pc.name:
        seed_state.pc.name = random.choice(pc_names)
    for npc_id, npc_data in seed_state.compendium.npcs.items():
        if npc_data.name and npc_names:
            npc_data.name = random.choice(npc_names)
    return seed_state


def _sanitize_seed_state(seed_state: SeedState, pool: dict[str, list[str]] | None = None) -> SeedState:
    """Strip non-ASCII from all name fields as a safety net."""
    # Replace names with pool names if pool is provided
    if pool is not None:
        seed_state = _replace_names_with_pool(seed_state, pool)
    seed_state.pc.name = _strip_non_ascii(seed_state.pc.name)
    seed_state.location.name = _strip_non_ascii(seed_state.location.name)
    for item in seed_state.inventory:
        item.name = _strip_non_ascii(item.name)
    seed_state.meta["session_name"] = _strip_non_ascii(
        seed_state.meta.get("session_name", "")
    )
    # Strip rogue prose fields from pc.situation. prepare_seed LLM sometimes
    # emits 'opening' / 'description' / 'narrative' despite the prompt saying
    # not to. These belong to narrate_seed, not prepare_seed — drop them so
    # the wasted tokens never enter the seed state.
    seed_state.pc.situation = {
        k: v
        for k, v in seed_state.pc.situation.items()
        if k not in {"opening", "description", "narrative"}
    }
    for evt in seed_state.scene.world_state:
        if isinstance(evt, str):
            seed_state.scene.world_state[seed_state.scene.world_state.index(evt)] = _strip_non_ascii(evt)
        elif isinstance(evt, dict):
            evt["text"] = _strip_non_ascii(evt.get("text", ""))
    for npc_id, npc_data in seed_state.compendium.npcs.items():
        if npc_data.name is not None:
            npc_data.name = _strip_non_ascii(npc_data.name)
        npc_data.title = _strip_non_ascii(npc_data.title or "")
        npc_data.bio = _strip_non_ascii(npc_data.bio or "")
        if npc_data.presence is None or npc_data.presence == "":
            npc_data.presence = "present"
        if not npc_data.color:
            npc_data.color = generate_npc_color(npc_id)

    if not seed_state.pc.color:
        seed_state.pc.color = generate_pc_color()

    for item in seed_state.inventory:
        if not item.color:
            item.color = generate_item_color(item.id)

    # Safety net: ensure at least 1 NPC has presence="present"
    has_present = any(
        npc.presence == "present"
        for npc in seed_state.compendium.npcs.values()
    )
    if not has_present and seed_state.compendium.npcs:
        first_npc = next(iter(seed_state.compendium.npcs.values()))
        first_npc.presence = "present"

    # Safety net: coerce null lists to empty lists (LLM sometimes emits null)
    if seed_state.long_term_objective is not None:
        if seed_state.long_term_objective.completed_threads is None:
            seed_state.long_term_objective.completed_threads = []
        if seed_state.long_term_objective.threads is None:
            seed_state.long_term_objective.threads = []

    return seed_state


def _validate_seed_state(seed_state: SeedState) -> None:
    """Raise ValueError if seed state violates hard constraints."""
    name_parts = seed_state.pc.name.strip().split()
    if len(name_parts) < 2:
        _log.warning(
            "PC name '%s' has only one part; seed will be used as-is",
            seed_state.pc.name,
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
    npc_tie: dict[str, Any] | None = None,
    scene_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a context dictionary with the selected entries' ids and tags."""
    ctx: dict[str, Any] = {
        "situation": situation,
        "arc": arc,
        "character_dynamic": character_dynamic,
    }
    if npc_tie:
        ctx["npc_tie"] = npc_tie
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

    npc_tie = _select_from_pool(
        scenario.npc_bonds, name_seed, "npc_tie"
    )
    scene_bundle = _select_from_pool(
        scenario.scene_detail_bundles, name_seed, "scene_detail_bundle"
    )

    return _build_synthesis_context(situation, arc, character_dynamic, npc_tie, scene_bundle)


_log = logging.getLogger(__name__)


def _build_prepare_seed_messages(
    env: Environment,
    pack: Pack,
    overrides: PlayerOverrides | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any] | None, dict[str, list[str]]]:
    import random
    scenario = pack.scenario
    locales = scenario.name_locales if scenario else pack.manifest.name_locales
    name_pool = generate_name_pool(locales)
    # Male-only name pool for historical combat genres via manifest config
    use_male = pack.manifest.use_male_only_names
    if use_male:
        # 40 male names for male-only genres
        male_npc_pool = generate_npc_names(locales, count=40, gender="male")
        name_pool = {
            "pc": male_npc_pool,
            "npc": male_npc_pool,
            "location": name_pool["location"],
            "inventory": name_pool["inventory"],
        }
    else:
        # 20 male + 20 female for mixed genres
        male_pool = generate_npc_names(locales, count=20, gender="male")
        female_pool = generate_npc_names(locales, count=20, gender="female")
        mixed_pool = male_pool + female_pool
        name_pool = {
            "pc": mixed_pool,
            "npc": mixed_pool,
            "location": name_pool["location"],
            "inventory": name_pool["inventory"],
        }
    # Randomize name_seed if not set
    name_seed = scenario.name_seed if scenario and scenario.name_seed is not None else random.randint(10_000_000, 99_999_999)

    pool_selection: dict[str, Any] | None = None
    if scenario is not None:
        try:
            pool_selection = _preselect_pools(scenario, name_seed)
        except Exception as exc:
            _log.warning("pool pre-selection failed (continuing without pools): %s", exc)

    ctx = {
        "scenario": scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "name_pool": name_pool,
        "name_seed": name_seed,
        "pool_selection": pool_selection,
    }
    system_text = _render(env, "prepare_seed_system.j2", ctx)
    user_text = _render(env, "prepare_seed_user.j2", ctx)
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ], pool_selection, name_pool


async def prepare_seed(
    pack: Pack,
    config: EngineConfig,
    *,
    overrides: PlayerOverrides | None = None,
    seed: int | None = None,
    template_dir: str | None = None,
) -> tuple[SeedStateEnvelope, dict[str, Any] | None]:
    if pack.scenario is None:
        raise ValueError("prepare_seed() requires a scenario.yaml pack")

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    _log.debug(
        "prepare_seed start pack=%s timeout=%s overrides=%s",
        pack.manifest.id, config.request_timeout_s,
        overrides.model_dump() if overrides else "none",
        extra={"trace_id": trace_id},
    )

    messages, pool_selection, name_pool = _build_prepare_seed_messages(env, pack, overrides)
    messages, _, _ = trim_messages(messages, config.context_window)

    for attempt in range(1 + config.max_llm_retries):
        # Source world_facts from scenario (new) or fall back to manifest baseline_facts / world.md parsing (legacy)

        try:
            result = await llm_chat(
                config,
                messages,
                temperature=config.prepare_seed_temperature,
                top_p=config.prepare_seed_top_p,
                timeout=float(config.request_timeout_s),
                num_ctx=config.num_ctx,
                enable_thinking=False,
                reasoning_effort="none",
                thinking_budget=0,
            )
        except LlmcTimeout:
            _log.error(
                "prepare_seed: LLM timeout",
                extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
            )
            raise
        except LlmcError as exc:
            _log.error(
                "prepare_seed: LLM error: %s",
                exc,
                extra={"error_kind": exc.kind, "trace_id": trace_id},
            )
            raise
        raw = result.content

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in prepare_seed response"
            _log.warning(
                "prepare_seed failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            # Save full response to file for debugging
            failed_dir = Path("saves") / "prepare_seed_failures"
            failed_dir.mkdir(parents=True, exist_ok=True)
            failed_file = failed_dir / f"{trace_id}_attempt{attempt + 1}.txt"
            failed_file.write_text(raw)
            _log.warning(
                "prepare_seed failed (attempt %d): %s — full response saved to %s",
                attempt + 1,
                parse_error,
                failed_file,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_llm_retries:
                fb = f"Your output failed to parse: {parse_error}. Re-emit a valid SeedState JSON only."
                messages.append({"role": "user", "content": fb})
            continue

        try:
            # Unwrap if nested under "seed_state" key (expected); also accept bare SeedState
            if "seed_state" not in j and "pc" in j:
                j = {"seed_state": j}

            # Pre-sanitize: coerce null lists to empty lists before Pydantic validation
            ss = j.get("seed_state", j)
            # Backward compat: old prompts used "arc" key; new ones use "long_term_objective"
            arc = ss.get("arc") or ss.get("long_term_objective")
            if arc is not None:
                if isinstance(arc, dict):
                    if arc.get("completed_threads") is None:
                        arc["completed_threads"] = []
                    if arc.get("threads") is None:
                        arc["threads"] = []

            state_envelope = SeedStateEnvelope(**j)
            state_envelope.seed_state = _sanitize_seed_state(state_envelope.seed_state, name_pool)
            _validate_seed_state(state_envelope.seed_state)

        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "prepare_seed validation failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_llm_retries:
                fb = (
                    f"SeedState validation failed: {parse_error[:300]}. "
                    "Check field types, required fields, and array length constraints. "
                    "Re-emit corrected JSON matching the schema."
                )
                messages.append({"role": "user", "content": fb})
            continue

        # Enforce hard limits on non-dormant threads and urgency (reads from seed_state.long_term_objective directly)
        arc = state_envelope.seed_state.long_term_objective
        if arc:
             # Set started_turn to the first player turn (always 1)
            if getattr(arc, "started_turn") is None:
                object.__setattr__(arc, "started_turn", 1)
            # Enforce hard limits on non-dormant threads and urgency
            non_dormant_threads = [t for t in (arc.threads or []) if not t.dormant]
            dormant_threads = [t for t in (arc.threads or []) if t.dormant]

            # Hard limit: at most 2 threads can be non-dormant at game start
            max_non_dormant = min(2, len(non_dormant_threads)) if non_dormant_threads else 0
            excess_non_dormant = non_dormant_threads[max_non_dormant:]

            for t in excess_non_dormant:
                object.__setattr__(t, "dormant", True)
                object.__setattr__(t, "urgency", "background")
                # Ensure urgency_set_turn is set so urgency decay can track this thread's age
                if getattr(t, "urgency_set_turn") is None:
                    object.__setattr__(t, "urgency_set_turn", 0)
                if getattr(t, "added_turn") is None:
                    object.__setattr__(t, "added_turn", 0)

            # Force all dormant threads to background urgency (never urgent)
            for t in dormant_threads + excess_non_dormant:
                current_urgency = getattr(t, "urgency", "normal") or "normal"
                if current_urgency == "urgent":
                    object.__setattr__(t, "urgency", "background")
                # Ensure turn tracking is set so decay/expiration passes can age this thread correctly
                if getattr(t, "urgency_set_turn") is None:
                    object.__setattr__(t, "urgency_set_turn", 0)
                if getattr(t, "added_turn") is None:
                    object.__setattr__(t, "added_turn", 0)

            _log.info(
                "enforce_thread_limits non_dormant=%d dormant=%d excess_capped=%d pack=%s",
                max_non_dormant, len(dormant_threads), len(excess_non_dormant),
                pack.manifest.id,
                extra={"trace_id": trace_id},
            )

        # Inject baseline_facts (hardcoded genre canon) into world_state
        # LLM generates 3 global facts into world_state; prepend baseline_facts
        if (scenario := pack.scenario) and scenario.world_facts:
            existing_ws = list(state_envelope.seed_state.scene.world_state)

            def _normalize_for_match(text: str) -> str:
                return _strip_non_ascii(text).strip().rstrip(".")

            baseline_texts_set = {_normalize_for_match(t) for t in scenario.world_facts}
            baseline_ws = [WorldStateFact(id=f"baseline_{i}", text=text, tier="global", permanent=True) for i, text in enumerate(scenario.world_facts)]
            merged_ws = cast(
                list[WorldStateFact | str],
                baseline_ws + [f for f in existing_ws if _normalize_for_match(f.text if isinstance(f, WorldStateFact) else f) not in baseline_texts_set],
            )
            state_envelope.seed_state.scene.world_state = merged_ws

        # Keep seeded compendium NPCs; clear engine-managed touch_order
        if "compendium_touch_order" in state_envelope.seed_state.meta:
            del state_envelope.seed_state.meta["compendium_touch_order"]

        # Inject pack currency into initial inventory
        if (scenario := pack.scenario) and scenario.currency_id and scenario.starting_currency_amount > 0:
            currency_ids = {item.id for item in state_envelope.seed_state.inventory}
            if scenario.currency_id not in currency_ids:
                state_envelope.seed_state.inventory.append(
                    InventoryItem(
                        id=scenario.currency_id,
                        name=scenario.currency_id.title(),
                        amount=scenario.starting_currency_amount,
                        notes="",
                    )
                )

        state_envelope.seed_state.meta["_seed_soft_warnings"] = []
        # Hard validation: at least 1 NPC must have presence="present"
        present_count = sum(
            1 for npc in state_envelope.seed_state.compendium.npcs.values()
            if npc.presence == "present"
        )
        _log.info(
            "prepare_seed NPC check pack=%s total_npcs=%d present_count=%d compendium_keys=%s",
            pack.manifest.id,
            len(state_envelope.seed_state.compendium.npcs),
            present_count,
            list(state_envelope.seed_state.compendium.npcs.keys())[:5],
            extra={"trace_id": trace_id},
        )
        if present_count == 0:
            # Safety net: force first NPC to present if compendium is non-empty
            if state_envelope.seed_state.compendium.npcs:
                first_npc = next(iter(state_envelope.seed_state.compendium.npcs.values()))
                first_npc.presence = "present"
                present_count = 1
                _log.info(
                    "prepare_seed forced first NPC to present (compendium had %d NPCs)",
                    len(state_envelope.seed_state.compendium.npcs),
                    extra={"trace_id": trace_id},
                )
            else:
                # Compendium is empty — raise to trigger retry
                if attempt < config.max_llm_retries:
                    fb = (
                        "SeedState validation failed: Seed must include at least 1 NPC with presence='present' in opening scene. "
                        "The compendium was empty — you must include at least one NPC in the opening scene. "
                        "Re-emit corrected JSON matching the schema."
                    )
                    messages.append({"role": "user", "content": fb})
                raise ValueError(
                    "Seed must include at least 1 NPC with presence='present' in opening scene"
                )

        # Engine-set metadata: these must come from config, not LLM output
        seed_meta = state_envelope.seed_state.meta
        seed_meta["model"] = config.model
        seed_meta.setdefault("pack_source", pack.manifest.id)
        seed_meta.setdefault("setting_pack", pack.manifest.id)
        seed_meta["turn"] = 0
        _log.info(
            "prepare_seed complete pack=%s pool_selection=%s",
            pack.manifest.id, bool(pool_selection),
            extra={"trace_id": trace_id},
        )
        return state_envelope, pool_selection

    raise RuntimeError(
        f"prepare_seed failed after {1 + config.max_llm_retries} attempts — trace {trace_id}"
    )


def _build_narrate_seed_messages(
    env: Environment,
    seed_state: SeedState,
    pool_selection: dict[str, Any] | None = None,
    pack: Pack | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Build prompt for narrate_seed from filtered SeedState context.
    
    Context passed to template (focused on what player needs at turn 0):
    - pc.name, pc.tagline, pc.situation (NOT bio, stats, conditions — shown in UI)
    - location.name only (no description — narration derives scene from situation)
    - arc_origin (world-level context)
    - arc.objective (the goal)
    - Present NPCs only (bio for context)
    - setting_info (genre, universe rules, creative direction)
    
    NOT passed: world_state, meta, world.locations, full inventory, known NPCs, location.description, scene bundles
    """
    pc = seed_state.pc
    location = seed_state.location
    
    # Extract setting info from pack for prompt grounding
    setting_info = None
    if pack and pack.scenario:
        setting_info = {
            "genre": pack.manifest.name,
            "universe_rules": pack.scenario.world_rules,
            "creative_direction": pack.scenario.inspiration,
        }
    
    # Extract compendium NPCs — only present ones for opening scene
    compendium_npcs = []
    for npc_id, npc_data in seed_state.compendium.npcs.items():
        if npc_data.presence == "present":
            compendium_npcs.append({
                "name": npc_data.name,
                "title": npc_data.title,
                "bio": npc_data.bio,
                "presence": npc_data.presence,
            })
    
    # Extract arc (objective only — threads surface later)
    arc_data = None
    if seed_state.long_term_objective:
        arc_data = {
            "objective": seed_state.long_term_objective.long_term_objective,
        }
    
    ctx = {
        "pc": {
            "name": pc.name,
            "tagline": pc.tagline,
            "situation": {k: v for k, v in pc.situation.items() if k != "opening"},
        },
        "location": {
            "id": location.id,
            "name": location.name,
        },
        "arc_origin": seed_state.arc_origin,
        "pool_selection": pool_selection,
        "setting_info": setting_info,
        "compendium_npcs": compendium_npcs,
        "arc": arc_data,
    }
    
    system_text = _render(env, "narrate_seed_system.j2", ctx)
    user_text = "Generate the opening_narrative, actions, and outcome_summary now."
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ], ctx


async def narrate_seed(
    seed_state: SeedState,
    config: EngineConfig,
    *,
    pack: Pack | None = None,
    pool_selection: dict[str, Any] | None = None,
    template_dir: str | None = None,
) -> dict[str, Any]:
    """Generate opening_narrative, actions, outcome_summary from validated SeedState.
    
    Returns dict with exactly:
    - opening_narrative: str (min_length=50)
    - actions: list[str] (min_length=4, max_length=4)
    - outcome_summary: str
    """
    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)
    trace_id = uuid.uuid4().hex[:8]

    _log.debug(
        "narrate_seed start pc=%s location=%s",
        seed_state.pc.name, seed_state.location.name,
        extra={"trace_id": trace_id},
    )

    messages, _ = _build_narrate_seed_messages(env, seed_state, pool_selection, pack=pack)
    messages, _, _ = trim_messages(messages, config.context_window)

    for attempt in range(1 + config.max_llm_retries):
        try:
            result = await llm_chat(
                config,
                messages,
                temperature=config.narrate_temperature,
                top_p=config.narrate_top_p,
                timeout=float(config.request_timeout_s),
                num_ctx=config.num_ctx,
                enable_thinking=False,
                reasoning_effort="none",
                thinking_budget=0,
            )
        except LlmcTimeout:
            _log.error(
                "narrate_seed: LLM timeout",
                extra={"error_kind": ErrorKind.LLM_TIMEOUT, "trace_id": trace_id},
            )
            raise
        except LlmcError as exc:
            _log.error(
                "narrate_seed: LLM error: %s",
                exc,
                extra={"error_kind": exc.kind, "trace_id": trace_id},
            )
            raise
        raw = result.content

        cleaned = strip_thinking(raw)
        j = _find_json(cleaned)
        if j is None:
            parse_error = "No JSON found in narrate_seed response"
            _log.warning(
                "narrate_seed failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_llm_retries:
                fb = f"Your output failed to parse: {parse_error}. Re-emit a valid JSON with opening_narrative, actions, and outcome_summary."
                messages.append({"role": "user", "content": fb})
            continue

        try:
            # Validate actions length
            actions = j.get("actions", [])
            if len(actions) < 4:
                raise ValueError(f"actions must have at least 4 items, got {len(actions)}")
            if len(actions) > 4:
                actions = actions[:4]
            
            opening_narrative = j.get("opening_narrative", "")
            if len(opening_narrative) < 1500:
                raise ValueError(f"opening_narrative must be at least 1500 characters, got {len(opening_narrative)}")
            
            outcome_summary = j.get("outcome_summary", "")

        except Exception as exc:
            parse_error = str(exc)
            _log.warning(
                "narrate_seed validation failed (attempt %d): %s",
                attempt + 1,
                parse_error,
                extra={"trace_id": trace_id},
            )
            if attempt < config.max_llm_retries:
                fb = (
                    f"Narration validation failed: {parse_error[:300]}. "
                    "Ensure opening_narrative is at least 50 characters, actions has exactly 4 items."
                )
                messages.append({"role": "user", "content": fb})
            continue

        _log.info(
            "narrate_seed complete opening_len=%d",
            len(opening_narrative),
            extra={"trace_id": trace_id},
        )
        return {
            "opening_narrative": opening_narrative,
            "actions": actions,
            "outcome_summary": outcome_summary,
        }

    raise RuntimeError(
        f"narrate_seed failed after {1 + config.max_llm_retries} attempts — trace {trace_id}"
    )
