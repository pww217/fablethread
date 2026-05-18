"""Turn orchestrator: run_turn, _validate, warmup."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Literal


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
from ccya.engine.npc_roster import build_npc_roster

from ccya.engine.rules import _avg_rules_ms, _call_rules, _log_rules_outcome, _rules_messages
from ccya.llm_client import (
    chat as llm_chat,
    chat_stream as llm_chat_stream,
    strip_thinking,
    trim_messages,
)
from ccya.models import (
    ArcThread,
    CampaignArc,
    IntentEnvelope,
    ProgressExtractResult,
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
from ccya.state.delta import _merge_arc_update

_log = logging.getLogger("ccya.engine")


@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str  # "Breathe" | "Pressure" | "MoveOn" | "Escalate" | ""
    beat_hint: str | None  # suggested gm_beat type, or None (sent to Narrator when a beat is pending)
    beat_locked: bool  # True: floor relief fired — Progress MUST emit breathing_room beat and gate is force-closed
    gate: Literal["block_add", "block_escalate", "allow"]  # Progress may only add threads when allow
    summary: str  # human-readable log string, never sent to LLM

    @staticmethod
    def neutral() -> PacingContext:
        """Default pacing context for turns without special conditions."""
        return PacingContext(directive="", beat_hint=None, beat_locked=False, gate="allow", summary="neutral")


_ACTIVE_THREAD_CAP = 3
"""Maximum number of threads in the active state."""

_THREAD_COMPLETION_THRESHOLD = 3
"""Progress value at which an active thread is marked complete."""

_LATENT_CAP = 4
"""Maximum number of threads in the latent state."""

_TACTICAL_TAG = "tactical"
"""Tag applied to engine-generated latent threads from candidate_opportunity."""

_EXPIRE_SILENT_TURNS = 5
"""Consecutive turns without being advanced before a thread is demoted to latent."""

_PROMOTION_COOLDOWN_TURNS = 3
"""Minimum turns between latent-to-active promotions."""


def _apply_thread_signals(
    state: dict[str, Any],
    progress_result: Any,
) -> CampaignArc | None:
    """Process simplified advanced_threads list.

    Unified threads[] with scope-aware active bool managed by Python.
    Arc-scoped threads follow the same lifecycle as before but use active: bool instead of ThreadState enum.
    Scene-scoped threads are not processed here (they expire via age rules).

    Any arc thread NOT in advanced_ids is implicitly ignored.
    After 5 consecutive turns without being listed -> demote to latent (frees slot).
    Threads with progress >= _THREAD_COMPLETION_THRESHOLD (3) -> complete.
    Promote latent threads if slots available and 3-turn cooldown met.

    Unknown advanced_ids that match a latent thread promote it immediately
    (bypassing the cooldown), per ARCHITECTURE.md "Engine-Driven Arc: Thread Lifecycle".

    Returns a CampaignArc if any mutation occurred, None otherwise. Logs at WARNING
    level when arc validation fails so silent returns can be diagnosed.
    """
    arc_raw = state.get("arc")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.debug(
            "thread_signals: no arc in state at T%d, skipping",
            turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_signals: failed to validate arc at T%d: %s",
            turn_no, exc, extra={"turn": turn_no},
        )
        return None

    advanced_ids = set(progress_result.thread_advance or [])
    # Unified threads[] with scope-aware active bool
    all_arc_threads = [t for t in arc.threads if getattr(t, "scope", "arc") == "arc"]
    active_by_id: dict[str, ArcThread] = {t.id: t for t in all_arc_threads if getattr(t, "active", True)}
    latent_by_id: dict[str, ArcThread] = {t.id: t for t in all_arc_threads if not getattr(t, "active", False)}

    _log.debug(
        "thread_signals: T%d advanced_ids=%s active_count=%d latent_count=%d",
        turn_no, sorted(advanced_ids), len(active_by_id), len(latent_by_id),
    )

    mutated = False
    newly_completed: list[ArcThread] = []
    still_active: list[ArcThread] = []

    # Process each active thread -> advance or silently expire
    for tid, t in active_by_id.items():
        if tid in advanced_ids:
            new_progress = t.progress + 1
            updated_t = t.model_copy(update={
                "progress": new_progress,
                "last_seen_turn": turn_no,
            })

            # Check completion threshold
            if new_progress >= _THREAD_COMPLETION_THRESHOLD:
                newly_completed.append(updated_t)
                mutated = True
                _log.debug(
                    "thread_signals: T%d thread %s completed at progress=%d",
                    turn_no, tid, new_progress,
                )
            else:
                still_active.append(updated_t)
                mutated = True  # Advancing a thread is also a mutation
        elif t.last_seen_turn is None or (turn_no - t.last_seen_turn >= _EXPIRE_SILENT_TURNS):
            # Expired -> demote to latent, reset timer
            expired_t = t.model_copy(update={
                "active": False,
                "last_seen_turn": None,
            })
            still_active.append(expired_t)  # will be moved below
            mutated = True
            _log.debug(
                "thread_signals: T%d thread %s silently demoted (turn_no=%d last_seen=%s)",
                turn_no, tid, turn_no, t.last_seen_turn,
            )

    really_still_active = [t for t in still_active if getattr(t, "active", True)]
    demoted_to_latent = [t for t in still_active if not getattr(t, "active", False)]

    # Rebuild threads list with updated active/latent split
    other_threads = [t for t in arc.threads if t.id not in {tid for tid in all_arc_threads}]  # scene-scoped and completed threads
    new_complete_ids = {t.id for t in newly_completed}

    updated_threads: list[ArcThread] = []
    for t in arc.threads:
        if getattr(t, "scope", "arc") != "arc":
            # Scene-scoped thread -> keep as-is (not managed by this function)
            updated_threads.append(t)
        elif t.id in new_complete_ids:
            # Completed threads moved to completed_threads list
            pass  # will be added below via arc_update
        else:
            updated_threads.append(t)

    # Update the thread objects with their new active state
    for tid, t in active_by_id.items():
        if tid in {st.id for st in really_still_active}:
            for i, ut in enumerate(updated_threads):
                if ut.id == tid:
                    updated_threads[i] = [st for st in really_still_active if st.id == tid][0]
                    break

    # Build the arc update with new thread lists
    all_updated_arc_threads = list(really_still_active) + demoted_to_latent + other_threads
    
    # Find completed threads to move out of active/latent into completed
    for t in newly_completed:
        updated_threads = [ut for ut in updated_threads if ut.id != t.id]

    arc = arc.model_copy(update={
        "threads": all_updated_arc_threads,
        "completed_threads": list(arc.completed_threads) + newly_completed,
    })

    # Promote latent threads matching unknown advanced_ids (first-time advancement).
    # These IDs were emitted by the progress extractor but don't exist in active_by_id.
    for tid in advanced_ids - set(active_by_id.keys()):
        if tid in latent_by_id:
            promoted = latent_by_id[tid].model_copy(update={
                "active": True,
                "progress": 0,
                "last_seen_turn": turn_no,
                "urgency": "normal",
            })
            updated_threads = [t for t in all_updated_arc_threads if t.id != tid]
            really_still_active.append(promoted)
            mutated = True
            _log.debug(
                "thread_signals: T%d latent thread %s promoted to active (unknown advanced_id)",
                turn_no, tid,
            )

    # Promotion check: only if 3-turn cooldown met and slots available
    last_promotion = arc_raw.get("arc_last_promotion_turn") or 0
    can_promote = (turn_no - last_promotion >= _PROMOTION_COOLDOWN_TURNS) or len(really_still_active) == 0

    if can_promote:
        available_slots = _ACTIVE_THREAD_CAP - len(really_still_active)

        # Find eligible latent threads (no unlock_if or satisfied, excluding recently demoted)
        completed_ids = {t.id for t in arc.completed_threads}
        already_active_ids = {t.id for t in really_still_active}
        available = [
            t for t in all_updated_arc_threads
            if not getattr(t, "active", False)
            and t.id not in completed_ids
            and t.id not in already_active_ids
            and not (getattr(t, "unlock_if") and str(getattr(t, "unlock_if")).strip())
        ]

        # Sort by last_seen_turn or added_turn (oldest first) -> skip recently demoted ones
        available.sort(key=lambda t: t.added_turn or 0)

        to_promote = available[:available_slots]
        if to_promote:
            promoted = [
                t.model_copy(update={
                    "active": True,
                    "last_seen_turn": turn_no
                }) for t in to_promote
            ]
            updated_threads = [t for t in all_updated_arc_threads if t.id not in {p.id for p in to_promote}]
            arc = arc.model_copy(update={
                "threads": list(really_still_active) + promoted + updated_threads,
                "arc_last_promotion_turn": turn_no,
            })
            mutated = True

    return arc if mutated else None


def _candidate_to_latent_thread(
    arc: CampaignArc,
    candidate: str,
    turn_no: int,
) -> CampaignArc | None:
    """Convert a candidate_opportunity string into a latent thread with cap enforcement."""
    if not candidate or not candidate.strip():
        return None

    words = candidate.strip().split()[:5]
    base_id = "_".join(
        w.lower().strip(".,;:!?\"'") for w in words
    )
    existing_ids = {
        t.id for t in arc.threads + arc.completed_threads
    }
    tid = base_id if base_id not in existing_ids else f"{base_id}_t{turn_no}"
    if tid in existing_ids:
        return None

    new_thread = ArcThread(
        id=tid,
        summary=candidate.strip(),
        scope="arc",
        active=False,  # latent -> inactive
        urgency="background",
        tags=[_TACTICAL_TAG],
        added_turn=turn_no,
    )

    latent_threads = [t for t in arc.threads if not getattr(t, "active", True) and getattr(t, "scope", "arc") == "arc"]
    if len(latent_threads) >= _LATENT_CAP:
        tactical = [
            (i, t) for i, t in enumerate(latent_threads)
            if _TACTICAL_TAG in (t.tags or [])
        ]
        if not tactical:
            return None
        tactical.sort(key=lambda x: (x[1].added_turn or 0))
        evict_idx = tactical[0][0]
        latent_thread_obj = latent_threads[evict_idx]
        arc = arc.model_copy(update={
            "threads": [t for t in arc.threads if t.id != latent_thread_obj.id],
        })

    return arc.model_copy(update={"threads": list(arc.threads) + [new_thread]})  # type: ignore[no-any-return]


def _apply_thread_resolutions(
    state: dict[str, Any],
    progress_result: ProgressExtractResult,
) -> CampaignArc | None:
    """Process thread_resolve from ProgressExtractResult.

    Moves resolved/failed/abandoned threads from arc.threads[] to
    arc.completed_threads[], setting resolution_state on each.
    Handles missing IDs gracefully (warning + skip). Deduplicates
    completed_threads entries by updating existing entry instead of
    creating a duplicate.
    """
    if not progress_result.thread_resolve:
        return None

    arc_raw = state.get("arc")
    turn_no = state.get("meta", {}).get("turn", 0) + 1

    if not arc_raw:
        _log.debug(
            "thread_resolutions: no arc in state at T%d, skipping",
            turn_no, extra={"turn": turn_no},
        )
        return None

    try:
        arc = CampaignArc.model_validate(arc_raw)
    except Exception as exc:
        _log.warning(
            "thread_resolutions: failed to validate arc at T%d: %s",
            turn_no, exc, extra={"turn": turn_no},
        )
        return None

    # Build a map of existing completed threads by id for dedup
    completed_by_id: dict[str, ArcThread] = {}
    for ct in arc.completed_threads:
        if ct.id not in completed_by_id:
            completed_by_id[ct.id] = ct

    new_completed: list[ArcThread] = []
    any_found = False

    for res in progress_result.thread_resolve:
        # Find matching thread in arc.threads[]
        found_idx = None
        for i, t in enumerate(arc.threads):
            if getattr(t, "id", "") == res.id:
                found_idx = i
                break

        if found_idx is None:
            _log.warning(
                "thread_resolutions: T%d thread_resolve references unknown id=%s — skipping",
                turn_no, res.id, extra={"turn": turn_no},
            )
            continue

        any_found = True
        thread = arc.threads[found_idx]
        updated_thread = thread.model_copy(update={
            "resolution_state": res.resolution_state,
        })

        # Remove from threads[]
        remaining_threads = [t for i2, t in enumerate(arc.threads) if i2 != found_idx]

        # Dedup: update existing completed entry or collect new ones
        if thread.id in completed_by_id:
            updated_existing = thread.model_copy(update={
                "resolution_state": res.resolution_state,
            })
            remaining_completed = [
                t if t.id != thread.id else updated_existing
                for t in arc.completed_threads
            ]
        else:
            new_completed.append(updated_thread)
            remaining_completed = list(arc.threads)  # placeholder

    # Finalize completed threads with dedup
    final_completed_map: dict[str, ArcThread] = {}
    if any_found and 'remaining_completed' in dir():
        for ct in (remaining_completed or []):
            cid = getattr(ct, "id", "")
            if cid not in final_completed_map:
                final_completed_map[cid] = ct

    # Add new completions (deduped)
    for nc in new_completed:
        if nc.id not in final_completed_map:
            final_completed_map[nc.id] = nc

    # If no resolutions were found, keep original completed list
    if not any_found and 'remaining_completed' not in dir():
        final_completed_list = list(arc.completed_threads)
    else:
        final_completed_list = list(final_completed_map.values())

    mutated = any_found or bool(new_completed)

    return arc.model_copy(update={
        "threads": remaining_threads if any_found else list(arc.threads),
        "completed_threads": final_completed_list,
    }) if mutated else None


def _compute_narrative_velocity(
    deescalate: float,
    momentum: int,
    avoidance: bool,
    momentum_floor: int = -3,
    momentum_ceiling: int = 3,
) -> float:
    """Compute a signed pacing scalar in [-1.0, 1.0].

    Negative values signal de-escalation (breathe, slow down).
    Positive values signal escalation (pressure, urgency).
    Zero is neutral.

    Priority:
      1. Explicit de-escalation from a successful check beats everything.
      2. Avoidance keyword in player input nudges negative.
      3. Momentum outside floor/ceiling normalizes toward +/-0.5.
      4. Default: 0.0 (neutral, let pressure/beat directives govern).
    """
    if deescalate > 0:
        return -deescalate

    if avoidance:
        return -0.4

    span = momentum_ceiling - momentum_floor
    if span <= 0:
        return 0.0
    midpoint = (momentum_ceiling + momentum_floor) / 2.0
    normalized = (momentum - midpoint) / (span / 2.0)
    # Scale down -- momentum alone shouldn't dominate; caps at +/-0.5
    return max(-0.5, min(0.5, normalized * 0.5))


def _compute_narration_directive(
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
    threat_ages: list[dict[str, Any]],
    threat_pressure_at: int = 3,
    threat_imperative_at: int = 5,
    building_threat_imperative_at: int = 4,
) -> str:
    """Compute the narration directive string using a priority stack.

    Derives urgency counts from unified arc.threads[] with scope=scene.
    ArcThread.urgency values map to directives: urgent→Pressure/Overwhelm,
    background→Tension, normal→Threat Pressure (when aging).

    Returns the highest-priority directive. Secondary directives are appended
    only when they do not contradict the primary (i.e., no escalation labels
    when velocity is negative).

    Priority order (highest to lowest):
      1. Breathe       -- explicit de-escalation (velocity < -0.3)
      2. Overwhelm     -- 3+ urgent threads
      3. Resolve a Threat -- aged-out threat pressure
      4. Pressure      -- 1-2 urgent threads
      5. Tension       -- background urgency threads only
      6. Threat Pressure -- normal urgency aging toward imperative
      Secondary (non-contradicting append):
      7. Combat Fatigue -- combat_age >= 3
    """
    # Priority 1: breathe (de-escalation wins unconditionally)
    if narrative_velocity < -0.3:
        return "Breathe"

    secondary: list[str] = []

    # Priority 2: overwhelm (3+ urgent threads)
    immediate_count = sum(1 for t in scope_scene_threads if getattr(t, "urgency", "") == "urgent")
    if immediate_count >= 3:
        primary = "Overwhelm"
    else:
        primary = ""

    # Priority 3: aged-out threat (resolve a threat)
    if not primary and threat_ages:
        old_building = [
            t for t in threat_ages
            if t.get("urgency") == "normal" and t.get("age", 0) >= building_threat_imperative_at
        ]
        old_background = [
            t for t in threat_ages
            if t.get("urgency") == "background" and t.get("age", 0) >= threat_imperative_at
        ]
        old_immediate = [
            t for t in threat_ages
            if t.get("urgency") == "urgent" and t.get("age", 0) >= 3
        ]
        if old_building or old_background or old_immediate:
            primary = "Resolve a Threat"

    # Priority 4: pressure (1-2 urgent)
    if not primary and immediate_count > 0:
        primary = "Pressure"

    # Priority 5: tension (background only)
    if not primary:
        building_count = sum(1 for t in scope_scene_threads if getattr(t, "urgency", "") == "background")
        if building_count > 0:
            primary = "Tension"

    # Priority 6: threat pressure (normal urgency aging toward imperative)
    if not primary and threat_ages:
        background_pressure = [
            t for t in threat_ages
            if t.get("urgency") == "normal"
            and threat_pressure_at <= t.get("age", 0) < threat_imperative_at
        ]
        if background_pressure:
            primary = "Threat Pressure"

    # Secondary: combat fatigue (non-contradicting append)
    if ages.get("combat_age", 0) >= 3:
        secondary.append("Combat Fatigue")

    parts = [primary] if primary else []
    parts.extend(secondary)
    return "; ".join(parts)


def _compute_pacing_context(
    deescalate: float,
    narrative_velocity: float,
    scope_scene_threads: list["ArcThread"],
    ages: dict[str, int],
    threat_ages: list[dict[str, Any]] | None,
    pending_beat: dict[str, Any] | None,
    momentum: int,
    config: "EngineConfig",
) -> PacingContext:
    """Compute unified pacing context for Narrate and Progress steps.

    Derives urgency from unified arc.threads[] with scope=scene instead of
    raw scene_pressure dicts. Replaces separate deescalate/narrative_velocity
    signals with a single authoritative struct containing directive, beat_hint,
    beat_locked, gate, summary.
    """
    # Compute directive using existing logic
    directive = _compute_narration_directive(
        narrative_velocity=narrative_velocity,
        scope_scene_threads=scope_scene_threads,
        ages=ages,
        threat_ages=threat_ages or [],
        threat_pressure_at=config.threat_pressure_at,
        threat_imperative_at=config.threat_imperative_at,
        building_threat_imperative_at=config.building_threat_imperative_at,
    )

    # Determine beat_hint: suggest a type when there's a pending beat
    beat_hint = None
    if pending_beat and isinstance(pending_beat, dict) and pending_beat.get("type"):
        beat_type = pending_beat.get("type") or "pressure"
        surface_as = pending_beat.get("surface_as", "ambient")
        beat_hint = f"{beat_type} ({surface_as})"

    # Determine beat_locked: floor relief fired when momentum is at minimum
    beat_locked = False
    if momentum <= config.momentum_floor:
        beat_locked = True
        directive_parts = [directive] if directive else []
        if "Combat Fatigue" not in (directive or ""):
            directive_parts.append("Resolve a Threat")
        directive = "; ".join(directive_parts) or ""

    # Determine gate: block_add when deescalation is strong (pressure just resolved)
    gate: Literal["block_add", "block_escalate", "allow"] = "allow"
    if deescalate >= 0.5:
        gate = "block_escalate"

    # Build summary for logging
    parts = [directive] if directive else []
    if beat_hint:
        parts.append(f"beat_hint={beat_hint}")
    if beat_locked:
        parts.append("locked")
    summary = ", ".join(parts) or "neutral"

    return PacingContext(
        directive=directive or "",
        beat_hint=beat_hint,
        beat_locked=beat_locked,
        gate=gate,
        summary=summary,
    )


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


def _compute_threat_ages(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Compute age of each scene-scoped arc thread for threat imperative directives.

    Returns a list of dicts with keys: id, text, urgency, age.
    Only includes threads with a valid added_turn (> 0).
    """
    threads = [t for t in ((state.get("arc") or {}).get("threads") or []) if isinstance(t, dict) and t.get("scope") == "scene"]
    current_turn = (state.get("meta") or {}).get("turn", 0)
    result: list[dict[str, Any]] = []
    for t in threads:
        added_turn = t.get("added_turn") or t.get("last_seen_turn")
        if not added_turn or added_turn == 0:
            continue
        result.append({
            "id": t.get("id", ""),
            "text": t.get("summary", ""),
            "urgency": t.get("urgency", "background"),
            "age": current_turn - added_turn,
        })
    # Sort by age descending so the oldest threat is first
    result.sort(key=lambda x: x["age"], reverse=True)
    return result


_LOCATION_PRESSURE_ID = "_engine_location_stale"


def _inject_location_pressure(
    ages: dict[str, int],
    existing_pressure: list[dict[str, Any]],
    location_pressure_at: int = 3,
    location_imperative_at: int = 5,
) -> list[dict[str, Any]]:
    """Return a new pressure list with a synthetic location staleness entry if warranted.

    Does not mutate the input list. Returns a new list.
    The synthetic entry is never persisted to state (turn_added=0 signals engine-generated).
    """
    location_age = ages.get("location_age", 0)
    filtered = [p for p in existing_pressure if p.get("id") != _LOCATION_PRESSURE_ID]
    if location_age <= location_pressure_at:
        return filtered

    urgency = "immediate" if location_age > location_imperative_at else "building"
    synthetic = {
        "id": _LOCATION_PRESSURE_ID,
        "text": "The scene has lingered here too long — move it along.",
        "urgency": urgency,
        "turn_added": 0,
    }
    return filtered + [synthetic]


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
    pack_narrator_rules: list[str] = [],
    pack_world_rules: list[str] = [],
    pack_factions: list[dict[str, str]] = [],
    pack_locations: list[dict[str, str]] = [],
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

        # Avoidance detection: flag de-escalation intent in player input
        _avoidance_kw = config.avoidance_keywords
        _input_lower = (user_input or "").lower()
        avoidance = any(kw in _input_lower for kw in _avoidance_kw)
        if avoidance:
            _log.debug(
                "pacing: avoidance detected in input",
                extra={"turn": state.get("meta", {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "pacing"},
            )

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

        # Get last turn's outcome_summary for rules context
        _prev_outcome = ""
        if turn_no > 1:
            _prev_events = load_recent_events(save_dir, 1)
            if _prev_events:
                _prev_outcome = _prev_events[0].get("rules", {}).get("outcome_summary", "")

        _present_npcs = list((state.get("scene") or {}).get("present_npcs") or [])
        rules_messages = _rules_messages(
            env, state, user_input,
            recent_turns=recent_turns[-1:],
            turn_no=turn_no,
            present_npcs=_present_npcs,
            last_outcome=_prev_outcome if _prev_outcome else None,
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
            momentum_before = state.get("pc", {}).get("momentum", 0)
            apply_momentum(state, outcome.band)
            momentum_after = state.get("pc", {}).get("momentum", 0)

        # De-escalation magnitude: success on a scene with active pressure
        deescalate: float = 0.0
        if config and config.thread_deescalate_on_success:
            if (
                outcome.rolled
                and outcome.band in ("success", "crit_success")
                and any(
                    t.get("urgency") in ("immediate", "building")
                    for t in ((state.get("arc") or {}).get("threads") or [])
                    if isinstance(t, dict) and t.get("scope") == "scene"
                )
            ):
                deescalate = 1.0 if outcome.band == "crit_success" else 0.6

        # Age counters for narration directives
        ages = _compute_ages(state)
        threat_ages = _compute_threat_ages(state)

        if config.log_prompts:
            _log_rules_outcome(
                state.get("meta", {}).get("turn", 0) + 1, intent, outcome
            )

        rules_ms = (asyncio.get_event_loop().time() - t_rules) * 1000
        rules_metrics = {
            "total_ms": round(rules_ms, 1),
            "rolled": outcome.rolled,
            "tokens_in": rules_usage.get("prompt_tokens", 0),
            "tokens_out": rules_usage.get("completion_tokens", 0),
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

        # Read resolved pressures from previous turn's purge/expire
        _resolved_pressures = (state.get("meta") or {}).get("resolved_pressures_last_turn")

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

        _pc_allegiance = (state.get("pc") or {}).get("allegiance")
        _pack_narrator_rules = pack_narrator_rules if pack_narrator_rules else []
        _pack_world_rules = pack_world_rules if pack_world_rules else []
        _world_factions = pack_factions if pack_factions else []
        _world_locations = pack_locations if pack_locations else []

        # Compute unified pacing scalar
        narrative_velocity = _compute_narrative_velocity(
            deescalate=deescalate,
            momentum=(state.get("pc") or {}).get("momentum", 0),
            avoidance=avoidance,
            momentum_floor=config.momentum_floor,
            momentum_ceiling=config.momentum_ceiling,
        )

        _raw_thread_dicts = [t for t in (state.get("arc") or {}).get("threads") or [] if isinstance(t, dict) and t.get("scope") == "scene"]

        # Convert raw thread dicts to ArcThread objects for computation functions
        _scope_scene_threads: list[ArcThread] = []
        for td in _raw_thread_dicts:
            try:
                _scope_scene_threads.append(ArcThread.model_validate(td))
            except Exception:
                pass  # skip malformed entries

        _effective_pressure = _inject_location_pressure(
            ages=ages,
            existing_pressure=_raw_thread_dicts,
            location_pressure_at=config.location_pressure_at,
            location_imperative_at=config.location_imperative_at,
        )

        # Compute unified pacing context (replaces separate directive computation)
        _pc = _compute_pacing_context(
            deescalate=deescalate,
            narrative_velocity=narrative_velocity,
            scope_scene_threads=_scope_scene_threads,
            ages=ages,
            threat_ages=threat_ages,
            pending_beat=_pending_gm_beat,
            momentum=(state.get("pc") or {}).get("momentum", 0),
            config=config,
        )

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
            pending_beat=_pending_gm_beat,
            pacing_context=_pc,
            ages=ages,
            known_npcs=_known_npcs,
            present_npcs=_present_npcs,
            compendium_bios=_compendium_bios,
            pc_allegiance=_pc_allegiance,
            scene_pressure=_effective_pressure,
            turn_no=turn_no,
            world_factions=_world_factions,
            world_locations=_world_locations,
            threat_ages=threat_ages,
            threat_pressure_at=config.threat_pressure_at,
            threat_imperative_at=config.threat_imperative_at,
            building_threat_imperative_at=config.building_threat_imperative_at,
            resolved_pressures=_resolved_pressures,
            npc_roster=build_npc_roster(
                present_npcs=_present_npcs,
                known_npcs=_known_npcs,
                recently_left=(state.get("scene") or {}).get("recently_left", []),
            ),
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
        first_visible = True
        async for chunk in llm_chat_stream(
            config.host,
            config.model,
            narr_messages,
            temperature=config.narrate_temperature,
            timeout=float(config.request_timeout_s),
            stream_stats=narr_stream_stats,
        ):
            narrative_chunks.append(chunk)
            if first_visible:
                first_ms = (asyncio.get_event_loop().time() - t0) * 1000
                first_visible = False
                yield ("phase", {"phase": "narrate_first_token", "first_token_ms": round(first_ms, 1)})
            yield ("token", chunk)

        narr_ms = (asyncio.get_event_loop().time() - t0) * 1000
        narrative = strip_thinking("".join(narrative_chunks))
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

        # Save beat before clearing so extraction pipeline can see it
        _beat_before_narration = (state.get("meta") or {}).get("pending_gm_beat")

        # Clear pending_gm_beat after narration consumed it
        state.setdefault("meta", {})["pending_gm_beat"] = None

        # === Extraction pipeline (3 streams) ===
        # Restore beat so progress extractor sees it in prompt for disposition decision
        if _beat_before_narration is not None:
            state.setdefault("meta", {})["pending_gm_beat"] = _beat_before_narration

        exp_ms = _avg_extract_ms(save_dir)
        yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
        t2 = asyncio.get_event_loop().time()

        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}

        _extract_result = None
        try:
            async for _evt in _run_extraction_pipeline(
                env, state, narrative,
                rules_outcome=outcome,
                intent=intent,
                config=config,
                trace_id=trace_id,
                turn_no=turn_no,
                pacing_context=_pc,
                recent_turns=recent_turns,
            ):
                if isinstance(_evt, tuple) and len(_evt) == 2 and _evt[0] == "phase":
                    yield _evt
                else:
                    _extract_result = _evt
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})

        if _extract_result is not None:
            delta, actions, outcome_summary, extraction_event, progress_result, scene_result = _extract_result  # type: ignore[misc]
            # Beat lifecycle: beat_disposition removed — Python infers from state mutations (gm_beat presence in delta)
            _new_beat = progress_result.gm_beat if progress_result else None

            if _new_beat and _new_beat.type:
                # New beat present → replace/clear pending_gm_beat with new value
                # Replace or fresh write (includes implicit replace when carry+new_beat)
                _beat_dict = _new_beat.model_dump(exclude_none=True)
                _beat_dict["beat_expires_turn"] = turn_no + 2
                state.setdefault("meta", {})["pending_gm_beat"] = _beat_dict
            else:
                # consume or no new beat — clear
                state.setdefault("meta", {})["pending_gm_beat"] = None

        yield ("phase", {"phase": "extract_done"})

        # Condition age pass: decrement turns_remaining, remove expired
        updated_conds = []
        for c in (state.get("pc") or {}).get("conditions") or []:
            tr = c.get("turns_remaining")
            if tr is None:
                # Permanent condition — do not age
                updated_conds.append(c)
                continue
            new_remaining = tr - 1
            if new_remaining <= 0:
                append_event(save_dir, {
                    "kind": "condition_expired",
                    "condition_id": c.get("id"),
                    "turn": turn_no,
                })
                # do not append — condition removed
            else:
                updated_conds.append({**c, "turns_remaining": new_remaining})

        (state.setdefault("pc", {})["conditions"])[:] = updated_conds

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

            reconcile_warnings = reconcile_delta(state, delta)
            for w in reconcile_warnings:
                _log.warning("[reconcile] turn %s: %s", state.get("meta", {}).get("turn", "?"), w, extra={"trace_id": trace_id})
            state, recent_events_evicted = apply_delta(
                state, delta,
                recent_events_max=config.recent_events_max,
                current_turn_no=turn_no,
            )
            # Add floor relief check after momentum is updated by apply_delta
            _check_floor_relief(state, config, outcome.band if outcome.rolled else "")
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
                }

            # Arc director: process thread signals and update arc state
            if state.get("arc") and progress_result:
                arc_delta = _apply_thread_signals(state, progress_result)
                if arc_delta is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), arc_delta
                    )
                    if delta is not None:
                        delta = delta.model_copy(
                            update={"arc_update": arc_delta}
                        )

                # Process thread resolutions (resolved/failed/abandoned -> completed)
                resolved_arc = _apply_thread_resolutions(state, progress_result)
                if resolved_arc is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), resolved_arc
                    )
                    if delta is not None:
                        delta = delta.model_copy(
                            update={"arc_update": resolved_arc}
                        )

                # Handle thread_add as new arc thread (only when gate == "allow")
                if progress_result.thread_add:
                    _new_thread = progress_result.thread_add
                    _scope = getattr(_new_thread, "scope", "arc")
                    if _scope == "scene":
                        # Scene-scoped threads are handled by age rules in Python, not here
                        pass

        narrative = _strip_fallback(narrative, trace_id=trace_id, turn=turn_no)

        # Extract narrator arc_update block if present
        narrative, narrator_arc_dict = _extract_narrator_arc_update(narrative)
        if narrator_arc_dict:
            try:
                narrator_arc_update = CampaignArc.model_validate(narrator_arc_dict)
                if delta is not None:
                    _merge_arc_update(
                        state.setdefault("arc", {}), narrator_arc_update
                    )
                    merged = narrator_arc_update.model_copy(
                        update={
                            "threads": (delta.arc_update.threads if delta.arc_update else None),
                            "completed_threads": (delta.arc_update.completed_threads if delta.arc_update else None),
                        }
                    )
                    delta = delta.model_copy(
                        update={"arc_update": merged}
                    )
            except Exception:
                _log.warning(
                    "narrator emitted invalid arc_update JSON — discarded",
                    extra={"turn": turn_no, "trace_id": trace_id},
                )

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
                "momentum_before": momentum_before,
                "momentum_after": momentum_after,
                "momentum_delta": momentum_after - momentum_before,
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
            state, compaction_ran = await maybe_compact(save_dir, state, config, trace_id=trace_id)
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


_FALLBACK_SENTINEL = "*That action didn't resolve as expected"


def _strip_fallback(narration: str, *, trace_id: str, turn: int) -> str:
    log = logging.getLogger(__name__)
    lines = narration.splitlines()
    clean = [ln for ln in lines if not ln.strip().startswith(_FALLBACK_SENTINEL)]
    if len(clean) < len(lines):
        log.warning(
            "Fallback message stripped from narration",
            extra={"trace_id": trace_id, "turn": turn},
        )
    return "\n".join(clean)


_ARC_UPDATE_RE = re.compile(
    r"<<<ARC_UPDATE_START>>>\s*(.*?)\s*<<<ARC_UPDATE_END>>>",
    re.DOTALL,
)


def _extract_narrator_arc_update(raw: str) -> tuple[str, dict[str, Any] | None]:
    """Strip arc_update block from narrator output.

    Returns (clean_text, arc_dict|None). If no block found, returns (raw, None).
    If block found but JSON is malformed, returns (clean_text, None).
    """
    match = _ARC_UPDATE_RE.search(raw)
    if not match:
        return raw, None
    clean = _ARC_UPDATE_RE.sub("", raw).rstrip()
    try:
        arc_dict = json.loads(match.group(1))
    except Exception:
        arc_dict = None
    return clean, arc_dict


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
        item = inv_by_id.get(canonical)
        if item and int(item.get("amount") or 0) == 0:
            rejections.append(
                {
                    "field": "inventory_remove",
                    "kind": "zero_balance",
                    "value": canonical,
                    "reason": f"Item '{canonical}' has zero balance",
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

    return rejections


def _check_floor_relief(
    state: dict[str, Any], config: EngineConfig, band: str
) -> None:
    """Check momentum floor and inject breathing_room beat if relief conditions met.

    Tracks consecutive floor turns via state["meta"]["consecutive_floor_count"].
    Resets counter on any non-floor momentum or success/crit_success band.
    """
    floor = config.momentum_floor
    relief_threshold = config.momentum_floor_relief_turns
    cur_momentum = (state.get("pc") or {}).get("momentum", 0)
    meta = state.setdefault("meta", {})

    if cur_momentum != floor:
        meta["consecutive_floor_count"] = 0
        return

    if band in ("success", "crit_success"):
        meta["consecutive_floor_count"] = 0
        return

    count = int(meta.get("consecutive_floor_count", 0)) + 1
    meta["consecutive_floor_count"] = count

    if (
        count >= relief_threshold
        and meta.get("pending_gm_beat") is None
    ):
        meta["pending_gm_beat"] = {
            "type": "breathing_room",
            "surface_as": "ambient",
            "beat_expires_turn": (state.get("meta") or {}).get("turn", 0) + 3,
        }
        _log.info(
            "pacing: injecting breathing_room beat (floor=%d, consecutive=%d)",
            cur_momentum, count,
            extra={"turn": (state.get("meta") or {}).get("turn", 0), "trace_id": "", "pack": "", "kind": "pacing"},
        )


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
