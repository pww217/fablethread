"""Pydantic models for LLM structured output and config."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    id: str
    name: str
    notes: str = ""


class LocationRef(BaseModel):
    id: str
    name: str
    description: str = ""


class QuestObjective(BaseModel):
    description: str
    done: bool = False


class QuestUpdate(BaseModel):
    id: str
    title: str = ""
    status: str = "active"  # active, completed, abandoned
    objectives: list[QuestObjective] = Field(default_factory=list)


class NpcRef(BaseModel):
    id: str
    name: str
    notes: str = ""  # one-line description + attitude toward the player


class StateDelta(BaseModel):
    inventory_add: list[InventoryItem] = Field(default_factory=list, max_length=6)
    inventory_remove: list[str] = Field(default_factory=list)
    location_change: LocationRef | None = None
    quest_updates: list[QuestUpdate] = Field(default_factory=list)
    pc_condition_add: list[str] = Field(default_factory=list)
    pc_condition_remove: list[str] = Field(default_factory=list)
    established_facts: list[str] = Field(default_factory=list)
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
