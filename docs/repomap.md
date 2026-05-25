# REPOMAP — module boundaries, public APIs, cross-module contracts

## Module index (file → responsibility)

| File | Responsibility |
|---|---|
| `ccya/__main__.py` | CLI entry: argparse + uvicorn.run |
| `ccya/cli.py` | CLI commands |
| `ccya/models.py` | All Pydantic models, TurnResult dataclass, load_config() |
| `ccya/errors.py` | ErrorKind string constants (LLM_TIMEOUT, LLM_RATE_LIMIT, etc.) + LlmcError exception hierarchy (LlmcTimeout, LlmcRateLimit, LlmcApiError) |
| `ccya/engine/__init__.py` | Re-exports public APIs; internal helpers for tests; LLM client re-exports (llm_chat, llm_chat_stream) |
| `ccya/engine/config.py` | EngineConfig dataclass, _EventLock, is_turn_in_progress(), Jinja env setup |
| `ccya/engine/turn.py` | run_turn() async orchestrator (thin — imports from submodules), _validate(), warmup() |
| `ccya/engine/narrate.py` | _narrate_messages(), NPC name helpers for prompt building |
| `ccya/engine/pack_gen.py` | generate_pack() — LLM-generated ScenarioBrief, writes to packs/custom/<slug>/ |
| `ccya/engine/names.py` | Name pool generation via Faker (pc, npc, location) |
| `ccya/engine/ruling.py` | _ruling_messages(), _call_ruling() with retry logic (NOT ccya/rules.py — that's the dice engine) |
| `ccya/engine/extraction.py` | _run_extraction_pipeline(): 3 streams (scene/state/storytell), _call_stream() with retry |
| `ccya/engine/seed.py` | generate_seed() for dynamic packs, soft validation |
| `ccya/engine/changes.py` | summarize_changes(), format_change_lines() — diff pre vs post state → emoji display lines |
| `ccya/engine/compactor.py` | maybe_compact(): chronicle compaction + state sanitization (NPC merge, inventory remove, etc.) |
| `ccya/engine/npc_roster.py` | build_npc_roster() — merges present/known NPCs with presence tags |
| `ccya/engine/generate_pack.py` | generate_pack_from_brief(): SSE-driven ephemeral pack generation from world brief |
| `ccya/state/__init__.py` | Re-exports all state symbols |
| `ccya/state/io.py` | load_state, save_state (atomic), init_save_dir, _migrate_state |
| `ccya/state/delta.py` | apply_delta(), reconcile_delta() — condition dedup, cross-turn dedup |
| `ccya/state/inventory.py` | normalize_inventory_id, resolve/fuzzy match helpers |
| `ccya/state/npcs.py` | build_npc_alias_map, touch_compendium_order (LRU) |
| `ccya/state/chronicle.py` | append_event (events.jsonl), append_chronicle (chronicle.md), load_chronicle_tail() |
| `ccya/state/momentum.py` | apply_momentum() — deterministic from rules band, clamped to [-3,+3] |
| `ccya/server/__init__.py` | Re-exports: app, main, config, SAVE_DIR, _validate_stats |
| `ccya/server/app.py` | FastAPI app bootstrap, Jinja env, pack loading, startup event; server error persistence + exception middleware → server_errors.jsonl |
| `ccya/server/routes.py` | All @app.get / @app.post route handlers |
| `ccya/server/panels.py` | Panel context builders: _debug_context(), _load_* helpers, _get_opening() |
| `ccya/server/tv.py` | Turn viewer data from events.jsonl + server_errors.jsonl — unified timeline with row_kind discrimination, per-stream metrics, status colors; `_turn_viewer_data()` returns `(rows, no_events)`; injects a synthetic `row_kind: "seed"` row at index 0 when seed data is present in state.yaml |
| `ccya/server/metrics.py` | _recent_turn_metrics(), _turn_log_entries() — latency/token formatting |
| `ccya/eval/__init__.py` | Re-exports: EvalConfig, JudgeResult, RunResult, Scenario, build_trace, run_scenario, etc. |
| `ccya/eval/config.py` | EvalConfig, JudgesSpec (per-judge rubric/model/temp), load_eval_config() |
| `ccya/eval/judge.py` | run_judges(): parallel domain judges + sequential meta judge; parse_judge_response() YAML front matter |
| `ccya/eval/universal_asserts.py` | 15 auto-checkers (recent_events turn-stamped, NPC cap=8, condition dedup, etc.) — red/yellow severity |
| `ccya/eval/report.py` | write_full_report(run_result, eval_cfg, judge_results=None): single-pass REPORT.md with metadata, optional judge summary + verdicts, flags, auto-checker table, pacing metrics, turn metrics; atomic write via tmp.replace() |
| `ccya/eval/scenario.py` | Scenario (with seed_overrides), Turn, TurnAssert (with stream_id) |
| `ccya/eval/engine_mirror.py` | Live engine constants for scenarios: BANDS, SKILLS, DIFFICULTIES, PC_CONDITION_CAP, SCENE_NAMED_NPC_CAP |
| `ccya/pack.py` | load_pack(), list_packs() — validates pack has seed (static) or scenario (generated) |
| `ccya/rules.py` | Pure-Python dice resolver: resolve_check() (2d6+stat+cond−diff→Band), build_directive() near-miss logic |
| `ccya/llm_client.py` | chat(), chat_stream() — OpenAI-compatible → mlx_lm.server; trim_messages() token-budget trimming |
| `ccya/logging_setup.py` | JSONL RotatingFileHandler + _JsonFormatter (extra fields → flat JSON keys); StreamHandler defaults to WARNING via CCYA_LOG_LEVEL env var |

## Public APIs (function names + 1-liner purpose)

### ccya/models.py
- **load_config(path)** → dict — loads config.yaml
- **TurnResult** dataclass — returned from run_turn(): turn, trace_id, narrative, state_delta, applied, rejected, actions, scene_tags, recent_events, diff, changes, metrics, errors, ruling, outcome_summary, recent_events_evicted, ts

### ccya/engine (via __init__.py)
- **run_turn(...)** → AsyncIterator — 5-call pipeline: rules→narrate→scene/state/storytell extract; yields ("token"), ("phase"), ("complete", TurnResult)
- **generate_seed(pack, config, overrides)** → SeedEnvelope — LLM-generated GameState + opening for dynamic packs
- **generate_seed(pack, config, overrides)** → SeedEnvelope — LLM-generated GameState + opening for dynamic packs (via `ccya/engine/seed.py`)
- **generate_pack_from_brief(...)** → AsyncIterator[dict] — SSE-driven ephemeral pack generation (via `ccya/engine/generate_pack.py`)
- **generate_pack(brief, config)** → Pack — LLM generates ScenarioBrief from WorldBrief (via `ccya/engine/pack_gen.py`)
- **maybe_compact(save_dir, state, config)** → (state, bool) — compacts chronicle + sanitizes state if turn % compact_every == 0
- **format_change_lines(changes)** → list[str] — emoji display lines for UI

### ccya/state (via __init__.py)
- **load_state(save_dir)** → dict — loads YAML with _migrate_state() normalization
- **save_state(save_dir, state)** — atomic write (tmp + rename)
- **apply_delta(state, delta)** → (dict, bool) — merges extract results into state; returns deep copy + evicted flag

### ccya/server (via __init__.py)
- **app** — FastAPI instance with ~25 routes (GET/POST for panels, turn SSE stream, new-game, healthz)

### ccya/pack.py
- **load_pack(pack_id)** → Pack — validates pack has seed_state.yaml (static) or scenario.yaml (generated)
- **list_packs(packs_dir)** → list[PackManifest] — aggregates from default/ and custom/

### ccya/rules.py
- **resolve_check(skill, difficulty, pc_stats, pc_conditions, intent_verb, rng)** → RulesOutcome — 2d6+stat_mod+cond_mod→Band (pure Python)

### ccya/llm_client.py
- **chat(host, model, messages)** → response dict — non-streaming LLM call with retry
- **chat_stream(...)** → AsyncIterator[str] — streaming tokens; trim_messages() drops oldest non-system msgs on budget overflow

## 5-call turn pipeline (run_turn)

1. **Rules/Intent** (non-streaming) — classifies intent, resolves dice via `rules.resolve_check()` → IntentEnvelope + RulesOutcome
2. **Narrate** (streaming→SSE→chronicle.md) — prose narrative with narration directive from velocity/threads
3. **Scene Extract** (JSON→SceneExtractResult) — scene tags, location change, present NPCs, compendium updates
4. **State Extract** (JSON→StateExtractResult) — inventory deltas, condition add/remove
5. **Storytell** (JSON→StorytellerResult) — thread_advance, thread_resolve, thread_add (gated by PacingContext.gate), recent_events, actions, gm_beat

Steps 3–5 merge into StateDelta → _validate() → apply_delta() → summarize_changes() → persist (atomic writes). After persist: maybe_compact().

## Cross-module contracts

### Error propagation path (structured observability)
LLM failure in extraction → typed LlmcError raised with ErrorKind classification → caught by server middleware → persisted to `server_errors.jsonl` + SSE error event pushed via logging_setup.py. Engine modules use `_log = logging.getLogger(__name__)`; all log calls pass structured fields via `extra={}` (error_kind, trace_id). TurnResult.errors collected as list[dict] with ErrorKind constants. Server middleware catches unhandled exceptions and returns JSON responses instead of raw HTML error pages.

### Scene thread lifecycle (unified arc.threads[])
- All scene_pressure functionality migrated to `arc.threads[]` with `scope: scene` — ccya/engine/pressure.py module deleted in phase 06 validation sweep
- Thread age-based rules handle urgency escalation via Python logic, not LLM labels

### Arc thread state machine
- States: LATENT → ACTIVE (via unlock_if condition met) → COMPLETE/FAILED (via advanced_threads progress counter at 3 or _apply_thread_resolutions from StorytellerResult.thread_resolve) / EXPIRED (5+ silent turns via last_seen_turn tracking)
- Engine owns threads; narrator owns visible_goal/thematic_question/discovered_truths
- Active cap = 3, latent cap = 4, promotion cooldown of 3 turns
- ArcThread.resolution_state: str | None — set when thread_resolve processes resolved/failed/abandoned; preserved on completed threads for narrative context and eval rubrics (Phase 05c)
- `_merge_arc_update` unconditionally replaces `arc["threads"]` and `arc["completed_threads"]` on every call — no truthy guard (fixes last-thread resolution persistence bug)
- Latent promotion in `_apply_thread_signals` skips thread IDs already in `arc.completed_threads` — defense-in-depth against re-promotion of resolved threads

### Momentum lifecycle
- `apply_momentum(state, band)` in ccya/state/momentum.py mutates `state["pc"]["momentum"]` deterministically from band delta, clamped to [-3, +3]
- Pre-ruling momentum captured BEFORE `_ruling_phase()` (turn.py line ~1044), post-ruling captured AFTER — delta reflects actual band-based change
- Auto-checker `check_momentum_band_delta` reads from `state_snapshot.pc.momentum` (not meta.momentum)

### Seed emotional context → narrator consumption
- **Seed generates**: `goal_context` (character-specific stake in visible_goal), NPC `relation` field (narrative job relative to PC), `pc_drive` (latent motive), action text (character-shaped, scene-grounded).
- **Narrator consumes**: `goal_context` in the narrate user prompt (`_arc.j2`). The system prompt provides general early-turn behavioral guidance; `_arc.j2` presents the actual value alongside other arc context for this turn. The narrator converts these fields into scene texture, dialogue pressure, and prose emphasis — never reciting them directly.
- **Sidebar surfaces**: `goal_context` as a hover/focus tooltip on the arc goal (`_state_left.html`), using the existing `has-tooltip`/`tooltip-body` nesting convention.
- **Signal mechanism**: The presence of `goal_context` on the arc is the signal for early-turn narrative mode (approach B, no turn-counting dependency).

### EngineConfig field naming (Phase 06b)
- Config fields: thread_urgency_building_at, thread_urgency_immediate_at, thread_urgency_max_age, thread_urgency_immediate_ttl, thread_deescalate_on_success — YAML keys match Python field names directly.

### Computation functions (Phase 06b)
- `_compute_narration_directive()` derives urgency counts from unified ArcThread objects with scope=scene instead of raw scene_pressure dicts
- `_compute_pacing_context()` passes derived `arc.threads[] scope=scene` list to `_compute_narration_directive()`

### Token budget cascade
`config.prompt_token_budget` (default 32768): `llm_client.trim_messages()` drops/truncates oldest non-system messages when budget exceeded. Priority: system prompts retained first, then most recent user/context blocks. This affects all pipeline stages — if budget is tight, older turns in chronicle tail get truncated before narration/extraction contexts.

### Extraction field routing
- **SceneExtractResult**: scene_tags, scene_tagline, location_change, location_description, npc_add/remove/update, compendium_npc_update (no pressure fields)
- **StateExtractResult**: inventory_add/remove/update, pc_condition_add/remove (no `failed`)
- **StorytellerResult**: thread_advance, thread_resolve (list[ThreadResolution]), thread_add (ArcThread | None), recent_events_add/update/remove, actions, outcome_summary, gm_beat (no quest_updates); thread_resolve processed by _apply_thread_resolutions() in turn.py to move threads from arc.threads[] to arc.completed_threads[]
- **StateDelta.actions**: list[str], max_length=10 — merged from StorytellerResult.actions, persisted to state["pc"]["actions"] as rolling window by apply_delta()

### Cross-stream data flow (minimal by design)
- Scene → State: location_change (id,name,description) + present_npcs (id,name,title,notes,bio)
- No items_gained/items_lost cross-stream fields exist (removed); extraction_ctx covers this-turn derived data

## Key models with non-obvious behavior

### GMBeat
- Only `type` validated by `StorytellerResult._nullify_invalid_gm_beat`: beat nullified if `type` is None/falsy
- `beat_expires_turn`: turn number at which pending beat expires (set to `turn_no + 2` in turn.py)

### CompactorSanitizationResult
- `inventory_remove`, `pressure_remove`, `condition_remove` coerced by `_coerce_actions` (field_validator): converts bare strings to `{id: str, confidence: "high"}` dicts

## Type aliases

| Alias | Values |
|---|---|
| `SkillName` | 6 skills (strength, dexterity, wits, lore, charisma, resolve) |
| `Difficulty` | 5 difficulty levels with modifiers in DIFFICULTY_MOD |
| `Band` | crit_fail, fail, setback, partial, success, crit_success (2d6 natural: 2=crit_fail, 12=crit_success) |

## State shape — state.yaml

```yaml
meta:
  game_name: str
  turn: int                    # source of truth — incremented only in engine/turn.py
  setting_pack: str
  model: str
  compendium_touch_order: [str]  # LRU order for NPC selection
  pending_gm_beat: dict | None  # GM beat from scene extractor, consumed by next turn's narrator (runtime-only)
  last_compacted_turn: int     # compaction tracking (0 = never compacted)
  prior_history: list[str]     # canonical append-only compacted history (- [T{n}] ...)
  _seed_type: str | None       # "static" or "dynamic" — set by seed application, read by turn viewer
  _pack_source: str | None     # pack ID that was used to generate this state

# Root-level keys only present when a game has been seeded (not in default empty state)
__seed_meta__:                 # {opening_narrative: str, actions: [str]} — dynamic packs only; set by _apply_seed_to_save_dir()

pc:
  name: str
  tagline: str
  bio: str
  stats: {strength, dexterity, wits, lore, charisma, resolve}: int (1-4 each, total 12-16)
  conditions: list[Condition] — id-based dedup, FIFO cap 5; TTL via turns_remaining (default 10 when None)
    - id: str, label: str, description: str, added_turn: int, turns_remaining: int | None
  momentum: int                # [-3, +3], engine-computed from roll bands
  actions: [str]               # rolling window of last 10 Storyteller actions, persisted by apply_delta

location: {id, name, description}: str

inventory: list[InventoryItem] — credits pinned to top
  - id: str, name: str, notes: str, amount: int (≥1)

arc:                           # managed by engine/turn.py (_apply_thread_signals, _candidate_to_latent_thread)
  visible_goal: str
  goal_context: str            # 2–3 sentences explaining why visible_goal matters to this character specifically (Phase 01)
  thematic_question: str       # emotional register — never stated directly in narration
  hidden_truths: [str]         # designer-only structural spine
  discovered_truths: [str]     # truths player has learned (starts empty)
  threads: list[ArcThread]     # unified arc.threads[] with active flag replaces old active_threads/latent_threads split

  completed_threads: list[Thread]

scene:
  tags: [str], tagline: str
  present_npcs: list[NpcRef]   # sticky: absence does not cause removal; only explicit npc_remove removes. Seed data may include `relation` field for NPC-PC narrative connection.
  world_state: [str]           # immutable after seed
  recent_events: list[Event]   # {id, text, turn} — FIFO cap (default 20)
  location_entered_turn: int   # when location was last changed
  combat_started_turn: int     # set when scene tags include "combat"

compendium.npcs: dict[id] → {name, title, bio, aliases: [str], allegiance: str | None}

world.factions: [str], world.locations: [str]
```

## Key constants

- `PC_CONDITIONS_MAX = 5`, `MOMENTUM_MIN = -3`, `MOMENTUM_MAX = 3`
- `NPC_SCENE_CAP = 8` (max present NPCs in scene)
- `DEFAULT_CONDITION_TTL = 10` turns when `turns_remaining` is None

### ErrorKind constants + LlmcError hierarchy (`ccya/errors.py`)
**ErrorKind string constants:** LLM_TIMEOUT, LLM_RATE_LIMIT, LLM_API_ERROR, TURN_PROCESSING_FAILED, PACK_LOAD_FAILED, PACK_GENERATION_FAILED, SEED_GENERATION_FAILED, SERVER_ERROR. All modules use these instead of magic strings for error classification.

**LlmcError exception hierarchy (base → subclasses):**
- `LlmcTimeout` — network/LLM timeout; retryable=True; status_code=None
- `LlmcRateLimit` — HTTP 429 from provider; retryable=True; status_code=429
- `LlmcApiError` — other API errors (5xx); retryable=False; dynamic status_code

**Structured logging pipeline:** All modules use `_log = logging.getLogger(__name__)`. Error calls pass structured fields via `extra={error_kind: ..., trace_id: ...}`. _JsonFormatter flattens extra dict entries as top-level JSON keys in log output. Server middleware persists unhandled exceptions to server_errors.jsonl with ErrorKind classification. Turn viewer merges events.jsonl + server_errors.jsonl into unified timeline sorted by timestamp, discriminated via `row_kind` field ("turn" vs "server_error").
