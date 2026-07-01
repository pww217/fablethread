"""State data models: threads, conditions, inventory, locations, world facts."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine-internal WorldState model (Phase 01 of I-17 #3)
# ---------------------------------------------------------------------------


class Meta(BaseModel):
    turn: int = 0
    setting_pack: str = ""
    model: str = ""
    session_name: str = ""
    compendium_touch_order: list[str] = Field(default_factory=list)
    prior_history: list[str] = Field(default_factory=list)
    pending_gm_beat: dict[str, Any] | None = None
    beat_candidates: list[dict[str, Any]] = Field(default_factory=list)
    recent_beats: list[dict[str, Any]] = Field(default_factory=list)
    recent_rolls: list[dict[str, Any]] = Field(default_factory=list)
    smoothed_convergence: float = 0.0
    last_inventory_change_reason: str | None = None
    last_condition_change_reason: str | None = None
    last_rules_outcome: dict[str, Any] | None = None
    last_thread_creation_turn: int | None = None
    last_arc_resolve_turn: int | None = None


class PC(BaseModel):
    name: str = ""
    tagline: str = ""
    bio: str = ""
    stats: dict[str, int] = Field(
        default_factory=lambda: {
            "strength": 2,
            "dexterity": 2,
            "wits": 2,
            "charisma": 2,
        },
    )
    conditions: list[Condition] = Field(default_factory=list)
    allegiance: str | None = None
    situation: dict[str, Any] = Field(default_factory=dict)
    directive: str = ""
    actions: list[str] = Field(default_factory=list)


class Scene(BaseModel):
    tags: list[str] = Field(default_factory=list)
    world_state: list[dict[str, Any]] = Field(default_factory=list)
    turn_entered: int = 0
    scene_phase: str = "SETUP"
    climax_turn_count: int = 0
    breather_turn_count: int = 0
    turns_in_phase: int = 0
    curtain_call: str = ""
    location_entered_turn: int = 0


class NPCEntry(BaseModel):
    name: str = ""
    title: str | None = None
    bio: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: NpcPresence = NpcPresence.KNOWN
    position: str | None = None
    personality: str | None = None
    tie: str | None = None
    party: bool = False
    last_presence_turn: int | None = None
    last_seen_location: str | None = None
    first_seen_turn: int | None = None
    departed_reason: str | None = None
    departed_turn: int | None = None


class Compendium(BaseModel):
    npcs: dict[str, NPCEntry] = Field(default_factory=dict)


class World(BaseModel):
    factions: list[dict[str, str]] = Field(default_factory=list)
    locations: list[KeyLocation] = Field(default_factory=list)


class WorldState(BaseModel):
    meta: Meta = Field(default_factory=Meta)
    pc: PC = Field(default_factory=PC)
    location: LocationRef = Field(default_factory=lambda: LocationRef())
    inventory: list[InventoryItem] = Field(default_factory=list)
    arc: LongTermObjective = Field(default_factory=LongTermObjective)
    scene: Scene = Field(default_factory=Scene)
    compendium: Compendium = Field(default_factory=Compendium)
    resolved_arcs: list[dict[str, Any]] = Field(default_factory=list)
    world_state_candidates: list[dict[str, Any]] = Field(default_factory=list)
    world: World = Field(default_factory=World)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "WorldState":
        """Validate and coerce raw YAML dict into WorldState.

        Handles backward-compat aliases:
        - ``long_term_objective`` key → ``arc`` field
        - ``active`` → ``dormant`` on ArcThread (handled by ArcThread validator)
        - Missing sections filled with model defaults
        """
        merged = dict(raw)
        # Backward-compat: ``long_term_objective`` key was used in old YAML
        if "long_term_objective" in merged and "arc" not in merged:
            merged["arc"] = merged.pop("long_term_objective")
        # Ensure missing sections get defaults
        for field_name in ("meta", "pc", "location", "inventory", "arc", "scene", "compendium", "resolved_arcs", "world_state_candidates", "world"):
            if field_name not in merged or merged[field_name] is None:
                merged[field_name] = {}
        return cls.model_validate(merged)

    def to_dict(self) -> dict[str, Any]:
        """Export WorldState to raw dict for YAML serialization."""
        return self.model_dump(exclude_none=False)


class NpcPresence(str, Enum):
    PRESENT = "present"
    NEARBY = "nearby"
    KNOWN = "known"
    DEPARTED = "departed"


class ProgressEntry(BaseModel):
    kind: Literal["advancement", "setback"] = "advancement"
    text: str


class ArcThread(BaseModel):
    id: str
    summary: str
    dormant: bool = False
    urgency: Literal["background", "normal", "urgent"] = "normal"
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _coerce_arc_thread_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.lower()
        valid_types = {"threat", "opportunity", "complication", "revelation"}
        if isinstance(v, str) and v not in valid_types:
            return None
        return v

    major_updates: list[ProgressEntry] = Field(default_factory=list)
    resolution_state: str | None = None
    outcome: str | None = None
    resolved_turn: int | None = None
    last_updated_turn: int | None = None
    added_turn: int | None = None
    urgency_set_turn: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_active_to_dormant(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "active" in data and "dormant" not in data:
                data["dormant"] = not data.pop("active")
        return data

    @model_validator(mode="after")
    def _dormant_not_urgent(self) -> "ArcThread":
        if self.dormant and self.urgency == "urgent":
            self.urgency = "background"
        return self


class LongTermObjective(BaseModel):
    long_term_objective: str = ""
    threads: list[ArcThread] = Field(default_factory=list)
    completed_threads: list[ArcThread] = Field(default_factory=list)
    resolution: str | None = None
    last_thread_created_turn: int = 0
    started_turn: int | None = None


class Condition(BaseModel):
    id: str
    label: str
    description: str = ""
    added_turn: int = 0
    turns_remaining: int | Literal["permanent"] = 0

    @field_validator("turns_remaining", mode="before")
    @classmethod
    def _coerce_tr(cls, v: Any) -> Any:
        if v is None:
            return 0
        return v


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
    turns_remaining: int | Literal["permanent"] = 0

    @field_validator("turns_remaining", mode="before")
    @classmethod
    def _coerce_tr(cls, v: Any) -> Any:
        if v is None:
            return 0
        return v

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
    id: str = ""
    name: str = ""
    description: str = ""


class KeyLocation(BaseModel):
    """A named place in the world at game start."""
    id: str
    name: str
    description: str = ""
    status: str = "active"
    tags: list[str] = Field(default_factory=list)


class Valence(str, Enum):
    THREAT = "threat"
    COMPLICATION = "complication"
    NEUTRAL = "neutral"
    BOON = "boon"


class WorldStateFact(BaseModel):
    id: str
    text: str
    tier: Literal["global", "local"] = "global"
    permanent: bool = False
    valence: Valence = Valence.NEUTRAL
    expires_turn: int | None = None


class SanitizedWorldStateFact(BaseModel):
    """A world state fact that has been confirmed by the thread sanitizer."""
    id: str
    text: str
    tier: Literal["global", "local"] = "global"
    permanent: bool = False
    valence: Valence = Valence.NEUTRAL
    expires_turn: int | None = None


class ThreadResolution(BaseModel):
    """Structured resolution for a thread — storyteller assigns outcome state."""
    id: str
    resolution_state: Literal["resolved", "failed", "abandoned"]
    outcome: str = ""  # one past-tense sentence written at resolution time; stored on completed ArcThread
    resolved_turn: int | None = None
    world_state_candidate: str | None = None


class ThreadUpdate(BaseModel):
    id: str
    dormant: bool | None = None
    urgency: Literal["background", "normal", "urgent"] | None = None
    type: Literal["threat", "opportunity", "complication", "revelation"] | None = None
    progress: str | None = None
    major_update_signal: Literal["advancement", "setback"] | None = None
    reason: str | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _coerce_thread_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.lower()
        valid_types = {"threat", "opportunity", "complication", "revelation"}
        if isinstance(v, str) and v not in valid_types:
            return None
        return v


class ArcResolution(BaseModel):
    resolution: str
    long_term_objective: str
