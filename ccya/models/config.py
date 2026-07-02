"""Config types and TurnResult dataclass."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

from ccya.models.state import WorldState

_log = logging.getLogger(__name__)

SkillName = Literal["strength", "dexterity", "wits", "charisma"]
Difficulty = Literal["trivial", "easy", "normal", "hard", "extreme"]
Band = Literal[
    "crit_fail", "fail", "setback", "partial", "success", "crit_success"
]


@dataclass
class TurnResult:
    turn: int
    trace_id: str
    narrative: str
    state_delta: dict[str, Any]
    applied: dict[str, Any] = field(default_factory=dict)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    diff: list[str] = field(
        default_factory=list
    )  # short human-readable delta lines for UI toast
    changes: dict[str, Any] = field(
        default_factory=dict
    )  # structured pre/post diff for modal + log
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    ruling: dict[str, Any] = field(
        default_factory=dict
    )  # serialized RulesOutcome + intent for logging/UI
    outcome_summary: str = field(default="")
    outcome_hint: str | None = None
    scene_phase: str = field(default="")
    summary: str = field(default="")
    ts: str = field(default="")
    state_snapshot: WorldState = field(default_factory=WorldState)


def load_config(path: str | os.PathLike[str] = "config.yaml") -> dict[str, Any]:
    _log.debug("loading model config from %s", path)
    with open(path) as f:
        result = yaml.safe_load(f)
        if isinstance(result, dict):
            return result
        raise ValueError("config.yaml must contain a mapping at top level")


def save_config(
    path: str | os.PathLike[str] = "config.yaml",
    config_dict: dict[str, Any] | None = None,
) -> None:
    """Write a config dict to YAML. Atomic via tmp + rename."""
    if config_dict is None:
        config_dict = load_config(path)
    path = Path(path).resolve()
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
    tmp_path.replace(path)
