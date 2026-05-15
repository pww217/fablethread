"""Pydantic models for LLM structured output and config."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Literal

from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator

SkillName = Literal["strength", "dexterity", "wits", "lore", "charisma", "resolve"]
Difficulty = Literal["trivial", "easy", "normal", "hard", "extreme"]
Band = Literal[
    "crit_fail", "fail", "setback", "partial", "success", "crit_success"
]


class ArcPhase(str, Enum):
    SETUP = "setup"
    PURSUIT = "pursuit"
    REVERSAL = "reversal"
    CRISIS = "crisis"
    RESOLUTION = "resolution"


class ThreadState(str, Enum):
    LATENT = "latent"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    EXPIRED = "expired"


class ThreadSignalType(str, Enum):
    ADVANCED = "advanced"
    BLOCKED = "blocked"
    FAILED = "failed"
    IGNORED = "ignored"


class ArcThread(BaseModel):
    id: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    state: ThreadState = ThreadState.LATENT
    urgency: str = "normal"
    progress: int = 0
    unlock_if: str | None = None
    promotes: list[str] = Field(default_factory=list)
    last_offered_turn: int | None = None


class CampaignArc(BaseModel):
    visible_goal: str = ""
    thematic_question: str = ""
    phase: ArcPhase = ArcPhase.SETUP
    hidden_truths: list[str] = Field(default_factory=list)
    discovered_truths: list[str] = Field(default_factory=list)
    active_threads: list[ArcThread] = Field(default_factory=list)
    latent_threads: list[ArcThread] = Field(default_factory=list)
    completed_threads: list[ArcThread] = Field(default_factory=list)
    arc_engagement: int = 0
    pc_drive: str = ""


class ThreadSignal(BaseModel):
    id: str
    signal: ThreadSignalType


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
    stakes: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)


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


class NpcRef(BaseModel):
    id: str
    name: str | None = None  # omit when known from compendium; engine hydrates
    title: str | None = None
    notes: str = ""  # current attitude or situation toward the player
    bio: str | None = None  # durable identity; omit when unchanged — engine hydrates


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


class NpcAdd(BaseModel):
    """Add an NPC to the scene. Notes always required; name/title/bio only for new NPCs or when new info arrives."""
    id: str
    notes: str = ""
    name: str | None = None  # omit when known from compendium
    title: str | None = None
    bio: str | None = None


class NpcRemove(BaseModel):
    """Remove an NPC from the scene."""
    id: str

    @field_validator("id", mode="before")
    @classmethod
    def _strip(cls, v: Any) -> Any:
        return str(v).strip() if v is not None else v


class NpcUpdate(BaseModel):
    """Update an existing scene NPC's notes (and optionally name/title/bio when new info arrives)."""
    id: str
    notes: str | None = None
    name: str | None = None
    title: str | None = None
    bio: str | None = None


class RecentEvent(BaseModel):
    id: str
    text: str
    turn: int = 0


class RecentEventUpdate(BaseModel):
    id: str
    text: str


class StateDelta(BaseModel):
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)
    inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)

    @field_validator("inventory_remove", mode="before")
    @classmethod
    def _coerce_inventory_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                out.append({"id": x, "amount": None})
            else:
                out.append(x)
        return out

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
    npc_add: list[NpcAdd] = Field(default_factory=list, max_length=6)
    npc_remove: list[NpcRemove] = Field(default_factory=list)
    npc_update: list[NpcUpdate] = Field(default_factory=list, max_length=6)
    recent_events_add: list[RecentEvent] = Field(default_factory=list)
    recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
    recent_events_remove: list[str] = Field(default_factory=list)
    scene_pressure_add: list[ScenePressure] = Field(default_factory=list)
    scene_pressure_remove: list[str] = Field(default_factory=list)
    scene_pressure_update: list[ScenePressure] = Field(default_factory=list)
    arc_update: CampaignArc | None = None

    @field_validator("pc_condition_add", mode="before")
    @classmethod
    def _coerce_condition_add(cls, v: Any) -> Any:
        if not v:
            return v
        return [_coerce_condition_str(x) for x in v]

    @field_validator("pc_condition_remove", mode="before")
    @classmethod
    def _coerce_condition_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                cid = x.lower().strip().replace(" ", "_")
                for ch in ("*", "_", "`", ".", ",", ";", ":", "!", "?"):
                    cid = cid.replace(ch, "")
                out.append({"id": "_".join(cid.split()) or "condition"})
            else:
                out.append(x)
        return out


class SceneExtractResult(BaseModel):
    scene_tags: list[str] = Field(default_factory=list)
    scene_tagline: str | None = None
    location_change: LocationRef | None = None
    location_description: str | None = None
    npc_add: list[NpcAdd] = Field(default_factory=list)
    npc_remove: list[NpcRemove] = Field(default_factory=list)
    npc_update: list[NpcUpdate] = Field(default_factory=list)
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    # scene_pressure_remove and scene_pressure_update REMOVED — now on ProgressExtractResult

    @field_validator("npc_remove", mode="before")
    @classmethod
    def _coerce_npc_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                out.append({"id": x})
            else:
                out.append(x)
        return out

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
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                out.append({"id": x, "amount": None})
            else:
                out.append(x)
        return out

    @field_validator("pc_condition_add", mode="before")
    @classmethod
    def _coerce_condition_add(cls, v: Any) -> Any:
        if not v:
            return v
        return [_coerce_condition_str(x) for x in v]

    @field_validator("pc_condition_remove", mode="before")
    @classmethod
    def _coerce_condition_remove(cls, v: Any) -> Any:
        if not v:
            return v
        out: list[Any] = []
        for x in v:
            if isinstance(x, str):
                cid = x.lower().strip().replace(" ", "_")
                for ch in ("*", "_", "`", ".", ","):
                    cid = cid.replace(ch, "")
                out.append({"id": "_".join(cid.split()) or "condition"})
            else:
                out.append(x)
        return out


class CompactorNpcMerge(BaseModel):
    keep_id: str
    remove_ids: list[str] = Field(default_factory=list)


class CompactorRecentEventCompact(BaseModel):
    """A consolidated recent event produced by the compactor."""
    id: str
    text: str
    turn: int = 0


class CompactorSanitizationAction(BaseModel):
    """A sanitization action with confidence level."""
    id: str
    confidence: Literal["high", "medium", "low"] = "high"


class CompactorSanitizationResult(BaseModel):
    npc_merge: list[CompactorNpcMerge] = Field(default_factory=list)
    inventory_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    pressure_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    condition_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    recent_events_compact: list[CompactorRecentEventCompact] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


class ScenePressure(BaseModel):
    id: str
    text: str
    urgency: Literal["immediate", "building", "background"] = "background"
    turn_added: int = 0
    max_turns: int | None = None


_GM_BEAT_FILLER_PREFIXES: tuple[str, ...] = (
    "something happens",
    "give the player",
    "something bad",
    "an event occurs",
    "things get worse",
    "a complication arises",
    "add tension",
    "raise the stakes",
    "provide a",
    "create a",
    "introduce a",
    "the gm",
)


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
    surface_as: Literal[
        "ambient",
        "event",
        "npc_behavior",
        "environmental",
        "player_discovery",
        "item",
    ] = "ambient"
    instruction: str | None = None
    beat_expires_turn: int | None = None

    @field_validator("instruction", mode="after")
    @classmethod
    def _validate_instruction_quality(cls, v: str | None) -> str | None:
        if not v:
            return None
        stripped = v.strip()
        if len(stripped) < 40:
            return None
        lower = stripped.lower()
        if any(lower.startswith(prefix) for prefix in _GM_BEAT_FILLER_PREFIXES):
            return None
        return stripped


class ProgressExtractResult(BaseModel):
    recent_events_add: list[RecentEvent] = Field(default_factory=list)
    recent_events_update: list[RecentEventUpdate] = Field(default_factory=list)
    recent_events_remove: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    outcome_summary: str = ""
    gm_beat: GMBeat | None = None
    beat_disposition: Literal["consume", "carry", "replace"] = "consume"
    scene_pressure_add: list[ScenePressure] = Field(default_factory=list)
    scene_pressure_remove: list[str] = Field(default_factory=list)       # migrated from SceneExtractResult
    scene_pressure_update: list[ScenePressure] = Field(default_factory=list)  # migrated from SceneExtractResult
    thread_signals: list[ThreadSignal] = Field(default_factory=list)
    player_drift_signals: list[str] = Field(default_factory=list)
    candidate_opportunity: str | None = None

    @model_validator(mode="after")
    def _nullify_invalid_gm_beat(self) -> "ProgressExtractResult":
        if self.gm_beat is not None:
            if not self.gm_beat.instruction or not self.gm_beat.type:
                self.gm_beat = None
        return self

    @field_validator("thread_signals", mode="before")
    @classmethod
    def _map_thread_id_to_id(cls, v: Any) -> Any:
        if not v:
            return v
        if isinstance(v, list):
            out = []
            for item in v:
                if isinstance(item, str):
                    continue
                if isinstance(item, dict):
                    if "thread_id" in item and "id" not in item:
                        item = dict(item)
                        item["id"] = item.pop("thread_id")
                    if "status" in item and "signal" not in item:
                        item = dict(item)
                        item["signal"] = item.pop("status")
                out.append(item)
            return out
        return v

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
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    diff: list[str] = field(
        default_factory=list
    )  # short human-readable delta lines for UI toast
    changes: dict[str, Any] = field(
        default_factory=dict
    )  # structured pre/post diff for modal + log
    metrics: dict[str, Any] = field(default_factory=dict)
    errors: list[dict[str, Any]] = field(default_factory=list)
    rules: dict[str, Any] = field(
        default_factory=dict
    )  # serialized RulesOutcome + intent for logging/UI
    outcome_summary: str = field(default="")
    recent_events_evicted: bool = field(default=False)
    ts: str = field(default="")


def load_config(path: str | os.PathLike[str] = "config.yaml") -> dict[str, Any]:
    import yaml

    with open(path) as f:
        result = yaml.safe_load(f)
        if isinstance(result, dict):
            return result
        raise ValueError("config.yaml must contain a mapping at top level")
