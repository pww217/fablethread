# REPOMAP — module index, entry points, links to arch docs

## Module index (file → responsibility)

| File | Responsibility |
|---|---|
| `fablethread/__main__.py` | CLI entry: argparse + uvicorn.run |
| `fablethread/cli.py` | CLI commands |
| `fablethread/models/` | Pydantic models: state, extraction, rules, config; `CompendiumNpcAdd` (write-once: seed + first appearance), `CompendiumNpcUpdate` (updatable: subsequent scenes); `NPCEntry` has `disposition` field |
| `fablethread/errors.py` | ErrorKind constants + LlmcError exception hierarchy |
| `fablethread/engine/__init__.py` | Re-exports public APIs; LLM client re-exports; turn lock helpers |
| `fablethread/engine/config.py` | EngineConfig dataclass (fields: convergence_alpha, convergence_enter_threshold, convergence_exit_threshold, RISING_min, CLIMAX_min, BREATHER_min, climax_turn_limit, extension_max, roll_starvation_threshold, threat_density_threshold, prepare_seed_temperature=0.4, prepare_seed_top_p=0.95, etc.); CheckerConfig threshold fields; turn lock management; Jinja env setup |
| `fablethread/engine/turn.py` | `run_turn()` orchestrator (~210 lines, down from 667); extracted subroutines: `_narrate_phase()` (narration streaming), `_extract_phase()` (extraction pipeline + metrics), `_apply_phase()` (delta application + rejection), `_persist_and_async_cleanup()` (event building, prompt logging, async sanitize/world, save); pipeline (rules→narrate→extract→apply→persist); end-of-turn async phases (Sanitize + World) after yield("complete"); deferred atomic write block with last_turn_state capture; events.jsonl includes `scene.total_ms`, `state.total_ms`, `record.total_ms` top-level fields for per-sub-stream duration tracking |
| `fablethread/engine/turn_context.py` | TurnContext + PacingContext dataclasses |
| `fablethread/engine/turn_state.py` | State delta application: thread updates, arc resolution, thread resolutions, validation, NPC lifecycle decay, TTL condition expiration (`_expire_conditions` — delegates decrement/removal to `state.expire_conditions()`); LongTermObjective.started_turn on arc resolve; location-change NPC demotion: `last_seen_location` stamping guard (new NPCs get location stamped, existing NPCs keep tracked location); compendium update handler with `last_presence_turn` tracking |
| `fablethread/engine/_pacing.py` | Beat constraints (BEAT_BUCKETS: tension/discovery/respite, no hazard), convergence score (urgent_thread 0-2 count-capped), hysteresis + min_turns phase transitions; `compute_convergence_score(scene_phase, active_threads, recent_beats, config, turn_no, recent_rolls) -> tuple[int, dict[str, int]]`; `_compute_scene_phase(state, ages, config, smoothed_convergence, turn_no)` |
| `fablethread/engine/narrate.py` | Narration: prompt building, streaming, arc context; convergence score computation + EMA smoothing; pure reader of `state.meta.pending_gm_beat` |
| `fablethread/engine/world.py` | World: async beat-candidate generation (Step 2d). Reads NPC profiles from compendium via `build_npc_roster()`; validates each candidate via `GMBeat`; filters against `allowed_beat_types` (phase constraint); strips to `{type, effect, npcs}` for ruling; returns (candidates, system_text, user_text, raw_response) for event recording; runs after Sanitize, before generator returns |
| `fablethread/engine/pack_gen.py` | LLM-generated ScenarioBrief → packs/custom/ |
| `fablethread/engine/names.py` | Name pool generation via Faker |
| `fablethread/engine/ruling.py` | Ruling prompts + LLM call with retry; `_filter_pc_situation()` filters pc.situation to persist=true keys from `state.pc_situation_schema`; index-based beat selection from `state.meta.beat_candidates`; validates selected beat type against `allowed_beat_types` (phase constraint); passes npcs through to pending_gm_beat; sets/pops `state.meta.pending_gm_beat` and `state.meta.beat_candidates` per turn |
| `fablethread/engine/extraction/` | Scene/state/record extraction pipeline (3 streams); two-channel NPC extraction (`compendium_npc_add` for new NPCs, `compendium_npc_update` for existing); `_run_extraction_pipeline` threads `save_dir` through streams; `extract_stream_done` events include `expected_ms`; `gm_beat` field removed from `StorytellerResult`; `candidate_npcs` removed from `SceneExtractResult`; `pacing_context` removed from pipeline signature (World reads directly from turn.py); `rules_outcome` replaced with `band` parameter; dedup pipeline handles both Add and Update arrays |
| `fablethread/engine/narrate.py` | Narrate prompt building; `_filter_pc_situation()` filters pc.situation to persist=true keys from `state.pc_situation_schema`; narrate_user.j2 includes `pc_situation` section (previously only ruling had it) |
| `fablethread/engine/hints.py` | Hint generation for ruling context (pc.situation) |
| `fablethread/engine/thread_sanitizer.py` | Batch arc/thread cleanup every N turns; atomic world_state swap |
| `fablethread/engine/seed.py` | prepare_seed() → SeedStateEnvelope (temp 0.4), narrate_seed() → opening_narrative/actions (temp 0.9); personality fallback |
| `fablethread/engine/changes.py` | State diff → emoji display lines for UI |
| `fablethread/engine/npc_roster.py` | NPC roster builder: presence filter, recency+richness scoring, top-12 selection; imports `is_named` and `strip_non_ascii` from `fablethread.engine.utils` |
| `fablethread/engine/utils.py` | Shared pure helpers: `is_named()` proper-name heuristic, `strip_non_ascii()` (precompiled regex), `coerce_condition_str()` — single source of truth for the condition/NPC text utilities |
| `fablethread/engine/generate_pack.py` | SSE-driven ephemeral pack generation from world brief |
| `fablethread/state/__init__.py` | Re-exports all state symbols |
| `fablethread/state/io.py` | load_state, save_state (atomic), init_save_dir, default_world_state() |
| `fablethread/state/delta_builder.py` | apply_delta(), reconcile_delta(), _merge_arc_update() — condition/inventory dedup; assigns default TTL when LLM omits turns_remaining; imports `strip_non_ascii` from `fablethread.engine.utils`
| `fablethread/state/inventory.py` | Inventory ID normalization + fuzzy matching |
| `fablethread/state/npcs.py` | Compendium LRU, scene management (`apply_npc_scene_management` with dual-write: Add path creates new NPCs with write-once fields + Add-for-existing-NPC guard; Update path merges updatable fields; location-change demotion guard: `presence='present'` at old location auto-demotes to `nearby`, `touch_compendium_order`); imports `is_named` and `strip_non_ascii` from `fablethread.engine.utils` |
| `fablethread/state/chronicle.py` | Append events.jsonl, chronicle.md, load_last_narration(), remove_last_event() (removes all events for last turn number including sanitizer events) |
| `fablethread/server/__init__.py` | Re-exports: app, main, config, SAVE_DIR |
| `fablethread/server/app.py` | FastAPI bootstrap, Jinja env, startup event, error persistence |
| `fablethread/server/routes.py` | All @app.get / @app.post route handlers; panel builders; save switching; `POST /api/npc/{id}/toggle-party` (toggle NPC party membership), `POST /api/inventory/drop` (remove inventory items) |
| `fablethread/server/panels.py` | Panel context builders: debug, state, opening |
| `fablethread/server/tv.py` | Turn viewer data from events.jsonl + server_errors.jsonl; pipeline stage rendering (ruling/narrate/scene/state/record/world) |
| `fablethread/server/tv_mirror.py` | StreamDescriptor registry — single source of truth for pipeline topology (6 stages: ruling→narrate→scene→state→record→world) |
| `fablethread/server/metrics.py` | Turn latency/token formatting |
| `scripts/debug/ev.py` | CLI tool: inspect events.jsonl (summary, timing, turn, prompt, checkers, play, eval) |
| `scripts/validate_packs.py` | Static pack validation — loads every pack and validates structural integrity (CI/pre-commit/manual) |
| `fablethread/ev/events.py` | Shared data access: load_events(), find_turn(), filter_turn_events() |
| `fablethread/ev/inspect.py` | Inspection commands: summary, timing, turn, prompt |
| `fablethread/ev/deltas.py` | Deltas and mechanics commands |
| `fablethread/ev/state_tools.py` | State commands: state, diff, trace, search, threads, beats |
| `fablethread/ev/play.py` | Play command: single-turn/interactive/LLM modes. PC prompt includes inventory, arc goal, recent turns (last 2-3 actions + outcomes), latest narrative |
| `fablethread/ev/persona.py` | 9 persona presets + custom. Aggressive, cautious, absurd, explorer, driven, opportunist, completionist, speedrunner, custom. Each includes arc goal priority, self-preservation, concrete action rule, decision framework, persona-specific style, explicit repetition-avoidance rule |
| `fablethread/ev/session_config.py` | Session config: ev.yaml loading, flag resolution |
| `fablethread/ev/init.py` | Creates save dir + ev.yaml |
| `fablethread/ev/status.py` | Session dashboard from state.yaml + ev.yaml |
| `fablethread/ev/check.py` | Run checkers against events by turn |
| `fablethread/ev/audit.py` | Audit commands: state history, conditions, NPC ghosting, storyteller, threads |
| `fablethread/ev/compat.py` | Detects changes vs extraction_context format mismatches |
| `fablethread/ev/eval.py` | Batch scenario runner: YAML scenarios → checkers → Markdown report; `eval compare` for cross-run checker comparison |
| `fablethread/ev/prompt_eval.py` | Fast prompt testing: dump (render only), call (render + LLM + check) |
| `fablethread/ev/scenario.py` | YAML scenario loader: Scenario, TurnAssert dataclasses |
| `fablethread/ev/__init__.py` | CLI dispatch: lazy import of subcommands |
| `fablethread/ev/checkers/` | Checker framework: @register_checker, 28 deterministic + 3 LLM checkers |
| `fablethread/ev/checkers/ruling.py` | Ruling checkers: `ruling_reason_quality`, `ruling_band_distribution`, `ruling_intent_match` |
| `fablethread/ev/checkers/convergence.py` | Convergence checker: `convergence_components` |
| `fablethread/ev/checkers/pacing_convergence.py` | Phase transition signals, convergence recomputation (6 components, no stall_floor), directive-beat alignment |
| `fablethread/ev/checkers/state.py` | State checkers: `location_description_consistency`, `world_state_facts` |
| `fablethread/personality.py` | NpcPersonality dataclass; 12 archetype registry; assign_personality() |
| `fablethread/pack.py` | SeedStateEnvelope (wraps SeedState without narrative min_length), SeedEnvelope, load_pack(), list_packs(), validate_pack(), _validate_pool_entries() — validates pack has seed or scenario; PackManifest.checkers for pack-level checker overrides |
| `fablethread/rules.py` | Pure-Python dice resolver: `_adjust_difficulty()` (stat-based difficulty adjustment), `resolve_check()` (1d12+stat_mod+diff_mod→Band), `compute_band()`, `build_directive()` |
| `fablethread/llm_client.py` | chat(), chat_stream(), chat_with_config(), chat_stream_with_config() — OpenAI-compatible; trim_messages() |
| `fablethread/logging_setup.py` | JSONL RotatingFileHandler for `logs/game.log` + console handler; `setup_server_logging()` for `logs/server.log` |
| `fablethread/prompts/` | Jinja2 prompt templates (system + user) + shared includes (sections/) |
| `fablethread/templates/` | HTML UI templates (sidebar, modals, character sheets) |
| `fablethread/static/tokens.css` | Design tokens, base reset, fluid typography |
| `fablethread/static/app-shell.css` | Main game UI — shell layout, header, narrative column, sidebars, modals, responsive rules |
| `fablethread/static/chronicle.css` | Chronicle overlay — turn log shell, panel, scrollbar |
| `fablethread/static/turn-viewer.css` | Standalone full-page debug turn viewer |
| `fablethread/static/game-utils.js` | Pure utility functions — markdown, entities, tooltips, display drain, pills, extraction row lifecycle (`_showExtractionRow()`, `_activateExtractionBar()`, `_completeExtractionBar()`, `_dismissExtractionRow()`), pre-stream bar lifecycle (`_showPreStreamBar()`, `_updatePreStreamExpectedMs()`, `_dismissPreStreamBar()`, `_getPreStreamFallbackMs()`); extraction row no longer has an outer grey wrapper (de-wrappered in Phase 02 of I-44) |
| `fablethread/static/game.js` | Alpine components — `charCreation()`, `worldBuilder()`, `game()` |
| `fablethread/static/app-init.js` | DOM initialization — `DOMContentLoaded` handlers, HTMX wiring, pills layout |

## Key entry points

- **run_turn()** → `fablethread/engine/turn.py` — pipeline orchestrator (rules→narrate→scene/state/record extract + end-of-turn Sanitize + World)
- **load_state()** → `fablethread/state/io.py` — loads YAML state
- **save_state()** → `fablethread/state/io.py` — atomic write (tmp + rename)
- **apply_delta()** → `fablethread/state/delta_builder.py` — merges extraction results into state
- **app** → `fablethread/server/__init__.py` — FastAPI instance with ~25 routes
- **load_pack()** → `fablethread/pack.py` — loads scenario.yaml packs (validates after loading)
- **validate_pack()** → `fablethread/pack.py` — structural validation gate for all packs (called by load_pack and list_packs); checks manifest fields, world facts minimum, pool min counts + uniqueness, faction/schema/bundle uniqueness
- **resolve_check()** → `fablethread/rules.py` — `_adjust_difficulty()` (stat-based difficulty adjustment), then 1d12+stat_mod+diff_mod→Band (pure Python)
- **chat()** → `fablethread/llm_client.py` — non-streaming LLM call with retry
- **chat_stream()** → `fablethread/llm_client.py` — streaming tokens

## Arch doc index

| Subsystem | Doc |
|---|---|
| **Pipeline overview** | [OVERVIEW.md](./architecture/OVERVIEW.md) |
| **Step 0 — Ruling/Intent** | [step0-ruling.md](./architecture/step0-ruling.md) |
| **Step 1 — Narrate** | [step1-narrate.md](./architecture/step1-narrate.md) |
| **Step 2a — Scene Extract** | [step2a-scene.md](./architecture/step2a-scene.md) |
| **Step 2b — State Extract** | [step2b-state.md](./architecture/step2b-state.md) |
| **Step 2c — Record** | [step2c-record.md](./architecture/step2c-record.md) | Backward-looking scribe (replaces Storytell); threads + actions + outcome_summary |
| **Step 2d — World** | [step2d-world.md](./architecture/step2d-world.md) | Async beat-candidate generation; runs after yield("complete") in the end-of-turn async window |
| **Pacing systems** | [pacing-systems.md](./architecture/pacing-systems.md) |
| **Delta → Validate → Apply** | [delta-validate.md](./architecture/delta-validate.md) |
| **Persist** | [persist.md](./architecture/persist.md) |
| **Cross-pipeline data flow** | [cross-pipeline.md](./architecture/cross-pipeline.md) |
| **Out-of-band pipelines** | [out-of-band.md](./architecture/out-of-band.md) |
| **State models** | [state-models.md](./architecture/state-models.md) |
| **Cross-module contracts** | [cross-module-contracts.md](./architecture/cross-module-contracts.md) |
| **Prompts architecture** | [prompts-architecture.md](./architecture/prompts-architecture.md) |
| **Engine overhaul checklist** | [engine-overhaul-checklist.md](../engine-overhaul-checklist.md) | 16-domain checklist for validating engine changes
| **Narration UI** | [narration-ui.md](./architecture/narration-ui.md) |
| **Turn viewer UI** | [turn-viewer-ui.md](./architecture/turn-viewer-ui.md) |
| **Logging standards** | [logging-standards.md](./architecture/logging-standards.md) |

## EV doc index

| Task | Doc |
|---|---|
| **ev.py commands** | [COMMANDS.md](../ev/COMMANDS.md) |
| **Checkers reference** | [CHECKERS.md](../ev/CHECKERS.md) |
| **Eval run storage** | [EVAL-RUNS.md](../ev/EVAL-RUNS.md) |
| **State reference** | [STATE-REFERENCE.md](../ev/STATE-REFERENCE.md) |
| **Eval scenarios** | [RUBRIC.md](../ev/RUBRIC.md) |

## Cross-module contracts (summary)

- **EV checkers** import from `fablethread/engine/config` and `fablethread/rules` deliberately — checkers need engine constants to validate mechanical invariants. Checkers read events.jsonl directly, not the turn pipeline.
- **Error propagation**: LLM failure → typed LlmcError → server middleware → `logs/server.log` (rotated) + `saves/server_errors.jsonl` (for turn viewer) + SSE error event. Engine modules use structured logging via `extra={}` (error_kind, trace_id).
- **Thread lifecycle**: Three-layer governance (auto-dormant at 8 turns, urgency decay at 8 turns, completion threshold auto-resolve). Scene-scoped threads purged on location change. State key: `state["long_term_objective"]` (renamed from `state["arc"]`). Model: `LongTermObjective` (renamed from `CampaignArc`). See [cross-module-contracts.md](./architecture/cross-module-contracts.md) for full state machine.
- **World state lifecycle**: `ThreadResolution.world_state_candidate` collected in `_apply_thread_resolutions()`. Two-step promotion: storyteller proposes (stored as `world_state_candidates` in state), thread sanitizer evaluates via atomic `world_state` swap (complete replacement array). TTL expiry pass in `_apply_state_updates()` removes facts whose `expires_turn` has passed. Valence enum: threat, complication, neutral, boon. Tier: global (immutable) or local (may expire). See [state-models.md](./architecture/state-models.md) for model details.
- **Extraction routing**: Two-channel NPC extraction — `SceneExtractResult` carries `compendium_npc_add` (new NPCs, write-once fields) and `compendium_npc_update` (existing NPCs, updatable fields only). `StateMerge` carries both arrays into `apply_delta()`. `apply_npc_scene_management()` handles Add path (create new NPCs, reject if existing) and Update path (merge updatable fields). Scene/state/record extraction pipeline (3 streams); `_run_extraction_pipeline` threads `save_dir` through streams; `extract_stream_done` events include `expected_ms`; dedup pipeline handles both Add and Update arrays. `candidate_npcs` removed from `SceneExtractResult`; `pacing_context` removed from pipeline signature (World reads directly from turn.py); `rules_outcome` replaced with `band` parameter. World reads NPC profiles directly from compendium via `build_npc_roster()` instead of receiving `candidate_npcs` from scene. GMBeat output includes `npcs` (validated required for NPC-driven beats). See [state-models.md](./architecture/state-models.md) for field routing details.
- **Token budget**: `config.context_window` (default 32768) — trim_messages() drops oldest non-system messages. Affects all pipeline stages.
- **Prompt architecture**: Two template systems (prompt templates in `fablethread/prompts/`, UI templates in `fablethread/templates/`). See [prompts-architecture.md](./architecture/prompts-architecture.md) for rendering flow.
