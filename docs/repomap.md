# REPOMAP — module boundaries, public APIs, cross-module contracts

## Module index (file → responsibility)

| File | Responsibility |
|---|---|
| `ccya/__main__.py` | CLI entry: argparse + uvicorn.run |
| `ccya/cli.py` | CLI commands |
| `ccya/models.py` | All Pydantic models including ProgressEntry, TurnResult dataclass, load_config() |
| `ccya/errors.py` | ErrorKind string constants (LLM_TIMEOUT, LLM_RATE_LIMIT, etc.) + LlmcError exception hierarchy (LlmcTimeout, LlmcRateLimit, LlmcApiError) |
| `ccya/engine/__init__.py` | Re-exports public APIs; internal helpers for tests; LLM client re-exports (llm_chat, llm_chat_stream) |
| `ccya/engine/config.py` | EngineConfig dataclass (including thread_stale_threshold, thread_max_active), _EventLock, is_turn_in_progress(), Jinja env setup |
| `ccya/engine/turn.py` | run_turn() async orchestrator (thin — imports from submodules), _validate(), warmup(), _apply_thread_updates(config) with content dedup + auto-latent + thread cap eviction |
| `ccya/engine/narrate.py` | _narrate_messages(), _get_resolved_arcs(), _fmt_progress(), NPC name helpers for prompt building |
| `ccya/engine/pack_gen.py` | generate_pack() — LLM-generated ScenarioBrief, writes to packs/custom/<slug>/ |
| `ccya/engine/names.py` | Name pool generation via Faker (pc, npc, location) |
| `ccya/engine/ruling.py` | _ruling_messages(), _call_ruling() with retry logic (NOT ccya/rules.py — that's the dice engine) |
| `ccya/engine/extraction.py` | _run_extraction_pipeline(): 3 streams (scene/state/storytell), _call_stream() with retry |
| `ccya/engine/seed.py` | generate_seed() for dynamic packs, soft validation |
| `ccya/engine/changes.py` | summarize_changes(), format_change_lines() — diff pre vs post state → emoji display lines |
| `ccya/engine/npc_roster.py` | build_npc_roster() — merges present/known NPCs with presence tags |
| `ccya/engine/generate_pack.py` | generate_pack_from_brief(): SSE-driven ephemeral pack generation from world brief |
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | load_state, save_state (atomic), init_save_dir, _migrate_state |
| `ccya/state/delta.py` | apply_delta(), reconcile_delta() — condition dedup, cross-turn dedup |
| `ccya/state/inventory.py` | normalize_inventory_id, resolve/fuzzy match helpers; resolve_inventory_remove_target() uses fuzzy matching (threshold 0.6) as final fallback |
| `ccya/state/npcs.py` | build_npc_alias_map, touch_compendium_order (LRU), strip_npcs_notes (clears this-turn NPC notes at start of each turn) |
| `ccya/state/chronicle.py` | append_event (events.jsonl), append_chronicle (chronicle.md), load_last_narration() |
| `ccya/state/momentum.py` | apply_momentum() — deterministic from rules band, clamped to [-3,+3] |
| `ccya/server/__init__.py` | Re-exports: app, main, config, SAVE_DIR, _validate_stats |
| `ccya/server/app.py` | FastAPI app bootstrap, Jinja env, pack loading, startup event; server error persistence + exception middleware → server_errors.jsonl |
| `ccya/server/routes.py` | All @app.get / @app.post route handlers |
| `ccya/server/panels.py` | Panel context builders: _debug_context(), _load_* helpers, _get_opening() |
| `ccya/server/tv.py` | Turn viewer data from events.jsonl + server_errors.jsonl — unified timeline with row_kind discrimination, per-stream metrics, status colors; `_turn_viewer_data()` returns `(rows, no_events)`; injects a synthetic `row_kind: "seed"` row at index 0 when seed data is present in state.yaml |
| `ccya/server/metrics.py` | _recent_turn_metrics(), _turn_log_entries() — latency/token formatting |
| `scripts/debug/ev.py` | CLI tool for inspecting events.jsonl directly; commands: summary, timing, turn, props, compact, prompt, outputs, deltas, dice, mechanics, connectors, pacing (summary/gate/momentum/band/beat_locked from top-level event fields), state, diff, trace, search (supports npc/item/condition/band/momentums_after/momentums_before/momentums_delta/rejected/input) |
| `ccya/eval/__init__.py` | Re-exports: EvalConfig, JudgeResult, RunResult (with track), Scenario, build_trace, run_scenario, etc. |
| `ccya/eval/config.py` | EvalConfig, JudgesSpec (per-judge rubric/model/temp), load_eval_config() |
| `ccya/eval/judge.py` | run_judges(track="adversarial"): parallel domain judges + sequential meta judge; parse_judge_response() YAML front matter; _build_metrics_rows(turn, tok_in per phase, pacing_directive, beat_generated/consumed from pending_gm_beat lifecycle) |
| `ccya/eval/universal_asserts.py` | Auto-checkers (condition dedup, consecutive_pressure_tracking beat-type-based counter, beat_locked dual-trigger from momentum_floor/consecutive_pressure_threshold, floor relief injection verification, no_removed_directives/npc_states negative assertions, exact directive value rendering via word-boundary regex, orphan condition detection, thread_add→state application verification, inventory remove existence, thread_update ID validity, beat type variety warning, surface_as consistency check) — red/yellow severity |
| `ccya/eval/report.py` | write_full_report(run_result, eval_cfg, judge_results=None): single-pass REPORT.md with metadata (including track + scoring philosophy), optional judge summary + verdicts, flags, auto-checker table (`[PASS]`/`[FAIL]` labels), pacing metrics, turn metrics; atomic write via tmp.replace() |
| `ccya/eval/scenario.py` | Scenario (with seed_overrides, track="adversarial"/"baseline"), Turn, TurnAssert (with stream_id) |
| `ccya/eval/engine_mirror.py` | Live engine constants for scenarios: BANDS, SKILLS, DIFFICULTIES, PC_CONDITION_CAP, CONDITION_TTL; pacing config mirror (momentum_floor=-3, consecutive_pressure_threshold=3, combat +2 scene_age boost) via EngineConfig defaults — THREAD_RESOLVED_ARC_TTL/THREAD_COMPLETED_THREAD_TTL imported from _defaults.arc_memory_ttl/_defaults.thread_memory_ttl, PRESSURE_BEAT_TYPES imported from turn.py, GM_BEAT_TYPES derived at runtime from GMBeat.type Literal annotation |
| `ccya/eval/test_eval_schema.py` | KNOWN_ASSERT_FIELDS validation against runner._check_asserts handler field names, KNOWN_SEED_PATHS dotpath format check, engine_mirror import sanity test |
| `evals/scenarios/baseline.py` | 13-turn organic narrative arc with track="baseline": Dustfall mystery, town → canyon travel, missing prospector search and rescue. Minimal asserts (7). |
| `evals/scenarios/eval_coverage_gap.py` | 8-turn scenario exercising ev1 findings: band-beat conflict, thread progress, orphan conditions, surface_as drift, skill variety |
| `ccya/pack.py` | load_pack(), list_packs() — validates pack has seed (static) or scenario (generated) |
| `ccya/rules.py` | Pure-Python dice resolver: resolve_check() (1d12+stat+cond−diff→Band), build_directive() near-miss logic |
| `ccya/llm_client.py` | chat(), chat_stream() — OpenAI-compatible → mlx_lm.server; trim_messages() token-budget trimming |
| `ccya/logging_setup.py` | JSONL RotatingFileHandler + _JsonFormatter (extra fields → flat JSON keys); StreamHandler defaults to WARNING via CCYA_LOG_LEVEL env var |

## Public APIs (function names + 1-liner purpose)

### ccya/models.py
- **load_config(path)** → dict — loads config.yaml
- **TurnResult** dataclass — returned from run_turn(): turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, diff, changes, metrics, errors, ruling, outcome_summary, ts

### ccya/engine (via __init__.py)
- **run_turn(...)** → AsyncIterator — 5-call pipeline: rules→narrate→scene/state/storytell extract; yields ("token"), ("phase"), ("complete", TurnResult)
- **generate_seed(pack, config, overrides)** → SeedEnvelope — LLM-generated GameState + opening for dynamic packs (via `ccya/engine/seed.py`; model class in `ccya/pack.py`)
- **generate_pack_from_brief(inputs, packs_root, config, template_dir, trace_id, max_retries=1)** → AsyncIterator[dict] — SSE-driven ephemeral pack generation; receives full EngineConfig instead of individual host/model args (Phase 08)
- **generate_pack(brief, config)** → Pack — LLM generates ScenarioBrief from WorldBrief (via `ccya/engine/pack_gen.py`)
- **format_change_lines(changes)** → list[str] — emoji display lines for UI

### ccya/state (via __init__.py)
- **load_state(save_dir)** → dict — loads YAML with _migrate_state() normalization
- **save_state(save_dir, state)** — atomic write (tmp + rename)
- **apply_delta(state, delta)** → dict — merges extract results into state; returns deep copy of mutated state dict

### ccya/server (via __init__.py)
- **app** — FastAPI instance with ~25 routes (GET/POST for panels, turn SSE stream, new-game, healthz)

### ccya/pack.py
- **load_pack(pack_id)** → Pack — validates pack has seed_state.yaml (static) or scenario.yaml (generated)
- **list_packs(packs_dir)** → list[PackManifest] — aggregates from default/ and custom/

### ccya/rules.py
- **resolve_check(skill, difficulty, pc_stats, pc_conditions, intent_verb, rng)** → RulesOutcome — 1d12+stat_mod+cond_mod→Band (pure Python)

### ccya/llm_client.py
- **chat(host, model, messages, *, temperature=None, max_tokens=None, timeout=180.0, top_p=None, frequency_penalty=None, seed=None)** → response dict — non-streaming LLM call with retry; optional sampling params passed conditionally (only when not None)
- **chat_stream(...)** → AsyncIterator[str] — streaming tokens; trim_messages() drops oldest non-system msgs on budget overflow

## 5-call turn pipeline (run_turn)

1. **Rules/Intent** (non-streaming) — classifies intent, resolves dice via `rules.resolve_check()` → IntentEnvelope + RulesOutcome. IntentEnvelope gains `impossible` and `impossible_reason` fields; when `impossible=true`, no roll occurs and Python synthesizes a failure outcome.
2. **Narrate** (streaming→SSE→chronicle.md) — prose narrative with narration directive from velocity/threads
3. **Scene Extract** (JSON→SceneExtractResult) — scene tags, location change, compendium updates
4. **State Extract** (JSON→StateExtractResult) — inventory deltas, condition add/remove
5. **Storytell** (JSON→StorytellerResult) — thread_update, goal_update (str | None, direct dict assignment), arc_resolve, thread_resolve, thread_add (gated by PacingContext.gate), world_state_add/remove, actions, gm_beat

Steps 3–5 merge into StateDelta → _validate() → apply_delta() → summarize_changes() → persist (atomic writes).

## Cross-module contracts

### Error propagation path (structured observability)
LLM failure in extraction → typed LlmcError raised with ErrorKind classification → caught by server middleware → persisted to `server_errors.jsonl` + SSE error event pushed via logging_setup.py. Engine modules use `_log = logging.getLogger(__name__)`; all log calls pass structured fields via `extra={}` (error_kind, trace_id). TurnResult.errors collected as list[dict] with ErrorKind constants. Server middleware catches unhandled exceptions and returns JSON responses instead of raw HTML error pages.

### Scene thread lifecycle (unified arc.threads[])
- All scene_pressure functionality migrated to arc.threads[] with `scope: scene` — ccya/engine/pressure.py module deleted in phase 06 validation sweep
- Thread state is storyteller-managed via `thread_update` directives — no Python-side age-based demotion or urgency decay
- **Scene-scoped threads purged on location change:** `apply_delta()` in delta_builder.py removes all threads with `scope: "scene"` from `arc.threads[]` when `location_change` is present in the delta, since they are localized to the prior location

### Arc thread state machine
- States: LATENT → ACTIVE (via thread_update with active=True) → COMPLETE/FAILED (via thread_resolve from StorytellerResult) / DORMANT (via thread_update with active=False)
- Storyteller controls all thread state transitions via `thread_update` — engine applies them without cap/cooldown enforcement
- Engine owns thread creation (id-based dedup only — no key or fuzzy merge); storyteller owns urgency/active/progress state
- TTL-based cleanup: completed threads and resolved arcs are pruned from prompt context after `completed_thread_ttl` / `resolved_arc_ttl` turns (default 3)
- ArcThread.resolution_state: str | None — set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads for narrative context

  - ArcThread.outcome: str | None — set from ThreadResolution.outcome when moved to completed_threads

  - ArcThread.resolved_turn: int | None — turn when thread was resolved; used for TTL filtering in prompts

  - ArcThread.last_updated_turn: int | None — turn when thread was last updated (active, urgency, summary, or progress change); persisted to state; used for auto-latent demotion and staleness display in prompts

  - ProgressEntry model: {kind: "advancement"|"setback"|"shift", text: str} — structured progress replacing bare strings; ArcThread.progress: list[ProgressEntry]; ThreadUpdate.progress_kind tags each emitted progress entry
- `_merge_arc_update` unconditionally replaces `arc["threads"]` and `arc["completed_threads"]` on every call

### Storyteller system prompt (`ccya/prompts/storytell_system.j2`)
- JSON schema example shows ArcThread without `key` or `tags`; `thread_update` supports `active`, `urgency`, and `progress`; `thread_add` no longer includes `tags` or `key`
- CRITICAL instruction added: storyteller must check all active/latent thread summaries for conceptual overlap before emitting new threads; update existing threads via `thread_update` instead of creating duplicates when tension is the same
- Band-aligned beat selection section: directive/band priority rule added (directive takes precedence over band — Breathe→breathing_room, Pressure/Overwhelm→complication/pressure, Tension→follow band); near-miss exception: fail near-misses within 2 of threshold at 7 may use complication; null cadence: emit null at least 1 of every 4 turns regardless of directive
- Choice momentum section added: instructs LLM to escalate from prior turns, connect pacing context to choice urgency, and avoid passive options
### Narrator system prompt (`ccya/prompts/narrate_system.j2`)
- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Player Input Is Truth, Inventory, Never Repeat Prior Narration, Fail-Band Outcomes), (3) Behavioral guidance (NPCs merged single section, Style, Pragmatic Interpretation, Pacing, Campaign arc context), (4) Formatting/output (Markdown). Output discipline section removed (narrator emits only prose after ARC UPDATE removal). Dynamic sections (Universe rules, Genre tone) remain at end.
- ARC UPDATE section (former lines 70-87) removed entirely — narrator never emits the block, extraction code removed from turn.py
- Directives section: removed Combat Fatigue, Location Pressure, Location Imperative definitions; added Scene Pressure (≥3 effective scene age, intermediate signal to wind down or shift focus) and Scene Imperative (≥5 effective scene age, high-priority directive forcing story advancement); new directives use scene-level language reflecting single-age signal from collapsed _compute_ages()
- Null-beat fallback: when no GM beat is present, narrate purely from pacing directive and player input — no added pressure or relief beyond what the scene demands
- Anti-repetition: consolidated three scattered rules into a prominent "Never repeat prior narration" section in Hard rules; covers plot/event rehashing and includes self-check instruction
- NPC favoring: soft guidance after NPC BEHAVIOR DRIVERS to favor NPCs with motivation/fear/leverage set and treat empty-driver NPCs as background
- NPC re-use consolidated: three scattered rules (general intro RE-USE, NPC RE-USE section, non-present NPC mentions) merged into one RE-USE section
### Seed system prompt (`ccya/prompts/generate_seed_system.j2`)
- Generation order: PC → World state → Campaign arc → Opening scene/NPCs → Inventory (arc before NPCs so NPC bonds reference actual campaign goals)
- CompendiumEntry model now has explicit motivation/fear/leverage optional string fields alongside existing name/title/bio/bond/presence/notes; seed prompt TypeScript schema includes these as optional fields (motivation?: string, fear?: string, leverage?: string); seed LLM allowed to assign motivation/fear/leverage at seed time on key NPCs (those with personal ties or central roles in opening situation)
- Scene ideal: 1–4 present NPCs; narrative pressure for exits above that (soft guidance only, engine does NOT track or enforce NPC count at runtime — hard cap removed per Phase 01)
### Storyteller user prompt (`ccya/prompts/storytell_user.j2`)
- Renders all threads in unified list with scope tags ([SCENE]/[ARC]), dormant markers for inactive threads, urgency levels; completed_threads rendered as "## past resolutions" section after active threads loop (for continuity — do not re-open resolved tensions)
- Sections reordered by recency: inventory → conditions → characters → location → arc/threads → past resolutions → world_state → pacing_context → rules_outcome → player_intent → CURRENT TURN NARRATION (most important signal last)
### Narrator user prompt (`ccya/prompts/narrate_user.j2`)
- Sections reordered by recency: Player Character → Inventory → Location → Characters → World State → Immutable Reference → Scene Context → Prior History (renamed from Prior Turns) → Recent Turns → Campaign Arc → This Turn's Result → PLAYER INPUT → directives (most important signal last)
- Thread rendering code extracted to shared `sections/_thread_list.j2` include (eliminated duplicated for-loop in if/elif branches)
- Renders ALL threads (active + latent/dormant, scene-scoped + arc-scoped) with scope tags and (latent) markers; completed_threads rendered as "### Past Resolutions" section after _arc.j2 include for full narrative continuity
- Impossible action block: when `rules_outcome.impossible=true`, renders `**IMPOSSIBLE:**` fact with reason before the band/no-roll section
- `outcome_hint` replaces `directive` as narrator's scene-motion signal: renders `**Outcome:** hold/advance/transition` with value-specific guidance
### Storyteller system prompt (`ccya/prompts/storytell_system.j2`)
- Restructured into 4-section hierarchy: (1) Task/role, (2) Hard rules (Output schema, Output discipline, State-presence rule), (3) Behavioral guidance (Actions, Outcome summary, Thread operations, Rules-outcome, World state rules, Latent threads, PacingContext), (4) GM Beat guidance (longest section, placed last for recency benefit)
- Contradiction fixed: "empty arrays for fields with no changes" removed from task line (conflicted with Output discipline "omit null or empty fields")
- Duplicate beat diversity rules (Beat type diversity + Crisis-aware beat selection) coalesced into single Crisis-aware beat diversity section
### Thread list include (`ccya/prompts/sections/_thread_list.j2`)
- Shared include rendering thread entries with scope tag, latent marker, urgency, and summary
- Used by narrate_user.j2 Scene Context section (eliminates duplicated for-loop in if/elif branches)
### Latent thread handling in system prompts
- narrate_system.j2: instructs narrator to push players toward latent threads through narration, environmental detail, NPC behaviour — show don't tell (NPC glancing at locked door, torchlight from tunnel, curious sounds); build 4 choices toward discovery; increase pressure for unsurfaced threads
- storytell_system.j2: instructs storyteller to use dormant/latent thread knowledge when generating suggestions and beats — craft situations where dormant threads naturally surface (character's past catching up, long-silent threat stirring); steer player via choices/suggestions/complications without exposing latent content directly

### Momentum lifecycle
- `apply_momentum(state, band)` in ccya/state/momentum.py mutates `state["pc"]["momentum"]` deterministically from rules band delta, clamped to [-3, +3]
- Pre-ruling momentum captured BEFORE `_ruling_phase()` (turn.py line ~1049), post-ruling captured AFTER — delta reflects actual band-based change
- Auto-checker `check_momentum_band_delta` reads from `state_snapshot.pc.momentum` (not meta.momentum)
- **events.jsonl fields**: `momentum_before`, `momentum_after`, `momentum_delta` written as top-level event keys on every turn (turn.py ~1501-1503), not only in the conditional ruling_event. Available for all turns including no-roll turns where momentum carries over unchanged from previous turn. Ruling dict includes `raw_total` (sum of dice + modifiers) alongside `final_total` for dice math verification.

### Pacing context and beat lifecycle (Phase 03 pacing overhaul)
- `_compute_pacing_context()` dual-trigger beat_locked: fires when either `consecutive_pressure_turns >= config.consecutive_pressure_threshold` OR `momentum <= config.momentum_floor`; appends "Resolve a Threat" to directive whenever locked
- `_compute_pacing_context()` gains `scene_motion` and `impossible` inputs from ruling LLM; computes `outcome_hint` (`hold`/`advance`/`transition`) from ruling's `scene_motion` and PacingContext escalation signals. `outcome_hint` replaces `directive` as narrator's primary scene-motion signal.
- Consecutive pressure counter (`state["meta"]["consecutive_pressure_turns"]`) updated at turn end: increments when storyteller's `gm_beat.type` is `"pressure"`, `"escalation"`, or `"complication"`; resets to 0 on any other beat type or null beat (re-keyed from directive-based tracking, which never fired)
- `pending_gm_beat` lifecycle: null-clear on null storytell output (key popped from meta); replaced on valid storytell emittion (beat_expires_turn = turn_no + 2); expires when turn_no > beat_expires_turn at narrate setup. Floor relief injects breathing_room when beat_locked AND (pending_gm_beat is None or pressure-type)

### Seed emotional context → narrator consumption
- **Seed generates**: `goal_context` (character-specific stake in visible_goal), NPC `relation` field (narrative job relative to PC), action text (character-shaped, scene-grounded).
- **`goal_context` is UI-only**: Rendered in the sidebar tooltip (`_state_left.html`). NOT rendered in narrator or storyteller prompt context — the LLM never reads the raw `goal_context` value during gameplay. The system prompt provides general early-turn behavioral guidance instead.
- **Sidebar surfaces**: `goal_context` as a hover/focus tooltip on the arc goal (`_state_left.html`), using the existing `has-tooltip`/`tooltip-body` nesting convention.
- **Seed emotional framing contract**: The seed generation prompt enforces `goal_context` (2-3 sentences of personal stakes for the PC), NPC `relation` field, and character-shaped action text. This emotional data is embedded in the initial state and the sidebar, not reintroduced per-turn via prompts.

### EngineConfig field naming (Phase 06b)
- Config fields: thread_deescalate_on_success, resolved_arc_ttl (default 3), completed_thread_ttl (default 3), thread_stale_threshold (default 3), thread_max_active (default 5) — YAML keys match Python field names directly.
- Sampling parameters: ruling_temperature/ruling_top_p, extract_temperature/extract_top_p/extract_frequency_penalty, narrate_temperature/narrate_top_p/narrate_frequency_penalty, generate_seed_temperature/generate_seed_top_p, pack_generation_temperature/pack_generation_top_p; stub fields always null until mlx-lm SDK support: seed, top_k, min_p, rep_penalty, rep_penalty_window. Config structure migrated from flat keys to nested `llm.<stage>.<param>` format (Phase 08).

### Computation functions (Phase 06b)
- `_compute_narration_directive()` derives urgency counts from unified ArcThread objects with scope=scene; reads `ages.get("effective_scene_age", 0)` for Scene Imperative (≥5 effective age, short-circuits all directives) and Scene Pressure (≥3 effective age, secondary append); priority order: Breathe → Scene Imperative → Overwhelm → Pressure → Tension → Scene Pressure
- `_compute_pacing_context()` passes derived `arc.threads[] scope=scene` list to `_compute_narration_directive()`; signature includes new `consecutive_pressure_turns: int = 0` parameter for dual-trigger beat_locked condition
- `_compute_ages(state)` returns only `{"scene_age": scene_age}` — location_age and combat_age removed in Phase 03 pacing overhaul; effective_scene_age pre-computed into ctx._ages dict before pacing context computation (turn.py ~821-826) with +2 boost when "combat" in scene tags

### Token budget cascade
`config.context_window` (default 32768): `llm_client.trim_messages()` drops/truncates oldest non-system messages when budget exceeded. Priority: system prompts retained first, then most recent user/context blocks. This affects all pipeline stages — if budget is tight, older turns in chronicle tail get truncated before narration/extraction contexts.

### Extraction field routing
- **SceneExtractResult**: scene_tags, scene_tagline, location_change, location_description, compendium_npc_update (no pressure fields); CompendiumEntry now has explicit motivation/fear/leverage optional string fields alongside existing name/title/bio/bond/presence/notes
- **StateExtractResult**: inventory_add/remove/update, pc_condition_add/remove (no `failed`)
  - **StorytellerResult**: thread_update (list[ThreadUpdate] with id/urgency/active/summary/progress/progress_kind), goal_update (str | None, applied directly to arc dict — NOT through _merge_arc_update), arc_resolve (ArcResolution with resolution/visible_goal/goal_context/drop_threads/new_threads), thread_resolve (list[ThreadResolution] with id/resolution_state/outcome), thread_add (ArcThread | None), world_state_add: list[WorldStateFact], world_state_remove: list[str], actions, outcome_summary, gm_beat; thread_add validated by id-based dedup only (no key, no fuzzy merge); thread_resolve processed by _apply_thread_resolutions() to move threads from arc.threads[] to arc.completed_threads[], persisting both resolution_state and outcome alongside the ArcThread
- **StateDelta.actions**: list[str], max_length=10 — merged from StorytellerResult.actions, persisted to state["pc"]["actions"] as rolling window by apply_delta()

### Cross-stream data flow (minimal by design)
- Scene → State: location_change (id,name,description) + compendium_npc_update (upserts into state.compendium.npcs with presence field)
- No items_gained/items_lost cross-stream fields exist (removed); extraction_ctx covers this-turn derived data

## Key models with non-obvious behavior

### GMBeat
- Only `type` validated by `StorytellerResult._nullify_invalid_gm_beat`: beat nullified if `type` is None/falsy
- `beat_expires_turn`: turn number at which pending beat expires (set to `turn_no + 2` in turn.py)

### WorldStateFact
- Pydantic model with id: str, text: str, tier: Literal["permanent", "persistent"] = "persistent" — permanent facts are seed-authored and never written or removed by the LLM; persistent facts are runtime-discovered durable environmental changes added via world_state_add (LLM must always emit "persistent")

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
  conditions: list[Condition] — id-based dedup, FIFO cap 5; TTL via turns_remaining (default 10 when None)
    - id: str, label: str, description: str, added_turn: int, turns_remaining: int | None
  momentum: int                # [-3, +3], engine-computed from roll bands
  actions: [str]               # rolling window of last 10 Storyteller actions, persisted by apply_delta

location: {id, name, description}: str

inventory: list[InventoryItem] — credits pinned to top
  - id: str, name: str, notes: str, amount: int (≥1), aliases: [str]

arc:                           # managed by engine/turn.py (_apply_thread_updates, _apply_arc_resolve)
  visible_goal: str
  goal_context: str            # 2–3 sentences explaining why visible_goal matters to this character specifically
  threads: list[ArcThread]     # unified arc.threads[] with active flag; dedup is id-only (no key or fuzzy merge); ArcThread.outcome nullable on active, set from ThreadResolution when completed; ArcThread.resolved_turn tracks when thread was resolved for TTL filtering
  completed_threads: list[ArcThread]   # resolved/failed/abandoned threads moved here by _apply_thread_resolutions(); each has resolution_state + outcome + resolved_turn from ThreadResolution
  resolution: str | None       # set when arc is resolved via arc_resolve
  last_thread_created_turn: int  # tracks when a thread was last created for pacing

resolved_arcs: list[dict]     # stored at state level, TTL-pruned in prompts; each entry has visible_goal, resolution, goal_context, resolved_turn

scene:
  tags: [str], tagline: str
  world_state: list[WorldStateFact]   # permanent tier = seed-authored; persistent tier = LLM-added at runtime
  turn_entered: int            # when the current scene was entered (set on location change, used by _compute_ages())
  location_entered_turn: int   # when location was last changed
  combat_started_turn: int     # set when scene tags include "combat"

compendium.npcs: dict[id] → {name, title, bio, aliases: [str], allegiance: str | None, presence: str | "present"|"nearby"|"known", notes: str | None, motivation: str | None (UI-visible), fear: str | None (hidden from UI), leverage: str | None (hidden from UI), first_seen_turn: int | None}

world.factions: [str], world.locations: [str]
```

## Key constants

- `PC_CONDITIONS_MAX = 5`, `MOMENTUM_MIN = -3`, `MOMENTUM_MAX = 3`
- `DEFAULT_CONDITION_TTL = 10` turns when `turns_remaining` is None

### ErrorKind constants + LlmcError hierarchy (`ccya/errors.py`)
**ErrorKind string constants:** LLM_TIMEOUT, LLM_RATE_LIMIT, LLM_API_ERROR, TURN_PROCESSING_FAILED, PACK_LOAD_FAILED, PACK_GENERATION_FAILED, SEED_GENERATION_FAILED, SERVER_ERROR. All modules use these instead of magic strings for error classification.

**LlmcError exception hierarchy (base → subclasses):**
- `LlmcTimeout` — network/LLM timeout; retryable=True; status_code=None
- `LlmcRateLimit` — HTTP 429 from provider; retryable=True; status_code=429
- `LlmcApiError` — other API errors (5xx); retryable=False; dynamic status_code

**Structured logging pipeline:** All modules use `_log = logging.getLogger(__name__)`. Error calls pass structured fields via `extra={error_kind: ..., trace_id: ...}`. _JsonFormatter flattens extra dict entries as top-level JSON keys in log output. Server middleware persists unhandled exceptions to server_errors.jsonl with ErrorKind classification. Turn viewer merges events.jsonl + server_errors.jsonl into unified timeline sorted by timestamp, discriminated via `row_kind` field ("turn" vs "server_error").
