# REPOMAP — module index, entry points, links to arch docs

## Module index (file → responsibility)

| File | Responsibility |
|---|---|
| `ccya/__main__.py` | CLI entry: argparse + uvicorn.run |
| `ccya/cli.py` | CLI commands |
| `ccya/models/` | Pydantic models: state, extraction, rules, config, compactor |
| `ccya/errors.py` | ErrorKind constants + LlmcError exception hierarchy |
| `ccya/engine/__init__.py` | Re-exports public APIs; LLM client re-exports; turn lock helpers |
| `ccya/engine/config.py` | EngineConfig dataclass (fields: roll_starvation_threshold, threat_density_threshold, stall_floor_max, extension_max, convergence_threshold, climax_turn_limit, etc.); CheckerConfig threshold fields; turn lock management; Jinja env setup |
| `ccya/engine/turn.py` | run_turn() orchestrator; pipeline (rules→narrate→scene/state/record); end-of-turn async phases (Sanitize + World) after yield("complete"); deferred atomic write block with last_turn_state capture (appended after async window); extraction_event includes world data under extraction.world |
| `ccya/engine/turn_context.py` | TurnContext + PacingContext dataclasses |
| `ccya/engine/turn_state.py` | State delta application: thread updates, arc resolution, thread resolutions, validation, NPC lifecycle decay, TTL condition expiration (_expire_conditions); LongTermObjective.started_turn on arc resolve |
| `ccya/engine/_pacing.py` | Beat constraints, 6-component convergence score (+stall_floor externally), spiral detection; `compute_convergence_score(scene_phase, active_threads, scene_age, recent_beats, config, turn_no, recent_rolls) -> tuple[int, dict[str, int]]`; `_compute_scene_phase(state, ages, config, total_convergence_score, turn_no)` |
| `ccya/engine/narrate.py` | Narration: prompt building, streaming, arc context; convergence score computation + stall_floor tracking via `consecutive_low_convergence`; pure reader of `state.meta.pending_gm_beat` |
| `ccya/engine/world.py` | World: async beat-candidate generation (Step 2d). Validates each candidate via `GMBeat`; strips to `{type, effect}` for ruling; returns (candidates, system_text, user_text, raw_response) for event recording; runs after Sanitize, before generator returns |
| `ccya/engine/pack_gen.py` | LLM-generated ScenarioBrief → packs/custom/ |
| `ccya/engine/names.py` | Name pool generation via Faker |
| `ccya/engine/ruling.py` | Ruling prompts + LLM call with retry; pc.situation in ruling context; index-based beat selection from `state.meta.beat_candidates`; sets/pops `state.meta.pending_gm_beat` and `state.meta.beat_candidates` per turn |
| `ccya/engine/extraction/` | Scene/state/record extraction pipeline (3 streams); `gm_beat` field removed from `StorytellerResult` |
| `ccya/engine/hints.py` | Hint generation for ruling context (pc.situation) |
| `ccya/engine/thread_sanitizer.py` | Batch arc/thread cleanup every N turns; atomic world_state swap |
| `ccya/engine/seed.py` | Dynamic pack seed generation; personality fallback |
| `ccya/engine/changes.py` | State diff → emoji display lines for UI |
| `ccya/engine/npc_roster.py` | NPC roster builder: presence filter, recency+richness scoring, top-12 selection |
| `ccya/engine/generate_pack.py` | SSE-driven ephemeral pack generation from world brief |
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | load_state, save_state (atomic), init_save_dir |
| `ccya/state/delta_builder.py` | apply_delta(), reconcile_delta(), _merge_arc_update() — condition/inventory dedup; assigns default TTL when LLM omits turns_remaining
| `ccya/state/inventory.py` | Inventory ID normalization + fuzzy matching |
| `ccya/state/npcs.py` | NPC alias map, compendium LRU, scene management |
| `ccya/state/chronicle.py` | Append events.jsonl, chronicle.md, load_last_narration(), remove_last_event() (removes all events for last turn number including sanitizer events) |
| `ccya/server/__init__.py` | Re-exports: app, main, config, SAVE_DIR |
| `ccya/server/app.py` | FastAPI bootstrap, Jinja env, startup event, error persistence |
| `ccya/server/routes.py` | All @app.get / @app.post route handlers; panel builders; save switching |
| `ccya/server/panels.py` | Panel context builders: debug, state, opening |
| `ccya/server/tv.py` | Turn viewer data from events.jsonl + server_errors.jsonl; pipeline stage rendering (ruling/narrate/scene/state/record/world) |
| `ccya/server/tv_mirror.py` | StreamDescriptor registry — single source of truth for pipeline topology (6 stages: ruling→narrate→scene→state→record→world) |
| `ccya/server/metrics.py` | Turn latency/token formatting |
| `scripts/debug/ev.py` | CLI tool: inspect events.jsonl (summary, timing, turn, prompt, checkers, play, eval) |
| `ccya/ev/events.py` | Shared data access: load_events(), find_turn(), filter_turn_events() |
| `ccya/ev/inspect.py` | Inspection commands: summary, timing, turn, prompt |
| `ccya/ev/deltas.py` | Deltas and mechanics commands |
| `ccya/ev/state_tools.py` | State commands: state, diff, trace, search, threads, beats |
| `ccya/ev/play.py` | Play command: single-turn/interactive/LLM modes |
| `ccya/ev/personality.py` | 8 personality presets + custom |
| `ccya/ev/session_config.py` | Session config: ev.yaml loading, flag resolution |
| `ccya/ev/init.py` | Creates save dir + ev.yaml |
| `ccya/ev/status.py` | Session dashboard from state.yaml + ev.yaml |
| `ccya/ev/check.py` | Run checkers against events by turn |
| `ccya/ev/audit.py` | Audit commands: state history, conditions, NPC ghosting, storyteller, threads |
| `ccya/ev/compat.py` | Detects changes vs extraction_context format mismatches |
| `ccya/ev/eval.py` | Batch scenario runner: YAML scenarios → checkers → Markdown report; `eval compare` for cross-run checker comparison |
| `ccya/ev/prompt_eval.py` | Fast prompt testing: dump (render only), call (render + LLM + check) |
| `ccya/ev/scenario.py` | YAML scenario loader: Scenario, TurnAssert dataclasses |
| `ccya/ev/__init__.py` | CLI dispatch: lazy import of subcommands |
| `ccya/ev/checkers/` | Checker framework: @register_checker, 28 deterministic + 3 LLM checkers |
| `ccya/ev/checkers/ruling.py` | Ruling checkers: `ruling_reason_quality`, `ruling_band_distribution`, `ruling_intent_match` |
| `ccya/ev/checkers/convergence.py` | Convergence checker: `convergence_components` |
| `ccya/ev/checkers/state.py` | State checkers: `location_description_consistency`, `world_state_facts` |
| `ccya/personality.py` | NpcPersonality dataclass; 12 archetype registry; assign_personality() |
| `ccya/pack.py` | load_pack(), list_packs() — validates pack has seed or scenario; PackManifest.checkers for pack-level checker overrides |
| `ccya/rules.py` | Pure-Python dice resolver: resolve_check() (1d12+stat_mod+diff_mod→Band) |
| `ccya/llm_client.py` | chat(), chat_stream() — OpenAI-compatible → mlx_lm.server; trim_messages() |
| `ccya/logging_setup.py` | JSONL RotatingFileHandler + _JsonFormatter; StreamHandler |
| `ccya/prompts/` | Jinja2 prompt templates (system + user) + shared includes (sections/) |
| `ccya/templates/` | HTML UI templates (sidebar, modals, character sheets) |
| `ccya/static/tokens.css` | Design tokens, base reset, fluid typography |
| `ccya/static/app-shell.css` | Main game UI — shell layout, header, narrative column, sidebars, modals, responsive rules |
| `ccya/static/chronicle.css` | Chronicle overlay — turn log shell, panel, scrollbar |
| `ccya/static/turn-viewer.css` | Standalone full-page debug turn viewer |
| `ccya/static/game-utils.js` | Pure utility functions — markdown, entities, tooltips, display drain, pills |
| `ccya/static/game.js` | Alpine components — `charCreation()`, `worldBuilder()`, `game()` |
| `ccya/static/app-init.js` | DOM initialization — `DOMContentLoaded` handlers, HTMX wiring, pills layout |

## Key entry points

- **run_turn()** → `ccya/engine/turn.py` — pipeline orchestrator (rules→narrate→scene/state/record extract + end-of-turn Sanitize + World)
- **load_state()** → `ccya/state/io.py` — loads YAML state
- **save_state()** → `ccya/state/io.py` — atomic write (tmp + rename)
- **apply_delta()** → `ccya/state/delta_builder.py` — merges extraction results into state
- **app** → `ccya/server/__init__.py` — FastAPI instance with ~25 routes
- **load_pack()** → `ccya/pack.py` — loads scenario.yaml packs
- **resolve_check()** → `ccya/rules.py` — 1d12+stat_mod+diff_mod→Band (pure Python)
- **chat()** → `ccya/llm_client.py` — non-streaming LLM call with retry
- **chat_stream()** → `ccya/llm_client.py` — streaming tokens

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

- **EV checkers** import from `ccya/engine/config` and `ccya/rules` deliberately — checkers need engine constants to validate mechanical invariants. Checkers read events.jsonl directly, not the turn pipeline.
- **Error propagation**: LLM failure → typed LlmcError → server middleware → server_errors.jsonl + SSE error event. Engine modules use structured logging via `extra={}` (error_kind, trace_id).
- **Thread lifecycle**: Three-layer governance (auto-dormant at 8 turns, urgency decay at 8 turns, completion threshold auto-resolve). Scene-scoped threads purged on location change. State key: `state["long_term_objective"]` (renamed from `state["arc"]`). Model: `LongTermObjective` (renamed from `CampaignArc`). See [cross-module-contracts.md](./architecture/cross-module-contracts.md) for full state machine.
- **World state lifecycle**: `ThreadResolution.world_state_candidate` collected in `_apply_thread_resolutions()`. Two-step promotion: storyteller proposes (stored as `world_state_candidates` in state), thread sanitizer evaluates via atomic `world_state` swap (complete replacement array). TTL expiry pass in `_apply_state_updates()` removes facts whose `expires_turn` has passed. Valence enum: threat, complication, neutral, boon. Tier: global (immutable) or local (may expire). See [state-models.md](./architecture/state-models.md) for model details.
- **Extraction routing**: SceneExtractResult (tagline, location, NPC updates, candidate_npcs), StateExtractResult (inventory, conditions), StorytellerResult (threads, goals, arcs — `gm_beat` field removed; beats are now World→Ruling flow). See [state-models.md](./architecture/state-models.md) for field routing details.
- **Token budget**: `config.context_window` (default 32768) — trim_messages() drops oldest non-system messages. Affects all pipeline stages.
- **Prompt architecture**: Two template systems (prompt templates in `ccya/prompts/`, UI templates in `ccya/templates/`). See [prompts-architecture.md](./architecture/prompts-architecture.md) for rendering flow.
