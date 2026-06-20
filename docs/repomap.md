# REPOMAP — module boundaries, public APIs, cross-module contracts

## Module index (file → responsibility)

| File | Responsibility |
|---|---|
| `ccya/__main__.py` | CLI entry: argparse + uvicorn.run |
| `ccya/cli.py` | CLI commands |
| `ccya/models.py` | All Pydantic models including ProgressEntry, TurnResult dataclass, load_config(); NpcPresence enum (PRESENT/NEARBY/KNOWN/DEPARTED); CompendiumNpcUpdate with departed_reason/departed_turn/personality (archetype id; write-once, immutable) |
| `ccya/errors.py` | ErrorKind string constants (LLM_TIMEOUT, LLM_RATE_LIMIT, etc.) + LlmcError exception hierarchy (LlmcTimeout, LlmcRateLimit, LlmcApiError) |
| `ccya/engine/__init__.py` | Re-exports public APIs; internal helpers for tests; LLM client re-exports (llm_chat, llm_chat_stream); clear_all_turn_locks() |
| `ccya/engine/config.py` | EngineConfig dataclass (including thread_max_active, nearby_decay_ttl, departed_archive_ttl, climax_turn_limit, breather_max_turns, convergence_threshold, thread_completion_threshold, thread_creation_cooldown), _EventLock, is_turn_in_progress(), clear_all_turn_locks(), Jinja env setup |
| `ccya/engine/turn.py` | run_turn() async orchestrator (thin — imports from submodules), _validate(), warmup(), _apply_thread_updates(config) with content dedup + auto-dormant every turn (urgent threads excluded) + thread completion threshold (configurable via thread_completion_threshold) + thread cap eviction + engine culling (≥3 dormant), _compute_scene_phase() 5-state phase machine with turns_in_phase tracking, _compute_narration_directive() phase-driven priority stack, _compute_pacing_context() with new signal set, _compute_ages(), _recent_turn_count() |
| `ccya/engine/_pacing.py` | BEAT_PHASE_MAP, BEAT_BUCKETS, detect_spiral(), derive_allowed_beat_types() — beat constraint derivation from scene phase and directive |
| `ccya/engine/narrate.py` | _narrate_messages(), _get_resolved_arcs(), _fmt_progress(), NPC name helpers for prompt building |
| `ccya/engine/pack_gen.py` | generate_pack() — LLM-generated ScenarioBrief, writes to packs/custom/<slug>/ |
| `ccya/engine/names.py` | Name pool generation via Faker (pc, npc, location) |
| `ccya/engine/ruling.py` | _ruling_messages() (builds ruling prompts with urgent_threads from arc.threads), _call_ruling() with retry logic (NOT ccya/rules.py — that's the dice engine) |
| `ccya/engine/extraction.py` | _run_extraction_pipeline(): 3 streams (scene/state/storytell), _call_stream() with retry |
| `ccya/engine/thread_sanitizer.py` | sanitize_threads() — batch arc/thread cleanup every N turns; LLM-driven delta output (update/add/resolve/remove threads, goal updates); event logging to events.jsonl; SSE phase events (sanitize_start/sanitize_done) |
| `ccya/engine/seed.py` | generate_seed() for dynamic packs, soft validation; post-parse hook validates LLM-assigned personality archetype ids; falls back to `ccya.personality.assign_personality()` for NPCs missing or having an invalid personality |
| `ccya/engine/changes.py` | summarize_changes(), format_change_lines() — diff pre vs post state → emoji display lines; thread entries may include `new_progress` field with formatted progress text (e.g., "[ADVANCEMENT] Rescuing the prisoner") for inline UI display |
| `ccya/engine/npc_roster.py` | build_npc_roster() — merges present/nearby/known/departed NPCs with presence tags; pre-filters archived; includes departed_reason in output; optional `personality_registry` parameter resolves archetype data into npc dict keys (`personality_label`, `personality_traits`, `personality_speech_hint`) for template rendering |
| `ccya/engine/generate_pack.py` | generate_pack_from_brief(): SSE-driven ephemeral pack generation from world brief |
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | load_state, save_state (atomic), init_save_dir (writes seed narration to chronicle.md as `## Turn 0 — Seed`; calls `_assign_seed_personalities()` to assign personality archetype ids to NPCs in static seeds), _migrate_state |
| `ccya/state/delta.py` | apply_delta(), reconcile_delta() — condition dedup, cross-turn dedup |
| `ccya/state/inventory.py` | normalize_inventory_id, resolve/fuzzy match helpers; resolve_inventory_remove_target() uses fuzzy matching (threshold 0.6) as final fallback |
| `ccya/state/npcs.py` | build_npc_alias_map, touch_compendium_order (LRU), strip_npcs_notes (skips departed/archived NPCs), apply_npc_scene_management (handles departed/nearby presence) |
| `ccya/state/chronicle.py` | append_event (events.jsonl), append_chronicle (chronicle.md), load_last_narration() |
| `ccya/server/__init__.py` | Re-exports: app, main, config, SAVE_DIR, _validate_stats |
| `ccya/server/app.py` | FastAPI app bootstrap, Jinja env, pack loading, startup event; server error persistence + exception middleware → server_errors.jsonl |
| `ccya/server/routes.py` | All @app.get / @app.post route handlers; `_list_saves()` helper (returns [{name, pack, turn_count, last_modified, pc_name, location_name}]); `_resolve_npc_personalities()` resolves archetype ids to label/traits for UI templates; `GET /` → loads opening from chronicle.md (turn 0) with in-memory fallback; `/api/saves` (GET) → list saves excluding default; `/api/switch-save` (POST) → validates save_name, checks is_turn_in_progress(), clears turn locks, updates SAVE_DIR, returns state; `POST /new-game` → builds PlayerOverrides from form fields, checks `overrides.is_empty()`: if empty, generates seed via LLM; if non-empty, uses static pack's seed_state.yaml as fallback (shows error if pack has no static seed) |
| `ccya/server/panels.py` | Panel context builders: _debug_context(), _load_* helpers, _get_opening(), _load_opening_from_chronicle() (extracts turn 0 from chronicle.md); _load_recent_history() excludes turn 0 (seed) |
| `ccya/server/tv.py` | Turn viewer data from events.jsonl + server_errors.jsonl — unified timeline with row_kind discrimination, per-stream metrics, status colors; `_turn_viewer_data()` returns `(rows, no_events)`; injects a synthetic `row_kind: "seed"` row at index 0 when seed data is present in state.yaml. TV delta rows include pacing metadata keys: gm_beat_type, gm_beat_surface_as alongside outcome_hint |
| `ccya/server/metrics.py` | _recent_turn_metrics(), _turn_log_entries() — latency/token formatting |
| `scripts/debug/ev.py` | CLI tool for inspecting events.jsonl directly; commands: summary, timing, turn, prompt, deltas, mechanics, state, diff, trace, search, play, check, eval, init, status, state-history, active-conditions, npc-ghosting, storyteller-audit, thread-audit, ruling-audit, compat, beats |
| `ccya/ev/events.py` | Shared data access layer: `load_events()`, `find_turn()`, `filter_turn_events()`, `extract_field()`, `load_current_state()`. Also consumed by TurnViewer. |
| `ccya/ev/inspect.py` | Inspection commands: `cmd_summary()`, `cmd_timing()`, `cmd_turn()`, `cmd_prompt()` |
| `ccya/ev/deltas.py` | Deltas and mechanics commands: `cmd_deltas()`, `cmd_mechanics()`, `_cmd_deltas_compact()` |
| `ccya/ev/state_tools.py` | State commands: `cmd_state()`, `cmd_diff()`, `cmd_trace()`, `cmd_search()`, `cmd_threads()`, `cmd_beats()` (with streak analysis for 3+ consecutive same-type beats), `cmd_rolls()`, `cmd_convergence()`, `cmd_phase_transitions()`, `cmd_curtain_call()`, `cmd_goals()`, `cmd_effective_age()`, `cmd_beat_ttl()` |
| `ccya/ev/play.py` | Play command: `play_turn()` sync wrapper around `run_turn()`, `cmd_play()` dispatch for single-turn/`--interactive`/`--llm` modes (requires --pack for new sessions), session management (`_create_play_session`, `_load_pack_params`), LLM player loop (`_llm_session` with scenario context, `personality`/`custom_persona` params, `until_error` flag), output formatting (`format_play_output`/`format_error_output`), session config integration (`_build_play_config` with ev.yaml resolution) |
| `ccya/ev/personality.py` | 8 personality presets + custom: `PERSONALITY_PROMPTS`, `resolve_personality(personality, custom_persona, arc_goal="")` → system prompt string with arc injection |
| `ccya/ev/session_config.py` | Session config: `load_session_config()` reads ev.yaml, `resolve_flag()` CLI>config>default resolution, `resolve_player_config()` personality resolution |
| `ccya/ev/init.py` | `cmd_init()` — creates save dir + ev.yaml from CLI args |
| `ccya/ev/status.py` | `cmd_status()` — prints session dashboard from state.yaml + ev.yaml |
| `ccya/ev/check.py` | `cmd_check()` — run checkers against existing events by turn; supports single turn + specific checkers, single turn + `--all`, or `--all` across all turns. Markdown output. Supports `--llm` flag to include LLM-based checkers, `--checker-model` to override model name. |
| `ccya/ev/audit.py` | Audit commands: `cmd_state_history()` (reconstructs active state from applied deltas — conditions, inventory, NPC ghosting), `cmd_active_conditions()` (max concurrent, cap violations, per-turn table), `cmd_npc_ghosting()` (NPC disappearance without departure tracking), `cmd_storyteller_audit()` (storyteller output format compliance), `cmd_thread_audit()` (storyteller vs sanitizer thread ID cross-reference), `cmd_ruling_audit()` (ruling.reason compliance, condition IDs in reason) |
| `ccya/ev/compat.py` | `cmd_compat()` — detects `changes` vs `extraction_context` format mismatches in events, warns which checkers will fail |
| `ccya/ev/eval.py` | `cmd_eval_run()` — batch scenario runner: loads YAML scenario, plays each turn via `play_turn()`, runs all checkers, validates TurnAsserts, produces Markdown report. `cmd_eval_list()` — lists available YAML scenarios. |
| `ccya/ev/prompt_eval.py` | Fast prompt testing: `cmd_prompt_eval_dump()` renders prompts (no LLM), `cmd_prompt_eval_call()` renders + LLM + check, `build_prompt_context()` builds context dict from `state_snapshot`. Three inline checkers: `_run_golden_match()`, `_run_prose_quality()`, `_run_extraction_format()`. Supports `scene`, `storytell`, `ruling`, `narrate`, and `state` streams. Uses `state_snapshot` (post-turn) as context. |
| `ccya/ev/scenario.py` | YAML scenario loader: `Scenario`, `ScenarioTurn`, `TurnAssert` dataclasses; `load_scenario()` parses YAML, `discover_scenarios()` finds YAML files in `packs/`. `PromptEvalScenario`, `PromptCheck` dataclasses; `load_prompt_scenario()` for prompt-eval scenarios. |
| `ccya/ev/__init__.py` | CLI dispatch: lazy import of `play`, `check`, `eval`, `init`, `status`, `audit`, `compat` subcommands; `_strip_flags()` utility; events path auto-detection for play command |
| `ccya/ev/checkers/__init__.py` | Checker framework: `@register_checker` decorator, `CheckerResult` dataclass, `run_checker()`/`run_checkers()`, `list_checkers()`, field validation, event pre-filtering, state access. Registry with explicit imports for 27 deterministic checkers + 3 LLM checkers. |
| `ccya/ev/checkers/_llm.py` | LLM checker infrastructure: `_load_checker_model()`, `_unload_checker_model()`, `_call_llm_checker()`, `_result_from_llm_output()`, `_build_checker_prompt()`, template registry. Handles model loading/unloading, prompt rendering, structured output parsing. |
| `ccya/ev/checkers/llm_checkers.py` | LLM-based narrative checkers: `directive_tone_match` (tone alignment with ruling band), `beat_narrative_chain` (GM beat narrative consequence), `state_fidelity` (extraction vs narration match). Each uses focused 20-30 line prompts. |
| `ccya/ev/checkers/gm_beat.py` | `gm_beat_lifecycle` — beat consumed, lifecycle, floor relief, binding present |
| `ccya/ev/checkers/inventory.py` | `location_change` — location applied correctly; `inventory_integrity` — overdraw, negatives, remove existence |
| `ccya/ev/checkers/conditions.py` | `conditions_lifecycle` — in-reason, dedup, cap |
| `ccya/ev/checkers/threads.py` | `thread_lifecycle` — thread_add applied, thread_update IDs valid |
| `ccya/ev/checkers/arc_goals.py` | `arc_goal_updates` — goal_update overwrites visible_goal |
| `ccya/ev/checkers/npc_presence.py` | `npc_presence` — removed NPC states check |
| `ccya/ev/checkers/pacing.py` | `pacing_directives` — outcome hint, directive render, removed directives, beat variety, surface_as consistency; `action_quality` — count/distinct |
| `ccya/ev/checkers/sanitizer.py` | `sanitizer_lifecycle` — thread operation validity vs state, orphan detection; needs non-turn events + state access |
| `ccya/ev/checkers/turn_assert.py` | `turn_assert` — validates per-turn YAML scenario assertions (stream/field/expected/min_amount); called programmatically by eval runner, not in default registry |
| `ccya/ev/checkers/phase_transition.py` | `phase_transition` — Validate phase engine transitions follow the state machine |

| `ccya/ev/checkers/recent_beats.py` | `recent_beats` — Validate recent_beats history list structure and constraints |
| `ccya/ev/checkers/phase_persistence.py` | `phase_persistence` — Validate scene_phase field present and valid on every turn (regression guard for phase-persistence bug) |
| `ccya/ev/checkers/scene_age_tracking.py` | `scene_age_tracking` — Validate scene_age increments every turn, resets on location change |
| `ccya/ev/checkers/climax_turn_counting.py` | `climax_turn_counting` — Validate climax_turn_count increments in CLIMAX, resets on phase exit |

| `ccya/ev/checkers/breather_enforcement.py` | `breather_enforcement` — Validate breather auto-transitions to RISING after breather_max_turns |
| `ccya/ev/checkers/roll_band_consistency.py` | `roll_band_consistency` — Verify band matches dice roll using rules engine |
| `ccya/ev/checkers/thread_resolution_validity.py` | `thread_resolution_validity` — thread_resolve entries have valid id/resolution_state/outcome |
| `ccya/ev/checkers/new_thread_validity.py` | `new_thread_validity` — thread_add entries have id/description/visible_goal, no duplicates |
| `ccya/ev/checkers/compendium_lifecycle.py` | `compendium_lifecycle` — NPCs added via compendium_npc_update appear in state.compendium.npcs |
| `ccya/ev/checkers/beat_phase_validity.py` | `beat_phase_validity` — gm_beat.type is allowed for the current phase |
| `ccya/ev/checkers/arc_resolution_validity.py` | `arc_resolution_validity` — arc_resolve has resolution + visible_goal, drop_threads reference existing threads |
| `ccya/ev/checkers/goal_update_validity.py` | `goal_update_validity` — goal_update is non-empty string, differs from previous visible_goal |
| `ccya/personality.py` | NpcPersonality frozen dataclass (id, label, traits, speech_hint, motivation_keywords, fear_keywords); ARCHETYPES registry (12 archetypes); assign_personality(motivation, fear, npc_id) → NpcPersonality (engine fallback; LLM is primary); validate_and_resolve(personality_id) → NpcPersonality | None (logs WARNING for unknown ids, caller falls back to assign_personality); _DEFAULT_ID = "wary_opportunist" |
| `ccya/pack.py` | load_pack(), list_packs() — validates pack has seed (static) or scenario (generated) |
 | `ccya/rules.py` | Pure-Python dice resolver: resolve_check() (1d12+stat_mod+diff_mod→Band), compute_band() (partial ≤7), build_directive() near-miss + mandatory-cost partial guidance |
| `ccya/llm_client.py` | chat(), chat_stream() — OpenAI-compatible → mlx_lm.server; trim_messages() token-budget trimming |
| `ccya/logging_setup.py` | JSONL RotatingFileHandler + _JsonFormatter (extra fields → flat JSON keys); StreamHandler defaults to WARNING via CCYA_LOG_LEVEL env var |
| `ccya/templates/index.html` | Main UI template: Alpine.js `game()` component with save picker (openSavePicker, closeSavePicker, confirmSwitchSave), settings panel, turn log, narrative streaming |
| `ccya/templates/_state_left.html` | Left sidebar: Scene NPCs (present NPCs with name/title/bio/personality/motivation/bond/notes), Location (name, description), Arc (visible_goal, goal_context, active threads, completed threads, resolved arcs), Compendium (all NPCs with bio/personality/motivation/bond/last_presence_turn/last_seen_location/departed_reason; tooltip shows alias fallback "Previously known as: X" when name is empty) |
| `ccya/templates/_state_right.html` | Right sidebar: Player (name, tagline, stats as pip grid, conditions as pills), Inventory (items with name/amount/notes), World State (non-permanent + permanent facts), Debug panel, footer (turn number, model name) |
| `ccya/static/app.src.css` | All UI styles including save picker modal (shell, backdrop, panel, cards, footer) |

### UI Panel Fields

Three main visual panels compose the browser UI. All NPC data in left/right panels comes from raw `state.yaml` dict (personality ids resolved server-side via `_resolve_npc_personalities()` in `routes.py`). The narrative panel is server-rendered from turn history then JS-streamed.

| Panel | Template | HTMX endpoint | Fields rendered |
|---|---|---|---|
| **Left sidebar** | `_state_left.html` | `GET /panels/state-left` | **Scene card** (open): present NPCs — name, title, inline notes, tooltip: bio → personality (Label — Traits) → motivation → bond. **Location card** (open): location name, description. **Arc card** (open): visible_goal (+ tooltip: goal_context), active threads (summary, urgency, progress tooltip), arc resolution, resolved arcs, completed threads. **Compendium card** (closed): all NPCs — name, title, tooltip: bio → alias fallback ("Previously known as: X" when name is empty) → personality → motivation → bond → last_seen_location + departed_reason (departed NPCs). |
| **Narrative panel** | `index.html` (inline) | `GET /` (initial) + SSE `/turn?input=` | Opening narrative (`.narrative-text`), turn history blocks — player input echo (`>`), narration text, roll badge (skill, difficulty, dice math, band result, outcome_summary), change lines (emoji-prefixed: inventory, player, location, faction, threads, arc resolution). Action pills below history. Input bar at bottom. |
| **Right sidebar** | `_state_right.html` | `GET /panels/state-right` | **Player card** (open): name (+ bio tooltip), tagline, stats grid (strength/wits/dexterity/charisma as 4-pip rows with tooltip descriptions), condition pills (label, description tooltip). **Inventory card** (open): items (name, amount, notes tooltip; credits highlighted). **World State card** (open): non-permanent facts (reverse order), permanent facts. **Debug card** (closed): raw debug info. **Footer**: turn number, model name. |

## Public APIs (function names + 1-liner purpose)

### ccya/models.py
- **load_config(path)** → dict — loads config.yaml
- **TurnResult** dataclass — returned from run_turn(): turn, trace_id, narrative, state_delta, applied, rejected, actions, diff, changes, metrics, errors, ruling, outcome_summary, gm_beat, outcome_hint, scene_phase, summary, ts

### ccya/engine (via __init__.py)
- **run_turn(...)** → AsyncIterator — 5-call pipeline: rules→narrate→scene/state/storytell extract; yields ("token"), ("phase"), ("complete", TurnResult)
- **generate_seed(pack, config, overrides)** → SeedEnvelope — LLM-generated GameState + opening for dynamic packs (via `ccya/engine/seed.py`; model class in `ccya/pack.py`)
- **generate_pack_from_brief(inputs, packs_root, config, template_dir, trace_id, max_retries=1)** → AsyncIterator[dict] — SSE-driven ephemeral pack generation; receives full EngineConfig instead of individual host/model args (Phase 08)
- **generate_pack(brief, config)** → Pack — LLM generates ScenarioBrief from WorldBrief (via `ccya/engine/pack_gen.py`)
- **format_change_lines(changes)** → list[str] — emoji display lines for UI
- **sanitize_threads(save_dir, state, config, trace_id="")** → (state, sanitize_ran) — batch arc/thread cleanup; runs every N turns per EngineConfig.sanitize_every; returns True when changes were applied

### ccya/state (via __init__.py)
- **load_state(save_dir)** → dict — loads YAML with _migrate_state() normalization
- **save_state(save_dir, state)** — atomic write (tmp + rename)
- **apply_delta(state, delta)** → dict — merges extract results into state; returns deep copy of mutated state dict

### ccya/server (via __init__.py)
- **app** — FastAPI instance with ~25 routes (GET/POST for panels, turn SSE stream, new-game, healthz)

### ccya/pack.py
- **load_pack(pack_id)** → Pack — validates pack has seed_state.yaml (static) or scenario.yaml (generated); also loads opening_scene.md and style.md if present
- **list_packs(packs_dir)** → list[PackManifest] — aggregates from default/, custom/, generated/, and eval/
- **ScenarioBrief** — complete world definition for a generated pack; fields: world_name, constraints, world_facts, narrator_rules, world_rules, factions, name_locales, name_seed, inspiration, situation_archetypes, arc_categories, character_dynamics, moral_pressures, npc_bonds, scene_detail_bundles, currency_id, starting_currency_amount
- **Pack** — Pydantic model; fields: manifest, seed, scenario, opening_scene (str|None), style (str|None)

### ccya/rules.py
 - **resolve_check(skill, difficulty, pc_stats, intent_verb)** → RulesOutcome — 1d12+stat_mod+diff_mod→Band (pure Python)

### ccya/llm_client.py
- **chat(host, model, messages, *, temperature=None, max_tokens=None, timeout=180.0, top_p=None, frequency_penalty=None, seed=None)** → response dict — non-streaming LLM call with retry; optional sampling params passed conditionally (only when not None)
- **chat_stream(...)** → AsyncIterator[str] — streaming tokens; trim_messages() drops oldest non-system msgs on budget overflow

### ccya/ev/checkers/_llm.py
- **_load_checker_model(config)** → tuple — loads checker model (mlx_lm.load), caches globally
- **_unload_checker_model()** → None — unloads checker model to free memory
- **_call_llm_checker(system_prompt, user_prompt, config)** → dict — calls LLM, parses JSON output, returns structured result
- **_result_from_llm_output(checker_id, llm_output)** → CheckerResult — converts LLM dict to CheckerResult
- **_build_checker_prompt(checker_id, events)** → tuple[str, str] — renders prompt templates with event data
- **register_prompt_template(checker_id, system_template, user_template)** → None — registers prompt templates

### ccya/ev/checkers/llm_checkers.py
- **directive_tone_match(events)** → CheckerResult — evaluates narration tone vs ruling band alignment
- **beat_narrative_chain(events)** → CheckerResult — evaluates GM beat narrative consequence
- **state_fidelity(events)** → CheckerResult — evaluates extraction vs narration match
- **set_checker_config(config)** → None — sets engine config for LLM checker calls

### ccya/ev/prompt_eval.py
- **cmd_prompt_eval(flags, args)** → None — CLI entry point for `ev.py prompt-eval` (dump/call subcommands)
- **build_prompt_context(events, turn_no, stream)** → dict — builds context dict from `state_snapshot` for prompt rendering (scene, storytell, ruling, narrate, state streams)

## 5-call turn pipeline (run_turn)

1. **Rules/Intent** (non-streaming) — classifies intent, resolves dice via `rules.resolve_check()` → IntentEnvelope + RulesOutcome. IntentEnvelope gains `impossible` and `reason` fields; when `impossible=true`, no roll occurs and Python synthesizes a failure outcome.
2. **Narrate** (streaming→SSE→chronicle.md) — prose narrative with narration directive from velocity/threads
3. **Scene Extract** (JSON→SceneExtractResult) — scene tagline, location change, compendium updates
4. **State Extract** (JSON→StateExtractResult) — inventory deltas, condition add/remove
5. **Storytell** (JSON→StorytellerResult) — thread_update, goal_update (str | None, direct dict assignment), arc_resolve, thread_resolve, thread_add (gated by PacingContext.gate), actions, gm_beat

Steps 3–5 merge into StateDelta → _validate() → apply_delta() → summarize_changes() → persist (atomic writes).

### Thread sanitizer phase (post-extraction)

After extraction and before `yield("complete")`, if `config.sanitize_every > 0` and current turn is a multiple, the thread sanitizer runs: calls LLM with arc state + recent narration evidence, applies delta changes to threads/goal, logs event record. SSE events: `sanitize_start` (expected_ms=0), `sanitize_done` (ms elapsed). Module: `ccya/engine/thread_sanitizer.py`.

## Cross-module contracts

### EV checker library imports
`ccya/ev/checkers/` imports directly from `ccya/engine/config` (EngineConfig, PRESSURE_BEAT_TYPES) and `ccya/rules` (MOMENTUM_DELTA, BANDS). This is a deliberate dependency — checkers need engine constants to validate mechanical invariants. The checker library does NOT depend on the turn pipeline; it reads events.jsonl directly.

### Error propagation path (structured observability)
LLM failure in extraction → typed LlmcError raised with ErrorKind classification → caught by server middleware → persisted to `server_errors.jsonl` + SSE error event pushed via logging_setup.py. Engine modules use `_log = logging.getLogger(__name__)`; all log calls pass structured fields via `extra={}` (error_kind, trace_id). TurnResult.errors collected as list[dict] with ErrorKind constants. Server middleware catches unhandled exceptions and returns JSON responses instead of raw HTML error pages.

### Scene thread lifecycle (unified arc.threads[])
- All scene_pressure functionality migrated to arc.threads[] with `scope: scene` — ccya/engine/pressure.py module deleted in phase 06 validation sweep
- **Three-layer engine governance:** (1) Auto-dormant at 4 turns with no activity (urgent threads excluded), (2) Urgency decay stepwise urgent→normal→background after `thread_urgency_max_age=8` turns at same level (Python-side floor), (3) Thread completion threshold auto-resolve when progress entries >= `thread_completion_threshold`
- **Scene-scoped threads purged on location change:** `apply_delta()` in delta_builder.py removes all threads with `scope: "scene"` from `arc.threads[]` when `location_change` is present in the delta, since they are localized to the prior location

### Arc thread state machine
- States: ACTIVE → DORMANT (via auto-dormant at 4 turns no activity, or storyteller thread_update with dormant=True) → COMPLETE/FAILED/ABANDONED (via thread_resolve or engine culling at ≥3 dormant). **Additional transitions:** urgent→normal→background via Python urgency decay pass; dormant threads with ≥3 dormant count trigger engine culling of oldest dormant
- Storyteller controls all thread state transitions via `thread_update` — engine applies them with cooldown enforcement (thread_creation_cooldown, thread_add only when turns since last add >= cooldown). Engine also enforces urgency decay (stepwise demotion), auto-dormant (4 turns no activity), thread completion (auto-resolve at progress threshold), and culling (≥3 dormant → cull oldest).
- Engine owns thread creation (`added_turn`, `urgency_set_turn` set at creation time in turn.py thread_add path); storyteller owns urgency/active/progress state
- TTL-based cleanup: completed threads and resolved arcs are pruned from prompt context after `completed_thread_ttl` / `resolved_arc_ttl` turns (default 3)
- ArcThread.resolution_state: str | None — set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads for narrative context

  - ArcThread.outcome: str | None — set from ThreadResolution.outcome when moved to completed_threads

  - ArcThread.resolved_turn: int | None — turn when thread was resolved; used for TTL filtering in prompts

  - ArcThread.last_updated_turn: int | None — turn when thread was last updated (dormant, urgency, type, or progress change); persisted to state; used for auto-dormant detection and staleness display in prompts

  - ArcThread.added_turn: int | None — turn when thread was created (thread_add or seed); enables age calculations for decay/expiration passes

  - ArcThread.urgency_set_turn: int | None — turn when urgency was last set; enables Python-side urgency decay pass to measure how long a thread has been at its current level

  - ProgressEntry model: {kind: "advancement"|"setback"|"shift", text: str} — structured progress replacing bare strings; ArcThread.progress: list[ProgressEntry]; ThreadUpdate.progress_kind tags each emitted progress entry
- `_merge_arc_update` unconditionally replaces `arc["threads"]` and `arc["completed_threads"]` on every call

### Storyteller system prompt (`ccya/prompts/storytell_system.j2`)
- JSON schema example shows ArcThread without `key` or `tags`; `thread_update` supports `dormant`, `urgency`, `type`, `progress`, and `progress_kind`; `thread_add` no longer includes `tags` or `key`
- CRITICAL instruction added: storyteller must check all active/dormant thread summaries for conceptual overlap before emitting new threads; update existing threads via `thread_update` instead of creating duplicates when tension is the same
- Phase→beat constraints table replaces old directive→beat mapping: phase table (SETUP/RISING/CLIMAX/RESOLUTION/BREATHER) with allowed beat types per phase, driven by `scene_phase` and `allowed_beat_types` context variables. Roll-band table becomes secondary constraint. Phase overrides roll band. RISING→CLIMAX transition now uses `convergence_score` (5-component composite) instead of binary urgency checks.
- Choice momentum section added: instructs LLM to escalate from prior turns, connect pacing context to choice urgency, and avoid passive options
### Narrator system prompt (`ccya/prompts/narrate_system.j2`)
- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Player Input Is Truth, Inventory, Never Repeat Prior Narration, Fail-Band Outcomes), (3) Behavioral guidance (NPCs merged single section, Style, Pragmatic Interpretation, Pacing, Campaign arc context), (4) Formatting/output (Markdown). Output discipline section removed (narrator emits only prose after ARC UPDATE removal). Dynamic sections (Universe rules, Genre tone) remain at end.
- ARC UPDATE section (former lines 70-87) removed entirely — narrator never emits the block, extraction code removed from turn.py
- Directives section: removed Combat Fatigue, Location Pressure, Location Imperative definitions; added Scene Pressure (≥3 effective scene age, intermediate signal to wind down or shift focus) and Scene Imperative (≥5 effective scene age, high-priority directive forcing story advancement); new directives use scene-level language reflecting single-age signal from collapsed _compute_ages()
- Null-beat fallback: when no GM beat is present, narrate purely from outcome hint and player input — no added pressure or relief beyond what the scene demands
- Anti-repetition: consolidated three scattered rules into a prominent "Never repeat prior narration" section in Hard rules; covers plot/event rehashing and includes self-check instruction
- NPC favoring: soft guidance after NPC BEHAVIOR DRIVERS to favor NPCs with motivation/fear/leverage set and treat empty-driver NPCs as background
- NPC re-use consolidated: three scattered rules (general intro RE-USE, NPC RE-USE section, non-present NPC mentions) merged into one RE-USE section
- Group NPC introduction: when introducing new groups, describe at least one distinguishing feature per individual in the narration (appearance, demeanor, visible trait). The scene extractor captures these into the group's compendium bio.
- Group NPC reintroduction: when an existing group NPC reappears, reference their distinguishing features from the compendium bio rather than collapsing to the generic type. Makes reuse feel like the same people, not any two sailors.
### Seed system prompt (`ccya/prompts/generate_seed_system.j2`)
- Generation order: PC → World state → Campaign arc → Opening scene/NPCs (inventory removed — PCs acquire items through gameplay)
- Inventory rules section removed; schema comment updated to note inventory removal
- Opening narrative instructions: weave world state facts naturally (show effect, not statement), show NPC personal ties through action/dialogue (not exposition), reference compendium NPCs naturally in narration (phone call, rumor, memory)
- CompendiumEntry model has explicit motivation/fear/leverage/personality optional string fields alongside existing name/title/bio/bond/presence/notes; seed prompt schema includes `personality` as `archetype_id` (required for named NPCs) alongside `motivation`/`fear`/`leverage`/`bond` as optional strings; seed prompt has tiered field requirements (named NPCs get `personality` + 2+ fields, unnamed NPCs get `bio` only) and a 12-archetype reference table
- Scene ideal: 1–4 present NPCs; narrative pressure for exits above that (soft guidance only, engine does NOT track or enforce NPC count at runtime — hard cap removed per Phase 01)
- Group NPC bio: must describe individuals in the group with at least one distinguishing feature per person (appearance, demeanor, visible trait). Name stays short with quantity + type; bio carries identity. Prevents generic "Two sailors" with no distinguishing features.
### Storyteller user prompt (`ccya/prompts/storytell_user.j2`)
- Renders all threads in unified list with scope tags ([SCENE]/[ARC]), dormant markers for threads with dormant=True, urgency levels; completed_threads rendered as "## past resolutions" section after active threads loop (for continuity — do not re-open resolved tensions)
- Sections reordered by recency: inventory → conditions → characters → location → arc/threads → past resolutions → world_state → pacing_context → scene_phase → rules_outcome → player_intent → CURRENT TURN NARRATION (most important signal last)
- `pacing_context` section no longer renders `gate` field (always "allow" after Plan 2); `scene_phase` and `allowed_beat_types` rendered as separate section after pacing_context
### Narrator user prompt (`ccya/prompts/narrate_user.j2`)
- Sections reordered by recency: Player Character → Inventory → Location → Characters → World State → Immutable Reference → Scene Context → Scene phase → Prior History (renamed from Prior Turns) → Recent Turns → Campaign Arc → This Turn's Result → PLAYER INPUT → directives (most important signal last)
- Thread rendering code extracted to shared `sections/_thread_list.j2` include (eliminated duplicated for-loop in if/elif branches)
- Renders ALL threads (active + dormant, scene-scoped + arc-scoped) with scope tags and [DORMANT] markers; completed_threads rendered as "### Past Resolutions" section after _arc.j2 include for full narrative continuity
- Impossible action block: when `rules_outcome.impossible=true`, renders `**IMPOSSIBLE:**` fact with reason before the band/no-roll section
- `outcome_hint` replaces `directive` as narrator's scene-motion signal: renders `**Outcome:** hold/advance/transition` with value-specific guidance
- Scene phase display added after Scene Context section: `## Scene phase: {{ state.scene.scene_phase }}` for narrator tone calibration
### NPC roster template (`ccya/prompts/sections/_npc_roster.j2`)
- Shared include rendered by narrate_user.j2, storytell_user.j2, extract_scene_user.j2; renders personality block (`| personality: **Label** (traits). Speech: hint.`) when `build_npc_roster()` resolves archetype data via `personality_registry` parameter; backward compatible — old saves without `personality` key render without the block
### Storyteller system prompt (`ccya/prompts/storytell_system.j2`)
- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Output schema, Output discipline, State-presence rule), (3) Behavioral guidance (Actions, Outcome summary, Thread operations, Rules-outcome, World state rules, Latent threads, PacingContext), (4) GM Beat guidance (longest section, placed last for recency benefit)
- Contradiction fixed: "empty arrays for fields with no changes" removed from task line (conflicted with Output discipline "omit null or empty fields")
- Duplicate beat diversity rules (Beat type diversity + Crisis-aware beat selection) coalesced into single Crisis-aware beat diversity section
### Thread list include (`ccya/prompts/sections/_thread_list.j2`)
- Shared include rendering thread entries with scope tag, latent marker, urgency, and summary
- Used by narrate_user.j2 Scene Context section (eliminates duplicated for-loop in if/elif branches)
- Gate block (`**Gate: blocked** — new threads will not be added this turn`) removed — gate is always "allow" after Plan 2, phase-derived `allowed_beat_types` is the gating mechanism
### Latent thread handling in system prompts
- narrate_system.j2: instructs narrator to push players toward latent threads through narration, environmental detail, NPC behaviour — show don't tell (NPC glancing at locked door, torchlight from tunnel, curious sounds); build 4 choices toward discovery; increase pressure for unsurfaced threads
- storytell_system.j2: instructs storyteller to use dormant thread knowledge when generating suggestions and beats — craft situations where dormant threads naturally surface (character's past catching up, long-silent threat stirring); steer player via choices/suggestions/complications without exposing dormant content directly

### Pacing context and beat lifecycle (Phase 03 pacing overhaul)
- `_compute_pacing_context()` sets `outcome_hint` overridden to "transition" when CLIMAX hits turn limit. Phase engine runs between ruling and narrate, computing `scene_phase` from thread urgency and scene age.
- `pending_gm_beat` lifecycle: null-clear on null storytell output (key popped from meta); replaced on valid storytell emittion (beat_expires_turn = turn_no + 2); expires when turn_no > beat_expires_turn at narrate setup.
- `recent_rolls`: rolling window (max 5) of `{"turn": int, "band": str}` records, most-recent-first. Appended after ruling phase on rolled turns. Consumed by `detect_spiral()` in `_narrate_setup()` to flag death spirals (3 consecutive hard+ rolls, or 3/5 recent). Spiral flag removes pressure bucket beats from allowed_beat_types.
- `spiral_detected` field on `PacingContext` (bool), also stored on `TurnContext._spiral_detected` for pipeline use.
- `scene_phase` stored in `state["scene"]` alongside `turn_entered`, `climax_turn_count`, `breather_turn_count`. Transitions: SETUP→RISING (urgent thread), RISING→CLIMAX (≥threshold urgent OR age≥pressure_threshold), CLIMAX→RESOLUTION (climax_turn_count≥limit), RESOLUTION→SETUP (location change) or BREATHER, BREATHER→RISING (urgent thread OR breather_max_turns).

### Seed emotional context → narrator consumption
- **Seed generates**: `goal_context` (character-specific stake in visible_goal), NPC `relation` field (narrative job relative to PC), action text (character-shaped, scene-grounded).
- **`goal_context` is UI-only**: Rendered in the sidebar tooltip (`_state_left.html`). NOT rendered in narrator or storyteller prompt context — the LLM never reads the raw `goal_context` value during gameplay. The system prompt provides general early-turn behavioral guidance instead.
- **Sidebar surfaces**: `goal_context` as a hover/focus tooltip on the arc goal (`_state_left.html`), using the existing `has-tooltip`/`tooltip-body` nesting convention.
- **Seed emotional framing contract**: The seed generation prompt enforces `goal_context` (2-3 sentences of personal stakes for the PC), NPC `relation` field, and character-shaped action text. This emotional data is embedded in the initial state and the sidebar, not reintroduced per-turn via prompts.
### EngineConfig field naming (Phase 06b)

- Config fields: thread_deescalate_on_success, resolved_arc_ttl (default 3), completed_thread_ttl (default 3), thread_max_active (default 5), sanitize_every (default 5, 0=disabled). **Thread lifecycle enforcement:** thread_urgency_max_age (default 8, stepwise urgency decay threshold), thread_completion_threshold (default 3, auto-resolve when progress entries reach threshold), thread_creation_cooldown (default 3, minimum turns between thread_add). YAML keys match Python field names directly. **Debug mode:** debug_mode (read from `game.debug.enabled` in config.yaml, default False) — gates streaming metadata display (scene_phase, gm_beat, outcome_hint, summary) in UI turn_complete handler.
- Sampling parameters: ruling_temperature/ruling_top_p, extract_temperature/extract_top_p/extract_frequency_penalty, narrate_temperature/narrate_top_p/narrate_frequency_penalty, generate_seed_temperature/generate_seed_top_p, pack_generation_temperature/pack_generation_top_p; stub fields always null until mlx-lm SDK support: seed, top_k, min_p, rep_penalty, rep_penalty_window. Config structure migrated from flat keys to nested `llm.<stage>.<param>` format (Phase 08).

### Computation functions (Phase 06b)
- `_compute_narration_directive(scene_phase, thread_urgency_count, effective_scene_age, ...)` — purely age-based priority stack: Scene Imperative → Scene Pressure → empty. Removed Overwhelm/Pressure/Tension/Breathe directives (handled by phase).
- `_compute_pacing_context(scene_phase, thread_urgency_count, effective_scene_age, ...)` — returns PacingContext with directive, outcome_hint, spiral_detected, convergence_score, climax_turn_count fields.
- `_compute_scene_phase(state, ages, config, convergence_score=0)` — 5-state phase machine (SETUP→RISING→CLIMAX→RESOLUTION→BREATHER), mutates state["scene"] in place. RISING→CLIMAX transition driven by convergence_score ≥ threshold. climax_turn_count tracked in state["scene"].
- `_compute_ages(state)` returns only `{"scene_age": scene_age}` — location_age and combat_age removed in Phase 03 pacing overhaul; effective_scene_age set in _ruling_phase() by adding combat boost to scene_age.
- `ccya/engine/_pacing.py` — BEAT_PHASE_MAP, BEAT_BUCKETS, detect_spiral(), derive_allowed_beat_types(directive=, spiral_detected=), compute_convergence_score(scene_phase, thread_urgency_count, scene_age, recent_beats, current_outcome, config) → int — beat constraint derivation with directive/spiral overrides, 5-component convergence score for RISING→CLIMAX transition. `detect_spiral()` uses rolling window of recent roll bands, configurable consecutive/ratio thresholds. `BEAT_BUCKETS` groups beat types into pressure/situation/relief functional buckets for phase-based filtering.

### Token budget cascade
`config.context_window` (default 32768): `llm_client.trim_messages()` drops/truncates oldest non-system messages when budget exceeded. Priority: system prompts retained first, then most recent user/context blocks. This affects all pipeline stages — if budget is tight, older turns in chronicle tail get truncated before narration/extraction contexts.

### Extraction field routing
- **SceneExtractResult**: scene_tagline, location_change, location_description, compendium_npc_update (no pressure fields); CompendiumNpcUpdate has position field for NPC spatial positioning; CompendiumEntry has explicit motivation/fear/leverage/bond/personality optional string fields alongside existing name/title/bio/aliases/presence/notes; extraction system prompt (`extract_scene_system.j2`) includes alias-first naming rules, tiered NPC field requirements (named: `bio` + `personality` + 2+ fields; unnamed: `bio` only, no personality fields), a 12-archetype reference, and passive NPC extraction instructions; `departed_reason` is combined (label + prose); `allegiance` removed; group NPC bio guidance — distinguishing features per individual in the group go in bio, not name
- **StateExtractResult**: inventory_add/remove/update, pc_condition_add/remove (no `failed`); `condition_change_reason` required when any condition change is present (Pydantic-enforced, same pattern as `inventory_change_reason`); reason persisted to `state.meta.last_condition_change_reason` for debugging
  - **StorytellerResult**: thread_update (list[ThreadUpdate] with id/dormant/urgency/type/progress/progress_kind), goal_update (str | None, applied directly to arc dict — NOT through _merge_arc_update), arc_resolve (ArcResolution with resolution/visible_goal/goal_context/drop_threads/new_threads), thread_resolve (list[ThreadResolution] with id/resolution_state/outcome + promote_to_world_state flag for promotion-only world state changes), thread_add (ArcThread | None, `added_turn` and `urgency_set_turn` set at creation time in turn.py); thread_add validated by id-based dedup only (no key, no fuzzy merge); thread_resolve processed by _apply_thread_resolutions() to move threads from arc.threads[] to arc.completed_threads[], persisting both resolution_state and outcome alongside the ArcThread
- **StateDelta.actions**: list[str], max_length=10 — merged from StorytellerResult.actions, persisted to state["pc"]["actions"] as rolling window by apply_delta()

### Cross-stream data flow (minimal by design)
- Scene → State: location_change (id,name,description) + compendium_npc_update (upserts into state.compendium.npcs with presence field)
- No items_gained/items_lost cross-stream fields exist (removed); extraction_ctx covers this-turn derived data

## Key models with non-obvious behavior

### GMBeat
- Only `type` validated by `StorytellerResult._nullify_invalid_gm_beat`: beat nullified if `type` is None/falsy
- `beat_expires_turn`: turn number at which pending beat expires (set to `turn_no + 2` in turn.py)

### WorldStateFact
- Pydantic model with id: str, text: str, tier: Literal["permanent", "persistent"] = "persistent" — permanent facts are seed-authored and never written or removed by the LLM; persistent facts are runtime-added durable environmental changes promoted from thread/arc resolution outcomes

### ThreadResolution
- Pydantic model with id: str, resolution_state: Literal["resolved", "failed", "abandoned"], outcome: str = "" — one past-tense sentence written at resolution time; persisted on completed ArcThread by _apply_thread_resolutions() alongside resolution_state (Phase 05e)

### CompactorSanitizationResult (dormant — no compactor runs)
- Models saved for future batch compaction implementation; currently unused. `inventory_remove`, `pressure_remove`, `condition_remove` coerced by `_coerce_sanitization_actions` (field_validator): converts bare strings to `{id: str, confidence: "high", reason: None}` dicts

## Type aliases

| Alias | Values |
|---|---|
| `SkillName` | 4 skills (strength, dexterity, wits, charisma) |
| `Difficulty` | 5 difficulty levels with modifiers in DIFFICULTY_MOD |
| `Band` | crit_fail, fail, setback, partial, success, crit_success (1d12 natural: 1=crit_fail, 12=crit_success) |

## State shape — state.yaml

```yaml
meta:
  game_name: str
  turn: int                    # source of truth — incremented only in engine/turn.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection
  pending_gm_beat: dict | None  # GM beat from scene extractor, consumed by next turn's narrator (runtime-only)
  prior_history: list[str]     # incremental history bullets (- [T{n}] text), appended per storyteller turn, capped at 20 newest
  _seed_type: str | None       # "static" or "dynamic" — set by seed application, read by turn viewer
  _pack_source: str | None     # pack ID that was used to generate this state

# Root-level keys only present when a game has been seeded (not in default empty state)
__seed_meta__:                 # {opening_narrative: str, actions: [str]} — dynamic packs only; set by _apply_seed_to_save_dir()

pc:
  name: str
  tagline: str
  bio: str
  stats: {strength, dexterity, wits, charisma}: int (1-4 each, total 8-12)
  conditions: list[Condition] — id-based dedup, FIFO cap 5; conditions persist until explicitly removed by extractor
    - id: str, label: str, description: str, added_turn: int
  actions: [str]               # rolling window of last 10 Storyteller actions, persisted by apply_delta

location: {id, name, description}: str

inventory: list[InventoryItem] — credits pinned to top
  - id: str, name: str, notes: str, amount: int (≥1), aliases: [str]

arc:                           # managed by engine/turn.py (_apply_thread_updates, _apply_arc_resolve)
  visible_goal: str
  goal_context: str            # 2–3 sentences explaining why visible_goal matters to this character specifically
  threads: list[ArcThread]     # unified arc.threads[] with dormant flag; dedup is id-only (no key or fuzzy merge); ArcThread.outcome nullable on active, set from ThreadResolution when completed; ArcThread.resolved_turn tracks when thread was resolved for TTL filtering
  completed_threads: list[ArcThread]   # resolved/failed/abandoned threads moved here by _apply_thread_resolutions(); each has resolution_state + outcome + resolved_turn from ThreadResolution
  resolution: str | None       # set when arc is resolved via arc_resolve
  last_thread_created_turn: int  # tracks when a thread was last created for thread_add cooldown gate

resolved_arcs: list[dict]     # stored at state level, TTL-pruned in prompts; each entry has visible_goal, resolution, goal_context, resolved_turn

scene:
  tagline: str
  world_state: list[WorldStateFact]   # permanent tier = seed-authored; persistent tier = LLM-added at runtime
  turn_entered: int            # when the current scene was entered (set on location change, used by _compute_ages())
  location_entered_turn: int   # when location was last changed

compendium.npcs: dict[id] → {name, title, bio, aliases: [str], presence: str | "present"|"nearby"|"known"|"departed"|"archived", notes: str | None, position: str | None, motivation: str | None (UI-visible), fear: str | None (hidden from UI), leverage: str | None (hidden from UI), personality: str | None (archetype id; write-once, immutable), first_seen_turn: int | None, last_presence_turn: int | None, last_seen_location: str | None, departed_reason: str | None, departed_turn: int | None}

world.factions: [str], world.locations: [str]
```

## Key constants

- `MOMENTUM_MIN = -3`, `MOMENTUM_MAX = 3`

### ErrorKind constants + LlmcError hierarchy (`ccya/errors.py`)
**ErrorKind string constants:** LLM_TIMEOUT, LLM_RATE_LIMIT, LLM_API_ERROR, TURN_PROCESSING_FAILED, PACK_LOAD_FAILED, PACK_GENERATION_FAILED, SEED_GENERATION_FAILED, SERVER_ERROR, INVENTORY_REMOVE_FAILED, INVENTORY_UPDATE_FAILED, INVENTORY_ADD_FAILED, DELTA_VALIDATION_FAILED, LOCATION_CHANGE_INVALID, NPC_SCENE_MANAGEMENT_FAILED, THREAD_UPDATE_INVALID, ARC_RESOLVE_INVALID, THREAD_RESOLVE_INVALID, EXTRACTION_CONTEXT_BUILD_FAILED, EXTRACTION_COERCION_FAILED, INVENTORY_NORMALIZE_FAILED, FUZZY_MATCH_FAILED, NPC_NAME_LOOKUP_FAILED, STATE_LOAD_FAILED, STATE_SAVE_FAILED, EVENT_APPEND_FAILED, CHRONICLE_APPEND_FAILED, RULING_PARSE_FAILED, EXTRACTION_PARSE_FAILED. All modules use these instead of magic strings for error classification.

**LlmcError exception hierarchy (base → subclasses):**
- `LlmcTimeout` — network/LLM timeout; retryable=True; status_code=None
- `LlmcRateLimit` — HTTP 429 from provider; retryable=True; status_code=429
- `LlmcApiError` — other API errors (5xx); retryable=False; dynamic status_code

**Structured logging pipeline:** All modules use `_log = logging.getLogger(__name__)`. Error calls pass structured fields via `extra={error_kind: ..., trace_id: ...}`. _JsonFormatter flattens extra dict entries as top-level JSON keys in log output. Server middleware persists unhandled exceptions to server_errors.jsonl with ErrorKind classification. Turn viewer merges events.jsonl + server_errors.jsonl into unified timeline sorted by timestamp, discriminated via `row_kind` field ("turn" vs "server_error").

### UI streaming metadata (thread progress, debug display)
- **Thread progress strings:** After turn completion, inline divs with class `thread-progress-line` are inserted below narrative text. Each thread entry in `changes["threads"]` may carry a `new_progress` field (formatted as "[KIND] text") populated by `summarize_changes()` when new progress entries appear on threads.
- **Debug metadata row:** When `EngineConfig.debug_mode` is true, a formatted div with class `debug-metadata-row` shows four metafields inline after turn completion: scene_phase, gm_beat (type/surface_as), outcome_hint, and summary. Parsed from `result.scene_phase`, `result.gm_beat`, `result.outcome_hint`, and `result.summary` on the TurnResult object.
- **Ruling reason tooltip:** When a ruling carries a `reason` field, the difficulty label (normal/hard/extreme) in the roll badge gets a `has-tooltip` showing the reason text. On no-roll turns, the outcome badge itself gets the tooltip.
- **Inventory change reason tooltip:** After each turn, `delta.inventory_change_reason` is persisted to `state.meta.last_inventory_change_reason`. The right-side panel Inventory `<summary>` shows this as a tooltip when present.
- **Sidebar thread ordering:** `_state_left.html` reverses active threads (`| reverse`) so most recently active appear first; completed_threads also reversed (top 20).

## Design documents

| Document | Path | Purpose |
|---|---|---|
| Eval methodology | `docs/design/eval-methodology-design.md` | Scenario taxonomy, checker suites, aggregation pipeline, Makefile targets |
| CLI defaults and personas | `docs/design/cli-defaults-and-personas-design.md` | Config system, persona registry, CLI flag conventions |
| UI streaming improvements | `docs/design/eval-ui-streaming-design.md` | SSE streaming, live eval progress, mid-turn pipeline visibility |
| EV tooling (completed) | `docs/design/complete/ev-tooling-design.md` | Original EV tooling architecture (play/check/eval commands) |
| Dual-track eval | `docs/design/complete/dual-track-eval-design.md` | Parallel eval strategy |
| Observability | `docs/design/complete/observability-design.md` | Logging, metrics, debugging infrastructure |
| Pacing beat system | `docs/design/complete/pacing-beat-system-design.md` | GM beat lifecycle, pacing directives |
| Narration simplification | `docs/design/complete/narration-simplification-design.md` | Narrator prompt overhaul |
| Narration prompt overhaul | `docs/design/complete/narration-prompt-overhaul-design.md` | Narrator system/user prompt restructuring |
| NPC death purge | `docs/design/complete/npc-death-purge-design.md` | NPC departure/archival lifecycle |
| GM signals | `docs/design/complete/gm-signals-design.md` | GM beat signals and pacing context |
| Thread sanitizer | `docs/design/complete/thread-sanitizer-design.md` | Thread cleanup and arc resolution |
| Condition difficulty | `docs/design/complete/condition-difficulty-design.md` | Condition system and difficulty modifiers |
| Arc thread system | `docs/design/complete/arc-thread-system-design.md` | Arc thread lifecycle and state machine |
| Arc system | `docs/design/complete/arc-system-design.md` | Arc goal system and resolution |
| Arc resolution redesign | `docs/design/complete/arc-resolution-redesign-design.md` | Arc resolution improvements |
| Prompt testing and schema discipline | `docs/design/complete/prompt-testing-and-schema-discipline.md` | Prompt testing methodology |
| Impossible action pacing outcome | `docs/design/complete/impossible-action-pacing-outcome.md` | Impossible action handling |
