# models.py — Pydantic models

## Pydantic models

`Condition`, `ConditionAdd`, `ConditionRemove`, `RulesCheck`, `Scope`, `IntentEnvelope`, `RulesOutcome`, `InventoryItem`, `InventoryRemove`, `InventoryUpdate`, `LocationRef`, `QuestObjective`, `QuestObjectiveUpdate`, `QuestUpdate`, `NpcRef`, `NpcAdd`, `NpcRemove`, `NpcUpdate`, `CompendiumNpcUpdate`, `RecentEvent`, `RecentEventUpdate`, `ScenePressure` (urgency: `immediate`/`building`/`background`/`pacing`), `StateDelta`, `SceneExtractResult`, `StateExtractResult`, `GMBeat`, `ProgressExtractResult`, `CompactorNpcMerge`, `CompactorRecentEventCompact`, `CompactorSanitizationResult`.

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
- `actions: list[str] = Field(default_factory=list)` — coerced by `_coerce_actions` (handles dicts/strings). Warns via `_warn_empty_actions` (model_validator, mode="after") when empty to surface silent-fallback issues in logs.
- `scene_pressure_remove: list[str]` — migrated from `SceneExtractResult` in scene-progress-fixes plan.
- `scene_pressure_update: list[ScenePressure]` — migrated from `SceneExtractResult` in scene-progress-fixes plan.
- `drift_analysis: list[DriftAnalysis] = Field(default_factory=list)` — coerced by `_coerce_drift_analysis` (field_validator, mode="before") which remaps `id` → `thread_id` and drops items with no identity key. Supersedes `player_drift_signals`.
- `player_drift_signals: list[str] = Field(default_factory=list)` — DEPRECATED: use drift_analysis instead.
- Fields: `quest_updates`, `recent_events_add`, `recent_events_update`, `recent_events_remove`, `actions`, `outcome_summary`, `gm_beat`, `beat_disposition`, `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update`.

## CompactorRecentEventCompact

- `id: str` — new snake_case ID for the consolidated event
- `text: str` — consolidated narrative text, in-universe phrasing
- `turn: int = 0` — turn this event originated from (for ordering)

## CompactorSanitizationResult

- `npc_merge: list[CompactorNpcMerge]` — NPC dedup merges
- `inventory_remove: list[CompactorSanitizationAction]` — coerced by `_coerce_actions` (field_validator, mode="before") which converts bare strings to `{"id": str, "confidence": "high"}` dicts
- `pressure_remove: list[CompactorSanitizationAction]` — coerced by `_coerce_actions` (same as above)
- `condition_remove: list[CompactorSanitizationAction]` — coerced by `_coerce_actions` (same as above)
- `recent_events_compact: list[CompactorRecentEventCompact]` — consolidated recent_events from compactor
- `_coerce_sanitization_actions` (module-level helper) — converts bare strings to `{"id": str, "confidence": "high"}` dicts for the three action lists above

## CampaignArc

- `visible_goal: str` — player-facing objective
- `thematic_question: str` — emotional register question
- `phase: ArcPhase = ArcPhase.SETUP` — arc phase enum
- `hidden_truths: list[str] = Field(default_factory=list)` — designer-only structural spine, never shown to player
- `discovered_truths: list[str] = Field(default_factory=list)` — truths the player has learned through play; starts empty, populated by future truth-promotion mechanism
- `active_threads: list[ArcThread] = Field(default_factory=list)` — situations currently in play
- `latent_threads: list[ArcThread] = Field(default_factory=list)` — threads not yet active
- `completed_threads: list[ArcThread] = Field(default_factory=list)` — finished/expired threads
- `arc_engagement: int = 0` — engagement metric (±1 per turn based on drift overlap)
- `pc_drive: str = ""` — PC's personal motivation for being in this situation

## ArcThread

- `id: str` — slugified unique identifier
- `summary: str` — 2–4 sentence situation description
- `tags: list[str] = Field(default_factory=list)` — semantic tags for salience scoring
- `state: ThreadState = ThreadState.LATENT` — latent/active/complete/failed/expired
- `urgency: str = "normal"` — normal/immediate
- `progress: int = 0` — advancement counter
- `unlock_if: str | None = None` — plain-language condition for activation
- `promotes: list[str] = Field(default_factory=list)` — thread IDs to activate on completion
- `last_offered_turn: int | None = None` — turn when last promoted to active

## ArcPhase (Enum)

- `SETUP = "setup"`
- `PURSUIT = "pursuit"`
- `REVERSAL = "reversal"`
- `CRISIS = "crisis"`
- `RESOLUTION = "resolution"`

## ThreadState (Enum)

- `LATENT = "latent"`
- `ACTIVE = "active"`
- `COMPLETE = "complete"`
- `FAILED = "failed"`
- `EXPIRED = "expired"`

## ThreadSignal

- `id: str` — thread ID
- `signal: ThreadSignalType` — advanced/blocked/failed/ignored

## DriftAnalysis

- `thread_id: str` — thread being analyzed
- `match: bool = False` — whether the player's action meaningfully engaged this thread
- `reason: str = ""` — one-sentence explanation of why this thread was or wasn't matched
- `new_interest: str = ""` — if match is False, what new direction the player seems interested in

## ThreadSignalType (Enum)

- `ADVANCED = "advanced"`
- `BLOCKED = "blocked"`
- `FAILED = "failed"`
- `IGNORED = "ignored"`

## Type aliases

- `SkillName` (6 skills)
- `Difficulty` (5 levels)
- `Band` (7 PbtA bands)
