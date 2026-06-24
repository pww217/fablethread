"""State data models: threads, conditions, inventory, locations, world facts."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

_log = logging.getLogger(__name__)


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

    @field_validator("progress", mode="wrap")
    @classmethod
    def _coerce_progress(cls, v: Any, handler: Any) -> Any:
        if isinstance(v, str):
            return handler([{"text": v, "kind": "advancement"}])
        if not v or (isinstance(v, int) and v == 0):
            return []
        if isinstance(v, list):
            if v and all(isinstance(item, str) for item in v):
                return handler([{"text": item, "kind": "advancement"} for item in v])
            return handler(v)
        return handler(v)


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
    id: str
    name: str
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
    valence: Valence | None = None
    expires_turn: int | None = None


class SanitizedWorldStateFact(BaseModel):
    """A world state fact that has been confirmed by the thread sanitizer."""
    id: str
    text: str
    tier: Literal["global", "local"] = "global"
    permanent: bool = False
    valence: Valence | None = None
    expires_turn: int | None = None
    source_thread: str | None = None


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
