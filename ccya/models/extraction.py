"""Extraction models: output schemas for the 3-stream extraction pipeline."""

from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ccya.models.state import (
    ArcThread, ArcResolution, CampaignArc, ConditionAdd, ConditionRemove,
    InventoryItem, InventoryRemove, InventoryUpdate, LocationRef, ThreadResolution, ThreadUpdate,
)

_log = logging.getLogger(__name__)


class CompendiumNpcUpdate(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    aliases: list[str] = Field(default_factory=list)
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    presence: str | None = None  # "present" | "nearby" | "known" | "departed" — scene extractor sets this
    position: str | None = None   # spatial position in current scene
    first_seen_turn: int | None = None  # set by engine on initial entry creation
    personality: str | None = None  # archetype id; immutable once set
    bond: str | None = None         # durable personal history — human-readable description
    departed_reason: str | None = None     # combined: "short label — prose" describing the departure
    departed_turn: int | None = None       # set by engine on first presence:"departed"


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


def _coerce_condition_str(v: Any) -> Any:
    if isinstance(v, str):
        cid = v.lower().strip().replace(" ", "_")
        for ch in ("*", "_", "`", ".", ",", ";", ":", "!", "?"):
            cid = cid.replace(ch, "")
        cid = "_".join(cid.split()) or "condition"
        return {"id": cid, "label": v.strip()}
    return v


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


class StateDelta(BaseModel):
    inventory_change_reason: str = ""
    condition_change_reason: str = ""
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
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    actions: list[str] = Field(default_factory=list, max_length=10)
    arc_update: CampaignArc | None = None

    @field_validator("pc_condition_add", mode="before")
    @classmethod
    def _coerce_condition_add(cls, v: Any) -> Any:
        return _coerce_condition_add_item(v)

    @field_validator("pc_condition_remove", mode="before")
    @classmethod
    def _coerce_condition_remove(cls, v: Any) -> Any:
        return _coerce_condition_remove_item(v)


class SceneExtractResult(BaseModel):
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(
        default_factory=list, max_length=12
    )
    npc_context: list[dict[str, Any]] = Field(default_factory=list)


class StateExtractResult(BaseModel):
    condition_change_reason: str = ""
    inventory_change_reason: str = ""
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)
    inventory_update: list[InventoryUpdate] = Field(default_factory=list, max_length=6)
    pc_condition_add: list[ConditionAdd] = Field(default_factory=list, max_length=2)
    pc_condition_remove: list[ConditionRemove] = Field(default_factory=list)
    location_change: LocationRef | None = None
    location_description: str | None = None

    model_config = {"extra": "ignore"}

    @model_validator(mode="after")
    def _validate_condition_reason(self) -> "StateExtractResult":
        if (self.pc_condition_add or self.pc_condition_remove) and not self.condition_change_reason:
            raise ValueError("condition_change_reason is required when condition changes are present")
        return self

    @model_validator(mode="after")
    def _validate_inventory_reason(self) -> "StateExtractResult":
        if (self.inventory_add or self.inventory_remove or self.inventory_update) and not self.inventory_change_reason:
            raise ValueError("inventory_change_reason is required when inventory changes are present")
        return self

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

    effect: str = ""
    npc_id: str | None = None
    driver: Literal["motivation", "fear", "leverage"] | None = None
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
    chapter_end: bool = False

    @field_validator("thread_update", mode="before")
    @classmethod
    def _coerce_progress_kind(cls, v: Any) -> Any:
        if not v:
            return v
        VALID_KINDS = {"advancement", "setback", "shift"}
        coerced = []
        for item in v:
            if isinstance(item, dict):
                pk = item.get("progress_kind")
                if pk is not None and pk not in VALID_KINDS:
                    item = dict(item)
                    item["progress_kind"] = "advancement"
            coerced.append(item)
        return coerced

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
