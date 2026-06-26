"""World step: async beat-candidate generation after turn completion."""

from __future__ import annotations

import json
import logging
from typing import Any

from jinja2 import Environment
from pydantic import ValidationError

from ccya.engine.config import EngineConfig, _render
from ccya.engine._pacing import derive_allowed_beat_types
from ccya.llm_client import chat as llm_chat
from ccya.models import GMBeat

_log = logging.getLogger(__name__)


async def _run_world_step(
    env: Environment,
    state: dict[str, Any],
    narration: str,
    scene_result: Any | None,
    pacing_context: Any | None,
    config: EngineConfig,
    trace_id: str,
    turn_no: int,
) -> list[dict[str, Any]]:
    """Generate 2-3 candidate GM beats for the next turn.

    Returns a list of validated beat dicts (model_dump shape), or [] on any failure.
    """
    candidate_npcs: list[dict[str, Any]] = []
    if scene_result is not None:
        candidate_npcs = list(getattr(scene_result, "candidate_npcs", None) or [])

    arc = state.get("arc") or {}
    recent_beats = list((state.get("meta") or {}).get("recent_beats", []) or [])
    scene_phase = (state.get("scene") or {}).get("scene_phase", "SETUP")

    allowed_beat_types = derive_allowed_beat_types(
        scene_phase,
        directive=pacing_context.directive if pacing_context else "",
        spiral_detected=pacing_context.spiral_detected if pacing_context else False,
    )

    rules_outcome_dict: dict[str, Any] = {}
    rules_outcome = (state.get("meta") or {}).get("last_rules_outcome") or {}
    if isinstance(rules_outcome, dict):
        rules_outcome_dict = {
            "band": rules_outcome.get("band", ""),
            "rolled": bool(rules_outcome.get("rolled", False)),
        }

    system_text = _render(env, "world_system.j2", {})
    user_text = _render(
        env,
        "world_user.j2",
        {
            "candidate_npcs": candidate_npcs,
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
        result = await llm_chat(
            config.host,
            config.model,
            messages,
            temperature=config.world_temperature,
            top_p=config.extract_top_p,
            timeout=float(config.request_timeout_s),
        )
    except Exception as exc:
        _log.warning(
            "world LLM call failed: %s", exc,
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        return []

    raw = result.get("response", "") if isinstance(result, dict) else ""
    candidates_raw = _parse_candidate_array(raw)
    if candidates_raw is None:
        _log.warning(
            "world: no valid JSON array in response",
            extra={"trace_id": trace_id, "turn": turn_no},
        )
        return []

    valid_beats: list[dict[str, Any]] = []
    for entry in candidates_raw:
        if not isinstance(entry, dict):
            continue
        try:
            beat = GMBeat(**entry)
        except ValidationError:
            continue
        if not beat.type:
            continue
        valid_beats.append(beat.model_dump(exclude_none=True))
        if len(valid_beats) >= 3:
            break

    return valid_beats


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
