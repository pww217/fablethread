"""Pydantic models for LLM structured output and config."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Rules engine types
# ---------------------------------------------------------------------------

SkillName = Literal["strength", "dexterity", "wits", "lore", "charisma", "resolve"]
Difficulty = Literal["trivial", "easy", "normal", "hard", "extreme"]
Band = Literal["crit_fail", "fail", "setback", "mixed", "boon", "success", "crit_success"]


class RulesCheck(BaseModel):
    required: bool = False
    skill: SkillName | None = None
    difficulty: Difficulty = "normal"
    tags: list[str] = Field(default_factory=list, max_length=4)


class Scope(BaseModel):
    active_domains: list[str] = Field(default_factory=list)
    skip_domains: list[str] = Field(default_factory=list)
    implicit_preconditions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)


class IntentEnvelope(BaseModel):
    intent: str = Field(default="", max_length=200)
    intent_verb: str = Field(default="act", max_length=24)
    target: str = ""
    stakes: str = ""
    check: RulesCheck = Field(default_factory=RulesCheck)
    scope: Scope = Field(default_factory=Scope)


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


class InventoryRemove(BaseModel):
    id: str
    amount: int | None = None  # None = remove entire stack; int = subtract from stack


class InventoryUpdate(BaseModel):
    """Patch name/notes on an existing stack without changing amount."""

    id: str
    name: str | None = None
    notes: str | None = None


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
    name: str | None = None  # omit when known from compendium; engine hydrates
    title: str | None = None
    notes: str = ""  # current attitude or situation toward the player
    bio: str | None = None  # durable identity; omit when unchanged — engine hydrates


class CompendiumNpcUpdate(BaseModel):
    """Update compendium entry for an NPC who may not be present this turn."""

    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None


class FactUpdate(BaseModel):
    """Replace one established fact by normalized match on `old`; write `new`."""

    old: str
    new: str


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
    quest_updates: list[QuestUpdate] = Field(default_factory=list)
    pc_condition_add: list[str] = Field(default_factory=list)
    pc_condition_remove: list[str] = Field(default_factory=list)
    established_facts_add: list[str] = Field(default_factory=list)
    established_facts_update: list[FactUpdate] = Field(default_factory=list)
    established_facts_remove: list[str] = Field(default_factory=list)
    scene_tags: list[str] = Field(default_factory=list)
    scene_tagline: str | None = None  # 3–6 words for UI header; persisted to state.scene.tagline
    present_npcs: list[NpcRef] = Field(default_factory=list)
    compendium_npc_update: list[CompendiumNpcUpdate] = Field(default_factory=list, max_length=12)


class ExtractResult(BaseModel):
    state_delta: StateDelta
    failed: list[str] = Field(default_factory=list)


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
    diff: list[str] = field(default_factory=list)  # short human-readable delta lines for UI toast
    changes: dict[str, Any] = field(default_factory=dict)  # structured pre/post diff for modal + log
    metrics: dict = field(default_factory=dict)
    errors: list[dict] = field(default_factory=list)
    rules: dict = field(default_factory=dict)  # serialized RulesOutcome + intent for logging/UI


# --- Config ---


def load_config(path: str = "config.yaml") -> dict[str, Any]:
    import yaml

    with open(path) as f:
        return yaml.safe_load(f)
