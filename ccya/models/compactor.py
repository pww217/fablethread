"""Dormant compactor models — schema ready for future batch compaction."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


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
