"""Pydantic models for LLM structured output and config."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, field_validator


class InventoryItem(BaseModel):
    id: str
    name: str
    notes: str = ""
    amount: int = Field(default=1, ge=1)


class InventoryRemove(BaseModel):
    id: str
    amount: int | None = None  # None = remove entire stack; int = subtract from stack


class LocationRef(BaseModel):
    id: str
    name: str
    description: str = ""


class QuestObjective(BaseModel):
    """Stored objective shape in state.yaml (not used in LLM deltas)."""

    description: str
    done: bool = False
    failed: bool = False


class QuestObjectiveUpdate(BaseModel):
    """Objective patch in quest_updates: prefer 1-based index over description."""

    index: int | None = None  # 1-based into existing objectives list
    description: str | None = None  # fallback match; required when adding a new objective
    done: bool | None = None
    failed: bool | None = None


class QuestUpdate(BaseModel):
    id: str
    title: str = ""
    # active | completed | failed | abandoned
    status: str = "active"
    objectives: list[QuestObjectiveUpdate] = Field(default_factory=list)


class NpcRef(BaseModel):
    id: str
    name: str
    title: str = ""  # occupation, role, or status (e.g. "Port Administrator", "OPA Fixer")
    notes: str = ""  # current attitude or situation toward the player


class FactUpdate(BaseModel):
    """Replace one established fact by normalized match on `old`; write `new`."""

    old: str
    new: str


class StateDelta(BaseModel):
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[InventoryRemove] = Field(default_factory=list)

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
    quest_updates: list[QuestUpdate] = Field(default_factory=list)
    pc_condition_add: list[str] = Field(default_factory=list)
    pc_condition_remove: list[str] = Field(default_factory=list)
    established_facts_add: list[str] = Field(default_factory=list)
    established_facts_update: list[FactUpdate] = Field(default_factory=list)
    established_facts_remove: list[str] = Field(default_factory=list)
    scene_tags: list[str] = Field(default_factory=list)
    present_npcs: list[NpcRef] = Field(default_factory=list)


class ExtractResult(BaseModel):
    state_delta: StateDelta
    actions: list[str] = Field(min_length=4, max_length=4)


# --- TurnResult (returned from engine, not Pydantic) ---


@dataclass
class TurnResult:
    turn: int
    trace_id: str
    narrative: str
    state_delta: dict
    applied: dict = field(default_factory=dict)
    rejected: list[dict] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    scene_tags: list[str] = field(default_factory=list)
    established_facts: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)


# --- Config ---


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)
