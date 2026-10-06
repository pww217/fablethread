"""Rules models: intent envelopes, rules checks, and outcomes."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from fablethread.models.config import Band, Difficulty, SkillName


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
    reason: str = ""
    scene_motion: Literal["hold", "advance", "transition"] = "hold"


class RulesOutcome(BaseModel):
    rolled: bool = False
    skill: str = ""
    stat_value: int = 0
    difficulty: str = "normal"
    original_difficulty: str = ""
    stat_mod: int = 0
    diff_mod: int = 0
    dice: list[int] = Field(default_factory=list)
    raw_total: int = 0
    final_total: int = 0
    band: Band = "success"
    directive: str = ""
    intent_verb: str = ""
    intent: str = ""
    impossible: bool = False
    reason: str = ""
    difficulty_adjustment: str = ""

    @property
    def roll_display(self) -> str:
        """Format the dice roll with modifiers for display in narration."""
        die = self.dice[0] if self.dice else "?"
        parts = [f"d12: {die}"]
        
        # Stat modifier (skill bonus/penalty), shown first if applicable
        if self.stat_mod != 0:
            sign = "+" if self.stat_mod > 0 else "-"
            parts.append(f"{sign} {abs(self.stat_mod)} ({self.skill.capitalize()})")
        
        # Difficulty modifier, shown second if not normal (normal=0)
        diff_labels = {"hard": "Hard", "extreme": "Extreme"}
        if self.diff_mod != 0:
            label = diff_labels.get(self.difficulty, self.difficulty.capitalize())
            sign = "+" if self.diff_mod > 0 else "-"
            parts.append(f"{sign} {abs(self.diff_mod)} ({label})")
        
        # If no modifiers shown and stat is zero, still show +0 for clarity
        if len(parts) == 1:
            parts.append("+ 0")
        
        return " ".join(parts) + f" → {self.final_total}"
