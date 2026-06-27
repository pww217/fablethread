"""Turn pipeline dataclasses: TurnContext and PacingContext."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig
from ccya.models import IntentEnvelope, RulesOutcome


@dataclass
class TurnContext:
    """Shared context across run_turn phases."""
    state: dict[str, Any]
    user_input: str
    turn_no: int
    trace_id: str
    config: EngineConfig
    recent_turns: list[dict[str, Any]]
    save_dir: Path
    packing: dict[str, Any]

    # Internal tracking (set during setup, consumed by phases)
    _env: Any = None  # Jinja env built in run_turn
    _rendered_ruling_system: str = ""
    _rendered_ruling_user: str = ""
    _ruling_raw_response: str = ""
    _ruling_parse_error: str | None = None
    _ruling_trimmed: bool = False
    _ruling_trimmed_chars: int = 0
    _ages: dict[str, int] = field(default_factory=dict)  # set by ruling phase before narrate setup reads it

    intent: IntentEnvelope | None = None
    outcome: RulesOutcome | None = None
    _spiral_detected: bool = False


@dataclass
class PacingContext:
    """Consolidated pacing decision for Narrate and Progress steps."""
    directive: str  # "Scene Imperative" | "Scene Pressure" | ""
    outcome_hint: str | None  # narrator's primary scene motion instruction
    summary: str  # human-readable log string, never sent to LLM
    spiral_detected: bool = False  # death spiral flag from recent roll history
    convergence_score: int = 0  # convergence score for RISING→CLIMAX transition (6 components + stall_floor)
    convergence_components: dict[str, int] = field(default_factory=dict)
