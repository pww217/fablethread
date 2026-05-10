# models.py — Pydantic models

## Pydantic models

`Condition`, `ConditionAdd`, `ConditionRemove`, `RulesCheck`, `Scope`, `IntentEnvelope`, `RulesOutcome`, `InventoryItem`, `InventoryRemove`, `InventoryUpdate`, `LocationRef`, `QuestObjective`, `QuestObjectiveUpdate`, `QuestUpdate`, `NpcRef`, `NpcAdd`, `NpcRemove`, `NpcUpdate`, `CompendiumNpcUpdate`, `RecentEvent`, `RecentEventUpdate`, `ScenePressure`, `StateDelta`, `SceneExtractResult`, `StateExtractResult`, `GMBeat`, `ProgressExtractResult`, `CompactorNpcMerge`, `CompactorRecentEventCompact`, `CompactorSanitizationResult`.

## Dataclasses

- **`TurnResult`** — returned from `run_turn()`: turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, recent_events, diff, changes, metrics, errors, rules, outcome_summary, recent_events_evicted.

## Functions

- **`load_config(path="config.yaml")`** → `dict`.

## GMBeat

- `type`: Literal["complication", "revelation", "opportunity", "breathing_room", "pressure", "twist", "setback", "escalation", "callback"] | None
- `surface_as`: Literal["ambient", "event", "npc_behavior", "environmental", "player_discovery", "item"] = "ambient"
- `instruction`: str | None — validated by `_validate_instruction_quality` (field_validator, mode="after") which nullifies the beat if instruction is empty, whitespace-only, under 40 chars, or starts with a filler prefix from `_GM_BEAT_FILLER_PREFIXES`.
- `beat_expires_turn`: int | None — turn number at which a pending beat expires; set by `turn.py` when storing `pending_gm_beat`.

## SceneExtractResult

- No `gm_beat` field (moved to `ProgressExtractResult` in progress-rules-narration plan).

## ProgressExtractResult

- `gm_beat: GMBeat | None = None` — validated by `_nullify_invalid_gm_beat` (model_validator, mode="after") which sets `gm_beat = None` if the beat has no instruction or no type.

## CompactorRecentEventCompact

- `id: str` — new snake_case ID for the consolidated event
- `text: str` — consolidated narrative text, in-universe phrasing
- `turn: int = 0` — turn this event originated from (for ordering)

## CompactorSanitizationResult

- `npc_merge: list[CompactorNpcMerge]` — NPC dedup merges
- `inventory_remove: list[str]` — duplicate inventory item IDs to remove
- `quest_close: list[str]` — active quest IDs to mark completed
- `pressure_remove: list[str]` — stale scene_pressure IDs to remove
- `condition_remove: list[str]` — resolved PC condition IDs to remove
- `recent_events_compact: list[CompactorRecentEventCompact]` — consolidated recent_events from compactor

## Type aliases

- `SkillName` (6 skills)
- `Difficulty` (5 levels)
- `Band` (7 PbtA bands)
