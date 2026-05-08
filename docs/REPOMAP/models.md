# models.py — Pydantic models

## Pydantic models

`Condition`, `ConditionAdd`, `ConditionRemove`, `RulesCheck`, `Scope`, `IntentEnvelope`, `RulesOutcome`, `InventoryItem`, `InventoryRemove`, `InventoryUpdate`, `LocationRef`, `QuestObjective`, `QuestObjectiveUpdate`, `QuestUpdate`, `NpcRef`, `NpcAdd`, `NpcRemove`, `NpcUpdate`, `CompendiumNpcUpdate`, `RecentEvent`, `RecentEventUpdate`, `ScenePressure`, `StateDelta`, `SceneExtractResult`, `StateExtractResult`, `GMBeat`, `ProgressExtractResult`, `CompactorNpcMerge`, `CompactorSanitizationResult`.

## Dataclasses

- **`TurnResult`** — returned from `run_turn()`: turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, recent_events, diff, changes, metrics, errors, rules, outcome_summary, recent_events_evicted.

## Functions

- **`load_config(path="config.yaml")`** → `dict`.

## GMBeat

- `type`: Literal["complication", "revelation", "opportunity", "breathing_room", "pressure"] | None
- `surface_as`: Literal["ambient", "event", "npc_behavior"] = "ambient"
- `instruction`: str | None — validated by `_validate_instruction_quality` (field_validator, mode="after") which nullifies the beat if instruction is empty, whitespace-only, under 40 chars, or starts with a filler prefix from `_GM_BEAT_FILLER_PREFIXES`.

## SceneExtractResult

- `gm_beat: GMBeat | None = None` — validated by `_nullify_invalid_gm_beat` (model_validator, mode="after") which sets `gm_beat = None` if the beat has no instruction or no type.

## Type aliases

- `SkillName` (6 skills)
- `Difficulty` (5 levels)
- `Band` (7 PbtA bands)
