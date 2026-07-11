# Engine Overhaul Checklist

Organized by domain area. Not everything touches everything — use the table to find what's relevant to your change.

## 1. Turn Pipeline

The six-step pipeline (Rules → Phase Engine → Narrate → Scene Extract → State Extract → Record) plus async end-of-turn window.

- [ ] **Pipeline order preserved:** Rules → Phase Engine → Narrate → 2a/2b/2c extract (parallel) → validate → apply → persist → async sanitize/world
- [ ] **`run_turn()` orchestrator intact:** `turn.py` ~210 lines; subroutines `_narrate_phase()`, `_extract_phase()`, `_apply_phase()`, `_persist_and_async_cleanup()`
- [ ] **`yield("complete")` fires before async window:** Sanitize + World run after yield, lock still held
- [ ] **TurnResult schema unchanged:** `TurnResult` in `models/config.py` — all expected fields present (narrative, state_delta, applied, rejected, actions, diff, changes, metrics, errors, ruling, outcome_summary, outcome_hint, scene_phase, summary, ts)
- [ ] **Trace IDs propagate:** Every turn gets a trace_id; structured logging uses `extra={error_kind, trace_id}`
- [ ] **Error handling:** LLM failures → `LlmcError` with `ErrorKind` → middleware → `server_errors.jsonl` + SSE error event; no bare `except: pass`

## 2. Ruling / Step 0

Intent classification, dice resolution, beat selection.

- [ ] **IntentEnvelope schema:** `intent`, `intent_verb`, `target`, `check` (RulesCheck), `impossible`, `reason`, `scene_motion`
- [ ] **RulesOutcome schema:** `rolled`, `skill`, `difficulty`, `stat_value`, `stat_mod`, `diff_mod`, `dice`, `raw_total`, `final_total`, `band`, `directive`, `intent`, `intent_verb`, `impossible`, `reason`
- [ ] **Dice resolution pure-Python:** `rules.resolve_check()` → 1d12 + stat_mod + diff_mod → Band
- [ ] **Band mapping correct:** 1=crit_fail, 12=crit_success; all bands represented
- [ ] **Impossible actions:** No roll occurs; Python synthesizes `fail` outcome
- [ ] **Beat selection:** Reads `state.meta.beat_candidates` (from prev turn's World), selects by index, sets/pops `state.meta.pending_gm_beat`, always pops `beat_candidates`
- [ ] **Beat type validation:** Selected beat type checked against `allowed_beat_types` (phase constraint)
- [ ] **PC situation filtering:** `_filter_pc_situation()` filters to `persist=true` keys from schema
- [ ] **Ruling reason quality:** Non-empty, substantive, contains causal keywords

## 3. Phase Engine / Pacing

5-state machine, convergence score, pacing context.

- [ ] **5-state machine:** SETUP → RISING → CLIMAX → RESOLUTION → BREATHER → (any) → SETUP on location change
- [ ] **Convergence score:** 6-component composite (urgent_thread, threat_thread, scene_age, beat_streak, dice_weight, plus one more)
- [ ] **Hysteresis + min_turns:** Phase transitions respect enter/exit thresholds and minimum turn counts
- [ ] **Climax turn limit:** `climax_turn_count` increments within CLIMAX, resets on exit; `outcome_hint` forced to "transition" at limit
- [ ] **Breather enforcement:** Auto-transitions to RISING after `breather_max_turns`
- [ ] **PacingContext fields:** `directive`, `outcome_hint`, `summary`, `convergence_score`, `convergence_components`, `convergence_threads`
- [ ] **EMA smoothing:** Convergence score smoothed across turns
- [ ] **Phase computed flag:** `_phase_computed` on state prevents duplicate computation
- [ ] **Beat phase map:** `BEAT_PHASE_MAP` / `BEAT_BUCKETS` — each phase has allowed beat types

## 4. Narration / Step 1

Prose generation, streaming, dice-band binding.

- [ ] **Streaming works:** `chat_stream()` / `chat_stream_with_config()` for narrate stage
- [ ] **Prompt templates:** `narrate_system.j2` + `narrate_user.j2` render correctly
- [ ] **Context inputs:** Full state, prior_history (last 20 bullets), recent_turns[-1:], pacing_context, pending_gm_beat, npc_roster, world_factions/locations
- [ ] **GM beat consumption:** Pure reader of `pending_gm_beat` (set by Ruling same turn)
- [ ] **Dice-band binding:** Narration reflects ruling band (success→positive, fail→tense, etc.)
- [ ] **Token trimming:** `trim_messages()` preserves system messages, 2000 head + 500 tail
- [ ] **Prompt logging:** All prompts written to `prompts.jsonl` with stream identifier
- [ ] **Temperature/top_p:** Uses `narrate_temperature` / `narrate_top_p` from config

## 5. Extraction Pipeline (Steps 2a–2c)

Scene, State, Record extraction — three parallel streams.

### 2a — Scene Extract
- [ ] **SceneExtractResult schema:** `compendium_npc_update`, `candidate_npcs` (per-NPC beat candidates: [{id, type, effect}])
- [ ] **NPC presence tracking:** presence values valid (present/nearby/known/departed/archived)
- [ ] **Compendium upserts:** NPC identity changes (presence, notes, bio, personality, position, party flag)
- [ ] **Candidate NPCs:** Per-NPC beat candidate signals with driver assignment

### 2b — State Extract
- [ ] **StateExtractResult schema:** `inventory_add/remove/update`, `pc_condition_add/remove`, `location_change`, `location_description`
- [ ] **Inventory change reason:** Required when any inventory change present (Pydantic-enforced)
- [ ] **Condition change reason:** Required when any condition change present (Pydantic-enforced)
- [ ] **Location change detection:** Previous location ID differs from new location ID
- [ ] **Condition TTL:** Default TTL assigned when LLM omits (`config.condition_default_ttl`); sentinel 0 replaced

### 2c — Record
- [ ] **StorytellerResult schema:** `thread_update`, `goal_update`, `arc_resolve`, `thread_resolve`, `thread_add`, `actions`, `outcome_summary`
- [ ] **gm_beat REMOVED:** Not in StorytellerResult; beats flow through state.meta
- [ ] **Thread lifecycle:** thread_add/id-dedup, thread_update/dormant+urgency+progress, thread_resolve/move to completed
- [ ] **Arc resolution:** resolution + visible_goal + goal_context; drop_threads reference existing threads
- [ ] **Goal update:** Non-empty string, differs from previous visible_goal
- [ ] **Actions rolling window:** Max 10 actions, persisted to `state.pc.actions`
- [ ] **Extraction context:** `_ExtractionContext` carries post-delta data into record prompt

## 6. Delta Validation & Application

Merge extraction results, validate constraints, mutate state.

- [ ] **StateDelta schema:** `location_change`, `location_description`, `compendium_npc_update`, `arc_update`, `inventory_add/remove/update`, `pc_condition_add/remove`, `actions`
- [ ] **No beat fields in StateDelta:** Beats flow through state.meta
- [ ] **Validation constraints:** inventory_remove IDs exist, no negative amounts, no overdraw
- [ ] **`apply_delta()` mutates state:** Merges all extraction results into state
- [ ] **Thread scope purge:** Scene-scoped threads removed on location change
- [ ] **TTL expiry pass:** `_expire_conditions()` decrements TTLs, removes at 0
- [ ] **LongTermObjective.started_turn:** Set on arc resolve
- [ ] **World state candidate collection:** `ThreadResolution.world_state_candidate` collected in `_apply_thread_resolutions()`

## 7. State Model & Persistence

Pydantic models, immutable mutations, I/O.

- [ ] **WorldState is root model:** All engine functions take `WorldState`, never `dict[str, Any]`
- [ ] **Immutable mutation:** Only typed mutator methods on `WorldState` (model_copy under the hood)
- [ ] **No dict-style assignment:** Never `state["key"] = value` or `state.setdefault()`
- [ ] **Mutator coverage:** `set_turn`, `add_recent_beat`, `add_recent_roll`, `add_prior_history_bullet`, `set_pending_beat`, `set_beat_candidates`, `add_npc`, `update_npc`, `add_condition`, `remove_condition`, `expire_conditions`, `set_scene_phase`, `set_world_state`, `expire_world_state_facts`, etc.
- [ ] **`load_state()` / `save_state()`:** YAML I/O, atomic write (tmp + rename)
- [ ] **YAML serialization:** Enums coerced to strings via `_coerce_enums()`
- [ ] **No schema_version:** All saves use current format
- [ ] **Events persistence:** `append_event()` to events.jsonl
- [ ] **Chronicle:** `chronicle.md` appended per turn
- [ ] **last_turn_state captured:** End-of-turn state stored in events for checker consumption

## 8. Async End-of-Turn (Sanitize + World)

Step 2d — World beat generation, Step 2e — Thread sanitizer.

### Sanitize
- [ ] **Runs every N turns:** `sanitize_every` config (default 5, 0=disabled)
- [ ] **Thread culling:** Dormant threads with ≥3 dormant count
- [ ] **Urgency decay:** Stepwise urgent→normal→background after `thread_urgency_max_age`
- [ ] **World state swap:** Atomic `set_world_state()` — full array replacement
- [ ] **World state fact expiration:** TTL-based removal of facts whose `expires_turn` passed
- [ ] **Completed arc pruning:** TTL-based from prompt context

### World (Step 2d)
- [ ] **Runs after yield("complete"):** Lock still held
- [ ] **NPC roster:** Reads from compendium via `build_npc_roster()`
- [ ] **Candidate validation:** `GMBeat(**candidate)` validates each candidate
- [ ] **Phase constraint filter:** Strips candidates with invalid beat types
- [ ] **Output format:** `{type, effect, npcs}` — stripped to minimal
- [ ] **Failure handling:** On any failure (LLM timeout, invalid JSON), `beat_candidates = []`
- [ ] **Event recording:** `extraction.world` added to event with output/tokens/ms
- [ ] **Temperature:** Uses `world_temperature` from config (default 0.55)

## 9. LLM Client

OpenAI-compatible API wrapper, retry logic, streaming.

- [ ] **`chat()` / `chat_stream()`:** Non-streaming and streaming paths
- [ ] **`chat_with_config()` / `chat_stream_with_config()`:** Per-stage parameter override
- [ ] **Retry logic:** LLM failures retried with backoff
- [ ] **`LlmResult` wrapper:** Frozen dataclass with `content`, `usage`, `elapsed_ms`
- [ ] **Both backends work:** Primary (10.75.100.51:1234) and fallback (localhost:8000)
- [ ] **`num_ctx` passed:** Controls server-side context window
- [ ] **`context_window` trimming:** Client-side trim when budget exceeded

## 10. Server / Routes

FastAPI app, SSE streaming, HTMX panels, save switching.

- [ ] **All routes functional:** ~25 route handlers in `routes.py`
- [ ] **SSE streaming:** Turn completion streams tokens to UI
- [ ] **Panel builders:** Debug, state, opening panels render correctly
- [ ] **Save switching:** Loading different saves works
- [ ] **Error middleware:** Unhandled exceptions return JSON, not HTML error pages
- [ ] **Logging:** `server.logging.level` (file) + `server.logging.console_level` (stdout)
- [ ] **Debug mode:** `debug.enabled` gates streaming metadata in UI

## 11. UI / Frontend

HTML templates, CSS, Alpine.js components, JavaScript.

- [ ] **Game shell layout:** Sidebar, narrative column, sidebars, modals
- [ ] **Alpine.js components:** `charCreation()`, `worldBuilder()`, `game()`
- [ ] **HTMX wiring:** Sidebar refresh on turn_complete
- [ ] **Narration rendering:** Markdown rendering, tokens display, tooltips
- [ ] **Drain display:** `game-utils.js` display drain, pills
- [ ] **Turn viewer:** Pipeline stage rendering, diff panel, inspector
- [ ] **Responsive design:** Fluid typography, responsive rules
- [ ] **Character sheets:** Rendered correctly
- [ ] **Chronicle overlay:** Turn log panel

## 12. Prompts

Jinja2 templates, shared sections, rendering flow.

- [ ] **All prompt templates render:** No undefined variables
- [ ] **Shared sections:** `prompts/sections/` templates included correctly
- [ ] **Template disambiguation:** Correct template system used (prompt vs UI)
- [ ] **Cross-module contracts:** Prompt rendering follows documented data flow
- [ ] **No hardcoded values:** Config-driven parameters
- [ ] **Prompt eval works:** `ev.py prompt-eval dump` and `call` subcommands

## 13. Config

EngineConfig, CheckerConfig, sampling parameters.

- [ ] **EngineConfig dataclass:** All fields present and typed
- [ ] **CheckerConfig thresholds:** Configurable per-checker
- [ ] **Sampling params per stage:** ruling, narrate, extract, prepare_seed, pack_generation
- [ ] **Config loading:** `config.yaml` → `EngineConfig` mapping
- [ ] **Nested format:** `llm.<stage>.<param>` structure

## 13a. Personality System

NPC personality archetypes, assignment.

- [ ] **NpcPersonality dataclass:** 12 archetype registry
- [ ] **`assign_personality()`:** Correct archetype assignment
- [ ] **Seed prompt integration:** Personality as `archetype_id` for named NPCs
- [ ] **Compendium integration:** Personality write-once, immutable

## 14. Rules Engine

Pure-Python dice resolution.

- [ ] **`resolve_check()`:** 1d12 + stat_mod + diff_mod → Band
- [ ] **Skill names:** strength, dexterity, wits, charisma
- [ ] **Difficulty levels:** 5 levels with modifiers in DIFFICULTY_MOD
- [ ] **Bands:** crit_fail, fail, setback, partial, success, crit_success
- [ ] **Natural 1 / 12:** Critical failure / critical success

## 15. Checkers

28 deterministic + 3 LLM checkers.

- [ ] **All checkers register:** `@register_checker` in `checkers/__init__.py`
- [ ] **`ev.py check --all` passes:** On a known-good save
- [ ] **Checker imports:** Deliberate imports from `engine/config` and `rules`
- [ ] **LLM checkers:** `--llm` flag works, uses checker model
- [ ] **`ev.py eval run` works:** YAML scenarios → checkers → report
- [ ] **`ev.py eval compare` works:** Cross-run checker comparison

### Checker coverage by domain
- [ ] **Ruling:** `ruling_reason_quality`, `ruling_band_distribution`, `ruling_intent_match`
- [ ] **Pacing:** `pacing_directives`, `phase_transition`, `climax_turn_counting`, `breather_enforcement`, `beat_phase_validity`
- [ ] **Convergence:** `convergence_components`
- [ ] **Beats:** `gm_beat_lifecycle`
- [ ] **Inventory/Conditions:** `inventory_integrity`, `conditions_lifecycle`, `location_change`
- [ ] **Threads/Arcs:** `thread_lifecycle`, `arc_goal_updates`, `thread_resolution_validity`, `new_thread_validity`, `arc_resolution_validity`, `goal_update_validity`
- [ ] **NPCs:** `npc_presence`, `compendium_lifecycle`
- [ ] **Sanitizer:** `sanitizer_lifecycle`
- [ ] **State:** `location_description_consistency`, `world_state_facts`
- [ ] **LLM-based:** `directive_tone_match`, `beat_narrative_chain`, `state_fidelity`

## 16. Cross-Cutting Concerns

- [ ] **Logging:** `logging.getLogger(__name__)` used everywhere; structured logging with `extra={}`
- [ ] **No bare `except: pass`:** Every exception handler logs at minimum a warning
- [ ] **Git workflow:** Branch slug = plan slug; commit prefix `[<slug>] [<ticket_id>]`
- [ ] **Doc updates:** `docs/architecture/`, `docs/repomap.md`, this file updated
- [ ] **No backwards compatibility hacks:** Clean removal of unused fields/routes/models
- [ ] **Makefile targets:** `make check` (lint + typecheck) passes
- [ ] **Roadmap tickets:** Frontmatter present, status updated
