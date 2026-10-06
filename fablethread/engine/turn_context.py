"""Turn pipeline dataclasses: TurnContext and PacingContext."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from jinja2 import Environment
from pathlib import Path
from typing import Any

from fablethread.engine.config import EngineConfig
from fablethread.models import IntentEnvelope, RulesOutcome, WorldState


def _is_cancel_requested(ctx: TurnContext) -> bool:
    return ctx._cancel_event is not None and ctx._cancel_event.is_set()


@dataclass
class TurnContext:
    """Shared context across run_turn phases."""
    state: WorldState
    user_input: str
    turn_no: int
    trace_id: str
    config: EngineConfig
    recent_turns: list[dict[str, Any]]
    save_dir: Path
    packing: dict[str, Any]

    # Internal tracking (set during setup, consumed by phases)
    _env: Environment | None = None  # Jinja env built in run_turn
    _rendered_ruling_system: str = ""
    _rendered_ruling_user: str = ""
    _ruling_raw_response: str = ""
    _ruling_parse_error: str | None = None
    _ruling_trimmed: bool = False
    _ruling_trimmed_chars: int = 0
    _ages: dict[str, int] = field(default_factory=dict)  # set by ruling phase before narrate setup reads it
    _cancel_event: asyncio.Event | None = None

    intent: IntentEnvelope | None = None
    outcome: RulesOutcome | None = None

    _selected_beat: Any = None


@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str  # "Scene Imperative" | "Scene Pressure" | ""
    outcome_hint: str | None  # narrator's primary scene motion instruction
    summary: str  # human-readable log string, never sent to LLM

    convergence_score: int = 0  # convergence score for RISING→CLIMAX transition (6 components, EMA smoothed)
    convergence_components: dict[str, int] = field(default_factory=dict)
    convergence_threads: list[dict[str, Any]] = field(default_factory=list)  # threads used for convergence computation
