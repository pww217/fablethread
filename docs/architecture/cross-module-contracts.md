# Cross-Module Contracts

## EV checker library imports

`ccya/ev/checkers/` imports directly from `ccya/engine/config` (EngineConfig, PRESSURE_BEAT_TYPES) and `ccya/rules` (MOMENTUM_DELTA, BANDS). This is a deliberate dependency — checkers need engine constants to validate mechanical invariants. The checker library does NOT depend on the turn pipeline; it reads events.jsonl directly.

## Error propagation path (structured observability)

LLM failure in extraction → typed LlmcError raised with ErrorKind classification → caught by server middleware → persisted to `server_errors.jsonl` + SSE error event pushed via logging_setup.py. Engine modules use `_log = logging.getLogger(__name__)`; all log calls pass structured fields via `extra={}` (error_kind, trace_id). TurnResult.errors collected as list[dict] with ErrorKind constants. Server middleware catches unhandled exceptions and returns JSON responses instead of raw HTML error pages.

## Scene thread lifecycle (unified arc.threads[])

- All scene_pressure functionality migrated to arc.threads[] with `scope: scene` — ccya/engine/pressure.py module deleted in phase 06 validation sweep
- **Three-layer engine governance:** (1) Auto-dormant at 8+ turns with no activity (urgent threads excluded), (2) Urgency decay stepwise urgent→normal→background after `thread_urgency_max_age=8` turns at same level (Python-side floor), (3) Engine culling of dormant threads with ≥5 dormant count
- **Scene-scoped threads purged on location change:** `apply_delta()` in delta_builder.py removes all threads with `scope: "scene"` from `arc.threads[]` when `location_change` is present in the delta, since they are localized to the prior location

## Arc thread state machine

- States: ACTIVE → DORMANT (via auto-dormant at 8+ turns no activity, or record `thread_update` with dormant=True — Record replaces Storytell, same ownership) → COMPLETE/FAILED/ABANDONED (via thread_resolve or engine culling at ≥5 dormant). **Additional transitions:** urgent→normal→background via Python urgency decay pass; dormant threads with ≥5 dormant count trigger engine culling of oldest dormant
- Record (formerly Storytell) controls all thread state transitions via `thread_update` — engine applies them with cooldown enforcement (thread_creation_cooldown, thread_add only when turns since last add >= cooldown). Engine also enforces urgency decay (stepwise demotion), auto-dormant (8+ turns no activity), and culling (≥5 dormant → cull oldest).
- Engine owns thread creation (`added_turn`, `urgency_set_turn` set at creation time in turn.py thread_add path); record owns urgency/active/progress state
- TTL-based cleanup: completed threads and resolved arcs are pruned from prompt context after `thread_memory_ttl` / `arc_memory_ttl` turns (default 3)
- ArcThread.resolution_state: str | None — set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads for narrative context
  - ArcThread.outcome: str | None — set from ThreadResolution.outcome when moved to completed_threads
  - ArcThread.resolved_turn: int | None — turn when thread was resolved; used for TTL filtering in prompts
  - ArcThread.last_updated_turn: int | None — turn when thread was last updated (dormant, urgency, type, or progress change); persisted to state; used for auto-dormant detection and staleness display in prompts
  - ArcThread.added_turn: int | None — turn when thread was created (thread_add or seed); enables age calculations for decay/expiration passes
  - ArcThread.urgency_set_turn: int | None — turn when urgency was last set; enables Python-side urgency decay pass to measure how long a thread has been at its current level
  - ProgressEntry model: {kind: "advancement"|"setback", text: str} — structured progress replacing bare strings; ArcThread.progress: list[ProgressEntry]; ThreadUpdate.major_update_signal tags each emitted progress entry
- `_merge_arc_update` unconditionally replaces `arc["threads"]` and `arc["completed_threads"]` on every call

## EngineConfig field naming (Phase 06b)

- Config fields: thread_deescalate_on_success, arc_memory_ttl (default 3), thread_memory_ttl (default 3), thread_max_active (default 5), sanitize_every (default 5, 0=disabled). **Thread lifecycle enforcement:** thread_urgency_max_age (default 8, stepwise urgency decay threshold), thread_creation_cooldown (default 3, minimum turns between thread_add). YAML keys match Python field names directly. **Debug mode:** debug_mode (read from `game.debug.enabled` in config.yaml, default False) — gates streaming metadata display (scene_phase, outcome_hint, summary) in UI turn_complete handler. (gm_beat no longer in turn_complete SSE payload — beats flow through state.meta.pending_gm_beat; debug row reads from there if needed.)
- New in beat generation split: `world_temperature` (default 0.55) — temperature for World step (Step 2d, async) beat-candidate generation.
- Sampling parameters: ruling_temperature/ruling_top_p, extract_temperature/extract_top_p/extract_frequency_penalty, narrate_temperature/narrate_top_p/narrate_frequency_penalty, generate_seed_temperature/generate_seed_top_p, pack_generation_temperature/pack_generation_top_p; stub fields always null until mlx-lm SDK support: seed, top_k, min_p, rep_penalty, rep_penalty_window. Config structure migrated from flat keys to nested `llm.<stage>.<param>` format (Phase 08).

## Computation functions (Phase 06b)

- `_compute_narration_directive(scene_phase, thread_urgency_count, effective_scene_age, ...)` — purely age-based priority stack: Scene Imperative → Scene Pressure → empty. Removed Overwhelm/Pressure/Tension/Breathe directives (handled by phase).
- `_compute_pacing_context(scene_phase, thread_urgency_count, effective_scene_age, ...)` — returns PacingContext with directive, outcome_hint, spiral_detected, convergence_score, climax_turn_count fields.
- `_compute_scene_phase(state, ages, config, convergence_score=0)` — 5-state phase machine (SETUP→RISING→CLIMAX→RESOLUTION→BREATHER), mutates state["scene"] in place. RISING→CLIMAX transition driven by convergence_score ≥ threshold. climax_turn_count tracked in state["scene"].
- `_compute_ages(state)` returns only `{"scene_age": scene_age}` — location_age and combat_age removed in Phase 03 pacing overhaul; effective_scene_age set in _ruling_phase() by adding combat boost to scene_age.
- `ccya/engine/_pacing.py` — BEAT_PHASE_MAP, BEAT_BUCKETS, detect_spiral(), derive_allowed_beat_types(directive=, spiral_detected=), compute_convergence_score(scene_phase, active_threads, scene_age, recent_beats, config, turn_no, recent_rolls) → tuple[int, dict[str, int]] — beat constraint derivation with directive/spiral overrides, 6-component convergence score for RISING→CLIMAX transition. `detect_spiral()` uses rolling window of recent roll bands, configurable consecutive/ratio thresholds. `BEAT_BUCKETS` groups beat types into pressure/situation/relief functional buckets for phase-based filtering.

## Token budget cascade

`config.context_window` (default 32768): `llm_client.trim_messages()` drops/truncates oldest non-system messages when budget exceeded. Priority: system prompts retained first, then most recent user/context blocks. This affects all pipeline stages — if budget is tight, older turns in chronicle tail get truncated before narration/extraction contexts.

## Extraction field routing

- **SceneExtractResult**: compendium_npc_update (no pressure fields); CompendiumNpcUpdate has position field for NPC spatial positioning, `party` field for companion exemption from location-change auto-demotion; CompendiumEntry has explicit motivation/fear/leverage/bond/personality optional string fields alongside existing name/title/bio/presence/position; extraction system prompt (`extract_scene_system.j2`) includes proper-name heuristic for unnamed detection (2+ words, first and last capitalized), tiered NPC field requirements (named: `bio` + `personality` + 2+ fields; unnamed: `bio` only, no personality fields), a 12-archetype reference, and passive NPC extraction instructions; `departed_reason` is combined (label + prose); `allegiance` removed
- **StateExtractResult**: inventory_add/remove/update, pc_condition_add/remove (no `failed`), location_change, location_description; `condition_change_reason` required when any condition change is present (Pydantic-enforced, same pattern as `inventory_change_reason`); reason persisted to `state.meta.last_condition_change_reason` for debugging; `turns_remaining: int | Literal["permanent"]` on ConditionAdd — engine assigns default TTL (from `config.condition_default_ttl`, default 10) when LLM omits it; TTL decrement pass in `_expire_conditions()` in `turn_state.py`
- **StorytellerResult** (Record output — same model class, gm_beat field removed): thread_update (list[ThreadUpdate] with id/dormant/urgency/type/progress/major_update_signal), goal_update (dict | None, applied directly to arc dict — NOT through _merge_arc_update), arc_resolve (ArcResolution with resolution/long_term_objective), thread_resolve (list[ThreadResolution] with id/resolution_state/outcome + world_state_candidate for two-step world state promotion), thread_add (ArcThread | None, `added_turn` and `urgency_set_turn` set at creation time in turn.py); thread_add validated by id-based dedup only (no key, no fuzzy merge); thread_resolve processed by _apply_thread_resolutions() to move threads from arc.threads[] to arc.completed_threads[], persisting both resolution_state and outcome alongside the ArcThread
- **StateDelta.actions**: list[str], max_length=10 — merged from StorytellerResult.actions (Record output), persisted to state["pc"]["actions"] as rolling window by apply_delta()

## Cross-stream data flow (minimal by design)

- Scene → State: compendium_npc_update (upserts into state.compendium.npcs with presence field)
- State → merged: location_change (id,name,description) + location_description flow from StateExtractResult into merged StateDelta
- No items_gained/items_lost cross-stream fields exist (removed); extraction_ctx covers this-turn derived data

## Seed emotional context → narrator consumption

- **Seed generates**: `arc_origin` (seed-time only, 2–3 sentences past-tense explaining "how did the PC end up here?"), NPC `relation` field (narrative job relative to PC), action text (character-shaped, scene-grounded).
- **`arc_origin` is UI-only**: Rendered in the sidebar (`_state_left.html`). NOT rendered in narrator or record prompt context during gameplay.
- **Seed emotional framing contract**: The seed generation prompt enforces `arc_origin`, NPC `relation` field, PC situation schema, and character-shaped action text. This emotional data is embedded in the initial state and the sidebar, not reintroduced per-turn via prompts.
