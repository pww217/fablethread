# REPOMAP — module index, entry points, links to arch docs

## Module index (file → responsibility)

| File | Responsibility |
|---|---|
| `ccya/__main__.py` | CLI entry: argparse + uvicorn.run |
| `ccya/cli.py` | CLI commands |
| `ccya/models/` | Pydantic models: state, extraction, rules, config, compactor |
| `ccya/errors.py` | ErrorKind constants + LlmcError exception hierarchy |
| `ccya/engine/__init__.py` | Re-exports public APIs; LLM client re-exports; turn lock helpers |
| `ccya/engine/config.py` | EngineConfig dataclass; turn lock management; Jinja env setup |
| `ccya/engine/turn.py` | run_turn() orchestrator; arc/thread state machine; pacing computation |
| `ccya/engine/turn_context.py` | TurnContext + PacingContext dataclasses |
| `ccya/engine/turn_state.py` | State delta application: thread updates, arc resolution, NPC lifecycle |
| `ccya/engine/_pacing.py` | Beat constraints, convergence score, spiral detection |
| `ccya/engine/narrate.py` | Narration: prompt building, streaming, arc context |
| `ccya/engine/pack_gen.py` | LLM-generated ScenarioBrief → packs/custom/ |
| `ccya/engine/names.py` | Name pool generation via Faker |
| `ccya/engine/ruling.py` | Ruling prompts + LLM call with retry |
| `ccya/engine/extraction/` | Scene/state/storytell extraction pipeline (3 streams) |
| `ccya/engine/thread_sanitizer.py` | Batch arc/thread cleanup every N turns |
| `ccya/engine/seed.py` | Dynamic pack seed generation; personality fallback |
| `ccya/engine/changes.py` | State diff → emoji display lines for UI |
| `ccya/engine/npc_roster.py` | NPC roster builder with presence tags + personality resolution |
| `ccya/engine/generate_pack.py` | SSE-driven ephemeral pack generation from world brief |
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | load_state, save_state (atomic), init_save_dir |
| `ccya/state/delta.py` | apply_delta(), reconcile_delta() — condition/inventory dedup |
| `ccya/state/inventory.py` | Inventory ID normalization + fuzzy matching |
| `ccya/state/npcs.py` | NPC alias map, compendium LRU, scene management |
| `ccya/state/chronicle.py` | Append events.jsonl, chronicle.md, load_last_narration() |
| `ccya/server/__init__.py` | Re-exports: app, main, config, SAVE_DIR |
| `ccya/server/app.py` | FastAPI bootstrap, Jinja env, startup event, error persistence |
| `ccya/server/routes.py` | All @app.get / @app.post route handlers; panel builders; save switching |
| `ccya/server/panels.py` | Panel context builders: debug, state, opening |
| `ccya/server/tv.py` | Turn viewer data from events.jsonl + server_errors.jsonl |
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
| `ccya/ev/eval.py` | Batch scenario runner: YAML scenarios → checkers → Markdown report |
| `ccya/ev/prompt_eval.py` | Fast prompt testing: dump (render only), call (render + LLM + check) |
| `ccya/ev/scenario.py` | YAML scenario loader: Scenario, TurnAssert dataclasses |
| `ccya/ev/__init__.py` | CLI dispatch: lazy import of subcommands |
| `ccya/ev/checkers/` | Checker framework: @register_checker, 27 deterministic + 3 LLM checkers |
| `ccya/personality.py` | NpcPersonality dataclass; 12 archetype registry; assign_personality() |
| `ccya/pack.py` | load_pack(), list_packs() — validates pack has seed or scenario |
| `ccya/rules.py` | Pure-Python dice resolver: resolve_check() (1d12+stat_mod+diff_mod→Band) |
| `ccya/llm_client.py` | chat(), chat_stream() — OpenAI-compatible → mlx_lm.server; trim_messages() |
| `ccya/logging_setup.py` | JSONL RotatingFileHandler + _JsonFormatter; StreamHandler |
| `ccya/prompts/` | Jinja2 prompt templates (system + user) + shared includes (sections/) |
| `ccya/templates/` | HTML UI templates (sidebar, modals, character sheets) |

## Key entry points

- **run_turn()** → `ccya/engine/turn.py` — 5-call pipeline orchestrator (rules→narrate→scene/state/storytell extract)
- **load_state()** → `ccya/state/io.py` — loads YAML with migration normalization
- **save_state()** → `ccya/state/io.py` — atomic write (tmp + rename)
- **apply_delta()** → `ccya/state/delta.py` — merges extraction results into state
- **app** → `ccya/server/__init__.py` — FastAPI instance with ~25 routes
- **load_pack()** → `ccya/pack.py` — validates pack has seed_state.yaml or scenario.yaml
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
| **Step 2c — Storytell** | [step2c-storytell.md](./architecture/step2c-storytell.md) |
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
- **Thread lifecycle**: Three-layer governance (auto-dormant at 4 turns, urgency decay at 8 turns, completion threshold auto-resolve). Scene-scoped threads purged on location change. See [cross-module-contracts.md](./architecture/cross-module-contracts.md) for full state machine.
- **Extraction routing**: SceneExtractResult (tagline, location, NPC updates), StateExtractResult (inventory, conditions), StorytellerResult (threads, goals, arcs, beats). See [state-models.md](./architecture/state-models.md) for field routing details.
- **Token budget**: `config.context_window` (default 32768) — trim_messages() drops oldest non-system messages. Affects all pipeline stages.
- **Prompt architecture**: Two template systems (prompt templates in `ccya/prompts/`, UI templates in `ccya/templates/`). See [prompts-architecture.md](./architecture/prompts-architecture.md) for rendering flow.
