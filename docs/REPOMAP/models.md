# models.py — Pydantic models

## Pydantic models

`Condition`, `ConditionAdd`, `ConditionRemove`, `RulesCheck`, `Scope`, `IntentEnvelope`, `RulesOutcome`, `InventoryItem`, `InventoryRemove`, `InventoryUpdate`, `LocationRef`, `QuestObjective`, `QuestObjectiveUpdate`, `QuestUpdate`, `NpcRef`, `NpcAdd`, `NpcRemove`, `NpcUpdate`, `CompendiumNpcUpdate`, `RecentEvent`, `RecentEventUpdate`, `ScenePressure`, `StateDelta`, `SceneExtractResult`, `StateExtractResult`, `GMBeat`, `ProgressExtractResult`, `ExtractResult`, `CompactorNpcMerge`, `CompactorSanitizationResult`.

## Dataclasses

- **`TurnResult`** — returned from `run_turn()`: turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, recent_events, diff, changes, metrics, errors, rules, outcome_summary, recent_events_evicted.

## Functions

- **`load_config(path="config.yaml")`** → `dict`.

## Type aliases

- `SkillName` (6 skills)
- `Difficulty` (5 levels)
- `Band` (7 PbtA bands)
