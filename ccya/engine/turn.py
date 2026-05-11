"""Turn orchestrator: run_turn, run_turn_retry, _validate, warmup."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from ccya.engine.changes import _summarize_applied, summarize_changes
from ccya.engine.compactor import maybe_compact
from ccya.engine.config import EngineConfig, _build_jinja_env, _inflight, _log_llm_io, _log_prompts
from ccya.engine.markers import strip_trace_markers_in_messages
from ccya.engine.extraction import (
    _avg_extract_ms,
    _avg_narrate_ms,
    _context_meta,
    _run_extraction_pipeline,
)
from ccya.engine.names import generate_npc_names_split
from ccya.engine.narrate import _known_characters_for_extract, _narrate_messages
from ccya.engine.pressure import _expire_scene_pressures, _purge_scene_pressures
from ccya.engine.rules import _avg_rules_ms, _call_rules, _log_rules_outcome, _rules_messages
from ccya.llm_client import (
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    IntentEnvelope,
    RulesCheck,
    RulesOutcome,
    StateDelta,
    TurnResult,
)
from ccya.rules import resolve_check
from ccya.state import (
    apply_delta,
    apply_momentum,
    append_chronicle,
    append_event,
    load_chronicle_tail,
    load_recent_chronicle_turns,
    load_recent_events,
    load_state,
    reconcile_delta,
    resolve_inventory_remove_target,
    save_state,
)

_log = logging.getLogger("ccya.engine")

_ALL_DOMAINS: frozenset[str] = frozenset({
    "scene",
    "inventory",
    "pc_condition",
    "quest_updates",
    "location_change",
    "recent_events",
    "compendium_npc",
})

_DEFAULT_DOMAINS: list[str] = [
    "scene",
    "inventory",
    "pc_condition",
    "quest_updates",
]

_SCOPE_OPEN = "<scope>"
_SCOPE_CLOSE = "</scope>"
_SCOPE_TAIL_RE = re.compile(r"<scope>(.*?)</scope>", re.DOTALL)
_SCOPE_TAIL_BUFFER_SIZE = len(_SCOPE_OPEN) - 1  # = 6


def _split_scope_tail(text: str) -> tuple[str, list[str] | None]:
    """Extract <scope>...</scope> tail, return (prose, active_domains | None).

    Returns:
        (prose, None)        — no tag found, or malformed JSON, or wrong shape.
                                Caller should use _DEFAULT_DOMAINS.
        (prose, [...])       — valid; list may be empty (intentional skip-everything).
                                Empty list = "run only progress."

    Filters domains against _ALL_DOMAINS; unknown values silently dropped.
    """
    m = _SCOPE_TAIL_RE.search(text)
    if not m:
        return text, None

    prose = (text[:m.start()] + text[m.end():]).rstrip()
    json_str = m.group(1).strip()

    try:
        parsed = json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return prose, None

    if not isinstance(parsed, dict):
        return prose, None

    raw = parsed.get("active_domains")
    if not isinstance(raw, list):
        return prose, None

    domains = [d for d in raw if isinstance(d, str) and d in _ALL_DOMAINS]
    return prose, domains


class _StreamTailFilter:
    """Filters a streaming text feed to suppress everything from <scope> onward.

    Maintains a sliding tail buffer of `_SCOPE_TAIL_BUFFER_SIZE` chars to detect
    the opening sentinel even when it crosses chunk boundaries. After the
    sentinel is observed, all subsequent chunks are accumulated internally
    (still recorded in full_text) but `feed()` returns "" so the SSE consumer
    sees no further tokens.

    Usage:
        flt = _StreamTailFilter()
        async for chunk in llm_chat_stream(...):
            visible = flt.feed(chunk)
            if visible:
                yield ("token", visible)
        tail = flt.flush()
        if tail:
            yield ("token", tail)
        full = flt.full_text()  # for post-stream parsing
    """

    __slots__ = ("_buf", "_seen_sentinel", "_chunks")

    def __init__(self) -> None:
        self._buf: str = ""
        self._seen_sentinel: bool = False
        self._chunks: list[str] = []

    def feed(self, chunk: str) -> str:
        self._chunks.append(chunk)
        if self._seen_sentinel:
            return ""
        combined = self._buf + chunk
        idx = combined.find(_SCOPE_OPEN)
        if idx >= 0:
            self._seen_sentinel = True
            self._buf = ""
            return combined[:idx]
        if len(combined) > _SCOPE_TAIL_BUFFER_SIZE:
            emit = combined[:-_SCOPE_TAIL_BUFFER_SIZE]
            self._buf = combined[-_SCOPE_TAIL_BUFFER_SIZE:]
            return emit
        self._buf = combined
        return ""

    def flush(self) -> str:
        if self._seen_sentinel:
            return ""
        out = self._buf
        self._buf = ""
        return out

    def full_text(self) -> str:
        return "".join(self._chunks)


def _compute_ages(state: dict[str, Any]) -> dict[str, int]:
    """Compute age/staleness counters for narration directives."""
    meta = state.get("meta") or {}
    scene = state.get("scene") or {}
    current_turn = meta.get("turn", 0)

    scene_entered = scene.get("turn_entered", 0)
    scene_age = current_turn - scene_entered if scene_entered > 0 else 0

    loc_entered = scene.get("location_entered_turn", 0)
    location_age = current_turn - loc_entered if loc_entered > 0 else 0

    tags = scene.get("tags") or []
    combat_entered = scene.get("combat_started_turn", 0)
    # combat_started_turn is set during apply_delta (post-narrate), so this
    # reads the pre-delta value. combat_age will be 0 on the turn combat
    # starts; COMBAT FATIGUE fires one turn late (acceptable — minor).
    combat_age = current_turn - combat_entered if ("combat" in tags and combat_entered > 0) else 0

    return {
        "scene_age": scene_age,
        "location_age": location_age,
        "combat_age": combat_age,
    }


def _compute_quest_ages(state: dict[str, Any], current_turn: int) -> list[dict[str, Any]]:
    result = []
    for q in (state.get("quests") or []):
        if q.get("status") != "active":
            continue
        last_advanced = q.get("last_advanced_turn", 0)
        stalled = current_turn - last_advanced if last_advanced > 0 else 0
        result.append({
            "id": q["id"],
            "title": q.get("title", ""),
            "stalled_turns": stalled,
        })
    return result


def _compute_recent_window(
    state: dict[str, Any], config: EngineConfig,
) -> tuple[int, int]:
    """Compute (desired_recent, last_compacted_turn) for narrate/extract calls.

    Returns the number of recent chronicle turns to load and the compaction
    boundary turn so the loader can skip already-compacted history.
    """
    meta = state.get("meta") or {}
    last_compacted_turn = int(meta.get("last_compacted_turn", 0) or 0)
    current_turn_completed = int(meta.get("turn", 0) or 0)
    turns_since_compaction = max(0, current_turn_completed - last_compacted_turn)
    desired_recent = min(config.window_turns, turns_since_compaction)
    if current_turn_completed > 0:
        desired_recent = max(
            desired_recent,
            min(config.recent_turns_min, turns_since_compaction),
        )
    return desired_recent, last_compacted_turn


async def run_turn(
    save_dir: Path,
    user_input: str,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
    pack_style: str = "",
    pack_name_locales: list[dict[str, Any]] = [],
    pack_factions: list[dict[str, str]] = [],
    pack_locations: list[dict[str, str]] = [],
    pack_narrator_rules: list[str] = [],
    pack_world_rules: list[str] = [],
) -> AsyncIterator[tuple[str, Any]]:
    if config is None:
        config = EngineConfig()

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)

    trace_id = uuid.uuid4().hex[:8]
    errors: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    state = load_state(save_dir)
    narrative_chunks: list[str] = []
    delta: StateDelta | None = None
    actions: list[str] = []
    recent_events: list[dict[str, Any]] = []
    recent_events_evicted: bool = False
    intent = IntentEnvelope(
        intent="", intent_verb="act", check=RulesCheck(required=False)
    )
    outcome = RulesOutcome(rolled=False)
    rules_metrics: dict[str, Any] = {"total_ms": 0, "rolled": False}

    try:
        await _inflight.acquire(str(save_dir))

        # Prompt capture variables (initialized early for exception safety)
        rendered_rules_system = ""
        rendered_rules_user = ""
        rendered_narr_system = ""
        rendered_narr_user = ""
        rules_raw_response = ""
        narrative = ""

        # --- Memory: load chronicle tail + recent turns ---
        # chronicle_tail is older history (compressed); recent_turns is the rolling
        # window. Slice the last window_turns from the tail to avoid overlap.
        desired_recent, last_compacted_turn = _compute_recent_window(state, config)
        recent_turns = load_recent_chronicle_turns(
            save_dir,
            desired_recent,
            min_turn_exclusive=last_compacted_turn,
        )
        chronicle_tail = load_chronicle_tail(
            save_dir,
            config.chronicle_prefix_budget_tokens,
            skip_last_n_turns=config.window_turns,
        )

        # === Call 0: Rules / intent classification ===
        exp_rules_ms = _avg_rules_ms(save_dir)
        yield ("phase", {"phase": "rules_start", "expected_ms": exp_rules_ms})
        t_rules = asyncio.get_event_loop().time()
        turn_no = state.get("meta", {}).get("turn", 0) + 1

        _present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])
        rules_messages = _rules_messages(
            env, state, user_input,
            recent_turns=recent_turns[-1:],
            turn_no=turn_no,
            present_npcs=_present_npcs,
        )
        # Capture pre-trim content for context_meta so the judge sees original sizes
        rendered_rules_system = rules_messages[0]["content"] if rules_messages else ""
        rendered_rules_user = rules_messages[-1]["content"] if rules_messages else ""
        strip_trace_markers_in_messages(rules_messages)
        rules_messages, rules_trimmed, rules_trimmed_chars = trim_messages(rules_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "rules", rules_messages
            )
        intent, rules_usage, rules_raw_response, rules_parse_error = await _call_rules(rules_messages, config, trace_id)

        # Resolve dice in Python (deterministic) — _call_rules degrades intent, we do outcome here
        if intent.check.required and intent.check.skill:
            try:
                # Normalize structured Condition dicts to ids for the rules engine.
                _pc_conds_struct = list((state.get("pc") or {}).get("conditions") or [])
                _pc_cond_ids = [
                    c.get("id", "") if isinstance(c, dict) else str(c)
                    for c in _pc_conds_struct
                ]
                outcome = resolve_check(
                    skill=intent.check.skill,
                    difficulty=intent.check.difficulty,
                    pc_stats=(state.get("pc") or {}).get("stats") or {},
                    pc_conditions=[cid for cid in _pc_cond_ids if cid],
                    intent_verb=intent.intent_verb,
                    intent=intent.intent,
                )
            except Exception as exc:
                _log.warning(
                    "rules.resolve_check failed: %s", exc, extra={"trace_id": trace_id}
                )
                outcome = RulesOutcome(
                    rolled=False, intent_verb=intent.intent_verb, intent=intent.intent
                )
        else:
            outcome = RulesOutcome(
                rolled=False, intent_verb=intent.intent_verb, intent=intent.intent
            )

        # Apply momentum deterministically from band (never from LLM)
        if outcome.rolled:
            apply_momentum(state, outcome.band)

        # De-escalation magnitude: success on a scene with active pressure
        deescalate: float = 0.0
        if config and config.scene_pressure_deescalate_on_success:
            if (
                outcome.rolled
                and outcome.band in ("success", "crit_success")
                and any(
                    p.get("urgency") in ("immediate", "building")
                    for p in (state.get("scene") or {}).get("scene_pressure") or []
                )
            ):
                deescalate = 1.0 if outcome.band == "crit_success" else 0.6

        # Age counters for narration directives
        ages = _compute_ages(state)
        quest_ages = _compute_quest_ages(state, turn_no)

        if config.log_prompts:
            _log_rules_outcome(
                state.get("meta", {}).get("turn", 0) + 1, intent, outcome
            )

        rules_ms = (asyncio.get_event_loop().time() - t_rules) * 1000
        rules_metrics = {
            "total_ms": round(rules_ms, 1),
            "rolled": outcome.rolled,
            "tokens_in": rules_usage.get("prompt_tokens", 0),
            "tokens_out": rules_usage.get("total_tokens", 0),
        }

        yield (
            "phase",
            {
                "phase": "rules_done",
                "rolled": outcome.rolled,
                "band": outcome.band if outcome.rolled else None,
                "skill": outcome.skill if outcome.rolled else None,
                "dice": outcome.dice if outcome.rolled else [],
                "final_total": outcome.final_total if outcome.rolled else 0,
                "difficulty": outcome.difficulty if outcome.rolled else None,
                "stat_value": outcome.stat_value if outcome.rolled else 0,
                "stat_mod": outcome.stat_mod if outcome.rolled else 0,
                "diff_mod": outcome.diff_mod if outcome.rolled else 0,
                "cond_mod": outcome.cond_mod if outcome.rolled else 0,
                "directive": outcome.directive if outcome.rolled else "",
                "intent_verb": intent.intent_verb,
            },
        )

        # === Call 1: Narrate (streaming) ===
        exp_narrate_ms = _avg_narrate_ms(save_dir)
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        # Rolling NPC name pool for mid-game cultural anchoring (split by gender)
        _npc_name_pool: dict[str, list[str]] = {}
        if pack_name_locales:
            _npc_name_pool = generate_npc_names_split(
                pack_name_locales,
                male_count=5,
                female_count=5,
                seed=state.get("meta", {}).get("turn", 0),
            )

        # Read pending_gm_beat from previous turn's progress extraction
        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
        if _pending_gm_beat:
            _expires = _pending_gm_beat.get("beat_expires_turn")
            if _expires is not None and turn_no > _expires:
                _pending_gm_beat = None
                state.setdefault("meta", {})["pending_gm_beat"] = None

        # Known NPCs for narrator context (Phase 4A)
        _known_npcs = _known_characters_for_extract(state, compact=True)

        # Present NPCs from delta-maintained state (Phase 4H)
        _present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])

        # Compendium bios for present + recently_left NPCs (Phase 1)
        _compendium_bios: list[dict[str, Any]] = []
        _bio_ids: set[str] = set()
        for npc in _present_npcs:
            nid = npc.get("id", "")
            if nid and nid not in _bio_ids:
                _bio_ids.add(nid)
                entry = (state.get("compendium") or {}).get("npcs", {}).get(nid, {})
                if entry:
                    _compendium_bios.append({
                        "id": nid,
                        "name": entry.get("name", ""),
                        "title": entry.get("title", ""),
                        "bio": (entry.get("bio") or "").strip(),
                    })
        for npc in (state.get("scene") or {}).get("recently_left", []):
            nid = npc.get("id", "") if isinstance(npc, dict) else ""
            if nid and nid not in _bio_ids:
                _bio_ids.add(nid)
                entry = (state.get("compendium") or {}).get("npcs", {}).get(nid, {})
                if entry:
                    _compendium_bios.append({
                        "id": nid,
                        "name": entry.get("name", ""),
                        "title": entry.get("title", ""),
                        "bio": (entry.get("bio") or "").strip(),
                    })

        # Phase 5: world context from pack scenario (primary) or state world (legacy)
        _world = state.get("world") or {}
        _world_factions = pack_factions if pack_factions else list(_world.get("factions") or [])
        _world_locations = pack_locations if pack_locations else list(_world.get("locations") or [])
        _pc_allegiance = (state.get("pc") or {}).get("allegiance")
        _pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
        _pack_world_rules = pack_world_rules if pack_world_rules else []

        narr_messages = _narrate_messages(
            env,
            state,
            user_input,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
            pack_style=pack_style,
            narrator_rules=_pack_narrator_rules,
            world_rules=_pack_world_rules,
            rules_outcome=outcome,
            npc_name_pool=_npc_name_pool,
            recently_left=(state.get("scene") or {}).get("recently_left", []),
            momentum=(state.get("pc") or {}).get("momentum", 0),
            pending_gm_beat=_pending_gm_beat,
            deescalate=deescalate,
            ages=ages,
            known_npcs=_known_npcs,
            present_npcs=_present_npcs,
            compendium_bios=_compendium_bios,
            world_factions=_world_factions,
            world_locations=_world_locations,
            pc_allegiance=_pc_allegiance,
            turn_no=turn_no,
        )
        # Capture pre-trim content for context_meta so the judge sees original sizes
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""
        strip_trace_markers_in_messages(narr_messages)
        narr_messages, narr_trimmed, narr_trimmed_chars = trim_messages(narr_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "narrate", narr_messages
            )

        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        narr_stream_stats: dict[str, Any] = {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_request",
                messages=narr_messages,
                max_chars=config.log_llm_io_max_chars,
            )
        scope_filter = _StreamTailFilter()
        first_visible = True
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            visible = scope_filter.feed(chunk)
            if visible:
                if first_visible:
                    first_ms = (asyncio.get_event_loop().time() - t0) * 1000
                    first_visible = False
                yield ("token", visible)
        tail = scope_filter.flush()
        if tail:
            if first_visible:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            yield ("token", tail)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        # Keep narrative_chunks compatible with downstream code paths (error fallback).
        narrative_chunks[:] = [scope_filter.full_text()]
        full_with_tail = strip_thinking(scope_filter.full_text())
        narrative, parsed_domains = _split_scope_tail(full_with_tail)
        _active_domains = (
            list(parsed_domains) if parsed_domains is not None else list(_DEFAULT_DOMAINS)
        )
        narr_metrics = {
            "first_token_ms": round(first_ms, 1),
            "total_ms": round(narr_ms, 1),
            "tokens_in": int(narr_stream_stats.get("prompt_eval_count", 0)),
            "tokens_out": int(narr_stream_stats.get("eval_count", 0)),
        }
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_response",
                response=narrative,
                extra={"timing_ms": narr_metrics},
                max_chars=config.log_llm_io_max_chars,
            )

        yield ("phase", {"phase": "narrate_done"})

        # Clear pending_gm_beat after narration consumed it
        state.setdefault("meta", {})["pending_gm_beat"] = None

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, extraction_event, progress_result, scene_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    active_domains=_active_domains,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    deescalate=deescalate,
                    quest_ages=quest_ages,
                    recent_turns=recent_turns,
                )
            )
            # Beat lifecycle: handle disposition from progress extractor
            _new_beat = progress_result.gm_beat if progress_result else None
            _disposition = progress_result.beat_disposition if progress_result else "consume"
            _current_beat = (state.get("meta") or {}).get("pending_gm_beat")

            if _disposition == "carry" and _current_beat and not _new_beat:
                # Keep existing beat — do not overwrite
                pass
            elif _new_beat and _new_beat.type:
                # Replace or fresh write (includes implicit replace when carry+new_beat)
                _beat_dict = _new_beat.model_dump(exclude_none=True)
                _beat_dict["beat_expires_turn"] = turn_no + 2
                state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
            else:
                # consume or no new beat — clear
                state.setdefault("meta", {})["pending_gm_beat"] = None
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})

        yield ("phase", {"phase": "extract_done"})

        # --- Scene pressure: purge stale pressures, then expire/escalate ---
        if delta is not None:
            location_changed = bool(delta.location_change)
            # Combat ended: combat was in last turn's tags but not in current
            combat_ended = False
            if not location_changed and delta.scene_tags is not None:
                current_tags = set(delta.scene_tags)
                prev_events = load_recent_events(save_dir, 1)
                if prev_events:
                    prev_tags = set(prev_events[0].get("scene_tags") or [])
                    if "combat" in prev_tags and "combat" not in current_tags:
                        combat_ended = True
            _purge_scene_pressures(
                state, delta,
                location_changed=location_changed,
                combat_ended=combat_ended,
                config=config,
            )
            _expire_scene_pressures(state, delta, config)

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        # Roll up per-stream token counts for the metrics dict
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "progress")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "progress")
        )
        # Build per-stream breakdown for UI display
        _streams = {}
        for s in ("scene", "state", "progress"):
            ev = extraction_event.get(s)
            if ev:
                _streams[s] = {
                    "ms": ev.get("ms", 0),
                    "tokens_in": ev.get("tokens_in", 0),
                    "tokens_out": ev.get("tokens_out", 0),
                    "skipped": ev.get("skipped", False),
                }
        ext_metrics = {
            "total_ms": round(ext_ms, 1),
            "tokens_in": _tokens_in,
            "tokens_out": _tokens_out,
            "retries": 0,
            "streams": _streams,
        }
        metrics = {
            "rules": rules_metrics,
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }

        # === Validate & apply delta ===
        state_pre_apply = copy.deepcopy(state)
        applied: dict[str, Any] = {}
        rejected: list[dict[str, Any]] = []

        if delta is not None:
            rejected = _validate(state, delta)
            blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
            if blocking:
                errors.append(
                    {
                        "trace_id": trace_id,
                        "message": f"Delta validation failed ({len(blocking)} rejection(s)).",
                    }
                )
                narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"
            else:
                reconcile_warnings = reconcile_delta(state, delta)
                for w in reconcile_warnings:
                    _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
                state, recent_events_evicted = apply_delta(
                    state, delta, recent_events_max=config.recent_events_max
                )
                recent_events = list(delta.recent_events_add)
                applied = delta.model_dump(exclude_none=True)
                for r in rejected:
                    if r.get("kind") == "warn_overdraw":
                        _log.warning(
                            "inventory over-draw clamped: %s",
                            r.get("reason"),
                            extra={"trace_id": trace_id},
                        )

                # Stamp last_seen on touched NPCs (Phase 4C)
                comp = state.get("compendium", {}).get("npcs", {})
                location = state.get("location", {})
                touched_ids: set[str] = set()
                for na in (delta.npc_add or []):
                    touched_ids.add(na.id)
                for nu in (delta.npc_update or []):
                    touched_ids.add(nu.id)
                for cu in (delta.compendium_npc_update or []):
                    touched_ids.add(cu.id)
                for nid in touched_ids:
                    entry = comp.setdefault(nid, {})
                    entry["last_seen"] = {
                        "turn": turn_no,
                        "location_id": location.get("id", ""),
                        "location_name": location.get("name", ""),
                        "last_seen_state": entry.get("last_seen_state", ""),
                    }

        # Decay recently_left counter (engine-side, not in state.py).
        scene = state.get("scene", {})
        turns = scene.get("recently_left_turns", 0)
        if turns > 0:
            turns -= 1
            if turns == 0:
                scene["recently_left"] = []
            else:
                scene["recently_left_turns"] = turns

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

        # === Turn increment (single source of truth: here) ===
        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        # === Write: events.jsonl → atomic state.yaml → chronicle.md ===
        # Narrative is canonical in chronicle.md only (see load_recent_chronicle_turns).
        rules_event: dict[str, Any] = {
            "intent_verb": intent.intent_verb,
            "intent": intent.intent,
            "rolled": outcome.rolled,
            "total_ms": rules_metrics.get("total_ms"),
            "tokens_in": rules_metrics.get("tokens_in", 0),
            "tokens_out": rules_metrics.get("tokens_out", 0),
        }
        if outcome.rolled:
            rules_event.update({
                "skill": outcome.skill,
                "difficulty": outcome.difficulty,
                "dice": outcome.dice,
                "stat_mod": outcome.stat_mod,
                "diff_mod": outcome.diff_mod,
                "cond_mod": outcome.cond_mod,
                "final_total": outcome.final_total,
                "band": outcome.band,
                "outcome_summary": outcome_summary,
            })

        _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = {
            "ts": _ts,
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": user_input,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "rules": rules_event,
            "narrate": narr_metrics,
            "extract": ext_metrics,
            "extraction": extraction_event,
            "scope": {
                "active_domains": _active_domains,
            },
            "changes": changes,
            # Prompt logging (for turn viewer)
            "rules_prompt": {
                "rendered_system": rendered_rules_system,
                "rendered_user": rendered_rules_user,
                "output": rules_raw_response,
                "parse_error": rules_parse_error,
                "context_meta": _context_meta(rendered_rules_system, rendered_rules_user, rules_trimmed, rules_trimmed_chars),
            },
            "narrate_prompt": {
                "rendered_system": rendered_narr_system,
                "rendered_user": rendered_narr_user,
                "output": narrative,
                "context_meta": _context_meta(rendered_narr_system, rendered_narr_user, narr_trimmed, narr_trimmed_chars),
            },
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(
            save_dir,
            f"\n\n## Turn {state['meta']['turn']} — {user_input}\n\n{narrative.strip()}",
        )

        # === Compaction (after persist, before yield complete) ===
        if config.compact_every > 0:
            t_compact = asyncio.get_running_loop().time()
            state, compaction_ran = await maybe_compact(save_dir, state, config)
            if compaction_ran:
                yield ("phase", {"phase": "compact_start", "expected_ms": 0})
                yield ("phase", {"phase": "compact_done", "ms": round(
                    (asyncio.get_running_loop().time() - t_compact) * 1000, 1
                )})
            save_state(save_dir, state)

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            recent_events=recent_events,
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            rules=rules_event or {},
            outcome_summary=outcome_summary,
            recent_events_evicted=recent_events_evicted,
            ts=_ts,
        )
        yield ("complete", result_obj)

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
        fallback = narrative_chunks and "".join(narrative_chunks) or ""
        if not fallback:
            fallback = f"*An error occurred. Trace `{trace_id}` — try rephrasing.*"
        yield (
            "complete",
            TurnResult(
                turn=state.get("meta", {}).get("turn", 0),
                trace_id=trace_id,
                narrative=fallback,
                state_delta={},
                errors=errors,
                metrics=metrics,
                diff=[],
                changes={},
                ts="",
            ),
        )
    finally:
        await _inflight.release(str(save_dir))


def _validate(state: dict[str, Any], delta: StateDelta) -> list[dict[str, Any]]:
    rejections: list[dict[str, Any]] = []

    inv_list: list[dict[str, Any]] = state.get("inventory", [])
    inv_by_id: dict[str, dict[str, Any]] = {
        str(it.get("id", "")): it for it in inv_list if isinstance(it, dict)
    }
    for rem in delta.inventory_remove:
        canonical = resolve_inventory_remove_target(inv_list, rem.id)
        if canonical is None:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "value": rem.id,
                    "reason": f"Inventory item '{rem.id}' does not exist",
                }
            )
            continue
        if rem.amount is None:
            continue
        try:
            requested = int(rem.amount)
        except (TypeError, ValueError):
            continue
        if requested <= 0:
            continue
        current = int(inv_by_id.get(canonical, {}).get("amount") or 1)
        if requested > current:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "warn_overdraw",
                    "value": canonical,
                    "requested": requested,
                    "current": current,
                    "reason": (
                        f"Over-draw on '{canonical}': requested {requested} but stack is {current}. "
                        "apply_delta will clamp to a full-stack remove."
                    ),
                }
            )

    # quest_updates is create-or-update: new quest IDs are allowed (apply_delta creates them).
    # No quest ID validation here.

    return rejections


async def run_turn_retry(
    save_dir: Path,
    rules_outcome: RulesOutcome,
    intent: IntentEnvelope,
    config: EngineConfig | None = None,
    *,
    template_dir: str | None = None,
    pack_style: str = "",
    pack_name_locales: list[dict[str, Any]] = [],
    pack_factions: list[dict[str, str]] = [],
    pack_locations: list[dict[str, str]] = [],
    pack_narrator_rules: list[str] = [],
    pack_world_rules: list[str] = [],
) -> AsyncIterator[tuple[str, Any]]:
    """Re-roll narration + extraction with the same rules outcome.

    Skips Call 0 (rules), uses the provided rules_outcome for Call 1 (narrate),
    then re-runs the extraction pipeline. Increments turn counter and writes
    a new turn entry.
    """
    if config is None:
        config = EngineConfig()

    template_dir = template_dir or str(Path(__file__).parent.parent / "prompts")
    env = _build_jinja_env(template_dir)

    trace_id = uuid.uuid4().hex[:8]
    errors: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    state = load_state(save_dir)
    narrative_chunks: list[str] = []
    delta: StateDelta | None = None
    actions: list[str] = []
    recent_events: list[dict[str, Any]] = []
    recent_events_evicted: bool = False
    outcome = rules_outcome

    try:
        await _inflight.acquire(str(save_dir))

        rendered_narr_system = ""
        rendered_narr_user = ""
        narrative = ""

        desired_recent, last_compacted_turn = _compute_recent_window(state, config)
        recent_turns = load_recent_chronicle_turns(
            save_dir,
            desired_recent,
            min_turn_exclusive=last_compacted_turn,
        )
        chronicle_tail = load_chronicle_tail(
            save_dir,
            config.chronicle_prefix_budget_tokens,
            skip_last_n_turns=config.window_turns,
        )

        turn_no = state.get("meta", {}).get("turn", 0) + 1

        # === Call 1: Narrate (streaming) — same as run_turn ===
        exp_narrate_ms = _avg_narrate_ms(save_dir)
        yield ("phase", {"phase": "narrate_start", "expected_ms": exp_narrate_ms})

        _npc_name_pool: dict[str, list[str]] = {}
        if pack_name_locales:
            _npc_name_pool = generate_npc_names_split(
                pack_name_locales,
                male_count=5,
                female_count=5,
                seed=state.get("meta", {}).get("turn", 0),
            )

        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
        if _pending_gm_beat:
            _expires = _pending_gm_beat.get("beat_expires_turn")
            if _expires is not None and turn_no > _expires:
                _pending_gm_beat = None
                state.setdefault("meta", {})["pending_gm_beat"] = None

        ages = _compute_ages(state)

        # Known NPCs for narrator context (Phase 4A)
        _known_npcs = _known_characters_for_extract(state, compact=True)

        # Present NPCs from delta-maintained state (Phase 4H)
        _present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])

        # Compendium bios for present + recently_left NPCs (Phase 1)
        _compendium_bios: list[dict[str, Any]] = []
        _bio_ids: set[str] = set()
        for npc in _present_npcs:
            nid = npc.get("id", "")
            if nid and nid not in _bio_ids:
                _bio_ids.add(nid)
                entry = (state.get("compendium") or {}).get("npcs", {}).get(nid, {})
                if entry:
                    _compendium_bios.append({
                        "id": nid,
                        "name": entry.get("name", ""),
                        "title": entry.get("title", ""),
                        "bio": (entry.get("bio") or "").strip(),
                    })
        for npc in (state.get("scene") or {}).get("recently_left", []):
            nid = npc.get("id", "") if isinstance(npc, dict) else ""
            if nid and nid not in _bio_ids:
                _bio_ids.add(nid)
                entry = (state.get("compendium") or {}).get("npcs", {}).get(nid, {})
                if entry:
                    _compendium_bios.append({
                        "id": nid,
                        "name": entry.get("name", ""),
                        "title": entry.get("title", ""),
                        "bio": (entry.get("bio") or "").strip(),
                    })

        # Phase 5: world context from pack scenario (primary) or state world (legacy)
        _world = state.get("world") or {}
        _world_factions = pack_factions if pack_factions else list(_world.get("factions") or [])
        _world_locations = pack_locations if pack_locations else list(_world.get("locations") or [])
        _pc_allegiance = (state.get("pc") or {}).get("allegiance")
        _pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
        _pack_world_rules = pack_world_rules if pack_world_rules else []

        narr_messages = _narrate_messages(
            env,
            state,
            intent.intent,
            chronicle_tail=chronicle_tail,
            recent_turns=recent_turns,
            enable_narrate_thinking=config.enable_narrate_thinking,
            pack_style=pack_style,
            narrator_rules=_pack_narrator_rules,
            world_rules=_pack_world_rules,
            rules_outcome=outcome,
            npc_name_pool=_npc_name_pool,
            recently_left=(state.get("scene") or {}).get("recently_left", []),
            momentum=(state.get("pc") or {}).get("momentum", 0),
            pending_gm_beat=_pending_gm_beat,
            # Retry: skip deescalation/quest-age awareness since the rules
            # outcome is already fixed — re-rolling narration shouldn't
            # change the pacing directive.
            deescalate=False,
            ages=ages,
            known_npcs=_known_npcs,
            present_npcs=_present_npcs,
            compendium_bios=_compendium_bios,
            world_factions=_world_factions,
            world_locations=_world_locations,
            pc_allegiance=_pc_allegiance,
        )
        # Capture pre-trim content for context_meta so the judge sees original sizes
        rendered_narr_system = narr_messages[0]["content"] if narr_messages else ""
        rendered_narr_user = narr_messages[-1]["content"] if narr_messages else ""
        strip_trace_markers_in_messages(narr_messages)
        narr_messages, narr_trimmed, narr_trimmed_chars = trim_messages(narr_messages, config.prompt_token_budget)
        if config.log_prompts:
            _log_prompts(
                state.get("meta", {}).get("turn", 0) + 1, "narrate", narr_messages
            )

        first_ms = 0.0
        t0 = asyncio.get_event_loop().time()
        narr_stream_stats: dict[str, Any] = {}
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_request",
                messages=narr_messages,
                max_chars=config.log_llm_io_max_chars,
            )
        scope_filter = _StreamTailFilter()
        first_visible = True
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            visible = scope_filter.feed(chunk)
            if visible:
                if first_visible:
                    first_ms = (asyncio.get_event_loop().time() - t0) * 1000
                    first_visible = False
                yield ("token", visible)
        tail = scope_filter.flush()
        if tail:
            if first_visible:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
            yield ("token", tail)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        # Keep narrative_chunks compatible with downstream code paths (error fallback).
        narrative_chunks[:] = [scope_filter.full_text()]
        full_with_tail = strip_thinking(scope_filter.full_text())
        narrative, parsed_domains = _split_scope_tail(full_with_tail)
        _active_domains = (
            list(parsed_domains) if parsed_domains is not None else list(_DEFAULT_DOMAINS)
        )
        narr_metrics = {
            "first_token_ms": round(first_ms, 1),
            "total_ms": round(narr_ms, 1),
            "tokens_in": int(narr_stream_stats.get("prompt_eval_count", 0)),
            "tokens_out": int(narr_stream_stats.get("eval_count", 0)),
        }
        if config.log_llm_io:
            _log_llm_io(
                trace_id=trace_id,
                phase="narrate_response",
                response=narrative,
                extra={"timing_ms": narr_metrics},
                max_chars=config.log_llm_io_max_chars,
            )

        yield ("phase", {"phase": "narrate_done"})

        state.setdefault("meta", {})["pending_gm_beat"] = None

        # === Extraction pipeline (3 streams) ===
        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, extraction_event, progress_result, scene_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    active_domains=_active_domains,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    deescalate=False,
                    quest_ages=[],
                    recent_turns=recent_turns,
                )
            )
            # Beat lifecycle: handle disposition from progress extractor
            _new_beat = progress_result.gm_beat if progress_result else None
            _disposition = progress_result.beat_disposition if progress_result else "consume"
            _current_beat = (state.get("meta") or {}).get("pending_gm_beat")

            if _disposition == "carry" and _current_beat and not _new_beat:
                # Keep existing beat — do not overwrite
                pass
            elif _new_beat and _new_beat.type:
                # Replace or fresh write (includes implicit replace when carry+new_beat)
                _beat_dict = _new_beat.model_dump(exclude_none=True)
                _beat_dict["beat_expires_turn"] = turn_no + 2
                state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
            else:
                # consume or no new beat — clear
                state.setdefault("meta", {})["pending_gm_beat"] = None
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})

        yield ("phase", {"phase": "extract_done"})

        if delta is not None:
            location_changed = bool(delta.location_change)
            combat_ended = False
            if not location_changed and delta.scene_tags is not None:
                current_tags = set(delta.scene_tags)
                prev_events = load_recent_events(save_dir, 1)
                if prev_events:
                    prev_tags = set(prev_events[0].get("scene_tags") or [])
                    if "combat" in prev_tags and "combat" not in current_tags:
                        combat_ended = True
            _purge_scene_pressures(
                state, delta,
                location_changed=location_changed,
                combat_ended=combat_ended,
                config=config,
            )
            _expire_scene_pressures(state, delta, config)

        ext_ms = (asyncio.get_event_loop().time() - t2) * 1000
        _tokens_in = sum(
            (extraction_event.get(s) or {}).get("tokens_in", 0)
            for s in ("scene", "state", "progress")
        )
        _tokens_out = sum(
            (extraction_event.get(s) or {}).get("tokens_out", 0)
            for s in ("scene", "state", "progress")
        )
        _streams = {}
        for s in ("scene", "state", "progress"):
            ev = extraction_event.get(s)
            if ev:
                _streams[s] = {
                    "ms": ev.get("ms", 0),
                    "tokens_in": ev.get("tokens_in", 0),
                    "tokens_out": ev.get("tokens_out", 0),
                    "skipped": ev.get("skipped", False),
                }
        ext_metrics = {
            "total_ms": round(ext_ms, 1),
            "tokens_in": _tokens_in,
            "tokens_out": _tokens_out,
            "retries": 0,
            "streams": _streams,
        }
        metrics = {
            "rules": {"total_ms": 0, "rolled": False},
            "narrate": narr_metrics,
            "extract": ext_metrics,
        }

        # === Validate & apply delta ===
        state_pre_apply = copy.deepcopy(state)
        applied: dict[str, Any] = {}
        rejected: list[dict[str, Any]] = []

        if delta is not None:
            rejected = _validate(state, delta)
            blocking = [r for r in rejected if r.get("kind") != "warn_overdraw"]
            if blocking:
                errors.append(
                    {
                        "trace_id": trace_id,
                        "message": f"Delta validation failed ({len(blocking)} rejection(s)).",
                    }
                )
                narrative += f"\n\n*That action didn't resolve as expected. Trace `{trace_id}` — try rephrasing.*"
            else:
                reconcile_warnings = reconcile_delta(state, delta)
                for w in reconcile_warnings:
                    _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
                state, recent_events_evicted = apply_delta(
                    state, delta, recent_events_max=config.recent_events_max
                )
                recent_events = list(delta.recent_events_add)
                applied = delta.model_dump(exclude_none=True)
                for r in rejected:
                    if r.get("kind") == "warn_overdraw":
                        _log.warning(
                            "inventory over-draw clamped: %s",
                            r.get("reason"),
                            extra={"trace_id": trace_id},
                        )

                # Stamp last_seen on touched NPCs (Phase 4C)
                comp = state.get("compendium", {}).get("npcs", {})
                location = state.get("location", {})
                touched_ids: set[str] = set()
                for na in (delta.npc_add or []):
                    touched_ids.add(na.id)
                for nu in (delta.npc_update or []):
                    touched_ids.add(nu.id)
                for cu in (delta.compendium_npc_update or []):
                    touched_ids.add(cu.id)
                for nid in touched_ids:
                    entry = comp.setdefault(nid, {})
                    entry["last_seen"] = {
                        "turn": turn_no,
                        "location_id": location.get("id", ""),
                        "location_name": location.get("name", ""),
                        "last_seen_state": entry.get("last_seen_state", ""),
                    }

        scene = state.get("scene", {})
        turns = scene.get("recently_left_turns", 0)
        if turns > 0:
            turns -= 1
            if turns == 0:
                scene["recently_left"] = []
            else:
                scene["recently_left_turns"] = turns

        diff_lines = _summarize_applied(applied)
        changes = summarize_changes(state_pre_apply, state, applied, rejected)

        state.setdefault("meta", {})["turn"] = state.get("meta", {}).get("turn", 0) + 1

        yield ("phase", {"phase": "persist"})

        rules_event: dict[str, Any] = {
            "intent_verb": intent.intent_verb,
            "intent": intent.intent,
            "rolled": outcome.rolled,
            "total_ms": 0,
            "tokens_in": 0,
            "tokens_out": 0,
        }
        if outcome.rolled:
            rules_event.update({
                "skill": outcome.skill,
                "difficulty": outcome.difficulty,
                "dice": outcome.dice,
                "stat_mod": outcome.stat_mod,
                "diff_mod": outcome.diff_mod,
                "cond_mod": outcome.cond_mod,
                "final_total": outcome.final_total,
                "band": outcome.band,
                "outcome_summary": outcome_summary,
            })

        _ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        event = {
            "ts": _ts,
            "trace_id": trace_id,
            "turn": state["meta"]["turn"],
            "input": intent.intent,
            "applied": applied,
            "rejected": rejected,
            "actions": actions,
            "scene_tags": list(getattr(delta, "scene_tags", [])),
            "rules": rules_event,
            "narrate": narr_metrics,
            "extract": ext_metrics,
            "extraction": extraction_event,
            "scope": {
                "active_domains": _active_domains,
            },
            "changes": changes,
            "rules_prompt": {
                "rendered_system": "",
                "rendered_user": "",
                "output": "",
                "context_meta": {},
            },
            "narrate_prompt": {
                "rendered_system": rendered_narr_system,
                "rendered_user": rendered_narr_user,
                "output": narrative,
                "context_meta": _context_meta(rendered_narr_system, rendered_narr_user, narr_trimmed, narr_trimmed_chars),
            },
        }
        append_event(save_dir, event)
        save_state(save_dir, state)
        append_chronicle(
            save_dir,
            f"\n\n## Turn {state['meta']['turn']} — {intent.intent}\n\n{narrative.strip()}",
        )

        # === Compaction (after persist, before yield complete) ===
        if config.compact_every > 0:
            t_compact = asyncio.get_running_loop().time()
            state, compaction_ran = await maybe_compact(save_dir, state, config)
            if compaction_ran:
                yield ("phase", {"phase": "compact_start", "expected_ms": 0})
                yield ("phase", {"phase": "compact_done", "ms": round(
                    (asyncio.get_running_loop().time() - t_compact) * 1000, 1
                )})
            save_state(save_dir, state)

        result_obj = TurnResult(
            turn=state["meta"]["turn"],
            trace_id=trace_id,
            narrative=narrative,
            state_delta=applied,
            applied=applied,
            rejected=rejected,
            actions=actions,
            scene_tags=list(getattr(delta, "scene_tags", [])),
            recent_events=recent_events,
            diff=diff_lines,
            changes=changes,
            metrics=metrics,
            errors=errors,
            rules=rules_event or {},
            outcome_summary=outcome_summary,
            recent_events_evicted=recent_events_evicted,
            ts=_ts,
        )
        yield ("complete", result_obj)

    except Exception as exc:
        errors.append({"trace_id": trace_id, "message": str(exc)})
        fallback = narrative_chunks and "".join(narrative_chunks) or ""
        if not fallback:
            fallback = f"*An error occurred. Trace `{trace_id}` — try rephrasing.*"
        yield (
            "complete",
            TurnResult(
                turn=state.get("meta", {}).get("turn", 0),
                trace_id=trace_id,
                narrative=fallback,
                state_delta={},
                errors=errors,
                metrics=metrics,
                diff=[],
                changes={},
                ts="",
            ),
        )
    finally:
        await _inflight.release(str(save_dir))


async def warmup(config: EngineConfig) -> None:
    try:
        await llm_chat(
            config.host,
            config.model,
            [{"role": "user", "content": "ok"}],
            temperature=0.0,
            timeout=30.0,
        )
    except Exception:
        pass
