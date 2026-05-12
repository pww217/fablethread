# models.py — Pydantic models

## Pydantic models

`Condition`, `ConditionAdd`, `ConditionRemove`, `RulesCheck`, `Scope`, `IntentEnvelope`, `RulesOutcome`, `InventoryItem`, `InventoryRemove`, `InventoryUpdate`, `LocationRef`, `QuestObjective`, `QuestObjectiveUpdate`, `QuestUpdate`, `NpcRef`, `NpcAdd`, `NpcRemove`, `NpcUpdate`, `CompendiumNpcUpdate`, `RecentEvent`, `RecentEventUpdate`, `ScenePressure`, `StateDelta`, `SceneExtractResult`, `StateExtractResult`, `GMBeat`, `ProgressExtractResult`, `CompactorNpcMerge`, `CompactorRecentEventCompact`, `CompactorSanitizationResult`.

## Condition

- `id: str`
- `label: str`
- `description: str = ""`
- `added_turn: int = 0`
- `turns_remaining: int | None = None` — number of turns until condition expires. `None` means permanent (no decay). Set by extractor, decremented by engine.

## ConditionAdd

- `id: str`
- `label: str`
- `description: str = ""`
- `turns_remaining: int | None = None` — optional duration; `None` means permanent.

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
- No `scene_pressure_remove` or `scene_pressure_update` (migrated to `ProgressExtractResult` in scene-progress-fixes plan).
- Fields: `scene_tags`, `scene_tagline`, `location_change`, `location_description`, `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update`.

## ProgressExtractResult

- `gm_beat: GMBeat | None = None` — validated by `_nullify_invalid_gm_beat` (model_validator, mode="after") which sets `gm_beat = None` if the beat has no instruction or no type.
- `scene_pressure_remove: list[str]` — migrated from `SceneExtractResult` in scene-progress-fixes plan.
- `scene_pressure_update: list[ScenePressure]` — migrated from `SceneExtractResult` in scene-progress-fixes plan.
- Fields: `quest_updates`, `recent_events_add`, `recent_events_update`, `recent_events_remove`, `actions`, `outcome_summary`, `gm_beat`, `beat_disposition`, `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update`.

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
