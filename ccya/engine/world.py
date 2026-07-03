"""World step: async beat-candidate generation after turn completion."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from jinja2 import Environment
from pydantic import ValidationError

from ccya.engine.config import EngineConfig, _render
from ccya.engine._pacing import derive_allowed_beat_types
from ccya.engine.npc_roster import build_npc_roster
from ccya.llm_client import chat as llm_chat
from ccya.models import GMBeat, WorldState

_log = logging.getLogger(__name__)


async def _run_world_step(
    env: Environment,
    state: WorldState,
    narration: str,
    pacing_context: Any | None,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
) -> tuple[list[dict[str, Any]], str, str, str, dict[str, int]]:
    """Generate 2-3 candidate GM beats for the next turn.

    Returns (beat_candidates, system_text, user_text, raw_response, usage).
    beat_candidates is a list of validated beat dicts (model_dump shape).
    system_text and user_text are the rendered template strings.
    raw_response is the raw LLM response text.
    usage is a dict with tokens_in and tokens_out.
    On any failure, returns ([], system_text, user_text, "", {"tokens_in": 0, "tokens_out": 0}).
    """
    recent_beats = list(state.meta.recent_beats or [])
    scene_phase = state.scene.scene_phase or "SETUP"

    comp = state.compendium.npcs or {}
    npc_roster = build_npc_roster(comp, turn_no=turn_no)
    # Only include present NPCs in beat generation to avoid re-injecting nearby NPCs
    # that should be decaying. Nearby NPCs are excluded from beats to prevent the
    # feedback loop: beats -> narration -> extractor re-promotion -> beats for present.
    npc_roster = [n for n in npc_roster if n.get("presence") == "present"]

    pc_directive = state.pc.situation.get("directive", "") if isinstance(state.pc.situation, dict) else ""
    allowed_beat_types = derive_allowed_beat_types(
        scene_phase,
        directive=pc_directive,
    )

    rules_outcome_dict: dict[str, Any] = {}
    rules_outcome = state.meta.last_rules_outcome or {}
    if isinstance(rules_outcome, dict):
        rules_outcome_dict = {
            "band": rules_outcome.get("band", ""),
            "rolled": bool(rules_outcome.get("rolled", False)),
        }

    arc = state.long_term_objective.model_dump()

    system_text = _render(env, "world_system.j2", {})
    user_text = _render(
        env,
        "world_user.j2",
        {
            "npc_roster": npc_roster,
            "arc": arc,
            "pacing_context": pacing_context,
            "recent_beats": recent_beats,
            "allowed_beat_types": allowed_beat_types,
            "rules_outcome": rules_outcome_dict,
            "narration": narration,
        },
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]

    try:
        _log.debug("world.step_start trace_id=%s turn=%d npc_roster=%d", trace_id, turn_no, len(npc_roster))
        _log.debug("world.step_before_llm trace_id=%s turn=%d host=%s model=%s timeout=%.1f", trace_id, turn_no, config.host, config.model, 60.0)
        async with asyncio.timeout(60.0):
            result = await llm_chat(
                config.host,
                config.model,
                messages,
                fallback_host=config.fallback_host,
                fallback_model=config.fallback_model,
                fallback_cooldown_s=config.fallback_cooldown_s,
                temperature=config.world_temperature,
                top_p=config.extract_top_p,
                timeout=60.0,  # asyncio.timeout() handles wall-clock timeout
                num_ctx=config.num_ctx,
            )
        _log.debug("world.step_llm_complete trace_id=%s turn=%d", trace_id, turn_no)
    except TimeoutError:
        _log.warning(
            "world LLM call timed out after 60s",
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        _log.debug("world.step_failed trace_id=%s turn=%d error=timeout", trace_id, turn_no)
        return [], system_text, user_text, "", {"tokens_in": 0, "tokens_out": 0}
    except asyncio.CancelledError:
        _log.warning(
            "world LLM call cancelled",
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        _log.debug("world.step_failed trace_id=%s turn=%d error=cancelled", trace_id, turn_no)
        return [], system_text, user_text, "", {"tokens_in": 0, "tokens_out": 0}
    except Exception as exc:
        _log.warning(
            "world LLM call failed: %s", exc,
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        _log.debug("world.step_failed trace_id=%s turn=%d error=%s", trace_id, turn_no, exc)
        return [], system_text, user_text, "", {"tokens_in": 0, "tokens_out": 0}

    raw = result.content
    usage = result.usage
    tokens_in = int(usage.get("prompt_tokens", 0))
    tokens_out = int(usage.get("completion_tokens", 0))
    candidates_raw = _parse_candidate_array(raw)
    if candidates_raw is None:
        _log.warning(
            "world: no valid JSON array in response",
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        _log.debug("world.step_no_json trace_id=%s turn=%d", trace_id, turn_no)
        return [], system_text, user_text, raw, {"tokens_in": tokens_in, "tokens_out": tokens_out}

    valid_beats: list[dict[str, Any]] = []
    seen_effects: set[str] = set()
    for entry in candidates_raw:
        if not isinstance(entry, dict):
            continue
        try:
            beat = GMBeat(**entry)
        except ValidationError:
            continue
        if not beat.type:
            continue
        if beat.type not in allowed_beat_types:
            _log.warning(
                "world.beat_phase_violation type=%s phase=%s allowed=%s",
                beat.type, scene_phase, allowed_beat_types,
                extra={"trace_id": trace_id, "turn": turn_no},
            )
            continue
        # Filter out beats that duplicate recent beats (semantic similarity)
        effect_lower = beat.effect.lower().strip()
        is_duplicate = False
        for rb in recent_beats:
            rb_effect = (rb.get("effect") or "").lower().strip()
            if rb_effect and (effect_lower == rb_effect or effect_lower[:150] == rb_effect[:150]):
                is_duplicate = True
                _log.debug(
                    "world.beat_dedup type=%s turn=%d effect=%s",
                    beat.type, turn_no, beat.effect[:60],
                    extra={"trace_id": trace_id},
                )
                break
            # Also catch beats sharing first 5 words (semantic duplicate)
            if not is_duplicate and rb_effect:
                rb_words = rb_effect.split()[:5]
                eff_words = effect_lower.split()[:5]
                if rb_words and rb_words == eff_words and len(rb_words) == 5:
                    is_duplicate = True
                    _log.debug(
                        "world.beat_dedup_words type=%s turn=%d effect=%s words=%s",
                        beat.type, turn_no, beat.effect[:60], rb_words,
                        extra={"trace_id": trace_id},
                    )
                    break
        # Also filter out beats that duplicate other candidates in this batch
        if not is_duplicate and effect_lower in seen_effects:
            is_duplicate = True
            _log.debug(
                "world.beat_dedup_batch type=%s turn=%d effect=%s",
                beat.type, turn_no, beat.effect[:60],
                extra={"trace_id": trace_id},
            )
        if is_duplicate:
            continue
        seen_effects.add(effect_lower)
        valid_beats.append({"type": beat.type, "effect": beat.effect, "npcs": entry.get("npcs", [])})
        if len(valid_beats) >= 3:
            break

    # Append all generated beats to recent_beats for diversity tracking
    # (not just selected beats — unselected beats should still be tracked to avoid repetition)
    for vb in valid_beats:
        state = state.add_recent_beat(
            {"turn": turn_no, "type": vb.get("type"), "effect": vb.get("effect", "")},
            max_size=config.recent_beats_max,
        )

    _log.debug("world.step_complete trace_id=%s turn=%d valid_beats=%d", trace_id, turn_no, len(valid_beats))
    return valid_beats, system_text, user_text, raw, {"tokens_in": tokens_in, "tokens_out": tokens_out}


def _parse_candidate_array(raw: str) -> list[dict[str, Any]] | None:
    """Extract a JSON array of candidate beat dicts from the LLM response."""
    text = raw.strip()
    if not text:
        return None

    def _try(t: str) -> Any:
        try:
            return json.loads(t)
        except (json.JSONDecodeError, ValueError):
            return None

    parsed = _try(text)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("beats", "candidates", "beat_candidates"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value

    if "```" in text:
        for part in text.split("```"):
            p = part.strip()
            if p.lower().startswith("json"):
                p = p[4:].strip()
            r = _try(p)
            if isinstance(r, list):
                return r
            if isinstance(r, dict):
                for key in ("beats", "candidates", "beat_candidates"):
                    value = r.get(key)
                    if isinstance(value, list):
                        return value

    return None
