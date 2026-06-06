"""Pydantic models for LLM structured output and config."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

_log = logging.getLogger(__name__)

SkillName = Literal["strength", "dexterity", "wits", "charisma"]
Difficulty = Literal["trivial", "easy", "normal", "hard", "extreme"]
Band = Literal[
    "crit_fail", "fail", "setback", "partial", "success", "crit_success"
]


class NpcPresence(str, Enum):
    PRESENT = "present"
    NEARBY = "nearby"
    KNOWN = "known"


class ArcThread(BaseModel):
    model_config = {"extra": "ignore"}

    id: str
    summary: str
    scope: Literal["scene", "arc"]
    active: bool = True
    urgency: Literal["background", "normal", "urgent"] = "normal"
    progress: list[str] = []
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None

    @field_validator("progress", mode="wrap")
    @classmethod
    def _coerce_progress(cls, v: Any, handler: Any) -> Any:
        if isinstance(v, str):
            return [v]
        if not v or (isinstance(v, int) and v == 0):
            return []
        return handler(v)


class CampaignArc(BaseModel):
    model_config = {"extra": "ignore"}
    visible_goal: str = ""
    goal_context: str = ""
    threads: list[ArcThread] = Field(default_factory=list)
    completed_threads: list[ArcThread] = Field(default_factory=list)
    resolution: str | None = None
    last_thread_created_turn: int = 0

class Condition(BaseModel):
    id: str
    label: str
    description: str = ""
    added_turn: int = 0
    turns_remaining: int | None = None


def _coerce_condition_str(v: Any) -> Any:
    if isinstance(v, str):
        cid = v.lower().strip().replace(" ", "_")
        for ch in ("*", "_", "`", ".", ",", ";", ":", "!", "?"):
            cid = cid.replace(ch, "")
        cid = "_".join(cid.split()) or "condition"
        return {"id": cid, "label": v.strip()}
    return v


def _coerce_inventory_remove_item(v: Any) -> Any:
    """Normalize inventory_remove entries: str -> {id, amount}, passthrough dicts."""
    if not v:
        return v
    out: list[Any] = []
    for x in v:
        if isinstance(x, str):
            out.append({"id": x, "amount": None})
        else:
            out.append(x)
    return out


def _coerce_condition_add_item(v: Any) -> Any:
    """Normalize condition_add entries using _coerce_condition_str."""
    if not v:
        return v
    return [_coerce_condition_str(x) for x in v]


_PUNCTUATION_STRIP = frozenset(("*", "_", "`", ".", ",", ";", ":", "!", "?"))


def _coerce_condition_remove_item(v: Any) -> Any:
    """Normalize condition_remove entries: str -> {id}, stripping punctuation."""
    if not v:
        return v
    out: list[Any] = []
    for x in v:
        if isinstance(x, str):
            cid = x.lower().strip().replace(" ", "_")
            for ch in _PUNCTUATION_STRIP:
                cid = cid.replace(ch, "")
            out.append({"id": "_".join(cid.split()) or "condition"})
        else:
            out.append(x)
    return out


class ConditionAdd(BaseModel):
    id: str
    label: str
    description: str = ""
    turns_remaining: int | None = None

    @field_validator("id", "label", mode="before")
    @classmethod
    def _strip(cls, v: Any) -> Any:
        return str(v).strip() if v is not None else v


class ConditionRemove(BaseModel):
    id: str

    @field_validator("id", mode="before")
    @classmethod
    def _strip(cls, v: Any) -> Any:
        return str(v).strip() if v is not None else v


class RulesCheck(BaseModel):
    required: bool = False
    skill: SkillName | None = None
    difficulty: Difficulty = "normal"

    @field_validator("skill", mode="before")
    @classmethod
    def _coerce_skill(cls, v: Any) -> Any:
        return None if v == "" else v

    @field_validator("difficulty", mode="before")
    @classmethod
    def _coerce_difficulty(cls, v: Any) -> Any:
        return "normal" if v == "" else v


class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    impossible: bool = False
    impossible_reason: str = ""
    scene_motion: Literal["hold", "advance", "transition"] = "hold"


class RulesOutcome(BaseModel):
    rolled: bool = False
    skill: str = ""
    stat_value: int = 0
    difficulty: str = "normal"
    stat_mod: int = 0
    diff_mod: int = 0
    cond_mod: int = 0
    dice: list[int] = Field(default_factory=list)
    raw_total: int = 0
    final_total: int = 0
    band: Band = "success"
    directive: str = ""
    intent_verb: str = ""
    intent: str = ""
    impossible: bool = False
    impossible_reason: str = ""


class InventoryItem(BaseModel):
    id: str
    name: str
    notes: str = ""
    amount: int = Field(default=1, ge=1)
    aliases: list[str] = Field(default_factory=list)


class InventoryRemove(BaseModel):
    id: str
    amount: int | None = None  # None = remove entire stack; int = subtract from stack


class InventoryUpdate(BaseModel):
    id: str
    name: str | None = None
    notes: str | None = None


class LocationRef(BaseModel):
    id: str
    name: str
    description: str = ""


class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)
    allegiance: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None  # "present" | "nearby" | "known" — scene extractor sets this
    notes: str | None = None      # scene-specific attitude, cleared on departure
    first_seen_turn: int | None = None  # set by engine on initial entry creation


class WorldStateFact(BaseModel):
    id: str
    text: str
    tier: Literal["permanent", "persistent"] = "persistent"



class StateDelta(BaseModel):
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)
    inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)

    @field_validator("inventory_remove", mode="before")
    @classmethod
    def _coerce_inventory_remove(cls, v: Any) -> Any:
        return _coerce_inventory_remove_item(v)

    location_change: LocationRef | None = None
    location_description: str | None = None
    pc_condition_add: list[ConditionAdd] = Field(default_factory=list, max_length=6)
    pc_condition_remove: list[ConditionRemove] = Field(default_factory=list)
    scene_tags: list[str] = Field(default_factory=list)
    scene_tagline: str | None = (
        None  # 3–6 words for UI header; persisted to state.scene.tagline
    )
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    actions: list[str] = Field(default_factory=list, max_length=10)
    arc_update: CampaignArc | None = None
    world_state_add: list[WorldStateFact] = Field(default_factory=list)
    world_state_remove: list[str] = Field(default_factory=list)

    @field_validator("pc_condition_add", mode="before")
    @classmethod
    def _coerce_condition_add(cls, v: Any) -> Any:
        return _coerce_condition_add_item(v)

    @field_validator("pc_condition_remove", mode="before")
    @classmethod
    def _coerce_condition_remove(cls, v: Any) -> Any:
        return _coerce_condition_remove_item(v)


class SceneExtractResult(BaseModel):
    scene_tags: list[str] = Field(default_factory=list)
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )

    @field_validator("location_description", mode="before")
    @classmethod
    def _coerce_location_description(cls, v: Any) -> Any:
        if not v:
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("description", str(v))
        return str(v)


class StateExtractResult(BaseModel):
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)
    inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)
    pc_condition_add: list[ConditionAdd] = Field(default_factory=list, max_length=2)
    pc_condition_remove: list[ConditionRemove] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @field_validator("inventory_remove", mode="before")
    @classmethod
    def _coerce_inventory_remove(cls, v: Any) -> Any:
        return _coerce_inventory_remove_item(v)

    @field_validator("pc_condition_add", mode="before")
    @classmethod
    def _coerce_condition_add(cls, v: Any) -> Any:
        return _coerce_condition_add_item(v)

    @field_validator("pc_condition_remove", mode="before")
    @classmethod
    def _coerce_condition_remove(cls, v: Any) -> Any:
        return _coerce_condition_remove_item(v)


# NOTE: These models are saved for future batch compaction implementation.
# No compactor runs currently — they exist so the schema is ready when needed.
class CompactorNpcMerge(BaseModel):
    keep_id: str
    remove_ids: list[str] = Field(default_factory=list)



class CompactorSanitizationAction(BaseModel):
    """A sanitization action with confidence level."""
    id: str
    confidence: Literal["high", "medium", "low"] = "high"
    reason: str | None = None


def _coerce_sanitization_actions(v: Any) -> Any:
    if not v:
        return v
    out = []
    for item in v:
        if isinstance(item, str):
            out.append({"id": item.strip(), "confidence": "high", "reason": None})
        else:
            out.append(item)
    return out


class CompactorSanitizationResult(BaseModel):
    npc_merge: list[CompactorNpcMerge] = Field(default_factory=list)
    inventory_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    pressure_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    condition_remove: list[CompactorSanitizationAction] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @field_validator("inventory_remove", "pressure_remove", "condition_remove", mode="before")
    @classmethod
    def _coerce_actions(cls, v: Any) -> Any:
        return _coerce_sanitization_actions(v)


class ThreadResolution(BaseModel):
    """Structured resolution for a thread — storyteller assigns outcome state."""
    id: str
    resolution_state: Literal["resolved", "failed", "abandoned"]
    outcome: str = ""  # one past-tense sentence written at resolution time; stored on completed ArcThread
    promote_to_world_state: bool = False


class ThreadUpdate(BaseModel):
    id: str
    active: bool | None = None
    urgency: Literal["background", "normal", "urgent"] | None = None
    summary: str | None = None
    progress: str | None = None


class ArcResolution(BaseModel):
    resolution: str
    visible_goal: str
    goal_context: str
    drop_threads: list[str] = Field(default_factory=list)
    new_threads: list[ArcThread] = Field(default_factory=list)


class GMBeat(BaseModel):
    type: Literal[
        "complication",
        "revelation",
        "opportunity",
        "breathing_room",
        "pressure",
        "twist",
        "setback",
        "escalation",
        "callback",
    ] | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _coerce_gm_beat_type(cls, v: Any) -> Any:
        valid_types = {
            "complication",
            "revelation",
            "opportunity",
            "breathing_room",
            "pressure",
            "twist",
            "setback",
            "escalation",
            "callback",
        }
        if isinstance(v, str) and v not in valid_types:
            return None
        return v
    surface_as: Literal[
        "ambient",
        "event",
        "npc_behavior",
        "environmental",
        "player_discovery",
        "item",
    ] = "ambient"
    beat_expires_turn: int | None = None


class StorytellerResult(BaseModel):
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    goal_update: str | None = None
    gm_beat: GMBeat | None = None
    thread_resolve: list[ThreadResolution] = Field(default_factory=list)
    thread_add: ArcThread | None = None
    thread_update: list[ThreadUpdate] = Field(default_factory=list)
    arc_resolve: ArcResolution | None = None
    world_state_add: list[WorldStateFact] = Field(default_factory=list)
    world_state_remove: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _nullify_invalid_gm_beat(self) -> "StorytellerResult":
        if self.gm_beat is not None:
            if not self.gm_beat.type:
                self.gm_beat = None
        return self

    @model_validator(mode="after")
    def _nullify_empty_arc_resolve(self) -> "StorytellerResult":
        if isinstance(self.arc_resolve, dict) and not self.arc_resolve:
            self.arc_resolve = None
        return self

    @model_validator(mode="after")
    def _nullify_empty_thread_add(self) -> "StorytellerResult":
        if isinstance(self.thread_add, dict) and not self.thread_add:
            self.thread_add = None
        return self

    @field_validator("actions", mode="before")
    @classmethod
    def _coerce_actions(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[str] = []
        for x in v:
            if isinstance(x, str):
                out.append(x)
            elif isinstance(x, dict):
                out.append(x.get("action") or x.get("description") or x.get("text") or str(x))
            else:
                out.append(str(x))
        return out

    @model_validator(mode="after")
    def _warn_empty_actions(self) -> "StorytellerResult":
        if not self.actions:
            _log.debug(
                "storytell.actions is empty — LLM omitted field or returned []",
            )
        return self


@dataclass
class TurnResult:
    turn: int
    trace_id: str
    narrative: str
    state_delta: dict[str, Any]
    applied: dict[str, Any] = field(default_factory=dict)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    scene_tags: list[str] = field(default_factory=list)
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
    ts: str = field(default="")


def load_config(path: str | os.PathLike[str] = "config.yaml") -> dict[str, Any]:
    import yaml

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
    import yaml as _yaml

    if config_dict is None:
        config_dict = load_config(path)
    path = Path(path).resolve()
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        _yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)
    tmp_path.replace(path)
